#!/usr/bin/env python3
"""Unit tests for `run.py`'s `--skill` and `--model` flags: arm-matrix
filtering, preflight arm/job-name selection, and argparse validation.

Imports `run` through `tests/run_fixtures.py`, which stubs the `agent` module
first -- `run.py` does `import agent`, and the real one needs `pier`, which
isn't installed in the interpreter this suite normally runs under. See that
module's docstring for the full rationale.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .run_fixtures import run


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


class ModelFilteredArmMatrixTests(unittest.TestCase):
    """`build_arms(model=...)` restricts CELLS to that one symmetric tier pair
    (1 CELLS arm per skill in play instead of 5); combined with `skill=...`
    it yields exactly one arm. Vanilla controls ARE filtered by `model`
    (unlike `skill`), since they're per-model rather than per-skill.
    """

    def test_model_filter_yields_one_cell_per_skill(self) -> None:
        arms = run.build_arms(include_vanilla=False, model="sonnet")
        self.assertEqual(len(arms), len(run.SKILLS))
        self.assertTrue(all(arm.orchestrator == "sonnet" and arm.impl == "sonnet" for arm in arms))

    def test_model_filter_selects_the_symmetric_cell(self) -> None:
        for tier in run.MODEL_CHOICES:
            arms = run.build_arms(include_vanilla=False, model=tier)
            for arm in arms:
                self.assertEqual((arm.orchestrator, arm.impl), (tier, tier))

    def test_model_and_skill_together_yield_exactly_one_arm(self) -> None:
        # Every skill x tier pairing (2 skills x 3 tiers = 6 combinations) must
        # each independently collapse the matrix to its own single arm id --
        # not just the one pairing spot-checked before this was parameterized.
        for skill in run.SKILLS:
            for tier in run.MODEL_CHOICES:
                arms = run.build_arms(include_vanilla=False, skill=skill, model=tier)
                self.assertEqual(len(arms), 1)
                [arm] = arms
                self.assertEqual(arm.id, f"{skill}__{tier}-{tier}")

    def test_model_filter_restricts_vanilla_arms_to_one(self) -> None:
        # Unlike --skill, --model DOES filter vanilla controls: they're
        # per-model, so leaving all 3 in would reintroduce the two tiers the
        # operator asked to exclude.
        arms = run.build_arms(include_vanilla=True, model="haiku")
        vanilla_arms = [arm for arm in arms if arm.is_vanilla]
        self.assertEqual([arm.id for arm in vanilla_arms], ["vanilla__haiku"])

    def test_model_and_skill_and_vanilla_together_yield_two_arms(self) -> None:
        arms = run.build_arms(include_vanilla=True, skill="do-and-judge", model="sonnet")
        expected_ids = ["do-and-judge__sonnet-sonnet", "vanilla__sonnet"]
        self.assertEqual([arm.id for arm in arms], expected_ids)

    def test_model_choices_are_derived_from_symmetric_cells(self) -> None:
        # MODEL_CHOICES must be exactly the CELLS entries where orchestrator
        # == impl -- the user's own "haiku,haiku or sonnet,sonnet" framing.
        expected = [orchestrator for orchestrator, impl in run.CELLS if orchestrator == impl]
        self.assertEqual(run.MODEL_CHOICES, expected)
        self.assertEqual(run.MODEL_CHOICES, ["haiku", "sonnet", "opus"])


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


class PreflightModelSelectionTests(unittest.TestCase):
    """`preflight_arm`/`preflight_job_name` select the requested tier's arm
    instead of the cheapest cell when `model` is given, and keep the bare
    `_preflight` job name only for the no-flags-at-all default.
    """

    def test_preflight_arm_uses_requested_model_instead_of_cheapest(self) -> None:
        arm = run.preflight_arm(run.SKILLS[0], "opus")
        self.assertEqual(arm.skill, run.SKILLS[0])
        self.assertEqual((arm.orchestrator, arm.impl), ("opus", "opus"))

    def test_preflight_arm_model_none_is_unchanged_cheapest_behavior(self) -> None:
        cheapest_orchestrator, cheapest_impl = run.CELLS[0]
        arm = run.preflight_arm(run.SKILLS[0], None)
        self.assertEqual((arm.orchestrator, arm.impl), (cheapest_orchestrator, cheapest_impl))

    def test_default_skill_with_model_gets_a_distinct_job_name(self) -> None:
        job_name = run.preflight_job_name(run.SKILLS[0], "sonnet")
        self.assertNotEqual(job_name, run.PREFLIGHT_JOB_NAME)
        self.assertIn("sonnet", job_name)

    def test_default_skill_no_model_job_name_still_bare(self) -> None:
        # Backward compatibility: omitting --model entirely must not disturb
        # the pinned bare `_preflight` name for the default skill.
        self.assertEqual(run.preflight_job_name(run.SKILLS[0], None), run.PREFLIGHT_JOB_NAME)

    def test_other_skill_with_model_combines_both_in_job_name(self) -> None:
        other_skill = run.SKILLS[1]
        job_name = run.preflight_job_name(other_skill, "opus")
        self.assertIn(other_skill, job_name)
        self.assertIn("opus", job_name)

    def test_same_skill_different_models_get_distinct_job_names(self) -> None:
        # Preflighting the same skill at two different tiers back to back
        # must not collide -- each tier's prompt.j2/arm.json needs its own dir.
        haiku_job_name = run.preflight_job_name(run.SKILLS[0], "haiku")
        opus_job_name = run.preflight_job_name(run.SKILLS[0], "opus")
        self.assertNotEqual(haiku_job_name, opus_job_name)


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


class ModelArgparseTests(unittest.TestCase):
    """`--model`'s accepted values come from `MODEL_CHOICES` -- argparse itself
    enforces this via `choices=`, so an unknown value must be rejected before
    any arm is built.
    """

    def test_model_omitted_defaults_to_none(self) -> None:
        parser = run.build_arg_parser()
        args = parser.parse_args(["--preflight", "--task", "some-task"])
        self.assertIsNone(args.model)

    def test_model_accepts_each_known_value(self) -> None:
        parser = run.build_arg_parser()
        for tier in run.MODEL_CHOICES:
            args = parser.parse_args(["--preflight", "--task", "some-task", "--model", tier])
            self.assertEqual(args.model, tier)

    def test_unknown_model_value_is_rejected(self) -> None:
        parser = run.build_arg_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["--preflight", "--task", "some-task", "--model", "not-a-real-tier"]
            )

    def test_model_and_skill_flags_combine_in_argparse(self) -> None:
        parser = run.build_arg_parser()
        args = parser.parse_args(
            ["--mode", "single", "--task", "some-task", "--skill", "do-in-steps", "--model", "sonnet"]
        )
        self.assertEqual(args.skill, "do-in-steps")
        self.assertEqual(args.model, "sonnet")


if __name__ == "__main__":
    unittest.main()
