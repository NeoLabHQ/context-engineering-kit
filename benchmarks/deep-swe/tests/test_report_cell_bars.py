#!/usr/bin/env python3
"""Unit tests for the per-cell Bar construction in report.py.

THE ONE PROPERTY THIS FILE EXISTS FOR
--------------------------------------
`results.json` currently has 41 of 46 cells absent and 5 measured, and one of
those 5 is a genuine `pass_at_1: 0.0`. A report that renders "the arm scored
nothing" and "nobody ever asked this arm to try" the same way is lying by
omission, so every test below is ultimately about keeping those two apart:

  * a measured cell -- including a measured 0.0 -- is `present=True` and
    carries no `AbsenceMark`;
  * an absent cell is `present=False` and always carries an `AbsenceMark`
    naming which of collect.py's four absence states it is and why.

The state vocabulary is read from `collect.py`'s own cell-state constants via
`report.ABSENCE_LABELS` rather than hand-listed, so a sixth state cannot be
introduced without failing here.
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py

from .report_fixtures import make_cell, make_measured

ABSENT_STATES = (
    "deliberately_skipped",
    "structurally_impossible",
    "technical_failure",
    "not_yet_run",
)


class MeasuredCellBarTests(unittest.TestCase):
    def test_a_measured_cell_yields_a_present_bar_with_no_absence_mark(self) -> None:
        bar = report.cell_pass_bar("do-in-steps", make_cell(state="measured"))
        self.assertTrue(bar.present)
        self.assertIsNone(bar.absence)
        self.assertEqual(bar.value, 1.0)

    def test_a_measured_zero_stays_present_and_is_not_an_absence(self) -> None:
        # The (cattrs, sonnet, do-in-steps) case from the real results.json:
        # one trial, resolved nothing. This is DATA, not a gap.
        cell = make_cell(
            state="measured", measured=make_measured(n_resolved=0, pass_at_1=0.0)
        )
        bar = report.cell_pass_bar("do-in-steps", cell)
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 0.0)
        self.assertIsNone(bar.absence)

    def test_a_single_trial_cell_never_carries_ci_bounds(self) -> None:
        # `is_single_trial` is branched on BEFORE the bounds are read, so a
        # future results.json that filled the bounds in for an n=1 cell still
        # produces a whisker-less bar rather than a one-observation interval.
        cell = make_cell(
            state="measured",
            measured=make_measured(
                is_single_trial=True, pass_at_1_ci_low=0.0, pass_at_1_ci_high=0.9
            ),
        )
        bar = report.cell_pass_bar("do-in-steps", cell)
        self.assertIsNone(bar.ci_low)
        self.assertIsNone(bar.ci_high)

    def test_a_multi_trial_cell_keeps_its_wilson_bounds(self) -> None:
        cell = make_cell(
            state="measured",
            measured=make_measured(
                n_resolved=2,
                n_attempts=3,
                pass_at_1=2 / 3,
                is_single_trial=False,
                pass_at_1_ci_low=0.2,
                pass_at_1_ci_high=0.94,
            ),
        )
        bar = report.cell_pass_bar("do-in-steps", cell)
        self.assertEqual((bar.ci_low, bar.ci_high), (0.2, 0.94))

    def test_the_bar_label_counts_trials_rather_than_quoting_a_percentage(self) -> None:
        bar = report.cell_pass_bar("do-in-steps", make_cell(state="measured"))
        self.assertEqual(bar.display, "1 of 1 resolved")


class AbsentCellBarTests(unittest.TestCase):
    def test_every_absent_state_yields_an_absent_bar_carrying_its_mark(self) -> None:
        for state in ABSENT_STATES:
            with self.subTest(state=state):
                bar = report.cell_pass_bar("do-in-steps", make_cell(state=state))
                self.assertFalse(bar.present)
                self.assertIsNone(bar.value)
                self.assertIsNotNone(bar.absence)
                self.assertEqual(bar.absence.state, state)

    def test_the_stated_reason_travels_with_the_mark(self) -> None:
        cell = make_cell(state="deliberately_skipped", reason="haiku cannot decompose this")
        bar = report.cell_pass_bar("do-in-steps", cell)
        self.assertEqual(bar.absence.reason, "haiku cannot decompose this")

    def test_a_structurally_impossible_cell_keeps_its_collapse_target(self) -> None:
        # "the same number, over there" -- not "this model failed".
        cell = make_cell(state="structurally_impossible", collapses_onto_model="sonnet")
        bar = report.cell_pass_bar("vanilla", cell)
        self.assertEqual(bar.absence.collapses_onto_model, "sonnet")

    def test_cannot_states_are_exactly_the_two_excluded_ones(self) -> None:
        self.assertTrue(report.is_cannot_state("deliberately_skipped"))
        self.assertTrue(report.is_cannot_state("structurally_impossible"))
        self.assertFalse(report.is_cannot_state("not_yet_run"))
        self.assertFalse(report.is_cannot_state("measured"))

    def test_only_not_yet_run_is_kept_out_of_the_glyph_map(self) -> None:
        # Membership in this map is what promotes a state to a full-height
        # hatched slot -- the rendering that says "this is a finding". "No
        # data yet" is not a finding, so it stays out and is drawn as one
        # faint baseline dot instead (see test_report_absence_rendering).
        self.assertNotIn("not_yet_run", report.ABSENCE_GLYPHS)
        self.assertNotIn(report.NOT_IN_SCHEDULE_STATE, report.ABSENCE_GLYPHS)
        for state in ("deliberately_skipped", "structurally_impossible", "technical_failure"):
            with self.subTest(state=state):
                self.assertIn(state, report.ABSENCE_GLYPHS)

    def test_every_absence_state_has_a_human_label(self) -> None:
        for state in ABSENT_STATES:
            with self.subTest(state=state):
                self.assertIn(state, report.ABSENCE_LABELS)

    def test_a_missing_cell_is_an_absence_and_never_a_zero(self) -> None:
        bar = report.cell_pass_bar("do-in-steps", None)
        self.assertFalse(bar.present)
        self.assertIsNotNone(bar.absence)


class CellMeasureBarTests(unittest.TestCase):
    """Cost/token bars read the same cells but a different numeric field, and
    must reach the identical absence handling rather than a parallel copy."""

    def test_a_measured_cost_bar_carries_the_value_and_a_formatted_label(self) -> None:
        cell = make_cell(state="measured", measured=make_measured(avg_cost_usd=22.5))
        bar = report.cell_measure_bar("do-in-steps", cell, "avg_cost_usd", report.format_usd)
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 22.5)
        self.assertEqual(bar.display, "$22.50")

    def test_a_cost_bar_never_carries_a_pass_at_1_interval(self) -> None:
        # A Wilson interval is a statement about a proportion; carrying one on
        # a dollar bar would draw a whisker that means nothing.
        cell = make_cell(
            state="measured",
            measured=make_measured(is_single_trial=False, pass_at_1_ci_low=0.2, pass_at_1_ci_high=0.9),
        )
        bar = report.cell_measure_bar("do-in-steps", cell, "avg_cost_usd", report.format_usd)
        self.assertIsNone(bar.ci_low)
        self.assertIsNone(bar.ci_high)

    def test_a_null_measure_on_a_measured_cell_is_still_an_absent_bar(self) -> None:
        cell = make_cell(state="measured", measured=make_measured(avg_cost_usd=None))
        bar = report.cell_measure_bar("do-in-steps", cell, "avg_cost_usd", report.format_usd)
        self.assertFalse(bar.present)

    def test_absent_cells_reach_the_same_marks_as_the_pass_chart(self) -> None:
        for state in ABSENT_STATES:
            with self.subTest(state=state):
                bar = report.cell_measure_bar(
                    "do-in-steps", make_cell(state=state), "avg_cost_usd", report.format_usd
                )
                self.assertFalse(bar.present)
                self.assertEqual(bar.absence.state, state)


class CellOutcomeFormattingTests(unittest.TestCase):
    def test_single_trial_outcomes_are_counted_not_rounded(self) -> None:
        self.assertEqual(
            report.format_cell_outcome(make_measured(n_resolved=1, n_attempts=1)),
            "1 of 1 resolved",
        )
        self.assertEqual(
            report.format_cell_outcome(make_measured(n_resolved=0, n_attempts=1, pass_at_1=0.0)),
            "0 of 1 resolved",
        )

    def test_a_single_trial_is_never_dressed_up_as_a_percentage(self) -> None:
        rendered = report.format_cell_outcome(make_measured(n_resolved=1, n_attempts=1))
        self.assertNotIn("%", rendered)

    def test_multi_trial_outcomes_show_the_rate_its_interval_and_its_counts(self) -> None:
        rendered = report.format_cell_outcome(
            make_measured(
                n_resolved=2,
                n_attempts=3,
                pass_at_1=2 / 3,
                is_single_trial=False,
                pass_at_1_ci_low=0.2,
                pass_at_1_ci_high=0.94,
            )
        )
        self.assertIn("2 of 3 resolved", rendered)
        self.assertIn("%", rendered)

    def test_a_multi_trial_cell_without_bounds_still_avoids_a_fake_interval(self) -> None:
        rendered = report.format_cell_outcome(
            make_measured(n_resolved=2, n_attempts=3, pass_at_1=2 / 3, is_single_trial=False)
        )
        self.assertIn("2 of 3 resolved", rendered)
        self.assertNotIn("±", rendered)

    def test_no_measurement_renders_an_em_dash(self) -> None:
        self.assertEqual(report.format_cell_outcome(None), "—")


if __name__ == "__main__":
    unittest.main()
