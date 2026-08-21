#!/usr/bin/env python3
"""Rendering-level tests for the one property this whole step exists for:
an absence and a measured zero must never look alike.

Four absence states plus a real `pass_at_1: 0.0` is five things that all have
"nothing above the baseline" as their naive rendering. These tests pin the
five apart at the SVG level, because that is the level a reader actually
sees -- a data model that distinguishes them and a renderer that collapses
them would still ship the lie.

The rendering contract, one row per case:

  measured > 0            filled hue bar, height proportional to the value
  measured == 0.0         filled hue bar clamped to a visible floor
  deliberately_skipped    full-height hatched slot + "⊘" glyph
  structurally_impossible full-height hatched slot + "≡" glyph
  technical_failure       full-height hatched slot + "⚠" glyph
  not_yet_run             one faint dot ON the baseline + hover target
  not_in_schedule         the same faint dot -- no run was ever planned
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR

# The real per-cell geometry, not a local copy: these tests are about what
# the shipped report actually draws, so a floor that got switched off in
# report.py must fail here rather than pass against a fixture.
CELL_GEOMETRY = report.CELL_CHART_GEOMETRY


def place(bar: report.Bar) -> report.PlacedBar:
    return report.PlacedBar(group_label="sonnet", bar=bar, x=100.0, width=20.0)


def absent(state: str, **kw: object) -> report.PlacedBar:
    return place(
        report.Bar(
            slot="do-in-steps",
            present=False,
            absence=report.AbsenceMark(state=state, reason="a stated reason", **kw),
        )
    )


class MeasuredZeroIsVisibleTests(unittest.TestCase):
    def test_a_measured_zero_draws_a_filled_mark_in_the_series_hue(self) -> None:
        bar = report.Bar(slot="do-in-steps", present=True, value=0.0, display="0 of 1 resolved")
        svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, "--series-2")
        self.assertIn("var(--series-2)", svg)
        # A path with an empty `d` is how a zero-height bar disappears.
        self.assertNotIn('d="" ', svg)
        self.assertIn("<path", svg)

    def test_a_measured_zero_sits_at_the_baseline_not_floating(self) -> None:
        top, height = report.floored_bar_extent(0.0, CELL_GEOMETRY, max_value=1.0)
        baseline = CELL_GEOMETRY.plot_top + CELL_GEOMETRY.plot_height
        self.assertEqual(height, CELL_GEOMETRY.min_measured_height)
        self.assertAlmostEqual(top + height, baseline)

    def test_a_nonzero_bar_is_untouched_by_the_floor(self) -> None:
        top, height = report.floored_bar_extent(0.5, CELL_GEOMETRY, max_value=1.0)
        self.assertAlmostEqual(height, CELL_GEOMETRY.plot_height / 2)

    def test_the_aggregation_charts_keep_their_original_zero_behaviour(self) -> None:
        # Default geometry has no floor, so the two pre-existing charts render
        # byte-for-byte as before -- their zero bars are made visible by the
        # Wilson whisker they carry, which the single-trial cells do not have.
        default = report.ChartGeometry()
        self.assertEqual(default.min_measured_height, 0.0)
        top, height = report.floored_bar_extent(0.0, default, max_value=1.0)
        self.assertEqual(height, 0.0)

    def test_a_measured_zero_labels_itself_by_count_in_its_tooltip(self) -> None:
        bar = report.Bar(slot="do-in-steps", present=True, value=0.0, display="0 of 1 resolved")
        svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, "--series-1")
        self.assertIn("0 of 1 resolved", svg)
        self.assertNotIn("0%", svg)


class AbsenceMarkRenderingTests(unittest.TestCase):
    def test_each_cannot_state_draws_a_hatched_slot_with_its_own_glyph(self) -> None:
        for state in ("deliberately_skipped", "structurally_impossible", "technical_failure"):
            with self.subTest(state=state):
                svg = report.render_bar_mark(absent(state), CELL_GEOMETRY, "--series-1")
                self.assertIn(report.ABSENCE_HATCH_URL, svg)
                self.assertIn(report.ABSENCE_GLYPHS[state], svg)

    def test_an_absence_never_borrows_the_categorical_series_hue(self) -> None:
        # Hue means "this is a measurement". An absence that borrowed one
        # would be indistinguishable from a very short bar.
        for state in report.ABSENCE_GLYPHS:
            with self.subTest(state=state):
                svg = report.render_bar_mark(absent(state), CELL_GEOMETRY, "--series-2")
                self.assertNotIn("var(--series-2)", svg)

    def test_an_absent_slot_spans_the_full_plot_height(self) -> None:
        # A partial-height hatch would read as a value on the y axis. A slot
        # that touches the top of the plot cannot be read as a quantity.
        svg = report.render_bar_mark(absent("deliberately_skipped"), CELL_GEOMETRY, None)
        self.assertIn(f'y="{CELL_GEOMETRY.plot_top:.1f}"', svg)
        self.assertIn(f'height="{CELL_GEOMETRY.plot_height:.1f}"', svg)

    def test_not_yet_run_draws_no_bar_and_no_hatch(self) -> None:
        # Minimal ink, but nothing that could be read as a quantity or as a
        # finding: no bar path, no hatched slot, no glyph.
        svg = report.render_bar_mark(absent("not_yet_run"), CELL_GEOMETRY, "--series-1")
        self.assertNotIn(report.ABSENCE_HATCH_URL, svg)
        self.assertNotIn("<path", svg)
        self.assertNotIn("<text", svg)

    def test_not_yet_run_draws_one_faint_dot_on_the_baseline(self) -> None:
        # The legend advertises a swatch for this state; a legend entry with
        # nothing drawn to match it is a promise the chart does not keep, and
        # a printed chart could not tell "awaiting a run" from empty paper.
        svg = report.render_bar_mark(absent("not_yet_run"), CELL_GEOMETRY, "--series-1")
        self.assertIn('class="absence-dot"', svg)
        baseline_y = CELL_GEOMETRY.plot_top + CELL_GEOMETRY.plot_height
        self.assertIn(f'cy="{baseline_y:.1f}"', svg)

    def test_the_faint_dot_never_borrows_a_series_hue(self) -> None:
        # Hue is this report's signal for "this is a measurement".
        svg = report.render_bar_mark(absent("not_yet_run"), CELL_GEOMETRY, "--series-1")
        self.assertNotIn("var(--series-1)", svg)

    def test_an_unscheduled_slot_is_not_labelled_not_yet_run(self) -> None:
        # "not yet run" is defined as runnable-and-pending. A combination
        # schedule.yaml never planned is not pending; it was never planned.
        mark = report.absence_mark_for_cell(None)
        self.assertEqual(mark.state, report.NOT_IN_SCHEDULE_STATE)
        self.assertNotEqual(mark.state, report.NOT_YET_RUN_STATE)
        self.assertEqual(report.ABSENCE_LABELS[mark.state], "not in schedule.yaml")

    def test_not_yet_run_is_still_reachable_on_hover(self) -> None:
        # Nearly invisible, but not unexplained: the slot keeps a transparent
        # full-height hover target so a reader can ask what happened there.
        svg = report.render_bar_mark(absent("not_yet_run"), CELL_GEOMETRY, "--series-1")
        self.assertIn("<title>", svg)
        self.assertIn('fill="transparent"', svg)

    def test_every_absence_tooltip_names_its_state_and_its_reason(self) -> None:
        for state in report.ABSENCE_LABELS:
            with self.subTest(state=state):
                svg = report.render_bar_mark(absent(state), CELL_GEOMETRY, "--series-1")
                self.assertIn(report.ABSENCE_LABELS[state], svg)
                self.assertIn("a stated reason", svg)

    def test_a_collapsed_cell_names_the_model_that_holds_its_measurement(self) -> None:
        placed = absent("structurally_impossible", collapses_onto_model="sonnet")
        svg = report.render_bar_mark(placed, CELL_GEOMETRY, "--series-1")
        self.assertIn("same measurement", svg)
        self.assertIn("sonnet", svg)

    def test_an_absent_bar_with_no_mark_still_draws_nothing(self) -> None:
        # The empty official slot inside each model group: no data, and no
        # story to tell about it either.
        placed = place(report.Bar(slot="official", present=False, outlined=True))
        self.assertEqual(report.render_bar_mark(placed, CELL_GEOMETRY, None), "")


class WhiskerNullGuardTests(unittest.TestCase):
    """A whisker grown from a null bound is a fabricated confidence claim.
    Every measured cell in the current results.json has null bounds."""

    def test_no_whisker_is_drawn_when_both_bounds_are_null(self) -> None:
        bar = report.Bar(
            slot="do-in-steps", present=True, value=1.0, ci_low=None, ci_high=None, display="1 of 1 resolved"
        )
        svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, "--series-1")
        self.assertNotIn("whisker", svg)

    def test_no_whisker_is_drawn_when_only_one_bound_is_null(self) -> None:
        for low, high in ((None, 0.9), (0.1, None)):
            with self.subTest(low=low, high=high):
                bar = report.Bar(
                    slot="s", present=True, value=0.5, ci_low=low, ci_high=high, display="50%"
                )
                svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, "--series-1")
                self.assertNotIn("whisker", svg)

    def test_a_whisker_appears_only_when_both_bounds_are_real(self) -> None:
        bar = report.Bar(slot="s", present=True, value=0.5, ci_low=0.2, ci_high=0.8, display="50%")
        svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, "--series-1")
        self.assertIn("whisker", svg)

    def test_a_fable5_bar_carries_no_bounds_to_draw_in_the_first_place(self) -> None:
        baseline = {
            "fable5": {
                "available": True,
                "per_task": {
                    "t": {
                        "present_on_site": True,
                        "all_efforts_pooled": {
                            "pass_at_1": {
                                "value": 0.65, "n_numerator": 13, "n_denominator": 20,
                                "interval_low": None, "interval_high": None,
                            }
                        },
                    }
                },
            }
        }
        bar = report.fable5_pass_bar(baseline, ["t"])
        self.assertIsNone(bar.ci_low)
        self.assertIsNone(bar.ci_high)
        svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, None)
        self.assertNotIn("whisker", svg)

    def test_a_fable5_bar_is_outlined_and_labelled_by_count(self) -> None:
        bar = report.Bar(
            slot="official", present=True, outlined=True, value=0.65, display="13/20"
        )
        svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, None)
        self.assertIn("var(--official-outline)", svg)
        self.assertIn("13/20", svg)
        self.assertNotIn("65%", svg)


class NoBareRateFallbackTests(unittest.TestCase):
    """Fix 1: there is no percentage fallback left in `render_bar_mark` for a
    present bar with no `display` text -- that path must be unreachable, not
    merely unused. Every real Bar constructor is covered by its own tests
    (`_arm_bar`/`_official_bar` in test_report_bars.py); this class pins the
    render function's OWN half of the contract: a hypothetical future
    constructor that forgets `display` fails loudly here instead of quietly
    reintroducing a bare "0%"/"65%" rate on the two aggregation charts.
    """

    def test_a_present_bar_with_no_display_text_is_a_programming_error(self) -> None:
        bar = report.Bar(slot="s", present=True, value=0.65)
        with self.assertRaises(AssertionError):
            report.render_bar_mark(place(bar), CELL_GEOMETRY, "--series-1")

    def test_the_percentage_fallback_string_is_gone_from_the_source(self) -> None:
        # Belt-and-suspenders on the exact defect report.py:1949 named: the
        # `f"{bar.value * 100:.0f}%"` fallback expression must not exist
        # anywhere in this file, not just be unreachable from one call site.
        import inspect

        source = inspect.getsource(report)
        self.assertNotIn("bar.value * 100:.0f", source)


class AbsoluteAxisRenderingTests(unittest.TestCase):
    def test_a_cost_bar_is_scaled_against_the_charts_own_maximum(self) -> None:
        bar = report.Bar(slot="s", present=True, value=18.0, display="$18.00")
        svg = report.render_bar_mark(place(bar), CELL_GEOMETRY, "--series-1", max_value=36.0)
        top, _ = report.floored_bar_extent(18.0, CELL_GEOMETRY, max_value=36.0)
        # Half the axis: exactly the vertical midpoint of the plot.
        self.assertAlmostEqual(top, CELL_GEOMETRY.plot_top + CELL_GEOMETRY.plot_height / 2)
        self.assertIn("$18.00", svg)

    def test_absolute_axis_ticks_are_formatted_in_the_charts_own_units(self) -> None:
        ticks = report.y_axis_value_ticks(CELL_GEOMETRY, 36.0, report.format_usd)
        labels = [label for _, label in ticks]
        self.assertIn("$36.00", labels)
        self.assertIn("$0.00", labels)

    def test_percentage_ticks_are_untouched_for_proportion_charts(self) -> None:
        labels = [label for _, label in report.y_axis_ticks(CELL_GEOMETRY)]
        self.assertEqual(labels, ["0%", "25%", "50%", "75%", "100%"])


class ComplexityChartRenderingTests(unittest.TestCase):
    def _series(self, *, single: bool) -> report.ComplexitySeries:
        return report.ComplexitySeries(
            model="sonnet",
            skill="do-in-steps",
            points=tuple(
                report.ComplexityPoint(
                    complexity_rank=rank, complexity=name, value=0.5,
                    n_resolved=1, n_attempts=1 if single else 4,
                    is_single_trial=single, label=f"{name}: counted",
                )
                for rank, name in enumerate(("low", "medium"))
            ),
        )

    def test_markers_are_drawn_for_every_point(self) -> None:
        svg = report.render_complexity_chart_svg(
            [self._series(single=True)], CELL_GEOMETRY,
            {"do-in-steps": "--series-3"}, {"sonnet": "square"}, ["low", "medium"],
        )
        # One square marker per point, both in the skill's hue.
        self.assertEqual(svg.count('fill="var(--series-3)"'), 2)

    def test_a_single_trial_series_is_connected_provisionally(self) -> None:
        # The line is drawn -- it was requested -- but dashed and faded, so
        # it reads as a reading aid rather than as an asserted trend.
        svg = report.render_complexity_chart_svg(
            [self._series(single=True)], CELL_GEOMETRY,
            {"do-in-steps": "--series-3"}, {"sonnet": "square"}, ["low", "medium"],
        )
        self.assertIn("connector-provisional", svg)
        self.assertIn('stroke-dasharray="4 3"', svg)

    def test_a_replicated_series_is_connected_solidly(self) -> None:
        svg = report.render_complexity_chart_svg(
            [self._series(single=False)], CELL_GEOMETRY,
            {"do-in-steps": "--series-3"}, {"sonnet": "square"}, ["low", "medium"],
        )
        self.assertIn("connector-solid", svg)
        self.assertNotIn("stroke-dasharray", svg)

    def test_an_empty_chart_says_so_rather_than_rendering_an_empty_frame(self) -> None:
        svg = report.render_complexity_chart_svg(
            [], CELL_GEOMETRY, {}, {}, ["low", "medium", "high"]
        )
        self.assertIn("empty-state", svg)


class LegendMatchesWhatIsDrawnTests(unittest.TestCase):
    """A legend entry with nothing on the chart to match it to is worse than
    no entry -- and for a whole release the blank swatch was exactly that."""

    def _absent_groups(self, state: str) -> list[report.ChartGroup]:
        return [
            report.ChartGroup(
                label="haiku",
                bars=(
                    report.Bar(slot="official", present=False, outlined=True),
                    report.Bar(
                        slot="do-in-steps",
                        present=False,
                        absence=report.AbsenceMark(state=state, reason="a stated reason"),
                    ),
                ),
            )
        ]

    def test_the_blank_swatch_shows_the_same_dot_the_chart_draws(self) -> None:
        legend = report.render_legend(
            {}, include_official=False, absence_states=(report.NOT_YET_RUN_STATE,)
        )
        self.assertIn("swatch-blank", legend)
        self.assertIn("swatch-dot", legend)

    def test_every_legended_absence_state_draws_some_ink(self) -> None:
        for state in report.ABSENCE_LABELS:
            with self.subTest(state=state):
                svg = report.render_bar_mark(absent(state), CELL_GEOMETRY, "--series-1")
                inked = report.ABSENCE_HATCH_URL in svg or 'class="absence-dot"' in svg
                self.assertTrue(inked, f"{state} draws nothing a reader can see")

    def test_an_unscheduled_slot_is_explained_by_its_chart_legend(self) -> None:
        # `not_in_schedule` is absent from CELL_STATE_REPORT_ORDER on
        # purpose, so the legend has to read a wider order or the state would
        # be drawn and never explained.
        groups = self._absent_groups(report.NOT_IN_SCHEDULE_STATE)
        self.assertEqual(
            report.drawn_absence_states(groups), (report.NOT_IN_SCHEDULE_STATE,)
        )
        legend = report.render_legend(
            {}, include_official=False, absence_states=report.drawn_absence_states(groups)
        )
        self.assertIn("not in schedule.yaml", legend)


class FlooredBarIsDisclosedOnThePageTests(unittest.TestCase):
    """The floor makes a true 0.0 and a very small non-zero value pixel-
    identical. That is a defensible trade, but only if the reader is told --
    and a comment in report.py is not telling the reader."""

    def setUp(self) -> None:
        import datetime
        import json

        from .report_fixtures import load_real_leaderboard

        results = json.loads((BENCHMARK_DIR / "results.json").read_text())
        self.page = report.build_report_html(
            results, load_real_leaderboard(), generated_at=datetime.datetime(2026, 1, 1)
        )

    def test_the_floor_is_still_on_for_the_per_cell_charts(self) -> None:
        # The premise of the disclosure: if the floor were off, a measured
        # 0.0 would vanish and this note would be describing nothing.
        self.assertGreater(report.CELL_CHART_GEOMETRY.min_measured_height, 0.0)

    def test_a_reader_who_never_hovers_is_told_what_a_floored_bar_means(self) -> None:
        self.assertIn("measured and very small", self.page)
        self.assertIn("rather than necessarily zero", self.page)

    def test_the_disclosure_rides_the_cost_and_token_footnotes(self) -> None:
        # The cost axis is where the ambiguity actually bites: a $0.14 cell
        # against a $35 axis floors to the same height as a real zero.
        cost = self.page[self.page.index("cost per attempt") :]
        cost = cost[: cost.index("</figure>")]
        self.assertIn("measured and very small", cost)

    def test_the_disclosure_rides_the_pass_at_1_footnotes_too(self) -> None:
        band = self.page[self.page.index("low complexity") :]
        band = band[: band.index("</figure>")]
        self.assertIn("measured and very small", band)


class AllCellsAbsentEmptyStateTests(unittest.TestCase):
    """Fix 3: an all-absent per-task/per-complexity figure gets a summary
    line above it, instead of reading as a rendering bug (a wall of hatched
    marks with nothing saying why)."""

    def _absent_group(self, label: str, state: str) -> report.ChartGroup:
        return report.ChartGroup(
            label=label,
            bars=(
                report.Bar(slot="official", present=False, outlined=True),
                report.Bar(
                    slot="do-in-steps",
                    present=False,
                    absence=report.AbsenceMark(state=state, reason="a stated reason"),
                ),
            ),
        )

    def test_true_when_every_schedule_cell_bar_is_absent(self) -> None:
        groups = [self._absent_group("haiku", "not_yet_run")]
        self.assertTrue(report.all_cells_absent(groups))

    def test_false_when_any_schedule_cell_bar_is_present(self) -> None:
        groups = [
            self._absent_group("haiku", "not_yet_run"),
            report.ChartGroup(
                label="opus",
                bars=(report.Bar(slot="do-in-steps", present=True, value=1.0, display="1 of 1 resolved"),),
            ),
        ]
        self.assertFalse(report.all_cells_absent(groups))

    def test_false_for_no_groups_at_all(self) -> None:
        # `render_chart_svg`'s own "No arms recorded" branch already covers
        # this case; `all_cells_absent` must not also claim it.
        self.assertFalse(report.all_cells_absent([]))

    def test_an_official_bar_being_present_does_not_count_as_a_measured_cell(self) -> None:
        # The Fable 5/official bar comes from a different source entirely
        # (the vendored leaderboard snapshot) and can carry data even when
        # this harness has not run a single trial for the task -- exactly
        # `kombu-single-active-consumer-priority`'s current state. Counting
        # it as "measured" would hide the empty state this test guards.
        groups = [
            self._absent_group("haiku", "not_yet_run"),
            report.ChartGroup(
                label="Fable 5",
                bars=(report.Bar(slot="official", present=True, value=0.65, display="13/20", outlined=True),),
            ),
        ]
        self.assertTrue(report.all_cells_absent(groups))

    def test_the_note_names_the_absence_breakdown_it_actually_has(self) -> None:
        groups = [
            self._absent_group("haiku", "not_yet_run"),
            self._absent_group("sonnet", "deliberately_skipped"),
        ]
        note = report.empty_cell_chart_note(groups)
        self.assertIn("2", note)  # total absent schedule-cell bars
        self.assertIn(report.ABSENCE_LABELS["not_yet_run"], note)
        self.assertIn(report.ABSENCE_LABELS["deliberately_skipped"], note)

    def test_figure_prepends_the_empty_state_paragraph_when_all_absent(self) -> None:
        groups = [self._absent_group("haiku", "not_yet_run")]
        figure = report.render_cell_chart_figure("title", "caption", groups, {})
        self.assertTrue(figure.startswith("<p class='empty-state'>"))
        self.assertIn("<figure", figure)

    def test_figure_carries_no_empty_state_paragraph_once_something_is_measured(self) -> None:
        groups = [
            report.ChartGroup(
                label="opus",
                bars=(report.Bar(slot="do-in-steps", present=True, value=1.0, display="1 of 1 resolved"),),
            )
        ]
        figure = report.render_cell_chart_figure("title", "caption", groups, {})
        self.assertNotIn("empty-state", figure)
        self.assertTrue(figure.startswith("<figure"))


class RealKombuTaskHasNoMeasuredCellsYetTests(unittest.TestCase):
    """The real, shipped `results.json` has exactly one task with zero
    measured cells: `kombu-single-active-consumer-priority` (schedule.yaml's
    sole high-complexity task, and sonnet is skipped for it entirely). This
    pins Fix 3 against that real regression, not just synthetic groups.
    """

    def setUp(self) -> None:
        import datetime
        import json

        from .report_fixtures import load_real_leaderboard

        results = json.loads((BENCHMARK_DIR / "results.json").read_text())
        self.page = report.build_report_html(
            results, load_real_leaderboard(), generated_at=datetime.datetime(2026, 1, 1)
        )

    def _section(self, start_heading: str, end_heading: str) -> str:
        start = self.page.index(start_heading)
        end = self.page.index(end_heading, start)
        return self.page[start:end]

    def test_kombus_cost_and_token_charts_both_carry_the_empty_state(self) -> None:
        section = self._section("<h3>kombu-single-active-consumer-priority", "<h3>bandit")
        self.assertEqual(section.count("empty-state"), 2)  # cost chart + token chart

    def test_the_high_complexity_chart_carries_the_empty_state_too(self) -> None:
        # kombu is schedule.yaml's only high-complexity task, so the
        # high-complexity Pass@1 chart is entirely kombu's own unmeasured
        # cells -- the third of "the three kombu ones". The empty-state
        # paragraph is emitted ABOVE the <figure>, so look just BEFORE this
        # figure's own caption rather than forward from it.
        idx = self.page.index("high complexity — pass@1")
        preceding = self.page[max(0, idx - 300) : idx]
        self.assertIn("empty-state", preceding)

    def test_a_task_with_measured_cells_carries_no_empty_state(self) -> None:
        # abs-stepped-slices (low complexity) has real measured cells in the
        # shipped results.json -- its section must not falsely claim "no
        # cell here has been measured yet".
        section = self._section("<h3>abs-stepped-slices", "<h3>cattrs")
        self.assertNotIn("empty-state", section)


if __name__ == "__main__":
    unittest.main()
