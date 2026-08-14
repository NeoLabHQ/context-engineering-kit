#!/usr/bin/env python3
"""Unit tests for report.py's Bar construction: `_official_bar`, `_arm_bar`
-- the single place that normalizes every "no data" case (missing tier,
missing arm, zero-attempt arm) into the same `present=False` Bar, while
keeping a genuine zero measurement `present=True`.
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py

from .report_fixtures import load_real_leaderboard, make_arm


class OfficialBarTests(unittest.TestCase):
    """Uses the real vendored `data/leaderboard.json`, where haiku is
    genuinely absent and sonnet/opus are genuinely present -- exercising
    `_official_bar` against real data rather than a synthetic stand-in that
    could quietly diverge from what ships.
    """

    def setUp(self) -> None:
        self.leaderboard = load_real_leaderboard()

    def test_tier_present_on_leaderboard_yields_a_present_outlined_bar(self) -> None:
        bar = report._official_bar("sonnet", self.leaderboard)
        self.assertTrue(bar.present)
        self.assertTrue(bar.outlined)
        self.assertEqual(bar.value, self.leaderboard["tiers"]["sonnet"]["pass_at_1"])

    def test_tier_absent_from_leaderboard_yields_an_absent_bar(self) -> None:
        # haiku has present_on_leaderboard=false in the real snapshot.
        bar = report._official_bar("haiku", self.leaderboard)
        self.assertFalse(bar.present)
        self.assertTrue(bar.outlined)  # still "the official slot", just empty
        self.assertIsNone(bar.value)

    def test_tier_not_mentioned_at_all_yields_an_absent_bar(self) -> None:
        bar = report._official_bar("some-future-tier", self.leaderboard)
        self.assertFalse(bar.present)


class ArmBarTests(unittest.TestCase):
    def test_present_arm_with_data_yields_a_present_bar(self) -> None:
        arm = make_arm(pass_at_1=0.5)
        bar = report._arm_bar("skill-a", arm)
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 0.5)

    def test_missing_arm_yields_an_absent_bar(self) -> None:
        bar = report._arm_bar("skill-a", None)
        self.assertFalse(bar.present)

    def test_zero_attempt_arm_with_null_pass_at_1_yields_an_absent_bar(self) -> None:
        # collect.py sets pass_at_1=None (not 0.0) for a zero-attempt arm --
        # this must normalize to the SAME absent Bar as "arm never existed",
        # not a zero-height bar.
        zero_attempt_arm = make_arm(
            pass_at_1=None, pass_at_1_ci_low=None, pass_at_1_ci_high=None
        )
        bar = report._arm_bar("skill-a", zero_attempt_arm)
        self.assertFalse(bar.present)

    def test_genuine_zero_pass_at_1_yields_a_present_bar_with_value_zero(self) -> None:
        # The counterpart to the test above: pass_at_1=0.0 is a REAL
        # measurement (every attempt failed) and must render as a present,
        # zero-height bar -- never collapsed into the same "absent" case.
        genuine_zero_arm = make_arm(pass_at_1=0.0, pass_at_1_ci_low=0.0, pass_at_1_ci_high=0.3)
        bar = report._arm_bar("skill-a", genuine_zero_arm)
        self.assertTrue(bar.present)
        self.assertEqual(bar.value, 0.0)


if __name__ == "__main__":
    unittest.main()
