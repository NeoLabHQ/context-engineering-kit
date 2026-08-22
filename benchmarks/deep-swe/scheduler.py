#!/usr/bin/env python3
"""Walks an expanded `schedule.yaml` plan, pacing, triaging and resuming.

WHAT THIS MODULE OWNS
----------------------
The *policy* of an unattended multi-day benchmark run: what order to run in,
how long to wait, when to retry, when to give up, and what to write down so a
restart does not redo work. `run.py --mode scheduled` supplies the mechanism
(spawn pier, spawn collect.py, spawn report.py) and this module decides when
each happens.

NOTHING HERE TOUCHES PIER, AND THAT IS THE POINT
-------------------------------------------------
Every side effect the loop performs arrives as a callable on `Harness` --
executing a run, checking whether one is already done, invoking collect and
report, appending to the attempt log, sleeping, reading the clock. `run.py`
binds those to the real thing;
the test suite binds them to functions that return canned verdicts and record
the durations that were asked for.

That is not decoration. This loop's defining behaviour is that it waits two
hours between runs and a further two hours before a technical retry, so a
test suite that exercised it honestly would take days. Injecting the clock is
what makes "does it actually wait 7200s before retrying?" a question the
suite answers in milliseconds -- and, like `schedule.py`, it keeps this
module importable without `pier` installed.

THE RETRY BOUND IS STRUCTURAL
------------------------------
There is no `while` loop in this file. Attempts are a `for` over
`range(1 + max_technical_retries)`, so the total work a schedule can ever do
is `len(runnable_runs) * (1 + MAX_TECHNICAL_RETRIES)` executions -- a number
you can compute before starting. `run.py` deliberately refuses to carry a
spend cap (see its `--dry-run`-adjacent comment and collect.py's "no 'spent
most of its budget' condition" section), so the retry count is the ONLY thing
standing between a transient API fault and an unattended process re-running a
$36 trial forever. It is therefore written as a bound the type system can see
rather than as a condition someone has to get right.

THE STATE FILE
---------------
`<jobs_dir>/scheduler-state.json`, rewritten after every terminal outcome:

    {
      "version": 1,                       # bumped only on an incompatible change
      "updated_at": "<ISO-8601 UTC>",
      "runs": {
        "<task>::<model>::<skill>": {     # the planned run's identity, in
                                          # schedule.yaml's own vocabulary
          "arm_id": "do-in-steps__opus-opus",
          "outcome": "success" | "model_failure" | "technical_failure",
          "reason": "resolved" | "no_model_patch" | "api_fault:..." | ...,
          "attempts": 2,                  # executions this run cost
          "recorded_at": "<ISO-8601 UTC>",
          "trial_dir": "<path>",          # optional: the trial that was judged
          "api_fault": {...}              # optional: triage.ApiFault.as_record()
        }
      }
    }

The last two keys are evidence, present only when there is any -- see
`state_entry`. They are additive, so `version` stays 1: both readers of this
file (`load_state` here and `collect.load_scheduler_state`) read named keys
and ignore the rest.

Keyed on (task, model, skill) rather than on `arm_id` because that is the
identity `schedule.yaml` speaks in, and it survives a schedule edit that
renames nothing. A file that cannot be read is treated as absent -- a
scheduler that refused to start because its own bookkeeping was truncated by
the interruption it exists to survive would be exactly backwards.

THE ATTEMPT LOG
----------------
`<jobs_dir>/scheduler-attempts.jsonl`, one JSON object APPENDED per attempt.
The deliberate contrast with the state file above: that one answers "what is
still to do" and is rewritten whole because only its latest content matters;
this one answers "why did this cell end up like that", which is a question
about history, and history that a later attempt overwrites is not history.
The state file keeps exactly one entry per planned run, so the third attempt's
rewrite erases the first two -- and those are the ones an operator asking "why
was this technical?" needs. Appending never loses one, and a truncated final
line costs one record instead of the file (each record is written and flushed
on its own, so an interrupted run leaves whole lines behind it plus at most
one partial).

It is instrumentation, not policy: nothing reads it back, no decision depends
on it, and a failure to write one is logged as a warning and otherwise
ignored. Losing a multi-day benchmark because a log line could not be
appended would be the same absurd trade `_collect_and_report` already refuses.
See `attempt_record` for the fields.

WHAT RESUMPTION WILL AND WILL NOT REDO
---------------------------------------
`success` and `model_failure` are terminal: the run is never executed again
(short of `--force`). A model failure especially -- re-running one would turn
a declared n=1 sweep into a quiet best-of-N, which is the single change most
likely to inflate this benchmark's numbers without anyone noticing.

`technical_failure` is NOT terminal across invocations. Within one
invocation the retry cap bounds it; once the cap is spent the run is recorded
and the schedule moves on. But a later invocation runs it again, because an
operator restarting the scheduler after a quota window closed is explicitly
asking for that, and the alternative -- permanently abandoning a cell to a
transient fault -- loses real data.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import schedule
import triage

# How many extra executions one planned run may buy after a technical failure.
#
# Two, i.e. three attempts in total. The number is set by what the backoff is
# waiting *for*: the only rate-limit DENIAL recorded in this repository
# reports `"rateLimitType": "five_hour"`, so five hours is the quota window
# this exists to outlast. Two backoffs of `technical_failure_backoff` (2h each
# in the committed schedule) plus the run time of the two failed attempts
# spans that window comfortably. A third retry would add hours to an already
# multi-day schedule for a fault class two backoffs already cover.
#
# The recorded transcripts DO also carry `"rateLimitType": "seven_day"`, but
# only on `allowed_warning` utilization notices -- served requests, not
# refusals (see `triage._rate_limit_severity`). No recorded run has been
# denied on a seven-day window, and no retry cap could sensibly outlast one if
# it were: a week of backoff is not a retry, it is a new invocation. That case
# is handled by `technical_failure` being non-terminal across invocations
# rather than by this number.
#
# It also caps the cost of the deliberate mis-triage documented at
# `triage.AMBIGUOUS_NONZERO_EXIT_REASON`: a genuine model failure that
# repeatedly crashes the `claude` process can cost at most two extra runs of
# that cell, never an unbounded spend.
MAX_TECHNICAL_RETRIES = 2

STATE_FILENAME = "scheduler-state.json"
STATE_VERSION = 1

# The append-only per-attempt decision trail, beside the state file. See the
# module docstring for why it is append-only where the state file is not.
ATTEMPT_LOG_FILENAME = "scheduler-attempts.jsonl"

# Outcomes that a later invocation must never execute again. `technical_failure`
# is deliberately absent -- see the module docstring.
TERMINAL_OUTCOMES = frozenset({triage.SUCCESS, triage.MODEL_FAILURE})

# How a planned run was disposed of. The scheduler's own vocabulary, distinct
# from `triage.Outcome` (which says how a run *turned out*) because a run can
# be disposed of without ever turning out at all.
SKIPPED = "skipped"  # schedule.yaml says do not run this cell, with a reason
RESUMED = "resumed"  # an earlier invocation already settled it
RAN = "ran"  # this invocation executed it


def run_key(planned: schedule.PlannedRun) -> str:
    """This planned run's identity in the state file."""
    return f"{planned.task.name}::{planned.model.name}::{planned.skill}"


@dataclass(frozen=True)
class RunAttempt:
    """What one execution of a planned run produced.

    `incomplete_trials` is `run.py`'s `find_incomplete_trials` verdict, passed
    through unchanged so the scheduled summary can report incompleteness in
    the same shape and with the same exit code as the other three modes.
    """

    verdict: triage.Verdict
    incomplete_trials: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RunReport:
    """The scheduler's record of what happened to one planned run.

    `verdict` is `None` only for a `SKIPPED` run, which never had an outcome
    to have. `attempts` is 0 for anything this invocation did not execute.
    """

    planned: schedule.PlannedRun
    disposition: str
    verdict: triage.Verdict | None
    attempts: int
    incomplete_trials: dict[str, str] = field(default_factory=dict)

    @property
    def label(self) -> str:
        """One-line identity for logs: which task, on which arm."""
        return f"{self.planned.task.name} / {self.planned.arm_id}"


@dataclass(frozen=True)
class ScheduleOutcome:
    """Everything one `run_schedule` call did, for the summary and the tests.

    `waits_requested` is every duration handed to `Harness.sleep`, in order.
    Kept as data rather than only being slept through so the summary can state
    the pacing an operator actually paid, and so a test can assert on it
    without a clock.
    """

    reports: tuple[RunReport, ...]
    collect_failures: tuple[str, ...]
    waits_requested: tuple[float, ...]
    elapsed_seconds: float

    def with_disposition(self, disposition: str) -> list[RunReport]:
        return [report for report in self.reports if report.disposition == disposition]

    def with_outcome(self, outcome: str) -> list[RunReport]:
        """Reports whose run settled on `outcome`, executed or resumed."""
        return [
            report
            for report in self.reports
            if report.verdict is not None and report.verdict.outcome == outcome
        ]

    @property
    def incomplete_by_arm(self) -> dict[str, dict[str, str]]:
        """arm_id -> {trial_id: reason}, in `report_run_summary`'s own shape."""
        return {
            report.planned.arm_id: report.incomplete_trials
            for report in self.reports
            if report.incomplete_trials
        }


@dataclass(frozen=True)
class Harness:
    """The side effects the loop drives, injected so the loop stays testable.

    `execute` runs one planned run to completion and triages it.
    `find_completed` returns an already-settled attempt for a run whose job
    directory a previous invocation finished (reusing `run.py`'s existing
    `resolve_completed_job_dir` machinery), or `None` when the run must
    actually happen. `collect_and_report` re-derives `results.json` and
    `report.html`, returning `None` on success or a description of what went
    wrong -- never raising, because a reporting failure must not be able to
    end a multi-day benchmark.

    `append_attempt` writes one `attempt_record` to the attempt log, and
    follows `collect_and_report`'s contract exactly -- `None` on success, a
    one-line description of the failure otherwise, never an exception. It has
    no default even though it is only instrumentation: a default that silently
    dropped every record would make a forgotten binding invisible, and the
    whole point of this log is to be there on the day someone needs it.
    `append_attempt_record` is the production implementation.

    `sleep` and `monotonic` default to the real ones, so production callers
    say nothing about them and only tests substitute.
    """

    execute: Callable[[schedule.PlannedRun], RunAttempt]
    find_completed: Callable[[schedule.PlannedRun], RunAttempt | None]
    collect_and_report: Callable[[], str | None]
    append_attempt: Callable[[dict], str | None]
    sleep: Callable[[float], None] = time.sleep
    monotonic: Callable[[], float] = time.monotonic


# --------------------------------------------------------------------------
# The state file
# --------------------------------------------------------------------------


def state_path_for(jobs_dir: Path) -> Path:
    return jobs_dir / STATE_FILENAME


def load_state(path: Path) -> dict[str, dict]:
    """The `runs` map from a state file; `{}` for anything unusable.

    Missing, unreadable, malformed or written by a future `version` all mean
    the same thing to a resuming scheduler: no trustworthy record of prior
    work, so run everything. That is the safe direction -- it costs money, but
    it cannot silently drop a cell from the matrix, which the opposite
    reading could.
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(document, dict) or document.get("version") != STATE_VERSION:
        return {}
    runs = document.get("runs")
    return runs if isinstance(runs, dict) else {}


def write_state(path: Path, runs: dict[str, dict]) -> None:
    """Rewrite the whole state file. Called after every terminal outcome.

    Whole-file rewrite rather than an append log because of what this file is
    FOR: it answers "what is still to do", which is a question about the
    present, and it holds one entry per planned run -- 45 of them for the
    committed schedule -- so a format an operator can read in full beats an
    append-only one they would have to replay.

    The cost of that choice is that a rewrite erases what it replaces, so a
    cell's third attempt takes the record of its first two with it. That is
    exactly what `append_attempt_record` exists to keep, and the two files are
    deliberately opposite for deliberately different questions: this one is
    the current state of the sweep, that one is its history.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "version": STATE_VERSION,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "runs": runs,
    }
    path.write_text(json.dumps(document, indent=2) + "\n")


def _verdict_evidence(verdict: triage.Verdict) -> dict:
    """The auditable half of a verdict: which trial, and what the scan found.

    Split out because both bookkeeping files want it and neither should have
    to know how a `triage.Verdict` stores it. Keys are omitted rather than
    written as `null` when there is nothing to say -- a state file where most
    entries carry `"api_fault": null` reads as noise, and an absent key and a
    null one mean the same thing to every reader here (`.get`).
    """
    evidence: dict = {}
    if verdict.trial_dir is not None:
        evidence["trial_dir"] = str(verdict.trial_dir)
    if verdict.fault is not None:
        evidence["api_fault"] = verdict.fault.as_record()
    return evidence


def state_entry(planned: schedule.PlannedRun, verdict: triage.Verdict, attempts: int) -> dict:
    """One state-file record for a planned run that reached an outcome.

    Carries the verdict's evidence alongside the reason slug so this file
    alone can answer "why?" -- the question that used to need triage re-run by
    hand over an 8 MB transcript. `trial_dir`/`api_fault` are additive
    optional keys, so `STATE_VERSION` does not move: every reader of this
    file (`load_state` here, `collect.load_scheduler_state`) reads named keys
    and ignores the rest, so an old file without them and a new file with them
    are both valid to both readers.
    """
    return {
        "arm_id": planned.arm_id,
        "outcome": verdict.outcome,
        "reason": verdict.reason,
        "attempts": attempts,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **_verdict_evidence(verdict),
    }


# --------------------------------------------------------------------------
# The attempt log
# --------------------------------------------------------------------------


def attempt_log_path_for(jobs_dir: Path) -> Path:
    return jobs_dir / ATTEMPT_LOG_FILENAME


def attempt_record(
    planned: schedule.PlannedRun,
    verdict: triage.Verdict,
    *,
    attempt: int,
    budget: int,
    slept_seconds: float,
) -> dict:
    """One attempt's decision, as the JSON object appended to the attempt log.

    `attempt`/`budget` are both recorded because neither is useful alone:
    "attempt 3" only means "this cell had run out of chances" if you also know
    the cap that invocation was running under, and the cap is a CLI-adjustable
    `max_technical_retries`, not a constant a reader can assume.

    `slept_seconds` is the backoff paid immediately *before* this attempt, 0.0
    for a first attempt. It makes the wall-clock cost of a stuck cell readable
    straight off the log rather than inferred from timestamps.

    `api_fault` carries the raw offending event, not just the slug. That is
    the whole point: the defect this log exists to catch was a rule misreading
    a benign event, and no summary of that event would have shown it -- only
    the event itself does.
    """
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "run_key": run_key(planned),
        "arm_id": planned.arm_id,
        "attempt": attempt,
        "budget": budget,
        "outcome": verdict.outcome,
        "reason": verdict.reason,
        "slept_seconds": slept_seconds,
        **_verdict_evidence(verdict),
    }


def append_attempt_record(path: Path, record: dict) -> str | None:
    """Append one record as a single JSON line; describe any failure instead of raising.

    `Harness.append_attempt`'s production implementation, and the reason that
    field exists rather than this being called from the loop directly: the
    loop stays testable without a filesystem.

    Opened in append mode per record rather than held open for the run, so
    nothing is buffered in a process that may be killed hours later, and so
    two invocations sharing a jobs dir cannot truncate each other's history.
    `json.dumps` with no newlines in the payload keeps one record on one line,
    which is what makes a truncated tail cost one record instead of the file.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
    except (OSError, TypeError, ValueError) as error:
        return f"could not append to {path}: {error}"
    return None


def entry_is_terminal(entry: object) -> bool:
    """Whether a prior record forbids running this cell again."""
    return isinstance(entry, dict) and entry.get("outcome") in TERMINAL_OUTCOMES


# --------------------------------------------------------------------------
# The loop
# --------------------------------------------------------------------------


def log_to_stdout(message: str) -> None:
    print(f"[schedule] {message}")


def describe_verdict(verdict: triage.Verdict) -> str:
    """A verdict for a human-readable log line, with its fault evidence if any.

    `Verdict.__str__` is deliberately left alone -- `report_scheduled_summary`
    and the README's quoted output both depend on its exact shape -- so the
    evidence is appended here instead, where only the live progress log sees
    it. An operator watching a run get slower is the person who most needs
    "which line of which transcript said so" without going to find the log
    file.
    """
    if verdict.fault is None:
        return str(verdict)
    return f"{verdict} [{verdict.fault}]"


class _ScheduleRunner:
    """One `run_schedule` call's mutable bookkeeping, kept off the free functions.

    A class rather than threaded parameters because the loop accumulates five
    things at once (reports, collect failures, requested waits, the state map,
    whether anything has run yet) and passing those through four call frames
    as in/out parameters would obscure the thing worth reading, which is the
    order the decisions happen in.
    """

    def __init__(
        self,
        harness: Harness,
        *,
        between_runs_seconds: float,
        backoff_seconds: float,
        max_technical_retries: int,
        state_path: Path,
        force: bool,
        log: Callable[[str], None],
    ) -> None:
        self.harness = harness
        self.between_runs_seconds = between_runs_seconds
        self.backoff_seconds = backoff_seconds
        self.max_technical_retries = max_technical_retries
        self.state_path = state_path
        self.force = force
        self.log = log

        self.state = {} if force else load_state(state_path)
        self.reports: list[RunReport] = []
        self.collect_failures: list[str] = []
        self.waits_requested: list[float] = []
        self.has_executed = False

    # --- the walk ---------------------------------------------------------

    def run(self, plan: Sequence[schedule.PlannedRun]) -> ScheduleOutcome:
        started = self.harness.monotonic()
        for planned in plan:
            self.reports.append(self._dispose(planned))
        return ScheduleOutcome(
            reports=tuple(self.reports),
            collect_failures=tuple(self.collect_failures),
            waits_requested=tuple(self.waits_requested),
            elapsed_seconds=self.harness.monotonic() - started,
        )

    def _dispose(self, planned: schedule.PlannedRun) -> RunReport:
        """Decide what happens to one planned run, and make it happen."""
        if planned.skipped:
            self.log(f"SKIP {planned.task.name} / {planned.arm_id} -- {planned.skip_reason}")
            return RunReport(planned, SKIPPED, None, attempts=0)

        resumed = None if self.force else self._resume(planned)
        if resumed is not None:
            return resumed

        self._pace_before_next_run()
        return self._execute_with_retries(planned)

    def _resume(self, planned: schedule.PlannedRun) -> RunReport | None:
        """An already-settled report for this run, or `None` to go run it.

        Two independent sources, checked in this order. The state file is
        authoritative because it is the only one that knows *why* a run ended
        -- a job directory alone cannot distinguish a recorded model failure
        from a cell nobody has reached yet. The on-disk check behind it
        catches runs made before this state file existed (or after it was
        deleted), and re-triages them from the artifacts they left.
        """
        recorded = self.state.get(run_key(planned))
        if entry_is_terminal(recorded):
            verdict = triage.Verdict(recorded["outcome"], recorded.get("reason", "recorded"))
            self.log(f"DONE {planned.task.name} / {planned.arm_id} -- {verdict} (from state file)")
            return RunReport(planned, RESUMED, verdict, attempts=0)

        completed = self.harness.find_completed(planned)
        if completed is None:
            return None

        # A finished job directory is not the same as a fair attempt. Pier
        # marks a job finished even when its only trial raised, so a run that
        # died on a dead container or a quota denial leaves exactly the same
        # `finished_at` behind as one that ran perfectly. Settling on that
        # would be the worst outcome available: the cell would be skipped on
        # sight by this invocation AND by every later one (the check does not
        # depend on the state file), so a transient fault would silently cost
        # the matrix a cell forever.
        #
        # So a technical verdict falls through and the run is executed. Note
        # that pier's own resume logic skips trials that already have a
        # `result.json`, so that execution may find nothing to do and triage
        # the same way again -- bounded by the retry cap, and reported as a
        # technical failure. `--force` on its own does NOT clear this: it
        # only makes `run.py` skip its own already-done check, and pier's own
        # per-trial resume still skips the trial regardless, on every future
        # invocation, `--force` or not. The job directory has to be removed
        # first -- `run.py`'s `report_scheduled_summary` names these STUCK
        # cells specifically and prints the exact recipe. Loud and bounded
        # beats silent and permanent.
        if completed.verdict.is_technical:
            self.log(
                f"REDO {planned.task.name} / {planned.arm_id} -- job dir is complete but "
                f"{describe_verdict(completed.verdict)}; not a fair attempt, so it does not "
                f"count as done"
            )
            return None

        self.log(
            f"DONE {planned.task.name} / {planned.arm_id} -- "
            f"{describe_verdict(completed.verdict)} (job dir already complete)"
        )
        self._record(planned, completed.verdict, attempts=0)
        return RunReport(planned, RESUMED, completed.verdict, 0, completed.incomplete_trials)

    def _execute_with_retries(self, planned: schedule.PlannedRun) -> RunReport:
        """Run this cell, retrying only technical failures, at most a fixed number of times.

        The bound is the `for` below: `attempt` cannot exceed `budget`, so no
        input -- not a permanently broken container, not an API refusing every
        request -- can make this function execute more than `budget` times.
        A model failure exits on the first pass and is never re-executed.

        Every attempt is appended to the attempt log, including the ones the
        state file will overwrite. That is the whole reason the log exists: a
        cell recorded with `attempts: 3` says nothing about what the first two
        attempts decided or on what evidence, and those are the attempts an
        investigation starts from.
        """
        budget = 1 + self.max_technical_retries
        report = None

        for attempt in range(1, budget + 1):
            slept_seconds = 0.0
            if attempt > 1:
                slept_seconds = self.backoff_seconds
                self._wait(
                    slept_seconds,
                    f"technical-failure backoff before attempt {attempt}/{budget}",
                )
            self.log(f"RUN  {planned.task.name} / {planned.arm_id} (attempt {attempt}/{budget})")
            outcome = self.harness.execute(planned)
            self.has_executed = True
            self._collect_and_report()

            report = RunReport(planned, RAN, outcome.verdict, attempt, outcome.incomplete_trials)
            self._log_attempt(
                planned, outcome.verdict, attempt=attempt, budget=budget,
                slept_seconds=slept_seconds,
            )
            self.log(f"     {report.label} -- {describe_verdict(outcome.verdict)}")
            if not outcome.verdict.is_technical:
                break
            if attempt == budget:
                self.log(f"     {report.label} -- retries exhausted after {budget} attempts")

        assert report is not None  # budget >= 1, so the loop always ran once
        self._record(planned, report.verdict, report.attempts)
        return report

    # --- the side effects -------------------------------------------------

    def _pace_before_next_run(self) -> None:
        """Wait `between_runs_seconds` before every execution but the first.

        Placed before the run rather than after it so a schedule that ends on
        a run does not spend two hours sleeping with nothing left to do, and
        so a skipped or resumed cell costs no wall-clock time at all -- there
        is nothing to pace away from when nothing ran.
        """
        if self.has_executed and self.between_runs_seconds > 0:
            self._wait(self.between_runs_seconds, "pacing between runs")

    def _wait(self, seconds: float, why: str) -> None:
        self.log(f"WAIT {seconds:.0f}s -- {why}")
        self.waits_requested.append(seconds)
        self.harness.sleep(seconds)

    def _collect_and_report(self) -> None:
        """Re-derive results.json/report.html; record a failure and carry on.

        A failure here is recorded and reported at the end, never raised.
        Losing a multi-day benchmark because `report.py` could not write an
        HTML file would be an absurd trade, and the artifacts the report is
        built from are all still on disk to be re-derived later.
        """
        failure = self.harness.collect_and_report()
        if failure is None:
            return
        self.collect_failures.append(failure)
        self.log(f"WARN collect/report failed (schedule continues): {failure}")

    def _log_attempt(
        self,
        planned: schedule.PlannedRun,
        verdict: triage.Verdict,
        *,
        attempt: int,
        budget: int,
        slept_seconds: float,
    ) -> None:
        """Append this attempt to the decision trail; warn and carry on if it fails.

        Same never-raise contract as `_collect_and_report`, with one
        difference: a failure here is NOT collected into `collect_failures`
        and so does not reach the exit code. `results.json` failing to build
        means this invocation did not do its job; a log line failing to append
        means one line of instrumentation is missing from a run that otherwise
        went fine, and turning that into a non-zero exit would train an
        operator to ignore the code that matters.
        """
        record = attempt_record(
            planned, verdict, attempt=attempt, budget=budget, slept_seconds=slept_seconds
        )
        failure = self.harness.append_attempt(record)
        if failure is not None:
            self.log(f"WARN attempt log not appended (schedule continues): {failure}")

    def _record(
        self, planned: schedule.PlannedRun, verdict: triage.Verdict | None, attempts: int
    ) -> None:
        if verdict is None:
            return
        self.state[run_key(planned)] = state_entry(planned, verdict, attempts)
        write_state(self.state_path, self.state)


def run_schedule(
    plan: Sequence[schedule.PlannedRun],
    *,
    harness: Harness,
    between_runs_seconds: float,
    backoff_seconds: float,
    state_path: Path,
    max_technical_retries: int = MAX_TECHNICAL_RETRIES,
    force: bool = False,
    log: Callable[[str], None] = log_to_stdout,
) -> ScheduleOutcome:
    """Execute every runnable cell of `plan`, in order, and report what happened.

    `plan` is `schedule.expand_schedule()`'s output verbatim, skipped cells
    included -- they are walked and reported as deliberate blanks rather than
    filtered out, so the summary can tell "not run, because X" apart from a
    cell the schedule forgot.

    Raises on a negative `max_technical_retries` rather than quietly running
    nothing: a schedule that executes zero trials and reports no failures is
    the one result nobody would think to question.
    """
    if max_technical_retries < 0:
        raise ValueError(
            f"max_technical_retries must be >= 0 (got {max_technical_retries}); "
            f"0 means one attempt and no retries"
        )
    runner = _ScheduleRunner(
        harness,
        between_runs_seconds=between_runs_seconds,
        backoff_seconds=backoff_seconds,
        max_technical_retries=max_technical_retries,
        state_path=state_path,
        force=force,
        log=log,
    )
    return runner.run(plan)


def preview_schedule(
    plan: Sequence[schedule.PlannedRun],
    *,
    between_runs_seconds: float,
    backoff_seconds: float,
    max_technical_retries: int = MAX_TECHNICAL_RETRIES,
    state: dict[str, dict] | None = None,
    already_done: Callable[[schedule.PlannedRun], str | None] | None = None,
) -> list[str]:
    """The lines `--dry-run` prints: execution order, skips with reasons, pacing.

    Writes nothing and executes nothing, so an operator can read the plan --
    including the wall-clock floor it implies and the worst case the retry cap
    permits -- before committing days to it.

    `state` is an already-loaded state map (`load_state`'s output) and
    `already_done` is the on-disk check, returning a short description for a
    cell whose job directory a previous run already finished or `None`
    otherwise. Both are optional, and both exist so the preview reports the
    same two resumption sources `_resume` consults -- a dry-run that told an
    operator 33 runs were pending when 2 of them would be skipped on sight
    would be worse than no preview at all. Passing neither previews the whole
    plan as unrun.
    """
    settled = state or {}
    lines: list[str] = []
    position = 0
    runnable = 0

    for planned in plan:
        if planned.skipped:
            lines.append(
                f"  SKIP      {planned.task.name} / {planned.arm_id} -- {planned.skip_reason}"
            )
            continue

        recorded = settled.get(run_key(planned))
        if entry_is_terminal(recorded):
            lines.append(
                f"  DONE      {planned.task.name} / {planned.arm_id} -- "
                f"{recorded['outcome']} ({recorded.get('reason', 'recorded')}), will not re-run"
            )
            continue

        on_disk = already_done(planned) if already_done is not None else None
        if on_disk is not None:
            lines.append(
                f"  DONE      {planned.task.name} / {planned.arm_id} -- "
                f"{on_disk}, will not re-run"
            )
            continue

        runnable += 1
        position += 1
        pacing = "no wait (first run)" if position == 1 else f"wait {between_runs_seconds:.0f}s first"
        lines.append(f"  {position:>2}. RUN   {planned.task.name} / {planned.arm_id} -- {pacing}")

    floor = max(0, runnable - 1) * between_runs_seconds
    worst_case_extra = runnable * max_technical_retries * backoff_seconds
    lines.append(
        f"  pacing: {runnable} still to run, {between_runs_seconds:.0f}s between runs "
        f"=> {floor:.0f}s ({floor / 3600:.1f}h) of pacing alone, excluding run time."
    )
    lines.append(
        f"  retries: at most {max_technical_retries} technical retries per run, "
        f"{backoff_seconds:.0f}s backoff each => at most {runnable * (1 + max_technical_retries)} "
        f"executions and {worst_case_extra:.0f}s ({worst_case_extra / 3600:.1f}h) of extra backoff."
    )
    return lines
