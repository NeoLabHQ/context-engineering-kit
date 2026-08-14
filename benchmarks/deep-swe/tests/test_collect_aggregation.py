#!/usr/bin/env python3
"""Unit tests for collect.py's per-arm aggregation: `aggregate_arm`,
`aggregate_all_arms`, `group_trials_by_arm`.
"""

from __future__ import annotations

import unittest

import collect  # sys.path patched by tests/__init__.py

from .collect_fixtures import make_trial


class AggregateArmTests(unittest.TestCase):
    """Hand-constructed inputs whose Pass@1/denominator/averages are computed
    by hand in each test's comment, not by re-deriving them from
    `aggregate_arm` itself.
    """

    def test_all_errored_arm_has_null_stats_and_no_division_by_zero(self) -> None:
        trials = [
            make_trial("errored", trial_id="t1"),
            make_trial("errored", trial_id="t2"),
        ]
        agg = collect.aggregate_arm(trials)

        self.assertEqual(agg.n_resolved, 0)
        self.assertEqual(agg.n_unresolved, 0)
        self.assertEqual(agg.n_errored, 2)
        self.assertEqual(agg.n_attempts, 0)  # must not raise ZeroDivisionError
        self.assertEqual(agg.n_total_trials, 2)
        self.assertIsNone(agg.pass_at_1)
        self.assertIsNone(agg.pass_at_1_ci_low)
        self.assertIsNone(agg.pass_at_1_ci_high)
        self.assertIsNone(agg.avg_cost_usd)
        self.assertIsNone(agg.avg_output_tokens)
        self.assertIsNone(agg.avg_n_agent_steps)

    def test_genuine_zero_pass_at_1_is_distinguishable_from_null(self) -> None:
        # 2 unresolved, 0 resolved, 0 errored: n_attempts=2 (not zero), so
        # pass_at_1 is the *number* 0.0/2=0.0 -- a real measurement -- not
        # `None` the way the all-errored arm above is. A renderer that
        # conflates these two would hide a genuinely bad arm as "no data".
        trials = [
            make_trial("unresolved", trial_id="t1"),
            make_trial("unresolved", trial_id="t2"),
        ]
        agg = collect.aggregate_arm(trials)

        self.assertEqual(agg.n_attempts, 2)
        self.assertIsNotNone(agg.pass_at_1)
        self.assertEqual(agg.pass_at_1, 0.0)
        # Wilson(0, 2), independently verified against statsmodels (see
        # test_collect_wilson.py's WilsonScoreIntervalTests class docstring).
        self.assertAlmostEqual(agg.pass_at_1_ci_low, 0.0, places=12)
        self.assertAlmostEqual(agg.pass_at_1_ci_high, 0.657619772493347, places=12)

    def test_errored_trials_excluded_from_denominator_and_every_average(self) -> None:
        # 2 resolved (cost 1.0/3.0, tokens 100/300, steps 10/30) + 1 errored
        # with wildly different figures (999s) that must NOT leak into any
        # average or the Pass@1 denominator.
        trials = [
            make_trial("resolved", cost_usd=1.0, output_tokens=100, n_agent_steps=10, trial_id="t1"),
            make_trial("resolved", cost_usd=3.0, output_tokens=300, n_agent_steps=30, trial_id="t2"),
            make_trial(
                "errored", cost_usd=999.0, output_tokens=9999, n_agent_steps=999, trial_id="t3"
            ),
        ]
        agg = collect.aggregate_arm(trials)

        self.assertEqual(agg.n_attempts, 2)  # excludes the errored trial
        self.assertEqual(agg.n_total_trials, 3)
        self.assertEqual(agg.pass_at_1, 1.0)  # 2 resolved / 2 attempts
        # Wilson(2, 2), independently verified against statsmodels.
        self.assertAlmostEqual(agg.pass_at_1_ci_low, 0.342380227506653, places=12)
        self.assertAlmostEqual(agg.pass_at_1_ci_high, 1.0, places=12)
        self.assertEqual(agg.avg_cost_usd, 2.0)  # (1.0 + 3.0) / 2, not /3
        self.assertEqual(agg.avg_output_tokens, 200.0)  # (100 + 300) / 2
        self.assertEqual(agg.avg_n_agent_steps, 20.0)  # (10 + 30) / 2

    def test_original_signature_without_run_metadata_reproduces_pre_v2_behavior(self) -> None:
        # Called with exactly one positional argument, the way every pre-v2
        # caller (and pre-v2 test) does -- run_metadata must default to a
        # no-op, not raise TypeError, and created_at/sample_seed must fall
        # back to None rather than crash on a missing lookup.
        trials = [make_trial("resolved", trial_id="t1")]
        agg = collect.aggregate_arm(trials)

        self.assertIsNone(agg.created_at)
        self.assertIsNone(agg.sample_seed)

    def test_run_metadata_populates_created_at_and_sample_seed(self) -> None:
        trials = [make_trial("resolved", arm_id="arm-9", trial_id="t1")]
        run_metadata = {
            "arm-9": {"created_at": "2026-01-01T00:00:00+00:00", "sample_seed": 20260809}
        }
        agg = collect.aggregate_arm(trials, run_metadata)

        self.assertEqual(agg.created_at, "2026-01-01T00:00:00+00:00")
        self.assertEqual(agg.sample_seed, 20260809)

    def test_run_metadata_missing_this_arm_falls_back_to_none(self) -> None:
        trials = [make_trial("resolved", arm_id="arm-9", trial_id="t1")]
        run_metadata = {"some-other-arm": {"created_at": "x", "sample_seed": 1}}
        agg = collect.aggregate_arm(trials, run_metadata)

        self.assertIsNone(agg.created_at)
        self.assertIsNone(agg.sample_seed)

    def test_is_vanilla_derived_from_absent_skill(self) -> None:
        vanilla_trials = [make_trial("resolved", skill=None, trial_id="t1")]
        self.assertTrue(collect.aggregate_arm(vanilla_trials).is_vanilla)

        skilled_trials = [make_trial("resolved", skill="skill-a", trial_id="t1")]
        self.assertFalse(collect.aggregate_arm(skilled_trials).is_vanilla)


class AggregateAllArmsTests(unittest.TestCase):
    def test_original_signature_without_run_metadata_still_works(self) -> None:
        # Called with exactly one positional argument -- pre-v2 call shape.
        trials = [
            make_trial("resolved", arm_id="arm-b", trial_id="t1"),
            make_trial("resolved", arm_id="arm-a", trial_id="t2"),
        ]
        arms = collect.aggregate_all_arms(trials)

        self.assertEqual([arm.arm_id for arm in arms], ["arm-a", "arm-b"])  # sorted
        self.assertTrue(all(arm.created_at is None for arm in arms))

    def test_one_aggregate_per_distinct_arm_id(self) -> None:
        trials = [
            make_trial("resolved", arm_id="arm-a", trial_id="t1"),
            make_trial("unresolved", arm_id="arm-a", trial_id="t2"),
            make_trial("resolved", arm_id="arm-b", trial_id="t3"),
        ]
        arms = collect.aggregate_all_arms(trials)

        by_id = {arm.arm_id: arm for arm in arms}
        self.assertEqual(set(by_id), {"arm-a", "arm-b"})
        self.assertEqual(by_id["arm-a"].n_total_trials, 2)
        self.assertEqual(by_id["arm-b"].n_total_trials, 1)


class GroupTrialsByArmTests(unittest.TestCase):
    def test_groups_preserve_first_seen_arm_order(self) -> None:
        trials = [
            make_trial("resolved", arm_id="arm-b", trial_id="t1"),
            make_trial("resolved", arm_id="arm-a", trial_id="t2"),
            make_trial("resolved", arm_id="arm-b", trial_id="t3"),
        ]
        groups = collect.group_trials_by_arm(trials)

        self.assertEqual(list(groups.keys()), ["arm-b", "arm-a"])
        self.assertEqual([t.trial_id for t in groups["arm-b"]], ["t1", "t3"])


if __name__ == "__main__":
    unittest.main()
