#!/usr/bin/env python3
"""Unit tests for report.py's chart-group assembly: `build_matched_chart_groups`,
`build_mixed_chart_groups` -- uses the real vendored leaderboard so the
present/absent-tier behavior is checked against real data (haiku is
genuinely absent; sonnet/opus are genuinely present).
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py

from .report_fixtures import load_real_leaderboard, make_arm


class BuildChartGroupsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.leaderboard = load_real_leaderboard()

    def test_official_only_tier_still_renders_in_matched_chart(self) -> None:
        # No experimental arms at all: sonnet/opus (present on the real
        # leaderboard) must still produce a group with just the official
        # bar; haiku (absent AND no arms) must be dropped entirely.
        groups = report.build_matched_chart_groups([], self.leaderboard)
        labels = [g.label for g in groups]
        self.assertEqual(labels, ["sonnet", "opus"])
        for group in groups:
            self.assertEqual([bar.slot for bar in group.bars], ["official"])
            self.assertTrue(group.bars[0].present)

    def test_mixed_chart_drops_tiers_with_no_mixed_arms_even_if_on_leaderboard(self) -> None:
        # Unlike the matched chart, chart 2 has no "official-only" fallback
        # -- a tier with zero mixed arms is skipped outright, even though
        # sonnet/opus are on the leaderboard.
        groups = report.build_mixed_chart_groups([], self.leaderboard)
        self.assertEqual(groups, [])

    def test_vanilla_slot_included_only_when_a_vanilla_arm_exists_anywhere(self) -> None:
        skill_arm = make_arm(arm_id="a1", orchestrator="sonnet", impl="sonnet")

        without_vanilla = report.build_matched_chart_groups([skill_arm], self.leaderboard)
        sonnet_group = next(g for g in without_vanilla if g.label == "sonnet")
        self.assertNotIn("vanilla", [bar.slot for bar in sonnet_group.bars])

        vanilla_arm = make_arm(
            arm_id="v1", skill=None, impl=None, is_vanilla=True, orchestrator="sonnet"
        )
        with_vanilla = report.build_matched_chart_groups([skill_arm, vanilla_arm], self.leaderboard)
        sonnet_group = next(g for g in with_vanilla if g.label == "sonnet")
        self.assertIn("vanilla", [bar.slot for bar in sonnet_group.bars])

    def test_matched_and_mixed_bar_slots_are_never_inverted(self) -> None:
        matched_arm = make_arm(arm_id="matched-1", orchestrator="sonnet", impl="sonnet")
        mixed_arm = make_arm(
            arm_id="mixed-1", skill="skill-b", orchestrator="sonnet", impl="opus"
        )
        arms = [matched_arm, mixed_arm]

        matched_groups = report.build_matched_chart_groups(arms, self.leaderboard)
        mixed_groups = report.build_mixed_chart_groups(arms, self.leaderboard)

        matched_sonnet = next(g for g in matched_groups if g.label == "sonnet")
        mixed_sonnet = next(g for g in mixed_groups if g.label == "sonnet")

        self.assertIn("skill-a", [bar.slot for bar in matched_sonnet.bars])
        self.assertNotIn("skill-b", [bar.slot for bar in matched_sonnet.bars])
        self.assertIn("skill-b", [bar.slot for bar in mixed_sonnet.bars])
        self.assertNotIn("skill-a", [bar.slot for bar in mixed_sonnet.bars])


if __name__ == "__main__":
    unittest.main()
