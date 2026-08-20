#!/usr/bin/env python3
"""Unit tests for `run.py`'s three-state per-arm verdict: `arm_status_label`
and `find_incomplete_trials`.

These pin the contract an operator (and a CI job) reads: PASS, INCOMPLETE and
FAIL are three distinct outcomes, and the end-of-run summary may only claim
success for the first. The rules deciding whether an individual trial is
incomplete live in `collect.py` and are tested in
`test_collect_completion_gate.py`; what is under test here is that `run.py`
asks collect.py rather than reimplementing them, and reports the answer.

`run` is imported through `run_fixtures` -- see that module's docstring.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from .run_fixtures import run


def write_trial(job_dir: Path, trial_id: str, *, model_patch: bool, final_message: str) -> Path:
    """One trial directory under `job_dir`, in pier's real layout.

    Always writes `result.json` (a trial without one was never judged -- pier
    failed that arm, and its exit code is the signal), then optionally the
    `artifacts/model.patch` and always a transcript whose terminal `result`
    event carries `final_message`.
    """
    trial_dir = job_dir / trial_id
    (trial_dir / "agent").mkdir(parents=True)
    (trial_dir / "result.json").write_text(json.dumps({"task_name": "task-1"}))
    (trial_dir / "agent" / "claude-code.txt").write_text(
        json.dumps({"type": "result", "subtype": "success", "result": final_message})
    )
    if model_patch:
        (trial_dir / "artifacts").mkdir()
        (trial_dir / "artifacts" / "model.patch").write_text("diff --git a/x b/x\n")
    return trial_dir


FINISHED_MESSAGE = "All 3 steps are complete and the work is committed."
ABANDONING_MESSAGE = "I could narrow the scope or keep going. Which would you like?"


class ArmStatusLabelTests(unittest.TestCase):
    def test_a_clean_arm_is_pass(self) -> None:
        self.assertEqual(run.arm_status_label(0, {}), "PASS")

    def test_a_nonzero_pier_exit_is_fail(self) -> None:
        self.assertEqual(run.arm_status_label(2, {}), "FAIL (exit 2)")

    def test_incomplete_trials_under_a_clean_exit_are_incomplete(self) -> None:
        # The recorded failure: pier exited 0 and printed PASS for a trial that
        # committed nothing.
        label = run.arm_status_label(0, {"task__abc": "no_model_patch"})
        self.assertEqual(label, "INCOMPLETE (1 trials -- no_model_patch x1)")

    def test_the_label_breaks_incompleteness_down_by_reason(self) -> None:
        label = run.arm_status_label(
            0,
            {
                "task-a__1": "no_model_patch",
                "task-b__2": "final_message_is_question",
                "task-c__3": "no_model_patch",
            },
        )
        self.assertEqual(
            label, "INCOMPLETE (3 trials -- final_message_is_question x1, no_model_patch x2)"
        )

    def test_a_pier_failure_outranks_incompleteness(self) -> None:
        # When pier itself failed, its exit code is the more actionable signal
        # and the artifacts a completion judgment needs may not exist at all.
        label = run.arm_status_label(1, {"task__abc": "no_model_patch"})
        self.assertEqual(label, "FAIL (exit 1)")


class FindIncompleteTrialsTests(unittest.TestCase):
    def test_an_arm_whose_trials_all_finished_reports_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp) / "do-in-steps__sonnet-sonnet"
            write_trial(job_dir, "task-a__1", model_patch=True, final_message=FINISHED_MESSAGE)
            write_trial(job_dir, "task-b__2", model_patch=True, final_message=FINISHED_MESSAGE)

            self.assertEqual(run.find_incomplete_trials(job_dir), {})

    def test_both_incompleteness_signals_are_reported_per_trial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp) / "do-in-steps__sonnet-sonnet"
            write_trial(job_dir, "task-a__1", model_patch=True, final_message=FINISHED_MESSAGE)
            write_trial(job_dir, "task-b__2", model_patch=False, final_message=FINISHED_MESSAGE)
            write_trial(job_dir, "task-c__3", model_patch=True, final_message=ABANDONING_MESSAGE)

            self.assertEqual(
                run.find_incomplete_trials(job_dir),
                {"task-b__2": "no_model_patch", "task-c__3": "final_message_is_question"},
            )

    def test_an_empty_or_absent_job_dir_reports_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_job_dir = Path(tmp) / "empty"
            empty_job_dir.mkdir()
            self.assertEqual(run.find_incomplete_trials(empty_job_dir), {})
            self.assertEqual(run.find_incomplete_trials(Path(tmp) / "never-ran"), {})

    def test_the_job_level_result_json_is_not_mistaken_for_a_trial(self) -> None:
        # `runs/<arm>/result.json` is pier's JOB result, one level above the
        # trials -- judging it as a trial would report a phantom incomplete on
        # every arm. Same glob-depth trap collect.py documents.
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp) / "do-in-steps__sonnet-sonnet"
            job_dir.mkdir()
            (job_dir / "result.json").write_text(json.dumps({"finished_at": "2026-08-18T20:03:01"}))
            write_trial(job_dir, "task-a__1", model_patch=True, final_message=FINISHED_MESSAGE)

            self.assertEqual(run.find_incomplete_trials(job_dir), {})

    def test_the_gate_is_collect_pys_and_not_a_second_copy(self) -> None:
        # If these ever diverge, a run's live verdict and results.json's
        # recorded status would disagree about the same trial.
        import collect

        self.assertIs(
            run.collect.find_trial_incompleteness_reason,
            collect.find_trial_incompleteness_reason,
        )


def write_finished_result(job_dir: Path) -> None:
    """Mark `job_dir` as a pier job that ran to completion.

    `finished_at` set == pier ran this job to completion; see `is_arm_complete`.
    """
    (job_dir / "result.json").write_text(json.dumps({"finished_at": "2026-08-18T20:03:01"}))


def write_single_task_config(job_dir: Path, task: str) -> None:
    """The one field of pier's own `config.json` `is_arm_complete`'s
    task-aware backward-compatibility check reads: a `tasks` list with this
    job's one task. Simulates the pre-fix flat `jobs_dir/<arm-id>` layout,
    where `--mode single` always planned exactly one task per job.
    """
    (job_dir / "config.json").write_text(json.dumps({"tasks": [{"path": f"/data/{task}"}]}))


class MainSummaryTests(unittest.TestCase):
    """`main()`'s end-of-run summary and exit code, with pier stubbed out.

    The defect that motivated all of this was a summary line: pier exited 0, so
    the harness printed "all 1 arms completed successfully" over a trial that
    committed nothing. These tests hold that line to its meaning.

    Only the three seams that shell out are patched -- `run_arm` (which would
    write templates and build a command), `run_pier` (the subprocess) and the
    `pier`-on-PATH check. Everything between them is the real `main()`.
    """

    ARM = run.Arm("do-in-steps", "sonnet", "sonnet")

    def job_dir_for(self, jobs_dir: Path, task: str) -> Path:
        """Where `main()` itself will look for `task`'s completion state --
        computed through the real `arm_job_dir`, not a hardcoded string, so
        these tests can't silently drift from what the code under test
        actually does.
        """
        return run.arm_job_dir(
            jobs_dir, self.ARM, mode="single", task=task, dataset_dir=run.SCRIPT_DIR / "data"
        )

    def run_main(
        self, jobs_dir: Path, *, pier_exit_code: int = 0, task: str = "task-1"
    ) -> tuple[int, str, str]:
        """Invoke `main()` for one arm against `jobs_dir`; capture (code, out, err)."""
        argv = [
            "--mode", "single",
            "--task", task,
            "--skill", "do-in-steps",
            "--model", "sonnet",
            "--jobs-dir", str(jobs_dir),
        ]
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(run, "run_pier", return_value=pier_exit_code), mock.patch.object(
            run, "run_arm", side_effect=lambda arm, args, dataset_args: (jobs_dir, ["pier", "run"])
        ), mock.patch.object(run.shutil, "which", return_value="/usr/bin/pier"):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = run.main(argv)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_a_clean_arm_still_reports_success_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "runs"
            job_dir = self.job_dir_for(jobs_dir, "task-1")
            write_trial(job_dir, "task-a__1", model_patch=True, final_message=FINISHED_MESSAGE)

            exit_code, stdout, stderr = self.run_main(jobs_dir)

            self.assertEqual(exit_code, 0)
            self.assertIn("completed successfully", stdout)
            self.assertIn("PASS", stdout)
            self.assertEqual(stderr, "")

    def test_an_incomplete_trial_stops_the_summary_claiming_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "runs"
            job_dir = self.job_dir_for(jobs_dir, "task-1")
            write_trial(job_dir, "task-a__1", model_patch=False, final_message=FINISHED_MESSAGE)

            exit_code, stdout, stderr = self.run_main(jobs_dir)

            self.assertEqual(exit_code, run.EXIT_TRIALS_INCOMPLETE)
            self.assertNotIn("completed successfully", stdout)
            self.assertIn("INCOMPLETE", stdout)
            self.assertIn("INCOMPLETE trials", stderr)
            self.assertIn("no_model_patch", stderr)

    def test_a_pier_failure_reports_failure_not_incompleteness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "runs"
            job_dir = self.job_dir_for(jobs_dir, "task-1")
            write_trial(job_dir, "task-a__1", model_patch=False, final_message=FINISHED_MESSAGE)

            exit_code, stdout, stderr = self.run_main(jobs_dir, pier_exit_code=1)

            self.assertEqual(exit_code, run.EXIT_ARM_FAILED)
            self.assertNotIn("completed successfully", stdout)
            self.assertIn("FAIL (exit 1)", stdout)
            self.assertIn("arms failed", stderr)

    def test_a_resumed_run_rechecks_arms_it_skips(self) -> None:
        # An arm pier already finished is skipped without re-running -- but a
        # run that skips an arm holding abandoned trials must not then report
        # success for them.
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "runs"
            job_dir = self.job_dir_for(jobs_dir, "task-1")
            write_trial(job_dir, "task-a__1", model_patch=False, final_message=FINISHED_MESSAGE)
            write_finished_result(job_dir)

            exit_code, stdout, stderr = self.run_main(jobs_dir)

            self.assertIn("SKIP", stdout)
            self.assertIn("1 INCOMPLETE trials", stdout)
            self.assertNotIn("completed successfully", stdout)
            self.assertIn("no_model_patch", stderr)
            self.assertEqual(exit_code, run.EXIT_TRIALS_INCOMPLETE)

    def test_a_never_run_task_is_not_skipped_by_a_different_completed_task(self) -> None:
        # The regression this fix closes: `do-in-steps__sonnet-sonnet` (the
        # bare arm-id dir) had already finished "task-1" -- asking for the
        # never-run "task-2" under the same skill+model must still execute
        # it, not report a false SKIP because the two tasks share an arm-id.
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "runs"
            legacy_job_dir = jobs_dir / self.ARM.id
            write_trial(legacy_job_dir, "task-1__1", model_patch=True, final_message=FINISHED_MESSAGE)
            write_finished_result(legacy_job_dir)
            write_single_task_config(legacy_job_dir, "task-1")

            exit_code, stdout, stderr = self.run_main(jobs_dir, task="task-2")

            self.assertNotIn("SKIP", stdout)
            self.assertIn("$ pier run", stdout)
            self.assertIn("completed successfully", stdout)
            self.assertEqual(exit_code, 0)

    def test_a_legacy_flat_job_dir_still_skips_a_genuine_rerun_of_its_own_task(self) -> None:
        # Runs recorded before task-aware job dirs existed (the flat
        # `jobs_dir/<arm-id>`, with no task suffix) must still be recognized
        # as complete when the SAME task is asked for again -- this is the
        # "genuine re-run" case the fix must not turn into wasted work.
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "runs"
            legacy_job_dir = jobs_dir / self.ARM.id
            write_trial(legacy_job_dir, "task-1__1", model_patch=True, final_message=FINISHED_MESSAGE)
            write_finished_result(legacy_job_dir)
            write_single_task_config(legacy_job_dir, "task-1")

            exit_code, stdout, stderr = self.run_main(jobs_dir, task="task-1")

            self.assertIn("SKIP", stdout)
            self.assertIn("completed successfully", stdout)
            self.assertEqual(exit_code, 0)

    def test_force_reruns_a_legacy_completed_task(self) -> None:
        # --force must still override even the backward-compatibility path,
        # exactly as it overrides the primary one.
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "runs"
            legacy_job_dir = jobs_dir / self.ARM.id
            write_trial(legacy_job_dir, "task-1__1", model_patch=True, final_message=FINISHED_MESSAGE)
            write_finished_result(legacy_job_dir)
            write_single_task_config(legacy_job_dir, "task-1")

            argv = [
                "--mode", "single",
                "--task", "task-1",
                "--skill", "do-in-steps",
                "--model", "sonnet",
                "--jobs-dir", str(jobs_dir),
                "--force",
            ]
            stdout_io, stderr_io = io.StringIO(), io.StringIO()
            with mock.patch.object(run, "run_pier", return_value=0), mock.patch.object(
                run,
                "run_arm",
                side_effect=lambda arm, args, dataset_args: (jobs_dir, ["pier", "run"]),
            ), mock.patch.object(run.shutil, "which", return_value="/usr/bin/pier"):
                with contextlib.redirect_stdout(stdout_io), contextlib.redirect_stderr(stderr_io):
                    exit_code = run.main(argv)

            self.assertNotIn("SKIP", stdout_io.getvalue())
            self.assertIn("$ pier run", stdout_io.getvalue())
            self.assertEqual(exit_code, 0)


class PreflightCompletionGateTests(unittest.TestCase):
    """`--preflight` must not print a bare PASSED over a trial that never finished.

    Its plugin verdict is deliberately kept separate from the completion state:
    preflight runs one task on the cheapest arm, which can lose or abandon that
    task without saying anything about whether the plugin loaded. So PASSED
    still reports the plugin checks, and the exit code carries completion using
    the same three-state contract main() uses.

    This matters concretely: `runs/_preflight-do-in-steps/…9ryVMmH`, the one
    recorded trial ending on an abandoning question, is a preflight trial.
    """

    STREAM_EVENTS = [
        {"type": "system", "subtype": "init", "plugins": [{"name": "sadd"}], "plugin_errors": []},
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_01",
                        "name": "Agent",
                        "input": {"subagent_type": "sadd:judge", "prompt": "judge it"},
                    }
                ],
            },
        },
    ]

    def run_preflight(
        self, jobs_dir: Path, *, model_patch: bool, final_message: str
    ) -> tuple[int, str, str]:
        """Run `run_preflight` with pier stubbed out to write a transcript.

        The stub populates the job directory the way a real pier run would --
        one trial with a stream log, a result.json and (optionally) a patch --
        so everything after `run_pier` in `run_preflight` is the real code.
        """
        args = run.build_arg_parser().parse_args(
            [
                "--preflight",
                "--task", "cattrs-partial-structuring-recovery",
                "--skill", "do-in-steps",
                "--jobs-dir", str(jobs_dir),
                "--dataset-dir", str(jobs_dir / "data"),
            ]
        )
        job_dir = jobs_dir / run.preflight_job_name(args.skill)

        def fake_run_pier(cmd: list[str]) -> int:
            trial_dir = write_trial(
                job_dir, "cattrs__abc", model_patch=model_patch, final_message=final_message
            )
            (trial_dir / "agent" / "claude-code.txt").write_text(
                "\n".join(
                    json.dumps(event)
                    for event in [
                        *self.STREAM_EVENTS,
                        {"type": "result", "subtype": "success", "result": final_message},
                    ]
                )
            )
            return 0

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(run, "run_pier", side_effect=fake_run_pier):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = run.run_preflight(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_a_finished_preflight_trial_still_passes_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exit_code, stdout, stderr = self.run_preflight(
                Path(tmp) / "runs", model_patch=True, final_message=FINISHED_MESSAGE
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("[preflight] PASSED:", stdout)
            self.assertNotIn("INCOMPLETE", stdout + stderr)

    def test_a_preflight_trial_with_no_patch_is_reported_and_exits_three(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exit_code, stdout, stderr = self.run_preflight(
                Path(tmp) / "runs", model_patch=False, final_message=FINISHED_MESSAGE
            )

            self.assertEqual(exit_code, run.EXIT_TRIALS_INCOMPLETE)
            self.assertNotIn("[preflight] PASSED:", stdout)
            self.assertIn("PASSED (plugin checks only)", stderr)
            self.assertIn("no_model_patch", stderr)

    def test_a_preflight_trial_ending_on_a_question_is_reported(self) -> None:
        # The recorded shape: the plugin worked, the agent asked the operator to
        # choose, and there was nobody to answer.
        with tempfile.TemporaryDirectory() as tmp:
            exit_code, stdout, stderr = self.run_preflight(
                Path(tmp) / "runs", model_patch=True, final_message=ABANDONING_MESSAGE
            )

            self.assertEqual(exit_code, run.EXIT_TRIALS_INCOMPLETE)
            self.assertNotIn("[preflight] PASSED:", stdout)
            self.assertIn("final_message_is_question", stderr)


class ExitCodeContractTests(unittest.TestCase):
    def test_incomplete_has_its_own_exit_code_distinct_from_failure_and_usage(self) -> None:
        # 2 is argparse's usage-error code (`parser.error`), so INCOMPLETE
        # cannot use it without making "you invoked me wrong" and "the agents
        # abandoned their tasks" indistinguishable to a CI job.
        self.assertEqual(run.EXIT_ARM_FAILED, 1)
        self.assertEqual(run.EXIT_TRIALS_INCOMPLETE, 3)
        self.assertNotIn(2, {run.EXIT_ARM_FAILED, run.EXIT_TRIALS_INCOMPLETE})


if __name__ == "__main__":
    unittest.main()
