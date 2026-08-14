#!/usr/bin/env python3
"""Unit tests for report.py's arm partitioning: `matched_arms_by_tier`,
`mixed_arms_by_orchestrator`, `vanilla_arm_by_tier`.
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py

from .report_fixtures import make_arm


class ArmPartitioningTests(unittest.TestCase):
    """`matched_arms_by_tier` and `mixed_arms_by_orchestrator` must partition
    non-vanilla arms with no overlap and no arm left out of both -- this
    class asserts that partition directly, both ways, so an inverted
    condition (`==` swapped for `!=`) would fail immediately.
    """

    def setUp(self) -> None:
        self.matched_sonnet = make_arm(arm_id="m-sonnet", orchestrator="sonnet", impl="sonnet")
        self.matched_opus = make_arm(arm_id="m-opus", orchestrator="opus", impl="opus")
        self.mixed_sonnet_opus = make_arm(
            arm_id="mix-sonnet-opus", orchestrator="sonnet", impl="opus"
        )
        self.vanilla_sonnet = make_arm(
            arm_id="vanilla-sonnet", skill=None, impl=None, is_vanilla=True, orchestrator="sonnet"
        )
        self.arms = [
            self.matched_sonnet,
            self.matched_opus,
            self.mixed_sonnet_opus,
            self.vanilla_sonnet,
        ]

    def test_matched_arms_grouped_by_tier_excludes_mixed_and_vanilla(self) -> None:
        matched = report.matched_arms_by_tier(self.arms)
        self.assertEqual(matched, {"sonnet": [self.matched_sonnet], "opus": [self.matched_opus]})

    def test_mixed_arms_grouped_by_orchestrator_excludes_matched_and_vanilla(self) -> None:
        mixed = report.mixed_arms_by_orchestrator(self.arms)
        self.assertEqual(mixed, {"sonnet": [self.mixed_sonnet_opus]})

    def test_matched_and_mixed_partition_is_not_inverted(self) -> None:
        matched = report.matched_arms_by_tier(self.arms)
        mixed = report.mixed_arms_by_orchestrator(self.arms)

        matched_ids = {arm["arm_id"] for arms in matched.values() for arm in arms}
        mixed_ids = {arm["arm_id"] for arms in mixed.values() for arm in arms}

        self.assertIn("m-sonnet", matched_ids)
        self.assertNotIn("m-sonnet", mixed_ids)
        self.assertIn("mix-sonnet-opus", mixed_ids)
        self.assertNotIn("mix-sonnet-opus", matched_ids)
        self.assertTrue(matched_ids.isdisjoint(mixed_ids))

    def test_groups_ordered_by_tier_capability_not_alphabetically(self) -> None:
        # TIER_ORDER is (haiku, sonnet, opus) -- alphabetical would put opus
        # before sonnet, scrambling the ascending-capability reading order.
        matched = report.matched_arms_by_tier(self.arms)
        self.assertEqual(list(matched.keys()), ["sonnet", "opus"])

    def test_vanilla_arm_by_tier_present(self) -> None:
        self.assertEqual(
            report.vanilla_arm_by_tier(self.arms), {"sonnet": self.vanilla_sonnet}
        )

    def test_vanilla_arm_by_tier_absent_is_empty_dict(self) -> None:
        no_vanilla_arms = [self.matched_sonnet, self.matched_opus, self.mixed_sonnet_opus]
        self.assertEqual(report.vanilla_arm_by_tier(no_vanilla_arms), {})


if __name__ == "__main__":
    unittest.main()
