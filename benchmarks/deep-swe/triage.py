#!/usr/bin/env python3
"""Decides whether a finished scheduled run deserves a retry, or a record.

WHY THIS EXISTS
----------------
`run.py --mode scheduled` walks a multi-day matrix unattended. After each
trial it has to answer one question that nothing else in this harness answers:
*was that a fair attempt?* Because the two wrong answers cost very different
things.

  - A **model failure** -- the agent attempted the task and did not solve it
    -- is the benchmark's product. It is recorded and never retried. Retrying
    one buys nothing and quietly turns an n=1 sweep into best-of-N.
  - A **technical failure** -- a container that never came up, a quota that
    ran out, an API 529 that killed the process -- is not a data point at all.
    Recording one as a model failure understates the model's Pass@1 with a
    trial it never got to run, permanently and invisibly.

`collect.Status` deliberately cannot express this distinction: its four
members describe what a trial *was*, not what the scheduler should *do* next,
and `tests/test_status_contract.py` pins that vocabulary. So the three
outcomes below are the scheduler's own, and live here.

THE HARD PART, AND WHAT THE EVIDENCE ACTUALLY SUPPORTS
-------------------------------------------------------
`collect.py`'s `_EXCEPTION_TYPE_CATEGORIES` comment states the problem
outright: pier has no exception class for an Anthropic 529 or a usage-limit
denial. Both crash the wrapped `claude` process, and pier surfaces *any*
non-zero exit as `NonZeroAgentExitCodeError` -> `agent_nonzero_exit`. From
the exception type alone, "the API refused to serve us" and "claude died for
some other reason" are the same string.

So the signal has to be built from the transcript. Every marker below was
chosen by reading the recorded stream logs under `runs/` (see
`api_fault_from_stream_lines` for exactly what was observed in them). The one
thing those recordings prove beyond doubt is a *negative*: substring matching
is not an option. Grepping those transcripts for `529` returns 14-71 hits per
file -- every single one a source-code line number, a uuid fragment or a
millisecond timestamp, in runs that finished cleanly with
`exception_info: null`. Every rule here therefore parses whole JSON events
and reads named fields, exactly as `stream_cost.py` does over the same file.

TWO DEFECTS THIS MODULE SHIPPED, AND WHAT THEY COST
----------------------------------------------------
Both were found by running this module over the runs recorded since it was
written, and both are worth stating here because both were *silent*.

1. **`allowed_warning` read as a denial.** The rule used to be "any
   `rate_limit_info.status` other than `allowed` is a refusal", written when
   `allowed` was the only value any recording contained. claude-code also
   emits `allowed_warning` -- a utilization notice (`utilization`,
   `surpassedThreshold`) that means requests are *still being served* -- and
   emits it on every request once an account crosses a threshold. So from the
   moment an account passed 75% weekly utilization, EVERY trial triaged
   `technical_failure` whatever it actually did, and because
   `technical_failure` is never terminal and pier's per-trial resume skips a
   trial that already has a `result.json`, each retry re-triaged the same
   stale file: 3 attempts x 2h backoff burned per cell, on every invocation.
   `_rate_limit_severity` now grades the status by what claude-code means by
   it rather than by one hardcoded spelling.

2. **First-fault-wins let a benign event shadow a real one.** The scan
   returned the first marker it found, so a run whose transcript opened with
   an `allowed_warning` and ended with a genuine `rejected` plus a 429 was
   reported by the benign opening line. The scan is now worst-fault-wins
   (`ApiFault.severity`), and carries the evidence -- transcript line number
   and raw event -- so the reason in the state file can be audited instead of
   re-derived by hand.

PURE CORE, IMPURE SHELL
------------------------
`verdict_from_signals` and `api_fault_from_stream_lines` hold every rule and
touch no disk; `triage_job_dir` and `find_api_fault` gather the signals.
Same split `collect.py` uses for `incompleteness_reason_from_signals` and
`stream_cost.py` for `parse_total_cost_from_stream_lines`, for the same
reason: the judgement is unit-testable with plain values, and a suite that
had to stage a container to test it would not test it.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

# Only for the completion-gate and verifier rules, which must stay one
# definition shared with what `results.json` records. Safe direction:
# collect.py imports neither this module nor run.py (see its docstring).
import collect

# The scheduler's own vocabulary. Deliberately NOT `collect.Status`: these
# name what the scheduler does next, not what the trial was.
Outcome = Literal["success", "model_failure", "technical_failure"]

SUCCESS: Outcome = "success"
MODEL_FAILURE: Outcome = "model_failure"
TECHNICAL_FAILURE: Outcome = "technical_failure"


# Fault severity. Higher is worse, and `api_fault_from_stream_lines` reports
# the worst fault a transcript contains rather than the first.
#
# The ordering is "how conclusively does this prove the API refused to serve
# us, and how specifically does it name why", because that is what the reason
# slug is for -- it is the only explanation an operator reading
# `scheduler-state.json` months later gets:
#
#   3. `rate_limit_status=rejected` -- the API said so itself, in the field
#      dedicated to saying so, and the same event names the window
#      (`rateLimitType`) and the cause (`overageDisabledReason`). Nothing is
#      more conclusive or more actionable than that.
#   2. `api_error_status=<n>` -- a request failed hard enough to end the turn.
#      Conclusive that something was refused, but the bare status does not say
#      whether it was a quota (429), an overload (529) or something else, so a
#      `rejected` event covering the same run explains it better.
#   1. `rate_limit_status=<anything unrecognised>` -- a spelling this harness
#      has never seen. Treated as a fault (see `_rate_limit_severity`) but the
#      weakest evidence there is, so any concrete fault outranks it.
SEVERITY_UNRECOGNISED_RATE_LIMIT_STATUS = 1
SEVERITY_API_ERROR_STATUS = 2
SEVERITY_RATE_LIMIT_REJECTED = 3


@dataclass(frozen=True)
class ApiFault:
    """One API-side refusal found in a transcript, with the evidence for it.

    The evidence exists because a bare slug cannot be audited. Before this
    carried a line number and the raw event, answering "why was this cell
    technical?" meant re-running the scan by hand over an 8 MB transcript --
    and the one time that question actually mattered, the answer turned out to
    be a benign event the rule had misread (see the module docstring).

    `slug` is what `verdict_from_signals` interpolates into the reason, so it
    stays short and greppable; everything else is for the log.

    `faults_seen` is the whole scan's fault count, not this fault's -- it is
    carried here so one value answers "was this a single blip or a storm?"
    without the caller needing a second return value. It is 1 by default so a
    fault built for a single event is honest on its own.
    """

    slug: str
    severity: int
    line_number: int  # 1-based, counting every line of the transcript
    event: dict[str, Any] = field(default_factory=dict)
    faults_seen: int = 1

    def as_record(self) -> dict[str, Any]:
        """This fault as JSON-serialisable evidence for a log line."""
        return {
            "slug": self.slug,
            "severity": self.severity,
            "line_number": self.line_number,
            "faults_seen": self.faults_seen,
            "event": self.event,
        }

    def __str__(self) -> str:
        return (
            f"{self.slug} at transcript line {self.line_number} "
            f"({self.faults_seen} fault(s) seen)"
        )


@dataclass(frozen=True)
class Verdict:
    """One run's outcome plus the short slug explaining how it was reached.

    `reason` is always populated -- including for `success` -- so the
    end-of-run summary can print why every line says what it says without
    the reader having to reconstruct the rule that fired.

    `fault` and `trial_dir` are evidence, not rules: they say which trial was
    judged and what the transcript scan found there, so `scheduler.py`'s
    per-attempt log can record why this verdict says what it does. `fault` is
    populated whenever the transcript contained one, even when some other rule
    decided the outcome -- a solve the API 429'd mid-session is still worth
    having in the log, and `reason` already names the rule that actually
    fired. Both default to `None` so a verdict built from plain values (a
    test, or `scheduler._resume` rebuilding one from the state file) needs
    neither.
    """

    outcome: Outcome
    reason: str
    fault: ApiFault | None = None
    trial_dir: Path | None = None

    @property
    def is_technical(self) -> bool:
        """Whether the scheduler should back off and retry this run."""
        return self.outcome == TECHNICAL_FAILURE

    def __str__(self) -> str:
        return f"{self.outcome} ({self.reason})"


# --------------------------------------------------------------------------
# Pier exception types -> outcome
#
# Every name below is one of `collect._EXCEPTION_TYPE_CATEGORIES`' keys,
# which that comment records as verified against pier's own source. What is
# added here is the *scheduler's* reading of each: does it describe a fair
# attempt, or the absence of one.
# --------------------------------------------------------------------------

# The environment, the setup or the grader failed -- the agent was never
# asked the question, or was never scored on its answer. Not the model's
# doing under any reading, so always worth another attempt.
TECHNICAL_EXCEPTION_TYPES = frozenset({
    "EnvironmentStartTimeoutError",
    "AgentSetupTimeoutError",
    "VerifierTimeoutError",
    "CancelledError",
})

# The agent had the whole clock (`--agent-timeout-multiplier`, 3.0 by
# default) and did not finish inside it. That IS the attempt: a model too
# slow to converge is exactly what a benchmark is measuring, and a retry
# would buy a second draw on a cell the sweep says gets one. Treated as a
# model failure unless the transcript shows the API was refusing to serve it
# (see `_verdict_for_exception`) -- an agent starved by a quota did not
# spend that clock thinking.
AGENT_TIMEOUT_EXCEPTION_TYPE = "AgentTimeoutError"

# The single ambiguous type, and the reason this module is hard. See
# `AMBIGUOUS_NONZERO_EXIT_REASON` for how it is resolved when the transcript
# offers no evidence either way.
AMBIGUOUS_EXCEPTION_TYPE = "NonZeroAgentExitCodeError"

# The documented default for `NonZeroAgentExitCodeError` with no API-fault
# evidence in the transcript: treat it as TECHNICAL and retry it, bounded.
#
# The two mistakes are not symmetric.
#
#   Calling a model failure technical costs one backoff plus one re-run of a
#   cell that will not pass -- real money and real hours, but *bounded* by
#   the scheduler's retry cap, visible in the summary, and once the cap is
#   spent the cell is recorded as technically-failed, i.e. as no data.
#
#   Calling a technical failure a model failure writes a permanent zero for
#   a trial the model never fairly attempted. Resumability then guarantees
#   it is never re-run, `results.json` carries it, and the published Pass@1
#   is biased downward by a trial that never happened -- with nothing in the
#   output to suggest anything went wrong.
#
# The first mistake is expensive and self-limiting; the second is cheap and
# permanent, and it corrupts the only thing this benchmark produces. So the
# ambiguous case buys the bounded loss.
#
# Note how narrow this default is: it applies only to an *abnormal process
# exit*. A pier run that exits cleanly and merely produced no patch never
# reaches here -- that is unambiguously a model failure, and is never
# retried.
AMBIGUOUS_NONZERO_EXIT_REASON = "ambiguous_nonzero_exit"

# `verdict_from_signals`'s reason when pier never wrote a trial `result.json`
# at all (a container that never came up, an environment build that failed
# before the agent ran). Named here, rather than left as a string literal
# inline, because `run.py`'s `stuck_technical_reports` reads it too: this is
# the ONE technical reason that is genuinely retried for real by a later
# `pier run` invocation -- with no trial directory on disk yet, pier's own
# per-trial resume (`Job._maybe_init_existing_job`) has nothing to skip.
# Every OTHER technical reason means a trial's `result.json` DOES exist, and
# that is exactly what pier's resume treats as already done, so the same
# stale verdict replays on every future invocation until the job directory
# is removed by hand. See run.py's `stuck_technical_reports` docstring.
NO_TRIAL_RESULT_REASON = "no_trial_result"


def _verdict_for_exception(exception_type: str, api_fault: ApiFault | None) -> Verdict:
    """Read one pier `exception_type` (plus any transcript evidence) as an outcome.

    Unrecognised types fall through to technical on purpose, under a reason
    slug that says so. `collect.py` maps them to `other_infra_error` and
    names a Docker build `RuntimeError` as the example: pier raises bare
    exceptions for infrastructure faults, so "a type this harness has not
    seen before" is far more likely to be new infrastructure than a new way
    for a model to fail. Naming it distinctly in the summary still tells an
    operator there is a type here worth classifying deliberately.
    """
    if api_fault is not None:
        return Verdict(TECHNICAL_FAILURE, f"api_fault:{api_fault.slug}")
    if exception_type == AGENT_TIMEOUT_EXCEPTION_TYPE:
        return Verdict(MODEL_FAILURE, "agent_timeout")
    if exception_type == AMBIGUOUS_EXCEPTION_TYPE:
        return Verdict(TECHNICAL_FAILURE, AMBIGUOUS_NONZERO_EXIT_REASON)
    if exception_type in TECHNICAL_EXCEPTION_TYPES:
        return Verdict(TECHNICAL_FAILURE, f"pier_exception:{exception_type}")
    return Verdict(TECHNICAL_FAILURE, f"unrecognised_pier_exception:{exception_type}")


def _verdict_by_precedence(
    *,
    has_trial_result: bool,
    exception_type: str | None,
    has_rewards: bool,
    resolved: bool,
    incompleteness_reason: str | None,
    api_fault: ApiFault | None,
) -> Verdict:
    """The rule chain itself. See `verdict_from_signals` for the precedence."""
    if not has_trial_result:
        return Verdict(TECHNICAL_FAILURE, NO_TRIAL_RESULT_REASON)
    if resolved:
        return Verdict(SUCCESS, "resolved")
    if exception_type is not None:
        return _verdict_for_exception(exception_type, api_fault)
    if not has_rewards:
        return Verdict(TECHNICAL_FAILURE, "missing_verifier_rewards")
    if api_fault is not None:
        return Verdict(TECHNICAL_FAILURE, f"api_fault:{api_fault.slug}")
    if incompleteness_reason is not None:
        return Verdict(MODEL_FAILURE, incompleteness_reason)
    return Verdict(MODEL_FAILURE, "unresolved")


def verdict_from_signals(
    *,
    has_trial_result: bool,
    exception_type: str | None,
    has_rewards: bool,
    resolved: bool,
    incompleteness_reason: str | None,
    api_fault: ApiFault | None,
    trial_dir: Path | None = None,
) -> Verdict:
    """Judge already-gathered signals. Pure counterpart of `triage_job_dir`.

    Precedence mirrors `collect.py` for every signal both look at, so the
    scheduler and `results.json` can never disagree about what a trial was.
    (`collect` has one rule this module has no signal for -- a plugin that
    failed to load, which means the arm measured something other than what its
    name claims. It sits between rules 1 and 2 below. Everywhere else the two
    orderings are the same.)

    1. No `result.json` at all -- pier died before the trial produced one, so
       the agent was never asked and there is no verifier output to trust.
       Technical, and above everything else including rule 2: `collect` reads
       the same signal the same way, one level above `classify_status` (see
       `_errored_record` and row 1 of that module's table), where it likewise
       outranks a `resolved` verdict.
    2. The verifier says resolved -- a solve, full stop. Checked BEFORE
       `exception_info`, the API-fault scan and the completion gate, so none
       of them can overturn it; checked AFTER rule 1, because a trial that
       never ran cannot have been solved. It sits this high, rather than in
       the middle, because of a real recorded run:
       `runs/do-in-steps__opus-opus__abs-stepped-slices` scored
       `reward 1, f2p 1.0` with a 131 KB patch and was then killed by a 429 on
       its way out, so pier reported `NonZeroAgentExitCodeError`. With
       the exception checked first, that solve was discarded and re-run: a
       verified success thrown away and paid for again, which is the one
       mistake this module has no way to detect after the fact.
    3. `exception_info` set -- pier's own infra signal. Dispatched by type
       above.
    4. No verifier rewards -- the grader produced no score, so there is no
       measurement to keep. Technical.
    5. An API fault in the transcript -- the case pier's exit code misses
       entirely: a session truncated by a quota denial can still exit 0, and
       would otherwise be recorded as `no_model_patch`, i.e. as the model's
       fault. Technical.
    6. The completion gate fired (`no_model_patch`,
       `final_message_is_question`) -- the agent attempted and abandoned.
       Model failure, recorded, never retried.
    7. Otherwise the agent attempted and was scored wrong. Model failure.

    Rule 1 standing above rule 2 is what stops this function reporting a
    success for a trial that never produced a result -- the guard is the
    branch order, enforced here, and not a property of any caller.
    `triage_job_dir` happens never to pass that combination (it derives
    `resolved` from a `result.json` plus a rewards bundle), but this is a
    public pure function, and a backfill or re-triage caller reading
    `resolved` off a rewards file alone would otherwise be handed a
    fabricated solve -- exactly the cheap, permanent corruption this module
    exists to prevent. `VerdictRuleTests` pins the combination.
    """
    verdict = _verdict_by_precedence(
        has_trial_result=has_trial_result,
        exception_type=exception_type,
        has_rewards=has_rewards,
        resolved=resolved,
        incompleteness_reason=incompleteness_reason,
        api_fault=api_fault,
    )
    return replace(verdict, fault=api_fault, trial_dir=trial_dir)


# --------------------------------------------------------------------------
# The transcript scan
# --------------------------------------------------------------------------

# claude-code's `rate_limit_info.status` vocabulary, as three rules rather
# than as a list of spellings. See `_rate_limit_severity`.
RATE_LIMIT_ALLOWED_PREFIX = "allowed"
RATE_LIMIT_STATUS_REJECTED = "rejected"


def _rate_limit_severity(status: object) -> int | None:
    """How bad one `rate_limit_info.status` is; `None` when it is not a fault.

    THE STATUS VOCABULARY, AND WHY IT IS A PREFIX RULE
    ---------------------------------------------------
    Three values are attested in the transcripts under `runs/`, 41 events in
    total:

      `allowed`          (14x)  the request was served, nothing to report.
      `allowed_warning`  (26x)  the request was ALSO served -- this is a
                                utilization notice, carrying `utilization`
                                and `surpassedThreshold` instead of a denial.
                                claude-code emits one per request once an
                                account crosses a threshold, so a healthy but
                                heavily-used account produces a continuous
                                stream of them.
      `rejected`         (1x)   the request was refused. Observed once, at
                                line 2936 of
                                `runs/do-in-steps__opus-opus__abs-stepped-slices`,
                                as `{"status": "rejected", "rateLimitType":
                                "five_hour", "overageDisabledReason":
                                "out_of_credits", ...}`, five lines before a
                                `result` event with `api_error_status: 429`.

    The rule is written as "an `allowed`-prefixed status is a permitted
    request" rather than as `status in {"allowed", "allowed_warning"}` because
    the prefix is the part that carries claude-code's actual meaning: the
    suffix grades how close to the limit the account is, and a future
    `allowed_<something>` would still be a served request. Matching on the
    exact spellings would reintroduce the original defect the first time a
    third suffix appeared.

    WHICH WAY AN UNRECOGNISED STATUS FALLS, AND WHY
    -----------------------------------------------
    Anything neither `allowed`-prefixed nor `rejected` is treated as a fault,
    at the lowest severity. That is the same asymmetry `AMBIGUOUS_NONZERO_EXIT_REASON`
    is built on, applied to a vocabulary rather than to an exit code: reading
    an unknown status as "fine" writes a permanent, invisible zero for a trial
    that may never have been served, while reading it as a fault costs a
    bounded, visible retry and puts the unrecognised spelling in the state
    file where an operator will see it and classify it deliberately. A
    bounded, loud cost beats a silent, permanent one.

    Note the direction this does NOT go: `allowed_warning` is not a fault, and
    a *missing* status is not a fault either. An event that makes no claim
    about whether the request was served is not evidence that it was refused,
    and treating absence as denial is how the original defect started.
    """
    if status is None:
        return None
    if isinstance(status, str) and status.startswith(RATE_LIMIT_ALLOWED_PREFIX):
        return None
    if status == RATE_LIMIT_STATUS_REJECTED:
        return SEVERITY_RATE_LIMIT_REJECTED
    return SEVERITY_UNRECOGNISED_RATE_LIMIT_STATUS


def _api_fault_from_event(event: object, line_number: int) -> ApiFault | None:
    """Whether one stream event reports an API-side refusal; `None` if not.

    Every lookup is shape-checked rather than assumed, for the reason
    `run.py`'s `assistant_tool_use_parts` documents: this file is written
    live, a run killed mid-write leaves a half-formed event behind, and a
    `TypeError` out of triage would abort a multi-day schedule over one
    truncated line. `_rate_limit_severity` takes an `object` for the same
    reason -- a `status` that is not a string must be graded, not crashed on.

    `line_number` is threaded in rather than found later because it cannot be
    recovered afterwards: the caller streams the transcript and does not keep
    it, and an 8 MB log is not something to re-read to answer "where?".
    """
    if not isinstance(event, dict):
        return None

    if event.get("type") == "result" and event.get("api_error_status") is not None:
        return ApiFault(
            slug=f"api_error_status={event['api_error_status']}",
            severity=SEVERITY_API_ERROR_STATUS,
            line_number=line_number,
            event=event,
        )

    if event.get("type") == "rate_limit_event":
        info = event.get("rate_limit_info")
        status = info.get("status") if isinstance(info, dict) else None
        severity = _rate_limit_severity(status)
        if severity is not None:
            return ApiFault(
                slug=f"rate_limit_status={status}",
                severity=severity,
                line_number=line_number,
                event=event,
            )

    return None


def api_fault_from_stream_lines(lines: Iterable[str]) -> ApiFault | None:
    """The WORST API-side refusal reported anywhere in a transcript, or None.

    `lines` is any iterable of raw stream lines -- an open file object (the
    recorded transcripts run to 8 MB, so they are never read whole) or a list
    of strings in a test.

    WORST WINS, NOT FIRST
    ----------------------
    This used to return the first marker it found and stop. That is wrong for
    the shape a real quota exhaustion actually has, and
    `runs/do-in-steps__opus-opus__abs-stepped-slices` is the proof: its
    transcript opens at line 6 with a benign `allowed_warning` (seven-day
    utilization 0.77) and only at line 2936 reaches the `rejected` that
    actually stopped it. First-wins reported the opening line, so the recorded
    reason named a notice rather than the denial. Reading the whole transcript
    and keeping the worst fault means a benign leading event can never shadow
    a real tail one -- see the severity constants for the ordering and why it
    is ordered that way. Ties keep the earliest occurrence, which is the first
    evidence of that class.

    The scan therefore no longer short-circuits. That costs nothing in
    practice: a clean transcript -- the overwhelmingly common case -- was
    always read to the end anyway, because there was no fault to stop at.

    WHAT WAS ACTUALLY OBSERVED
    ---------------------------
    Read off the `runs/*/*/agent/claude-code.txt` recordings committed in this
    directory. Unlike the first version of this docstring, the recordings now
    include real examples of the failure this function detects: one `rejected`
    rate-limit event and one `api_error_status: 429`, both in
    `runs/do-in-steps__opus-opus__abs-stepped-slices`, whose trial pier
    surfaced as `NonZeroAgentExitCodeError`.

    `api_error_status` (marker 1)
      The field is present on every `{"type":"result"}` event across the
      recordings, and `null` on all but one of them, in runs that completed
      normally (`is_error: false`, `subtype: "success"`,
      `terminal_reason: "completed"`). The exception is line 2941 of the run
      above: `api_error_status: 429` with `is_error: true`. So a non-null
      value carrying the failing HTTP status is observed, not inferred.

    `rate_limit_event.rate_limit_info.status` (marker 2)
      41 `{"type":"rate_limit_event"}` events across the recordings: 14
      `allowed`, 26 `allowed_warning`, 1 `rejected`. See
      `_rate_limit_severity` for the full vocabulary, what each value means,
      and which way an unrecognised fourth value falls.
      NOTE the field NOT used: `overageStatus: "rejected"` is present in
      *allowed* events too. Keying on it would fail most runs in this
      repository as quota denials -- a good illustration of why these rules
      are read off artifacts instead of reasoned out from field names.

    WHAT IS DELIBERATELY NOT A MARKER
    ----------------------------------
    * Any substring search. `529` appears 14-71 times per recorded
      transcript -- as Go/Python source line numbers in tool results, as
      uuid fragments, and as timestamp milliseconds -- and never once as an
      API status. `rate_limit` and `api_error` likewise appear only inside
      the two structured events above.
    * A plain-text banner such as claude's interactive usage-limit notice.
      The transcripts contain zero non-JSON lines, so there is no recorded
      evidence that pier's tee ever carries one, and inventing the wording
      would be exactly the fabrication this docstring exists to avoid.
    * `is_error: true` / `subtype != "success"` on a result event. Their
      non-clean values cover agent-side outcomes too (a turn limit is not an
      API fault), so they would blur the very line this function is drawing --
      and the one recorded `is_error: true` event carries
      `api_error_status: 429` anyway, so marker 1 already catches it. An
      unexplained failure that reaches none of the markers above is handled by
      `AMBIGUOUS_NONZERO_EXIT_REASON` instead, which is honest about being a
      default rather than pretending to be a detection.

    Unparseable lines, blank lines and lines not starting with `{` are
    skipped, matching `stream_cost.py` and `run.py`'s readers over this same
    file: a truncated final line is normal in a log still being written. They
    still advance the line count, so a reported line number is the transcript's
    own.
    """
    worst: ApiFault | None = None
    faults_seen = 0

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        fault = _api_fault_from_event(event, line_number)
        if fault is None:
            continue
        faults_seen += 1
        if worst is None or fault.severity > worst.severity:
            worst = fault

    return None if worst is None else replace(worst, faults_seen=faults_seen)


def find_api_fault(trial_dir: Path) -> ApiFault | None:
    """Scan this trial's `agent/claude-code.txt`, streaming rather than slurping.

    Opened with `encoding="utf-8", errors="replace"` per `run.py`'s
    `iter_stream_events` and `stream_cost.py`: the transcript carries
    arbitrary tool output, and one undecodable byte must not cost the whole
    scan. Line-by-line because the recorded logs reach 8 MB.

    A missing log is not a fault -- it means the agent never started, which
    `verdict_from_signals` reaches through `has_trial_result` instead.
    """
    stream_log = trial_dir / "agent" / "claude-code.txt"
    if not stream_log.is_file():
        return None
    with stream_log.open(encoding="utf-8", errors="replace") as handle:
        return api_fault_from_stream_lines(handle)


# --------------------------------------------------------------------------
# The shell: gather one job dir's signals off disk
# --------------------------------------------------------------------------


def find_trial_dir(job_dir: Path) -> Path | None:
    """The trial directory to judge, or `None` when pier wrote no result.

    A scheduled run is one arm against one task, so pier produces exactly one
    trial here. The newest-by-mtime tiebreak matters only for a job dir that
    a `--force` re-run left more than one trial in, and picks the same way
    `run.py`'s `find_stream_log` does: the run that just finished is the one
    being judged.
    """
    results = sorted(job_dir.glob("*/result.json"), key=lambda p: p.stat().st_mtime)
    return results[-1].parent if results else None


def triage_job_dir(job_dir: Path) -> Verdict:
    """Gather one finished scheduled run's signals off disk, then judge them.

    A `result.json` that cannot be parsed is read as no result at all, not as
    an error of its own: `collect.load_json_or_none` exists because an
    interrupted job leaves truncated JSON behind, and a job interrupted
    mid-write is a technical failure by any reading.
    """
    trial_dir = find_trial_dir(job_dir)
    trial = None if trial_dir is None else collect.load_json_or_none(trial_dir / "result.json")
    if trial_dir is None or trial is None:
        return verdict_from_signals(
            has_trial_result=False,
            exception_type=None,
            has_rewards=False,
            resolved=False,
            incompleteness_reason=None,
            api_fault=None,
        )

    exception_info = trial.get("exception_info")
    verifier_result = trial.get("verifier_result")
    rewards = verifier_result.get("rewards") if verifier_result else None

    return verdict_from_signals(
        has_trial_result=True,
        exception_type=exception_info.get("exception_type") if exception_info else None,
        has_rewards=bool(rewards),
        resolved=bool(rewards) and collect.verifier_reports_success(rewards),
        incompleteness_reason=collect.find_trial_incompleteness_reason(trial_dir),
        api_fault=find_api_fault(trial_dir),
        trial_dir=trial_dir,
    )
