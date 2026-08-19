#!/usr/bin/env python3
"""Unit tests for `agent.py`'s `ClaudeCodeSadd._parse_total_cost_from_stream_json`
-- the thin I/O shell around `stream_cost.parse_total_cost_from_stream_lines`,
plus the override's resolution order against pier's real `ClaudeCode`.

WHY THIS FILE NEEDS `pier` (AND WHY THAT IS NOW HARMLESS)
---------------------------------------------------------
What is under test here is precisely that a method defined on `ClaudeCodeSadd`
overrides the one it inherits from pier's real `ClaudeCode`, and that the
override reads a real file. A stubbed base class would test the stub's
resolution order, so these tests import the real thing and skip -- never fail
-- when pier is absent.

That used to mean the cost fix itself went untested under the project's default
`python3 -m unittest discover`. It no longer does: the parsing RULE lives in
`stream_cost.py`, which imports nothing but stdlib `json`, and
`tests/test_stream_cost.py` covers it unconditionally. What skips here is only
the file-opening shell and the MRO check.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from . import BENCHMARK_DIR
from .test_stream_cost import (
    RECORDED_FIRST_EVENT_COST_USD,
    RECORDED_TOTAL_COST_USD,
    result_line,
)

PIER_AVAILABLE = importlib.util.find_spec("pier") is not None

RECORDED_AGENT_LOGS_DIR = (
    BENCHMARK_DIR
    / "runs"
    / "do-in-steps__sonnet-sonnet"
    / "cattrs-partial-structuring-recov__ZsbwRdJ"
    / "agent"
)


@unittest.skipUnless(PIER_AVAILABLE, "pier is not installed in this interpreter")
class OverrideResolutionTests(unittest.TestCase):
    def test_the_override_is_what_inheritance_resolves_to(self) -> None:
        # An override pier's own caller never reaches would be no fix at all,
        # so pin the resolution order itself, not just a return value.
        from agent import ClaudeCodeSadd
        from pier.agents.installed.claude_code import ClaudeCode

        self.assertIn(ClaudeCode, ClaudeCodeSadd.__mro__)
        self.assertEqual(
            ClaudeCodeSadd._parse_total_cost_from_stream_json.__qualname__,
            "ClaudeCodeSadd._parse_total_cost_from_stream_json",
        )
        self.assertIsNot(
            ClaudeCodeSadd._parse_total_cost_from_stream_json,
            ClaudeCode._parse_total_cost_from_stream_json,
        )

    def test_the_shell_delegates_to_the_pure_rule(self) -> None:
        # The method must stay a shell: if it ever grows its own copy of the
        # rule, this stops being true and the unconditional tests stop covering
        # the code that actually runs.
        import agent
        import stream_cost

        self.assertIs(
            agent.parse_total_cost_from_stream_lines,
            stream_cost.parse_total_cost_from_stream_lines,
        )


@unittest.skipUnless(PIER_AVAILABLE, "pier is not installed in this interpreter")
class IoShellTests(unittest.TestCase):
    """The file-opening half: what the shell does that the pure rule cannot."""

    def parse_cost(self, stream_bytes: bytes | None) -> float | None:
        """Run the override over a temp `claude-code.txt`; None writes no file."""
        from agent import ClaudeCodeSadd

        with tempfile.TemporaryDirectory() as tmp:
            logs_dir = Path(tmp)
            if stream_bytes is not None:
                (logs_dir / "claude-code.txt").write_bytes(stream_bytes)
            return ClaudeCodeSadd(logs_dir=logs_dir)._parse_total_cost_from_stream_json()

    def test_a_real_file_is_read_and_parsed(self) -> None:
        stream = f"{result_line(0.5)}\n{result_line(2.5)}\n".encode()
        self.assertEqual(self.parse_cost(stream), 2.5)

    def test_a_missing_log_reports_unknown_rather_than_raising(self) -> None:
        self.assertIsNone(self.parse_cost(None))

    def test_a_log_truncated_mid_character_does_not_raise(self) -> None:
        # `errors="replace"` on the open: upstream's `except OSError` does not
        # catch UnicodeDecodeError, so a job interrupted mid-write would
        # otherwise take trajectory building down with it.
        truncated = result_line(5.0).encode() + b"\n" + "é".encode()[:1]
        self.assertEqual(self.parse_cost(truncated), 5.0)


@unittest.skipUnless(PIER_AVAILABLE, "pier is not installed in this interpreter")
@unittest.skipUnless(
    RECORDED_AGENT_LOGS_DIR.exists(), f"recorded run not present at {RECORDED_AGENT_LOGS_DIR}"
)
class RecordedRunEndToEndTests(unittest.TestCase):
    """Override vs upstream, both reading the real 6 MB recorded transcript."""

    def test_the_override_reports_the_full_total_where_upstream_does_not(self) -> None:
        from agent import ClaudeCodeSadd
        from pier.agents.installed.claude_code import ClaudeCode

        self.assertEqual(
            ClaudeCodeSadd(logs_dir=RECORDED_AGENT_LOGS_DIR)._parse_total_cost_from_stream_json(),
            RECORDED_TOTAL_COST_USD,
        )
        self.assertEqual(
            ClaudeCode(logs_dir=RECORDED_AGENT_LOGS_DIR)._parse_total_cost_from_stream_json(),
            RECORDED_FIRST_EVENT_COST_USD,
        )


if __name__ == "__main__":
    unittest.main()
