#!/usr/bin/env python3
"""Unit tests for `schedule.py` -- the declarative schedule configuration layer.

WHAT THESE TESTS GUARD
-----------------------
`schedule.yaml` decides which (task, model, skill) trials a scheduled
benchmark actually runs. A misconfiguration there does not crash anything --
it produces a benchmark that completes cleanly while measuring the wrong
matrix, and nobody notices until the report is already being quoted. So the
bulk of this module is *negative* tests: one per validation failure mode,
each asserting the error names the offending field, because an error that
only says "invalid schedule" costs the operator the same debugging time a
silent default would have.

The other half pins the things later steps read: expansion order (Step 2
paces runs in this order), the runnable/skipped split with reasons (Step 3
records them), and the complexity ordering (Step 4 uses it as a chart axis).

Imports `run` through `tests/run_fixtures.py` purely to cross-check
`schedule.py`'s mirrored copies of `CELLS`/`SKILLS` against the real ones --
see `MirroredConstantTests`.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

import schedule

from .run_fixtures import run


def minimal_document() -> dict:
    """A small, valid schedule document that the validation tests mutate one
    field at a time.

    Deliberately smaller than the committed `schedule.yaml` so that a failing
    assertion points at the field the test mutated rather than at incidental
    scale.
    """
    return {
        "models": [
            {"name": "haiku", "orchestrator": "haiku", "impl": "haiku"},
            {"name": "opus-sonnet", "orchestrator": "opus", "impl": "sonnet"},
        ],
        "skills": ["vanilla", "do-and-judge"],
        "duration": {"between_runs": "2h", "technical_failure_backoff": "30m"},
        "tasks": [
            {"name": "task-low", "complexity": "low"},
            {"name": "task-high", "complexity": "high"},
        ],
        "skips": [
            {"reason": "example rule", "models": ["haiku"], "skills": ["vanilla"]},
        ],
    }


def parse(document: dict) -> schedule.Schedule:
    return schedule.parse_schedule(document, source="test-schedule")


class MirroredConstantTests(unittest.TestCase):
    """`schedule.py` cannot `import run` (run.py imports agent, which imports
    pier), so it carries its own copies of the tier pairs and skill names.
    These tests are the mechanism that keeps the copies honest.
    """

    def test_valid_cells_mirrors_run_cells_exactly(self) -> None:
        self.assertEqual(list(schedule.VALID_CELLS), list(run.CELLS))

    def test_known_skills_is_vanilla_plus_run_skills(self) -> None:
        self.assertEqual(list(schedule.KNOWN_SKILLS), ["vanilla", *run.SKILLS])

    def test_vanilla_skill_constant_is_not_a_run_skill(self) -> None:
        # The whole point of the translation: run.py has no "vanilla" skill
        # string, it has `Arm.skill is None`.
        self.assertNotIn(schedule.VANILLA_SKILL, run.SKILLS)


class CommittedScheduleFileTests(unittest.TestCase):
    """The real, committed `schedule.yaml` must load and validate. This is the
    test that fails when someone hand-edits the file into an invalid state.
    """

    def setUp(self) -> None:
        self.schedule = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)

    def test_declares_the_five_cells_as_models(self) -> None:
        names = [model.name for model in self.schedule.models]
        self.assertEqual(
            names, ["haiku", "sonnet", "opus", "sonnet-haiku", "opus-sonnet"]
        )

    def test_every_model_maps_onto_a_real_cell(self) -> None:
        pairs = [(model.orchestrator, model.impl) for model in self.schedule.models]
        self.assertEqual(sorted(pairs), sorted(run.CELLS))

    def test_declares_vanilla_plus_both_plugin_skills(self) -> None:
        self.assertEqual(
            list(self.schedule.skills), ["vanilla", "do-and-judge", "do-in-steps"]
        )

    def test_declares_the_three_tasks_with_their_complexities(self) -> None:
        self.assertEqual(
            {task.name: task.complexity for task in self.schedule.tasks},
            {
                "kombu-single-active-consumer-priority": "high",
                "cattrs-partial-structuring-recovery": "medium",
                "abs-stepped-slices": "low",
            },
        )

    def test_both_durations_are_two_hours(self) -> None:
        self.assertEqual(self.schedule.between_runs_seconds, 2 * 60 * 60)
        self.assertEqual(self.schedule.technical_failure_backoff_seconds, 2 * 60 * 60)

    def test_the_two_durations_are_independent_knobs(self) -> None:
        # They read the same today, which is exactly the risk: a parser that
        # wired both fields to one key would pass every assertion above. Feed
        # them different values and they must move independently, because Step
        # 2 has to read the right one for each situation.
        document = minimal_document()
        document["duration"] = {
            "between_runs": "2h",
            "technical_failure_backoff": "15m",
        }
        parsed = parse(document)
        self.assertEqual(parsed.between_runs_seconds, 7200)
        self.assertEqual(parsed.technical_failure_backoff_seconds, 900)

    def test_declares_exactly_the_three_skip_rules(self) -> None:
        self.assertEqual(len(self.schedule.skip_rules), 3)
        for rule in self.schedule.skip_rules:
            self.assertTrue(rule.reason.strip())


class CommittedScheduleExpansionTests(unittest.TestCase):
    """The arithmetic of the committed schedule: 3 tasks x 5 models x 3 skills
    = 45 planned runs, 12 of them skipped, 33 runnable.

    The 12 come from three skip rules whose model selectors are disjoint, so
    they simply add up: haiku-at-vanilla over 3 tasks (3), sonnet on the
    kombu task over 3 skills (3), and the two mixed pairs at vanilla over 3
    tasks (2 x 3 = 6).
    """

    def setUp(self) -> None:
        self.schedule = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)
        self.runs = schedule.expand_schedule(self.schedule)

    def test_full_matrix_is_the_cartesian_product(self) -> None:
        self.assertEqual(len(self.runs), 3 * 5 * 3)
        self.assertEqual(len(self.runs), 45)

    def test_every_combination_appears_exactly_once(self) -> None:
        keys = [(r.task.name, r.model.name, r.skill) for r in self.runs]
        self.assertEqual(len(set(keys)), len(keys))

    def test_twelve_skipped_thirty_three_runnable(self) -> None:
        skipped = [r for r in self.runs if r.skipped]
        runnable = [r for r in self.runs if not r.skipped]
        self.assertEqual(len(skipped), 3 + 3 + 6)
        self.assertEqual(len(skipped), 12)
        self.assertEqual(len(runnable), 33)
        self.assertEqual(len(skipped) + len(runnable), 45)

    def test_the_three_skip_rules_are_disjoint(self) -> None:
        # The 3 + 3 + 6 arithmetic above is only additive because no cell is
        # claimed by two rules. Their model selectors do not overlap today;
        # this asserts it rather than trusting it, because overlapping rules
        # would make the counts silently wrong instead of visibly wrong.
        claimed = [
            {
                (r.task.name, r.model.name, r.skill)
                for r in self.runs
                if rule.matches(r.task, r.model, r.skill)
            }
            for rule in self.schedule.skip_rules
        ]
        self.assertEqual([len(cells) for cells in claimed], [3, 3, 6])
        for first in range(len(claimed)):
            for second in range(first + 1, len(claimed)):
                self.assertEqual(claimed[first] & claimed[second], set())

    def test_haiku_vanilla_is_skipped_for_all_three_tasks(self) -> None:
        skipped = {
            (r.task.name, r.model.name, r.skill) for r in self.runs if r.skipped
        }
        for task in ("kombu-single-active-consumer-priority",
                     "cattrs-partial-structuring-recovery",
                     "abs-stepped-slices"):
            self.assertIn((task, "haiku", "vanilla"), skipped)

    def test_kombu_on_sonnet_is_skipped_across_all_skills(self) -> None:
        skipped = {
            (r.task.name, r.model.name, r.skill) for r in self.runs if r.skipped
        }
        for skill in ("vanilla", "do-and-judge", "do-in-steps"):
            self.assertIn(
                ("kombu-single-active-consumer-priority", "sonnet", skill), skipped
            )

    def test_mixed_model_pairs_are_skipped_at_vanilla_for_all_three_tasks(
        self,
    ) -> None:
        skipped = {
            (r.task.name, r.model.name, r.skill) for r in self.runs if r.skipped
        }
        for task in ("kombu-single-active-consumer-priority",
                     "cattrs-partial-structuring-recovery",
                     "abs-stepped-slices"):
            for model in ("sonnet-haiku", "opus-sonnet"):
                self.assertIn((task, model, "vanilla"), skipped)

    def test_mixed_model_pairs_still_run_under_both_plugin_skills(self) -> None:
        # The exclusion is about vanilla specifically -- a mixed pair is the
        # whole point of the sweep everywhere the impl tier is actually used.
        runnable = {
            (r.task.name, r.model.name, r.skill)
            for r in self.runs
            if not r.skipped
        }
        for model in ("sonnet-haiku", "opus-sonnet"):
            for skill in ("do-and-judge", "do-in-steps"):
                self.assertIn(("abs-stepped-slices", model, skill), runnable)

    def test_the_skipped_set_is_exactly_those_twelve(self) -> None:
        all_tasks = (
            "kombu-single-active-consumer-priority",
            "cattrs-partial-structuring-recovery",
            "abs-stepped-slices",
        )
        expected = {
            (task, "haiku", "vanilla") for task in all_tasks
        } | {
            ("kombu-single-active-consumer-priority", "sonnet", skill)
            for skill in ("vanilla", "do-and-judge", "do-in-steps")
        } | {
            (task, model, "vanilla")
            for task in all_tasks
            for model in ("sonnet-haiku", "opus-sonnet")
        }
        actual = {
            (r.task.name, r.model.name, r.skill) for r in self.runs if r.skipped
        }
        self.assertEqual(actual, expected)
        self.assertEqual(len(expected), 12)

    def test_every_skipped_run_carries_a_nonempty_reason(self) -> None:
        for planned in self.runs:
            if planned.skipped:
                self.assertTrue(planned.skip_reason and planned.skip_reason.strip())

    def test_no_runnable_run_carries_a_reason(self) -> None:
        for planned in self.runs:
            if not planned.skipped:
                self.assertIsNone(planned.skip_reason)

    def test_haiku_skip_reason_mentions_haiku_being_overmatched(self) -> None:
        planned = next(
            r for r in self.runs
            if r.model.name == "haiku" and r.skill == "vanilla"
        )
        self.assertIn("haiku", planned.skip_reason.lower())

    def test_sonnet_skip_reason_mentions_sonnet(self) -> None:
        planned = next(
            r for r in self.runs
            if r.model.name == "sonnet"
            and r.task.name == "kombu-single-active-consumer-priority"
        )
        self.assertIn("sonnet", planned.skip_reason.lower())

    def test_mixed_pair_skip_reason_explains_the_mechanism(self) -> None:
        # "Not run" is not an explanation. The reason has to say WHY these
        # cells are the same trial as their symmetric twins, because the
        # report prints it verbatim to a reader who will otherwise read the
        # blank as missing data.
        planned = next(
            r for r in self.runs
            if r.model.name == "sonnet-haiku" and r.skill == "vanilla"
        )
        reason = planned.skip_reason.lower()
        self.assertIn("implementer tier", reason)
        self.assertIn("vanilla__sonnet", reason)
        self.assertIn("job directory", reason)


class RunnableRunUniquenessTests(unittest.TestCase):
    """No two runnable runs may target the same job.

    `run.py` derives a trial's job directory from `(arm_id, task)` alone, so
    two runnable cells sharing a `(task, arm_id)` pair are not two
    measurements -- they are one measurement paid for twice, racing for one
    directory, and each capable of re-running a trial the other's model was
    explicitly skipped for.

    This is the structural guarantee behind the mixed-pair vanilla skip in
    `schedule.yaml`: re-adding `sonnet-haiku` or `opus-sonnet` at vanilla
    fails here, immediately, instead of during a benchmark night.
    """

    def setUp(self) -> None:
        self.schedule = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)
        self.runs = schedule.expand_schedule(self.schedule)

    def runnable_job_keys(self) -> list[tuple[str, str]]:
        """The job each runnable run would claim: `run.py` names a job
        directory from the arm id and the task, and nothing else.
        """
        return [(r.task.name, r.arm_id) for r in self.runs if not r.skipped]

    def vanilla_cell_for(self, task_name: str, model_name: str) -> schedule.PlannedRun:
        """The one vanilla cell for a (task, model) pair, skipped or not."""
        return next(
            planned
            for planned in self.runs
            if planned.is_vanilla
            and planned.task.name == task_name
            and planned.model.name == model_name
        )

    def test_no_two_runnable_runs_share_a_task_and_arm_id(self) -> None:
        keys = self.runnable_job_keys()
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        self.assertEqual(duplicates, [], f"colliding runnable runs: {duplicates}")
        self.assertEqual(len(set(keys)), len(keys))

    def test_every_runnable_vanilla_cell_has_its_own_arm_id_per_task(self) -> None:
        # The narrower statement of the same invariant, aimed at the arms that
        # could actually collide: vanilla is the only skill whose arm id drops
        # a tier, so it is the only one where two models can converge.
        vanilla = [
            r for r in self.runs if not r.skipped and r.is_vanilla
        ]
        keys = {(r.task.name, r.arm_id) for r in vanilla}
        self.assertEqual(len(keys), len(vanilla))

    def test_the_excluded_mixed_cells_are_duplicates_not_lost_measurements(
        self,
    ) -> None:
        """The invariant is upheld by excluding cells, so pin that nothing was
        lost: every excluded mixed-pair vanilla cell has the same arm id, for
        the same task, as a cell the schedule still plans.
        """
        excluded = [
            planned
            for planned in self.runs
            if planned.is_vanilla
            and planned.skipped
            and planned.model.orchestrator != planned.model.impl
        ]
        self.assertEqual(len(excluded), 6)

        for planned in excluded:
            twin = self.vanilla_cell_for(planned.task.name, planned.model.orchestrator)
            self.assertEqual(twin.arm_id, planned.arm_id)



class ExpansionOrderTests(unittest.TestCase):
    """Order is part of the contract: Step 2 executes runs in this order and
    Step 4 groups the report by it. It must be a pure function of the file.
    """

    def setUp(self) -> None:
        self.schedule = parse(minimal_document())

    def test_expansion_is_repeatable(self) -> None:
        first = schedule.expand_schedule(self.schedule)
        second = schedule.expand_schedule(self.schedule)
        self.assertEqual(first, second)

    def test_two_loads_of_the_same_file_expand_identically(self) -> None:
        a = schedule.expand_schedule(schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH))
        b = schedule.expand_schedule(schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH))
        self.assertEqual(a, b)

    def test_order_is_task_then_model_then_skill_in_declaration_order(self) -> None:
        runs = schedule.expand_schedule(self.schedule)
        expected = [
            (task["name"], model["name"], skill)
            for task in minimal_document()["tasks"]
            for model in minimal_document()["models"]
            for skill in minimal_document()["skills"]
        ]
        self.assertEqual([(r.task.name, r.model.name, r.skill) for r in runs], expected)

    def test_skipped_runs_stay_in_place_rather_than_being_filtered_out(self) -> None:
        # Skipped entries remain in the list so the report can show a cell as
        # deliberately-skipped rather than as missing data.
        runs = schedule.expand_schedule(self.schedule)
        self.assertEqual(len(runs), 2 * 2 * 2)
        self.assertTrue(any(r.skipped for r in runs))


class SkipRuleSelectorTests(unittest.TestCase):
    """An omitted selector means "all"; an explicit selector means "only
    these". Both halves matter -- the second skip rule in the committed file
    relies on omitting `skills`.
    """

    def test_omitted_selectors_match_everything(self) -> None:
        document = minimal_document()
        document["skips"] = [{"reason": "halt everything"}]
        runs = schedule.expand_schedule(parse(document))
        self.assertTrue(all(r.skipped for r in runs))

    def test_task_only_selector_skips_that_task_across_the_matrix(self) -> None:
        document = minimal_document()
        document["skips"] = [{"reason": "task is broken", "tasks": ["task-high"]}]
        runs = schedule.expand_schedule(parse(document))
        self.assertTrue(all(r.skipped for r in runs if r.task.name == "task-high"))
        self.assertFalse(any(r.skipped for r in runs if r.task.name == "task-low"))

    def test_first_matching_rule_supplies_the_reason(self) -> None:
        document = minimal_document()
        document["skips"] = [
            {"reason": "first rule", "tasks": ["task-low"]},
            {"reason": "second rule", "tasks": ["task-low"]},
        ]
        runs = schedule.expand_schedule(parse(document))
        planned = next(r for r in runs if r.task.name == "task-low")
        self.assertEqual(planned.skip_reason, "first rule")

    def test_empty_skip_list_means_nothing_is_skipped(self) -> None:
        document = minimal_document()
        document["skips"] = []
        runs = schedule.expand_schedule(parse(document))
        self.assertFalse(any(r.skipped for r in runs))


class ArmIdResolutionTests(unittest.TestCase):
    """A planned run must resolve to the same `Arm.id` string `run.py` would
    have produced, or Step 2 writes its trials into a directory nothing else
    reads.
    """

    def setUp(self) -> None:
        self.schedule = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)
        self.by_name = {model.name: model for model in self.schedule.models}

    def test_plugin_arm_id_is_skill_orchestrator_impl(self) -> None:
        self.assertEqual(
            schedule.arm_id_for(self.by_name["opus-sonnet"], "do-in-steps"),
            "do-in-steps__opus-sonnet",
        )
        self.assertEqual(
            schedule.arm_id_for(self.by_name["haiku"], "do-and-judge"),
            "do-and-judge__haiku-haiku",
        )

    def test_vanilla_arm_id_drops_the_impl_tier(self) -> None:
        self.assertEqual(schedule.arm_id_for(self.by_name["opus"], "vanilla"),
                         "vanilla__opus")

    def test_arm_ids_match_run_py_for_every_planned_run(self) -> None:
        for planned in schedule.expand_schedule(self.schedule):
            expected = run.Arm(
                skill=planned.arm_skill,
                orchestrator=planned.model.orchestrator,
                impl=planned.model.impl if not planned.is_vanilla else None,
            ).id
            self.assertEqual(planned.arm_id, expected)

    def test_vanilla_translates_to_run_pys_none_skill(self) -> None:
        planned = next(
            r for r in schedule.expand_schedule(self.schedule) if r.skill == "vanilla"
        )
        self.assertTrue(planned.is_vanilla)
        self.assertIsNone(planned.arm_skill)

    def test_plugin_skills_pass_through_untranslated(self) -> None:
        planned = next(
            r for r in schedule.expand_schedule(self.schedule)
            if r.skill == "do-and-judge"
        )
        self.assertFalse(planned.is_vanilla)
        self.assertEqual(planned.arm_skill, "do-and-judge")


class VanillaArmIdCollisionTests(unittest.TestCase):
    """Why a mixed pair has no vanilla arm of its own.

    `run.py`'s vanilla arms are keyed on the orchestrator tier alone
    (`vanilla__<orchestrator>`), because with no plugin there are no
    sub-agents for an impl tier to serve. The schedule's models are tier
    *pairs*, so `arm_id_for` maps `sonnet-haiku` and `sonnet` onto the same
    `vanilla__sonnet` -- not two arms that happen to share a name, but one
    arm reached by two labels.

    That is a property of `Arm.id` and it is unchanged; Step 2 still needs to
    know it when resolving ids. What changed is that the schedule no longer
    *schedules* both: `schedule.yaml` skips vanilla for the mixed pairs, so
    the id is never claimed twice by anything runnable.
    `RunnableRunUniquenessTests` is what enforces that; these tests explain
    what it is protecting against.
    """

    def test_mixed_and_symmetric_models_resolve_to_one_vanilla_arm(self) -> None:
        loaded = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)
        by_name = {model.name: model for model in loaded.models}
        self.assertEqual(
            schedule.arm_id_for(by_name["sonnet-haiku"], "vanilla"),
            schedule.arm_id_for(by_name["sonnet"], "vanilla"),
        )
        self.assertEqual(
            schedule.arm_id_for(by_name["opus-sonnet"], "vanilla"),
            schedule.arm_id_for(by_name["opus"], "vanilla"),
        )

    def test_no_such_convergence_for_plugin_skills(self) -> None:
        loaded = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)
        ids = [
            schedule.arm_id_for(model, "do-in-steps") for model in loaded.models
        ]
        self.assertEqual(len(set(ids)), len(ids))

    def test_the_schedule_never_makes_both_labels_runnable(self) -> None:
        # The resolution, stated where the hazard is explained: every model
        # the committed schedule actually runs at vanilla is a symmetric pair,
        # so no arm id is reachable by two runnable labels.
        loaded = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)
        runnable_vanilla_models = {
            planned.model
            for planned in schedule.expand_schedule(loaded)
            if planned.is_vanilla and not planned.skipped
        }
        for model in runnable_vanilla_models:
            self.assertEqual(model.orchestrator, model.impl, model.name)


class ComplexityTests(unittest.TestCase):
    """Step 4 plots complexity as an ordered axis, so the ordering is data,
    not presentation.
    """

    def setUp(self) -> None:
        self.schedule = schedule.load_schedule(schedule.DEFAULT_SCHEDULE_PATH)

    def test_levels_are_ordered_low_to_high(self) -> None:
        self.assertEqual(list(schedule.COMPLEXITY_LEVELS), ["low", "medium", "high"])

    def test_rank_is_strictly_increasing(self) -> None:
        self.assertLess(schedule.complexity_rank("low"), schedule.complexity_rank("medium"))
        self.assertLess(schedule.complexity_rank("medium"), schedule.complexity_rank("high"))

    def test_rank_rejects_an_unknown_level(self) -> None:
        with self.assertRaises(schedule.ScheduleError) as caught:
            schedule.complexity_rank("extreme")
        self.assertIn("extreme", str(caught.exception))

    def test_complexity_lookup_by_task_name(self) -> None:
        self.assertEqual(
            self.schedule.complexity_of("kombu-single-active-consumer-priority"), "high"
        )
        self.assertEqual(
            self.schedule.complexity_of("cattrs-partial-structuring-recovery"), "medium"
        )
        self.assertEqual(self.schedule.complexity_of("abs-stepped-slices"), "low")

    def test_complexity_lookup_rejects_an_unknown_task(self) -> None:
        with self.assertRaises(schedule.ScheduleError) as caught:
            self.schedule.complexity_of("no-such-task")
        message = str(caught.exception)
        self.assertIn("no-such-task", message)
        self.assertIn("abs-stepped-slices", message)  # names what IS declared


class DurationParsingTests(unittest.TestCase):
    """Durations are human-legible in the file and seconds in the code."""

    def test_hour_suffix(self) -> None:
        self.assertEqual(schedule.parse_duration("2h", where="d"), 7200)

    def test_minute_and_second_suffixes(self) -> None:
        self.assertEqual(schedule.parse_duration("30m", where="d"), 1800)
        self.assertEqual(schedule.parse_duration("45s", where="d"), 45)

    def test_bare_integer_is_seconds(self) -> None:
        self.assertEqual(schedule.parse_duration(7200, where="d"), 7200)

    def test_zero_is_allowed(self) -> None:
        self.assertEqual(schedule.parse_duration("0h", where="d"), 0)

    def test_rejects_unparseable_text(self) -> None:
        with self.assertRaises(schedule.ScheduleError) as caught:
            schedule.parse_duration("2 hours", where="duration.between_runs")
        message = str(caught.exception)
        self.assertIn("duration.between_runs", message)
        self.assertIn("2 hours", message)

    def test_rejects_an_unknown_unit(self) -> None:
        with self.assertRaises(schedule.ScheduleError):
            schedule.parse_duration("2w", where="d")

    def test_a_multi_letter_unit_reaches_the_unknown_unit_message(self) -> None:
        # "2hr" is the typo a human writes for "2h". The pattern accepts a
        # multi-character unit purely so this lands on the message that names
        # the unit rather than on the generic "cannot parse" one.
        with self.assertRaises(schedule.ScheduleError) as caught:
            schedule.parse_duration("2hr", where="duration.between_runs")
        message = str(caught.exception)
        self.assertIn("unknown duration unit", message)
        self.assertIn("'hr'", message)

    def test_days_are_not_an_accepted_unit(self) -> None:
        # The vocabulary is exactly s/m/h -- a pacing knob measured in days
        # is a mistake worth stopping, not a convenience worth supporting.
        with self.assertRaises(schedule.ScheduleError) as caught:
            schedule.parse_duration("1d", where="d")
        self.assertIn("unknown duration unit", str(caught.exception))

    def test_rejects_a_negative_duration(self) -> None:
        with self.assertRaises(schedule.ScheduleError):
            schedule.parse_duration(-1, where="d")

    def test_rejects_a_boolean(self) -> None:
        # `True` is an int subclass in Python; YAML's `yes` would otherwise
        # silently become a 1-second pause.
        with self.assertRaises(schedule.ScheduleError):
            schedule.parse_duration(True, where="d")


class ValidationTests(unittest.TestCase):
    """One test per documented failure mode. Each asserts the message names
    the offending field -- a bare "invalid schedule" is not actionable.
    """

    def assert_rejected(self, document: dict, *needles: str) -> str:
        with self.assertRaises(schedule.ScheduleError) as caught:
            parse(document)
        message = str(caught.exception)
        for needle in needles:
            self.assertIn(needle, message)
        return message

    def test_the_minimal_document_is_actually_valid(self) -> None:
        parse(minimal_document())  # guards every other test in this class

    def test_rejects_a_non_mapping_document(self) -> None:
        with self.assertRaises(schedule.ScheduleError):
            schedule.parse_schedule(["not", "a", "mapping"], source="test-schedule")

    def test_rejects_a_missing_section(self) -> None:
        for section in (
            "models",
            "skills",
            "tasks",
            "duration",
            "skips",
        ):
            document = minimal_document()
            del document[section]
            self.assert_rejected(document, section)

    def test_rejects_an_unknown_top_level_key(self) -> None:
        document = minimal_document()
        document["skip"] = []  # the plausible typo for `skips`
        self.assert_rejected(document, "skip")

    def test_rejects_an_empty_models_section(self) -> None:
        document = minimal_document()
        document["models"] = []
        self.assert_rejected(document, "models")

    def test_rejects_an_empty_tasks_section(self) -> None:
        document = minimal_document()
        document["tasks"] = []
        self.assert_rejected(document, "tasks")

    def test_rejects_an_empty_skills_section(self) -> None:
        document = minimal_document()
        document["skills"] = []
        self.assert_rejected(document, "skills")

    def test_rejects_a_duplicate_model_name(self) -> None:
        document = minimal_document()
        document["models"].append(
            {"name": "haiku", "orchestrator": "haiku", "impl": "haiku"}
        )
        self.assert_rejected(document, "duplicate", "haiku")

    def test_rejects_a_duplicate_task_name(self) -> None:
        document = minimal_document()
        document["tasks"].append({"name": "task-low", "complexity": "low"})
        self.assert_rejected(document, "duplicate", "task-low")

    def test_rejects_a_duplicate_skill(self) -> None:
        document = minimal_document()
        document["skills"].append("vanilla")
        self.assert_rejected(document, "duplicate", "vanilla")

    def test_rejects_an_unknown_skill(self) -> None:
        document = minimal_document()
        document["skills"] = ["vanilla", "do-everything"]
        self.assert_rejected(document, "do-everything", "do-in-steps")

    def test_rejects_a_tier_pair_that_is_not_a_cell(self) -> None:
        document = minimal_document()
        # haiku orchestrating opus is not one of run.py's CELLS.
        document["models"][0] = {
            "name": "haiku-opus", "orchestrator": "haiku", "impl": "opus"
        }
        self.assert_rejected(document, "haiku-opus", "CELLS")

    def test_rejects_an_unknown_orchestrator_tier(self) -> None:
        document = minimal_document()
        document["models"][0]["orchestrator"] = "gpt"
        self.assert_rejected(document, "gpt")

    def test_rejects_an_unknown_complexity_label(self) -> None:
        document = minimal_document()
        document["tasks"][0]["complexity"] = "extreme"
        self.assert_rejected(document, "extreme", "low")

    def test_rejects_a_model_entry_missing_impl(self) -> None:
        document = minimal_document()
        del document["models"][0]["impl"]
        self.assert_rejected(document, "impl")

    def test_rejects_an_unknown_key_in_a_model_entry(self) -> None:
        document = minimal_document()
        document["models"][0]["implementation"] = "haiku"
        self.assert_rejected(document, "implementation")

    def test_rejects_an_unknown_key_in_a_task_entry(self) -> None:
        document = minimal_document()
        document["tasks"][0]["difficulty"] = "low"
        self.assert_rejected(document, "difficulty")

    def test_rejects_a_missing_duration_key(self) -> None:
        document = minimal_document()
        del document["duration"]["technical_failure_backoff"]
        self.assert_rejected(document, "technical_failure_backoff")

    def test_rejects_an_unknown_duration_key(self) -> None:
        document = minimal_document()
        document["duration"]["between_run"] = "1h"  # singular typo
        self.assert_rejected(document, "between_run")

    def test_rejects_an_unparseable_duration(self) -> None:
        document = minimal_document()
        document["duration"]["between_runs"] = "two hours"
        self.assert_rejected(document, "between_runs", "two hours")

    def test_rejects_a_skip_rule_without_a_reason(self) -> None:
        document = minimal_document()
        del document["skips"][0]["reason"]
        self.assert_rejected(document, "reason")

    def test_rejects_a_blank_skip_reason(self) -> None:
        document = minimal_document()
        document["skips"][0]["reason"] = "   "
        self.assert_rejected(document, "reason")

    def test_rejects_a_skip_rule_naming_an_unknown_model(self) -> None:
        document = minimal_document()
        document["skips"][0]["models"] = ["gpt"]
        self.assert_rejected(document, "gpt")

    def test_rejects_a_skip_rule_naming_an_unknown_task(self) -> None:
        document = minimal_document()
        document["skips"][0]["tasks"] = ["task-medium"]
        self.assert_rejected(document, "task-medium")

    def test_rejects_a_skip_rule_naming_an_undeclared_skill(self) -> None:
        document = minimal_document()
        # `do-in-steps` is a KNOWN skill but this document does not declare it.
        document["skips"][0]["skills"] = ["do-in-steps"]
        self.assert_rejected(document, "do-in-steps")

    def test_rejects_an_unknown_key_in_a_skip_rule(self) -> None:
        document = minimal_document()
        # The singular typo is the dangerous one: it would otherwise be read
        # as "no model selector", i.e. skip on EVERY model.
        document["skips"][0]["model"] = ["haiku"]
        self.assert_rejected(document, "model")

    def test_rejects_an_empty_selector_list_in_a_skip_rule(self) -> None:
        document = minimal_document()
        document["skips"][0]["models"] = []
        self.assert_rejected(document, "models")

    def test_error_messages_name_the_source(self) -> None:
        document = minimal_document()
        del document["models"]
        self.assert_rejected(document, "test-schedule")


class LoadingTests(unittest.TestCase):
    """`load_schedule` is the only impure edge -- it reads one file."""

    def write(self, text: str) -> Path:
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        handle.write(text)
        handle.close()
        path = Path(handle.name)
        self.addCleanup(path.unlink)
        return path

    def test_rejects_malformed_yaml(self) -> None:
        path = self.write("models: [\n  unclosed")
        with self.assertRaises(schedule.ScheduleError) as caught:
            schedule.load_schedule(path)
        self.assertIn(str(path), str(caught.exception))

    def test_rejects_an_empty_file(self) -> None:
        path = self.write("")
        with self.assertRaises(schedule.ScheduleError):
            schedule.load_schedule(path)

    def test_rejects_a_missing_file(self) -> None:
        with self.assertRaises(schedule.ScheduleError) as caught:
            schedule.load_schedule(Path("/nonexistent/schedule.yaml"))
        self.assertIn("/nonexistent/schedule.yaml", str(caught.exception))

    def test_the_error_type_is_catchable_as_value_error(self) -> None:
        # Callers in Steps 2-4 should be able to `except ValueError` without
        # importing this module's exception type.
        self.assertTrue(issubclass(schedule.ScheduleError, ValueError))


class PurityTests(unittest.TestCase):
    """`schedule.py` is a configuration layer, not an execution layer. Step 2
    owns sleeping and subprocesses; if they leak in here, the module stops
    being unit-testable.

    Stated as an allowlist over the module's actual import graph rather than
    as a blocklist of spellings: a denylist of source substrings passes
    happily against `from subprocess import run`, `import time as t`, or
    `os.system`, which is to say it pins a spelling and not the guarantee.
    """

    ALLOWED_IMPORTS = frozenset({"re", "dataclasses", "pathlib", "yaml", "__future__"})

    def imported_module_names(self) -> set[str]:
        """Every top-level module `schedule.py` imports, however spelled.

        Both `import x.y` and `from x.y import z` are reduced to `x`, so an
        indirect route to a forbidden module is caught the same as a direct
        one.
        """
        tree = ast.parse(Path(schedule.__file__).read_text(encoding="utf-8"))
        names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])

        return names

    def test_imports_nothing_outside_the_allowlist(self) -> None:
        unexpected = self.imported_module_names() - self.ALLOWED_IMPORTS
        self.assertEqual(
            unexpected,
            set(),
            f"schedule.py must not import {sorted(unexpected)}; it is a pure "
            f"configuration layer and Step 2 owns execution",
        )

    def test_the_allowlist_is_not_vacuous(self) -> None:
        # A walk that found nothing would pass the test above for the wrong
        # reason, so pin that it actually sees the imports that are there.
        self.assertEqual(self.imported_module_names(), self.ALLOWED_IMPORTS)


if __name__ == "__main__":
    unittest.main()
