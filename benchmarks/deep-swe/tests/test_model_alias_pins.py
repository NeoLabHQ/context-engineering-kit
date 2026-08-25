#!/usr/bin/env python3
"""Unit tests for `model_alias_pins.without_gateway_alias_pins`.

The rule that keeps this benchmark's implementation-tier axis alive behind a
gateway base URL: pier pins `haiku`/`sonnet`/`opus` (and the sub-agent model)
to the orchestrator's own model whenever `ANTHROPIC_BASE_URL` and
`ANTHROPIC_MODEL` are both set, which would silently collapse `opus-sonnet`
into `opus-opus`. `ClaudeCodeSadd.exec_as_agent` removes those pins by calling
this function; here it is exercised on plain dicts.

Stdlib only, no `pier`, no `runs/` -- see `model_alias_pins`' docstring for why
the rule lives outside `agent.py`.
"""

from __future__ import annotations

import unittest

from model_alias_pins import (  # sys.path patched by tests/__init__.py
    GATEWAY_PINNED_ALIAS_VARS,
    without_gateway_alias_pins,
)

# The env dict pier hands to `exec_as_agent` for an `opus-sonnet` arm routed
# through a gateway: the four pins, plus the surrounding vars it also sets.
GATEWAY_ENV = {
    "ANTHROPIC_AUTH_TOKEN": "tok",
    "ANTHROPIC_BASE_URL": "https://gateway.example.com",
    "ANTHROPIC_MODEL": "claude-opus-4-1-20250805",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-opus-4-1-20250805",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-4-1-20250805",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-opus-4-1-20250805",
    "CLAUDE_CODE_SUBAGENT_MODEL": "claude-opus-4-1-20250805",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "IS_SANDBOX": "1",
    "CLAUDE_CONFIG_DIR": "/agent/sessions",
}


class GatewayRunTests(unittest.TestCase):
    """With a base URL in play, exactly the four pins come out."""

    def test_all_four_pins_are_removed(self) -> None:
        stripped = without_gateway_alias_pins(dict(GATEWAY_ENV))

        for name in GATEWAY_PINNED_ALIAS_VARS:
            self.assertNotIn(name, stripped)

    def test_the_four_are_the_ones_pier_sets(self) -> None:
        # Names, not just a count: a typo here would strip nothing and the
        # test above would still pass on the remaining three.
        self.assertEqual(
            set(GATEWAY_PINNED_ALIAS_VARS),
            {
                "ANTHROPIC_DEFAULT_SONNET_MODEL",
                "ANTHROPIC_DEFAULT_OPUS_MODEL",
                "ANTHROPIC_DEFAULT_HAIKU_MODEL",
                "CLAUDE_CODE_SUBAGENT_MODEL",
            },
        )

    def test_nothing_else_is_touched(self) -> None:
        # Including ANTHROPIC_MODEL itself -- the orchestrator's own model is
        # what the arm asked for and must survive.
        stripped = without_gateway_alias_pins(dict(GATEWAY_ENV))

        expected = {
            key: value
            for key, value in GATEWAY_ENV.items()
            if key not in GATEWAY_PINNED_ALIAS_VARS
        }
        self.assertEqual(stripped, expected)

    def test_the_callers_dict_is_not_mutated(self) -> None:
        # Pier reuses one env dict across both of its `exec_as_agent` calls.
        env = dict(GATEWAY_ENV)

        without_gateway_alias_pins(env)

        self.assertEqual(env, GATEWAY_ENV)


class NonGatewayRunTests(unittest.TestCase):
    """Without the pair pier keys off, the env must pass through identically.

    The whole safety argument for this override is that a first-party
    `api.anthropic.com` run reaches the container byte-identical to what pier
    built, so these assert object identity rather than equality.
    """

    def test_no_base_url_returns_the_same_object(self) -> None:
        env = {"ANTHROPIC_API_KEY": "sk-ant-x", "ANTHROPIC_MODEL": "claude-opus-4-1"}

        self.assertIs(without_gateway_alias_pins(env), env)

    def test_base_url_without_a_model_returns_the_same_object(self) -> None:
        # Pier's guard is an `and`; half of it must not trigger the removal.
        env = {"ANTHROPIC_BASE_URL": "https://gateway.example.com"}

        self.assertIs(without_gateway_alias_pins(env), env)

    def test_a_stray_pin_survives_a_non_gateway_run(self) -> None:
        # Deliberate: pier did not set these here, so they came from the
        # operator's own `--ae`/`agent.env` and are not this rule's to undo.
        env = {"CLAUDE_CODE_SUBAGENT_MODEL": "claude-haiku-4-5"}

        self.assertIs(without_gateway_alias_pins(env), env)

    def test_empty_env_returns_the_same_object(self) -> None:
        env: dict[str, str] = {}

        self.assertIs(without_gateway_alias_pins(env), env)


class InstallStepTests(unittest.TestCase):
    """`install()` routes its `user="agent"` steps through the same override.

    Every install step this harness or pier's `ClaudeCode` declares carries
    `env=None`, so the no-op path is the one that actually runs at install
    time -- a filter that raised or substituted `{}` here would break the
    container build rather than a trial.
    """

    def test_none_stays_none(self) -> None:
        self.assertIsNone(without_gateway_alias_pins(None))

    def test_a_small_install_step_env_is_unchanged(self) -> None:
        env = {"DEBIAN_FRONTEND": "noninteractive"}

        self.assertIs(without_gateway_alias_pins(env), env)


if __name__ == "__main__":
    unittest.main()
