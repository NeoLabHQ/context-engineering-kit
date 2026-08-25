#!/usr/bin/env python3
"""Pins that `ClaudeCodeSadd.exec_as_agent` is the method pier actually calls.

The RULE it applies is covered unconditionally by
`tests/test_model_alias_pins.py`; what needs the real `pier` -- and so skips
rather than fails when pier is absent -- is only the wiring: that this
override is what inheritance resolves to, and that it reaches pier's own
implementation with every parameter intact.

Both are the failure mode this harness has already been bitten by once: a
correct rule attached to a hook nothing calls (see `tests/test_run_dispatch.py`
on the `Task`/`Agent` rename). If pier renamed or stopped routing through
`exec_as_agent`, the alias pins would come back with nothing turning red.
"""

from __future__ import annotations

import asyncio
import importlib.util
import unittest

PIER_AVAILABLE = importlib.util.find_spec("pier") is not None

GATEWAY_ENV = {
    "ANTHROPIC_BASE_URL": "https://gateway.example.com",
    "ANTHROPIC_MODEL": "claude-opus-4-1-20250805",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-opus-4-1-20250805",
    "CLAUDE_CODE_SUBAGENT_MODEL": "claude-opus-4-1-20250805",
    "IS_SANDBOX": "1",
}


@unittest.skipUnless(PIER_AVAILABLE, "pier is not installed in this interpreter")
class OverrideResolutionTests(unittest.TestCase):
    def test_the_override_is_what_inheritance_resolves_to(self) -> None:
        from agent import ClaudeCodeSadd
        from pier.agents.installed.base import BaseInstalledAgent

        self.assertIn(BaseInstalledAgent, ClaudeCodeSadd.__mro__)
        self.assertIsNot(ClaudeCodeSadd.exec_as_agent, BaseInstalledAgent.exec_as_agent)


@unittest.skipUnless(PIER_AVAILABLE, "pier is not installed in this interpreter")
class DelegationTests(unittest.TestCase):
    """Drives the real override down to pier's own `_exec`, which is stubbed.

    `__init__` is bypassed deliberately: `exec_as_agent` reads no instance
    state, and constructing a real agent would want a container. Everything
    between the override and `_exec` -- including pier's `exec_as_agent`
    itself -- is the genuine article.
    """

    def exec_call(self, **kwargs: object) -> dict:
        """Call the override with `kwargs` and return what `_exec` received."""
        from agent import ClaudeCodeSadd

        recorded: dict = {}

        class RecordingAgent(ClaudeCodeSadd):
            # `_exec` is the one method below the override; stubbing it stops
            # the call at pier's own boundary without a container.
            async def _exec(  # type: ignore[override]
                self, environment, command, **exec_kwargs
            ):
                recorded.update(environment=environment, command=command, **exec_kwargs)
                return "exec-result"

        agent = RecordingAgent.__new__(RecordingAgent)
        result = asyncio.run(agent.exec_as_agent(**kwargs))  # type: ignore[arg-type]

        recorded["returned"] = result
        return recorded

    def test_the_pins_are_stripped_before_the_command_runs(self) -> None:
        recorded = self.exec_call(
            environment="container", command="claude --print", env=dict(GATEWAY_ENV)
        )

        self.assertNotIn("ANTHROPIC_DEFAULT_SONNET_MODEL", recorded["env"])
        self.assertNotIn("CLAUDE_CODE_SUBAGENT_MODEL", recorded["env"])
        self.assertEqual(
            recorded["env"]["ANTHROPIC_MODEL"], GATEWAY_ENV["ANTHROPIC_MODEL"]
        )

    def test_every_other_parameter_is_forwarded_and_the_result_returned(self) -> None:
        # `cwd` and `timeout_sec` are pier's to set; dropping either would
        # change how a trial runs for a reason unrelated to model aliases.
        recorded = self.exec_call(
            environment="container",
            command="claude --print",
            env=dict(GATEWAY_ENV),
            cwd="/app",
            timeout_sec=1800,
        )

        self.assertEqual(recorded["environment"], "container")
        self.assertEqual(recorded["command"], "claude --print")
        self.assertEqual(recorded["cwd"], "/app")
        self.assertEqual(recorded["timeout_sec"], 1800)
        self.assertEqual(recorded["returned"], "exec-result")

    def test_an_install_step_passes_through_with_env_none(self) -> None:
        # `install()` routes `user="agent"` steps here with `env=step.env`,
        # which is None for every step this harness declares.
        recorded = self.exec_call(
            environment="container", command="git init -q /tmp/cek"
        )

        self.assertIsNone(recorded["env"])


if __name__ == "__main__":
    unittest.main()
