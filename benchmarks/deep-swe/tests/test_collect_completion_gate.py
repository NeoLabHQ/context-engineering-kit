#!/usr/bin/env python3
"""Unit tests for `collect.py`'s completion gate -- the rules behind the
`incomplete` trial status: `last_prose_line`, `message_ends_in_question`,
`incompleteness_reason_from_signals`, and their filesystem-backed wrappers
`find_stream_log_final_message`, `trial_has_model_patch`,
`find_trial_incompleteness_reason`.

`classify_status`'s handling of the gate's verdict (and its precedence against
the rows either side of it) lives in `test_collect_status.py`, with the rest of
the classification table.

The question heuristic is fuzzy by nature, so it is tested from both
directions: the abandonment shapes it MUST catch, and -- at greater length --
the shapes it must stay quiet about, since a false positive would brand a
finished trial abandoned.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import collect  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR
from .collect_fixtures import make_trial

# The abandonment shape, written out here so the rule's behavior is pinned even
# in a checkout without `runs/`. It is a condensed stand-in for a real recorded
# one: `runs/_preflight-do-in-steps/cattrs-partial-structuring-recov__9ryVMmH`
# ends its final message with "Which approach would you prefer? Or shall I
# continue with the current orchestration pace?" after offering a numbered menu
# under budget pressure. `RecordedFinalMessageTests` asserts against that real
# prose directly.
ABANDONING_QUESTION = (
    "I can either narrow the scope to the structuring path only, or keep going "
    "and risk running long.\n"
    "\n"
    "1. Narrow scope now\n"
    "2. Keep going\n"
    "\n"
    "Which would you like?"
)


class MessageEndsInQuestionTests(unittest.TestCase):
    def test_the_described_abandonment_shape_is_caught(self) -> None:
        self.assertTrue(collect.message_ends_in_question(ABANDONING_QUESTION))

    def test_questions_are_caught_through_whitespace_and_markdown(self) -> None:
        for label, text in {
            "plain": "Which would you like?",
            "trailing whitespace": "Which would you like?   \n\n  \n",
            "bold": "**Which would you like?**",
            "italic and code": "_Which `option` would you like?_",
            "bulleted last line": "- Which would you like?",
            "blockquoted": "> Which would you like?",
            "question after a code fence": (
                "Here is the diff:\n```diff\n-a\n+b\n```\nShall I apply it?"
            ),
        }.items():
            with self.subTest(shape=label):
                self.assertTrue(collect.message_ends_in_question(text))

    def test_a_rhetorical_question_followed_by_content_is_not_an_abandonment(self) -> None:
        for label, text in {
            "answered in the same line": "Why did it fail? Because the parser read the first event.",
            "answered on a later line": "Should I stop here?\n\nNo -- continuing with step 2.",
            "question then summary": (
                "Was the patch enough?\n\n"
                "It was: all 69 fail-to-pass tests now pass and the suite is green."
            ),
        }.items():
            with self.subTest(shape=label):
                self.assertFalse(collect.message_ends_in_question(text))

    def test_a_question_mark_inside_code_is_not_a_question(self) -> None:
        for label, text in {
            "fenced shell": "Ran the check:\n```bash\ntest -f x || echo what?\n```",
            "fenced with tildes": "Output:\n~~~\nWHERE name = ?\n~~~",
            "indented code block": "Applied this regex:\n\n    re.match(r'a?b', s)",
            "unclosed fence": "Tail of the log:\n```\nassert x == y  # really?",
        }.items():
            with self.subTest(shape=label):
                self.assertFalse(collect.message_ends_in_question(text))

    def test_a_quoted_or_parenthesized_question_is_reported_not_asked(self) -> None:
        # These close with `"` or `)`, which are deliberately absent from
        # `_TRAILING_MARKDOWN_CHARS`: quoting a question is not asking one.
        for label, text in {
            "quoted": 'The failing assertion prints "are you sure?"',
            "parenthesized": "Left the retry in place (why would we drop it?)",
        }.items():
            with self.subTest(shape=label):
                self.assertFalse(collect.message_ends_in_question(text))

    def test_a_finished_summary_is_never_a_question(self) -> None:
        finished = (
            "All 3 steps are complete. The 69 fail-to-pass tests pass, the 7 "
            "pass-to-pass tests still pass, and the work is committed."
        )
        self.assertFalse(collect.message_ends_in_question(finished))

    def test_absent_or_blank_text_is_not_a_question(self) -> None:
        for text in (None, "", "   \n\n", "```\ncode only\n```"):
            with self.subTest(text=text):
                self.assertFalse(collect.message_ends_in_question(text))


class LastProseLineTests(unittest.TestCase):
    """`message_ends_in_question`'s line selector, pinned on its own so a
    future tweak to either one can't silently change the other's meaning."""

    def test_picks_the_last_non_code_non_blank_line(self) -> None:
        text = "first\n\nsecond\n```\nfenced\n```\n\n   \n"
        self.assertEqual(collect.last_prose_line(text), "second")

    def test_returns_none_when_there_is_no_prose_at_all(self) -> None:
        self.assertIsNone(collect.last_prose_line("```\nonly code\n```"))
        self.assertIsNone(collect.last_prose_line("\n\n    indented only\n"))


class IncompletenessReasonFromSignalsTests(unittest.TestCase):
    def test_a_missing_patch_is_incomplete_whatever_the_final_message_says(self) -> None:
        reason = collect.incompleteness_reason_from_signals(
            has_model_patch=False, final_message="All done, everything is committed."
        )
        self.assertEqual(reason, "no_model_patch")

    def test_a_question_is_incomplete_even_with_a_patch_present(self) -> None:
        reason = collect.incompleteness_reason_from_signals(
            has_model_patch=True, final_message=ABANDONING_QUESTION
        )
        self.assertEqual(reason, "final_message_is_question")

    def test_the_missing_patch_is_reported_first_when_both_fire(self) -> None:
        # The stronger, non-heuristic evidence leads -- see the function's
        # docstring.
        reason = collect.incompleteness_reason_from_signals(
            has_model_patch=False, final_message=ABANDONING_QUESTION
        )
        self.assertEqual(reason, "no_model_patch")

    def test_a_patch_plus_a_finished_message_is_not_incomplete(self) -> None:
        reason = collect.incompleteness_reason_from_signals(
            has_model_patch=True, final_message="Done -- 69/69 fail-to-pass tests pass."
        )
        self.assertIsNone(reason)

    def test_a_patch_and_no_transcript_at_all_is_not_incomplete(self) -> None:
        # A missing final message is not evidence of abandonment; the patch is
        # evidence of work. Conservative direction, deliberately.
        self.assertIsNone(
            collect.incompleteness_reason_from_signals(has_model_patch=True, final_message=None)
        )


def write_trial(
    trial_dir: Path,
    *,
    model_patch: bool = False,
    empty_model_patch: bool = False,
    stream_events: list[dict] | None = None,
) -> Path:
    """Build a temp trial directory in pier's real layout.

    `model_patch` writes a real `artifacts/model.patch`; `empty_model_patch`
    writes a zero-byte one instead (a distinct case -- see
    `trial_has_model_patch`); `stream_events` writes `agent/claude-code.txt` as
    one JSON object per line. Omitting each leaves that path genuinely absent,
    which is the case under test for all of them.
    """
    trial_dir.mkdir(parents=True, exist_ok=True)
    if model_patch or empty_model_patch:
        (trial_dir / "artifacts").mkdir(exist_ok=True)
        contents = "" if empty_model_patch else "diff --git a/x b/x\n"
        (trial_dir / "artifacts" / "model.patch").write_text(contents)
    if stream_events is not None:
        (trial_dir / "agent").mkdir(exist_ok=True)
        (trial_dir / "agent" / "claude-code.txt").write_text(
            "\n".join(json.dumps(event) for event in stream_events)
        )
    return trial_dir


def result_event(message: str, **extra: object) -> dict:
    """A terminal `result` stream event carrying `message` as its answer."""
    return {"type": "result", "subtype": "success", "result": message, **extra}


class FilesystemGateTests(unittest.TestCase):
    """Real temp directories in pier's trial layout -- no mocking."""

    def test_missing_artifacts_directory_reports_no_patch_without_raising(self) -> None:
        # The recorded failure mode: pier's artifact download failed, leaving
        # `artifacts/` with only a manifest -- or, as here, nothing at all.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = write_trial(Path(tmp) / "trial-1")
            self.assertFalse(collect.trial_has_model_patch(trial_dir))
            self.assertEqual(collect.find_trial_incompleteness_reason(trial_dir), "no_model_patch")

    def test_a_missing_trial_directory_entirely_still_does_not_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(collect.trial_has_model_patch(Path(tmp) / "nope"))

    def test_a_present_patch_is_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = write_trial(Path(tmp) / "trial-1", model_patch=True)
            self.assertTrue(collect.trial_has_model_patch(trial_dir))

    def test_a_zero_byte_patch_counts_as_no_patch(self) -> None:
        # An empty patch says the same thing about the agent as a missing one:
        # it committed nothing. Accepting it would let the very condition this
        # gate exists to catch through as `unresolved`.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = write_trial(
                Path(tmp) / "trial-1",
                empty_model_patch=True,
                stream_events=[result_event("All done, everything is committed.")],
            )
            self.assertTrue((trial_dir / "artifacts" / "model.patch").is_file())
            self.assertFalse(collect.trial_has_model_patch(trial_dir))
            self.assertEqual(collect.find_trial_incompleteness_reason(trial_dir), "no_model_patch")

    def test_final_message_is_the_last_result_event_not_the_first(self) -> None:
        # A `--print` session with async sub-agents emits one `result` per
        # resumption; only the last describes how the session ended.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = write_trial(
                Path(tmp) / "trial-1",
                stream_events=[
                    result_event("Step 1 dispatched, waiting on the research agent."),
                    result_event("Step 2 running.", origin={"kind": "task-notification"}),
                    result_event(ABANDONING_QUESTION, origin={"kind": "task-notification"}),
                ],
            )
            self.assertEqual(
                collect.find_stream_log_final_message(trial_dir), ABANDONING_QUESTION
            )

    def test_assistant_text_blocks_are_not_mistaken_for_the_final_message(self) -> None:
        # The documented choice: the `result` field, not the last assistant
        # text block (which may belong to a sub-agent).
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = write_trial(
                Path(tmp) / "trial-1",
                stream_events=[
                    result_event("Everything is committed and the suite is green."),
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "Shall I continue?"}]},
                    },
                ],
            )
            self.assertEqual(
                collect.find_stream_log_final_message(trial_dir),
                "Everything is committed and the suite is green.",
            )

    def test_no_transcript_or_no_result_event_yields_no_final_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            no_log = write_trial(Path(tmp) / "trial-1")
            self.assertIsNone(collect.find_stream_log_final_message(no_log))

            no_result = write_trial(
                Path(tmp) / "trial-2", stream_events=[{"type": "system", "subtype": "init"}]
            )
            self.assertIsNone(collect.find_stream_log_final_message(no_result))

    def test_a_patched_trial_ending_in_a_question_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = write_trial(
                Path(tmp) / "trial-1",
                model_patch=True,
                stream_events=[result_event(ABANDONING_QUESTION)],
            )
            self.assertEqual(
                collect.find_trial_incompleteness_reason(trial_dir), "final_message_is_question"
            )

    def test_a_patched_trial_that_reported_finishing_is_not_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = write_trial(
                Path(tmp) / "trial-1",
                model_patch=True,
                stream_events=[result_event("All 3 steps done; work committed.")],
            )
            self.assertIsNone(collect.find_trial_incompleteness_reason(trial_dir))

    def test_iter_stream_events_skips_junk_and_survives_a_missing_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            (trial_dir / "agent").mkdir(parents=True)
            (trial_dir / "agent" / "claude-code.txt").write_text(
                '\nnot json\n{"type": "result", "result": "done"\n'
                '{"type": "result", "subtype": "success", "result": "really done"}\n'
            )
            events = list(collect.iter_stream_events(trial_dir / "agent" / "claude-code.txt"))
            self.assertEqual([event["result"] for event in events], ["really done"])
            self.assertEqual(list(collect.iter_stream_events(trial_dir / "absent.txt")), [])


RUNS_DIR = BENCHMARK_DIR / "runs"


@unittest.skipUnless(RUNS_DIR.exists(), f"recorded runs not present at {RUNS_DIR}")
class RecordedFinalMessageTests(unittest.TestCase):
    """The question heuristic, run over the real agent prose in `runs/`.

    This is where the rule earns its keep on writing no one composed for it.
    One of the three recorded trials really does end on the abandonment this
    whole change exists for, and the other two end on prose that must NOT trip
    it -- including one closing on a bolded status line and a quoted judge
    verdict that itself contains a full stop and quotation marks.

    Every recorded final message is classified explicitly, and the test fails
    if `runs/` gains or loses a trial, so a new recording cannot slip through
    unclassified.
    """

    # The verdict the heuristic gives for each recorded trial's final `result`
    # message, with the closing prose line that decides it:
    #
    # _preflight/…HyQJyYy   False
    #   "**Status: Ready for merge. All requirements met. Feature complete and
    #    correct.**" -- markdown emphasis stripped, ends in a full stop.
    #
    # _preflight-do-in-steps/…9ryVMmH   True
    #   "Which approach would you prefer? Or shall I continue with the current
    #    orchestration pace?" -- a real recorded abandonment: the agent hit
    #   budget pressure, offered a numbered menu ("Should I: 1… 2… 3…") and
    #   ended its turn asking the operator to choose, with no stdin for anyone
    #   to answer through. Exactly the failure Fix 2's prompt contract and this
    #   signal exist for, observed rather than imagined.
    #
    # do-in-steps__sonnet-sonnet/…ZsbwRdJ   False
    #   "Meta-judge for Step 6 is done. Waiting on the implementation agent to
    #    finish the final gap-fill work." -- a progress note; that trial is
    #   caught by the missing-patch signal instead.
    EXPECTED_VERDICTS = {
        "_preflight/abs-stepped-slices__HyQJyYy": False,
        "_preflight-do-in-steps/cattrs-partial-structuring-recov__9ryVMmH": True,
        "do-in-steps__sonnet-sonnet/cattrs-partial-structuring-recov__ZsbwRdJ": False,
    }

    def test_every_recorded_final_message_is_classified_explicitly(self) -> None:
        seen = {}
        for result_path in sorted(RUNS_DIR.glob("*/*/result.json")):
            trial_dir = result_path.parent
            trial_key = f"{trial_dir.parent.name}/{trial_dir.name}"
            final_message = collect.find_stream_log_final_message(trial_dir)
            seen[trial_key] = collect.message_ends_in_question(final_message)

        # A new recording is not a silent pass: it has to be classified here.
        self.assertEqual(
            sorted(seen), sorted(self.EXPECTED_VERDICTS),
            "runs/ gained or lost a trial -- classify its final message above",
        )
        for trial_key, expected in self.EXPECTED_VERDICTS.items():
            with self.subTest(trial=trial_key):
                self.assertEqual(seen[trial_key], expected)

    def test_the_recorded_abandonment_is_caught_on_its_own_prose(self) -> None:
        # The positive case, isolated: feed only the recorded message to the
        # rule, so this fails if the heuristic ever stops catching real
        # abandonment prose (rather than passing because a patch was missing).
        trial_dir = RUNS_DIR / "_preflight-do-in-steps" / "cattrs-partial-structuring-recov__9ryVMmH"
        final_message = collect.find_stream_log_final_message(trial_dir)
        self.assertIsNotNone(final_message)
        self.assertTrue(collect.message_ends_in_question(final_message))
        self.assertEqual(
            collect.incompleteness_reason_from_signals(
                has_model_patch=True, final_message=final_message
            ),
            "final_message_is_question",
        )

    def test_the_recorded_trials_all_trip_the_missing_patch_signal(self) -> None:
        # Precedence on real data: none of the three committed anything, so the
        # patch check answers first even for the trial that also ends on a
        # question.
        for result_path in sorted(RUNS_DIR.glob("*/*/result.json")):
            trial_dir = result_path.parent
            with self.subTest(trial=trial_dir.name):
                self.assertEqual(
                    collect.find_trial_incompleteness_reason(trial_dir), "no_model_patch"
                )


class IncompleteAggregationTests(unittest.TestCase):
    """`incomplete` trials count as failed attempts, unlike `errored` ones."""

    def test_incomplete_trials_stay_in_the_pass_at_1_denominator(self) -> None:
        # The docstring's worked example: 6 resolved, 2 unresolved, 1
        # incomplete, 2 errored.
        trials = (
            [make_trial("resolved") for _ in range(6)]
            + [make_trial("unresolved") for _ in range(2)]
            + [make_trial("incomplete")]
            + [make_trial("errored") for _ in range(2)]
        )
        aggregate = collect.aggregate_arm(trials)

        self.assertEqual(aggregate.n_incomplete, 1)
        self.assertEqual(aggregate.n_attempts, 9)
        self.assertEqual(aggregate.n_total_trials, 11)
        self.assertAlmostEqual(aggregate.pass_at_1, 6 / 9)

    def test_abandoning_a_task_cannot_raise_an_arms_pass_at_1(self) -> None:
        # The incentive this choice exists to remove: if incomplete trials were
        # dropped like errored ones, an arm that walked away from the tasks it
        # was losing would score better than one that tried and failed.
        tried_and_failed = [make_trial("resolved"), make_trial("unresolved")]
        walked_away = [make_trial("resolved"), make_trial("incomplete")]
        self.assertEqual(
            collect.aggregate_arm(tried_and_failed).pass_at_1,
            collect.aggregate_arm(walked_away).pass_at_1,
        )

    def test_incomplete_trial_costs_are_reported_not_dropped(self) -> None:
        # With no spend cap in the harness, a runaway trial's cost is only
        # visible if it is actually reported -- and the max is what an average
        # over many trials hides.
        trials = [
            make_trial("resolved", cost_usd=1.0),
            make_trial("incomplete", cost_usd=26.53),
        ]
        aggregate = collect.aggregate_arm(trials)

        self.assertAlmostEqual(aggregate.avg_cost_usd, (1.0 + 26.53) / 2)
        self.assertEqual(aggregate.max_cost_usd, 26.53)

    def test_max_cost_reports_none_rather_than_zero_without_data(self) -> None:
        aggregate = collect.aggregate_arm([make_trial("errored", cost_usd=None)])
        self.assertIsNone(aggregate.max_cost_usd)
        self.assertIsNone(aggregate.avg_cost_usd)


if __name__ == "__main__":
    unittest.main()
