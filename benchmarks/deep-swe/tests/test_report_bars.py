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


class BarFieldDefaultsTests(unittest.TestCase):
    """`Bar` gained `absence` for the per-cell charts, defaulting to `None` so
    every aggregation-chart bar stays exactly the bar it built before that
    field existed -- no cell there ever knows a schedule-derived reason.

    `display`, by contrast, is now ALWAYS populated for a present bar on
    these two charts (Fix 1): `render_bar_mark` no longer has a percentage
    fallback to fall back to, so a `None` here would surface as a rendering
    crash, not a quietly-wrong "0%".
    """

    def test_an_arm_bar_carries_no_absence_mark_but_does_carry_display(self) -> None:
        bar = report._arm_bar("skill-a", make_arm())
        self.assertIsNone(bar.absence)
        self.assertEqual(
            bar.display,
            report.format_pass_at_1_with_ci(0.5, 0.4, 0.6),  # make_arm()'s defaults
        )

    def test_an_absent_arm_bar_carries_no_absence_mark(self) -> None:
        # An arm with no data has no *reason* recorded anywhere -- unlike a
        # cell, which always knows why it is empty. Inventing a mark here
        # would draw a hatched slot claiming an explanation nobody wrote.
        bar = report._arm_bar("skill-a", None)
        self.assertFalse(bar.present)
        self.assertIsNone(bar.absence)

    def test_an_official_bar_carries_no_absence_mark_but_does_carry_display(self) -> None:
        leaderboard = load_real_leaderboard()
        bar = report._official_bar("sonnet", leaderboard)
        tier_data = leaderboard["tiers"]["sonnet"]
        self.assertIsNone(bar.absence)
        self.assertEqual(
            bar.display,
            report.format_pass_at_1_with_ci(
                tier_data["pass_at_1"], tier_data["ci_low"], tier_data["ci_high"]
            ),
        )

    def test_an_official_bar_carries_no_ci_bounds(self) -> None:
        # Fix 2: leaderboard.json's own ci_low/ci_high is a run-to-run
        # standard error, not a Wilson interval -- drawing it into the same
        # whisker channel as this harness's own bars would plot two
        # different statistics as if they were peers. The real vendored
        # sonnet tier DOES carry non-null ci_low/ci_high, so this only holds
        # if `_official_bar` deliberately leaves them off the Bar it builds.
        leaderboard = load_real_leaderboard()
        tier_data = leaderboard["tiers"]["sonnet"]
        self.assertIsNotNone(tier_data["ci_low"])
        self.assertIsNotNone(tier_data["ci_high"])
        bar = report._official_bar("sonnet", leaderboard)
        self.assertIsNone(bar.ci_low)
        self.assertIsNone(bar.ci_high)


if __name__ == "__main__":
    unittest.main()
