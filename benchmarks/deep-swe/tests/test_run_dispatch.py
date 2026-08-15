#!/usr/bin/env python3
"""Unit tests for `run.py`'s preflight dispatch predicate, `has_subagent_dispatch`.

WHY THIS FILE STUBS `agent`
----------------------------
`run.py` does `import agent`, and `agent.py` imports `pier` -- a package
installed only in `/tmp/pier-venv`, not in the interpreter this suite runs
under. Rather than leave the predicate untested (the state that let the
`Task`/`Agent` rename break a correct run while 102 tests stayed green), we
register a stub `agent` module carrying just the two constants `run.py` reads,
then import `run`. Nothing else in `run.py` -- command building, the pier
subprocess, the container lifecycle -- is exercised or exercisable this way;
see README.md's "Running the tests" section for what covers those instead.

The transcript fixtures below are the real `tool_use` part shape, taken from
`runs/_preflight/abs-stepped-slices__HyQJyYy/agent/claude-code.txt`
(5 `Agent` dispatches, whose `subagent_type` values are, in order,
`sadd:meta-judge`, `general-purpose`, `sadd:judge`, `general-purpose`,
`sadd:judge`). `test_recorded_preflight_transcript_shows_dispatch`
re-checks the fixtures against that file directly whenever it is present.
"""

from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

if "agent" not in sys.modules:  # real `agent` needs `pier`; see module docstring
    _agent_stub = types.ModuleType("agent")
    _agent_stub.CEK_REF = "v0.0.0-test-stub"
    _agent_stub.CEK_INSTALL_DIR = "/tmp/context-engineering-kit"
    sys.modules["agent"] = _agent_stub

import run  # noqa: E402 -- must follow the `agent` stub above

RECORDED_TRANSCRIPT = (
    Path(run.__file__).resolve().parent
    / "runs/_preflight/abs-stepped-slices__HyQJyYy/agent/claude-code.txt"
)


def tool_use_part(name: str, **tool_input: object) -> dict:
    """One `tool_use` content part in the shape claude-code actually emits."""
    return {
        "type": "tool_use",
        "id": "toolu_01HmJKhn9piKoqm6pe7KoDCg",
        "name": name,
        "input": tool_input,
        "caller": {"type": "direct"},
    }


def assistant_event(*parts: object) -> dict:
    """One `assistant` stream event wrapping the given content parts."""
    return {"type": "assistant", "message": {"role": "assistant", "content": list(parts)}}


class HasSubagentDispatchTests(unittest.TestCase):
    """`has_subagent_dispatch` over transcripts written to a temp file.

    The predicate takes a path, so each case materializes its events as
    JSON lines exactly the way pier's stream log is written.
    """

    def assertDispatch(self, expected: bool, *events: dict) -> None:
        """Write `events` as a stream log and assert the predicate's verdict."""
        with tempfile.TemporaryDirectory() as tmp:
            stream_log = Path(tmp) / "claude-code.txt"
            stream_log.write_text("\n".join(json.dumps(event) for event in events))

            self.assertEqual(run.has_subagent_dispatch(stream_log), expected)

    def test_agent_tool_with_subagent_type_is_a_dispatch(self) -> None:
        # The defect: claude-code 2.1.233 (the pinned container version)
        # names this tool `Agent`. Matching only `Task` failed a correct run.
        self.assertDispatch(
            True,
            assistant_event(
                tool_use_part(
                    "Agent",
                    description="Judge the implementation",
                    subagent_type="sadd:meta-judge",
                    prompt="...",
                )
            ),
        )

    def test_legacy_task_tool_with_subagent_type_is_still_a_dispatch(self) -> None:
        # Pre-2.1.x transcripts must keep reading correctly.
        self.assertDispatch(
            True, assistant_event(tool_use_part("Task", subagent_type="general-purpose"))
        )

    def test_task_tracking_tools_are_not_a_dispatch(self) -> None:
        # `TaskCreate`/`TaskUpdate` share the namespace a bare `Task` match
        # would have caught. None of them launch a sub-agent.
        self.assertDispatch(
            False,
            assistant_event(tool_use_part("TaskCreate", title="Write the tests")),
            assistant_event(tool_use_part("TaskUpdate", status="in_progress")),
        )

    def test_dispatch_tool_without_subagent_type_is_not_a_dispatch(self) -> None:
        # The tool name alone is not evidence; only a real dispatch names the
        # sub-agent it launches.
        self.assertDispatch(False, assistant_event(tool_use_part("Agent", prompt="...")))

    def test_transcript_with_no_tool_use_at_all_is_not_a_dispatch(self) -> None:
        self.assertDispatch(
            False,
            {"type": "system", "subtype": "init", "plugins": [{"name": "sadd"}]},
            assistant_event({"type": "text", "text": "I will do this myself."}),
        )

    def test_dispatch_shaped_part_on_a_non_assistant_event_is_ignored(self) -> None:
        # `user` events echo tool results back; only what the orchestrator
        # itself emitted counts as evidence it dispatched.
        part = tool_use_part("Agent", subagent_type="sadd:judge")
        self.assertDispatch(False, {"type": "user", "message": {"content": [part]}})

    def test_dispatch_is_found_after_unrelated_tool_calls(self) -> None:
        # The real transcript interleaves 121 Bash / 39 Read / 23 Edit calls
        # around its 5 Agent dispatches, so the predicate must scan the whole
        # file, not just the head.
        self.assertDispatch(
            True,
            assistant_event(tool_use_part("Bash", command="ls")),
            assistant_event(tool_use_part("Read", file_path="/x")),
            assistant_event(tool_use_part("Agent", subagent_type="sadd:judge")),
        )


class MalformedTranscriptTests(unittest.TestCase):
    """A truncated or half-written transcript must return False, never raise.

    `run_preflight` reports every failure through `fail()`, which prints an
    actionable message and exits non-zero. A `TypeError` escaping the
    predicate would replace that message with a traceback in exactly the
    situation -- a run that died mid-write -- where the operator most needs
    the clean signal.
    """

    def assertNoDispatch(self, *events: dict) -> None:
        """Assert the predicate returns False rather than raising."""
        with tempfile.TemporaryDirectory() as tmp:
            stream_log = Path(tmp) / "claude-code.txt"
            stream_log.write_text("\n".join(json.dumps(event) for event in events))

            self.assertFalse(run.has_subagent_dispatch(stream_log))

    def test_null_content_returns_false(self) -> None:
        self.assertNoDispatch({"type": "assistant", "message": {"content": None}})

    def test_missing_message_returns_false(self) -> None:
        self.assertNoDispatch({"type": "assistant"})

    def test_non_dict_message_returns_false(self) -> None:
        self.assertNoDispatch({"type": "assistant", "message": "truncated"})

    def test_string_content_part_returns_false(self) -> None:
        self.assertNoDispatch(assistant_event("a bare string part"))

    def test_non_dict_tool_input_returns_false(self) -> None:
        # A string `input` would make `"subagent_type" in input` a substring
        # test -- a silent false positive, not a crash. Pinned either way.
        part = {"type": "tool_use", "name": "Agent", "input": "subagent_type=x"}
        self.assertNoDispatch(assistant_event(part))

    def test_valid_dispatch_after_a_malformed_event_is_still_found(self) -> None:
        # Tolerating garbage must mean skipping it, not abandoning the scan.
        with tempfile.TemporaryDirectory() as tmp:
            stream_log = Path(tmp) / "claude-code.txt"
            stream_log.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "assistant", "message": {"content": None}}),
                        "not json at all",
                        json.dumps(
                            assistant_event(
                                tool_use_part("Agent", subagent_type="sadd:judge")
                            )
                        ),
                    ]
                )
            )

            self.assertTrue(run.has_subagent_dispatch(stream_log))


class RecordedTranscriptTests(unittest.TestCase):
    """Grounds the fixtures above against the transcript they were read from.

    Skipped where `runs/` is absent (a fresh checkout, or CI) -- the fixture
    tests above stand alone; this one exists so a shape drifting away from
    reality is caught wherever the recording is available.
    """

    @unittest.skipUnless(
        RECORDED_TRANSCRIPT.exists(), f"no recorded transcript at {RECORDED_TRANSCRIPT}"
    )
    def test_recorded_preflight_transcript_shows_dispatch(self) -> None:
        self.assertTrue(run.has_subagent_dispatch(RECORDED_TRANSCRIPT))


if __name__ == "__main__":
    unittest.main()
