#!/usr/bin/env python3
"""Unit tests for `run.py`'s `AGENT_ENV` assembly and its `--ae` emission.

`agent_env_for_host` decides which `--ae KEY=VALUE` pairs reach pier, and
therefore which env vars reach the container: a fixed Claude Code runtime
setting, plus whichever of `FORWARDED_HOST_ENV` the operator actually
exported. Pier reads only its own closed list of credential vars from the
host, so a var missing from here does not reach a trial at all -- and one
emitted blank is recorded in the job's `config.json` as a setting nobody
chose.

The function takes the host environment as a parameter rather than reading
`os.environ`, which is what makes this reachable without `pier` and without
mutating process state; `run` itself comes from `tests/run_fixtures.py` for
the reason that module's docstring gives.
"""

from __future__ import annotations

import unittest

from .run_fixtures import run

# One arm's worth of the arguments `build_pier_command` needs. Nothing here is
# under test; the `--ae` pairs it emits are.
ARM_COMMAND_KWARGS = {
    "pier_bin": "pier",
    "orchestrator_model_id": "claude-opus-4-1-20250805",
    "template_path": "/tmp/prompt.j2",
    "job_name": "do-in-steps__opus-sonnet",
    "jobs_dir": "/tmp/runs",
    "agent_timeout_multiplier": 3.0,
    "dataset_args": [],
}


def agent_env_pairs(command: list[str]) -> list[str]:
    """Every `--ae` value in `command`, in the order it was emitted."""
    return [value for flag, value in zip(command, command[1:]) if flag == "--ae"]


class FixedEntryTests(unittest.TestCase):
    """The background-wait ceiling is unconditional and must stay that way."""

    def test_the_ceiling_is_present_with_an_empty_host_env(self) -> None:
        self.assertEqual(
            run.agent_env_for_host({}),
            {"CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0"},
        )

    def test_the_host_cannot_override_the_ceiling(self) -> None:
        # It is a correctness setting, not a tuning knob -- see its comment.
        # Only FORWARDED_HOST_ENV names are read from the host at all.
        env = run.agent_env_for_host({"CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "600000"})

        self.assertEqual(env["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"], "0")


class ForwardedHostVarTests(unittest.TestCase):
    """Host vars forwarded only when the operator actually exported them."""

    def test_both_are_forwarded_when_set(self) -> None:
        env = run.agent_env_for_host(
            {
                "ANTHROPIC_CUSTOM_HEADERS": "X-Tenant: acme",
                "API_TIMEOUT_MS": "600000",
            }
        )

        self.assertEqual(env["ANTHROPIC_CUSTOM_HEADERS"], "X-Tenant: acme")
        self.assertEqual(env["API_TIMEOUT_MS"], "600000")

    def test_an_unset_var_is_absent_rather_than_blank(self) -> None:
        env = run.agent_env_for_host({"API_TIMEOUT_MS": "600000"})

        self.assertNotIn("ANTHROPIC_CUSTOM_HEADERS", env)

    def test_a_blank_var_is_treated_as_unset(self) -> None:
        # `export API_TIMEOUT_MS=` is how a shell empties one in place.
        env = run.agent_env_for_host(
            {"ANTHROPIC_CUSTOM_HEADERS": "", "API_TIMEOUT_MS": "   "}
        )

        self.assertNotIn("ANTHROPIC_CUSTOM_HEADERS", env)
        self.assertNotIn("API_TIMEOUT_MS", env)

    def test_a_multi_header_value_is_passed_through_untouched(self) -> None:
        # ANTHROPIC_CUSTOM_HEADERS is newline-separated `Name: Value` pairs;
        # argv reaches subprocess.run without a shell, so this must survive.
        headers = "X-Tenant: acme\nX-Trace: on"

        env = run.agent_env_for_host({"ANTHROPIC_CUSTOM_HEADERS": headers})

        self.assertEqual(env["ANTHROPIC_CUSTOM_HEADERS"], headers)

    def test_unrelated_host_vars_are_not_forwarded(self) -> None:
        # The list is closed: forwarding everything would leak the whole host
        # env into a recorded, plaintext `config.json`.
        env = run.agent_env_for_host(
            {"ANTHROPIC_API_KEY": "sk-ant-x", "PATH": "/usr/bin"}
        )

        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("PATH", env)

    def test_surrounding_whitespace_is_stripped_from_a_forwarded_value(self) -> None:
        # The defect this guards: gating on `value.strip()` while storing the
        # padded original, which forwards the padding into the container and
        # into the recorded `config.json`.
        env = run.agent_env_for_host({"API_TIMEOUT_MS": "  600000\n"})

        self.assertEqual(env["API_TIMEOUT_MS"], "600000")

    def test_only_the_outer_edges_of_a_multi_header_value_are_stripped(self) -> None:
        # Interior newlines separate `Name: Value` pairs and must survive.
        env = run.agent_env_for_host(
            {"ANTHROPIC_CUSTOM_HEADERS": "\n X-Tenant: acme\nX-Trace: on \n"}
        )

        self.assertEqual(
            env["ANTHROPIC_CUSTOM_HEADERS"], "X-Tenant: acme\nX-Trace: on"
        )

    def test_the_forwarded_names_are_the_documented_three(self) -> None:
        self.assertEqual(
            run.FORWARDED_HOST_ENV,
            (
                "ANTHROPIC_CUSTOM_HEADERS",
                "API_TIMEOUT_MS",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
            ),
        )


class NonessentialTrafficTests(unittest.TestCase):
    """`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`: pier's default, overridable.

    Unlike the other two forwarded names, pier sets this one itself -- it
    hardcodes `"1"` at `claude_code.py:1302`. Forwarding it still gives the
    host the final word, because `--ae` values are re-merged BELOW that line
    (`base.py:320-323`, in `_exec`, which `exec_as_agent` delegates to). The
    two halves of that contract are what these tests pin: a host value must be
    emitted so it can win, and an unset host must emit NOTHING so pier's `"1"`
    stands unopposed.
    """

    def test_a_host_value_is_forwarded_so_it_can_win_below_pier_s_hardcode(self) -> None:
        env = run.agent_env_for_host({"CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "0"})

        self.assertEqual(env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"], "0")

    def test_an_unset_host_leaves_pier_s_default_in_place(self) -> None:
        # Absence is the assertion: with no `--ae` pair, nothing re-merges
        # over `claude_code.py:1302` and the container keeps pier's `"1"`.
        # Emitting `=1` here would look equivalent but would silently pin the
        # default against a future pier release that changes it.
        env = run.agent_env_for_host({})

        self.assertNotIn("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", env)

    def test_a_blank_host_value_does_not_displace_pier_s_default(self) -> None:
        # `--ae KEY=` would be dropped by pier's empty filter at `:1269` but
        # still recorded in `config.json` as a setting nobody chose.
        env = run.agent_env_for_host({"CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "  "})

        self.assertNotIn("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", env)


class EmittedFlagTests(unittest.TestCase):
    """`build_pier_command` renders `AGENT_ENV` as one `--ae` pair per entry."""

    def test_every_agent_env_entry_becomes_one_ae_pair(self) -> None:
        arm = run.Arm(skill="do-in-steps", orchestrator="opus", impl="sonnet")

        command = run.build_pier_command(arm, **ARM_COMMAND_KWARGS)

        self.assertEqual(
            agent_env_pairs(command),
            [f"{key}={value}" for key, value in run.AGENT_ENV.items()],
        )

    def test_a_vanilla_arm_gets_the_same_pairs(self) -> None:
        # `--ae` is not plugin-related: a control arm needs it just as much.
        vanilla = run.Arm(skill=None, orchestrator="opus", impl=None)
        plugin = run.Arm(skill="do-in-steps", orchestrator="opus", impl="sonnet")

        self.assertEqual(
            agent_env_pairs(run.build_pier_command(vanilla, **ARM_COMMAND_KWARGS)),
            agent_env_pairs(run.build_pier_command(plugin, **ARM_COMMAND_KWARGS)),
        )

    def test_no_pair_is_ever_emitted_with_an_empty_value(self) -> None:
        # The defect this guards: an unset host var rendered as `--ae KEY=`,
        # which pier drops from the container env but still records verbatim.
        arm = run.Arm(skill=None, orchestrator="haiku", impl=None)

        command = run.build_pier_command(arm, **ARM_COMMAND_KWARGS)

        for pair in agent_env_pairs(command):
            self.assertNotEqual(pair.split("=", 1)[1], "", pair)


if __name__ == "__main__":
    unittest.main()
