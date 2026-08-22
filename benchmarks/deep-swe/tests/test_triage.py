#!/usr/bin/env python3
"""Unit tests for `triage.py`: the rules that decide whether a run gets retried.

WHY THIS FILE EXISTS
---------------------
`triage.py` decides, unattended and with nobody watching, whether a finished
trial is the benchmark's product or was never a fair attempt. Getting it wrong
is expensive in both directions -- the module's own docstring lays out the
asymmetry -- and for a long time its rules were pinned only *indirectly*, by a
handful of cases inside `tests/test_run_scheduled.py`, whose subject is the
scheduling loop rather than the triage. Two defects shipped under that
arrangement, and both were the kind of thing a direct test would have caught:

  * `allowed_warning` -- a utilization NOTICE that means requests are still
    being served -- read as an API-side refusal, so every trial triaged
    `technical_failure` once an account crossed 75% weekly utilization,
    burning 3 attempts x 2h backoff per cell on every invocation.
  * `reward == 1` ranked below pier's exception type, so a trial that solved
    its task and was then killed by a 429 on the way out was discarded and
    re-run instead of recorded as the solve it was.

Both are pinned below, by name.

NO `pier`, NO `runs/`
----------------------
`triage.py` imports only stdlib plus `collect.py`, and that is deliberate (see
`.claude/rules/pure-core-for-third-party-dependent-logic.md`): a rule whose
tests skip is a rule with no tests. So everything in this file except
`RecordedTriageTests` runs in any checkout, off plain values and the committed
`tests/fixtures/recorded-rate-limit-events.txt`. `RecordedTriageTests` is the
one class that needs the gitignored `runs/` tree and skips without it, matching
`tests/test_readme_claims.py` and `tests/test_collect_completion_gate.py`.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import triage

from . import BENCHMARK_DIR

RUNS_DIR = BENCHMARK_DIR / "runs"
RATE_LIMIT_FIXTURE = BENCHMARK_DIR / "tests" / "fixtures" / "recorded-rate-limit-events.txt"

# The two recorded job directories this module's two shipped defects were found
# in. Both are `abs-stepped-slices` under opus/opus, and they fail in opposite
# directions, which is why both are named here rather than only the dramatic one.
CLEAN_BUT_UNRESOLVED_JOB = "do-and-judge__opus-opus__abs-stepped-slices"
SOLVED_THEN_KILLED_JOB = "do-in-steps__opus-opus__abs-stepped-slices"


def fixture_lines() -> list[str]:
    """The committed rate-limit fixture, comments included.

    The `#` header lines are handed to the scan on purpose: they are exactly
    the "not JSON, skip it" case, and keeping them means the line numbers this
    file asserts on are the fixture's own.
    """
    return RATE_LIMIT_FIXTURE.read_text(encoding="utf-8").splitlines()


# --------------------------------------------------------------------------
# The status vocabulary
# --------------------------------------------------------------------------


class RateLimitStatusVocabularyTests(unittest.TestCase):
    """What each `rate_limit_info.status` means, and which way an unknown falls."""

    def scan(self, status: object) -> triage.ApiFault | None:
        event = {"type": "rate_limit_event", "rate_limit_info": {"status": status}}
        return triage.api_fault_from_stream_lines([json.dumps(event)])

    def test_allowed_is_not_a_fault(self) -> None:
        self.assertIsNone(self.scan("allowed"))

    def test_allowed_warning_is_not_a_fault(self) -> None:
        # THE defect. claude-code emits this once per request when an account
        # is over a utilization threshold; the request is still served, and
        # reading it as a denial failed every trial an over-quota account ran.
        self.assertIsNone(self.scan("allowed_warning"))

    def test_any_allowed_prefixed_status_is_not_a_fault(self) -> None:
        # The rule is a prefix rule rather than a two-name allowlist, so a
        # third suffix cannot reintroduce the defect above.
        self.assertIsNone(self.scan("allowed_something_new"))

    def test_rejected_is_a_fault(self) -> None:
        fault = self.scan("rejected")
        self.assertIsNotNone(fault)
        self.assertEqual(fault.slug, "rate_limit_status=rejected")
        self.assertEqual(fault.severity, triage.SEVERITY_RATE_LIMIT_REJECTED)

    def test_an_unrecognised_status_is_a_fault_at_the_lowest_severity(self) -> None:
        # Deliberate direction, documented at `_rate_limit_severity`: an
        # unknown status may not be silently read as "served". A bounded,
        # visible retry beats a permanent zero for a trial nobody can prove
        # was ever answered -- and the spelling lands in the state file where
        # an operator will see it and classify it on purpose.
        fault = self.scan("throttled")
        self.assertIsNotNone(fault)
        self.assertEqual(fault.slug, "rate_limit_status=throttled")
        self.assertEqual(fault.severity, triage.SEVERITY_UNRECOGNISED_RATE_LIMIT_STATUS)

    def test_a_non_string_status_is_graded_rather_than_crashed_on(self) -> None:
        # A half-written transcript must never raise out of triage.
        fault = self.scan(7)
        self.assertIsNotNone(fault)
        self.assertEqual(fault.severity, triage.SEVERITY_UNRECOGNISED_RATE_LIMIT_STATUS)

    def test_an_absent_status_is_not_a_fault(self) -> None:
        # Absence is not denial. An event making no claim about whether the
        # request was served is not evidence that it was refused.
        self.assertIsNone(self.scan(None))
        self.assertIsNone(
            triage.api_fault_from_stream_lines([json.dumps({"type": "rate_limit_event"})])
        )

    def test_a_malformed_rate_limit_info_cannot_raise(self) -> None:
        self.assertIsNone(
            triage.api_fault_from_stream_lines(
                [json.dumps({"type": "rate_limit_event", "rate_limit_info": "not a mapping"})]
            )
        )


# --------------------------------------------------------------------------
# The transcript scan: what fires, what does not, and which one wins
# --------------------------------------------------------------------------


class ApiFaultScanTests(unittest.TestCase):
    """The scan over whole events. The negatives matter as much as the positives."""

    def scan(self, *events: dict) -> triage.ApiFault | None:
        return triage.api_fault_from_stream_lines(json.dumps(event) for event in events)

    def test_a_clean_result_event_is_not_a_fault(self) -> None:
        self.assertIsNone(
            self.scan({"type": "result", "subtype": "success", "is_error": False,
                       "terminal_reason": "completed", "api_error_status": None})
        )

    def test_a_populated_api_error_status_is_a_fault_naming_the_status(self) -> None:
        fault = self.scan({"type": "result", "api_error_status": 529})
        self.assertEqual(fault.slug, "api_error_status=529")
        self.assertEqual(fault.severity, triage.SEVERITY_API_ERROR_STATUS)

    def test_overage_status_rejected_is_deliberately_not_a_fault(self) -> None:
        # It reads "rejected" inside ALLOWED events too, in this repository's
        # own recordings. Keying on it would fail most runs as quota denials.
        self.assertIsNone(
            self.scan({"type": "rate_limit_event",
                       "rate_limit_info": {"status": "allowed", "overageStatus": "rejected"}})
        )

    def test_the_number_529_in_ordinary_content_is_not_a_fault(self) -> None:
        # 14-71 such substrings appear per recorded transcript, all benign:
        # source line numbers, uuid fragments, timestamp milliseconds.
        self.assertIsNone(
            self.scan({"type": "user", "message": {"content": [
                {"type": "tool_result", "content": "529\\t\\treturn evalIndexAssignment(...)"}]},
                "uuid": "0e966324-9529-4b50-9034-3389c980a856",
                "timestamp": "2026-08-15T17:14:55.529Z"})
        )

    def test_unparseable_blank_and_non_json_lines_are_skipped(self) -> None:
        # A truncated final line is normal in a log still being written.
        lines = ["", "not json at all", "{truncated",
                 json.dumps({"type": "result", "api_error_status": 429})]
        self.assertEqual(triage.api_fault_from_stream_lines(lines).slug, "api_error_status=429")

    def test_a_truncated_final_line_cannot_hide_an_earlier_fault(self) -> None:
        lines = [json.dumps({"type": "result", "api_error_status": 429}), '{"type":"resu']
        self.assertEqual(triage.api_fault_from_stream_lines(lines).slug, "api_error_status=429")

    def test_a_non_dict_json_line_is_skipped(self) -> None:
        self.assertIsNone(triage.api_fault_from_stream_lines(['{}', '["a list"]']))

    def test_an_empty_transcript_is_not_a_fault(self) -> None:
        self.assertIsNone(triage.api_fault_from_stream_lines([]))


class WorstFaultWinsTests(unittest.TestCase):
    """The scan reports the WORST fault in a transcript, never merely the first.

    This replaces an earlier `the_first_fault_wins_and_the_scan_stops`. First
    wins is wrong for the shape a real quota exhaustion has: the recorded
    `do-in-steps__opus-opus__abs-stepped-slices` opens with a benign notice
    thousands of lines before the denial that actually stopped it, so
    first-wins reported the notice and the state file named the wrong cause.
    """

    def scan(self, *events: dict) -> triage.ApiFault | None:
        return triage.api_fault_from_stream_lines(json.dumps(event) for event in events)

    def rate_limit(self, status: str) -> dict:
        return {"type": "rate_limit_event", "rate_limit_info": {"status": status}}

    def test_the_severity_order_is_rejected_then_api_error_then_unrecognised(self) -> None:
        # Pins the ordering itself, so a reshuffle has to be deliberate.
        self.assertGreater(
            triage.SEVERITY_RATE_LIMIT_REJECTED, triage.SEVERITY_API_ERROR_STATUS
        )
        self.assertGreater(
            triage.SEVERITY_API_ERROR_STATUS, triage.SEVERITY_UNRECOGNISED_RATE_LIMIT_STATUS
        )

    def test_a_trailing_denial_outranks_a_leading_unrecognised_status(self) -> None:
        fault = self.scan(self.rate_limit("throttled"), self.rate_limit("rejected"))
        self.assertEqual(fault.slug, "rate_limit_status=rejected")

    def test_a_leading_denial_is_not_displaced_by_a_weaker_later_fault(self) -> None:
        fault = self.scan(self.rate_limit("rejected"), {"type": "result", "api_error_status": 529})
        self.assertEqual(fault.slug, "rate_limit_status=rejected")

    def test_an_api_error_outranks_an_unrecognised_rate_limit_status(self) -> None:
        fault = self.scan(self.rate_limit("throttled"), {"type": "result", "api_error_status": 529})
        self.assertEqual(fault.slug, "api_error_status=529")

    def test_ties_keep_the_earliest_occurrence(self) -> None:
        fault = self.scan(
            {"type": "result", "api_error_status": 529},
            {"type": "result", "api_error_status": 429},
        )
        self.assertEqual(fault.slug, "api_error_status=529")

    def test_benign_events_never_shadow_a_real_one_however_many_there_are(self) -> None:
        # The recorded shape: 21 allowed_warning notices, then the denial.
        events = [self.rate_limit("allowed_warning")] * 21 + [self.rate_limit("rejected")]
        fault = self.scan(*events)
        self.assertEqual(fault.slug, "rate_limit_status=rejected")
        self.assertEqual(fault.faults_seen, 1)


class ApiFaultEvidenceTests(unittest.TestCase):
    """The evidence a fault carries, which is what makes a reason auditable."""

    def test_the_line_number_is_the_transcripts_own(self) -> None:
        # Skipped lines still advance the count, so the number points at the
        # line an operator would go and read.
        lines = ["", "not json", json.dumps({"type": "result", "api_error_status": 429})]
        self.assertEqual(triage.api_fault_from_stream_lines(lines).line_number, 3)

    def test_the_raw_event_is_carried_verbatim(self) -> None:
        # Not a summary of it: the defect this evidence exists to catch was a
        # rule misreading a benign event, and only the event itself shows that.
        event = {"type": "rate_limit_event", "rate_limit_info": {
            "status": "rejected", "rateLimitType": "five_hour",
            "overageDisabledReason": "out_of_credits"}}
        fault = triage.api_fault_from_stream_lines([json.dumps(event)])
        self.assertEqual(fault.event, event)

    def test_faults_seen_counts_every_fault_not_just_the_worst(self) -> None:
        lines = [
            json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "rejected"}}),
            json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed"}}),
            json.dumps({"type": "result", "api_error_status": 429}),
        ]
        self.assertEqual(triage.api_fault_from_stream_lines(lines).faults_seen, 2)

    def test_the_log_record_is_json_serialisable_and_names_everything(self) -> None:
        fault = triage.api_fault_from_stream_lines(
            [json.dumps({"type": "result", "api_error_status": 429})]
        )
        record = fault.as_record()
        self.assertEqual(
            set(record), {"slug", "severity", "line_number", "faults_seen", "event"}
        )
        json.dumps(record)  # would raise if the evidence could not be logged

    def test_the_human_form_names_the_line(self) -> None:
        fault = triage.ApiFault(slug="rate_limit_status=rejected", severity=3, line_number=2936)
        self.assertIn("2936", str(fault))
        self.assertIn("rate_limit_status=rejected", str(fault))


class RecordedRateLimitFixtureTests(unittest.TestCase):
    """The scan over the committed fixture of real recorded events.

    Runs in any checkout, `runs/` present or not -- which is the point: these
    are the exact event shapes the two defects turned on, and a test that
    skipped when the recorded artifacts were absent would prove nothing.
    """

    def test_the_fixture_holds_all_three_observed_statuses(self) -> None:
        statuses = [
            json.loads(line)["rate_limit_info"]["status"]
            for line in fixture_lines()
            if line.startswith("{") and json.loads(line)["type"] == "rate_limit_event"
        ]
        self.assertEqual(statuses, ["allowed", "allowed_warning", "allowed_warning", "rejected"])

    def test_the_denial_wins_over_the_notices_that_precede_it(self) -> None:
        fault = triage.api_fault_from_stream_lines(fixture_lines())
        self.assertEqual(fault.slug, "rate_limit_status=rejected")
        self.assertEqual(fault.event["rate_limit_info"]["rateLimitType"], "five_hour")

    def test_both_real_faults_are_counted(self) -> None:
        # The `rejected` event and the 429 result five lines after it. The two
        # `allowed_warning` notices and the `allowed` event are not faults.
        self.assertEqual(triage.api_fault_from_stream_lines(fixture_lines()).faults_seen, 2)

    def test_the_notices_alone_are_not_a_fault(self) -> None:
        # Drop the denial and the 429: what is left is a heavily-used but
        # perfectly healthy account, and it must scan clean.
        served = [line for line in fixture_lines() if '"rejected"' not in line
                  and "api_error_status" not in line]
        self.assertIsNone(triage.api_fault_from_stream_lines(served))


# --------------------------------------------------------------------------
# The verdict rules
# --------------------------------------------------------------------------


class VerdictRuleTests(unittest.TestCase):
    """One test per branch of `triage.verdict_from_signals`."""

    def judge(self, **overrides) -> triage.Verdict:
        signals = {
            "has_trial_result": True,
            "exception_type": None,
            "has_rewards": True,
            "resolved": False,
            "incompleteness_reason": None,
            "api_fault": None,
        }
        signals.update(overrides)
        return triage.verdict_from_signals(**signals)

    def fault(self, slug: str = "api_error_status=429") -> triage.ApiFault:
        return triage.ApiFault(
            slug=slug, severity=triage.SEVERITY_API_ERROR_STATUS, line_number=1
        )

    # --- rule 1: no trial result -----------------------------------------

    def test_a_missing_result_json_is_technical(self) -> None:
        verdict = self.judge(has_trial_result=False)
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, triage.NO_TRIAL_RESULT_REASON)

    def test_a_solve_claimed_for_a_trial_that_never_ran_is_still_technical(self) -> None:
        # The combination `triage_job_dir` cannot produce but a backfill or
        # re-triage caller reading `resolved` off a rewards file alone can:
        # rewards say solved, yet no `result.json` exists. Rule 1 sits above
        # rule 2 precisely so this cannot be reported as a success -- writing
        # a fabricated solve into the benchmark's product is the one error
        # this module cannot walk back. Pinned here rather than argued in
        # prose, because the guard is branch order and nothing else.
        verdict = self.judge(has_trial_result=False, resolved=True)
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, triage.NO_TRIAL_RESULT_REASON)

    # --- rule 2: resolved ------------------------------------------------

    def test_a_resolved_trial_is_a_success(self) -> None:
        verdict = self.judge(resolved=True)
        self.assertEqual(verdict.outcome, triage.SUCCESS)
        self.assertEqual(verdict.reason, "resolved")

    # --- rule 3: pier's exception ----------------------------------------

    def test_infrastructure_exceptions_are_technical(self) -> None:
        for exception_type in sorted(triage.TECHNICAL_EXCEPTION_TYPES):
            with self.subTest(exception_type=exception_type):
                verdict = self.judge(exception_type=exception_type)
                self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
                self.assertIn(exception_type, verdict.reason)

    def test_an_unknown_exception_type_is_technical_and_says_so(self) -> None:
        verdict = self.judge(exception_type="SomeBrandNewError")
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertIn("unrecognised", verdict.reason)

    def test_an_agent_timeout_is_the_model_running_out_of_clock(self) -> None:
        verdict = self.judge(exception_type=triage.AGENT_TIMEOUT_EXCEPTION_TYPE)
        self.assertEqual(verdict.outcome, triage.MODEL_FAILURE)
        self.assertEqual(verdict.reason, "agent_timeout")

    def test_an_agent_timeout_under_an_api_fault_is_technical_instead(self) -> None:
        # An agent starved by a quota did not spend that clock thinking.
        verdict = self.judge(
            exception_type=triage.AGENT_TIMEOUT_EXCEPTION_TYPE,
            api_fault=self.fault("rate_limit_status=rejected"),
        )
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, "api_fault:rate_limit_status=rejected")

    def test_an_unexplained_nonzero_exit_defaults_to_technical(self) -> None:
        # The documented asymmetry: a bounded overspend beats a permanently
        # biased data point. See triage.AMBIGUOUS_NONZERO_EXIT_REASON.
        verdict = self.judge(exception_type=triage.AMBIGUOUS_EXCEPTION_TYPE)
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, triage.AMBIGUOUS_NONZERO_EXIT_REASON)

    def test_a_nonzero_exit_with_evidence_names_the_evidence(self) -> None:
        verdict = self.judge(
            exception_type=triage.AMBIGUOUS_EXCEPTION_TYPE, api_fault=self.fault()
        )
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertIn("429", verdict.reason)

    # --- rule 4: no rewards ----------------------------------------------

    def test_an_unscored_trial_is_technical(self) -> None:
        # The grader produced nothing, so there is no measurement to keep.
        verdict = self.judge(has_rewards=False)
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, "missing_verifier_rewards")

    # --- rule 5: an API fault in the transcript --------------------------

    def test_an_api_fault_rescues_a_clean_exit_that_produced_no_patch(self) -> None:
        # The case pier's exit code misses entirely: a session truncated by a
        # quota denial exits 0 and would otherwise be blamed on the model.
        verdict = self.judge(incompleteness_reason="no_model_patch", api_fault=self.fault())
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, "api_fault:api_error_status=429")

    # --- rules 6 and 7: the model attempted and lost ---------------------

    def test_an_incomplete_trial_is_a_model_failure_carrying_its_reason(self) -> None:
        for reason in ("no_model_patch", "final_message_is_question"):
            with self.subTest(reason=reason):
                verdict = self.judge(incompleteness_reason=reason)
                self.assertEqual(verdict.outcome, triage.MODEL_FAILURE)
                self.assertEqual(verdict.reason, reason)

    def test_an_unresolved_trial_is_a_model_failure(self) -> None:
        verdict = self.judge()
        self.assertEqual(verdict.outcome, triage.MODEL_FAILURE)
        self.assertEqual(verdict.reason, "unresolved")


class ResolvedOutranksEverythingTests(unittest.TestCase):
    """Rule 2: `reward == 1` beats every fault, exception and heuristic.

    Every signal below it, that is. The one signal above it -- no
    `result.json` at all -- is covered by
    `VerdictRuleTests.test_a_solve_claimed_for_a_trial_that_never_ran_is_still_technical`.

    The second shipped defect. `resolved` used to sit below `exception_type`,
    so `runs/do-in-steps__opus-opus__abs-stepped-slices` -- a 131 KB patch the
    verifier scored `reward 1`, whose `claude` process was then killed by a 429
    -- was triaged technical, thrown away, and re-run three times. A verified
    solve is the one thing this harness can never recover after discarding.
    """

    def judge(self, **overrides) -> triage.Verdict:
        signals = {
            "has_trial_result": True,
            "exception_type": None,
            "has_rewards": True,
            "resolved": True,
            "incompleteness_reason": None,
            "api_fault": None,
        }
        signals.update(overrides)
        return triage.verdict_from_signals(**signals)

    def test_a_solve_survives_the_exception_type_that_killed_the_process(self) -> None:
        verdict = self.judge(exception_type=triage.AMBIGUOUS_EXCEPTION_TYPE)
        self.assertEqual(verdict.outcome, triage.SUCCESS)
        self.assertEqual(verdict.reason, "resolved")

    def test_a_solve_survives_every_exception_type_this_module_knows(self) -> None:
        types = sorted(triage.TECHNICAL_EXCEPTION_TYPES) + [
            triage.AGENT_TIMEOUT_EXCEPTION_TYPE,
            triage.AMBIGUOUS_EXCEPTION_TYPE,
            "SomeBrandNewError",
        ]
        for exception_type in types:
            with self.subTest(exception_type=exception_type):
                self.assertEqual(self.judge(exception_type=exception_type).outcome, triage.SUCCESS)

    def test_a_solve_survives_an_api_fault(self) -> None:
        fault = triage.ApiFault(
            slug="api_error_status=429",
            severity=triage.SEVERITY_API_ERROR_STATUS,
            line_number=2941,
        )
        self.assertEqual(self.judge(api_fault=fault).outcome, triage.SUCCESS)

    def test_a_solve_survives_both_at_once(self) -> None:
        # The exact recorded combination: a 429 in the transcript AND
        # NonZeroAgentExitCodeError from pier, over a reward-1 bundle.
        verdict = self.judge(
            exception_type=triage.AMBIGUOUS_EXCEPTION_TYPE,
            api_fault=triage.ApiFault(
                slug="api_error_status=429",
                severity=triage.SEVERITY_API_ERROR_STATUS,
                line_number=2941,
            ),
        )
        self.assertEqual(verdict.outcome, triage.SUCCESS)
        self.assertEqual(verdict.reason, "resolved")

    def test_a_solve_survives_the_completion_gate(self) -> None:
        self.assertEqual(
            self.judge(incompleteness_reason="no_model_patch").outcome, triage.SUCCESS
        )

    def test_the_evidence_still_travels_with_the_success(self) -> None:
        # `reason` says which rule fired; `fault` says what the transcript
        # held. A solve the API 429'd is still worth having in the log.
        fault = triage.ApiFault(
            slug="api_error_status=429",
            severity=triage.SEVERITY_API_ERROR_STATUS,
            line_number=2941,
        )
        verdict = self.judge(api_fault=fault)
        self.assertEqual(verdict.reason, "resolved")
        self.assertEqual(verdict.fault, fault)


class VerdictEvidenceTests(unittest.TestCase):
    """`Verdict` carries what was judged, not only how it was judged."""

    def judge(self, **overrides) -> triage.Verdict:
        signals = {
            "has_trial_result": True,
            "exception_type": None,
            "has_rewards": True,
            "resolved": False,
            "incompleteness_reason": None,
            "api_fault": None,
        }
        signals.update(overrides)
        return triage.verdict_from_signals(**signals)

    def test_a_verdict_with_nothing_to_show_carries_nothing(self) -> None:
        verdict = self.judge()
        self.assertIsNone(verdict.fault)
        self.assertIsNone(verdict.trial_dir)

    def test_the_trial_dir_travels_when_the_caller_supplies_it(self) -> None:
        verdict = self.judge(trial_dir=Path("runs/arm/trial-1"))
        self.assertEqual(verdict.trial_dir, Path("runs/arm/trial-1"))

    def test_the_string_form_is_unchanged_by_the_evidence(self) -> None:
        # `report_scheduled_summary` and README's quoted output both depend on
        # this exact shape; the evidence is appended by the caller that wants
        # it (`scheduler.describe_verdict`), never here.
        verdict = self.judge(
            resolved=True,
            api_fault=triage.ApiFault("api_error_status=429", 2, 2941),
            trial_dir=Path("runs/arm/trial-1"),
        )
        self.assertEqual(str(verdict), "success (resolved)")

    def test_is_technical_only_for_technical_failures(self) -> None:
        self.assertTrue(self.judge(has_trial_result=False).is_technical)
        self.assertFalse(self.judge().is_technical)
        self.assertFalse(self.judge(resolved=True).is_technical)


# --------------------------------------------------------------------------
# The shell: gathering signals off disk
# --------------------------------------------------------------------------


class TrialDirectoryResolutionTests(unittest.TestCase):
    """`find_trial_dir` / `triage_job_dir` over staged directories."""

    def test_a_job_dir_with_no_trial_at_all_is_technical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(triage.find_trial_dir(Path(tmp)))
            verdict = triage.triage_job_dir(Path(tmp))
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, triage.NO_TRIAL_RESULT_REASON)

    def test_an_unparseable_result_json_reads_as_no_result_at_all(self) -> None:
        # A job interrupted mid-write is a technical failure by any reading.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            trial_dir.mkdir()
            (trial_dir / "result.json").write_text("{truncated")
            verdict = triage.triage_job_dir(Path(tmp))
        self.assertEqual(verdict.reason, triage.NO_TRIAL_RESULT_REASON)

    def test_a_missing_stream_log_is_not_a_fault(self) -> None:
        # It means the agent never started, which `has_trial_result` covers.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(triage.find_api_fault(Path(tmp)))

    def test_the_judged_trial_dir_is_reported_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = self._staged_trial(Path(tmp), exception_type="AgentTimeoutError")
            verdict = triage.triage_job_dir(Path(tmp))
        self.assertEqual(verdict.trial_dir, trial_dir)

    def _staged_trial(self, job_dir: Path, *, exception_type: str) -> Path:
        trial_dir = job_dir / "trial-1"
        trial_dir.mkdir()
        (trial_dir / "result.json").write_text(
            json.dumps({"exception_info": {"exception_type": exception_type},
                        "verifier_result": None})
        )
        return trial_dir


class SyntheticExceptionInfoTriageTests(unittest.TestCase):
    """`triage_job_dir`'s one line converting pier's recorded `exception_info`
    into `verdict_from_signals`' `exception_type` argument --
    `exception_info.get("exception_type") if exception_info else None` -- is
    the most load-bearing artifact read in the whole triage, and almost every
    real job dir under `runs/` carries `exception_info: null`. These stage a
    synthetic trial directory with a POPULATED `exception_info` so the truthy
    branch is exercised without depending on `runs/` at all.
    """

    def _job_dir_with_exception(self, tmp: str, *, exception_type: str) -> Path:
        job_dir = Path(tmp)
        trial_dir = job_dir / "trial-1"
        trial_dir.mkdir()
        (trial_dir / "result.json").write_text(
            json.dumps(
                {
                    "exception_info": {"exception_type": exception_type},
                    "verifier_result": None,
                }
            )
        )
        return job_dir

    def test_a_populated_infrastructure_exception_type_is_a_technical_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = self._job_dir_with_exception(
                tmp, exception_type="EnvironmentStartTimeoutError"
            )
            verdict = triage.triage_job_dir(job_dir)
        self.assertEqual(verdict.outcome, triage.TECHNICAL_FAILURE)
        self.assertEqual(verdict.reason, "pier_exception:EnvironmentStartTimeoutError")

    def test_a_populated_agent_timeout_exception_type_is_a_model_failure(self) -> None:
        # Proves the shell threads whatever exception_type it reads all the
        # way through to `_verdict_for_exception`'s dispatch, not just to
        # the technical branch every other case here happens to land on.
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = self._job_dir_with_exception(
                tmp, exception_type=triage.AGENT_TIMEOUT_EXCEPTION_TYPE
            )
            verdict = triage.triage_job_dir(job_dir)
        self.assertEqual(verdict.outcome, triage.MODEL_FAILURE)
        self.assertEqual(verdict.reason, "agent_timeout")

    def test_a_solved_trial_outranks_a_populated_exception_on_disk(self) -> None:
        # End-to-end over the shell, not just the pure rule: the recorded
        # `do-in-steps__opus-opus` combination, staged so it runs without
        # `runs/`.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            (trial_dir / "artifacts").mkdir(parents=True)
            (trial_dir / "artifacts" / "model.patch").write_text("diff --git a/x b/x\n")
            (trial_dir / "result.json").write_text(
                json.dumps({
                    "exception_info": {"exception_type": "NonZeroAgentExitCodeError"},
                    "verifier_result": {"rewards": {"reward": 1, "f2p": 1.0, "p2p": 1.0}},
                })
            )
            verdict = triage.triage_job_dir(Path(tmp))
        self.assertEqual(verdict.outcome, triage.SUCCESS)
        self.assertEqual(verdict.reason, "resolved")


# --------------------------------------------------------------------------
# Triage against the real recorded artifacts
# --------------------------------------------------------------------------


@unittest.skipUnless(RUNS_DIR.exists(), f"recorded runs not present at {RUNS_DIR}")
class RecordedTriageTests(unittest.TestCase):
    """The triage, run over the real pier job directories under `runs/`.

    These are the only recorded evidence this repository holds about what a
    claude transcript actually contains, and they are also what caught both
    defects this module shipped. Every assertion here is a fact about the
    committed artifacts, re-derived rather than restated -- so a future
    recording that genuinely does contain a technical failure fails this class
    loudly instead of being absorbed.
    """

    def job_dirs(self) -> list[Path]:
        return sorted(path for path in RUNS_DIR.iterdir() if path.is_dir())

    def test_there_are_recorded_runs_to_check(self) -> None:
        # Guards every other test in this class against an empty runs/ tree.
        self.assertGreaterEqual(len(self.job_dirs()), 5)

    def test_every_recorded_run_produced_a_trial_to_judge(self) -> None:
        for job_dir in self.job_dirs():
            with self.subTest(job=job_dir.name):
                self.assertIsNotNone(triage.find_trial_dir(job_dir))

    def test_no_recorded_run_is_triaged_as_a_technical_failure(self) -> None:
        # The property that used to be false for four of these job dirs, and
        # is the whole point of the `allowed_warning` fix: every recorded run
        # either solved its task or lost it, and none of them is "no data".
        for job_dir in self.job_dirs():
            with self.subTest(job=job_dir.name):
                verdict = triage.triage_job_dir(job_dir)
                self.assertNotEqual(verdict.outcome, triage.TECHNICAL_FAILURE, str(verdict))

    def test_only_one_recorded_transcript_trips_the_api_fault_scan(self) -> None:
        tripped = {
            job_dir.name
            for job_dir in self.job_dirs()
            if triage.find_api_fault(triage.find_trial_dir(job_dir)) is not None
        }
        self.assertEqual(tripped, {SOLVED_THEN_KILLED_JOB})

    def test_the_one_real_fault_is_the_denial_not_the_notice_before_it(self) -> None:
        # Worst-fault-wins over 2,900 lines of real transcript. First-wins
        # reported `allowed_warning` from line 6 instead.
        fault = triage.find_api_fault(triage.find_trial_dir(RUNS_DIR / SOLVED_THEN_KILLED_JOB))
        self.assertEqual(fault.slug, "rate_limit_status=rejected")
        self.assertEqual(fault.line_number, 2936)
        self.assertEqual(fault.event["rate_limit_info"]["overageDisabledReason"], "out_of_credits")

    def test_the_solved_but_killed_run_is_recorded_as_the_success_it_is(self) -> None:
        # reward 1, f2p 1.0, a 131 KB patch -- and NonZeroAgentExitCodeError
        # from the 429 that killed claude on its way out. Triaging this
        # technical discarded a verified solve and paid for it three times.
        verdict = triage.triage_job_dir(RUNS_DIR / SOLVED_THEN_KILLED_JOB)
        self.assertEqual(verdict.outcome, triage.SUCCESS)
        self.assertEqual(verdict.reason, "resolved")

    def test_a_clean_run_the_verifier_failed_is_an_honest_model_failure(self) -> None:
        # The other defect, and the quieter one: this trial has
        # `exception_info: null`, one clean `result` event, a 70 KB patch and
        # f2p 5/6 -- an unambiguous, fairly-earned loss. The only thing in its
        # 2,300-line transcript that ever made it "technical" was a single
        # `allowed_warning` utilization notice.
        verdict = triage.triage_job_dir(RUNS_DIR / CLEAN_BUT_UNRESOLVED_JOB)
        self.assertEqual(verdict.outcome, triage.MODEL_FAILURE)
        self.assertEqual(verdict.reason, "unresolved")

    def test_a_recorded_run_with_no_patch_is_a_model_failure(self) -> None:
        verdict = triage.triage_job_dir(RUNS_DIR / "_preflight")
        self.assertEqual(verdict.outcome, triage.MODEL_FAILURE)
        self.assertEqual(verdict.reason, "no_model_patch")

    def test_a_recorded_run_the_verifier_passed_is_a_success(self) -> None:
        verdict = triage.triage_job_dir(RUNS_DIR / "do-in-steps__sonnet-sonnet__abs-stepped-slices")
        self.assertEqual(verdict.outcome, triage.SUCCESS)
        self.assertEqual(verdict.reason, "resolved")

    def test_the_committed_fixture_still_matches_the_runs_it_was_read_from(self) -> None:
        """The fixture cannot silently drift from its source.

        Same guarantee `tests/test_stream_cost.py` gives its own fixture: the
        vocabulary tests above run unconditionally off the copy, so something
        has to check the copy is still the truth when the originals are here.
        """
        recorded = {
            json.loads(line.strip())["rate_limit_info"]["status"]
            for job_dir in self.job_dirs()
            for line in (triage.find_trial_dir(job_dir) / "agent" / "claude-code.txt").open(
                encoding="utf-8", errors="replace"
            )
            if line.strip().startswith('{"type":"rate_limit_event"')
        }
        fixture = {
            json.loads(line)["rate_limit_info"]["status"]
            for line in fixture_lines()
            if line.startswith("{") and json.loads(line)["type"] == "rate_limit_event"
        }
        self.assertEqual(fixture, recorded)


if __name__ == "__main__":
    unittest.main()
