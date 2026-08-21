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
chosen by reading the five recorded stream logs under `runs/` (see
`api_fault_from_stream_lines` for exactly what was observed in them, and for
which half of each marker is inferred rather than observed). The one thing
those recordings prove beyond doubt is a *negative*: substring matching is
not an option. Grepping those transcripts for `529` returns 14-71 hits per
file -- every single one a source-code line number, a uuid fragment or a
millisecond timestamp, in runs that finished cleanly with
`exception_info: null`. Every rule here therefore parses whole JSON events
and reads named fields, exactly as `stream_cost.py` does over the same file.

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
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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


@dataclass(frozen=True)
class Verdict:
    """One run's outcome plus the short slug explaining how it was reached.

    `reason` is always populated -- including for `success` -- so the
    end-of-run summary can print why every line says what it says without
    the reader having to reconstruct the rule that fired.
    """

    outcome: Outcome
    reason: str

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


def _verdict_for_exception(exception_type: str, api_fault: str | None) -> Verdict:
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
        return Verdict(TECHNICAL_FAILURE, f"api_fault:{api_fault}")
    if exception_type == AGENT_TIMEOUT_EXCEPTION_TYPE:
        return Verdict(MODEL_FAILURE, "agent_timeout")
    if exception_type == AMBIGUOUS_EXCEPTION_TYPE:
        return Verdict(TECHNICAL_FAILURE, AMBIGUOUS_NONZERO_EXIT_REASON)
    if exception_type in TECHNICAL_EXCEPTION_TYPES:
        return Verdict(TECHNICAL_FAILURE, f"pier_exception:{exception_type}")
    return Verdict(TECHNICAL_FAILURE, f"unrecognised_pier_exception:{exception_type}")


def verdict_from_signals(
    *,
    has_trial_result: bool,
    exception_type: str | None,
    has_rewards: bool,
    resolved: bool,
    incompleteness_reason: str | None,
    api_fault: str | None,
) -> Verdict:
    """Judge already-gathered signals. Pure counterpart of `triage_job_dir`.

    Precedence mirrors `collect.classify_status` wherever both look at the
    same signal, so the scheduler and `results.json` can never disagree about
    what a trial was:

    1. No `result.json` at all -- pier died before the trial produced one, so
       the agent was never asked. Technical.
    2. `exception_info` set -- pier's own infra signal, checked before rewards
       exactly as `classify_status` does. Dispatched by type above.
    3. No verifier rewards -- the grader produced no score, so there is no
       measurement to keep. Technical.
    4. The verifier says resolved -- a solve, full stop. Checked BEFORE the
       transcript scan on purpose: the recorded runs show transient API
       noise inside sessions that went on to finish and pass, and a verified
       success must never be thrown away and re-run over it.
    5. An API fault in the transcript -- the case pier's exit code misses
       entirely: a session truncated by a quota denial can still exit 0, and
       would otherwise be recorded as `no_model_patch`, i.e. as the model's
       fault. Technical.
    6. The completion gate fired (`no_model_patch`,
       `final_message_is_question`) -- the agent attempted and abandoned.
       Model failure, recorded, never retried.
    7. Otherwise the agent attempted and was scored wrong. Model failure.
    """
    if not has_trial_result:
        return Verdict(TECHNICAL_FAILURE, NO_TRIAL_RESULT_REASON)
    if exception_type is not None:
        return _verdict_for_exception(exception_type, api_fault)
    if not has_rewards:
        return Verdict(TECHNICAL_FAILURE, "missing_verifier_rewards")
    if resolved:
        return Verdict(SUCCESS, "resolved")
    if api_fault is not None:
        return Verdict(TECHNICAL_FAILURE, f"api_fault:{api_fault}")
    if incompleteness_reason is not None:
        return Verdict(MODEL_FAILURE, incompleteness_reason)
    return Verdict(MODEL_FAILURE, "unresolved")


# --------------------------------------------------------------------------
# The transcript scan
# --------------------------------------------------------------------------

# The one `rate_limit_info.status` value observed in every recorded run.
# See `api_fault_from_stream_lines` for what is observed and what is not.
RATE_LIMIT_STATUS_ALLOWED = "allowed"


def _api_fault_from_event(event: object) -> str | None:
    """Whether one stream event reports an API-side refusal; `None` if not.

    Both lookups are shape-checked rather than assumed, for the reason
    `run.py`'s `assistant_tool_use_parts` documents: this file is written
    live, a run killed mid-write leaves a half-formed event behind, and a
    `TypeError` out of triage would abort a multi-day schedule over one
    truncated line.
    """
    if not isinstance(event, dict):
        return None

    if event.get("type") == "result" and event.get("api_error_status") is not None:
        return f"api_error_status={event['api_error_status']}"

    if event.get("type") == "rate_limit_event":
        info = event.get("rate_limit_info")
        status = info.get("status") if isinstance(info, dict) else None
        if status is not None and status != RATE_LIMIT_STATUS_ALLOWED:
            return f"rate_limit_status={status}"

    return None


def api_fault_from_stream_lines(lines: Iterable[str]) -> str | None:
    """The first API-side refusal reported anywhere in a transcript, or None.

    `lines` is any iterable of raw stream lines -- an open file object (the
    recorded transcripts run to 8 MB, so they are never read whole) or a list
    of strings in a test.

    WHAT WAS ACTUALLY OBSERVED, AND WHAT IS INFERRED
    -------------------------------------------------
    Read off the five `runs/*/*/agent/claude-code.txt` recordings committed
    in this directory, all five of which ended with `exception_info: null` --
    that is, **no recorded run in this repository is an example of the
    failure this function detects.** The markers below are therefore built
    from what a *clean* run demonstrably looks like, and the fault side of
    each is an inference. That is stated here rather than dressed up,
    because a confidently-wrong marker string would silently disable the
    whole retry path.

    `api_error_status` (marker 1)
      OBSERVED: the field is present on all 54 `{"type":"result"}` events
      across the five transcripts, and is `null` in every one of them, in
      runs that completed normally (`is_error: false`, `subtype: "success"`,
      `terminal_reason: "completed"`).
      INFERRED: that a non-null value carries the failing HTTP status, and
      therefore that any non-null value means an API-side refusal. The field
      name and its null-on-every-clean-run behaviour are facts; the shape of
      its populated form is not, which is why the marker string interpolates
      whatever value is found rather than comparing against a guessed one.

    `rate_limit_event.rate_limit_info.status` (marker 2)
      OBSERVED: 7 `{"type":"rate_limit_event"}` events across the five
      transcripts, every one of them
      `{"status": "allowed", "rateLimitType": "five_hour",
        "overageStatus": "rejected", "overageDisabledReason":
        "out_of_credits", "isUsingOverage": false, "resetsAt": <epoch>}`.
      INFERRED: that a `status` other than `"allowed"` means the request was
      refused. The rule is written as "not allowed" rather than as a list of
      guessed denial spellings precisely because the denial vocabulary is
      the part that was never observed.
      NOTE the field NOT used: `overageStatus: "rejected"` is present in all
      seven *allowed* events. Keying on it would fail every run in this
      repository as a quota denial -- a good illustration of why these rules
      were read off artifacts instead of reasoned out from field names.

    WHAT IS DELIBERATELY NOT A MARKER
    ----------------------------------
    * Any substring search. `529` appears 14-71 times per recorded
      transcript -- as Go/Python source line numbers in tool results, as
      uuid fragments, and as timestamp milliseconds -- and never once as an
      API status. `rate_limit` and `api_error` likewise appear only inside
      the two structured events above.
    * A plain-text banner such as claude's interactive usage-limit notice.
      All five transcripts contain zero non-JSON lines, so there is no
      recorded evidence that pier's tee ever carries one, and inventing the
      wording would be exactly the fabrication this docstring exists to
      avoid.
    * `is_error: true` / `subtype != "success"` on a result event. Observed
      as `false`/`"success"` everywhere, but their non-clean values cover
      agent-side outcomes too (a turn limit is not an API fault), so they
      would blur the very line this function is drawing. An unexplained
      failure that reaches none of the markers above is handled by
      `AMBIGUOUS_NONZERO_EXIT_REASON` instead, which is honest about being a
      default rather than pretending to be a detection.

    Unparseable lines, blank lines and lines not starting with `{` are
    skipped, matching `stream_cost.py` and `run.py`'s readers over this same
    file: a truncated final line is normal in a log still being written.
    """
    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        fault = _api_fault_from_event(event)
        if fault is not None:
            return fault
    return None


def find_api_fault(trial_dir: Path) -> str | None:
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
    )
