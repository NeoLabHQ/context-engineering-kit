#!/usr/bin/env python3
"""Unit tests for `run.py`'s `--skill` flag: arm-matrix filtering, preflight
arm/job-name selection, and argparse validation.

Stubs the `agent` module for the same reason `test_run_dispatch.py` does --
`run.py` does `import agent`, and the real one needs `pier`, which isn't
installed in the interpreter this suite runs under. See that file's module
docstring for the full rationale; this file only repeats the minimum needed
to import `run` standalone under `python3 -m unittest` (module import order
across test files isn't guaranteed, so this guard can't assume the other
test module has already registered the stub).
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


class DefaultArmMatrixTests(unittest.TestCase):
    """`build_arms()` with no `skill` argument must behave exactly as before
    `--skill` was added: 10 plugin arms, 13 with vanilla, same order.
    """

    def test_ten_plugin_arms_without_vanilla(self) -> None:
        arms = run.build_arms(include_vanilla=False)
        self.assertEqual(len(arms), len(run.SKILLS) * len(run.CELLS))
        self.assertEqual(len(arms), 10)
        self.assertTrue(all(not arm.is_vanilla for arm in arms))

    def test_thirteen_arms_with_vanilla(self) -> None:
        arms = run.build_arms(include_vanilla=True)
        self.assertEqual(len(arms), 13)
        vanilla_arms = [arm for arm in arms if arm.is_vanilla]
        self.assertEqual(len(vanilla_arms), 3)

    def test_arm_order_is_skills_outer_cells_inner(self) -> None:
        # SKILLS x CELLS, skill varying slower than cell -- collect.py and the
        # dry-run print order both depend on this staying stable.
        arms = run.build_arms(include_vanilla=False)
        expected_ids = [
            f"{skill}__{orchestrator}-{impl}"
            for skill in run.SKILLS
            for orchestrator, impl in run.CELLS
        ]
        self.assertEqual([arm.id for arm in arms], expected_ids)

    def test_vanilla_arms_appended_after_all_plugin_arms(self) -> None:
        arms = run.build_arms(include_vanilla=True)
        expected_vanilla_ids = [f"vanilla__{model}" for model in run.VANILLA_MODELS]
        self.assertEqual([arm.id for arm in arms[-3:]], expected_vanilla_ids)


class SkillFilteredArmMatrixTests(unittest.TestCase):
    """`build_arms(skill=...)` restricts plugin arms to one skill's CELLS;
    vanilla control arms are untouched by the filter.
    """

    def test_skill_filter_yields_only_that_skills_cells(self) -> None:
        arms = run.build_arms(include_vanilla=False, skill="do-in-steps")
        self.assertEqual(len(arms), len(run.CELLS))
        self.assertTrue(all(arm.skill == "do-in-steps" for arm in arms))

    def test_skill_filter_preserves_cell_order(self) -> None:
        arms = run.build_arms(include_vanilla=False, skill="do-and-judge")
        expected_ids = [
            f"do-and-judge__{orchestrator}-{impl}" for orchestrator, impl in run.CELLS
        ]
        self.assertEqual([arm.id for arm in arms], expected_ids)

    def test_skill_filter_does_not_drop_vanilla_arms(self) -> None:
        arms = run.build_arms(include_vanilla=True, skill="do-in-steps")
        vanilla_arms = [arm for arm in arms if arm.is_vanilla]
        self.assertEqual(len(vanilla_arms), 3)
        self.assertEqual(len(arms), len(run.CELLS) + 3)

    def test_skill_filter_does_not_duplicate_vanilla_arms(self) -> None:
        # Vanilla arms have skill=None; a naive filter keyed on `arm.skill ==
        # skill` could accidentally match or multiply them. It must not.
        arms = run.build_arms(include_vanilla=True, skill="do-and-judge")
        vanilla_ids = [arm.id for arm in arms if arm.is_vanilla]
        self.assertEqual(vanilla_ids, [f"vanilla__{model}" for model in run.VANILLA_MODELS])

    def test_without_with_vanilla_flag_skill_filter_has_no_vanilla_arms(self) -> None:
        arms = run.build_arms(include_vanilla=False, skill="do-and-judge")
        self.assertTrue(all(not arm.is_vanilla for arm in arms))


class PreflightArmSelectionTests(unittest.TestCase):
    """`preflight_arm`/`preflight_job_name` pick the cheapest cell (CELLS[0])
    for whichever skill is requested, and keep the default skill's job dir
    name unchanged so the pinned recorded transcript stays reachable.
    """

    def test_preflight_arm_uses_cheapest_cell_for_default_skill(self) -> None:
        arm = run.preflight_arm(run.SKILLS[0])
        cheapest_orchestrator, cheapest_impl = run.CELLS[0]
        self.assertEqual(arm.skill, run.SKILLS[0])
        self.assertEqual(arm.orchestrator, cheapest_orchestrator)
        self.assertEqual(arm.impl, cheapest_impl)

    def test_preflight_arm_uses_cheapest_cell_for_other_skill(self) -> None:
        other_skill = run.SKILLS[1]
        arm = run.preflight_arm(other_skill)
        cheapest_orchestrator, cheapest_impl = run.CELLS[0]
        self.assertEqual(arm.skill, other_skill)
        self.assertEqual(arm.orchestrator, cheapest_orchestrator)
        self.assertEqual(arm.impl, cheapest_impl)

    def test_default_skill_job_name_is_unchanged_bare_preflight(self) -> None:
        # Pinned: tests/test_run_dispatch.py and tests/collect_fixtures.py
        # read the recorded transcript at exactly
        # runs/_preflight/abs-stepped-slices__HyQJyYy/agent/claude-code.txt.
        self.assertEqual(run.preflight_job_name(run.SKILLS[0]), "_preflight")
        self.assertEqual(run.preflight_job_name(run.SKILLS[0]), run.PREFLIGHT_JOB_NAME)

    def test_other_skill_gets_a_distinct_job_name(self) -> None:
        other_skill = run.SKILLS[1]
        job_name = run.preflight_job_name(other_skill)
        self.assertNotEqual(job_name, run.PREFLIGHT_JOB_NAME)
        self.assertIn(other_skill, job_name)

    def test_both_skills_preflight_files_coexist_in_one_jobs_dir(self) -> None:
        # test_other_skill_gets_a_distinct_job_name only proves the two job
        # names differ; it doesn't prove that preflighting both skills back
        # to back actually leaves both skills' files intact on disk. Drive
        # the real write_prompt_template/write_arm_metadata code paths for
        # both skills into one shared jobs_dir and check every file survives
        # with the right, distinct content.
        with tempfile.TemporaryDirectory() as jobs_dir_str:
            jobs_dir = Path(jobs_dir_str)
            job_dirs = {}

            for skill in run.SKILLS:
                arm = run.preflight_arm(skill)
                job_dir = jobs_dir / run.preflight_job_name(skill)
                job_dirs[skill] = job_dir
                run.write_prompt_template(job_dir, arm)
                run.write_arm_metadata(
                    job_dir, arm, orchestrator_model_id="claude-haiku-4-5-20251001", mode="single"
                )

            # The two skills must not have landed in the same job dir.
            self.assertNotEqual(job_dirs[run.SKILLS[0]], job_dirs[run.SKILLS[1]])

            for skill in run.SKILLS:
                job_dir = job_dirs[skill]
                prompt_text = (job_dir / "prompt.j2").read_text()
                arm_metadata = json.loads((job_dir / "arm.json").read_text())

                self.assertEqual(prompt_text, run.render_prompt_template_text(run.preflight_arm(skill)))
                self.assertEqual(arm_metadata["skill"], skill)
                self.assertEqual(arm_metadata["arm_id"], run.preflight_arm(skill).id)


class SkillArgparseTests(unittest.TestCase):
    """`--skill`'s accepted values come from `SKILLS` -- argparse itself
    enforces this via `choices=`, so an unknown value must be rejected before
    any arm is built.
    """

    def test_skill_omitted_defaults_to_none(self) -> None:
        parser = run.build_arg_parser()
        args = parser.parse_args(["--preflight", "--task", "some-task"])
        self.assertIsNone(args.skill)

    def test_skill_accepts_each_known_value(self) -> None:
        parser = run.build_arg_parser()
        for skill in run.SKILLS:
            args = parser.parse_args(["--preflight", "--task", "some-task", "--skill", skill])
            self.assertEqual(args.skill, skill)

    def test_unknown_skill_value_is_rejected(self) -> None:
        parser = run.build_arg_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["--preflight", "--task", "some-task", "--skill", "not-a-real-skill"]
            )


if __name__ == "__main__":
    unittest.main()
