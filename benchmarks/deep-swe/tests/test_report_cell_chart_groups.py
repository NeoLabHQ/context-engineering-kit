#!/usr/bin/env python3
"""Unit tests for the per-complexity and per-task chart-group builders.

These are the builders that turn `results.json`'s `cells` + `schedule` +
`baseline.fable5` sections into the same `ChartGroup`/`Bar` shape the two
aggregation charts already use, so the existing layout and rendering code is
reused rather than duplicated.

Two structural invariants are load-bearing and tested here directly:

  * every group in one chart carries the same slot list in the same order
    (`layout_chart_bars` reads `groups[0].bars` to size every group, so a
    ragged chart silently mislays every bar after the first group);
  * the task-to-complexity mapping comes from the `schedule` section, never
    from a list restated in report.py.
"""

from __future__ import annotations

import json
import unittest
from typing import Any

import report  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR
from .report_fixtures import make_cell, make_measured

SCHEDULE: dict[str, Any] = {
    "available": True,
    "complexity_levels": ["low", "medium", "high"],
    "vanilla_skill": "vanilla",
    "skills": ["vanilla", "do-and-judge", "do-in-steps"],
    "models": [
        {"name": "haiku", "orchestrator": "haiku", "impl": "haiku"},
        {"name": "sonnet", "orchestrator": "sonnet", "impl": "sonnet"},
        {"name": "sonnet-haiku", "orchestrator": "sonnet", "impl": "haiku"},
    ],
    "tasks": [
        {"name": "task-low", "complexity": "low", "complexity_rank": 0},
        {"name": "task-med", "complexity": "medium", "complexity_rank": 1},
    ],
}


def load_real_results() -> dict[str, Any]:
    """The committed results.json -- the sparse, mostly-absent real matrix
    these charts exist to render honestly."""
    return json.loads((BENCHMARK_DIR / "results.json").read_text())


class ScheduleReadingTests(unittest.TestCase):
    def test_model_and_skill_order_come_from_the_schedule_not_a_local_list(self) -> None:
        self.assertEqual(
            report.schedule_model_names(SCHEDULE), ["haiku", "sonnet", "sonnet-haiku"]
        )
        # Declaration order, not alphabetical: it puts the no-plugin control
        # arm first, which is the order a reader compares against.
        self.assertEqual(
            report.schedule_skill_names(SCHEDULE), ["vanilla", "do-and-judge", "do-in-steps"]
        )

    def test_tasks_are_ordered_by_complexity_rank(self) -> None:
        cells = [make_cell(task="task-med", complexity="medium", complexity_rank=1)]
        ordered = report.tasks_in_report_order(SCHEDULE, cells)
        self.assertEqual([t["name"] for t in ordered], ["task-low", "task-med"])

    def test_an_unscheduled_task_is_kept_but_sorted_last_with_no_complexity(self) -> None:
        # `bandit-incremental-cache-control` in the real data: measured, but
        # absent from schedule.yaml, so it has no rung on the complexity axis.
        cells = [make_cell(task="task-x", complexity=None, complexity_rank=None)]
        ordered = report.tasks_in_report_order(SCHEDULE, cells)
        self.assertEqual([t["name"] for t in ordered], ["task-low", "task-med", "task-x"])
        self.assertIsNone(ordered[-1]["complexity"])

    def test_the_real_schedule_maps_the_three_tasks_to_three_complexities(self) -> None:
        results = load_real_results()
        ordered = report.tasks_in_report_order(results["schedule"], results["cells"])
        ranked = [(t["name"], t["complexity"]) for t in ordered if t["complexity"] is not None]
        self.assertEqual([c for _, c in ranked], ["low", "medium", "high"])


class ComplexityChartGroupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = {"available": False}

    def test_groups_are_models_and_slots_are_skills_plus_the_official_slot(self) -> None:
        groups = report.build_complexity_chart_groups("low", [], SCHEDULE, self.baseline)
        self.assertEqual([g.label for g in groups[:-1]], ["haiku", "sonnet", "sonnet-haiku"])
        for group in groups:
            self.assertEqual(
                [bar.slot for bar in group.bars],
                ["official", "vanilla", "do-and-judge", "do-in-steps"],
            )

    def test_every_group_carries_an_identical_slot_count(self) -> None:
        groups = report.build_complexity_chart_groups("low", [], SCHEDULE, self.baseline)
        self.assertEqual(len({len(g.bars) for g in groups}), 1)

    def test_a_measured_cell_becomes_a_present_bar_in_its_model_group(self) -> None:
        cells = [
            make_cell(task="task-low", model="sonnet", skill="do-in-steps", complexity="low", complexity_rank=0)
        ]
        groups = report.build_complexity_chart_groups("low", cells, SCHEDULE, self.baseline)
        sonnet = next(g for g in groups if g.label == "sonnet")
        bar = next(b for b in sonnet.bars if b.slot == "do-in-steps")
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 1.0)

    def test_cells_from_another_complexity_level_never_leak_in(self) -> None:
        cells = [
            make_cell(task="task-med", model="sonnet", skill="do-in-steps", complexity="medium", complexity_rank=1)
        ]
        groups = report.build_complexity_chart_groups("low", cells, SCHEDULE, self.baseline)
        sonnet = next(g for g in groups if g.label == "sonnet")
        bar = next(b for b in sonnet.bars if b.slot == "do-in-steps")
        self.assertFalse(bar.present)

    def test_an_unmeasured_slot_carries_its_absence_state_forward(self) -> None:
        cells = [
            make_cell(
                task="task-low",
                model="haiku",
                skill="vanilla",
                complexity="low",
                complexity_rank=0,
                state="deliberately_skipped",
                reason="too complex for haiku at the vanilla level",
            )
        ]
        groups = report.build_complexity_chart_groups("low", cells, SCHEDULE, self.baseline)
        haiku = next(g for g in groups if g.label == "haiku")
        bar = next(b for b in haiku.bars if b.slot == "vanilla")
        self.assertEqual(bar.absence.state, "deliberately_skipped")
        self.assertIn("too complex", bar.absence.reason)


class PooledSlotTests(unittest.TestCase):
    """A complexity level can hold several tasks, so one slot can pool several
    cells. Pooling must not invent a statistic nor flatten disagreeing
    absence states into the vaguest one."""

    def _cell(self, task: str, **kw: Any) -> dict[str, Any]:
        return make_cell(task=task, complexity="low", complexity_rank=0, **kw)

    def test_a_single_contributing_cell_keeps_its_own_interval(self) -> None:
        cell = self._cell(
            "task-low",
            measured=make_measured(
                n_resolved=2, n_attempts=3, pass_at_1=2 / 3,
                is_single_trial=False, pass_at_1_ci_low=0.2, pass_at_1_ci_high=0.94,
            ),
        )
        bar = report.pool_pass_bar("do-in-steps", [cell])
        self.assertEqual((bar.ci_low, bar.ci_high), (0.2, 0.94))

    def test_pooling_several_cells_sums_counts_and_draws_no_interval(self) -> None:
        # collect.py's per-cell Wilson bounds are computed against per-cell
        # denominators and do not compose; the renderer must not manufacture
        # a pooled one.
        cells = [
            self._cell("task-a", measured=make_measured(n_resolved=1, n_attempts=1)),
            self._cell("task-b", measured=make_measured(n_resolved=0, n_attempts=1, pass_at_1=0.0)),
        ]
        bar = report.pool_pass_bar("do-in-steps", cells)
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 0.5)
        self.assertIsNone(bar.ci_low)
        self.assertIsNone(bar.ci_high)
        self.assertIn("1 of 2 resolved", bar.display)

    def test_a_pooled_zero_is_present_not_absent(self) -> None:
        cells = [
            self._cell("task-a", measured=make_measured(n_resolved=0, n_attempts=1, pass_at_1=0.0)),
            self._cell("task-b", measured=make_measured(n_resolved=0, n_attempts=1, pass_at_1=0.0)),
        ]
        bar = report.pool_pass_bar("do-in-steps", cells)
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 0.0)

    def test_a_measured_cell_outvotes_an_absent_sibling(self) -> None:
        cells = [
            self._cell("task-a", state="not_yet_run"),
            self._cell("task-b", measured=make_measured(n_resolved=1, n_attempts=1)),
        ]
        bar = report.pool_pass_bar("do-in-steps", cells)
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 1.0)

    def test_disagreeing_absences_report_the_most_conclusive_state(self) -> None:
        cells = [
            self._cell("task-a", state="not_yet_run"),
            self._cell("task-b", state="deliberately_skipped", reason="declared unrun"),
        ]
        bar = report.pool_pass_bar("do-in-steps", cells)
        self.assertEqual(bar.absence.state, "deliberately_skipped")
        self.assertIn("declared unrun", bar.absence.reason)

    def test_a_partial_absence_says_how_many_tasks_it_covers(self) -> None:
        cells = [
            self._cell("task-a", state="not_yet_run"),
            self._cell("task-b", state="deliberately_skipped", reason="declared unrun"),
        ]
        bar = report.pool_pass_bar("do-in-steps", cells)
        self.assertIn("1 of 2 tasks", bar.absence.reason)

    def test_no_cells_at_all_is_an_absence_and_never_a_zero(self) -> None:
        bar = report.pool_pass_bar("do-in-steps", [])
        self.assertFalse(bar.present)
        self.assertIsNotNone(bar.absence)


class TaskMeasureChartGroupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = {"available": False}

    def test_cost_groups_are_models_with_one_slot_per_skill(self) -> None:
        groups = report.build_task_measure_chart_groups(
            "task-low", [], SCHEDULE, self.baseline, "avg_cost_usd", "mean_cost_usd", report.format_usd
        )
        self.assertEqual([g.label for g in groups[:-1]], ["haiku", "sonnet", "sonnet-haiku"])
        for group in groups:
            self.assertEqual(
                [bar.slot for bar in group.bars],
                ["official", "vanilla", "do-and-judge", "do-in-steps"],
            )

    def test_a_measured_cost_lands_in_its_model_group_with_a_dollar_label(self) -> None:
        cells = [
            make_cell(
                task="task-low", model="sonnet", skill="do-in-steps",
                measured=make_measured(avg_cost_usd=22.54),
            )
        ]
        groups = report.build_task_measure_chart_groups(
            "task-low", cells, SCHEDULE, self.baseline, "avg_cost_usd", "mean_cost_usd", report.format_usd
        )
        sonnet = next(g for g in groups if g.label == "sonnet")
        bar = next(b for b in sonnet.bars if b.slot == "do-in-steps")
        self.assertEqual(bar.value, 22.54)
        self.assertEqual(bar.display, "$22.54")

    def test_no_cost_bar_ever_carries_an_interval(self) -> None:
        cells = [make_cell(task="task-low", model="sonnet", skill="do-in-steps")]
        groups = report.build_task_measure_chart_groups(
            "task-low", cells, SCHEDULE, self.baseline, "avg_cost_usd", "mean_cost_usd", report.format_usd
        )
        for group in groups:
            for bar in group.bars:
                with self.subTest(group=group.label, slot=bar.slot):
                    self.assertIsNone(bar.ci_low)
                    self.assertIsNone(bar.ci_high)


class ChartMaxValueTests(unittest.TestCase):
    def test_a_pass_at_1_chart_is_always_scaled_to_a_full_100_percent(self) -> None:
        groups = [report.ChartGroup(label="m", bars=(report.Bar(slot="s", present=True, value=0.2),))]
        self.assertEqual(report.chart_max_value(groups, fixed_max=1.0), 1.0)

    def test_an_absolute_chart_is_scaled_to_a_nice_ceiling_above_its_largest_bar(self) -> None:
        # Fix 4: the axis ceiling is rounded UP to a readable step rather
        # than sitting exactly on the largest bar -- 36.5 rounds up to a 40
        # ceiling (four steps of 10), so every gridline `y_axis_value_ticks`
        # derives from this maximum is a round number, not "$9.13"/"$18.25".
        groups = [
            report.ChartGroup(
                label="m",
                bars=(
                    report.Bar(slot="a", present=True, value=10.0),
                    report.Bar(slot="b", present=True, value=36.5),
                ),
            )
        ]
        self.assertEqual(report.chart_max_value(groups, fixed_max=None), 40.0)

    def test_a_measured_zero_is_counted_when_deriving_the_maximum(self) -> None:
        # `bar.value` of 0.0 is falsy, so a truthiness test here would drop a
        # real measurement out of the axis calculation -- the same "a zero is
        # not no-data" mistake this whole step is about, one layer down.
        groups = [
            report.ChartGroup(
                label="m",
                bars=(
                    report.Bar(slot="a", present=True, value=0.0),
                    report.Bar(slot="b", present=False),
                ),
            )
        ]
        self.assertEqual(report.chart_max_value(groups, fixed_max=None), report.EMPTY_AXIS_MAX)
        with_value = [
            report.ChartGroup(
                label="m",
                bars=(
                    report.Bar(slot="a", present=True, value=0.0),
                    report.Bar(slot="b", present=True, value=12.0),
                ),
            )
        ]
        # 12.0 rounds up to a 20 ceiling (four steps of 5) -- see Fix 4 above.
        self.assertEqual(report.chart_max_value(with_value, fixed_max=None), 20.0)

    def test_an_all_absent_chart_falls_back_to_a_positive_max(self) -> None:
        # A max of 0 would make value_to_y divide by zero-ish and flatten
        # every future bar onto the baseline.
        groups = [report.ChartGroup(label="m", bars=(report.Bar(slot="a", present=False),))]
        self.assertGreater(report.chart_max_value(groups, fixed_max=None), 0.0)


if __name__ == "__main__":
    unittest.main()
