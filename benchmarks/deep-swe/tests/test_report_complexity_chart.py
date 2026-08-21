#!/usr/bin/env python3
"""Unit tests for the complexity chart: series assembly, its two-channel
encoding, and its pure geometry.

THE ENCODING PROBLEM THIS CHART SOLVES
---------------------------------------
5 models x 3 skills is up to 15 series, and `assign_categorical_color_vars`
refuses more than 3 categorical colors -- correctly, because a 15-hue chart is
unreadable. So the chart splits identity across two channels: hue carries the
skill (there are exactly 3, which is exactly what the palette validates) and
marker SHAPE carries the model. The tests below pin both halves, and pin that
the 3-slot color guard is still the unweakened original.

HOW THE LINES ARE DRAWN
------------------------
Two independent decisions, and conflating them was the bug this file's
`ConnectorGapTests` and `ConnectorRuleTests` now guard:

* WHETHER a segment may be drawn is adjacency. `build_complexity_series`
  compresses unmeasured ranks out of `points`, so two neighbouring entries
  can be low and high with an unmeasured medium between them; the connector
  is therefore split into contiguous runs and one polyline is emitted per
  run. A single polyline over the whole list would draw a straight segment
  across the unmeasured level and assert a measurement nobody took.
* HOW FIRMLY it is drawn is replication. Every measured cell in the current
  data is a single trial, so each point is one 0-or-1 observation and a line
  through them cannot assert a trend. Those lines are drawn dashed and faded
  (`CONNECTOR_PROVISIONAL`) as a reading aid; the solid stroke is reserved
  for series whose every point has more than one attempt behind it.
"""

from __future__ import annotations

import json
import unittest
from typing import Any

import report  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR
from .report_fixtures import make_cell, make_measured

SCHEDULE: dict[str, Any] = {
    "complexity_levels": ["low", "medium", "high"],
    "skills": ["vanilla", "do-and-judge", "do-in-steps"],
    "models": [
        {"name": "haiku"},
        {"name": "sonnet"},
        {"name": "opus"},
        {"name": "sonnet-haiku"},
        {"name": "opus-sonnet"},
    ],
    "tasks": [
        {"name": "task-low", "complexity": "low", "complexity_rank": 0},
        {"name": "task-med", "complexity": "medium", "complexity_rank": 1},
        {"name": "task-high", "complexity": "high", "complexity_rank": 2},
    ],
}


def measured_cell(task: str, rank: int, model: str, skill: str, **kw: Any) -> dict[str, Any]:
    return make_cell(
        task=task,
        model=model,
        skill=skill,
        complexity=SCHEDULE["complexity_levels"][rank],
        complexity_rank=rank,
        measured=make_measured(**kw),
    )


class ColorGuardIsIntactTests(unittest.TestCase):
    """The reason this chart needed a second channel in the first place. If
    this guard is ever loosened, the encoding below stops being justified --
    so it is asserted here, not only where it is defined."""

    def test_three_slots_are_allowed(self) -> None:
        assigned = report.assign_categorical_color_vars(["vanilla", "do-and-judge", "do-in-steps"])
        self.assertEqual(set(assigned.values()), {"--series-1", "--series-2", "--series-3"})

    def test_a_fourth_slot_still_raises(self) -> None:
        with self.assertRaises(ValueError):
            report.assign_categorical_color_vars(["a", "b", "c", "d"])

    def test_the_skill_channel_can_never_need_a_fourth_color(self) -> None:
        # Hue is assigned over skills only; the 5 models ride the shape
        # channel, so model count cannot push the palette over its limit.
        report.assign_categorical_color_vars(report.schedule_skill_names(SCHEDULE))


class MarkerShapeChannelTests(unittest.TestCase):
    def test_each_model_gets_a_distinct_shape_in_schedule_order(self) -> None:
        shapes = report.assign_model_marker_shapes(report.schedule_model_names(SCHEDULE))
        self.assertEqual(len(set(shapes.values())), 5)
        self.assertEqual(shapes["haiku"], report.MODEL_MARKER_SHAPES[0])

    def test_a_model_keeps_its_shape_regardless_of_which_chart_it_appears_on(self) -> None:
        # Assignment is by position in the schedule's own model list, so a
        # chart that happens to show a subset does not reshuffle shapes.
        full = report.assign_model_marker_shapes(["haiku", "sonnet", "opus"])
        self.assertEqual(full["sonnet"], report.MODEL_MARKER_SHAPES[1])

    def test_more_models_than_shapes_raises_rather_than_reusing_one(self) -> None:
        # Same philosophy as the color guard: an ambiguous chart is worse than
        # a loud failure. Two models sharing a shape is an unreadable legend.
        too_many = [f"m{i}" for i in range(len(report.MODEL_MARKER_SHAPES) + 1)]
        with self.assertRaises(ValueError):
            report.assign_model_marker_shapes(too_many)

    def test_every_declared_shape_renders_some_ink(self) -> None:
        for shape in report.MODEL_MARKER_SHAPES:
            with self.subTest(shape=shape):
                markup = report.render_marker(shape, 10.0, 20.0, "--series-1")
                self.assertTrue(markup.strip())
                self.assertIn("var(--series-1)", markup)

    def test_an_unknown_shape_raises_instead_of_drawing_nothing(self) -> None:
        with self.assertRaises(ValueError):
            report.render_marker("hexagram", 10.0, 20.0, "--series-1")


class ComplexitySeriesTests(unittest.TestCase):
    def test_a_series_is_one_model_skill_pair_ordered_by_complexity_rank(self) -> None:
        cells = [
            measured_cell("task-med", 1, "sonnet", "do-in-steps", n_resolved=0, pass_at_1=0.0),
            measured_cell("task-low", 0, "sonnet", "do-in-steps"),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)
        self.assertEqual(len(series), 1)
        self.assertEqual((series[0].model, series[0].skill), ("sonnet", "do-in-steps"))
        self.assertEqual([p.complexity_rank for p in series[0].points], [0, 1])

    def test_only_measured_cells_become_points(self) -> None:
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps"),
            make_cell(
                task="task-med", model="sonnet", skill="do-in-steps",
                complexity="medium", complexity_rank=1, state="not_yet_run",
            ),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)
        self.assertEqual([p.complexity_rank for p in series[0].points], [0])

    def test_an_unranked_task_lands_on_no_complexity_axis(self) -> None:
        # The real `bandit-incremental-cache-control` cell: measured, but the
        # schedule never gave it a complexity, so it has no x position.
        cells = [
            make_cell(
                task="task-x", model="sonnet", skill="do-in-steps",
                complexity=None, complexity_rank=None,
            )
        ]
        self.assertEqual(report.build_complexity_series(cells, SCHEDULE), [])

    def test_a_measured_zero_is_a_point_not_a_gap(self) -> None:
        cells = [measured_cell("task-low", 0, "sonnet", "do-in-steps", n_resolved=0, pass_at_1=0.0)]
        series = report.build_complexity_series(cells, SCHEDULE)
        self.assertEqual(series[0].points[0].value, 0.0)

    def test_series_are_ordered_by_schedule_model_then_skill(self) -> None:
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps"),
            measured_cell("task-low", 0, "haiku", "vanilla"),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)
        self.assertEqual([(s.model, s.skill) for s in series], [("haiku", "vanilla"), ("sonnet", "do-in-steps")])

    def test_each_point_reports_its_counts_and_its_task(self) -> None:
        cells = [measured_cell("task-low", 0, "sonnet", "do-in-steps")]
        point = report.build_complexity_series(cells, SCHEDULE)[0].points[0]
        self.assertEqual((point.n_resolved, point.n_attempts), (1, 1))
        self.assertTrue(point.is_single_trial)
        self.assertIn("task-low", point.label)
        self.assertIn("1 of 1 resolved", point.label)

    def test_two_tasks_at_one_complexity_pool_into_a_single_point(self) -> None:
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps", n_resolved=1),
            make_cell(
                task="task-low-b", model="sonnet", skill="do-in-steps",
                complexity="low", complexity_rank=0,
                measured=make_measured(n_resolved=0, pass_at_1=0.0),
            ),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)
        self.assertEqual(len(series[0].points), 1)
        self.assertEqual(series[0].points[0].value, 0.5)
        self.assertFalse(series[0].points[0].is_single_trial)


class ConnectorRuleTests(unittest.TestCase):
    """Two independent decisions, tested separately because they are
    separate: WHETHER a segment may be drawn (adjacency) and HOW firmly it is
    drawn (replication). Conflating them was the earlier bug -- withholding
    every line for lack of replication deleted the requested chart element
    for the whole single-trial data regime instead of qualifying it."""

    def test_two_adjacent_measured_points_are_joined_up(self) -> None:
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps"),
            measured_cell("task-med", 1, "sonnet", "do-in-steps", n_resolved=0, pass_at_1=0.0),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)[0]
        self.assertTrue(report.series_has_connector(series))

    def test_a_single_trial_series_is_joined_provisionally_not_solidly(self) -> None:
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps"),
            measured_cell("task-med", 1, "sonnet", "do-in-steps", n_resolved=0, pass_at_1=0.0),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)[0]
        self.assertEqual(report.series_connector_style(series), report.CONNECTOR_PROVISIONAL)

    def test_a_series_where_every_point_has_real_replication_is_drawn_solid(self) -> None:
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps", n_resolved=3, n_attempts=4, pass_at_1=0.75, is_single_trial=False),
            measured_cell("task-med", 1, "sonnet", "do-in-steps", n_resolved=1, n_attempts=4, pass_at_1=0.25, is_single_trial=False),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)[0]
        self.assertTrue(report.series_has_connector(series))
        self.assertEqual(report.series_connector_style(series), report.CONNECTOR_SOLID)

    def test_one_single_trial_point_makes_the_whole_series_provisional(self) -> None:
        # A line is read end to end, so one 0-or-1 anchor qualifies the whole
        # shape -- not just the segment touching it.
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps", n_resolved=3, n_attempts=4, pass_at_1=0.75, is_single_trial=False),
            measured_cell("task-med", 1, "sonnet", "do-in-steps"),
        ]
        series = report.build_complexity_series(cells, SCHEDULE)[0]
        self.assertEqual(report.series_connector_style(series), report.CONNECTOR_PROVISIONAL)

    def test_a_lone_point_is_never_connected_to_itself(self) -> None:
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps", n_resolved=3, n_attempts=4, pass_at_1=0.75, is_single_trial=False)
        ]
        series = report.build_complexity_series(cells, SCHEDULE)[0]
        self.assertFalse(report.series_has_connector(series))

    def test_the_real_results_do_join_up_their_one_adjacent_pair(self) -> None:
        # sonnet/do-in-steps is measured at low and at medium -- adjacent
        # ranks, so the chart draws the line the brief asked for, dashed
        # because both points are single trials.
        results = json.loads((BENCHMARK_DIR / "results.json").read_text())
        series = report.build_complexity_series(results["cells"], results["schedule"])
        connected = [s for s in series if report.series_has_connector(s)]
        self.assertEqual([(s.model, s.skill) for s in connected], [("sonnet", "do-in-steps")])
        self.assertEqual(report.series_connector_style(connected[0]), report.CONNECTOR_PROVISIONAL)


class ConnectorGapTests(unittest.TestCase):
    """The defect these exist for: `build_complexity_series` compresses
    unmeasured ranks out of `points`, so list adjacency is NOT axis
    adjacency. One polyline over the whole list would draw a straight
    segment across an unmeasured complexity level and assert a measurement
    nobody took."""

    def _gapped_series(self) -> report.ComplexitySeries:
        """Measured at low (rank 0) and high (rank 2); medium never run."""
        cells = [
            measured_cell("task-low", 0, "sonnet", "do-in-steps"),
            measured_cell("task-high", 2, "sonnet", "do-in-steps", n_resolved=0, pass_at_1=0.0),
        ]
        return report.build_complexity_series(cells, SCHEDULE)[0]

    def test_the_gapped_series_really_has_a_missing_middle_rank(self) -> None:
        # Guards the fixture itself: if this ever stopped skipping rank 1,
        # every assertion below would pass for the wrong reason.
        self.assertEqual([p.complexity_rank for p in self._gapped_series().points], [0, 2])

    def test_a_gap_splits_the_series_into_two_runs(self) -> None:
        runs = report.contiguous_measured_runs(self._gapped_series())
        self.assertEqual([[p.complexity_rank for p in run] for run in runs], [[0], [2]])

    def test_neither_side_of_a_gap_is_long_enough_to_draw(self) -> None:
        self.assertEqual(report.series_connector_runs(self._gapped_series()), [])
        self.assertFalse(report.series_has_connector(self._gapped_series()))

    def test_a_gap_between_two_measured_pairs_emits_two_polylines_not_one(self) -> None:
        # Ranks 0,1 measured and 3,4 measured with 2 absent: the connector
        # path must break at the gap, so exactly two polylines are drawn.
        schedule = {
            **SCHEDULE,
            "complexity_levels": ["l0", "l1", "l2", "l3", "l4"],
        }
        cells = [
            make_cell(
                task=f"task-{rank}", model="sonnet", skill="do-in-steps",
                complexity=f"l{rank}", complexity_rank=rank,
                measured=make_measured(n_resolved=2, n_attempts=4, pass_at_1=0.5, is_single_trial=False),
            )
            for rank in (0, 1, 3, 4)
        ]
        series = report.build_complexity_series(cells, schedule)[0]
        self.assertEqual(
            [[p.complexity_rank for p in run] for run in report.series_connector_runs(series)],
            [[0, 1], [3, 4]],
        )

        svg = report.render_complexity_chart_svg(
            [series], report.CELL_CHART_GEOMETRY,
            {"do-in-steps": "--series-3"}, {"sonnet": "square"},
            schedule["complexity_levels"],
        )
        self.assertEqual(svg.count("<polyline"), 2)

    def test_no_drawn_SEGMENT_crosses_the_unmeasured_column(self) -> None:
        # The pixel-level statement of the same fact, and the one that
        # actually discriminates: a single polyline over the compressed point
        # list emits NO vertex at the absent column, so checking vertices
        # alone would pass against the very bug this guards. What matters is
        # that no drawn SEGMENT passes over that column's x.
        schedule = {**SCHEDULE, "complexity_levels": ["l0", "l1", "l2", "l3", "l4"]}
        cells = [
            make_cell(
                task=f"task-{rank}", model="sonnet", skill="do-in-steps",
                complexity=f"l{rank}", complexity_rank=rank,
                measured=make_measured(n_resolved=2, n_attempts=4, pass_at_1=0.5, is_single_trial=False),
            )
            for rank in (0, 1, 3, 4)
        ]
        series = report.build_complexity_series(cells, schedule)[0]
        geometry = report.CELL_CHART_GEOMETRY
        gap_x = report.complexity_column_x(2, geometry)

        svg = report.render_complexity_chart_svg(
            [series], geometry, {"do-in-steps": "--series-3"}, {"sonnet": "square"},
            schedule["complexity_levels"],
        )
        for polyline in svg.split("<polyline")[1:]:
            points = polyline.split('points="')[1].split('"')[0]
            xs = [float(pair.split(",")[0]) for pair in points.split()]
            for left, right in zip(xs, xs[1:], strict=False):
                with self.subTest(segment=(left, right)):
                    self.assertFalse(
                        left < gap_x < right,
                        f"segment {left}->{right} crosses the unmeasured column at {gap_x}",
                    )


class ConnectorStrokeTests(unittest.TestCase):
    def test_a_provisional_connector_is_dashed_and_faded(self) -> None:
        markup = report.render_connector("1.0,2.0 3.0,4.0", "--series-1", report.CONNECTOR_PROVISIONAL)
        self.assertIn('stroke-dasharray="4 3"', markup)
        self.assertIn('stroke-opacity="0.4"', markup)

    def test_a_solid_connector_carries_no_dash_pattern(self) -> None:
        markup = report.render_connector("1.0,2.0 3.0,4.0", "--series-1", report.CONNECTOR_SOLID)
        self.assertNotIn("stroke-dasharray", markup)

    def test_the_two_styles_are_visually_distinguishable(self) -> None:
        provisional = report.render_connector("1.0,2.0", "--series-1", report.CONNECTOR_PROVISIONAL)
        solid = report.render_connector("1.0,2.0", "--series-1", report.CONNECTOR_SOLID)
        self.assertNotEqual(provisional, solid)

    def test_an_unknown_style_raises_rather_than_defaulting_to_solid(self) -> None:
        # Falling back to solid would silently upgrade a reading aid into an
        # asserted trend.
        with self.assertRaises(ValueError):
            report.render_connector("1.0,2.0", "--series-1", "emphatic")


class ComplexityGeometryTests(unittest.TestCase):
    """Expected pixel values are computed by hand from ChartGeometry's default
    field values and the module's own column/dodge constants -- never by
    calling the function under test to produce its own expectation."""

    def setUp(self) -> None:
        self.geometry = report.ChartGeometry()  # plot_left=46, plot_top=30, plot_height=200

    def test_each_complexity_sits_at_the_centre_of_its_own_column(self) -> None:
        width = report.COMPLEXITY_COLUMN_WIDTH
        self.assertAlmostEqual(report.complexity_column_x(0, self.geometry), 46.0 + 0.5 * width)
        self.assertAlmostEqual(report.complexity_column_x(2, self.geometry), 46.0 + 2.5 * width)

    def test_a_lone_series_is_not_dodged_off_centre(self) -> None:
        self.assertEqual(report.series_dodge_offset(0, 1), 0.0)

    def test_dodging_is_symmetric_about_the_column_centre(self) -> None:
        offsets = [report.series_dodge_offset(i, 4) for i in range(4)]
        self.assertAlmostEqual(sum(offsets), 0.0)
        self.assertAlmostEqual(offsets[0], -offsets[-1])

    def test_dodging_is_deterministic_rather_than_jittered(self) -> None:
        # Two identical calls must agree: a random jitter would move a point
        # between report builds and make two reports incomparable.
        self.assertEqual(report.series_dodge_offset(2, 5), report.series_dodge_offset(2, 5))

    def test_the_shared_value_axis_is_reused_rather_than_re_derived(self) -> None:
        # Points sit on exactly the same 0-100% scale as the bar charts.
        self.assertEqual(
            report.value_to_y(1.0, self.geometry), self.geometry.plot_top
        )
        self.assertEqual(
            report.value_to_y(0.0, self.geometry),
            self.geometry.plot_top + self.geometry.plot_height,
        )


if __name__ == "__main__":
    unittest.main()
