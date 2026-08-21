#!/usr/bin/env python3
"""Loads, validates and expands `schedule.yaml` into an ordered run plan.

WHAT THIS MODULE IS FOR
------------------------
`schedule.yaml` states the benchmark matrix declaratively -- tasks, model
tier pairs, skills, pacing, and the combinations deliberately left unrun.
This module is the only thing that reads it. `run.py --mode scheduled`
executes what `expand_schedule` returns, `collect.py` records it, and
`report.py` groups by the complexity labels it carries. None of them
re-derive the matrix; there is one plan and this is where it comes from.

PURE BY CONSTRUCTION
---------------------
Nothing here sleeps, shells out, opens a socket, or writes a file. Reading
one YAML file in `load_schedule` is the entire I/O surface, and every other
entry point takes an already-parsed document. That is what lets the whole
matrix -- including the pacing arithmetic and every skip decision -- be
tested without a container, an API key, or a two-hour wait. Pacing *policy*
lives here as data (`between_runs_seconds`); actually waiting is the caller's
job, and must stay that way.

THE `vanilla` TRANSLATION -- READ THIS BEFORE TOUCHING `Arm`
------------------------------------------------------------
There is no "vanilla" skill string in the codebase. `run.py` has
`SKILLS = ["do-and-judge", "do-in-steps"]` and models the no-plugin control
arm as `Arm(skill=None, ...)`, keyed on `Arm.is_vanilla`. But from the
operator's side, vanilla is plainly a third arm type you schedule a task
under, and a YAML file that listed two skills and then carried a separate
`include_vanilla: true` flag would make the skip rules unable to talk about
vanilla at all.

So the file says `vanilla` and this module translates at the boundary:

    schedule.yaml skill        run.py representation
    -------------------        ---------------------
    "vanilla"                  Arm.skill = None, Arm.impl = None
    "do-and-judge"             Arm.skill = "do-and-judge"
    "do-in-steps"              Arm.skill = "do-in-steps"

`PlannedRun.arm_skill` performs that translation and `PlannedRun.arm_id`
reproduces `Arm.id` exactly. `run.py`'s constants and `Arm` are deliberately
NOT changed -- `tests/test_run_arm_matrix.py` and the rest of the harness
depend on the existing representation, and a config file is the wrong reason
to churn it.

WHY MIXED MODEL PAIRS ARE NOT SCHEDULED AT `vanilla`
----------------------------------------------------
`Arm.id` for a vanilla arm is `vanilla__<orchestrator>` -- the impl tier is
dropped, because a vanilla arm has no sub-agents to have an impl tier for.
The schedule's models, though, are tier *pairs*, so at skill `vanilla` the
mixed pairs collapse onto the symmetric ones: `sonnet-haiku` and `sonnet`
both resolve to `vanilla__sonnet`, as `opus-sonnet` and `opus` both resolve
to `vanilla__opus`. That is not a naming quirk -- the two are the *same
trial*. With no plugin there is nothing to dispatch sub-agents, so the impl
tier is never consulted and both cells issue an identical pier invocation
into an identical job directory.

Running both would therefore pay twice for one measurement, and worse, would
let a mixed cell re-run a trial an operator had deliberately excluded via a
skip rule naming the symmetric model. So `schedule.yaml` skips `vanilla` for
`sonnet-haiku` and `opus-sonnet` outright, with that reason attached: the
cells stay visible in the report as deliberate blanks instead of vanishing.

The consequence for callers is that no two runnable planned runs share a
`(task, arm_id)` pair, which
`tests/test_schedule.py::RunnableRunUniquenessTests` asserts against the
committed file. The underlying `Arm.id` behaviour is unchanged, so anything
resolving ids for models the schedule does not run must still expect the
collapse; `VanillaArmIdCollisionTests` pins that property of `arm_id_for`.

WHY VALIDATION IS UNFORGIVING
------------------------------
Every failure mode below raises instead of defaulting. A misconfigured
schedule does not crash a benchmark -- it produces a run that looks entirely
valid and measured the wrong matrix, and the cost of that is only paid days
later when the numbers are already being quoted. Unknown keys are rejected
for the same reason: `model:` where `models:` was meant is not a harmless
typo, it silently widens a skip rule from one model to all of them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

SCHEDULE_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEDULE_PATH = SCHEDULE_DIR / "schedule.yaml"


class ScheduleError(ValueError):
    """A schedule file that cannot be trusted to describe the intended run.

    Subclasses `ValueError` so callers in `run.py`/`report.py` can handle a
    bad config without importing this module's exception type.
    """


# --------------------------------------------------------------------------
# Mirrored constants
#
# These duplicate `run.py`'s CELLS and SKILLS on purpose. Importing `run`
# here is not an option: `run.py` imports `agent`, which imports `pier`, a
# package installed only in the dedicated pier venv -- and this module has to
# stay importable (and testable) from a plain interpreter, exactly like
# `collect.py`. Duplication is the lesser evil, and it is not left to
# vigilance: `tests/test_schedule.py::MirroredConstantTests` asserts these
# equal the real ones, so drift fails the suite rather than a benchmark.
# --------------------------------------------------------------------------

VALID_CELLS: tuple[tuple[str, str], ...] = (
    ("haiku", "haiku"),
    ("sonnet", "haiku"),
    ("sonnet", "sonnet"),
    ("opus", "sonnet"),
    ("opus", "opus"),
)

# The literal the YAML uses for the no-plugin control arm; see the module
# docstring's translation table.
VANILLA_SKILL = "vanilla"

KNOWN_SKILLS: tuple[str, ...] = (VANILLA_SKILL, "do-and-judge", "do-in-steps")

# Ordered low -> high. The order IS the data: `report.py` uses these as an
# ordered axis, so alphabetising them ("high, low, medium") would silently
# scramble every complexity chart.
COMPLEXITY_LEVELS: tuple[str, ...] = ("low", "medium", "high")

# Suffix -> seconds. Deliberately small: seconds, minutes and hours are what
# the file needs, and every extra unit is another thing a reader has to look
# up -- so the vocabulary is exactly what a pacing knob can usefully mean.
_DURATION_UNITS: dict[str, int] = {"s": 1, "m": 60, "h": 3600}

# The unit group is `+`, not a single character, so that a plausible typo like
# "2hr" reaches the unknown-unit error naming `hr` rather than falling through
# to the generic "cannot parse" message.
_DURATION_PATTERN = re.compile(r"(\d+)([a-z]+)")

_TOP_LEVEL_SECTIONS = (
    "models",
    "skills",
    "duration",
    "tasks",
    "skips",
)


def complexity_rank(level: str) -> int:
    """Position of `level` in `COMPLEXITY_LEVELS`, for sorting sanely.

    Raises rather than returning a sentinel: a chart axis silently sorting an
    unrecognised label to position -1 is worse than a crash.
    """
    if level not in COMPLEXITY_LEVELS:
        raise ScheduleError(
            f"unknown complexity {level!r} (known levels: {', '.join(COMPLEXITY_LEVELS)})"
        )
    return COMPLEXITY_LEVELS.index(level)


# --------------------------------------------------------------------------
# The schedule's data model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ScheduledTask:
    """One deep-swe task in the sweep, with its complexity band."""

    name: str
    complexity: str


@dataclass(frozen=True)
class ScheduledModel:
    """One `run.py` CELLS entry, named.

    `orchestrator` is the tier pier gets as `-m`; `impl` is the tier the
    slash command hands its sub-agents. Both are read from the file rather
    than split out of `name` -- see schedule.yaml's own comment on why.
    """

    name: str
    orchestrator: str
    impl: str


@dataclass(frozen=True)
class SkipRule:
    """A declarative "do not run these" rule with its mandatory reason.

    Each selector is `None` for "every one of them" or a tuple for "only
    these", and the selectors AND together. `None` and an empty tuple are NOT
    the same thing, which is why the parser rejects an empty list outright
    instead of picking one meaning for it.
    """

    reason: str
    tasks: tuple[str, ...] | None
    models: tuple[str, ...] | None
    skills: tuple[str, ...] | None

    def matches(self, task: ScheduledTask, model: ScheduledModel, skill: str) -> bool:
        """Whether this rule covers one (task, model, skill) combination."""
        if self.tasks is not None and task.name not in self.tasks:
            return False
        if self.models is not None and model.name not in self.models:
            return False
        if self.skills is not None and skill not in self.skills:
            return False
        return True


@dataclass(frozen=True)
class PlannedRun:
    """One (task, model, skill) cell of the matrix, runnable or skipped.

    Skipped cells stay in the expansion rather than being filtered out: the
    report needs to distinguish "deliberately not run, because X" from "no
    data", and it can only do that if the skipped cells are still present.
    """

    task: ScheduledTask
    model: ScheduledModel
    skill: str
    skipped: bool
    skip_reason: str | None

    @property
    def is_vanilla(self) -> bool:
        return self.skill == VANILLA_SKILL

    @property
    def arm_skill(self) -> str | None:
        """This run's skill in `run.py`'s vocabulary -- `None` for vanilla."""
        return None if self.is_vanilla else self.skill

    @property
    def arm_id(self) -> str:
        """The `run.py` `Arm.id` this run corresponds to."""
        return arm_id_for(self.model, self.skill)


def arm_id_for(model: ScheduledModel, skill: str) -> str:
    """Reproduce `run.py`'s `Arm.id` for a (model, skill) pair.

    Kept as a free function as well as a `PlannedRun` property so callers can
    resolve an id without first materialising a planned run.

    Mirrors `Arm.id` exactly, including the vanilla form dropping the impl
    tier -- `tests/test_schedule.py::ArmIdResolutionTests` compares this
    against real `run.Arm` instances for every planned run, so the two cannot
    drift. Dropping the impl tier means a mixed pair and its orchestrator tier
    resolve to the same vanilla id; the schedule keeps that from mattering by
    not scheduling mixed pairs at vanilla. See the module docstring.
    """
    if skill == VANILLA_SKILL:
        return f"vanilla__{model.orchestrator}"
    return f"{skill}__{model.orchestrator}-{model.impl}"


@dataclass(frozen=True)
class Schedule:
    """A validated `schedule.yaml`. Every field is known-good by construction.

    Only `parse_schedule` builds these, and it raises rather than returning a
    partially-valid one -- so anything holding a `Schedule` can use it without
    re-checking anything.
    """

    tasks: tuple[ScheduledTask, ...]
    models: tuple[ScheduledModel, ...]
    skills: tuple[str, ...]
    between_runs_seconds: int
    technical_failure_backoff_seconds: int
    skip_rules: tuple[SkipRule, ...]

    def complexity_of(self, task_name: str) -> str:
        """The declared complexity band for `task_name`."""
        for task in self.tasks:
            if task.name == task_name:
                return task.complexity
        declared = ", ".join(task.name for task in self.tasks)
        raise ScheduleError(
            f"unknown task {task_name!r} (declared tasks: {declared})"
        )


def expand_schedule(schedule: Schedule) -> list[PlannedRun]:
    """The full matrix as an ordered list, each cell runnable or skipped.

    ORDER IS PART OF THE CONTRACT: tasks outer, then models, then skills, all
    in the order `schedule.yaml` declares them. Step 2 executes runs in this
    order and the report groups by it, so this is a pure function of the file
    -- no sets, no sorting, no dict iteration order to depend on. Re-expanding
    the same schedule always yields an equal list.

    Each cell is planned exactly once: this is an n=1 sweep. Replicates would
    need a per-trial identity nothing downstream has -- two runs of one cell
    share an arm id and therefore a job directory -- so the count is fixed
    here rather than being a knob the schedule file can turn.

    The FIRST matching skip rule wins and supplies the reason, so overlapping
    rules are resolved by declaration order rather than by which one happens
    to be checked first.
    """
    return [
        _plan_one(schedule, task, model, skill)
        for task in schedule.tasks
        for model in schedule.models
        for skill in schedule.skills
    ]


def _plan_one(
    schedule: Schedule, task: ScheduledTask, model: ScheduledModel, skill: str
) -> PlannedRun:
    """Build one cell, consulting the skip rules in declaration order."""
    reason = next(
        (rule.reason for rule in schedule.skip_rules if rule.matches(task, model, skill)),
        None,
    )
    return PlannedRun(
        task=task,
        model=model,
        skill=skill,
        skipped=reason is not None,
        skip_reason=reason,
    )


# --------------------------------------------------------------------------
# Loading and validation
#
# Every helper below takes a `where` string naming the field it is checking
# ("models[2].impl", "skips[0].models") and puts it in the error message.
# That string is the difference between an operator fixing a schedule in ten
# seconds and bisecting it by deletion.
# --------------------------------------------------------------------------


def load_schedule(path: str | Path = DEFAULT_SCHEDULE_PATH) -> Schedule:
    """Read and validate a schedule file. The module's only I/O."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ScheduleError(f"cannot read schedule file {path}: {error}") from error

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ScheduleError(f"{path}: malformed YAML: {error}") from error

    return parse_schedule(document, source=str(path))


def parse_schedule(document: object, *, source: str = "<schedule>") -> Schedule:
    """Validate an already-parsed schedule document into a `Schedule`.

    Split from `load_schedule` so the validation rules can be exercised
    against in-memory documents -- no temp files, and a test that mutates one
    field reads as exactly that.
    """
    mapping = _require_mapping(document, where="document", source=source)
    _check_keys(mapping, required=_TOP_LEVEL_SECTIONS, where="document", source=source)

    models = _parse_models(mapping["models"], source=source)
    skills = _parse_skills(mapping["skills"], source=source)
    tasks = _parse_tasks(mapping["tasks"], source=source)
    between_runs, backoff = _parse_durations(mapping["duration"], source=source)
    skip_rules = _parse_skip_rules(
        mapping["skips"], tasks=tasks, models=models, skills=skills, source=source
    )

    return Schedule(
        tasks=tasks,
        models=models,
        skills=skills,
        between_runs_seconds=between_runs,
        technical_failure_backoff_seconds=backoff,
        skip_rules=skip_rules,
    )


def parse_duration(value: object, *, where: str) -> int:
    """Parse a human-legible duration ("2h", "30m", "45s") into seconds.

    A bare integer is read as seconds. Booleans are rejected explicitly
    because `bool` subclasses `int` in Python and YAML spells `True` as
    `yes`/`on` -- without this guard, `between_runs: yes` would quietly become
    a one-second pause between trials.
    """
    if isinstance(value, bool):
        raise ScheduleError(f"{where}: expected a duration, got the boolean {value!r}")

    if isinstance(value, int):
        if value < 0:
            raise ScheduleError(f"{where}: duration cannot be negative (got {value})")
        return value

    if not isinstance(value, str):
        raise ScheduleError(
            f"{where}: expected a duration like '2h' or a number of seconds, "
            f"got {type(value).__name__}"
        )

    match = _DURATION_PATTERN.fullmatch(value.strip().lower())
    if match is None:
        units = "/".join(_DURATION_UNITS)
        raise ScheduleError(
            f"{where}: cannot parse duration {value!r}; expected <integer><unit> "
            f"with unit one of {units} (e.g. '2h'), or a bare number of seconds"
        )

    amount, unit = match.groups()
    if unit not in _DURATION_UNITS:
        raise ScheduleError(
            f"{where}: unknown duration unit {unit!r} in {value!r} "
            f"(known units: {', '.join(_DURATION_UNITS)})"
        )
    return int(amount) * _DURATION_UNITS[unit]


# --- section parsers ------------------------------------------------------


def _parse_models(raw: object, *, source: str) -> tuple[ScheduledModel, ...]:
    """Model entries, each pinned to one of `run.py`'s CELLS."""
    entries = _require_nonempty_list(raw, where="models", source=source)
    models: list[ScheduledModel] = []

    for index, entry in enumerate(entries):
        where = f"models[{index}]"
        mapping = _require_mapping(entry, where=where, source=source)
        _check_keys(
            mapping, required=("name", "orchestrator", "impl"), where=where, source=source
        )
        name = _require_text(mapping["name"], where=f"{where}.name", source=source)
        orchestrator = _require_text(
            mapping["orchestrator"], where=f"{where}.orchestrator", source=source
        )
        impl = _require_text(mapping["impl"], where=f"{where}.impl", source=source)

        if (orchestrator, impl) not in VALID_CELLS:
            listed = ", ".join(f"({o}, {i})" for o, i in VALID_CELLS)
            raise ScheduleError(
                f"{source}: {where} {name!r}: orchestrator/impl pair "
                f"({orchestrator!r}, {impl!r}) is not one of run.py's CELLS: {listed}"
            )
        models.append(ScheduledModel(name=name, orchestrator=orchestrator, impl=impl))

    _reject_duplicates([m.name for m in models], kind="model", where="models", source=source)
    return tuple(models)


def _parse_skills(raw: object, *, source: str) -> tuple[str, ...]:
    """Skill names, each one the harness actually knows how to run."""
    entries = _require_nonempty_list(raw, where="skills", source=source)
    skills: list[str] = []

    for index, entry in enumerate(entries):
        where = f"skills[{index}]"
        skill = _require_text(entry, where=where, source=source)
        if skill not in KNOWN_SKILLS:
            raise ScheduleError(
                f"{source}: {where}: unknown skill {skill!r} "
                f"(known skills: {', '.join(KNOWN_SKILLS)})"
            )
        skills.append(skill)

    _reject_duplicates(skills, kind="skill", where="skills", source=source)
    return tuple(skills)


def _parse_tasks(raw: object, *, source: str) -> tuple[ScheduledTask, ...]:
    """Task entries, each carrying an ordered complexity label."""
    entries = _require_nonempty_list(raw, where="tasks", source=source)
    tasks: list[ScheduledTask] = []

    for index, entry in enumerate(entries):
        where = f"tasks[{index}]"
        mapping = _require_mapping(entry, where=where, source=source)
        _check_keys(mapping, required=("name", "complexity"), where=where, source=source)
        name = _require_text(mapping["name"], where=f"{where}.name", source=source)
        complexity = _require_text(
            mapping["complexity"], where=f"{where}.complexity", source=source
        )

        if complexity not in COMPLEXITY_LEVELS:
            raise ScheduleError(
                f"{source}: {where} {name!r}: unknown complexity {complexity!r} "
                f"(known levels: {', '.join(COMPLEXITY_LEVELS)})"
            )
        tasks.append(ScheduledTask(name=name, complexity=complexity))

    _reject_duplicates([t.name for t in tasks], kind="task", where="tasks", source=source)
    return tuple(tasks)


def _parse_durations(raw: object, *, source: str) -> tuple[int, int]:
    """The two independent pacing settings, in seconds."""
    where = "duration"
    mapping = _require_mapping(raw, where=where, source=source)
    _check_keys(
        mapping,
        required=("between_runs", "technical_failure_backoff"),
        where=where,
        source=source,
    )
    between_runs = parse_duration(
        mapping["between_runs"], where=f"{source}: {where}.between_runs"
    )
    backoff = parse_duration(
        mapping["technical_failure_backoff"],
        where=f"{source}: {where}.technical_failure_backoff",
    )
    return between_runs, backoff


def _parse_skip_rules(
    raw: object,
    *,
    tasks: tuple[ScheduledTask, ...],
    models: tuple[ScheduledModel, ...],
    skills: tuple[str, ...],
    source: str,
) -> tuple[SkipRule, ...]:
    """Skip rules, with every selector checked against what is declared.

    A rule naming something that does not exist is always a mistake, and one
    that would otherwise be invisible: the rule would simply never fire, and
    the trials it was meant to suppress would run.
    """
    entries = _require_list(raw, where="skips", source=source)
    rules: list[SkipRule] = []

    for index, entry in enumerate(entries):
        where = f"skips[{index}]"
        mapping = _require_mapping(entry, where=where, source=source)
        _check_keys(
            mapping,
            required=("reason",),
            optional=("tasks", "models", "skills"),
            where=where,
            source=source,
        )
        reason = _require_text(mapping["reason"], where=f"{where}.reason", source=source)
        rules.append(
            SkipRule(
                reason=reason.strip(),
                tasks=_parse_selector(
                    mapping, "tasks", {t.name for t in tasks}, where=where, source=source
                ),
                models=_parse_selector(
                    mapping, "models", {m.name for m in models}, where=where, source=source
                ),
                skills=_parse_selector(
                    mapping, "skills", set(skills), where=where, source=source
                ),
            )
        )

    return tuple(rules)


def _parse_selector(
    mapping: dict,
    key: str,
    declared: set[str],
    *,
    where: str,
    source: str,
) -> tuple[str, ...] | None:
    """One optional skip selector: `None` for "all", a tuple for "only these".

    An omitted key means "all". An empty list is rejected instead of being
    read as either "all" or "none" -- both readings are defensible, which is
    exactly why the file must not be allowed to say it.
    """
    if key not in mapping:
        return None

    entries = _require_list(mapping[key], where=f"{where}.{key}", source=source)
    if not entries:
        raise ScheduleError(
            f"{source}: {where}.{key}: empty selector list is ambiguous; omit the key "
            f"to mean 'all {key}', or list the {key} to restrict the rule"
        )

    names: list[str] = []
    for index, entry in enumerate(entries):
        name = _require_text(entry, where=f"{where}.{key}[{index}]", source=source)
        if name not in declared:
            raise ScheduleError(
                f"{source}: {where}.{key}: unknown {key[:-1]} {name!r} "
                f"(declared {key}: {', '.join(sorted(declared))})"
            )
        names.append(name)

    _reject_duplicates(names, kind=key[:-1], where=f"{where}.{key}", source=source)
    return tuple(names)


# --- shape checks ---------------------------------------------------------


def _require_mapping(value: object, *, where: str, source: str) -> dict:
    if not isinstance(value, dict):
        raise ScheduleError(
            f"{source}: {where}: expected a mapping, got {type(value).__name__}"
        )
    return value


def _require_list(value: object, *, where: str, source: str) -> list:
    if not isinstance(value, list):
        raise ScheduleError(
            f"{source}: {where}: expected a list, got {type(value).__name__}"
        )
    return value


def _require_nonempty_list(value: object, *, where: str, source: str) -> list:
    """An empty models/skills/tasks section collapses the matrix to nothing --
    always a mistake, never an intent worth honouring silently.
    """
    entries = _require_list(value, where=where, source=source)
    if not entries:
        raise ScheduleError(f"{source}: {where}: must declare at least one entry")
    return entries


def _require_text(value: object, *, where: str, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScheduleError(
            f"{source}: {where}: expected a non-empty string, got {value!r}"
        )
    return value.strip()


def _check_keys(
    mapping: dict,
    *,
    required: tuple[str, ...],
    optional: tuple[str, ...] = (),
    where: str,
    source: str,
) -> None:
    """Reject both missing required keys and unrecognised ones.

    Rejecting unknown keys is the load-bearing half. A misspelled key is not
    a no-op: `model:` for `models:` in a skip rule drops the model selector,
    which widens the rule from one model to every model, and the run that
    follows looks perfectly healthy.
    """
    for key in required:
        if key not in mapping:
            raise ScheduleError(f"{source}: {where}: missing required key {key!r}")

    allowed = set(required) | set(optional)
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ScheduleError(
            f"{source}: {where}: unknown key(s) {', '.join(repr(k) for k in unknown)} "
            f"(allowed: {', '.join(sorted(allowed))})"
        )


def _reject_duplicates(names: list[str], *, kind: str, where: str, source: str) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ScheduleError(f"{source}: {where}: duplicate {kind} {name!r}")
        seen.add(name)
