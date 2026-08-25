#!/usr/bin/env python3
"""Unit tests for `stream_cost.parse_total_cost_from_stream_lines` -- the rule
behind this harness's cost fix, that pier's own version got wrong by returning
the FIRST `{"type":"result"}` event in a resumed session's stream.

Every test here runs under the project's default test command (`python3 -m
unittest discover`), with no `pier` and no third-party package, which is the
whole reason the rule lives in its own module rather than inside
`ClaudeCodeSadd`: a rule reachable only through a `pier` import is a rule whose
tests skip, and a suite that skips its way to green is what let a claude-code
tool rename break a correct run in this repo before. The thin I/O shell that
wraps this function, and the override's resolution order, still need pier and
are covered in `tests/test_agent_cost_parsing.py`.

The recorded cost sequence is asserted against a committed, trimmed copy of the
real stream's result events (`tests/fixtures/recorded-result-events.txt`, see
that directory's README) so it holds in any checkout: `runs/` is a gitignored
recording, and the trial this fixture was trimmed from is no longer among the
recordings in this tree, so the copy is now the only evidence of it there is.
"""

from __future__ import annotations

import json
import unittest

import stream_cost  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR

FIXTURE_PATH = BENCHMARK_DIR / "tests" / "fixtures" / "recorded-result-events.txt"

# The recorded run this fix exists for: 22 cumulative result events.
RECORDED_TOTAL_COST_USD = 26.53034819999999
RECORDED_FIRST_EVENT_COST_USD = 0.39202004999999995
RECORDED_N_RESULT_EVENTS = 22


def result_line(total_cost_usd: object, **extra: object) -> str:
    """One `{"type":"result"}` stream line, in the shape claude-code emits."""
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "total_cost_usd": total_cost_usd,
            **extra,
        }
    )


# A background task completion resuming the session -- the event kind whose
# existence makes "the first result event" the wrong one to read.
TASK_NOTIFICATION_ORIGIN = {"origin": {"kind": "task-notification"}}


class MultipleResultEventTests(unittest.TestCase):
    def test_a_resumed_session_reports_its_total_not_its_first_event(self) -> None:
        lines = [
            result_line(0.47798145),
            result_line(1.8358266, **TASK_NOTIFICATION_ORIGIN),
            result_line(1.98284115, **TASK_NOTIFICATION_ORIGIN),
        ]
        self.assertEqual(stream_cost.parse_total_cost_from_stream_lines(lines), 1.98284115)

    def test_out_of_order_events_still_report_the_largest_total(self) -> None:
        # Why max rather than last: these events are flushed by concurrent
        # background tasks, so "last" would under-report the moment they arrive
        # out of order -- the exact failure being fixed.
        lines = [result_line(1.98284115), result_line(0.47798145)]
        self.assertEqual(stream_cost.parse_total_cost_from_stream_lines(lines), 1.98284115)

    def test_a_single_event_stream_behaves_exactly_as_upstream_did(self) -> None:
        # Not every stream was affected: `runs/_preflight/abs-stepped-slices__HyQJyYy`
        # carries one result event, so first and last are the same number and its
        # recorded cost was always correct.
        self.assertEqual(
            stream_cost.parse_total_cost_from_stream_lines([result_line(1.8649315)]), 1.8649315
        )


class UnusableCostFieldTests(unittest.TestCase):
    def test_an_unusable_cost_field_does_not_erase_a_valid_one(self) -> None:
        # Upstream returns None the moment the FIRST event is bad. One malformed
        # resumption event must not report "no cost data" while a real figure
        # sits elsewhere in the file -- in either order.
        bad_events = {
            "null": result_line(None),
            "missing": json.dumps({"type": "result", "subtype": "success"}),
            "unparseable": result_line("not-a-number"),
            "list": result_line([1, 2]),
        }
        for label, bad_event in bad_events.items():
            with self.subTest(bad_cost_field=label):
                self.assertEqual(
                    stream_cost.parse_total_cost_from_stream_lines([bad_event, result_line(2.5)]),
                    2.5,
                )
                self.assertEqual(
                    stream_cost.parse_total_cost_from_stream_lines([result_line(2.5), bad_event]),
                    2.5,
                )

    def test_no_usable_cost_anywhere_reports_unknown_not_zero(self) -> None:
        # "Unknown" and "$0.00" are different claims; only None is honest.
        self.assertIsNone(
            stream_cost.parse_total_cost_from_stream_lines(
                [result_line(None), result_line("nope")]
            )
        )

    def test_a_genuine_zero_cost_is_reported_as_zero_not_unknown(self) -> None:
        # The converse: $0.00 really observed must not be laundered into None.
        self.assertEqual(stream_cost.parse_total_cost_from_stream_lines([result_line(0)]), 0.0)

    def test_an_integer_or_string_number_is_accepted(self) -> None:
        self.assertEqual(stream_cost.parse_total_cost_from_stream_lines([result_line(3)]), 3.0)
        self.assertEqual(stream_cost.parse_total_cost_from_stream_lines([result_line("2.5")]), 2.5)


class SkippedLineTests(unittest.TestCase):
    def test_upstream_line_skipping_is_preserved(self) -> None:
        cases = {
            "no lines at all": ([], None),
            "blank and whitespace lines": (["", "   ", "\n"], None),
            "no result event": (['{"type": "assistant", "message": {}}'], None),
            "non-json lines": (["not json at all", result_line(3.0)], 3.0),
            "truncated json line": (
                ['{"type": "result", "total_cost_usd": ', result_line(4.0)],
                4.0,
            ),
            "trailing newlines on each line": ([result_line(5.0) + "\n", "\n"], 5.0),
            "other event types ignored": (
                ['{"type": "system", "subtype": "init", "total_cost_usd": 99.0}'],
                None,
            ),
        }
        for label, (lines, expected) in cases.items():
            with self.subTest(case=label):
                self.assertEqual(stream_cost.parse_total_cost_from_stream_lines(lines), expected)

    def test_a_replacement_character_only_costs_its_own_line(self) -> None:
        # What the shell's `errors="replace"` produces from a log truncated
        # mid-multibyte-character: one corrupted line, which fails json.loads
        # and is skipped, leaving every other event usable. Asserted here on
        # pre-decoded lines so it runs without pier; the shell's own decoding is
        # covered in tests/test_agent_cost_parsing.py.
        corrupted = result_line(9.0)[:-3] + "\ufffd"
        lines = [result_line(1.0), corrupted, result_line(2.0)]
        self.assertEqual(stream_cost.parse_total_cost_from_stream_lines(lines), 2.0)

    def test_any_iterable_of_lines_is_accepted(self) -> None:
        # The shell passes an open file object so a huge transcript is never
        # loaded whole; a generator stands in for one here.
        lines = (line for line in [result_line(1.0), result_line(7.5)])
        self.assertEqual(stream_cost.parse_total_cost_from_stream_lines(lines), 7.5)


def recorded_result_event_lines() -> list[str]:
    """The fixture's `result` event lines, comment header stripped.

    Module-level so `tests/test_agent_cost_parsing.py` can stage the same
    recorded sequence as a real file for the I/O shell to read, rather than
    keeping a second copy of how this fixture is parsed.
    """
    return [
        line
        for line in FIXTURE_PATH.read_text(encoding="utf-8").splitlines()
        if line.startswith("{")
    ]


class RecordedStreamTests(unittest.TestCase):
    """The real regression, asserted against the committed trimmed fixture."""

    def fixture_lines(self) -> list[str]:
        return FIXTURE_PATH.read_text(encoding="utf-8").splitlines()

    def test_the_recorded_cost_sequence_reports_its_full_total(self) -> None:
        parsed = stream_cost.parse_total_cost_from_stream_lines(self.fixture_lines())
        self.assertEqual(parsed, RECORDED_TOTAL_COST_USD)

    def test_upstreams_first_event_rule_would_report_68x_too_little(self) -> None:
        # Pins the size of the defect: if a future pier release fixes this
        # upstream (making the override redundant), that is worth noticing.
        first_events = [
            json.loads(line)
            for line in self.fixture_lines()
            if line.startswith("{")
        ]
        self.assertEqual(len(first_events), RECORDED_N_RESULT_EVENTS)
        self.assertEqual(first_events[0]["total_cost_usd"], RECORDED_FIRST_EVENT_COST_USD)
        self.assertGreater(RECORDED_TOTAL_COST_USD / RECORDED_FIRST_EVENT_COST_USD, 60)

    def test_the_recorded_costs_are_cumulative_so_max_equals_last(self) -> None:
        # The evidence behind reading these events as running totals rather than
        # per-turn deltas: they only increase, and their sum ($282.19) is an
        # order of magnitude past the $28.39 the stream's own final
        # modelUsage.costUSD reports for the session.
        costs = [
            json.loads(line)["total_cost_usd"]
            for line in self.fixture_lines()
            if line.startswith("{")
        ]
        self.assertEqual(costs, sorted(costs))
        self.assertEqual(max(costs), costs[-1])
        self.assertEqual(max(costs), RECORDED_TOTAL_COST_USD)
        self.assertGreater(sum(costs), 10 * RECORDED_TOTAL_COST_USD)

    def test_the_rule_reads_the_fixture_the_way_the_shell_reads_a_stream(self) -> None:
        # The fixture is not merely inspected field by field above -- it is
        # fed to the real rule, line by line from an iterator, exactly as the
        # I/O shell feeds it a file handle. That is the call the cost fix
        # actually makes, so a rule that only worked on a materialised list
        # would show up here.
        self.assertEqual(
            stream_cost.parse_total_cost_from_stream_lines(iter(self.fixture_lines())),
            RECORDED_TOTAL_COST_USD,
        )


if __name__ == "__main__":
    unittest.main()
