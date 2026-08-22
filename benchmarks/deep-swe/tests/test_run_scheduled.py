#!/usr/bin/env python3
"""Unit tests for `--mode scheduled`: the loop, the pacing, the bookkeeping, the bound.

WHAT THESE TESTS GUARD
-----------------------
This mode runs unattended for days, spending real money per trial, with
nobody watching. Four of its properties are the ones that make that
tolerable, and every one of them is a *negative*, which is exactly the kind
of property that rots silently:

  * It never retries a genuine model failure. A retry there turns a declared
    n=1 sweep into a quiet best-of-N and inflates every number the benchmark
    publishes.
  * It never retries anything forever. `run.py` deliberately carries no spend
    cap, so the retry count is the only bound there is.
  * A collect.py or report.py failure never ends the run. Losing days of
    benchmarking because an HTML file could not be written would be absurd.
  * Nor does a failure to append to the attempt log -- instrumentation must
    never be able to outrank the thing it is instrumenting.

NO TEST HERE SLEEPS
--------------------
`scheduler.Harness` takes its `sleep`/`monotonic` as injected callables, so
`FakeClock` below stands in for both: it records what duration was asked for
and advances a counter instead of blocking. That is what lets these tests
assert "it waited 7200 seconds before retrying" in milliseconds -- and a
suite that could not make that assertion would be leaving the whole pacing
design unverified. `FakeRunner` does the same for the two files the loop
writes, so the attempt log's CONTENT is assertable without a filesystem.

WHAT IS NOT HERE
-----------------
`triage.py`'s own rules. They used to be, and that is how two triage defects
shipped -- see the "Triage's own rules are NOT tested here" comment below.
`tests/test_triage.py` owns them now; everything here feeds the loop canned
verdicts, because what the loop does with a verdict is this file's subject.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

import schedule
import scheduler
import triage

from .run_fixtures import run

BENCHMARK_DIR = Path(__file__).resolve().parent.parent
RUNS_DIR = BENCHMARK_DIR / "runs"

TASK_LOW = schedule.ScheduledTask(name="task-low", complexity="low")
TASK_HIGH = schedule.ScheduledTask(name="task-high", complexity="high")
MODEL_HAIKU = schedule.ScheduledModel(name="haiku", orchestrator="haiku", impl="haiku")
MODEL_OPUS = schedule.ScheduledModel(name="opus", orchestrator="opus", impl="opus")

SUCCESS = triage.Verdict(triage.SUCCESS, "resolved")
MODEL_LOSS = triage.Verdict(triage.MODEL_FAILURE, "no_model_patch")
TECHNICAL = triage.Verdict(triage.TECHNICAL_FAILURE, "api_fault:api_error_status=529")

# A technical verdict carrying the evidence a real one carries -- the recorded
# denial from `runs/do-in-steps__opus-opus__abs-stepped-slices`, line 2936 --
# so the bookkeeping tests assert on the shape production actually writes.
TECHNICAL_WITH_EVIDENCE = triage.Verdict(
    triage.TECHNICAL_FAILURE,
    "api_fault:rate_limit_status=rejected",
    fault=triage.ApiFault(
        slug="rate_limit_status=rejected",
        severity=triage.SEVERITY_RATE_LIMIT_REJECTED,
        line_number=2936,
        event={"type": "rate_limit_event",
               "rate_limit_info": {"status": "rejected", "rateLimitType": "five_hour"}},
    ),
    trial_dir=Path("runs/arm/trial-1"),
)


def planned(
    task: schedule.ScheduledTask,
    model: schedule.ScheduledModel,
    skill: str,
    *,
    skip_reason: str | None = None,
) -> schedule.PlannedRun:
    """One plan entry, runnable unless a skip reason is given."""
    return schedule.PlannedRun(
        task=task,
        model=model,
        skill=skill,
        skipped=skip_reason is not None,
        skip_reason=skip_reason,
    )


class FakeClock:
    """Stands in for `time.sleep`/`time.monotonic` so tests never actually wait.

    `requested` is every duration the loop asked to sleep for, in order --
    the thing the pacing tests assert on. `monotonic` advances by exactly
    those durations, so `elapsed_seconds` in the outcome is the sum of the
    waits and nothing else, which makes it deterministic.
    """

    def __init__(self) -> None:
        self.requested: list[float] = []
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.requested.append(seconds)
        self.now += seconds

    def monotonic(self) -> float:
        return self.now


class FakeRunner:
    """A `scheduler.Harness` whose side effects are recorded instead of performed.

    `verdicts` maps a planned run's state-file key to the sequence of verdicts
    successive executions of it should return, so a test can say "technical,
    then technical, then success" and watch the retry logic walk it. A key
    with no entry yields `default` every time.
    """

    def __init__(
        self,
        *,
        verdicts: dict[str, list[triage.Verdict]] | None = None,
        default: triage.Verdict = SUCCESS,
        completed: dict[str, scheduler.RunAttempt] | None = None,
        collect_results: list[str | None] | None = None,
        incomplete_trials: dict[str, dict[str, str]] | None = None,
        append_failure: str | None = None,
    ) -> None:
        self.verdicts = {key: list(values) for key, values in (verdicts or {}).items()}
        self.default = default
        self.completed = completed or {}
        self.collect_results = list(collect_results or [])
        self.incomplete_trials = incomplete_trials or {}
        self.append_failure = append_failure

        self.executed: list[str] = []
        self.completion_checks: list[str] = []
        self.collect_calls = 0
        self.attempts_logged: list[dict] = []
        self.clock = FakeClock()

    def _execute(self, run: schedule.PlannedRun) -> scheduler.RunAttempt:
        key = scheduler.run_key(run)
        self.executed.append(key)
        queued = self.verdicts.get(key)
        verdict = queued.pop(0) if queued else self.default
        return scheduler.RunAttempt(verdict, dict(self.incomplete_trials.get(key, {})))

    def _find_completed(self, run: schedule.PlannedRun) -> scheduler.RunAttempt | None:
        key = scheduler.run_key(run)
        self.completion_checks.append(key)
        return self.completed.get(key)

    def _collect_and_report(self) -> str | None:
        self.collect_calls += 1
        if not self.collect_results:
            return None
        return self.collect_results.pop(0)

    def _append_attempt(self, record: dict) -> str | None:
        """Records instead of writing, so the log's CONTENT is assertable.

        `append_failure` makes every append fail, which is how the tests prove
        that a broken attempt log cannot end a schedule.
        """
        self.attempts_logged.append(record)
        return self.append_failure

    @property
    def harness(self) -> scheduler.Harness:
        return scheduler.Harness(
            execute=self._execute,
            find_completed=self._find_completed,
            collect_and_report=self._collect_and_report,
            append_attempt=self._append_attempt,
            sleep=self.clock.sleep,
            monotonic=self.clock.monotonic,
        )


@contextlib.contextmanager
def quiet_subprocesses():
    """Silence stdout/stderr at the file-descriptor level, subprocesses included.

    `contextlib.redirect_stdout` rebinds `sys.stdout` only, which a spawned
    process never sees -- it inherits the real descriptors. `run_pier` and
    `run_collect_and_report` deliberately leave their children's output
    uncaptured (an operator staring at a silent terminal cannot tell a hung
    multi-day run from a slow one), so silencing them here needs `dup2`.
    """
    with open(os.devnull, "w") as devnull:
        saved = [os.dup(1), os.dup(2)]
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(saved[0], 1)
            os.dup2(saved[1], 2)
            for descriptor in saved:
                os.close(descriptor)


class SchedulerTestCase(unittest.TestCase):
    """Shared plumbing: a temp jobs dir for the state file, and a driver."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.jobs_dir = Path(self._tmp.name)
        self.state_path = scheduler.state_path_for(self.jobs_dir)

    def drive(
        self,
        plan: list[schedule.PlannedRun],
        runner: FakeRunner,
        *,
        between_runs_seconds: float = 7200,
        backoff_seconds: float = 7200,
        max_technical_retries: int = scheduler.MAX_TECHNICAL_RETRIES,
        force: bool = False,
    ) -> scheduler.ScheduleOutcome:
        return scheduler.run_schedule(
            plan,
            harness=runner.harness,
            between_runs_seconds=between_runs_seconds,
            backoff_seconds=backoff_seconds,
            state_path=self.state_path,
            max_technical_retries=max_technical_retries,
            force=force,
            log=lambda message: None,
        )

    def read_state(self) -> dict[str, dict]:
        return scheduler.load_state(self.state_path)


# --------------------------------------------------------------------------
# Argument surface
# --------------------------------------------------------------------------


class ScheduledArgumentTests(unittest.TestCase):
    """`--mode scheduled` must accept what it needs and refuse what it cannot honour.

    The refusals are the load-bearing half. A `--skill` that silently did
    nothing would let an operator believe they had run one skill's arms when
    they had in fact committed to the whole 33-run matrix -- roughly three
    days and several hundred dollars of difference.
    """

    def parse(self, argv: list[str]):
        parser = run.build_arg_parser()
        args = parser.parse_args(argv)
        run.validate_args(parser, args)
        return args

    def assert_rejected(self, argv: list[str], *needles: str) -> str:
        """argparse's `parser.error` prints to stderr and raises SystemExit(2)."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            self.parse(argv)
        self.assertEqual(caught.exception.code, 2)
        message = stderr.getvalue()
        for needle in needles:
            self.assertIn(needle, message)
        return message

    def test_scheduled_is_an_accepted_mode(self) -> None:
        self.assertEqual(run.build_arg_parser().parse_args(["--mode", "scheduled"]).mode, "scheduled")

    def test_scheduled_needs_neither_task_nor_n_tasks(self) -> None:
        args = self.parse(["--mode", "scheduled"])
        self.assertIsNone(args.task)
        self.assertIsNone(args.n_tasks)

    def test_schedule_defaults_to_the_committed_file(self) -> None:
        self.assertEqual(self.parse(["--mode", "scheduled"]).schedule, schedule.DEFAULT_SCHEDULE_PATH)

    def test_schedule_path_is_overridable(self) -> None:
        args = self.parse(["--mode", "scheduled", "--schedule", "/tmp/other.yaml"])
        self.assertEqual(args.schedule, Path("/tmp/other.yaml"))

    def test_rejects_every_matrix_flag_it_cannot_honour(self) -> None:
        for extra in (
            ["--task", "abs-stepped-slices"],
            ["--n-tasks", "3"],
            ["--skill", "do-in-steps"],
            ["--model", "sonnet"],
            ["--with-vanilla"],
        ):
            with self.subTest(extra=extra):
                # The message must name the flag AND point at the fix, or the
                # operator's next move is to guess.
                self.assert_rejected(["--mode", "scheduled", *extra], extra[0], "skips")

    def test_the_other_three_modes_are_unchanged(self) -> None:
        # Guards the whole existing CLI against this mode's additions.
        self.parse(["--mode", "single", "--task", "abs-stepped-slices"])
        self.parse(["--mode", "sample", "--n-tasks", "5"])
        self.parse(["--mode", "full"])
        self.parse(["--mode", "single", "--task", "t", "--skill", "do-in-steps", "--model", "opus"])

    def test_single_and_sample_still_require_their_own_flags(self) -> None:
        self.assert_rejected(["--mode", "single"])
        self.assert_rejected(["--mode", "sample"])


class PlannedRunToArmTests(unittest.TestCase):
    """`arm_for_planned_run` must reproduce the arm id `schedule.py` promises.

    Both halves of the harness key work on these ids -- pier's job name and
    the resume check -- so a mismatch would silently run the wrong arm into
    the right directory.
    """

    def setUp(self) -> None:
        self.plan = schedule.expand_schedule(schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH))

    def test_every_planned_run_builds_the_arm_it_names(self) -> None:
        for entry in self.plan:
            with self.subTest(cell=(entry.task.name, entry.model.name, entry.skill)):
                self.assertEqual(run.arm_for_planned_run(entry).id, entry.arm_id)

    def test_vanilla_runs_become_a_vanilla_arm_with_no_impl_tier(self) -> None:
        entry = planned(TASK_LOW, MODEL_OPUS, schedule.VANILLA_SKILL)
        arm = run.arm_for_planned_run(entry)
        self.assertTrue(arm.is_vanilla)
        self.assertIsNone(arm.skill)
        self.assertIsNone(arm.impl)

    def test_plugin_runs_carry_both_tiers(self) -> None:
        mixed = schedule.ScheduledModel(name="opus-sonnet", orchestrator="opus", impl="sonnet")
        arm = run.arm_for_planned_run(planned(TASK_LOW, mixed, "do-in-steps"))
        self.assertEqual((arm.skill, arm.orchestrator, arm.impl), ("do-in-steps", "opus", "sonnet"))


# --------------------------------------------------------------------------
# The loop
# --------------------------------------------------------------------------


class ExecutionOrderTests(SchedulerTestCase):
    """Runs happen in the plan's declared order, and skipped cells are reported."""

    def test_runnable_cells_execute_in_declared_order(self) -> None:
        plan = [
            planned(TASK_HIGH, MODEL_HAIKU, "do-in-steps"),
            planned(TASK_LOW, MODEL_OPUS, "do-and-judge"),
            planned(TASK_LOW, MODEL_HAIKU, "vanilla"),
        ]
        runner = FakeRunner()
        self.drive(plan, runner)
        self.assertEqual(runner.executed, [scheduler.run_key(entry) for entry in plan])

    def test_skipped_cells_are_reported_with_their_reason_and_never_executed(self) -> None:
        skipped = planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="too complex for haiku")
        plan = [skipped, planned(TASK_LOW, MODEL_OPUS, "do-in-steps")]
        runner = FakeRunner()

        outcome = self.drive(plan, runner)

        self.assertEqual(runner.executed, [scheduler.run_key(plan[1])])
        reports = outcome.with_disposition(scheduler.SKIPPED)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].planned.skip_reason, "too complex for haiku")
        self.assertIsNone(reports[0].verdict)

    def test_a_skipped_cell_is_not_checked_for_completion_either(self) -> None:
        # Nothing about a deliberately-unrun cell is worth a disk read.
        plan = [planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="deliberate")]
        runner = FakeRunner()
        self.drive(plan, runner)
        self.assertEqual(runner.completion_checks, [])

    def test_every_planned_cell_appears_in_the_outcome(self) -> None:
        plan = [
            planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="deliberate"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
        ]
        outcome = self.drive(plan, FakeRunner())
        self.assertEqual(len(outcome.reports), 2)


class PacingTests(SchedulerTestCase):
    """The waits, asserted as durations rather than endured as delays."""

    def three_runs(self) -> list[schedule.PlannedRun]:
        return [
            planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
            planned(TASK_HIGH, MODEL_OPUS, "do-in-steps"),
        ]

    def test_waits_the_declared_gap_between_consecutive_runs(self) -> None:
        runner = FakeRunner()
        outcome = self.drive(self.three_runs(), runner, between_runs_seconds=7200)
        # Three runs, two gaps -- nothing before the first, nothing after the last.
        self.assertEqual(runner.clock.requested, [7200, 7200])
        self.assertEqual(outcome.waits_requested, (7200, 7200))

    def test_no_wait_before_the_first_run(self) -> None:
        runner = FakeRunner()
        self.drive([self.three_runs()[0]], runner, between_runs_seconds=7200)
        self.assertEqual(runner.clock.requested, [])

    def test_skipped_cells_cost_no_wall_clock_time(self) -> None:
        plan = [
            planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="deliberate"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
        ]
        runner = FakeRunner()
        self.drive(plan, runner, between_runs_seconds=7200)
        self.assertEqual(runner.clock.requested, [])

    def test_a_zero_gap_requests_no_sleep_at_all(self) -> None:
        runner = FakeRunner()
        self.drive(self.three_runs(), runner, between_runs_seconds=0)
        self.assertEqual(runner.clock.requested, [])

    def test_elapsed_time_is_measured_with_the_injected_clock(self) -> None:
        runner = FakeRunner()
        outcome = self.drive(self.three_runs(), runner, between_runs_seconds=7200)
        self.assertEqual(outcome.elapsed_seconds, 14400)


class CollectAndReportTests(SchedulerTestCase):
    """collect.py + report.py run after every trial, and cannot end the schedule."""

    def test_invoked_once_after_each_executed_run(self) -> None:
        plan = [
            planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
        ]
        runner = FakeRunner()
        self.drive(plan, runner)
        self.assertEqual(runner.collect_calls, 2)

    def test_invoked_after_every_retry_attempt_too(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(verdicts={scheduler.run_key(entry): [TECHNICAL, SUCCESS]})
        self.drive([entry], runner)
        self.assertEqual(runner.collect_calls, 2)

    def test_not_invoked_for_a_skipped_or_resumed_run(self) -> None:
        skipped = planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="deliberate")
        done = planned(TASK_LOW, MODEL_OPUS, "do-in-steps")
        runner = FakeRunner(
            completed={scheduler.run_key(done): scheduler.RunAttempt(SUCCESS)}
        )
        self.drive([skipped, done], runner)
        self.assertEqual(runner.collect_calls, 0)

    def test_a_failure_is_recorded_and_the_schedule_continues(self) -> None:
        plan = [
            planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
            planned(TASK_HIGH, MODEL_OPUS, "do-in-steps"),
        ]
        runner = FakeRunner(collect_results=["collect.py exited 1", None, None])

        outcome = self.drive(plan, runner)

        # The whole plan still ran; the failure is reported, not raised.
        self.assertEqual(len(runner.executed), 3)
        self.assertEqual(outcome.collect_failures, ("collect.py exited 1",))

    def test_a_failure_on_every_single_run_still_completes_the_schedule(self) -> None:
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
                planned(TASK_LOW, MODEL_OPUS, "do-in-steps")]
        runner = FakeRunner(collect_results=["report.py exited 3", "report.py exited 3"])

        outcome = self.drive(plan, runner)

        self.assertEqual(len(runner.executed), 2)
        self.assertEqual(len(outcome.collect_failures), 2)
        self.assertEqual(len(outcome.with_outcome(triage.SUCCESS)), 2)


# --------------------------------------------------------------------------
# Retry policy -- the part that must never be wrong
# --------------------------------------------------------------------------


class RetryPolicyTests(SchedulerTestCase):
    """A model failure is recorded once. A technical failure is retried, bounded."""

    def test_a_model_failure_is_never_retried(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(default=MODEL_LOSS)

        outcome = self.drive([entry], runner)

        self.assertEqual(runner.executed, [scheduler.run_key(entry)])
        self.assertEqual(runner.clock.requested, [])  # no backoff was ever waited
        self.assertEqual(outcome.reports[0].attempts, 1)
        self.assertEqual(outcome.reports[0].verdict, MODEL_LOSS)

    def test_no_model_failure_reason_is_ever_retried(self) -> None:
        # Every way a trial can be the agent's fault, run through the loop.
        reasons = ("no_model_patch", "final_message_is_question", "unresolved", "agent_timeout")
        for index, reason in enumerate(reasons):
            with self.subTest(reason=reason):
                # A distinct cell per case: they share this test's state file,
                # and a run already settled by the previous case would be
                # skipped rather than run, hiding the thing being asserted.
                task = schedule.ScheduledTask(name=f"task-{index}", complexity="low")
                entry = planned(task, MODEL_HAIKU, "do-in-steps")
                runner = FakeRunner(default=triage.Verdict(triage.MODEL_FAILURE, reason))
                self.drive([entry], runner)
                self.assertEqual(len(runner.executed), 1)

    def test_a_technical_failure_backs_off_and_retries_the_same_run(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(verdicts={scheduler.run_key(entry): [TECHNICAL, SUCCESS]})

        outcome = self.drive([entry], runner, backoff_seconds=7200)

        self.assertEqual(runner.executed, [scheduler.run_key(entry)] * 2)
        self.assertEqual(runner.clock.requested, [7200])
        self.assertEqual(outcome.reports[0].attempts, 2)
        self.assertEqual(outcome.reports[0].verdict, SUCCESS)

    def test_retries_are_bounded_by_the_cap_and_then_recorded(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(default=TECHNICAL)  # never recovers

        outcome = self.drive([entry], runner, backoff_seconds=7200, max_technical_retries=2)

        self.assertEqual(len(runner.executed), 3)  # 1 attempt + 2 retries, and no more
        self.assertEqual(runner.clock.requested, [7200, 7200])
        self.assertEqual(outcome.reports[0].attempts, 3)
        self.assertEqual(outcome.reports[0].verdict.outcome, triage.TECHNICAL_FAILURE)

    def test_the_whole_schedule_is_bounded_even_if_everything_fails(self) -> None:
        # The property that makes unattended operation safe: total executions
        # can be computed before starting, and no input can exceed it.
        plan = [
            planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
            planned(TASK_HIGH, MODEL_OPUS, "do-in-steps"),
        ]
        runner = FakeRunner(default=TECHNICAL)

        self.drive(plan, runner, max_technical_retries=2)

        self.assertEqual(len(runner.executed), len(plan) * (1 + 2))

    def test_a_negative_retry_cap_is_refused_rather_than_running_nothing(self) -> None:
        with self.assertRaises(ValueError):
            self.drive([planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")],
                       FakeRunner(), max_technical_retries=-1)

    def test_zero_retries_means_exactly_one_attempt(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(default=TECHNICAL)
        self.drive([entry], runner, max_technical_retries=0)
        self.assertEqual(len(runner.executed), 1)
        self.assertEqual(runner.clock.requested, [])

    def test_a_failing_run_does_not_stop_the_ones_after_it(self) -> None:
        plan = [
            planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
        ]
        runner = FakeRunner(verdicts={scheduler.run_key(plan[0]): [TECHNICAL] * 3})
        self.drive(plan, runner, max_technical_retries=2)
        self.assertIn(scheduler.run_key(plan[1]), runner.executed)


# --------------------------------------------------------------------------
# Resumability
# --------------------------------------------------------------------------


class ResumptionTests(SchedulerTestCase):
    """A restarted schedule must not redo settled work -- least of all a loss."""

    def settle(self, entry: schedule.PlannedRun, verdict: triage.Verdict) -> None:
        scheduler.write_state(
            self.state_path,
            {scheduler.run_key(entry): scheduler.state_entry(entry, verdict, attempts=1)},
        )

    def test_a_recorded_model_failure_is_never_run_again(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        self.settle(entry, MODEL_LOSS)
        runner = FakeRunner()

        outcome = self.drive([entry], runner)

        self.assertEqual(runner.executed, [])
        self.assertEqual(outcome.reports[0].disposition, scheduler.RESUMED)
        self.assertEqual(outcome.reports[0].verdict.outcome, triage.MODEL_FAILURE)

    def test_a_recorded_success_is_never_run_again(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        self.settle(entry, SUCCESS)
        runner = FakeRunner()
        self.drive([entry], runner)
        self.assertEqual(runner.executed, [])

    def test_a_recorded_technical_failure_is_run_again_on_a_new_invocation(self) -> None:
        # Within one invocation the cap stops it; a fresh invocation is the
        # operator asking for another go, which is the whole point of
        # restarting after a quota window closes.
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        self.settle(entry, TECHNICAL)
        runner = FakeRunner()
        self.drive([entry], runner)
        self.assertEqual(runner.executed, [scheduler.run_key(entry)])

    def test_a_completed_job_dir_settles_a_run_with_no_state_file(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(completed={scheduler.run_key(entry): scheduler.RunAttempt(SUCCESS)})

        outcome = self.drive([entry], runner)

        self.assertEqual(runner.executed, [])
        self.assertEqual(outcome.reports[0].disposition, scheduler.RESUMED)
        # ...and it is written down, so the next restart need not re-read it.
        self.assertEqual(self.read_state()[scheduler.run_key(entry)]["outcome"], triage.SUCCESS)

    def test_a_completed_job_dir_that_was_not_a_fair_attempt_is_re_run(self) -> None:
        # Pier marks a job finished even when its trial raised, so "complete"
        # alone must not settle a cell -- otherwise a transient fault would
        # cost the matrix that cell on this invocation AND every later one,
        # since this check never consults the state file.
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(completed={scheduler.run_key(entry): scheduler.RunAttempt(TECHNICAL)})

        outcome = self.drive([entry], runner)

        self.assertEqual(runner.executed, [scheduler.run_key(entry)])
        self.assertEqual(outcome.reports[0].disposition, scheduler.RAN)

    def test_only_the_unsettled_cells_run_on_a_restart(self) -> None:
        done = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        pending = planned(TASK_LOW, MODEL_OPUS, "do-in-steps")
        self.settle(done, MODEL_LOSS)
        runner = FakeRunner()

        self.drive([done, pending], runner)

        self.assertEqual(runner.executed, [scheduler.run_key(pending)])

    def test_a_resumed_run_is_not_paced_against(self) -> None:
        done = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        pending = planned(TASK_LOW, MODEL_OPUS, "do-in-steps")
        self.settle(done, SUCCESS)
        runner = FakeRunner()
        self.drive([done, pending], runner, between_runs_seconds=7200)
        self.assertEqual(runner.clock.requested, [])

    def test_force_re_runs_everything_and_ignores_the_state_file(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        self.settle(entry, MODEL_LOSS)
        runner = FakeRunner(completed={scheduler.run_key(entry): scheduler.RunAttempt(SUCCESS)})

        self.drive([entry], runner, force=True)

        self.assertEqual(runner.executed, [scheduler.run_key(entry)])
        self.assertEqual(runner.completion_checks, [])


class StateFileTests(SchedulerTestCase):
    """The on-disk resume record: schema, and surviving its own corruption."""

    def test_every_settled_run_is_written_with_its_outcome_and_attempts(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(verdicts={scheduler.run_key(entry): [TECHNICAL, MODEL_LOSS]})

        self.drive([entry], runner)

        record = self.read_state()[scheduler.run_key(entry)]
        self.assertEqual(record["outcome"], triage.MODEL_FAILURE)
        self.assertEqual(record["reason"], "no_model_patch")
        self.assertEqual(record["attempts"], 2)
        self.assertEqual(record["arm_id"], entry.arm_id)
        self.assertIn("recorded_at", record)

    def test_the_document_carries_its_version(self) -> None:
        self.drive([planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")], FakeRunner())
        document = json.loads(self.state_path.read_text())
        self.assertEqual(document["version"], scheduler.STATE_VERSION)
        self.assertIn("updated_at", document)

    def test_skipped_runs_are_not_written_down(self) -> None:
        # A skip is a property of schedule.yaml, not a result to remember.
        entry = planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="deliberate")
        self.drive([entry], FakeRunner())
        self.assertEqual(self.read_state(), {})

    def test_an_unreadable_state_file_is_treated_as_absent(self) -> None:
        self.state_path.write_text("{ this is not json")
        self.assertEqual(scheduler.load_state(self.state_path), {})

    def test_a_missing_state_file_is_treated_as_absent(self) -> None:
        self.assertEqual(scheduler.load_state(self.jobs_dir / "nope.json"), {})

    def test_a_future_version_is_treated_as_absent(self) -> None:
        # Re-running costs money; misreading a schema silently drops cells.
        self.state_path.write_text(json.dumps({"version": 999, "runs": {"a": {"outcome": "success"}}}))
        self.assertEqual(scheduler.load_state(self.state_path), {})

    def test_a_corrupt_state_file_causes_a_re_run_rather_than_a_crash(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        self.state_path.write_text("truncated")
        runner = FakeRunner()
        self.drive([entry], runner)
        self.assertEqual(runner.executed, [scheduler.run_key(entry)])

    def test_the_verdicts_evidence_is_recorded_alongside_its_reason(self) -> None:
        # So `scheduler-state.json` alone answers "why?", instead of needing
        # the triage re-run by hand over an 8 MB transcript.
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(default=TECHNICAL_WITH_EVIDENCE)

        self.drive([entry], runner, max_technical_retries=0)

        record = self.read_state()[scheduler.run_key(entry)]
        self.assertEqual(record["trial_dir"], "runs/arm/trial-1")
        self.assertEqual(record["api_fault"]["slug"], "rate_limit_status=rejected")
        self.assertEqual(record["api_fault"]["line_number"], 2936)

    def test_a_verdict_with_no_evidence_writes_no_evidence_keys(self) -> None:
        # An absent key and a null one mean the same thing to every reader,
        # and a file where most entries read `"api_fault": null` is noise.
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        self.drive([entry], FakeRunner(default=SUCCESS))
        record = self.read_state()[scheduler.run_key(entry)]
        self.assertNotIn("api_fault", record)
        self.assertNotIn("trial_dir", record)


class AttemptLogTests(SchedulerTestCase):
    """The append-only per-attempt decision trail.

    Its whole reason for existing is the attempts the state file overwrites:
    a cell recorded `attempts: 3` says nothing about what the first two
    attempts decided, and those are where an investigation starts.
    """

    def test_one_record_is_appended_per_attempt_not_per_cell(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(
            verdicts={scheduler.run_key(entry): [TECHNICAL, TECHNICAL, MODEL_LOSS]}
        )

        self.drive([entry], runner)

        self.assertEqual([record["attempt"] for record in runner.attempts_logged], [1, 2, 3])
        self.assertEqual(
            [record["outcome"] for record in runner.attempts_logged],
            [triage.TECHNICAL_FAILURE, triage.TECHNICAL_FAILURE, triage.MODEL_FAILURE],
        )

    def test_each_record_names_the_cell_the_arm_and_the_budget(self) -> None:
        entry = planned(TASK_HIGH, MODEL_OPUS, "do-and-judge")
        runner = FakeRunner()

        self.drive([entry], runner, max_technical_retries=2)

        record = runner.attempts_logged[0]
        self.assertEqual(record["run_key"], scheduler.run_key(entry))
        self.assertEqual(record["arm_id"], entry.arm_id)
        self.assertEqual((record["attempt"], record["budget"]), (1, 3))
        self.assertEqual(record["reason"], "resolved")
        self.assertIn("recorded_at", record)

    def test_the_backoff_paid_before_each_retry_is_recorded(self) -> None:
        # Makes the wall-clock cost of a stuck cell readable off the log
        # rather than inferred from timestamps.
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(default=TECHNICAL)

        self.drive([entry], runner, backoff_seconds=7200)

        self.assertEqual(
            [record["slept_seconds"] for record in runner.attempts_logged], [0.0, 7200, 7200]
        )

    def test_the_fault_evidence_travels_into_the_log(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(default=TECHNICAL_WITH_EVIDENCE)

        self.drive([entry], runner, max_technical_retries=0)

        fault = runner.attempts_logged[0]["api_fault"]
        self.assertEqual(fault["slug"], "rate_limit_status=rejected")
        self.assertEqual(fault["event"]["rate_limit_info"]["status"], "rejected")

    def test_every_record_is_json_serialisable(self) -> None:
        # The production writer json.dumps() these; a record it could not
        # serialise would be a lost log line on every attempt.
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(default=TECHNICAL_WITH_EVIDENCE)
        self.drive([entry], runner)
        for record in runner.attempts_logged:
            json.dumps(record)

    def test_skipped_and_resumed_cells_log_nothing(self) -> None:
        # Neither of them attempted anything, and an attempt log with
        # non-attempts in it would misstate what a run cost.
        skipped = planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="deliberate")
        resumed = planned(TASK_HIGH, MODEL_OPUS, "do-in-steps")
        runner = FakeRunner(
            completed={scheduler.run_key(resumed): scheduler.RunAttempt(SUCCESS)}
        )

        self.drive([skipped, resumed], runner)

        self.assertEqual(runner.attempts_logged, [])

    def test_a_failing_attempt_log_cannot_end_the_schedule(self) -> None:
        # Instrumentation must never outrank the benchmark. Note this is NOT
        # a collect/report failure and so does not reach the exit code.
        entries = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
                   planned(TASK_HIGH, MODEL_OPUS, "do-in-steps")]
        runner = FakeRunner(append_failure="disk full")

        outcome = self.drive(entries, runner)

        self.assertEqual(len(runner.executed), 2)
        self.assertEqual(outcome.collect_failures, ())
        self.assertEqual(len(outcome.with_disposition(scheduler.RAN)), 2)

    def test_the_production_writer_appends_whole_lines(self) -> None:
        path = scheduler.attempt_log_path_for(self.jobs_dir / "nested")

        self.assertIsNone(scheduler.append_attempt_record(path, {"attempt": 1}))
        self.assertIsNone(scheduler.append_attempt_record(path, {"attempt": 2}))

        records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(records, [{"attempt": 1}, {"attempt": 2}])

    def test_the_production_writer_describes_a_failure_instead_of_raising(self) -> None:
        # Same contract as `collect_and_report`: never an exception out of a
        # side effect the loop cannot do anything about.
        unwritable = self.jobs_dir / "a-file" / scheduler.ATTEMPT_LOG_FILENAME
        (self.jobs_dir / "a-file").write_text("not a directory")

        failure = scheduler.append_attempt_record(unwritable, {"attempt": 1})

        self.assertIsNotNone(failure)
        self.assertIn(str(unwritable), failure)

    def test_an_unserialisable_record_is_described_rather_than_raised(self) -> None:
        path = scheduler.attempt_log_path_for(self.jobs_dir)
        failure = scheduler.append_attempt_record(path, {"event": object()})
        self.assertIsNotNone(failure)


# --------------------------------------------------------------------------
# Triage's own rules are NOT tested here
#
# They used to be: four classes covering `verdict_from_signals`, the transcript
# scan and the recorded job directories lived in this file, because it was the
# first place that needed them. That arrangement is what let two triage
# defects ship -- a file whose subject is the scheduling loop is not where
# anyone looks to check a status vocabulary, and the loop tests all pass
# canned verdicts, so they stayed green throughout. `tests/test_triage.py` now
# owns every triage rule, directly and in one place; nothing about them is
# asserted here, so the two files cannot contradict each other.
#
# What this file still covers about triage is the ONE thing that is genuinely
# the loop's business: what the loop DOES with a verdict -- retry it, record
# it, resume from it, log it, exit on it.
# --------------------------------------------------------------------------



# --------------------------------------------------------------------------
# Summary and exit codes
# --------------------------------------------------------------------------


class SummaryExitCodeTests(SchedulerTestCase):
    """`report_scheduled_summary` must reuse the existing codes, not invent one."""

    def exit_code_for(self, runner: FakeRunner, plan: list[schedule.PlannedRun]) -> int:
        """The summary prints; swallow it so a passing suite stays readable."""
        outcome = self.drive(plan, runner)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return run.report_scheduled_summary(outcome)

    def test_an_all_clean_schedule_exits_zero(self) -> None:
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        self.assertEqual(self.exit_code_for(FakeRunner(), plan), 0)

    def test_a_model_failure_alone_exits_zero(self) -> None:
        # An agent that attempted and scored wrong is a measurement, not a
        # harness error -- same as an unresolved `--mode single` trial today.
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        runner = FakeRunner(default=triage.Verdict(triage.MODEL_FAILURE, "unresolved"))
        self.assertEqual(self.exit_code_for(runner, plan), 0)

    def test_a_technical_failure_exits_with_the_arm_failed_code(self) -> None:
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        self.assertEqual(
            self.exit_code_for(FakeRunner(default=TECHNICAL), plan), run.EXIT_ARM_FAILED
        )

    def test_a_collect_or_report_failure_exits_with_the_arm_failed_code(self) -> None:
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        runner = FakeRunner(collect_results=["report.py exited 1"])
        self.assertEqual(self.exit_code_for(runner, plan), run.EXIT_ARM_FAILED)

    def test_incomplete_trials_exit_with_the_existing_incomplete_code(self) -> None:
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(
            default=MODEL_LOSS,
            incomplete_trials={scheduler.run_key(entry): {"trial-1": "no_model_patch"}},
        )
        self.assertEqual(self.exit_code_for(runner, [entry]), run.EXIT_TRIALS_INCOMPLETE)

    def test_a_technical_failure_outranks_an_incomplete_trial(self) -> None:
        # Same precedence the other three modes use: FAIL beats INCOMPLETE.
        entry = planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")
        runner = FakeRunner(
            default=TECHNICAL,
            incomplete_trials={scheduler.run_key(entry): {"trial-1": "no_model_patch"}},
        )
        self.assertEqual(self.exit_code_for(runner, [entry]), run.EXIT_ARM_FAILED)

    def test_a_schedule_of_nothing_but_skips_exits_zero(self) -> None:
        plan = [planned(TASK_LOW, MODEL_HAIKU, "vanilla", skip_reason="deliberate")]
        self.assertEqual(self.exit_code_for(FakeRunner(), plan), 0)


class StuckTechnicalCellTests(SchedulerTestCase):
    """Fix 5: a technical failure whose job directory already holds a
    finished trial is STUCK -- pier's own per-trial resume
    (`Job._maybe_init_existing_job`) will keep skipping that trial forever,
    on every future `--mode scheduled` invocation, so `report_scheduled_
    summary` must call it out separately from the generic technical-failure
    list and print the recipe that actually clears it.
    """

    NO_TRIAL_RESULT = triage.Verdict(triage.TECHNICAL_FAILURE, triage.NO_TRIAL_RESULT_REASON)

    def args_for(self, dataset_dir: Path | None = None) -> argparse.Namespace:
        return argparse.Namespace(
            jobs_dir=self.jobs_dir, dataset_dir=dataset_dir or Path("/dataset")
        )

    def test_no_trial_result_is_not_stuck(self) -> None:
        # Nothing was ever written to disk for this cell, so the NEXT
        # invocation's `pier run` has no existing result.json to skip -- a
        # genuinely fresh attempt, not a stuck one.
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        outcome = self.drive(plan, FakeRunner(default=self.NO_TRIAL_RESULT))
        self.assertEqual(run.stuck_technical_reports(outcome), [])

    def test_every_other_technical_reason_is_stuck(self) -> None:
        # TECHNICAL's reason ("api_fault:...") implies a trial DID finish and
        # write a result.json -- pier's own resume will keep skipping it.
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        outcome = self.drive(plan, FakeRunner(default=TECHNICAL))
        stuck = run.stuck_technical_reports(outcome)
        self.assertEqual(len(stuck), 1)
        self.assertEqual(stuck[0].planned, plan[0])

    def test_a_success_or_model_failure_is_never_stuck(self) -> None:
        plan = [
            planned(TASK_LOW, MODEL_HAIKU, "do-in-steps"),
            planned(TASK_LOW, MODEL_OPUS, "do-in-steps"),
        ]
        outcome = self.drive(plan, FakeRunner(default=SUCCESS))
        self.assertEqual(run.stuck_technical_reports(outcome), [])

    def test_the_summary_calls_out_stuck_cells_with_their_job_dir_and_recipe(self) -> None:
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        outcome = self.drive(plan, FakeRunner(default=TECHNICAL))
        args = self.args_for()
        expected_job_dir = run.scheduled_job_dir(args, plan[0])

        stderr = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            run.report_scheduled_summary(outcome, args)

        printed = stderr.getvalue()
        self.assertIn("STUCK", printed)
        self.assertIn(str(expected_job_dir), printed)
        # The actual recommended command: remove the job dir, then re-run
        # WITHOUT --force. `--force` bypasses run.py's own already-done
        # check for every OTHER cell too, forcing them all back through pier
        # and re-paying the full between-run pacing wait for each one -- see
        # scheduler.py's `_resume` comment on why a bare `--force` does not
        # actually clear a stuck cell. The message may still discuss
        # `--force` in prose (to explain why it is not the fix); what must
        # never appear is the flag tacked onto the recipe's own command line.
        recipe_command = f"rm -rf {expected_job_dir} && uv run python3 run.py --mode scheduled"
        self.assertIn(recipe_command, printed)
        self.assertNotIn(f"{recipe_command} --force", printed)

    def test_no_stuck_cells_prints_no_stuck_section(self) -> None:
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        outcome = self.drive(plan, FakeRunner(default=SUCCESS))
        stderr = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            run.report_scheduled_summary(outcome, self.args_for())
        self.assertNotIn("STUCK", stderr.getvalue())

    def test_the_summary_still_works_with_no_args_given(self) -> None:
        # `args` defaults to `None` so a caller with no Namespace at hand
        # (every other test in this file's `SummaryExitCodeTests`) keeps
        # working unchanged -- only the STUCK line's job-dir path degrades.
        plan = [planned(TASK_LOW, MODEL_HAIKU, "do-in-steps")]
        outcome = self.drive(plan, FakeRunner(default=TECHNICAL))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exit_code = run.report_scheduled_summary(outcome)
        self.assertEqual(exit_code, run.EXIT_ARM_FAILED)


class CollectAndReportSubprocessTests(unittest.TestCase):
    """The real `collect.py` + `report.py` subprocess wiring, run for real.

    Everything else in this file substitutes this step, so these are the only
    tests that would catch a mistyped flag or a script that cannot start --
    and that mistake would surface on night one of a multi-day run, after the
    first trial, with nobody watching. Writes into a scratch directory so the
    committed `results.json`/`report.html` are untouched.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out_dir = Path(self._tmp.name)

    def test_both_steps_succeed_against_the_recorded_runs(self) -> None:
        with quiet_subprocesses():
            failure = run.run_collect_and_report(RUNS_DIR, out_dir=self.out_dir)

        self.assertIsNone(failure)
        for produced in ("results.json", "results.csv", "report.html"):
            with self.subTest(file=produced):
                self.assertTrue((self.out_dir / produced).is_file())

    def test_a_failing_step_is_described_rather_than_raised(self) -> None:
        # An unwritable out-dir makes collect.py fail; the scheduler must get
        # a string back so it can record it and carry on.
        unwritable = self.out_dir / "results.json"
        unwritable.write_text("{}")  # a FILE where collect.py needs a directory
        with quiet_subprocesses():
            failure = run.run_collect_and_report(RUNS_DIR, out_dir=unwritable)

        self.assertIsInstance(failure, str)
        self.assertIn("collect.py", failure)


class PreviewTests(unittest.TestCase):
    """`--dry-run`'s output: order, skips with reasons, pacing, and what is done."""

    def setUp(self) -> None:
        self.declared = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)
        self.plan = schedule.expand_schedule(self.declared)

    def preview(self, state: dict | None = None) -> list[str]:
        return scheduler.preview_schedule(
            self.plan,
            between_runs_seconds=self.declared.between_runs_seconds,
            backoff_seconds=self.declared.technical_failure_backoff_seconds,
            state=state,
        )

    def test_every_planned_cell_gets_a_line_plus_two_summary_lines(self) -> None:
        self.assertEqual(len(self.preview()), len(self.plan) + 2)

    def test_skipped_cells_carry_their_reason(self) -> None:
        skip_lines = [line for line in self.preview() if "SKIP" in line]
        self.assertEqual(len(skip_lines), 12)
        for line in skip_lines:
            self.assertGreater(len(line.split("--")[-1].strip()), 20)

    def test_the_pacing_line_states_the_declared_gap_and_the_total(self) -> None:
        pacing = next(line for line in self.preview() if "pacing:" in line)
        self.assertIn("7200s between runs", pacing)
        self.assertIn("33 still to run", pacing)

    def test_the_retry_line_states_the_bound_on_total_executions(self) -> None:
        retries = next(line for line in self.preview() if "retries:" in line)
        self.assertIn(f"at most {33 * (1 + scheduler.MAX_TECHNICAL_RETRIES)} executions", retries)

    def test_cells_already_complete_on_disk_are_shown_as_done_too(self) -> None:
        # The preview must consult BOTH resumption sources the run consults,
        # or it reports a schedule length the run will not honour.
        first = next(entry for entry in self.plan if not entry.skipped)
        lines = scheduler.preview_schedule(
            self.plan,
            between_runs_seconds=self.declared.between_runs_seconds,
            backoff_seconds=self.declared.technical_failure_backoff_seconds,
            already_done=lambda entry: "success (resolved)" if entry is first else None,
        )
        self.assertTrue(any("DONE" in line and "resolved" in line for line in lines))
        self.assertIn("32 still to run", next(line for line in lines if "pacing:" in line))

    def test_the_real_recorded_runs_are_previewed_as_done(self) -> None:
        # End-to-end against `runs/`: two committed job directories cover
        # cells of the committed schedule, and the preview must say so.
        args = argparse.Namespace(jobs_dir=RUNS_DIR, dataset_dir=BENCHMARK_DIR / "data")
        done = [
            entry
            for entry in self.plan
            if not entry.skipped and run.describe_completed(entry, args) is not None
        ]
        self.assertGreaterEqual(len(done), 1)

    def test_settled_cells_are_shown_as_done_and_drop_out_of_the_count(self) -> None:
        first = next(entry for entry in self.plan if not entry.skipped)
        state = {scheduler.run_key(first): {"outcome": triage.MODEL_FAILURE, "reason": "unresolved"}}
        lines = self.preview(state)
        self.assertTrue(any("DONE" in line and "will not re-run" in line for line in lines))
        self.assertIn("32 still to run", next(line for line in lines if "pacing:" in line))


if __name__ == "__main__":
    unittest.main()
