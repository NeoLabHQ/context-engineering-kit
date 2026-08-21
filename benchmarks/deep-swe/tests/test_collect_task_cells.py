#!/usr/bin/env python3
"""Unit tests for collect.py's per-(task, model, skill) cell aggregation.

WHAT THESE TESTS GUARD
-----------------------
The per-arm aggregate answers "how did `do-in-steps__sonnet-sonnet` do?". The
per-cell aggregate answers the question the report is actually for: "can THIS
model do THIS task under THIS skill?" -- and the honest answer is very often
"we do not know", for four categorically different reasons.

The load-bearing property below is that those four reasons never collapse
into each other, and never collapse into `0.0`. A chart that draws a zero bar
where the truth is "haiku was never asked" is not a rendering bug, it is a
false claim about a model's capability, and it is the exact claim the whole
absence vocabulary exists to prevent. So `NoZeroCoercionTests` walks every
cell the committed schedule produces and asserts there is no numeric field a
renderer could mistake for a pass rate.

The tests deliberately load the REAL `schedule.yaml` rather than a fixture:
complexity labels and skip reasons are supposed to come from that file and
nowhere else, so a test that supplied its own would pass even if collect.py
hardcoded the labels it was checking.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from typing import get_args

import collect  # sys.path patched by tests/__init__.py
import schedule

from .collect_fixtures import make_trial

# The committed schedule, loaded once: every test below reads its complexity
# labels and skip reasons from here rather than restating them.
SCHEDULE = schedule.load_schedule()

# Cells this suite reaches for by name. Spelled out so a schedule edit that
# renames a task fails these tests loudly instead of silently testing nothing.
LOW_TASK = "abs-stepped-slices"
MEDIUM_TASK = "cattrs-partial-structuring-recovery"
HIGH_TASK = "kombu-single-active-consumer-priority"


def cell_index(cells: list[collect.TaskCellAggregate]) -> dict[tuple[str, str, str], collect.TaskCellAggregate]:
    """Cells keyed by their (task, model, skill) identity, for lookup by name."""
    return {(cell.task, cell.model, cell.skill): cell for cell in cells}


def build(trials: list[collect.TrialRecord] | None = None, **kwargs) -> list[collect.TaskCellAggregate]:
    """`build_task_cells` against the committed schedule, with no trials by default."""
    return collect.build_task_cells(SCHEDULE, trials or [], **kwargs)


class TaskNameReconciliationTests(unittest.TestCase):
    """The three spellings of one task name, and how they are reconciled.

    pier records `task_name` as `datacurve/cattrs-partial-structuring-recovery`
    but names the trial DIRECTORY `cattrs-partial-structuring-recov__ZsbwRdJ`.
    `schedule.yaml` uses the plain, untruncated name. Nothing may assume the
    three match.
    """

    def test_the_pier_namespace_is_stripped_from_a_recorded_task_name(self) -> None:
        self.assertEqual(
            collect.strip_task_namespace("datacurve/cattrs-partial-structuring-recovery"),
            "cattrs-partial-structuring-recovery",
        )
        # A name with no namespace at all is already in schedule vocabulary.
        self.assertEqual(collect.strip_task_namespace("abs-stepped-slices"), "abs-stepped-slices")

    def test_the_trial_directory_suffix_is_stripped_to_a_task_slug(self) -> None:
        self.assertEqual(
            collect.task_slug_from_trial_id("cattrs-partial-structuring-recov__ZsbwRdJ"),
            "cattrs-partial-structuring-recov",
        )
        # A task name containing hyphens must survive; only the `__` suffix goes.
        self.assertEqual(
            collect.task_slug_from_trial_id("abs-stepped-slices__HyQJyYy"), "abs-stepped-slices"
        )

    def test_a_truncated_slug_resolves_to_the_full_scheduled_name(self) -> None:
        known = [task.name for task in SCHEDULE.tasks]
        self.assertEqual(
            collect.resolve_scheduled_task_name("cattrs-partial-structuring-recov", known),
            MEDIUM_TASK,
        )

    def test_an_ambiguous_prefix_resolves_to_nothing_rather_than_guessing(self) -> None:
        # Two scheduled tasks share this prefix, so no single answer is correct
        # and returning either one would silently attribute trials to the wrong task.
        self.assertIsNone(collect.resolve_scheduled_task_name("task", ["task-a", "task-b"]))

    def test_an_unknown_task_resolves_to_nothing_rather_than_the_nearest_match(self) -> None:
        known = [task.name for task in SCHEDULE.tasks]
        self.assertIsNone(collect.resolve_scheduled_task_name("bandit-incremental-cache-control", known))

    def test_a_trial_resolves_through_its_task_name_not_its_truncated_directory(self) -> None:
        trial = make_trial(
            "resolved",
            task_name="datacurve/cattrs-partial-structuring-recovery",
            trial_id="cattrs-partial-structuring-recov__ZsbwRdJ",
        )
        name, method = collect.resolve_trial_task_name(trial, [task.name for task in SCHEDULE.tasks])
        self.assertEqual(name, MEDIUM_TASK)
        self.assertEqual(method, "task_name")

    def test_a_trial_with_no_recorded_task_name_falls_back_to_its_directory(self) -> None:
        # An `errored` record built from a malformed result.json has task_name=None;
        # the truncated directory name is then the only evidence left.
        trial = make_trial(
            "errored", task_name=None, trial_id="cattrs-partial-structuring-recov__ZsbwRdJ"
        )
        name, method = collect.resolve_trial_task_name(trial, [task.name for task in SCHEDULE.tasks])
        self.assertEqual(name, MEDIUM_TASK)
        self.assertEqual(method, "trial_id_prefix")


class CellShapeTests(unittest.TestCase):
    """The matrix the committed schedule expands to, and each cell's identity."""

    def test_every_scheduled_combination_gets_exactly_one_cell(self) -> None:
        cells = build()
        expected = len(SCHEDULE.tasks) * len(SCHEDULE.models) * len(SCHEDULE.skills)
        self.assertEqual(len(cells), expected)  # 3 tasks x 5 models x 3 skills = 45
        self.assertEqual(len(cell_index(cells)), expected)  # all identities distinct

    def test_complexity_is_read_from_the_schedule_for_every_cell(self) -> None:
        for cell in build():
            with self.subTest(cell=(cell.task, cell.model, cell.skill)):
                self.assertEqual(cell.complexity, SCHEDULE.complexity_of(cell.task))
                self.assertEqual(cell.complexity_rank, schedule.complexity_rank(cell.complexity))

    def test_the_three_complexity_bands_are_all_represented(self) -> None:
        # Guards against a rank/label mix-up collapsing the chart axis the whole
        # sweep exists to plot against.
        by_task = {cell.task: (cell.complexity, cell.complexity_rank) for cell in build()}
        self.assertEqual(by_task[LOW_TASK], ("low", 0))
        self.assertEqual(by_task[MEDIUM_TASK], ("medium", 1))
        self.assertEqual(by_task[HIGH_TASK], ("high", 2))

    def test_each_cell_carries_the_arm_id_its_trials_would_land_under(self) -> None:
        cells = cell_index(build())
        self.assertEqual(cells[(LOW_TASK, "sonnet-haiku", "do-in-steps")].arm_id, "do-in-steps__sonnet-haiku")
        self.assertEqual(cells[(LOW_TASK, "opus", "vanilla")].arm_id, "vanilla__opus")


class MeasuredCellTests(unittest.TestCase):
    """A cell that actually has data: what it reports and where it reports it."""

    def sonnet_do_in_steps_trials(self) -> list[collect.TrialRecord]:
        """Two attempts and one infra failure on the medium task."""
        return [
            make_trial(
                "resolved",
                arm_id="do-in-steps__sonnet-sonnet",
                skill="do-in-steps",
                orchestrator="sonnet",
                impl="sonnet",
                task_name="datacurve/cattrs-partial-structuring-recovery",
                cost_usd=10.0,
                output_tokens=100,
                input_tokens=1000,
                cache_tokens=900,
                n_agent_steps=20,
                trial_id="cattrs-partial-structuring-recov__aaa",
            ),
            make_trial(
                "unresolved",
                arm_id="do-in-steps__sonnet-sonnet",
                skill="do-in-steps",
                orchestrator="sonnet",
                impl="sonnet",
                task_name="datacurve/cattrs-partial-structuring-recovery",
                cost_usd=30.0,
                output_tokens=300,
                input_tokens=3000,
                cache_tokens=1100,
                n_agent_steps=40,
                trial_id="cattrs-partial-structuring-recov__bbb",
            ),
            make_trial(
                "errored",
                arm_id="do-in-steps__sonnet-sonnet",
                skill="do-in-steps",
                orchestrator="sonnet",
                impl="sonnet",
                task_name="datacurve/cattrs-partial-structuring-recovery",
                cost_usd=999.0,  # contaminated: must not reach any average
                output_tokens=999,
                trial_id="cattrs-partial-structuring-recov__ccc",
            ),
        ]

    def measured_cell(self) -> collect.TaskCellAggregate:
        cells = cell_index(build(self.sonnet_do_in_steps_trials()))
        return cells[(MEDIUM_TASK, "sonnet", "do-in-steps")]

    def test_a_cell_with_attempts_is_measured_and_has_no_absence(self) -> None:
        cell = self.measured_cell()
        self.assertEqual(cell.state, "measured")
        self.assertIsNone(cell.absence)
        self.assertIsNotNone(cell.measured)

    def test_pass_at_1_uses_the_same_denominator_the_arm_table_does(self) -> None:
        cell = self.measured_cell()
        # 1 resolved + 1 unresolved attempted; the errored trial is excluded.
        self.assertEqual(cell.measured.n_attempts, 2)
        self.assertEqual(cell.measured.pass_at_1, 0.5)
        self.assertEqual(cell.n_trials_seen, 3)
        self.assertEqual(cell.n_errored_trials, 1)

    def test_the_interval_names_its_own_statistic_and_denominator(self) -> None:
        # Without these two strings a renderer cannot tell this interval apart
        # from DeepSWE's run-to-run SE, and co-plotting them is a false claim.
        cell = self.measured_cell()
        self.assertEqual(cell.measured.pass_at_1_interval_type, collect.LOCAL_PASS_AT_1_INTERVAL_TYPE)
        self.assertEqual(
            cell.measured.pass_at_1_denominator_unit, collect.LOCAL_PASS_AT_1_DENOMINATOR_UNIT
        )
        low, high = collect.wilson_score_interval(1, 2)
        self.assertEqual((cell.measured.pass_at_1_ci_low, cell.measured.pass_at_1_ci_high), (low, high))

    def test_cost_and_token_rollups_exclude_errored_trials(self) -> None:
        measured = self.measured_cell().measured
        # Attempts are $10 and $30 -- the $999 errored trial is contaminated
        # by whatever infra fault occurred and never reaches these figures.
        self.assertEqual(measured.total_cost_usd, 40.0)
        self.assertEqual(measured.avg_cost_usd, 20.0)
        self.assertEqual(measured.max_cost_usd, 30.0)
        self.assertEqual(measured.total_output_tokens, 400)
        self.assertEqual(measured.avg_output_tokens, 200.0)
        self.assertEqual(measured.total_input_tokens, 4000)
        self.assertEqual(measured.avg_input_tokens, 2000.0)
        self.assertEqual(measured.total_cache_tokens, 2000)
        self.assertEqual(measured.avg_n_agent_steps, 30.0)

    def test_missing_cost_figures_stay_null_rather_than_summing_to_zero(self) -> None:
        trials = [
            make_trial(
                "unresolved",
                arm_id="do-in-steps__opus-opus",
                skill="do-in-steps",
                orchestrator="opus",
                impl="opus",
                task_name="datacurve/abs-stepped-slices",
                trial_id="abs-stepped-slices__zzz",
            )
        ]
        measured = cell_index(build(trials))[(LOW_TASK, "opus", "do-in-steps")].measured
        self.assertIsNone(measured.total_cost_usd)  # not 0.0 -- nothing was recorded
        self.assertIsNone(measured.avg_cost_usd)
        self.assertIsNone(measured.total_output_tokens)

    def test_the_cell_lists_the_trials_it_aggregated(self) -> None:
        cell = self.measured_cell()
        self.assertEqual(
            cell.trial_ids,
            (
                "cattrs-partial-structuring-recov__aaa",
                "cattrs-partial-structuring-recov__bbb",
                "cattrs-partial-structuring-recov__ccc",
            ),
        )

    def test_a_genuine_zero_pass_rate_is_measured_not_absent(self) -> None:
        # The distinction the whole absence vocabulary exists for: this arm
        # tried and scored nothing, which is a real, defensible 0.0.
        trials = [
            make_trial(
                "unresolved",
                arm_id="do-and-judge__haiku-haiku",
                skill="do-and-judge",
                orchestrator="haiku",
                impl="haiku",
                task_name="datacurve/abs-stepped-slices",
                trial_id="abs-stepped-slices__q",
            )
        ]
        cell = cell_index(build(trials))[(LOW_TASK, "haiku", "do-and-judge")]
        self.assertEqual(cell.state, "measured")
        self.assertEqual(cell.measured.pass_at_1, 0.0)


class SingleTrialIntervalTests(unittest.TestCase):
    """A one-attempt cell must not carry an interval shaped like a pooled one.

    `schedule.yaml` plans exactly ONE trial per (task, model, skill), so this
    is the shape of very nearly every cell a renderer will ever meet. A Wilson
    interval over n=1 is arithmetically defined -- (0.207, 1.0) for a single
    success -- but it spans 79 percentage points and, decisively, it lands in
    the SAME field names `ArmAggregate` uses for a genuine interval pooled
    over many trials. A chart reading `pass_at_1_ci_low`/`_high` cannot tell
    the two apart, so it would draw one coin flip as a measured error bar.

    collect.py already refuses to let an incomparable interval occupy the
    local field names on the Fable 5 side -- `_baseline_rate` hardcodes
    `comparable_to_local_wilson_interval: False` -- and the same rule has to
    hold locally. So a single-attempt cell carries no bounds at all, plus an
    explicit `is_single_trial` flag, which is what lets a renderer draw a 0/1
    outcome as the outcome it is rather than as a rate with error bars.
    """

    def cell_with(self, *statuses: str) -> collect.CellMeasurement:
        """A measured `(abs-stepped-slices, opus, do-in-steps)` cell with one
        attempt per status given -- the only axis these tests vary."""
        trials = [
            make_trial(
                status,
                arm_id="do-in-steps__opus-opus",
                skill="do-in-steps",
                orchestrator="opus",
                impl="opus",
                task_name="datacurve/abs-stepped-slices",
                trial_id=f"abs-stepped-slices__n{index}",
            )
            for index, status in enumerate(statuses)
        ]
        return cell_index(build(trials))[(LOW_TASK, "opus", "do-in-steps")].measured

    def test_a_single_attempt_cell_carries_no_interval_at_all(self) -> None:
        measured = self.cell_with("resolved")
        self.assertTrue(measured.is_single_trial)
        self.assertIsNone(measured.pass_at_1_ci_low)
        self.assertIsNone(measured.pass_at_1_ci_high)

    def test_the_single_attempt_bounds_are_not_the_n_equals_1_wilson_interval(self) -> None:
        # The specific regression: `wilson_score_interval(1, 1)` is a real pair
        # of floats, and putting it in these fields is indistinguishable from a
        # pooled arm's interval. Naming the value here means a future edit that
        # reinstates it fails on the number itself, not on a vague `is None`.
        measured = self.cell_with("resolved")
        self.assertEqual(collect.wilson_score_interval(1, 1), (0.20654931437723745, 1.0))
        self.assertNotEqual(
            (measured.pass_at_1_ci_low, measured.pass_at_1_ci_high),
            collect.wilson_score_interval(1, 1),
        )

    def test_dropping_the_interval_keeps_every_integer_count_intact(self) -> None:
        # The counts are the honest record of a single trial and are exactly
        # what a renderer needs to draw "1 of 1 resolved" instead of "100%".
        measured = self.cell_with("resolved")
        self.assertEqual(
            (measured.n_resolved, measured.n_unresolved, measured.n_incomplete, measured.n_attempts),
            (1, 0, 0, 1),
        )
        self.assertEqual(measured.pass_at_1, 1.0)

    def test_a_multi_attempt_cell_still_carries_its_wilson_interval(self) -> None:
        # Pooling really does happen once a cell has more than one attempt, and
        # nothing above may suppress it: this is the case the interval is for.
        measured = self.cell_with("resolved", "unresolved")
        self.assertFalse(measured.is_single_trial)
        self.assertEqual(
            (measured.pass_at_1_ci_low, measured.pass_at_1_ci_high),
            collect.wilson_score_interval(1, 2),
        )
        self.assertIsInstance(measured.pass_at_1_ci_low, float)
        self.assertIsInstance(measured.pass_at_1_ci_high, float)

    def test_the_flag_and_the_bounds_can_never_disagree(self) -> None:
        # One derived fact stated twice is a drift hazard, so assert the two
        # agree at every arity a cell can actually reach.
        arities = (
            ("resolved",),
            ("unresolved",),
            ("resolved", "unresolved"),
            ("resolved", "incomplete", "unresolved"),
        )
        for statuses in arities:
            with self.subTest(n_attempts=len(statuses)):
                measured = self.cell_with(*statuses)
                self.assertEqual(measured.is_single_trial, measured.n_attempts < 2)
                has_bounds = measured.pass_at_1_ci_low is not None
                self.assertEqual(has_bounds, not measured.is_single_trial)
                # `_high` is never set without `_low`; an interval is a pair.
                self.assertEqual(has_bounds, measured.pass_at_1_ci_high is not None)


class DeliberateSkipTests(unittest.TestCase):
    """Cells `schedule.yaml` says not to run, and the reason it gives."""

    def test_haiku_at_vanilla_is_skipped_with_the_schedules_own_words(self) -> None:
        cell = cell_index(build())[(HIGH_TASK, "haiku", "vanilla")]
        self.assertEqual(cell.state, "deliberately_skipped")
        self.assertIsNone(cell.measured)
        self.assertIn("Too complex for haiku at the vanilla level", cell.absence.reason)
        self.assertEqual(cell.absence.source, "schedule.yaml")
        # The same text is also readable without going through `absence`, so a
        # measured-but-since-skipped cell never loses it.
        self.assertEqual(cell.schedule_skip_reason, cell.absence.reason)

    def test_sonnet_on_the_high_task_is_skipped_under_every_skill(self) -> None:
        cells = cell_index(build())
        for skill in SCHEDULE.skills:
            with self.subTest(skill=skill):
                cell = cells[(HIGH_TASK, "sonnet", skill)]
                self.assertEqual(cell.state, "deliberately_skipped")
                self.assertIn("Too complex for sonnet", cell.absence.reason)

    def test_a_skip_reason_is_recorded_even_when_the_cell_was_measured(self) -> None:
        # Evidence beats declaration for `state` -- but the declaration must
        # still be visible, or the report would silently drop the operator's
        # stated intent for a cell that was run anyway.
        trials = [
            make_trial(
                "resolved",
                arm_id="do-in-steps__sonnet-sonnet",
                skill="do-in-steps",
                orchestrator="sonnet",
                impl="sonnet",
                task_name="datacurve/kombu-single-active-consumer-priority",
                trial_id="kombu-single-active-consumer-pri__x",
            )
        ]
        cell = cell_index(build(trials))[(HIGH_TASK, "sonnet", "do-in-steps")]
        self.assertEqual(cell.state, "measured")
        self.assertIsNone(cell.absence)
        self.assertIn("Too complex for sonnet", cell.schedule_skip_reason)


class StructuralImpossibilityTests(unittest.TestCase):
    """The mixed-tier vanilla cells, which are not skipped so much as absent.

    A vanilla arm has no implementer tier, so `sonnet-haiku` + vanilla IS
    `sonnet` + vanilla -- the same arm id, the same job directory, the same
    pier invocation. There is no measurement to be had, ever, at any budget.
    """

    def test_all_six_mixed_tier_vanilla_cells_are_structurally_impossible(self) -> None:
        impossible = [cell for cell in build() if cell.state == "structurally_impossible"]
        # 2 mixed model pairs x 3 tasks.
        self.assertEqual(len(impossible), 6)
        self.assertEqual({cell.skill for cell in impossible}, {"vanilla"})
        self.assertEqual({cell.model for cell in impossible}, {"sonnet-haiku", "opus-sonnet"})

    def test_the_state_is_derived_from_the_arm_id_collapse_not_the_reason_prose(self) -> None:
        cell = cell_index(build())[(LOW_TASK, "sonnet-haiku", "vanilla")]
        self.assertEqual(cell.state, "structurally_impossible")
        self.assertEqual(cell.absence.collapses_onto_model, "sonnet")
        self.assertEqual(cell.arm_id, "vanilla__sonnet")
        self.assertIn("arm_id", cell.absence.source)

    def test_the_schedules_own_reason_survives_alongside_the_derived_state(self) -> None:
        cell = cell_index(build())[(LOW_TASK, "opus-sonnet", "vanilla")]
        self.assertIn("A vanilla arm has no implementer tier", cell.absence.reason)
        self.assertIn("A vanilla arm has no implementer tier", cell.schedule_skip_reason)

    def test_a_structurally_impossible_cell_never_claims_the_symmetric_cells_trials(self) -> None:
        # The hazard this guards: `sonnet-haiku`+vanilla and `sonnet`+vanilla
        # resolve to the SAME arm id, so a naive (task, arm_id) lookup would
        # attribute one measurement to two cells and double-count it.
        trials = [
            make_trial(
                "resolved",
                arm_id="vanilla__sonnet",
                skill=None,
                orchestrator="sonnet",
                impl=None,
                task_name="datacurve/abs-stepped-slices",
                trial_id="abs-stepped-slices__v",
            )
        ]
        cells = cell_index(build(trials))
        mixed = cells[(LOW_TASK, "sonnet-haiku", "vanilla")]
        symmetric = cells[(LOW_TASK, "sonnet", "vanilla")]

        self.assertEqual(mixed.state, "structurally_impossible")
        self.assertEqual(mixed.n_trials_seen, 0)
        self.assertEqual(mixed.trial_ids, ())
        self.assertEqual(symmetric.state, "measured")
        self.assertEqual(symmetric.measured.n_attempts, 1)


class TechnicalFailureTests(unittest.TestCase):
    """Cells that were attempted but never fairly attempted."""

    def state_file(self, entries: dict[str, dict]) -> dict[str, dict]:
        return entries

    def test_a_scheduler_technical_failure_is_its_own_absence_state(self) -> None:
        state = {
            "abs-stepped-slices::opus::do-in-steps": {
                "arm_id": "do-in-steps__opus-opus",
                "outcome": "technical_failure",
                "reason": "api_fault:rate_limit",
                "attempts": 3,
                "recorded_at": "2026-08-20T00:00:00+00:00",
            }
        }
        cell = cell_index(build(scheduler_state=state))[(LOW_TASK, "opus", "do-in-steps")]
        self.assertEqual(cell.state, "technical_failure")
        self.assertIsNone(cell.measured)
        self.assertEqual(cell.absence.source, "runs/scheduler-state.json")
        self.assertIn("api_fault:rate_limit", cell.absence.reason)
        self.assertEqual(cell.scheduler_outcome, "technical_failure")
        self.assertEqual(cell.scheduler_attempts, 3)

    def test_a_scheduler_model_failure_is_not_a_technical_failure(self) -> None:
        # A model failure means the agent got a fair shot and lost. If its
        # trial output is missing anyway, the honest label is "no data" -- with
        # the scheduler's own record left visible so the gap is inspectable.
        state = {
            "abs-stepped-slices::opus::do-in-steps": {
                "arm_id": "do-in-steps__opus-opus",
                "outcome": "model_failure",
                "reason": "no_model_patch",
                "attempts": 1,
                "recorded_at": "2026-08-20T00:00:00+00:00",
            }
        }
        cell = cell_index(build(scheduler_state=state))[(LOW_TASK, "opus", "do-in-steps")]
        self.assertEqual(cell.state, "not_yet_run")
        self.assertEqual(cell.scheduler_outcome, "model_failure")
        self.assertIn("model_failure", cell.absence.reason)

    def test_a_cell_whose_every_trial_errored_is_a_technical_failure(self) -> None:
        trials = [
            make_trial(
                "errored",
                arm_id="do-in-steps__opus-opus",
                skill="do-in-steps",
                orchestrator="opus",
                impl="opus",
                task_name="datacurve/abs-stepped-slices",
                trial_id="abs-stepped-slices__e1",
            )
        ]
        cell = cell_index(build(trials))[(LOW_TASK, "opus", "do-in-steps")]
        self.assertEqual(cell.state, "technical_failure")
        self.assertIsNone(cell.measured)  # n_attempts would be 0; no rate exists
        self.assertEqual(cell.n_errored_trials, 1)
        self.assertEqual(cell.absence.source, "trial_records")

    def test_the_state_key_matches_the_schedulers_own_vocabulary(self) -> None:
        # collect.py cannot import scheduler.py (triage.py already imports
        # collect.py, so it would be circular), so the key format is mirrored.
        # This pins the mirror against the real thing.
        import scheduler

        planned = schedule.expand_schedule(SCHEDULE)[0]
        self.assertEqual(
            collect.scheduler_state_key(planned.task.name, planned.model.name, planned.skill),
            scheduler.run_key(planned),
        )

    def test_the_mirrored_state_filename_matches_the_schedulers(self) -> None:
        import scheduler

        self.assertEqual(collect.SCHEDULER_STATE_FILENAME, scheduler.STATE_FILENAME)
        self.assertEqual(collect.SCHEDULER_STATE_VERSION, scheduler.STATE_VERSION)


class NotYetRunTests(unittest.TestCase):
    """The plainest absence: nobody has run this cell."""

    def test_an_unrun_cell_reports_no_data_and_no_numbers(self) -> None:
        cell = cell_index(build())[(LOW_TASK, "opus", "do-in-steps")]
        self.assertEqual(cell.state, "not_yet_run")
        self.assertIsNone(cell.measured)
        self.assertEqual(cell.n_trials_seen, 0)
        self.assertEqual(cell.absence.source, "no_data")
        self.assertIsNone(cell.scheduler_outcome)


class NoZeroCoercionTests(unittest.TestCase):
    """The requirement the whole schema exists to satisfy.

    None of the four absence states may be readable as "attempted and scored
    zero", and none may be readable as a bare missing key either. The schema
    enforces this by construction: every number lives inside `measured`, which
    is `None` for every absent cell -- so a renderer reaching for a rate on an
    absent cell raises `TypeError` instead of quietly drawing a zero bar.
    """

    def all_four_absence_states(self) -> dict[str, collect.TaskCellAggregate]:
        trials = [
            make_trial(
                "errored",
                arm_id="do-in-steps__opus-opus",
                skill="do-in-steps",
                orchestrator="opus",
                impl="opus",
                task_name="datacurve/abs-stepped-slices",
                trial_id="abs-stepped-slices__e1",
            )
        ]
        state = {
            "cattrs-partial-structuring-recovery::opus::do-in-steps": {
                "arm_id": "do-in-steps__opus-opus",
                "outcome": "technical_failure",
                "reason": "api_fault:overloaded",
                "attempts": 3,
                "recorded_at": "2026-08-20T00:00:00+00:00",
            }
        }
        cells = cell_index(build(trials, scheduler_state=state))
        by_state = {
            "deliberately_skipped": cells[(HIGH_TASK, "haiku", "vanilla")],
            "structurally_impossible": cells[(LOW_TASK, "sonnet-haiku", "vanilla")],
            "technical_failure": cells[(LOW_TASK, "opus", "do-in-steps")],
            "not_yet_run": cells[(LOW_TASK, "opus", "do-and-judge")],
        }
        for expected, cell in by_state.items():
            self.assertEqual(cell.state, expected)
        return by_state

    def test_the_four_absence_states_are_all_reachable_and_distinct(self) -> None:
        by_state = self.all_four_absence_states()
        self.assertEqual(len(by_state), 4)
        self.assertEqual(len({cell.state for cell in by_state.values()}), 4)
        # And the vocabulary is closed: every state collect can emit is documented.
        self.assertEqual(set(get_args(collect.CellState)), set(collect.CELL_STATE_DESCRIPTIONS))

    def test_no_absent_cell_exposes_any_number_a_renderer_could_plot(self) -> None:
        for state, cell in self.all_four_absence_states().items():
            with self.subTest(state=state):
                self.assertIsNone(cell.measured)
                self.assertIsNotNone(cell.absence)
                # A renderer that forgets to branch on `state` gets an
                # exception, never a zero.
                with self.assertRaises(TypeError):
                    asdict(cell)["measured"]["pass_at_1"]

    def test_every_absent_cell_states_a_reason_and_where_it_came_from(self) -> None:
        for cell in build():
            if cell.state == "measured":
                continue
            with self.subTest(cell=(cell.task, cell.model, cell.skill)):
                self.assertTrue(cell.absence.reason.strip())
                self.assertTrue(cell.absence.source.strip())

    def test_absence_is_never_recorded_alongside_a_measurement(self) -> None:
        # The invariant is enforced in the dataclass itself rather than only
        # asserted here, so no future construction path can violate it.
        with self.assertRaises(ValueError):
            collect.TaskCellAggregate(
                task=LOW_TASK,
                model="haiku",
                skill="do-in-steps",
                complexity="low",
                complexity_rank=0,
                arm_id="do-in-steps__haiku-haiku",
                in_schedule=True,
                state="measured",
                measured=None,
                absence=None,
                schedule_skip_reason=None,
                scheduler_outcome=None,
                scheduler_reason=None,
                scheduler_attempts=None,
                n_trials_seen=0,
                n_errored_trials=0,
                trial_ids=(),
            )

    def test_the_absence_state_is_not_smuggled_into_the_trial_status_vocabulary(self) -> None:
        # `Status` describes how a TRIAL turned out; `CellState` describes
        # whether a CELL has a measurement at all. Conflating them would put
        # "not yet run" into the arm table's status columns, where it has no
        # meaning. tests/test_status_contract.py derives from `Status`.
        self.assertEqual(set(get_args(collect.Status)) & set(get_args(collect.CellState)), set())


class UnscheduledTaskTests(unittest.TestCase):
    """Trials for tasks the schedule does not declare are kept, not dropped."""

    def bandit_trial(self) -> collect.TrialRecord:
        return make_trial(
            "unresolved",
            arm_id="do-in-steps__sonnet-sonnet",
            skill="do-in-steps",
            orchestrator="sonnet",
            impl="sonnet",
            task_name="datacurve/bandit-incremental-cache-control",
            trial_id="bandit-incremental-cache-control__kUB4hhY",
            cost_usd=36.5,
        )

    def test_an_unscheduled_task_gets_a_cell_with_no_complexity_label(self) -> None:
        cells = cell_index(build([self.bandit_trial()]))
        cell = cells[("bandit-incremental-cache-control", "sonnet", "do-in-steps")]
        self.assertFalse(cell.in_schedule)
        # `schedule.yaml` is the only source of complexity, and it declares
        # none for this task -- so there is none, rather than a guessed one.
        self.assertIsNone(cell.complexity)
        self.assertIsNone(cell.complexity_rank)
        self.assertEqual(cell.state, "measured")
        self.assertEqual(cell.measured.total_cost_usd, 36.5)

    def test_scheduled_cells_still_all_appear_alongside_it(self) -> None:
        cells = build([self.bandit_trial()])
        scheduled = [cell for cell in cells if cell.in_schedule]
        self.assertEqual(len(scheduled), 45)
        self.assertEqual(len(cells), 46)

    def test_cells_are_ordered_by_complexity_then_schedule_order(self) -> None:
        # Step 4 plots complexity as an ordered axis; emitting the cells in
        # that order means the renderer never has to re-sort (and never has to
        # decide where an unlabelled task goes -- they come last).
        cells = build([self.bandit_trial()])
        ranks = [cell.complexity_rank for cell in cells]
        labelled = [rank for rank in ranks if rank is not None]
        self.assertEqual(labelled, sorted(labelled))
        self.assertIsNone(ranks[-1])


class RealRunsDirectoryTests(unittest.TestCase):
    """Against the committed `runs/` tree, not a fixture.

    The recorded data is deliberately thin -- 5 trials, no vanilla arm, no
    kombu run at all -- so almost every cell is empty. That sparsity is the
    interesting case, and a fixture rich enough to be convenient would never
    exercise it.
    """

    @classmethod
    def setUpClass(cls) -> None:
        runs_dir = collect.SCRIPT_DIR / "runs"
        if not runs_dir.is_dir():
            raise unittest.SkipTest("no recorded runs/ tree in this checkout")
        cls.trials = collect.collect_trial_records(runs_dir)
        cls.cells = collect.build_task_cells(
            SCHEDULE, cls.trials, scheduler_state=collect.load_scheduler_state(runs_dir)
        )

    def test_every_recorded_trial_lands_in_exactly_one_cell(self) -> None:
        placed = [trial_id for cell in self.cells for trial_id in cell.trial_ids]
        self.assertEqual(sorted(placed), sorted(trial.trial_id for trial in self.trials))
        self.assertEqual(len(placed), len(set(placed)))  # never double-counted

    def test_the_sparse_matrix_is_mostly_honest_absence(self) -> None:
        measured = [cell for cell in self.cells if cell.state == "measured"]
        self.assertTrue(measured, "expected at least one measured cell in runs/")
        self.assertLess(len(measured), len(self.cells) / 2)
        for cell in self.cells:
            if cell.state != "measured":
                with self.subTest(cell=(cell.task, cell.model, cell.skill)):
                    self.assertIsNone(cell.measured)

    def test_the_absent_kombu_row_is_never_a_row_of_zeros(self) -> None:
        kombu = [cell for cell in self.cells if cell.task == HIGH_TASK]
        self.assertEqual(len(kombu), len(SCHEDULE.models) * len(SCHEDULE.skills))
        self.assertEqual({cell.state for cell in kombu} & {"measured"}, set())

    def test_no_measured_cell_here_carries_a_single_attempt_interval(self) -> None:
        # The synthetic fixtures in `SingleTrialIntervalTests` state the rule;
        # this is where it was actually violated. `schedule.yaml` plans one
        # trial per cell, so every measured cell in this tree is the n=1 case.
        for cell in self.cells:
            if cell.state != "measured" or cell.measured.n_attempts >= 2:
                continue
            with self.subTest(cell=(cell.task, cell.model, cell.skill)):
                self.assertTrue(cell.measured.is_single_trial)
                self.assertIsNone(cell.measured.pass_at_1_ci_low)
                self.assertIsNone(cell.measured.pass_at_1_ci_high)

    def test_the_unscheduled_bandit_trial_is_not_silently_dropped(self) -> None:
        tasks = {cell.task for cell in self.cells}
        self.assertIn("bandit-incremental-cache-control", tasks)


class SchedulerStateLoadingTests(unittest.TestCase):
    """Reading Step 2's state file, including every way it can be unusable."""

    def write_state(self, directory: Path, document: object) -> Path:
        path = directory / collect.SCHEDULER_STATE_FILENAME
        path.write_text(json.dumps(document))
        return path

    def test_a_well_formed_state_file_is_read_at_runs_dir_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            entry = {"arm_id": "a", "outcome": "technical_failure", "reason": "r", "attempts": 1}
            self.write_state(runs, {"version": 1, "runs": {"t::m::s": entry}})
            self.assertEqual(collect.load_scheduler_state(runs), {"t::m::s": entry})

    def test_a_missing_or_unusable_state_file_reads_as_no_records(self) -> None:
        # Same call as scheduler.load_state: an unreadable state file must not
        # take the collector down, and must not be guessed at either.
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            self.assertEqual(collect.load_scheduler_state(runs), {})

            (runs / collect.SCHEDULER_STATE_FILENAME).write_text("{not json")
            self.assertEqual(collect.load_scheduler_state(runs), {})

            self.write_state(runs, {"version": 99, "runs": {"t::m::s": {}}})
            self.assertEqual(collect.load_scheduler_state(runs), {})

            self.write_state(runs, {"version": 1, "runs": "not-a-mapping"})
            self.assertEqual(collect.load_scheduler_state(runs), {})


if __name__ == "__main__":
    unittest.main()
