#!/usr/bin/env python3
"""Tests for Fable 5's WHOLE-BENCHMARK figure appearing in a chart.

The brief asks for the official results "aggregated and per task ... in
charts and table" -- four placements. Three of them (aggregate-in-table,
per-task-in-chart, per-task-in-table) were already covered elsewhere; this
file covers the fourth, which was previously rendered only as text in a
definition list and appeared in no `<svg>` at all.

The placement is an ADDITION to the matched-arms aggregation chart, not a
change to it: `build_matched_chart_groups` is untouched, and
`with_fable5_aggregate_group` appends a category to whatever that builder
returned. `MatchedChartIsUntouchedTests` pins that separation, because the
one hard constraint on this work was not breaking the two pre-existing
aggregation charts.
"""

from __future__ import annotations

import json
import unittest
from typing import Any

import report  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR
from .report_fixtures import load_real_leaderboard


def real_baseline() -> dict[str, Any]:
    """The committed baseline snapshot, not a synthetic stand-in: the point
    of this chart is that the shipped page shows the shipped number."""
    return json.loads((BENCHMARK_DIR / "results.json").read_text())["baseline"]


def plain_groups() -> list[report.ChartGroup]:
    return [
        report.ChartGroup(
            label="sonnet",
            bars=(
                report.Bar(slot=report.OFFICIAL_SLOT, present=True, outlined=True, value=0.4),
                report.Bar(slot="do-in-steps", present=True, value=0.5),
            ),
        )
    ]


class AggregateBarTests(unittest.TestCase):
    def test_the_bar_carries_the_headline_k_of_n(self) -> None:
        bar = report.fable5_aggregate_bar(real_baseline())
        self.assertTrue(bar.present)
        self.assertEqual(bar.display, "304/436")
        self.assertAlmostEqual(bar.value, 304 / 436)

    def test_the_bar_is_outlined_and_never_takes_a_categorical_hue(self) -> None:
        # Hue is this report's signal for "this is one of our measurements".
        bar = report.fable5_aggregate_bar(real_baseline())
        self.assertTrue(bar.outlined)
        self.assertEqual(bar.slot, report.OFFICIAL_SLOT)

    def test_the_bar_carries_no_interval_for_the_whisker_channel(self) -> None:
        # Fable 5's interval is a run-to-run standard error across whole-
        # benchmark passes; the baseline's own
        # `co_plotting_intervals_allowed` is false, so it must never reach a
        # whisker beside this harness's Wilson bounds.
        bar = report.fable5_aggregate_bar(real_baseline())
        self.assertIsNone(bar.ci_low)
        self.assertIsNone(bar.ci_high)

    def test_the_published_interval_really_is_the_kind_that_must_not_be_plotted(self) -> None:
        # Guards the premise of the test above: if the snapshot ever stopped
        # forbidding co-plotting, the omission would need re-deciding rather
        # than silently inheriting.
        fable5 = real_baseline()["fable5"]
        self.assertFalse(fable5["comparability"]["co_plotting_intervals_allowed"])
        figure = fable5["aggregate"]["headline"]["pass_at_1"]
        self.assertIsNotNone(figure["interval_low"])
        self.assertFalse(figure["comparable_to_local_wilson_interval"])

    def test_an_unavailable_baseline_yields_an_absent_bar_not_a_zero(self) -> None:
        bar = report.fable5_aggregate_bar({"fable5": {"available": False}})
        self.assertFalse(bar.present)
        self.assertIsNone(bar.value)

    def test_a_missing_denominator_yields_an_absent_bar(self) -> None:
        baseline = {
            "fable5": {
                "available": True,
                "aggregate": {"headline": {"pass_at_1": {"n_numerator": 3, "n_denominator": 0}}},
            }
        }
        self.assertFalse(report.fable5_aggregate_bar(baseline).present)

    def test_the_chart_and_the_summary_quote_the_same_config(self) -> None:
        baseline = real_baseline()
        summary = dict(report.fable5_aggregate_summary(baseline))
        self.assertEqual(
            summary["Config"], report.fable5_aggregate_headline(baseline)["config"]
        )


class AggregateGroupTests(unittest.TestCase):
    def test_the_group_is_appended_as_its_own_x_axis_category(self) -> None:
        groups = report.with_fable5_aggregate_group(plain_groups(), real_baseline())
        self.assertEqual([g.label for g in groups], ["sonnet", report.FABLE5_GROUP_LABEL])

    def test_the_new_group_matches_the_incoming_slot_list_exactly(self) -> None:
        # `layout_chart_bars` sizes every group from `groups[0].bars`; a
        # ragged group silently mislays every bar after the first.
        groups = report.with_fable5_aggregate_group(plain_groups(), real_baseline())
        self.assertEqual(
            [bar.slot for bar in groups[-1].bars], [bar.slot for bar in groups[0].bars]
        )

    def test_every_non_official_slot_in_the_new_group_is_absent(self) -> None:
        # Fable 5 ran no claude-code skill; a present bar in a skill slot
        # there would invent one.
        groups = report.with_fable5_aggregate_group(plain_groups(), real_baseline())
        for bar in groups[-1].bars:
            if bar.slot != report.OFFICIAL_SLOT:
                with self.subTest(slot=bar.slot):
                    self.assertFalse(bar.present)

    def test_an_unavailable_baseline_adds_no_category_at_all(self) -> None:
        # Better an unchanged chart than an empty column implying a pending
        # comparison.
        original = plain_groups()
        self.assertEqual(
            report.with_fable5_aggregate_group(original, {"fable5": {"available": False}}),
            original,
        )

    def test_an_empty_chart_stays_empty(self) -> None:
        self.assertEqual(report.with_fable5_aggregate_group([], real_baseline()), [])


class MatchedChartIsUntouchedTests(unittest.TestCase):
    """The constraint: the two pre-existing aggregation charts must keep
    drawing exactly what they drew before."""

    def setUp(self) -> None:
        self.results = json.loads((BENCHMARK_DIR / "results.json").read_text())
        self.leaderboard = load_real_leaderboard()
        self.matched = report.build_matched_chart_groups(
            self.results["arms"], self.leaderboard
        )

    def test_the_builder_itself_still_returns_only_model_tiers(self) -> None:
        self.assertNotIn(
            report.FABLE5_GROUP_LABEL, [group.label for group in self.matched]
        )

    def test_every_pre_existing_bar_is_passed_through_by_identity(self) -> None:
        extended = report.with_fable5_aggregate_group(self.matched, self.results["baseline"])
        for before, after in zip(self.matched, extended, strict=False):
            with self.subTest(group=before.label):
                self.assertIs(before, after)

    def test_the_mixed_chart_is_not_given_a_fable5_category(self) -> None:
        # One figure, one place. Repeating the same whole-benchmark number on
        # a second chart would read as two independent observations.
        page = report.build_report_html(
            self.results,
            self.leaderboard,
            generated_at=__import__("datetime").datetime(2026, 1, 1),
        )
        mixed = page[page.index("Mixed arms") :]
        mixed = mixed[: mixed.index("</figure>")]
        self.assertNotIn(report.FABLE5_GROUP_LABEL, mixed)


class AggregateOnThePageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.results = json.loads((BENCHMARK_DIR / "results.json").read_text())
        self.page = report.build_report_html(
            self.results,
            load_real_leaderboard(),
            generated_at=__import__("datetime").datetime(2026, 1, 1),
        )
        matched = self.page[self.page.index("Matched arms") :]
        self.figure = matched[: matched.index("</figure>")]

    def test_the_aggregate_figure_is_inside_the_chart_not_only_in_a_table(self) -> None:
        svg = self.figure[self.figure.index("<svg") : self.figure.index("</svg>")]
        self.assertIn("304/436", svg)
        self.assertIn(report.FABLE5_GROUP_LABEL, svg)

    def test_the_chart_footnote_names_the_config_and_the_denominator_unit(self) -> None:
        self.assertIn("mini_swe_agent_claude_fable_5_max", self.figure)
        self.assertIn("scored_rollout_attempts", self.figure)

    def test_the_fable5_column_draws_no_whisker(self) -> None:
        svg = self.figure[self.figure.index("<svg") : self.figure.index("</svg>")]
        # The Fable 5 mark is the last group's bar; whiskers belong to the
        # leaderboard tier bars that precede it.
        tail = svg[svg.index("304/436") :]
        self.assertNotIn("whisker", tail)


if __name__ == "__main__":
    unittest.main()
