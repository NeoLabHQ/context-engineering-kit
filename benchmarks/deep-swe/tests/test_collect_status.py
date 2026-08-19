#!/usr/bin/env python3
"""Unit tests for `collect.py`'s status/error classification:
`verifier_reports_success`, `classify_status`, `infra_error_category`,
`plugin_load_error_from_init_event`.
"""

from __future__ import annotations

import unittest

import collect  # sys.path patched by tests/__init__.py
from .collect_fixtures import (
    LEGACY_BINARY_REWARDS,
    LEGACY_BINARY_REWARDS_FAILED,
    REGRESSION_REWARDS,
    REGRESSION_REWARDS_NO_SCALAR,
    RESOLVED_REWARDS,
    RESOLVED_REWARDS_NO_SCALAR,
    UNRESOLVED_REWARDS,
)


class VerifierReportsSuccessTests(unittest.TestCase):
    """All three rules, in their documented order, against real bundle shapes.

    The whole point of these fixtures is that they are not invented: the
    verifier reports a metrics bundle whose counts (`f2p_total: 6`) are
    routinely != 1, so any rule reading every value rather than the scalar
    scores a perfect trial unresolved. Ordering is under test as much as the
    rules are -- scalar, then f2p/p2p arithmetic, then all-ones last.
    """

    def test_real_resolved_bundle_is_success(self) -> None:
        self.assertTrue(collect.verifier_reports_success(RESOLVED_REWARDS))

    def test_real_unresolved_bundle_is_not_success(self) -> None:
        self.assertFalse(collect.verifier_reports_success(UNRESOLVED_REWARDS))

    def test_scalar_reward_outranks_the_ratios_it_is_derived_from(self) -> None:
        # Precedence probe, not a shape the verifier emits: a deliberately
        # self-contradictory bundle (scalar says solved, ratios say not) to
        # prove rule 1 decides alone whenever `reward` is present.
        contradictory = {**UNRESOLVED_REWARDS, "reward": 1}
        self.assertTrue(collect.verifier_reports_success(contradictory))

    def test_float_valued_scalar_reward_is_success(self) -> None:
        # Rule 1 compares `reward == 1`, not `is 1` or `isinstance(_, int)`,
        # so a verifier emitting the scalar as a float still reads resolved.
        # Correct today and pinned here: tightening that comparison would
        # zero Pass@1 again, and nothing else in the suite would go red.
        self.assertTrue(collect.verifier_reports_success({**RESOLVED_REWARDS, "reward": 1.0}))

    def test_bundle_without_scalar_is_decided_by_f2p_and_p2p(self) -> None:
        # Rule 2. Both bundles carry `f2p_total: 6`, so the last-resort
        # all-ones rule would score BOTH False -- reaching it here would be
        # the original defect all over again.
        self.assertTrue(collect.verifier_reports_success(RESOLVED_REWARDS_NO_SCALAR))
        self.assertFalse(collect.verifier_reports_success(REGRESSION_REWARDS_NO_SCALAR))

    def test_bundle_with_neither_scalar_nor_ratios_falls_back_to_all_ones(self) -> None:
        # Rule 3, the last resort: a genuinely binary bundle from another
        # verifier, where every value really is a 0/1 verdict.
        self.assertTrue(collect.verifier_reports_success(LEGACY_BINARY_REWARDS))
        self.assertFalse(collect.verifier_reports_success(LEGACY_BINARY_REWARDS_FAILED))


class ClassifyStatusTests(unittest.TestCase):
    """Precedence order under test (collect.py's classification table):
    plugin_load_error > exception_type > missing/empty rewards > the
    verifier's success verdict > the completion gate > otherwise. Each test
    isolates one row; the precedence tests at the bottom prove a
    higher-priority signal wins even when a lower-priority one would, by
    itself, say something different.

    Every call passes `incompleteness_reason` explicitly, because
    classify_status requires it -- a completion gate with a default is a
    completion gate a caller can forget.
    """

    def test_real_resolved_bundle_is_resolved(self) -> None:
        # Guards the actual defect: f2p_total == 6 must not stop a bundle
        # whose scalar reward is 1 from classifying resolved.
        status, reason = collect.classify_status(
            exception_type=None,
            rewards=RESOLVED_REWARDS,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        self.assertEqual((status, reason), ("resolved", None))

    def test_real_unresolved_bundle_is_unresolved(self) -> None:
        status, reason = collect.classify_status(
            exception_type=None,
            rewards=UNRESOLVED_REWARDS,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        self.assertEqual((status, reason), ("unresolved", None))

    def test_regression_bundle_is_unresolved(self) -> None:
        # All fail-to-pass tests fixed but half the pass-to-pass tests broken:
        # `partial` is a high 0.75, yet the binary verdict is still 0.
        status, reason = collect.classify_status(
            exception_type=None,
            rewards=REGRESSION_REWARDS,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        self.assertEqual((status, reason), ("unresolved", None))

    def test_bundle_without_scalar_still_classifies_via_the_fallbacks(self) -> None:
        # Both fallback rules reach classify_status intact: the f2p/p2p one
        # for a DeepSWE bundle missing its scalar, the all-ones one for a
        # legacy binary bundle.
        by_ratios, _ = collect.classify_status(
            exception_type=None,
            rewards=RESOLVED_REWARDS_NO_SCALAR,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        by_all_ones, _ = collect.classify_status(
            exception_type=None,
            rewards=LEGACY_BINARY_REWARDS,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        failed, _ = collect.classify_status(
            exception_type=None,
            rewards=LEGACY_BINARY_REWARDS_FAILED,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        self.assertEqual((by_ratios, by_all_ones, failed), ("resolved", "resolved", "unresolved"))

    def test_missing_rewards_is_errored(self) -> None:
        status, reason = collect.classify_status(
            exception_type=None,
            rewards=None,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        self.assertEqual((status, reason), ("errored", "missing_verifier_rewards"))

    def test_empty_rewards_dict_is_errored(self) -> None:
        status, reason = collect.classify_status(
            exception_type=None,
            rewards={},
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        self.assertEqual((status, reason), ("errored", "missing_verifier_rewards"))

    def test_exception_type_wins_over_success_rewards(self) -> None:
        # Module docstring's worked example: claude crashes (API 529 surfaced
        # as NonZeroAgentExitCodeError) but the verifier still ran and scored
        # the trial a success. exception_info is checked before rewards, so
        # this must stay errored, never flip to resolved.
        status, reason = collect.classify_status(
            exception_type="NonZeroAgentExitCodeError",
            rewards=RESOLVED_REWARDS,
            plugin_load_error=None,
            incompleteness_reason=None,
        )
        self.assertEqual(
            (status, reason),
            ("errored", "pier_exception:agent_nonzero_exit:NonZeroAgentExitCodeError"),
        )

    def test_plugin_load_error_wins_over_exception_type_and_success_rewards(self) -> None:
        # First-match-wins precedence check requested by the task: an infra
        # signal (plugin load failure) must outrank a rewards-based verdict
        # of success -- even when an exception_type is ALSO present, plugin
        # load is checked first and its reason is what surfaces.
        status, reason = collect.classify_status(
            exception_type="AgentTimeoutError",
            rewards=RESOLVED_REWARDS,
            plugin_load_error="sadd_plugin_not_loaded:loaded=[]",
            incompleteness_reason=None,
        )
        self.assertEqual((status, reason), ("errored", "sadd_plugin_not_loaded:loaded=[]"))

    def test_incompleteness_reason_downgrades_an_otherwise_unresolved_trial(self) -> None:
        # The motivating trial: the verifier ran and scored the untouched repo
        # 0/69, which alone reads as a normal wrong answer. The missing patch
        # is what tells those two apart.
        status, reason = collect.classify_status(
            exception_type=None,
            rewards=UNRESOLVED_REWARDS,
            plugin_load_error=None,
            incompleteness_reason="no_model_patch",
        )
        self.assertEqual((status, reason), ("incomplete", "no_model_patch"))

    def test_verifier_success_outranks_the_completion_gate(self) -> None:
        # Row 5 before row 6: if the verifier certifies the task solved, no
        # heuristic about patches or question marks may take that away.
        status, reason = collect.classify_status(
            exception_type=None,
            rewards=RESOLVED_REWARDS,
            plugin_load_error=None,
            incompleteness_reason="final_message_is_question",
        )
        self.assertEqual((status, reason), ("resolved", None))

    def test_infra_failure_outranks_the_completion_gate(self) -> None:
        # An infra failure also leaves no model.patch behind, so both signals
        # fire at once. `errored` must win: the harness broke, and blaming the
        # agent for abandoning a task it never got to attempt would also pull
        # the trial into Pass@1's denominator, which errored trials are
        # excluded from.
        status, reason = collect.classify_status(
            exception_type="AgentTimeoutError",
            rewards=UNRESOLVED_REWARDS,
            plugin_load_error=None,
            incompleteness_reason="no_model_patch",
        )
        self.assertEqual((status, reason), ("errored", "pier_exception:agent_timeout:AgentTimeoutError"))


class InfraErrorCategoryTests(unittest.TestCase):
    def test_known_exception_types_map_to_their_category(self) -> None:
        expected = {
            "EnvironmentStartTimeoutError": "environment_start_timeout",
            "AgentSetupTimeoutError": "agent_setup_timeout",
            "AgentTimeoutError": "agent_timeout",
            "NonZeroAgentExitCodeError": "agent_nonzero_exit",
            "VerifierTimeoutError": "verifier_timeout",
            "CancelledError": "cancelled",
        }
        for exception_type, category in expected.items():
            with self.subTest(exception_type=exception_type):
                self.assertEqual(collect.infra_error_category(exception_type), category)

    def test_unmapped_exception_type_falls_back_to_other(self) -> None:
        # e.g. a plain RuntimeError from a Docker build failure -- see the
        # module's _EXCEPTION_TYPE_CATEGORIES comment for why there is no
        # dedicated category for this.
        self.assertEqual(collect.infra_error_category("RuntimeError"), "other_infra_error")
        self.assertEqual(collect.infra_error_category("SomeFutureError"), "other_infra_error")


class PluginLoadErrorFromInitEventTests(unittest.TestCase):
    def test_missing_event_is_missing_init_event(self) -> None:
        self.assertEqual(
            collect.plugin_load_error_from_init_event(None), "missing_init_event"
        )

    def test_plugin_errors_present_is_reported_verbatim(self) -> None:
        event = {"plugin_errors": ["boom: bad manifest"], "plugins": []}
        self.assertEqual(
            collect.plugin_load_error_from_init_event(event),
            "plugin_load_error:['boom: bad manifest']",
        )

    def test_sadd_missing_from_loaded_plugins_is_reported(self) -> None:
        event = {"plugin_errors": [], "plugins": [{"name": "other-plugin"}]}
        self.assertEqual(
            collect.plugin_load_error_from_init_event(event),
            "sadd_plugin_not_loaded:loaded=['other-plugin']",
        )

    def test_clean_load_with_sadd_present_is_none(self) -> None:
        event = {"plugin_errors": [], "plugins": [{"name": "sadd"}, {"name": "other"}]}
        self.assertIsNone(collect.plugin_load_error_from_init_event(event))


if __name__ == "__main__":
    unittest.main()
