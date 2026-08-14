#!/usr/bin/env python3
"""Unit tests for `collect.py`'s status/error classification: `classify_status`,
`infra_error_category`, `plugin_load_error_from_init_event`.
"""

from __future__ import annotations

import unittest

import collect  # sys.path patched by tests/__init__.py


class ClassifyStatusTests(unittest.TestCase):
    """Precedence order under test (collect.py's classification table):
    plugin_load_error > exception_type > missing/empty rewards > all-ones
    rewards > otherwise. Each test isolates one row; the precedence tests at
    the bottom prove a higher-priority signal wins even when a lower-priority
    one would, by itself, say something different.
    """

    def test_all_rewards_one_is_resolved(self) -> None:
        status, reason = collect.classify_status(
            exception_type=None, rewards={"a": 1, "b": 1}, plugin_load_error=None
        )
        self.assertEqual((status, reason), ("resolved", None))

    def test_any_reward_not_one_is_unresolved(self) -> None:
        status, reason = collect.classify_status(
            exception_type=None, rewards={"a": 1, "b": 0}, plugin_load_error=None
        )
        self.assertEqual((status, reason), ("unresolved", None))

    def test_missing_rewards_is_errored(self) -> None:
        status, reason = collect.classify_status(
            exception_type=None, rewards=None, plugin_load_error=None
        )
        self.assertEqual((status, reason), ("errored", "missing_verifier_rewards"))

    def test_empty_rewards_dict_is_errored(self) -> None:
        status, reason = collect.classify_status(
            exception_type=None, rewards={}, plugin_load_error=None
        )
        self.assertEqual((status, reason), ("errored", "missing_verifier_rewards"))

    def test_exception_type_wins_over_all_ones_rewards(self) -> None:
        # Module docstring's worked example: claude crashes (API 529 surfaced
        # as NonZeroAgentExitCodeError) but the verifier still ran and scored
        # every reward as 1. exception_info is checked before rewards, so
        # this must stay errored, never flip to resolved.
        status, reason = collect.classify_status(
            exception_type="NonZeroAgentExitCodeError",
            rewards={"pass": 1},
            plugin_load_error=None,
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
            rewards={"pass": 1},
            plugin_load_error="sadd_plugin_not_loaded:loaded=[]",
        )
        self.assertEqual((status, reason), ("errored", "sadd_plugin_not_loaded:loaded=[]"))


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
