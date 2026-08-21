#!/usr/bin/env python3
"""Unit tests for report.py's table-row formatting: `arm_table_rows`,
`official_baseline_table_rows`.
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py

from .report_fixtures import load_real_leaderboard, make_arm


class ArmTableRowsTests(unittest.TestCase):
    def test_row_fields_are_formatted_consistently_with_the_formatting_helpers(self) -> None:
        arm = make_arm(
            arm_id="sonnet-skill-a-sonnet",
            pass_at_1=0.62,
            pass_at_1_ci_low=0.54,
            pass_at_1_ci_high=0.70,
            avg_cost_usd=12.5,
            max_cost_usd=41.0,
            avg_output_tokens=5000.0,
            avg_n_agent_steps=42.0,
            n_incomplete=2,
            n_errored=3,
        )
        rows = report.arm_table_rows([arm])
        self.assertEqual(
            rows,
            [
                {
                    "arm_id": "sonnet-skill-a-sonnet",
                    # n=12: make_arm's n_attempts is 10 + n_incomplete (Fix 1
                    # -- the attempt count is folded into this cell so a
                    # single-attempt rate can never be mistaken for one
                    # established over many tries).
                    "pass_at_1": "62% ± 8% (n=12)",
                    "avg_cost_usd": "$12.50",
                    "max_cost_usd": "$41.00",
                    "avg_output_tokens": "5,000",
                    "avg_n_agent_steps": "42",
                    # Never summed with n_errored: incomplete trials count in
                    # Pass@1's denominator, errored ones don't.
                    "n_incomplete": "2",
                    "n_errored": "3",
                }
            ],
        )

    def test_zero_attempt_arm_renders_dashes_not_zeros(self) -> None:
        arm = make_arm(
            pass_at_1=None,
            pass_at_1_ci_low=None,
            pass_at_1_ci_high=None,
            avg_cost_usd=None,
            max_cost_usd=None,
            avg_output_tokens=None,
            avg_n_agent_steps=None,
        )
        row = report.arm_table_rows([arm])[0]
        # No "(n=0)" tacked onto the dash either -- that would state the same
        # zero-attempt fact twice in two different vocabularies.
        self.assertEqual(row["pass_at_1"], "—")
        self.assertEqual(row["avg_cost_usd"], "—")
        self.assertEqual(row["max_cost_usd"], "—")

    def test_format_arm_pass_at_1_cell_appends_the_attempt_count(self) -> None:
        arm = make_arm(pass_at_1=0.0, pass_at_1_ci_low=0.0, pass_at_1_ci_high=0.4)
        self.assertEqual(
            report.format_arm_pass_at_1_cell(arm),
            f"0% ± 20% (n={arm['n_attempts']})",
        )

    def test_format_arm_pass_at_1_cell_never_appends_a_count_to_a_dash(self) -> None:
        arm = make_arm(pass_at_1=None, pass_at_1_ci_low=None, pass_at_1_ci_high=None)
        self.assertEqual(report.format_arm_pass_at_1_cell(arm), "—")


class OfficialBaselineTableRowsTests(unittest.TestCase):
    """Uses the real vendored leaderboard: haiku genuinely absent (renders
    its absence_reason), sonnet/opus genuinely present (render real
    formatted values)."""

    def setUp(self) -> None:
        self.leaderboard = load_real_leaderboard()
        self.rows_by_tier = {
            row["tier"]: row for row in report.official_baseline_table_rows(self.leaderboard)
        }

    def test_covers_every_tier_in_tier_order(self) -> None:
        self.assertEqual(set(self.rows_by_tier), {"haiku", "sonnet", "opus"})

    def test_absent_tier_renders_its_absence_reason_not_dashes_unexplained(self) -> None:
        row = self.rows_by_tier["haiku"]
        self.assertEqual(row["pass_at_1"], "—")
        self.assertEqual(
            row["note"], self.leaderboard["tiers"]["haiku"]["absence_reason"]
        )

    def test_present_tier_renders_real_formatted_values(self) -> None:
        row = self.rows_by_tier["sonnet"]
        tier_data = self.leaderboard["tiers"]["sonnet"]
        expected_pass_at_1 = report.format_pass_at_1_with_ci(
            tier_data["pass_at_1"], tier_data["ci_low"], tier_data["ci_high"]
        )
        self.assertEqual(row["pass_at_1"], expected_pass_at_1)
        self.assertNotEqual(row["pass_at_1"], "—")
        self.assertIn("reasoning_effort=", row["note"])


if __name__ == "__main__":
    unittest.main()
