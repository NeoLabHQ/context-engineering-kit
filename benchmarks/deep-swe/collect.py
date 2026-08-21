#!/usr/bin/env python3
"""Deep-SWE benchmark result collector -- turns pier's `runs/` tree into
`results.json` + `results.csv`.

WHY THIS FILE DOES NOT IMPORT `pier` (OR `run.py`/`agent.py`)
---------------------------------------------------------------
`run.py` and `agent.py` both transitively `import pier` (a package only
installed in the dedicated `/tmp/pier-venv`, not in the interpreter this
script -- or its unit tests -- normally run under). `collect.py`'s job is
pure post-hoc JSON aggregation over files pier already wrote to disk; it has
no need to invoke pier or construct its agent classes. So instead of
`from pier.models.trial.result import TrialResult`, every trial's raw
`result.json` dict is read and picked apart by hand below. Two small
consequences of that choice, both called out at their point of use:

1. `agent_step_count_from_result()` / `token_cost_totals_from_result()` are
   deliberate re-implementations of `TrialResult.agent_step_count()` /
   `.compute_token_cost_totals()` (verified against
   `/tmp/pier-repo/src/pier/models/trial/result.py`, lines 91-144, on the
   pier version this harness was built against). If pier changes that
   fallback logic, these need re-syncing by hand.
2. `find_stream_log_init_event()` / `plugin_load_error_from_init_event()`
   duplicate (rather than import) run.py's `find_init_event`/
   `iter_stream_events` for the same reason -- importing run.py would pull
   in `agent.py`'s `import pier`. The duplicated logic is ~10 lines of
   stable, single-purpose JSON-line parsing; see run.py for the original.

WHAT THIS FILE MAY IMPORT
--------------------------
`schedule.py` is safe and is imported: its only dependency is PyYAML (already
a declared one), it performs no I/O beyond reading one config file, and it is
the single source of truth for the matrix, the complexity labels and the
deliberate skips -- re-deriving any of those here is exactly the duplication
it exists to prevent.

`triage.py` and `scheduler.py` are NOT, and cannot become, imports here:
`triage.py` already imports THIS module, so the arrow only ever points one
way. That is why `SCHEDULER_STATE_FILENAME`, `SCHEDULER_STATE_VERSION` and
`scheduler_state_key` are mirrored copies of scheduler.py's, and why
`tests/test_collect_task_cells.py` compares all three against the real
module so the copies cannot drift.

TRIAL-VS-JOB GLOB DEPTH
------------------------
Pier writes a `result.json` at *two* depths under `runs/`:
`runs/<arm-id>/result.json` is the JOB-level result (a `JobResult`, with its
own `stats`/`trial_results` shape); `runs/<arm-id>/<task>__<uuid>/result.json`
is the TRIAL-level result (a `TrialResult`) -- see run.py's module docstring
for the full layout. `find_trial_result_paths()` globs `*/*/result.json`,
exactly two levels down, so the shallower job-level file is never mistaken
for a trial.

STATUS CLASSIFICATION -- the single most consequential piece of logic here
-----------------------------------------------------------------------------
`status` is one of `resolved` / `unresolved` / `incomplete` / `errored`.
Signals are checked in this order (first match wins), each verified against
pier's real `TrialResult` schema
(`/tmp/pier-repo/src/pier/models/trial/result.py`):

| # | Signal                                                        | status     |
|---|----------------------------------------------------------------|------------|
| 1 | result.json missing/corrupt/truncated (can't even be parsed)   | errored    |
| 2 | non-vanilla trial, `sadd` plugin didn't load (system/init event)| errored   |
| 3 | `TrialResult.exception_info` is set (pier's own infra-failure signal: Docker/environment build failure, agent/verifier timeout, non-zero agent exit code, cancellation -- and transitively, an API 529/rate-limit failure that crashed the `claude` process; see `infra_error_category()` for how the raw exception type is normalized into one of these) | errored |
| 4 | `verifier_result` missing, or its `rewards` dict is missing/empty (verifier never produced a scalar) | errored |
| 5 | `rewards["reward"] == 1` -- or, for a bundle carrying no `reward` key, `f2p == 1.0 and p2p == 1.0`, falling back last to every value in `rewards` equalling `1` | resolved |
| 6 | no `artifacts/model.patch`, or the agent's final message ends in a question (the agent stopped without finishing -- see `find_trial_incompleteness_reason()`) | incomplete |
| 7 | otherwise (verifier ran and did not report success)            | unresolved |

Rows 1-4 are infrastructure failures, not task attempts: the agent never got
a fair, uncorrupted shot at the task, or (row 2) we can't trust this trial as
a measurement of the plugin in the first place. Folding them into
`unresolved` would silently deflate Pass@1. Row 5 reads the verdict off the
scalar `reward` key because this benchmark's verifier reports `rewards` as a
*metrics bundle* -- test counts, ratios and a `partial` graded-credit score
alongside the one binary `reward` -- so an all-values-equal-1 rule would call
a perfect trial unresolved whenever it has more than one fail-to-pass test.
See `verifier_reports_success()` for the real observed bundle, the arithmetic
relating its keys, and the two fallbacks used for bundles carrying no
`reward` key -- recomputing the verdict from `f2p`/`p2p` where those exist,
and only then the all-ones rule. Note that pier's own
`compute_pass_at_k_by_evals` (see `/tmp/pier-repo/src/pier/utils/pass_at_k.py`)
does assume one binary reward per key, so its Pass@k is not interchangeable
with this module's.

Row 6 (`incomplete`) is a THIRD outcome, deliberately neither of the two
either side of it. Read the trial that motivated it -- job
`do-in-steps__sonnet-sonnet`, trial `cattrs-partial-structuring-recov__ZsbwRdJ`
-- as recorded: it committed nothing, so pier's artifact download failed and
left no `artifacts/model.patch` (its `artifacts/manifest.json` records that
failure); pier nonetheless saw a clean agent exit and no `exception_info`; and
the verifier then dutifully scored the untouched repository 0/69, which is
indistinguishable from a genuine wrong answer.

The second signal is grounded in a different recorded trial, where the
mechanism is visible rather than inferred: `_preflight-do-in-steps/
cattrs-partial-structuring-recov__9ryVMmH` ends its final message with "Which
approach would you prefer? Or shall I continue with the current orchestration
pace?" after laying out a numbered menu under budget pressure -- a question
asked under `claude --print` with no stdin for anyone to answer through. That
is why this gate has two signals and why run.py's prompt carries a
non-interactive contract.

It is not `errored` either: nothing in the infrastructure failed, so calling it
one would blame the harness for the agent's own abandonment (and, per the
section below, quietly drop it out of Pass@1). `incomplete` names what
actually happened, and row 6 sits AFTER row 5 so a trial the verifier
certifies as solved can never be downgraded by these heuristics --
`incomplete` only ever refines what would otherwise have been `unresolved`.

PASS@1 DENOMINATOR
-------------------
`errored` trials are EXCLUDED from every per-arm average (Pass@1, avg cost,
avg output tokens, avg steps): they are not task attempts, and their
cost/token/step figures are contaminated by whatever infra failure occurred
(a Docker build failure trial burns ~$0; a timeout can burn substantial
cost before pier kills it, without finishing). `n_errored` is still reported
per arm, separately, so a reader can see how much data was dropped without
it silently disappearing from the numbers.

`incomplete` trials are INCLUDED -- they are counted as attempts that failed,
exactly where `unresolved` sits, and `n_incomplete` is reported alongside so
the reason stays visible. This is the opposite call from `errored` because
the cause is the opposite: the agent got a fair shot at the task and walked
away from it. Excluding them would let an arm raise its own Pass@1 by
abandoning the tasks it was losing, which is the last incentive this
benchmark should create.

WHY THERE IS NO "SPENT MOST OF ITS BUDGET" CONDITION
------------------------------------------------------
`incomplete` covers a missing patch and an abandoning question, but NOT
"cost came within X% of a cap" -- this harness deliberately enforces no
per-trial spend cap (see README.md's Cost section), so there is no cap for a
cost to approach and no such condition to evaluate. Cost anomalies stay
visible a different way instead: every trial's `cost_usd` is recorded
per-row, and each arm reports both `avg_cost_usd` and `max_cost_usd` --
the max because a single runaway trial is invisible in an average over
dozens. Those figures are only worth reading at all because
`ClaudeCodeSadd._parse_total_cost_from_stream_json` (agent.py) fixed the
upstream parser that reported the FIRST of a stream's many cumulative
`result` events, understating the motivating run's real spend 68x.

THE PER-CELL LAYER -- and why absence needed its own vocabulary
-----------------------------------------------------------------
The per-arm aggregate answers "how did `do-in-steps__sonnet-sonnet` do?".
The report is for a different question: "can THIS model do THIS task under
THIS skill?" -- so this module also aggregates by (task, model, skill), the
identity `schedule.yaml` itself speaks in. `build_task_cells` produces one
`TaskCellAggregate` per cell of the declared matrix, plus one for any task
found in `runs/` that the schedule does not declare (dropping those would be
data loss; guessing a complexity band for them would be worse).

The honest answer for most cells is "we do not know", and there are FOUR
categorically different reasons for that:

  deliberately_skipped     schedule.yaml says do not run it, and says why.
  structurally_impossible  there is no such trial. A vanilla arm has no
                           implementer tier, so `sonnet-haiku` + vanilla IS
                           `sonnet` + vanilla -- one arm id, one job
                           directory, one pier invocation.
  technical_failure        attempted, never fairly attempted: every trial was
                           an infra failure, or the scheduler recorded one.
  not_yet_run              no data.

None of them is `0.0`. A zero bar where the truth is "haiku was never asked"
is not a rendering bug, it is a false claim about a model's capability -- and
it is precisely the claim this benchmark exists to avoid making. So the
schema does not merely *permit* a renderer to keep them apart, it forces it:
EVERY number lives inside `TaskCellAggregate.measured`, which is `None` for
every absent cell. A chart reaching for `cell["measured"]["pass_at_1"]`
without branching on `state` raises `TypeError`; it cannot quietly draw a
zero. The mirror-image field, `absence`, is `None` exactly when `measured` is
not, and the dataclass raises if that invariant is ever broken.

`structurally_impossible` is decided from the arm-id collapse
(`schedule.arm_id_for`), not from matching the skip rule's prose -- a
classification that depended on the wording of a YAML comment would break the
first time someone rephrased it. The committed schedule does state that reason
in words, and those words are carried verbatim in `absence.reason` alongside
the derived state. Deciding it structurally also closes a real double-counting
hazard: a mixed vanilla cell shares its arm id with the symmetric one, so a
naive (task, arm_id) lookup would attribute one measurement to two cells.

THE THREE SPELLINGS OF A TASK NAME
------------------------------------
Nothing may assume these match, because they do not:

    schedule.yaml     cattrs-partial-structuring-recovery
    result.json       datacurve/cattrs-partial-structuring-recovery
    trial directory   cattrs-partial-structuring-recov__ZsbwRdJ

`resolve_trial_task_name` reconciles them, preferring `task_name` (which is
namespaced but complete) and falling back to the trial directory name (which
is truncated) only for a record whose result.json could not be parsed at all.
The truncated form is resolved by unique prefix extension, and an AMBIGUOUS
prefix resolves to nothing rather than to whichever candidate came first --
attributing trials to the wrong task is worse than leaving them unattributed.
Every reconciliation is recorded in results.json's
`schedule.task_name_reconciliation` so the mapping is auditable rather than
implicit.

RE-RUNNABLE BY CONSTRUCTION
-----------------------------
This script never reads its own previous `results.json`/`results.csv`. Every
invocation walks the full current `runs/` tree from scratch and overwrites
both output files. There is no merge/dedup step to get wrong -- running it
again after more trials complete just produces a fresh, complete rebuild.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import schedule

SCRIPT_DIR = Path(__file__).resolve().parent

# Bump when TrialRecord/ArmAggregate's field set or meaning changes, so a
# consumer of results.json can detect a shape it wasn't written for instead
# of silently misreading renamed/removed/reordered fields.
#
# v2: ArmAggregate gained `created_at` and `sample_seed`, surfaced from each
# arm's `arm.json` (see `load_arm_run_metadata`) so report.py can render a
# real run-start date/seed in its header instead of the "not recorded"
# placeholder v1 consumers must still fall back to.
#
# v3 (this version): `status` gained a fourth value, `incomplete` (see the
# module docstring's classification table), and ArmAggregate gained the
# `n_incomplete` and `max_cost_usd` fields that go with it. A v2 consumer
# reading a v3 file would silently miscount abandoned trials as `unresolved`
# ones, which is exactly the confusion this version bump exists to surface.
#
# WHY THE PER-CELL SECTIONS DID NOT BUMP THIS TO 4
# -------------------------------------------------
# results.json also carries three sections this constant does not track --
# `cells` (per-(task, model, skill) aggregates with honest absence states),
# `schedule` (the matrix those cells came from) and `baseline` (the vendored
# DeepSWE Fable 5 snapshot). They are purely ADDITIVE: `TrialRecord` and
# `ArmAggregate` are untouched, so a reader of THIS version's contract sees
# exactly the file it expects plus top-level keys it ignores, and a consumer
# that wants the new sections detects them by key presence rather than by
# integer. Bumping for them would have bought no consumer anything and cost
# the mirrored-constant guard its equality (see report.py's
# EXPECTED_RESULTS_SCHEMA_VERSION and tests/test_status_contract.py) for as
# long as report.py had not caught up -- an unbounded window in which a real,
# NON-additive drift could have slipped through unnoticed. The step that
# teaches report.py to draw the cells bumps both constants together.
#
# v4 (this version) IS that step: report.py now reads `cells`, `schedule` and
# `baseline` to draw the per-complexity, per-task and comparison views, so
# those sections stopped being optional extras a consumer could ignore and
# became part of what a reader of this file is entitled to expect. The
# integer moved for that change of status, not for a field change -- no
# TrialRecord/ArmAggregate field was touched here. Bumped together with
# report.EXPECTED_RESULTS_SCHEMA_VERSION in the same change, which is the
# equality tests/test_status_contract.py exists to enforce.
RESULTS_SCHEMA_VERSION = 4

Status = Literal["resolved", "unresolved", "incomplete", "errored"]

# How a (task, model, skill) CELL stands -- deliberately NOT a `Status`.
#
# `Status` says how one trial turned out. `CellState` says whether a cell has
# a measurement at all, and if not, which of four categorically different
# reasons applies. Merging the two vocabularies would put "not yet run" into
# the arm table's status columns, where it means nothing, and would let a
# renderer treat "never attempted" as a kind of failure. They stay disjoint;
# `tests/test_collect_task_cells.py` asserts the two sets do not intersect.
CellState = Literal[
    "measured",
    "deliberately_skipped",
    "structurally_impossible",
    "technical_failure",
    "not_yet_run",
]

# The vocabulary, written down where the consumer can read it. Emitted into
# results.json as `cell_state_vocabulary` so a renderer never has to infer
# what a state means from its name.
CELL_STATE_DESCRIPTIONS: dict[str, str] = {
    "measured": (
        "At least one fair attempt was made and scored. This is the ONLY state "
        "carrying numbers; `measured.pass_at_1` may legitimately be 0.0, which "
        "means the arm tried and solved nothing."
    ),
    "deliberately_skipped": (
        "schedule.yaml declares this cell unrun, with a stated reason. Nobody "
        "asked this model to do this task, so no claim about its ability follows."
    ),
    "structurally_impossible": (
        "There is no such trial to run. A vanilla arm has no implementer tier, "
        "so a mixed model pair's vanilla cell IS its orchestrator tier's vanilla "
        "cell -- same arm id, same job directory, same pier invocation. No budget "
        "makes this cell measurable; see `absence.collapses_onto_model`."
    ),
    "technical_failure": (
        "Attempted, but never fairly attempted: every trial was an infrastructure "
        "failure, or the scheduler recorded the cell as `technical_failure`. The "
        "agent did not get an uncontaminated shot at the task."
    ),
    "not_yet_run": "No data. The cell is runnable and simply has not been run.",
}

# The statistic behind a LOCAL per-cell interval, named in the payload so it
# can never be silently co-plotted with DeepSWE's. See `build_fable5_baseline`.
LOCAL_PASS_AT_1_INTERVAL_TYPE = "wilson_binomial"
LOCAL_PASS_AT_1_DENOMINATOR_UNIT = "local_trial_attempts"

# DeepSWE's, which are different statistics over different denominators.
FABLE5_INTERVAL_TYPE = "run_to_run_standard_error_across_whole_benchmark_passes"
FABLE5_ATTEMPT_DENOMINATOR_UNIT = "scored_rollout_attempts"
FABLE5_TASK_DENOMINATOR_UNIT = "tasks"

# Emitted into results.json alongside the numbers, so the incomparability is a
# field a renderer must read rather than a caveat it may skip.
INTERVAL_TYPE_DESCRIPTIONS: dict[str, str] = {
    LOCAL_PASS_AT_1_INTERVAL_TYPE: (
        "95% Wilson score interval over this cell's own binomial attempts "
        "(see `wilson_score_interval`)."
    ),
    FABLE5_INTERVAL_TYPE: (
        "95% run-to-run standard error across 4 whole-benchmark passes "
        "(1.96 * std(runs)/sqrt(R)). NOT a binomial interval over tasks, and "
        "not on the same footing as a Wilson interval from this harness -- "
        "drawing them as peer error bars asserts something neither supports."
    ),
}

# The vendored DeepSWE Fable 5 snapshot. Read for `results.json`'s `baseline`
# section; see `build_fable5_baseline` for what is and is not carried over.
DEFAULT_FABLE5_BASELINE_PATH = SCRIPT_DIR / "data" / "fable5_official.json"

# Step 2's bookkeeping file, at `runs/` depth 1 (NOT inside an arm directory).
#
# The name and version are MIRRORED from `scheduler.py` rather than imported:
# `triage.py` already imports this module, and `scheduler.py` imports
# `triage.py`, so importing scheduler here would close an import cycle.
# `tests/test_collect_task_cells.py` compares both constants -- and the key
# format -- against the real `scheduler` module, so the copies cannot drift.
SCHEDULER_STATE_FILENAME = "scheduler-state.json"
SCHEDULER_STATE_VERSION = 1

# The scheduler outcome that means "never fairly attempted". Its siblings
# (`success`, `model_failure`) mean the agent DID get a fair shot, so they are
# deliberately not mapped onto an absence state; see `_cell_absence`.
SCHEDULER_TECHNICAL_FAILURE_OUTCOME = "technical_failure"

# The stream-json event pier tees to `<trial_dir>/agent/claude-code.txt` that
# carries plugin-load information (see run.py's `find_init_event`, verified
# against a live `claude` invocation).
_STREAM_LOG_RELATIVE_PATH = Path("agent") / "claude-code.txt"

# The patch pier copies out of the container for a trial that committed work.
# Its absence is the hardest available evidence that a trial produced nothing
# at all -- observed on the motivating run, whose `artifacts/manifest.json`
# records `{"source": "/logs/artifacts/model.patch", "status": "failed"}`
# because the agent never committed anything for pier to download.
_MODEL_PATCH_RELATIVE_PATH = Path("artifacts") / "model.patch"


# --------------------------------------------------------------------------
# Output record shapes
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TrialRecord:
    """One row of `results.csv` / one entry of `results.json["trials"]`.

    Field order here is the single source of truth for both the CSV header
    and the JSON key order (see write_results_csv/write_results_json) --
    changing it changes both outputs together, by construction.
    """

    arm_id: str
    skill: str | None
    orchestrator: str
    impl: str | None
    task_name: str | None
    task_checksum: str | None
    resolved: bool
    # The verifier's own scalar binary verdict (`rewards["reward"]`, 0 or 1),
    # never a sum over the metrics bundle; None when the bundle has no such
    # key. See `verifier_reports_success()`.
    reward: float | None
    cost_usd: float | None
    output_tokens: int | None
    input_tokens: int | None
    cache_tokens: int | None
    n_agent_steps: int | None
    duration_sec: float | None
    status: Status
    plugin_ref: str
    claude_code_version: str | None
    # Beyond the required field list: trial_id makes every row traceable back
    # to its `runs/<arm-id>/<trial_id>/` directory, and error_reason is how
    # an `errored` row's cause -- or an `incomplete` row's, verbatim from
    # `find_trial_incompleteness_reason` -- surfaces instead of being
    # silently dropped (required by this task's plugin-load-assertion and
    # error-visibility rules). See "Context for Next Steps" in the handoff
    # notes.
    trial_id: str
    error_reason: str | None


@dataclass(frozen=True)
class ArmAggregate:
    """One entry of `results.json["arms"]` -- one row per (skill, orchestrator, impl)."""

    arm_id: str
    skill: str | None
    orchestrator: str
    impl: str | None
    is_vanilla: bool
    n_resolved: int
    n_unresolved: int
    # Trials the agent abandoned rather than failed -- counted as attempts,
    # not dropped like `n_errored`; see the module docstring's "PASS@1
    # DENOMINATOR" section for why the two are treated oppositely.
    n_incomplete: int
    n_errored: int
    n_attempts: int  # resolved + unresolved + incomplete -- the Pass@1 denominator
    n_total_trials: int  # n_attempts + n_errored -- every trial seen for this arm
    pass_at_1: float | None
    pass_at_1_ci_low: float | None
    pass_at_1_ci_high: float | None
    avg_cost_usd: float | None
    # The costliest single attempt in this arm. Reported next to the average
    # because an average over dozens of trials hides exactly the anomaly worth
    # seeing -- one runaway trial -- and, with no spend cap in this harness to
    # bound it, that outlier is the only warning an operator gets. See the
    # module docstring's "WHY THERE IS NO ..." section.
    max_cost_usd: float | None
    avg_output_tokens: float | None
    avg_n_agent_steps: float | None
    # v2 additions, both sourced from this arm's `arm.json` (see
    # `load_arm_run_metadata`) rather than computed from trials -- every
    # trial in an arm shares one arm.json, so these are constant per arm.
    created_at: str | None  # when run.py started this arm (ISO 8601, UTC)
    sample_seed: int | None  # run.py's pinned SAMPLE_SEED, or None if the
    # run mode wasn't "sample" (the seed plays no role otherwise) -- see
    # run.py's write_arm_metadata docstring.


@dataclass(frozen=True)
class CellMeasurement:
    """The numbers for one (task, model, skill) cell -- and the ONLY place
    numbers live.

    A `TaskCellAggregate` carries this only when `state == "measured"`, i.e.
    when at least one fair attempt was scored. For every absent cell it is
    `None`, so a consumer that forgets to branch on `state` gets a
    `TypeError` rather than a plausible-looking zero. That is the whole point;
    see the module docstring's "THE PER-CELL LAYER" section.

    Cost/token/step figures follow `aggregate_arm`'s conventions exactly:
    computed over ATTEMPTS only (errored trials are excluded, their figures
    being contaminated by whatever infra fault occurred), and `None` rather
    than `0` when nothing was recorded at all.
    """

    n_resolved: int
    n_unresolved: int
    n_incomplete: int
    n_attempts: int  # the Pass@1 denominator: resolved + unresolved + incomplete
    pass_at_1: float
    # True when this cell rests on ONE attempt, which is what `schedule.yaml`
    # plans for every (task, model, skill). A renderer reads this first and
    # draws the outcome ("1 of 1 resolved") rather than a rate with error bars.
    is_single_trial: bool
    # `None` for a single-attempt cell -- see `_cell_measurement` for why an
    # n=1 Wilson interval is not merely wide but actively misleading in these
    # particular field names. A consumer must branch; the fields are always
    # present and explicitly null rather than absent, matching how
    # `_baseline_rate` reports an interval DeepSWE does not publish.
    pass_at_1_ci_low: float | None
    pass_at_1_ci_high: float | None
    # What KIND of statistic the interval above is, and what its denominator
    # counts. Carried per-measurement rather than documented once, because the
    # baseline section of the same file carries a different interval over a
    # different denominator and the two must never be drawn as peers.
    #
    # Both stay populated on a single-attempt cell, where the bounds are None:
    # they name the statistic family and the denominator of `pass_at_1` ITSELF,
    # which is true whether or not bounds were computed. Nulling them with the
    # bounds would strip the local-vs-Fable-5 disambiguator from exactly the
    # cells this file currently emits, leaving a renderer nothing to check.
    pass_at_1_interval_type: str
    pass_at_1_denominator_unit: str
    total_cost_usd: float | None
    avg_cost_usd: float | None
    max_cost_usd: float | None
    total_output_tokens: float | None
    avg_output_tokens: float | None
    total_input_tokens: float | None
    avg_input_tokens: float | None
    total_cache_tokens: float | None
    avg_cache_tokens: float | None
    avg_n_agent_steps: float | None


@dataclass(frozen=True)
class CellAbsence:
    """Why one cell has no measurement -- the ONLY place absence is explained.

    Carried exactly when `CellMeasurement` is not. `reason` is prose for a
    human (verbatim from `schedule.yaml` or the scheduler where either has
    something to say); `source` names where the claim comes from, so a reader
    can go and check it.
    """

    reason: str
    # One of: "schedule.yaml", "schedule.yaml + arm_id collapse (schedule.arm_id_for)",
    # "runs/scheduler-state.json", "trial_records", "no_data".
    source: str
    # Set only for a `structurally_impossible` cell: the schedule model whose
    # vanilla cell IS this one's measurement, so a report can point the reader
    # at the number that does exist instead of leaving a blank.
    collapses_onto_model: str | None


@dataclass(frozen=True)
class TaskCellAggregate:
    """One (task, model, skill) cell of the schedule's matrix.

    `measured` and `absence` are mutually exclusive and jointly exhaustive,
    which `__post_init__` enforces rather than merely documents: every
    construction path -- including any added later -- is checked, so the
    schema's central promise cannot be broken by a new caller.

    Everything outside those two fields is true in EVERY state and safe to
    read unconditionally: the identity, the complexity label, the trial counts,
    and any declaration `schedule.yaml`/the scheduler made about this cell.
    `schedule_skip_reason` in particular is kept at this level rather than only
    inside `absence`, so a cell that was measured despite a later-added skip
    rule still discloses the operator's stated intent.
    """

    task: str  # schedule.yaml's plain name, reconciled from pier's spellings
    model: str  # schedule.yaml's model name, e.g. "sonnet-haiku"
    skill: str  # schedule.yaml's vocabulary, so "vanilla" is a peer of the plugins
    complexity: str | None  # from schedule.yaml alone; None for an undeclared task
    complexity_rank: int | None  # schedule.complexity_rank(complexity), for ordering
    arm_id: str  # the run.py Arm.id whose trials land here
    in_schedule: bool  # False for a task found in runs/ but not declared
    state: CellState
    measured: CellMeasurement | None  # non-null IFF state == "measured"
    absence: CellAbsence | None  # non-null IFF state != "measured"
    schedule_skip_reason: str | None  # whenever schedule.yaml skips this cell
    scheduler_outcome: str | None  # whenever scheduler-state.json recorded it
    scheduler_reason: str | None
    scheduler_attempts: int | None
    n_trials_seen: int  # including errored ones, which no average counts
    n_errored_trials: int
    trial_ids: tuple[str, ...]  # every trial directory folded into this cell

    def __post_init__(self) -> None:
        has_measurement = self.measured is not None
        if has_measurement != (self.state == "measured"):
            raise ValueError(
                f"cell ({self.task}, {self.model}, {self.skill}) has state "
                f"{self.state!r} but measured={'set' if has_measurement else 'None'}"
            )
        if has_measurement == (self.absence is not None):
            raise ValueError(
                f"cell ({self.task}, {self.model}, {self.skill}) must carry exactly "
                "one of `measured` / `absence`"
            )


# --------------------------------------------------------------------------
# Wilson score interval (pure, independently testable)
# --------------------------------------------------------------------------


def wilson_score_interval(
    successes: int, n: int, *, z: float = 1.959963984540054
) -> tuple[float, float]:
    """95% Wilson score confidence interval for a binomial proportion.

    `z` defaults to Phi^-1(0.975) ~= 1.959963984540054, the standard two-sided
    95% z-score; hardcoded rather than computed at runtime since it's a fixed,
    universally tabulated constant and pulling in scipy just for this would be
    a heavyweight dependency for one number.

    Numerically verified against
    `statsmodels.stats.proportion.proportion_confint(..., method="wilson")`:
    (successes=8, n=10) -> (0.4902, 0.9433); (successes=50, n=100) ->
    (0.4038, 0.5962); both match to float precision.

    n=0 is "no data", not "zero observed successes": statsmodels' own formula
    divides by n and produces NaN in that case, which both misrepresents "no
    data" as an unrepresentable number AND isn't valid JSON. This function
    instead returns (0.0, 1.0) -- maximum uncertainty -- explicitly.
    """
    if n == 0:
        return 0.0, 1.0
    if not 0 <= successes <= n:
        raise ValueError(f"successes ({successes}) must be within [0, n={n}]")

    p_hat = successes / n
    z_squared = z * z
    denominator = 1 + z_squared / n
    center = (p_hat + z_squared / (2 * n)) / denominator
    margin = (
        z * math.sqrt((p_hat * (1 - p_hat) / n) + (z_squared / (4 * n * n)))
    ) / denominator

    return max(0.0, center - margin), min(1.0, center + margin)


# --------------------------------------------------------------------------
# Status / error classification (pure, independently testable)
# --------------------------------------------------------------------------


def plugin_load_error_from_init_event(init_event: dict[str, Any] | None) -> str | None:
    """Judge a claude-code `system`/`init` event for a clean `sadd` plugin load.

    Pure judgment over an already-parsed event dict (or None if none was
    found) -- deliberately split from the file-reading step
    (`find_stream_log_init_event`) so this can be unit-tested with hand-built
    dicts, no fixture files needed. Returns None on a clean load, or a short
    machine-readable reason otherwise.
    """
    if init_event is None:
        return "missing_init_event"

    plugin_errors = init_event.get("plugin_errors") or []
    if plugin_errors:
        return f"plugin_load_error:{plugin_errors}"

    loaded_plugins = {p.get("name") for p in init_event.get("plugins", [])}
    if "sadd" not in loaded_plugins:
        loaded = sorted(name for name in loaded_plugins if name)
        return f"sadd_plugin_not_loaded:loaded={loaded}"

    return None


# A fenced code block opens and closes on a line whose first non-space
# characters are a run of backticks or tildes (CommonMark). Tracked so a `?`
# inside a diff, a traceback or a shell snippet can never read as a question.
_CODE_FENCE_PREFIXES = ("```", "~~~")

# Markdown decoration stripped off the end of the final line before looking
# for a trailing question mark, so `**Which would you like?**` still reads as a
# question. Quote and bracket characters are deliberately NOT in this set --
# see `message_ends_in_question`.
_TRAILING_MARKDOWN_CHARS = "*_`~ \t"

# The question marks a closing line may end with. ASCII `?` covers the agent
# prose this harness has recorded; U+FF1F is the full-width form a CJK
# keyboard produces (`你好？`), which reads identically to a human and would
# otherwise be a silent miss. Other scripts' marks -- Arabic `\u061f`, Greek
# `\u037e` -- are NOT matched; see this function's documented blind spots.
_QUESTION_MARKS = ("?", "\uff1f")


def last_prose_line(text: str) -> str | None:
    """The last line of `text` a reader would take as its closing sentence.

    Skips what is not prose: blank lines, fence delimiters, every line inside
    a fenced code block, and lines indented four spaces or a tab (markdown's
    other code-block form). Returns None when nothing prose-like is left.

    An unclosed fence keeps everything after it excluded, which is the
    conservative direction: a truncated log ends mid-code-block, and code is
    never a question to the operator.
    """
    inside_fence = False
    closing_line: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith(_CODE_FENCE_PREFIXES):
            inside_fence = not inside_fence
            continue
        if inside_fence or not line:
            continue
        if raw_line.startswith(("    ", "\t")):
            continue
        closing_line = line

    return closing_line


def message_ends_in_question(text: str | None) -> bool:
    """Whether an agent's final message closes by asking the reader something.

    This is a heuristic over free-form prose, so it is tuned to under-report
    rather than over-report: a missed abandonment still shows up as a failed
    trial, while a false positive would libel a trial that really did finish.
    Concretely, it fires only when the message's closing prose line (see
    `last_prose_line`) ends in a literal `?` once markdown emphasis is
    stripped. That single rule is what buys the guarantees below:

    * A rhetorical question followed by more content cannot fire -- only the
      LAST prose line is examined, so "Why? Because the parser was wrong."
      and "Should I stop? No -- continuing." are both quiet.
    * A `?` inside a code fence cannot fire; the fence's contents are skipped
      wholesale, as are indented code blocks.
    * A quoted or parenthesized question ends in `"` or `)`, not `?`, so
      `the error says "what now?"` stays quiet. Those closers are excluded
      from `_TRAILING_MARKDOWN_CHARS` on purpose: quoting a question is
      reporting one, not asking it.
    * Trailing whitespace, blank lines and a trailing newline are irrelevant,
      and so is `**bold**`/`_italic_`/`` `code` `` emphasis around the
      question itself.

    Concretely, "ends in a question mark" means ASCII `?` or its full-width
    U+FF1F form (`_QUESTION_MARKS`), the latter because a CJK keyboard produces
    it and it reads identically to a human.

    The accepted blind spots, all false NEGATIVES: a question asked in a
    four-space-indented line (markdown cannot tell that from code); a question
    phrased without a question mark ("Let me know which you prefer."); and a
    question closed with another script's mark -- Arabic `\u061f` (U+061F) or
    Greek `\u037e` (U+037E) -- neither of which has appeared in a recorded
    transcript, and adding either on speculation would widen the rule with no
    evidence behind it. Empty or absent text is never a question.
    """
    if not text:
        return False

    closing_line = last_prose_line(text)
    if closing_line is None:
        return False

    return closing_line.rstrip(_TRAILING_MARKDOWN_CHARS).endswith(_QUESTION_MARKS)


def incompleteness_reason_from_signals(
    *, has_model_patch: bool, final_message: str | None
) -> str | None:
    """Judge two already-gathered signals; None means the trial looks finished.

    Pure counterpart of `find_trial_incompleteness_reason`, split from it the
    same way `plugin_load_error_from_init_event` is split from
    `find_stream_log_init_event`: the judgment is unit-testable with plain
    values, no fixture files needed.

    The missing patch is reported first when both fire, because it is the
    stronger, non-heuristic evidence -- an operator reading
    `no_model_patch` needs no further convincing, while
    `final_message_is_question` invites a look at the transcript.
    """
    if not has_model_patch:
        return "no_model_patch"
    if message_ends_in_question(final_message):
        return "final_message_is_question"
    return None


# Maps a pier `exception_type` (an `Exception` class's bare `__name__`, per
# `ExceptionInfo.from_exception` at pier's `models/trial/result.py:31`) to a
# coarse, human-legible category. Every key below is a real class verified in
# `/tmp/pier-repo`, not invented: `AgentSetupTimeoutError`/`AgentTimeoutError`/
# `EnvironmentStartTimeoutError` at `trial/execution.py:26,30,34`,
# `NonZeroAgentExitCodeError` at `agents/installed/base.py:18`,
# `VerifierTimeoutError` at `trial/trial.py:64`, and `CancelledError`
# (asyncio's built-in, surfaced as this exact string at `job.py:40` and
# checked against at `models/job/result.py:158`).
#
# Pier has no dedicated exception class for a Docker/environment build
# failure or an Anthropic API 529: a build failure raises a plain
# `RuntimeError` (see e.g. `environments/docker/docker.py`), and a 529
# crashes the wrapped `claude` process, which pier surfaces as
# `NonZeroAgentExitCodeError` -- there is no separate signal to tell those
# two apart from the exception type alone.
_EXCEPTION_TYPE_CATEGORIES: dict[str, str] = {
    "EnvironmentStartTimeoutError": "environment_start_timeout",
    "AgentSetupTimeoutError": "agent_setup_timeout",
    "AgentTimeoutError": "agent_timeout",
    "NonZeroAgentExitCodeError": "agent_nonzero_exit",  # covers API 529 (rate limit) failures
    "VerifierTimeoutError": "verifier_timeout",
    "CancelledError": "cancelled",
}
_UNMAPPED_EXCEPTION_CATEGORY = "other_infra_error"  # e.g. RuntimeError from a Docker build failure


def infra_error_category(exception_type: str) -> str:
    """Normalize a pier `exception_type` string into one of the coarse
    categories above, or `_UNMAPPED_EXCEPTION_CATEGORY` for anything else
    (still preserved verbatim alongside this category -- see `classify_status`).
    """
    return _EXCEPTION_TYPE_CATEGORIES.get(exception_type, _UNMAPPED_EXCEPTION_CATEGORY)


def verifier_reports_success(rewards: dict[str, float | int]) -> bool:
    """Whether a non-empty verifier rewards bundle means the task was solved.

    DeepSWE's verifier emits `rewards` as a *metrics bundle*, not a set of
    binary rewards. A real observed value (a run that fixed nothing but broke
    nothing), read verbatim from
    `runs/_preflight/abs-stepped-slices__HyQJyYy/verifier/reward.json`, is:

        {"reward": 0, "f2p_total": 6, "f2p_passed": 0, "p2p_total": 6,
         "p2p_passed": 6, "f2p": 0.0, "p2p": 1.0, "partial": 0.5}

    Only `reward` is the binary verdict -- 1 iff `f2p == 1.0 and p2p == 1.0`,
    i.e. standard SWE-bench "resolved" semantics. The other keys are raw test
    counts (`*_total`/`*_passed`), their ratios, and `partial` graded credit
    ((f2p + p2p) / 2). Demanding that *every* value equal 1 therefore marks a
    perfect trial unresolved the moment it has more than one f2p test, which
    is why Pass@1 must be read off the scalar instead.

    Three rules are tried in this order, most to least grounded:

    1. `reward` present -- the verifier's own verdict, used verbatim.
    2. no `reward`, but `f2p`/`p2p` present -- recompute the verdict from the
       definition above (`f2p == 1.0 and p2p == 1.0`). This is the same
       arithmetic the verifier itself applies, just done here.
    3. neither -- fall back to the original all-values-equal-1 rule.

    Rule 3 is deliberately last: it is exactly the rule that misclassified
    every perfect DeepSWE trial, so it may only decide a bundle that offers
    no better signal at all. On a genuinely binary bundle (`{"resolved": 1}`)
    it is correct, which is why it stays rather than raising.
    """
    if "reward" in rewards:
        return rewards["reward"] == 1
    if {"f2p", "p2p"} <= rewards.keys():
        return rewards["f2p"] == 1.0 and rewards["p2p"] == 1.0
    return all(value == 1 for value in rewards.values())


def classify_status(
    *,
    exception_type: str | None,
    rewards: dict[str, float | int] | None,
    plugin_load_error: str | None,
    incompleteness_reason: str | None,
) -> tuple[Status, str | None]:
    """Classify one trial's outcome. Returns (status, error_reason).

    `incompleteness_reason` is `find_trial_incompleteness_reason()`'s verdict
    for this trial (None if it looks finished). It is a required argument with
    no default on purpose: a completion gate that a caller can forget to pass
    is a completion gate that silently stops gating, which is the failure mode
    this parameter was added to end.

    `error_reason` is always None for `resolved`/`unresolved`; for `errored`
    it names which of the rules in this module's docstring table fired, and
    for `incomplete` it carries the incompleteness reason verbatim. A
    pier exception_info additionally carries a normalized category from
    `infra_error_category()` alongside the raw `exception_type`, so no
    information is lost even though the outcome is always `errored` either
    way. Signal precedence matches the module docstring's table (plugin
    load, then pier's own exception_info, then a missing/empty rewards
    dict, then the verifier's own success verdict, and only then the
    completion gate -- a verified success is never downgraded to
    `incomplete`).

    Worked example: `claude` crashes mid-task from an Anthropic API 529 (so
    `exception_type="NonZeroAgentExitCodeError"`), but the verifier still
    happened to run and scored the trial a success (`rewards["reward"] == 1`).
    exception_info is checked before rewards, so this is still
    `("errored", "pier_exception:agent_nonzero_exit:NonZeroAgentExitCodeError")`
    -- never `resolved`, even though the verifier said the task was solved.
    """
    if plugin_load_error is not None:
        return "errored", plugin_load_error
    if exception_type is not None:
        category = infra_error_category(exception_type)
        return "errored", f"pier_exception:{category}:{exception_type}"
    if not rewards:
        return "errored", "missing_verifier_rewards"
    if verifier_reports_success(rewards):
        return "resolved", None
    if incompleteness_reason is not None:
        return "incomplete", incompleteness_reason
    return "unresolved", None


# --------------------------------------------------------------------------
# Re-implementations of TrialResult.agent_step_count() /
# .compute_token_cost_totals() over the raw JSON dict -- see module
# docstring's "WHY THIS FILE DOES NOT IMPORT pier" section for why these
# aren't just calls into pier's own pydantic model.
# --------------------------------------------------------------------------


def agent_step_count_from_result(trial: dict[str, Any]) -> int | None:
    """Mirrors `TrialResult.agent_step_count()` (pier result.py:91-110)."""
    if trial.get("n_agent_steps") is not None:
        return trial["n_agent_steps"]

    agent_result = trial.get("agent_result")
    if agent_result and agent_result.get("n_agent_steps") is not None:
        return agent_result["n_agent_steps"]

    step_results = trial.get("step_results")
    if not step_results:
        return None

    total = 0
    found_any = False
    for step in step_results:
        step_agent_result = step.get("agent_result")
        if not step_agent_result or step_agent_result.get("n_agent_steps") is None:
            continue
        found_any = True
        total += step_agent_result["n_agent_steps"]
    return total if found_any else None


def token_cost_totals_from_result(
    trial: dict[str, Any],
) -> tuple[int | None, int | None, int | None, float | None]:
    """Mirrors `TrialResult.compute_token_cost_totals()` (pier result.py:112-144).

    Returns (n_input_tokens, n_cache_tokens, n_output_tokens, cost_usd).
    """
    agent_result = trial.get("agent_result")
    if agent_result:
        contexts = [agent_result]
    else:
        step_results = trial.get("step_results") or []
        contexts = [
            step["agent_result"] for step in step_results if step.get("agent_result")
        ]

    if not contexts:
        return None, None, None, None

    n_input = n_cache = n_output = None
    cost: float | None = None
    for ctx in contexts:
        if ctx.get("n_input_tokens") is not None:
            n_input = (n_input or 0) + ctx["n_input_tokens"]
        if ctx.get("n_cache_tokens") is not None:
            n_cache = (n_cache or 0) + ctx["n_cache_tokens"]
        if ctx.get("n_output_tokens") is not None:
            n_output = (n_output or 0) + ctx["n_output_tokens"]
        if ctx.get("cost_usd") is not None:
            cost = (cost or 0.0) + ctx["cost_usd"]

    return n_input, n_cache, n_output, cost


def trial_duration_seconds(started_at: str | None, finished_at: str | None) -> float | None:
    """Whole-trial wall time from TrialResult's top-level started_at/finished_at.

    (As opposed to just `agent_execution` time -- this includes environment
    setup and verification too, i.e. "how long did this trial take end to
    end". Both are always set once `result.json` exists: pier's
    `_cleanup_and_finalize` sets `finished_at` in a `finally` block that runs
    on every code path, success or exception -- see trial.py:943-1046.)
    """
    if started_at is None or finished_at is None:
        return None
    return (datetime.fromisoformat(finished_at) - datetime.fromisoformat(started_at)).total_seconds()


def mean_or_none(values: list[float | int | None]) -> float | None:
    """Average of the non-None values, or None if there are none."""
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def max_or_none(values: list[float | int | None]) -> float | None:
    """Largest of the non-None values, or None if there are none.

    Same "no data is None, never 0.0" contract as `mean_or_none` -- report.py
    relies on every numeric arm field distinguishing the two (see its
    "NULL-HANDLING PHILOSOPHY" docstring section).
    """
    present = [v for v in values if v is not None]
    return max(present) if present else None


def sum_or_none(values: list[float | int | None]) -> float | None:
    """Total of the non-None values, or None if there are none.

    The `None`-not-`0.0` contract matters more here than anywhere else in this
    file, because `sum([])` is `0` and Python will hand it over without
    complaint. A cell whose cost was never recorded would then report having
    cost nothing, which is a claim, and a false one -- so the empty case is
    answered explicitly instead.
    """
    present = [v for v in values if v is not None]
    return sum(present) if present else None


# --------------------------------------------------------------------------
# Filesystem walking
# --------------------------------------------------------------------------


def find_trial_result_paths(runs_dir: Path) -> list[Path]:
    """All TRIAL-level result.json files: `runs/<arm-id>/<trial>/result.json`.

    Exactly two levels below runs_dir -- see module docstring's "TRIAL-VS-JOB
    GLOB DEPTH" section for why this must not match the shallower job-level
    `runs/<arm-id>/result.json`.
    """
    return sorted(runs_dir.glob("*/*/result.json"))


def load_json_or_none(path: Path) -> dict[str, Any] | None:
    """Parse a JSON file, returning None instead of raising for any I/O or
    parse failure (missing file, truncated write, invalid JSON, invalid or
    truncated UTF-8).

    A `result.json`/`arm.json` corrupted mid-write by an interrupted job --
    the exact scenario this collector must survive -- can leave behind an
    invalid UTF-8 byte or a multi-byte character cut off at EOF. Without
    catching `UnicodeDecodeError` here, `path.read_text()` raises past this
    function and crashes `main()`, discarding every already-collected trial
    from the whole run (see `find_stream_log_init_event` below, which reads
    its log with `errors="replace"` for the same reason).
    """
    try:
        return json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def iter_stream_events(stream_log: Path) -> Iterator[dict[str, Any]]:
    """Yield each parseable JSON object from a claude-code.txt transcript,
    or nothing at all if the log is missing.

    Duplicated from run.py's `iter_stream_events` (same name, same shape)
    rather than imported -- see module docstring's "WHY THIS FILE DOES NOT
    IMPORT pier" section. Within *this* file it is the one reader both
    `find_stream_log_init_event` and `find_stream_log_final_message` share, so
    the two can't drift apart on which lines count as events.

    Read with `errors="replace"` for the reason `load_json_or_none` documents:
    a transcript truncated mid-multibyte-character must not take the whole
    collection run down with a UnicodeDecodeError. A replaced byte corrupts
    only its own line, which then fails to parse and is skipped.
    """
    try:
        content = stream_log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return

    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def find_stream_log_init_event(trial_dir: Path) -> dict[str, Any] | None:
    """Locate and return the `system`/`init` event from this trial's
    claude-code.txt transcript, or None if the log or the event is missing.
    """
    for event in iter_stream_events(trial_dir / _STREAM_LOG_RELATIVE_PATH):
        if event.get("type") == "system" and event.get("subtype") == "init":
            return event
    return None


def find_stream_log_final_message(trial_dir: Path) -> str | None:
    """The agent's final message: the `result` field of the LAST
    `{"type":"result"}` event in this trial's transcript.

    WHICH MESSAGE COUNTS AS "FINAL" -- the load-bearing choice here. The two
    candidates are this one and the last `assistant` text block in the stream;
    this one wins for three reasons. It is by construction the text
    `claude --print` emitted as its turn-final answer to the (absent)
    operator, i.e. the message that accompanies `stop_reason: end_turn` and
    would have been the question a human was expected to answer. It is one
    flat string, where the last assistant block has to be dug out of
    interleaved content parts whose text may belong to a sub-agent rather
    than the orchestrator -- attributing a sub-agent's question to the run
    would be a false positive. And it is the same event family
    `ClaudeCodeSadd._parse_total_cost_from_stream_json` reads, so both cost
    and completion are judged off one authoritative event.

    LAST, not first: a `--print` session with async sub-agents emits one
    `result` event per resumption (22 of them on the motivating run), and only
    the last one describes how the session actually ended -- the same trap
    agent.py's cost override exists to fix.

    Returns None when the log is missing, carries no `result` event, or that
    event's `result` is not a string.
    """
    final_message: str | None = None
    for event in iter_stream_events(trial_dir / _STREAM_LOG_RELATIVE_PATH):
        if event.get("type") != "result":
            continue
        message = event.get("result")
        if isinstance(message, str):
            final_message = message
    return final_message


def trial_has_model_patch(trial_dir: Path) -> bool:
    """Whether this trial left behind a NON-EMPTY `artifacts/model.patch`.

    Absent and empty both mean the same thing about the agent -- it committed
    nothing -- so they are answered the same way here. An empty patch is the
    likelier shape whenever pier creates the destination before the copy it is
    about to fail (the motivating run instead lost the file entirely: its
    `artifacts/manifest.json` records `model.patch` with `"status": "failed"`,
    leaving only that manifest behind). Accepting a zero-byte file would let
    exactly the condition this gate exists to catch through as `unresolved`,
    which is why the size is checked and not just the file's existence.

    `os.stat` is only reached when `is_file()` already said there is a file to
    stat, and `is_file()` is false -- never an exception -- when the file, the
    `artifacts/` directory, or the whole trial directory is absent. So this
    answers False for every one of those cases without raising.
    """
    model_patch = trial_dir / _MODEL_PATCH_RELATIVE_PATH
    return model_patch.is_file() and model_patch.stat().st_size > 0


def find_trial_incompleteness_reason(trial_dir: Path) -> str | None:
    """Gather this trial's completion signals off disk, then judge them.

    Impure counterpart of `incompleteness_reason_from_signals`, which holds
    the actual rules. Also called by run.py (the only import direction that
    is safe: run.py may import collect.py, never the reverse -- see this
    module's docstring) so that the gate a run reports live and the gate
    `results.json` records are the same code, not two drifting copies.
    """
    return incompleteness_reason_from_signals(
        has_model_patch=trial_has_model_patch(trial_dir),
        final_message=find_stream_log_final_message(trial_dir),
    )


def build_trial_record(trial_dir: Path, arm_meta: dict[str, Any]) -> TrialRecord:
    """Build one TrialRecord from `<trial_dir>/result.json` plus its arm's metadata."""
    trial = load_json_or_none(trial_dir / "result.json")
    if trial is None:
        return _errored_record(trial_dir, arm_meta, error_reason="malformed_result_json")

    is_vanilla = bool(arm_meta.get("is_vanilla"))
    plugin_load_error = (
        None if is_vanilla else plugin_load_error_from_init_event(find_stream_log_init_event(trial_dir))
    )

    exception_info = trial.get("exception_info")
    exception_type = exception_info.get("exception_type") if exception_info else None

    verifier_result = trial.get("verifier_result")
    rewards = verifier_result.get("rewards") if verifier_result else None

    status, error_reason = classify_status(
        exception_type=exception_type,
        rewards=rewards,
        plugin_load_error=plugin_load_error,
        incompleteness_reason=find_trial_incompleteness_reason(trial_dir),
    )

    n_input, n_cache, n_output, cost = token_cost_totals_from_result(trial)
    agent_info = trial.get("agent_info") or {}

    return TrialRecord(
        arm_id=arm_meta["arm_id"],
        skill=arm_meta.get("skill"),
        orchestrator=arm_meta["orchestrator_tier"],
        impl=arm_meta.get("impl_tier"),
        task_name=trial.get("task_name"),
        task_checksum=trial.get("task_checksum"),
        resolved=status == "resolved",
        # The verifier's scalar binary verdict, not a sum over the bundle --
        # summing a metrics bundle produces a meaningless number (28.0 for a
        # perfect trial). None when the bundle carries no `reward` key; see
        # `verifier_reports_success` for that fallback.
        reward=rewards.get("reward") if rewards else None,
        cost_usd=cost,
        output_tokens=n_output,
        input_tokens=n_input,
        cache_tokens=n_cache,
        n_agent_steps=agent_step_count_from_result(trial),
        duration_sec=trial_duration_seconds(trial.get("started_at"), trial.get("finished_at")),
        status=status,
        plugin_ref=arm_meta.get("cek_ref", ""),
        claude_code_version=agent_info.get("version"),
        trial_id=trial_dir.name,
        error_reason=error_reason,
    )


def _errored_record(trial_dir: Path, arm_meta: dict[str, Any], *, error_reason: str) -> TrialRecord:
    """An `errored` TrialRecord built from arm metadata alone, for trials whose
    result.json couldn't even be parsed (see rule #1 in the classification table).
    """
    return TrialRecord(
        arm_id=arm_meta["arm_id"],
        skill=arm_meta.get("skill"),
        orchestrator=arm_meta["orchestrator_tier"],
        impl=arm_meta.get("impl_tier"),
        task_name=None,
        task_checksum=None,
        resolved=False,
        reward=None,
        cost_usd=None,
        output_tokens=None,
        input_tokens=None,
        cache_tokens=None,
        n_agent_steps=None,
        duration_sec=None,
        status="errored",
        plugin_ref=arm_meta.get("cek_ref", ""),
        claude_code_version=None,
        trial_id=trial_dir.name,
        error_reason=error_reason,
    )


def collect_trial_records(runs_dir: Path) -> list[TrialRecord]:
    """Walk `runs_dir` and build one TrialRecord per trial-level result.json.

    Full rebuild every call -- see module docstring's "RE-RUNNABLE BY
    CONSTRUCTION" section for why there is no merge/dedup step to write.
    An arm whose `arm.json` is missing or unreadable is skipped with a loud
    warning (never silently, never crashing the whole collection run) since
    its required skill/orchestrator/impl fields can't be recovered. The
    warning is printed once per arm (job_dir), not once per trial -- an arm
    with a bad arm.json still has N trial result.json files under it, and
    without `warned_job_dirs` tracking, this loop would otherwise print the
    same warning N times for what is really a single problem.
    """
    records: list[TrialRecord] = []
    arm_meta_by_job_dir: dict[Path, dict[str, Any] | None] = {}
    warned_job_dirs: set[Path] = set()

    for result_path in find_trial_result_paths(runs_dir):
        trial_dir = result_path.parent
        job_dir = trial_dir.parent

        if job_dir not in arm_meta_by_job_dir:
            arm_meta_by_job_dir[job_dir] = load_json_or_none(job_dir / "arm.json")
        arm_meta = arm_meta_by_job_dir[job_dir]

        if arm_meta is None:
            if job_dir not in warned_job_dirs:
                warned_job_dirs.add(job_dir)
                print(
                    f"[collect] WARNING: skipping all trials under {job_dir} -- no readable arm.json",
                    file=sys.stderr,
                )
            continue

        records.append(build_trial_record(trial_dir, arm_meta))

    return records


def load_arm_run_metadata(runs_dir: Path) -> dict[str, dict[str, Any]]:
    """Map arm_id -> {"created_at", "sample_seed"}, read fresh from each
    arm's `arm.json`.

    Deliberately a separate walk from `collect_trial_records`'s own
    `arm_meta_by_job_dir` cache rather than a shared lookup -- this keeps the
    v2 run-metadata addition fully additive, with zero chance of perturbing
    trial-collection's already-verified arm-loading/warning behavior.

    An `arm.json` written before this field existed (i.e. by a run.py that
    predates this change) simply has no "sample_seed" key; `.get()` reports
    that the same way as a genuinely inapplicable run mode -- `None` -- since
    `aggregate_arm` records are additionally guarded by `RESULTS_SCHEMA_VERSION`:
    a v1 `results.json` never had this field at all, which is how
    report.py's fallback tells "never recorded" apart from "recorded as N/A".
    """
    metadata: dict[str, dict[str, Any]] = {}
    for arm_json_path in sorted(runs_dir.glob("*/arm.json")):
        arm_meta = load_json_or_none(arm_json_path)
        if arm_meta is None or "arm_id" not in arm_meta:
            continue
        metadata[arm_meta["arm_id"]] = {
            "created_at": arm_meta.get("created_at"),
            "sample_seed": arm_meta.get("sample_seed"),
        }
    return metadata


# --------------------------------------------------------------------------
# Per-arm aggregation (pure, independently testable)
# --------------------------------------------------------------------------


def group_trials_by_arm(trials: list[TrialRecord]) -> dict[str, list[TrialRecord]]:
    """Group trial records by arm_id, preserving each arm's first-seen order."""
    groups: dict[str, list[TrialRecord]] = {}
    for trial in trials:
        groups.setdefault(trial.arm_id, []).append(trial)
    return groups


def aggregate_arm(
    trials: list[TrialRecord], run_metadata: dict[str, Any] | None = None
) -> ArmAggregate:
    """Aggregate one arm's trials into its leaderboard row.

    `trials` must all share the same arm_id (group_trials_by_arm's job).
    Errored trials are excluded from every average and from Pass@1's
    denominator; incomplete ones are included as failed attempts -- see module
    docstring's "PASS@1 DENOMINATOR" section for both calls.

    Worked example: 11 trials for one arm -- 6 resolved, 2 unresolved, 1
    incomplete, 2 errored -- yield `n_attempts=9` (6+2+1, excluding only the
    errored pair), `pass_at_1=6/9`, and a CI from
    `wilson_score_interval(6, 9)`. The 2 errored trials count toward
    `n_errored`/`n_total_trials` only, never the denominator or any average.

    `run_metadata` is this arm's `{"created_at", "sample_seed"}` entry from
    `load_arm_run_metadata` (keyed by arm_id), or `None` when the caller has
    no such mapping (e.g. an existing unit test built straight from
    TrialRecords) -- both `created_at`/`sample_seed` fall back to `None`
    rather than raising, keeping this function usable exactly as before.
    """
    first = trials[0]
    resolved = [t for t in trials if t.status == "resolved"]
    unresolved = [t for t in trials if t.status == "unresolved"]
    incomplete = [t for t in trials if t.status == "incomplete"]
    errored = [t for t in trials if t.status == "errored"]
    attempts = resolved + unresolved + incomplete

    n_attempts = len(attempts)
    pass_at_1 = len(resolved) / n_attempts if n_attempts > 0 else None
    ci_low, ci_high = (
        wilson_score_interval(len(resolved), n_attempts) if n_attempts > 0 else (None, None)
    )
    arm_run_metadata = (run_metadata or {}).get(first.arm_id, {})

    return ArmAggregate(
        arm_id=first.arm_id,
        skill=first.skill,
        orchestrator=first.orchestrator,
        impl=first.impl,
        is_vanilla=first.skill is None,
        n_resolved=len(resolved),
        n_unresolved=len(unresolved),
        n_incomplete=len(incomplete),
        n_errored=len(errored),
        n_attempts=n_attempts,
        n_total_trials=len(trials),
        pass_at_1=pass_at_1,
        pass_at_1_ci_low=ci_low,
        pass_at_1_ci_high=ci_high,
        avg_cost_usd=mean_or_none([t.cost_usd for t in attempts]),
        max_cost_usd=max_or_none([t.cost_usd for t in attempts]),
        avg_output_tokens=mean_or_none([t.output_tokens for t in attempts]),
        avg_n_agent_steps=mean_or_none([t.n_agent_steps for t in attempts]),
        created_at=arm_run_metadata.get("created_at"),
        sample_seed=arm_run_metadata.get("sample_seed"),
    )


def aggregate_all_arms(
    trials: list[TrialRecord], run_metadata: dict[str, Any] | None = None
) -> list[ArmAggregate]:
    """One ArmAggregate per distinct arm_id seen in `trials`, sorted for
    deterministic output ordering.

    `run_metadata` is forwarded verbatim to `aggregate_arm` -- see its
    docstring; `None` (the default) preserves this function's pre-v2 behavior
    exactly, so existing callers/tests need no changes.
    """
    groups = group_trials_by_arm(trials)
    return [aggregate_arm(groups[arm_id], run_metadata) for arm_id in sorted(groups)]


# --------------------------------------------------------------------------
# Task-name reconciliation (pure, independently testable)
#
# One task wears three different names on the way through this harness; see
# the module docstring's "THE THREE SPELLINGS OF A TASK NAME" section for the
# worked example and for why an ambiguous prefix resolves to nothing.
# --------------------------------------------------------------------------


def strip_task_namespace(name: str) -> str:
    """`datacurve/abs-stepped-slices` -> `abs-stepped-slices`.

    pier records the task under its pier-side namespace; `schedule.yaml` names
    it plainly. Split on the LAST separator so a namespace that ever gains a
    second level still reduces to the bare task name.
    """
    return name.rsplit("/", 1)[-1]


def task_slug_from_trial_id(trial_id: str) -> str:
    """`cattrs-partial-structuring-recov__ZsbwRdJ` -> `cattrs-partial-structuring-recov`.

    Splits on the LAST `__` because pier appends its per-trial suffix there,
    while task names themselves contain single hyphens (and could contain a
    `__` of their own only by appending one). The result is frequently
    TRUNCATED -- pier caps the directory-name prefix -- which is why callers
    must resolve it against the schedule rather than compare it directly.
    """
    return trial_id.rsplit("__", 1)[0]


def resolve_scheduled_task_name(candidate: str, known_tasks: Sequence[str]) -> str | None:
    """The scheduled task `candidate` names, or None if that is not decidable.

    An exact hit wins. Otherwise `candidate` is treated as a possibly-truncated
    prefix and accepted only when exactly ONE scheduled task extends it.

    Returning None for an ambiguous prefix is the whole point: silently picking
    the first match would attribute a trial's cost and verdict to the wrong
    task, which is a worse outcome than leaving it unattributed and visible.
    """
    if not candidate:
        return None
    if candidate in known_tasks:
        return candidate

    extensions = [task for task in known_tasks if task.startswith(candidate)]
    return extensions[0] if len(extensions) == 1 else None


def resolve_trial_task_name(
    trial: TrialRecord, known_tasks: Sequence[str]
) -> tuple[str | None, str]:
    """This trial's task in schedule vocabulary, plus how it was determined.

    `result.json`'s `task_name` is preferred because it is complete (merely
    namespaced). The trial DIRECTORY name is only truncated evidence, so it is
    the fallback -- reached for a record whose result.json could not be parsed
    at all, which is exactly when `task_name` is None.

    The returned method is one of `task_name`, `task_name_unscheduled`,
    `trial_id_prefix`, `trial_id_unscheduled` or `unresolved`, and is recorded
    in results.json so the mapping can be audited rather than trusted.
    """
    if trial.task_name:
        stripped = strip_task_namespace(trial.task_name)
        scheduled = resolve_scheduled_task_name(stripped, known_tasks)
        if scheduled is not None:
            return scheduled, "task_name"
        # A real task pier ran that `schedule.yaml` does not declare. Keeping
        # it under its own name is the only non-lossy option.
        return stripped, "task_name_unscheduled"

    slug = task_slug_from_trial_id(trial.trial_id)
    scheduled = resolve_scheduled_task_name(slug, known_tasks)
    if scheduled is not None:
        return scheduled, "trial_id_prefix"
    return (slug or None), ("trial_id_unscheduled" if slug else "unresolved")


# --------------------------------------------------------------------------
# Cell identity (pure, independently testable)
# --------------------------------------------------------------------------


def cell_is_structurally_impossible(model: schedule.ScheduledModel, skill: str) -> bool:
    """Whether this (model, skill) pair names a trial that cannot exist.

    True exactly for a mixed tier pair at `vanilla`. With no plugin there is
    nothing to dispatch sub-agents, so the impl tier is never consulted and
    `Arm.id` drops it -- meaning the cell resolves to the symmetric model's
    arm, not to one of its own.

    Decided from the tier pair, NOT from matching `schedule.yaml`'s skip-rule
    prose: a classification that depended on the wording of a comment would
    break the first time someone rephrased it, and would silently reclassify
    six cells as ordinary skips.
    """
    return skill == schedule.VANILLA_SKILL and model.orchestrator != model.impl


def vanilla_collapse_target(
    models: Sequence[schedule.ScheduledModel], model: schedule.ScheduledModel
) -> schedule.ScheduledModel | None:
    """The symmetric model whose vanilla cell IS `model`'s vanilla cell.

    `sonnet-haiku` collapses onto `sonnet`, `opus-sonnet` onto `opus`. Found by
    comparing real `arm_id_for` results rather than by string-splitting the
    model name, since `schedule.py` deliberately refuses to make the tier
    mapping guessable. None when nothing collapses (a symmetric model, or a
    schedule that declares no symmetric peer for this orchestrator).
    """
    if model.orchestrator == model.impl:
        return None

    collapsed_id = schedule.arm_id_for(model, schedule.VANILLA_SKILL)
    return next(
        (
            candidate
            for candidate in models
            if candidate.name != model.name
            and candidate.orchestrator == candidate.impl
            and schedule.arm_id_for(candidate, schedule.VANILLA_SKILL) == collapsed_id
        ),
        None,
    )


def scheduled_model_for_tiers(
    models: Sequence[schedule.ScheduledModel], orchestrator: str, impl: str | None, skill: str
) -> schedule.ScheduledModel | None:
    """The schedule model an arm's recorded tier pair corresponds to.

    `arm.json` records tiers, not schedule model names, so a trial found under
    a cell the schedule does not plan has to be mapped back by hand.

    A VANILLA arm records `impl_tier: null`, because it has no implementer
    tier to record -- so matching on the pair would match nothing. The
    orchestrator alone is therefore the key there, resolved to the SYMMETRIC
    model, which mirrors exactly what `arm_id_for` does when it drops the impl
    tier. (The mixed pairs that also share that orchestrator have no vanilla
    cell of their own; see `cell_is_structurally_impossible`.)
    """
    if skill == schedule.VANILLA_SKILL:
        symmetric = next(
            (m for m in models if m.orchestrator == orchestrator and m.impl == orchestrator), None
        )
        return symmetric or next((m for m in models if m.orchestrator == orchestrator), None)

    return next((m for m in models if m.orchestrator == orchestrator and m.impl == impl), None)


# --------------------------------------------------------------------------
# The scheduler's state file
# --------------------------------------------------------------------------


def scheduler_state_key(task: str, model: str, skill: str) -> str:
    """One cell's identity in `scheduler-state.json`.

    Mirrors `scheduler.run_key` rather than importing it -- `triage.py`
    already imports this module and `scheduler.py` imports `triage.py`, so the
    import would be circular. `tests/test_collect_task_cells.py` compares this
    against the real `scheduler.run_key` so the two cannot drift.
    """
    return f"{task}::{model}::{skill}"


def load_scheduler_state(runs_dir: Path) -> dict[str, dict]:
    """The `runs` map from `runs/scheduler-state.json`; `{}` for anything unusable.

    Written at `runs_dir` depth 1 -- beside the arm directories, not inside
    one. Missing, unreadable, malformed or written by a version this doesn't
    know all mean the same thing here: no trustworthy record, so no cell is
    labelled a technical failure on its authority. That is the safe direction
    -- it can leave a cell reading `not_yet_run`, which is honest, where the
    opposite reading would invent a failure that may never have happened.

    Deliberately the same tolerant contract as `scheduler.load_state`, for the
    same reason: bookkeeping truncated by the very interruption it exists to
    survive must not take down the thing reading it.
    """
    document = load_json_or_none(runs_dir / SCHEDULER_STATE_FILENAME)
    if document is None or document.get("version") != SCHEDULER_STATE_VERSION:
        return {}

    runs = document.get("runs")
    return runs if isinstance(runs, dict) else {}


# --------------------------------------------------------------------------
# Per-cell aggregation (pure, independently testable)
#
# `build_task_cells` is the entry point; everything below it is a step of that
# one walk, split out so each rule can be read and tested on its own.
# --------------------------------------------------------------------------


def build_task_cells(
    sched: schedule.Schedule,
    trials: list[TrialRecord],
    *,
    scheduler_state: dict[str, dict] | None = None,
) -> list[TaskCellAggregate]:
    """One `TaskCellAggregate` per cell of `sched`'s matrix, plus any extras.

    "Extras" are (task, arm) pairs found in `trials` that the schedule does
    not plan -- a task run before it was declared, or one run ad hoc. They are
    emitted with `in_schedule=False` and no complexity label, because dropping
    real measurements would be data loss and inventing a complexity band for
    them would be worse.

    Ordered by complexity band (low -> high), then by `schedule.yaml`'s own
    declaration order within a band, with the unlabelled extras last. Step 4
    plots complexity as an ordered axis, so emitting them already in that
    order means the renderer never has to decide where an unlabelled task goes.
    """
    known_tasks = [task.name for task in sched.tasks]
    trials_by_cell, reconciliation = group_trials_by_task_and_arm(trials, known_tasks)
    state = scheduler_state or {}

    claimed: set[tuple[str, str]] = set()
    planned_cells = [
        _planned_cell(planned, sched.models, trials_by_cell, state, claimed)
        for planned in schedule.expand_schedule(sched)
    ]
    # Stable sort: within one complexity band, `expand_schedule`'s declaration
    # order survives untouched.
    planned_cells.sort(key=lambda cell: cell.complexity_rank)

    return planned_cells + _unscheduled_cells(sched, trials_by_cell, state, claimed)


def group_trials_by_task_and_arm(
    trials: list[TrialRecord], known_tasks: Sequence[str]
) -> tuple[dict[tuple[str, str], list[TrialRecord]], dict[str, dict[str, str | None]]]:
    """Bucket trials by (reconciled task name, arm id), preserving input order.

    Also returns the reconciliation audit trail: raw spelling -> what it
    resolved to and by which rule. A trial whose task cannot be determined at
    all is recorded there and then dropped from the buckets -- it cannot be
    attributed to any cell without guessing, and a guess here is a wrong number
    on a chart rather than a visible gap.
    """
    buckets: dict[tuple[str, str], list[TrialRecord]] = {}
    reconciliation: dict[str, dict[str, str | None]] = {}

    for trial in trials:
        raw = trial.task_name or trial.trial_id
        resolved, method = resolve_trial_task_name(trial, known_tasks)
        reconciliation[raw] = {"resolved": resolved, "method": method}
        if resolved is None:
            continue
        buckets.setdefault((resolved, trial.arm_id), []).append(trial)

    return buckets, reconciliation


def _planned_cell(
    planned: schedule.PlannedRun,
    models: Sequence[schedule.ScheduledModel],
    trials_by_cell: dict[tuple[str, str], list[TrialRecord]],
    scheduler_state: dict[str, dict],
    claimed: set[tuple[str, str]],
) -> TaskCellAggregate:
    """Build one cell of the declared matrix, claiming the trials it owns.

    A structurally impossible cell claims NOTHING, and `claimed` is how that is
    enforced: it shares its (task, arm_id) key with the symmetric model's cell,
    so letting it read that key would attribute one measurement to two cells
    and double-count it in every chart downstream.
    """
    structural = cell_is_structurally_impossible(planned.model, planned.skill)
    key = (planned.task.name, planned.arm_id)

    if structural:
        cell_trials: list[TrialRecord] = []
    else:
        cell_trials = trials_by_cell.get(key, [])
        claimed.add(key)

    return _build_cell(
        task=planned.task.name,
        model=planned.model,
        model_name=planned.model.name,
        skill=planned.skill,
        complexity=planned.task.complexity,
        arm_id=planned.arm_id,
        in_schedule=True,
        structural=structural,
        skip_reason=planned.skip_reason,
        trials=cell_trials,
        models=models,
        scheduler_entry=scheduler_state.get(
            scheduler_state_key(planned.task.name, planned.model.name, planned.skill)
        ),
    )


def _unscheduled_cells(
    sched: schedule.Schedule,
    trials_by_cell: dict[tuple[str, str], list[TrialRecord]],
    scheduler_state: dict[str, dict],
    claimed: set[tuple[str, str]],
) -> list[TaskCellAggregate]:
    """Cells for measurements the schedule does not plan, in first-seen order."""
    declared = {task.name for task in sched.tasks}
    cells: list[TaskCellAggregate] = []

    for (task, arm_id), cell_trials in trials_by_cell.items():
        if (task, arm_id) in claimed:
            continue

        first = cell_trials[0]
        skill = first.skill or schedule.VANILLA_SKILL
        model = scheduled_model_for_tiers(sched.models, first.orchestrator, first.impl, skill)
        cells.append(
            _build_cell(
                task=task,
                model=model,
                # A tier pair the schedule does not declare has no name there,
                # so the tiers themselves are the honest label.
                model_name=model.name if model else _tier_pair_label(first.orchestrator, first.impl),
                skill=skill,
                # `schedule.yaml` is the only source of complexity. A task it
                # does not declare has none -- not a guessed one.
                complexity=sched.complexity_of(task) if task in declared else None,
                arm_id=arm_id,
                in_schedule=False,
                structural=False,
                skip_reason=None,
                trials=cell_trials,
                models=sched.models,
                scheduler_entry=None,
            )
        )

    return cells


def _tier_pair_label(orchestrator: str, impl: str | None) -> str:
    """A readable model label for a tier pair `schedule.yaml` does not name."""
    return orchestrator if impl is None else f"{orchestrator}-{impl}"


def _build_cell(
    *,
    task: str,
    model: schedule.ScheduledModel | None,
    model_name: str,
    skill: str,
    complexity: str | None,
    arm_id: str,
    in_schedule: bool,
    structural: bool,
    skip_reason: str | None,
    trials: list[TrialRecord],
    models: Sequence[schedule.ScheduledModel],
    scheduler_entry: dict | None,
) -> TaskCellAggregate:
    """Assemble one cell: decide its state, then attach exactly one of the two
    mutually exclusive payloads.
    """
    attempts = [trial for trial in trials if trial.status != "errored"]
    measurement = _cell_measurement(attempts) if attempts and not structural else None
    absence = (
        None
        if measurement is not None
        else _cell_absence(
            structural=structural,
            skip_reason=skip_reason,
            trials=trials,
            scheduler_entry=scheduler_entry,
            model=model,
            models=models,
            arm_id=arm_id,
        )
    )
    entry = scheduler_entry or {}

    return TaskCellAggregate(
        task=task,
        model=model_name,
        skill=skill,
        complexity=complexity,
        complexity_rank=schedule.complexity_rank(complexity) if complexity else None,
        arm_id=arm_id,
        in_schedule=in_schedule,
        state=_cell_state(measurement, structural, skip_reason, trials, scheduler_entry),
        measured=measurement,
        absence=absence,
        schedule_skip_reason=skip_reason,
        scheduler_outcome=entry.get("outcome"),
        scheduler_reason=entry.get("reason"),
        scheduler_attempts=entry.get("attempts"),
        n_trials_seen=len(trials),
        n_errored_trials=len(trials) - len(attempts),
        trial_ids=tuple(trial.trial_id for trial in trials),
    )


def _cell_state(
    measurement: CellMeasurement | None,
    structural: bool,
    skip_reason: str | None,
    trials: list[TrialRecord],
    scheduler_entry: dict | None,
) -> CellState:
    """Which of the five states this cell is in. First match wins.

    The order encodes two judgement calls worth stating out loud.

    STRUCTURAL BEATS EVERYTHING, because it is a fact about the matrix rather
    than about this run: there is no such trial to have, so no evidence can
    make the cell measurable.

    A DELIBERATE SKIP BEATS a technical failure, because the schedule's
    declaration is why the cell has no measurement going forward, and a stale
    errored trial from some earlier run should not overwrite the operator's
    stated reason with an infrastructure story. The errored trials stay
    visible either way in `n_errored_trials`.
    """
    if structural:
        return "structurally_impossible"
    if measurement is not None:
        return "measured"
    if skip_reason:
        return "deliberately_skipped"
    if trials:
        return "technical_failure"
    if (scheduler_entry or {}).get("outcome") == SCHEDULER_TECHNICAL_FAILURE_OUTCOME:
        return "technical_failure"
    return "not_yet_run"


def _cell_measurement(attempts: list[TrialRecord]) -> CellMeasurement:
    """The numbers for a cell with at least one fair attempt.

    Denominator and exclusions match `aggregate_arm` exactly -- see the module
    docstring's "PASS@1 DENOMINATOR" section -- so a per-cell rate and a
    per-arm rate mean the same thing and can be read side by side.

    WHY A ONE-ATTEMPT CELL GETS NO INTERVAL
    ----------------------------------------
    `wilson_score_interval(1, 1)` is perfectly well defined -- (0.207, 1.0) --
    and perfectly useless: it is an error bar 79 points wide drawn over a
    single coin flip. That alone would be a judgement call. What makes it a
    correctness problem is the FIELD NAMES: an `ArmAggregate` pooling dozens of
    trials publishes its interval as `pass_at_1_ci_low`/`_high` too, so a
    renderer reading those two keys cannot tell one observation from thirty.
    `schedule.yaml` plans exactly one trial per (task, model, skill), so that
    is not an edge case here -- it is nearly every cell in the file.

    This module already refuses to let an incomparable interval sit in the
    local field names on the Fable 5 side (`_baseline_rate` hardcodes
    `comparable_to_local_wilson_interval: False`); the same rule has to hold
    locally. So the bounds are `None` below n=2 and `is_single_trial` says so
    outright, leaving the integer counts -- which are the honest record of what
    happened -- as what a renderer draws instead.
    """
    resolved = [trial for trial in attempts if trial.status == "resolved"]
    # One derived fact, computed once: the flag and the presence of bounds are
    # two statements of the same condition and must not be able to disagree.
    is_single_trial = len(attempts) < 2
    ci_low, ci_high = (
        (None, None) if is_single_trial else wilson_score_interval(len(resolved), len(attempts))
    )

    return CellMeasurement(
        n_resolved=len(resolved),
        n_unresolved=sum(1 for trial in attempts if trial.status == "unresolved"),
        n_incomplete=sum(1 for trial in attempts if trial.status == "incomplete"),
        n_attempts=len(attempts),
        pass_at_1=len(resolved) / len(attempts),
        is_single_trial=is_single_trial,
        pass_at_1_ci_low=ci_low,
        pass_at_1_ci_high=ci_high,
        pass_at_1_interval_type=LOCAL_PASS_AT_1_INTERVAL_TYPE,
        pass_at_1_denominator_unit=LOCAL_PASS_AT_1_DENOMINATOR_UNIT,
        total_cost_usd=sum_or_none([trial.cost_usd for trial in attempts]),
        avg_cost_usd=mean_or_none([trial.cost_usd for trial in attempts]),
        max_cost_usd=max_or_none([trial.cost_usd for trial in attempts]),
        total_output_tokens=sum_or_none([trial.output_tokens for trial in attempts]),
        avg_output_tokens=mean_or_none([trial.output_tokens for trial in attempts]),
        total_input_tokens=sum_or_none([trial.input_tokens for trial in attempts]),
        avg_input_tokens=mean_or_none([trial.input_tokens for trial in attempts]),
        total_cache_tokens=sum_or_none([trial.cache_tokens for trial in attempts]),
        avg_cache_tokens=mean_or_none([trial.cache_tokens for trial in attempts]),
        avg_n_agent_steps=mean_or_none([trial.n_agent_steps for trial in attempts]),
    )


def _cell_absence(
    *,
    structural: bool,
    skip_reason: str | None,
    trials: list[TrialRecord],
    scheduler_entry: dict | None,
    model: schedule.ScheduledModel | None,
    models: Sequence[schedule.ScheduledModel],
    arm_id: str,
) -> CellAbsence:
    """Why this cell has no measurement, in the same order `_cell_state` decides.

    Every branch names a `source` a reader can go and check, because "no data"
    with no provenance is the thing this vocabulary was built to replace.
    """
    if structural:
        collapse = vanilla_collapse_target(models, model) if model else None
        return CellAbsence(
            reason=skip_reason
            or (
                "A vanilla arm has no implementer tier, so this cell is the same "
                f"trial as the symmetric model's vanilla cell ({arm_id})."
            ),
            source="schedule.yaml + arm_id collapse (schedule.arm_id_for)",
            collapses_onto_model=collapse.name if collapse else None,
        )

    if skip_reason:
        return CellAbsence(reason=skip_reason, source="schedule.yaml", collapses_onto_model=None)

    if trials:
        causes = sorted({trial.error_reason or "unknown" for trial in trials})
        return CellAbsence(
            reason=(
                f"All {len(trials)} recorded trial(s) were infrastructure failures "
                f"({', '.join(causes)}), so the agent never got a fair attempt at this task."
            ),
            source="trial_records",
            collapses_onto_model=None,
        )

    return _scheduler_absence(scheduler_entry) or CellAbsence(
        reason="No trial result recorded under runs/, and no scheduler record for this cell.",
        source="no_data",
        collapses_onto_model=None,
    )


def _scheduler_absence(scheduler_entry: dict | None) -> CellAbsence | None:
    """What `scheduler-state.json` has to say about an unmeasured cell, if anything.

    Two different things it can say, and they are NOT the same absence:

    A `technical_failure` means the cell never got a fair attempt -- the state
    `_cell_state` labels it with.

    A `success` or `model_failure` means the agent DID get a fair shot, so
    neither maps onto a technical failure. If we are here at all, the cell has
    no trial output despite having been settled: that is missing data, and it
    is described as missing rather than quietly relabelled as unrun.
    """
    entry = scheduler_entry or {}
    outcome = entry.get("outcome")
    if not outcome:
        return None

    if outcome == SCHEDULER_TECHNICAL_FAILURE_OUTCOME:
        reason = (
            f"The scheduler recorded this cell as {outcome!r} after "
            f"{entry.get('attempts')} attempt(s): {entry.get('reason')}."
        )
    else:
        reason = (
            f"No trial result was found under runs/ for this cell, although the "
            f"scheduler recorded it as {outcome!r} ({entry.get('reason')}) -- its "
            "trial output is missing rather than never produced."
        )

    return CellAbsence(
        reason=reason, source=f"runs/{SCHEDULER_STATE_FILENAME}", collapses_onto_model=None
    )


# --------------------------------------------------------------------------
# The DeepSWE Fable 5 baseline (pure, independently testable)
#
# WHY MERGING A SNAPSHOT NEEDED THIS MUCH CARE
# ---------------------------------------------
# Every number in `data/fable5_official.json` is ALMOST comparable to a local
# one, and each near-miss is a way to publish a false claim without writing a
# single wrong digit:
#
#   * Its pass@1 denominator is scored rollout ATTEMPTS -- 113 tasks x 4
#     whole-benchmark passes, minus exclusions -- not tasks, and not this
#     harness's per-cell attempt count either.
#   * Its interval is a run-to-run standard error across those 4 passes. This
#     harness plots a Wilson binomial interval. Drawing them as peer error
#     bars asserts something neither statistic supports.
#   * Its per-task results are k-of-n counts over 20 attempts, so a bare
#     `0.65` reads as a precision the figure does not have.
#   * It ran on mini-swe-agent, not claude-code. It is tier-placement
#     context, not a like-for-like baseline -- the same disclosure report.py
#     already makes for `data/leaderboard.json`.
#
# So provenance is attached to each NUMBER rather than stated once in prose:
# every rate below is a `_baseline_rate` carrying its numerator, its
# denominator, what that denominator counts, which interval statistic (if
# any) applies, and an explicit `comparable_to_local_wilson_interval: false`.
# A docstring cannot stop a chart; a field a renderer has to read can.
#
# NOTHING IS COMPUTED THAT THE SNAPSHOT DOES NOT PUBLISH, with exactly one
# exception -- `mean_cost_usd_as_fraction_of_headline`, a division of two
# published figures -- and that one is listed in `derived_fields` so it can
# never be mistaken for a transcribed number.
# --------------------------------------------------------------------------


def _baseline_rate(
    value: float | None,
    numerator: int | None,
    denominator: int | None,
    denominator_unit: str,
    *,
    interval_low: float | None = None,
    interval_high: float | None = None,
    interval_type: str | None = None,
    interval_n_runs: int | None = None,
) -> dict[str, Any]:
    """One published rate, inseparable from what it is a rate OF.

    The interval fields are always present and are `None` where DeepSWE
    publishes no interval -- an explicit "not published" rather than a missing
    key some consumer will default. `comparable_to_local_wilson_interval` is
    hardcoded False because it is false for every rate in this file: a
    run-to-run SE across whole-benchmark passes and a Wilson interval over one
    cell's attempts are different statistics over different populations.
    """
    return {
        "value": value,
        "n_numerator": numerator,
        "n_denominator": denominator,
        "denominator_unit": denominator_unit,
        "interval_low": interval_low,
        "interval_high": interval_high,
        "interval_type": interval_type,
        "interval_n_runs": interval_n_runs,
        "comparable_to_local_wilson_interval": False,
    }


def _note_starting_with(notes: Sequence[str], prefix: str) -> str | None:
    """The snapshot's own note on one subject, verbatim.

    The notes are carried word-for-word rather than paraphrased: they are the
    publisher's statement of what their numbers do and do not support, and a
    summary of a caveat is a weaker caveat.
    """
    return next((note for note in notes if note.startswith(prefix)), None)


def _fable5_effort_block(effort: dict[str, Any]) -> dict[str, Any]:
    """One reasoning-effort configuration's aggregate figures."""
    return {
        "reasoning_effort": effort.get("reasoning_effort"),
        "config": effort.get("config"),
        "pass_at_1": _baseline_rate(
            effort.get("pass_at_1"),
            effort.get("n_passed"),
            effort.get("n_attempted_scored") or effort.get("n_attempted"),
            FABLE5_ATTEMPT_DENOMINATOR_UNIT,
            interval_low=effort.get("ci_lo"),
            interval_high=effort.get("ci_hi"),
            interval_type=FABLE5_INTERVAL_TYPE,
            interval_n_runs=effort.get("n_runs"),
        ),
        # pass@4's denominator is TASKS, not attempts. DeepSWE's own metric
        # definition calls the two "NOT comparable"; the differing
        # `denominator_unit` is how a renderer can tell without reading prose.
        "pass_at_4": _baseline_rate(
            effort.get("pass_at_4"),
            effort.get("n_tasks_passed_any"),
            effort.get("n_tasks_attempted"),
            FABLE5_TASK_DENOMINATOR_UNIT,
        ),
        "mean_cost_usd": effort.get("mean_cost_usd"),
        "median_cost_usd": effort.get("median_cost_usd"),
        "mean_output_tokens": effort.get("mean_output_tokens"),
        "mean_input_tokens": effort.get("mean_input_tokens"),
        "mean_agent_steps": effort.get("mean_agent_steps"),
    }


def _fable5_per_task_block(task: dict[str, Any]) -> dict[str, Any]:
    """One task's published figures, as k-of-n counts.

    Both blocks are pass rates over ATTEMPTS -- 20 pooled across the five
    reasoning efforts, 4 at the headline `max` effort -- so both carry their
    counts. DeepSWE publishes no per-task confidence interval at any effort,
    so every interval field here is explicitly null: an error bar drawn on
    these would be fabricated.
    """
    pooled = task.get("all_efforts_pooled") or {}
    at_max = task.get("headline_config_max") or {}

    return {
        "task_title": task.get("task_title"),
        "task_url": task.get("task_url"),
        "present_on_site": task.get("present_on_site"),
        "all_efforts_pooled": {
            "pass_at_1": _baseline_rate(
                pooled.get("pass_rate"),
                pooled.get("n_passed"),
                pooled.get("n_attempted"),
                FABLE5_ATTEMPT_DENOMINATOR_UNIT,
            ),
            "mean_cost_usd": pooled.get("mean_cost_usd"),
            "mean_output_tokens": pooled.get("mean_output_tokens"),
            "mean_agent_steps": pooled.get("mean_agent_steps"),
            "source": pooled.get("source"),
        },
        "headline_config_max": {
            "pass_at_1": _baseline_rate(
                at_max.get("pass_rate"),
                at_max.get("n_passed"),
                at_max.get("n_scored"),
                FABLE5_ATTEMPT_DENOMINATOR_UNIT,
            ),
            "mean_cost_usd": at_max.get("mean_cost_usd"),
            "mean_output_tokens": at_max.get("mean_output_tokens"),
            "mean_agent_steps": at_max.get("mean_agent_steps"),
        },
    }


def _fable5_best_scoring_effort(
    efforts: dict[str, Any], headline: dict[str, Any]
) -> dict[str, Any] | None:
    """The highest-SCORING configuration, beside the site's highest-EFFORT one.

    The site's default view collapses each model to one row by taking the
    highest available reasoning effort, not the best-scoring one -- so Fable
    5's headline is `max` (0.6972) even though `xhigh` scores 0.6991 for
    roughly 62% of the cost. A report quoting only the headline understates
    the model, so both are carried and the comparison is made explicit.
    """
    scored = [effort for effort in efforts.values() if effort.get("pass_at_1") is not None]
    if not scored:
        return None

    best = max(scored, key=lambda effort: effort["pass_at_1"])
    block = _fable5_effort_block(best)

    headline_cost = headline.get("mean_cost_usd")
    best_cost = best.get("mean_cost_usd")
    block["outscores_headline"] = best["pass_at_1"] > (headline.get("pass_at_1") or 0)
    block["mean_cost_usd_as_fraction_of_headline"] = (
        best_cost / headline_cost if headline_cost and best_cost is not None else None
    )
    # The only figure in this whole payload DeepSWE does not publish outright.
    block["derived_fields"] = [
        "mean_cost_usd_as_fraction_of_headline",
        "outscores_headline",
    ]
    return block


def build_fable5_baseline(document: object) -> dict[str, Any]:
    """Merge the vendored DeepSWE snapshot into results.json's `baseline` shape.

    Pure: takes an already-parsed document so every honesty property above is
    testable without touching the filesystem (`load_fable5_baseline` is the
    I/O half). A document missing the aggregate block yields
    `{"available": False, ...}` and NO numbers -- a partial baseline that
    looked whole would be the worst outcome available here.

    Per-task blocks are keyed by DeepSWE's task ids, which are the same
    strings `schedule.yaml` uses, so a consumer can join them to
    `results.json`'s `cells` on `task` directly.
    """
    if not isinstance(document, dict):
        return {"available": False, "reason": "snapshot is not a JSON object"}

    aggregate = document.get("aggregate") or {}
    headline = aggregate.get("headline") or {}
    if not headline:
        return {"available": False, "reason": "snapshot carries no aggregate headline row"}

    source = document.get("source") or {}
    metric = document.get("metric_definition") or {}
    model = document.get("model") or {}
    notes = [note for note in document.get("notes") or [] if isinstance(note, str)]

    return {
        "available": True,
        "source": _fable5_source_block(document, source),
        "model": _fable5_model_block(model),
        "comparability": _fable5_comparability(metric, source, notes),
        "aggregate": {
            "headline": _fable5_effort_block(headline),
            "best_scoring_effort": _fable5_best_scoring_effort(
                aggregate.get("all_reasoning_efforts") or {}, headline
            ),
            "row_selection_rule": metric.get("row_selection_rule_for_displayed_number"),
            "rank": aggregate.get("rank"),
            "trial_completeness": aggregate.get("trial_completeness"),
        },
        "per_task": {
            name: _fable5_per_task_block(task)
            for name, task in (document.get("per_task") or {}).items()
        },
        "not_published": [
            note
            for note in (
                _note_starting_with(notes, "NOT AVAILABLE"),
                _note_starting_with(notes, "The site publishes no per-task"),
                model.get("note"),
            )
            if note
        ],
        "notes": notes,
    }


def _fable5_source_block(document: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Where these numbers came from and when -- carried so they can be re-checked.

    `artifact_generated_at` matters more than it looks: DeepSWE regenerates
    its artifacts as new jobs land, so a figure quoted months later may no
    longer be the published one. The snapshot's own note says to re-check it
    before reuse, which is only possible if it travels with the data.
    """
    return {
        "name": source.get("name"),
        "site": source.get("site"),
        "dataset_version": source.get("dataset_version"),
        "harness": source.get("harness"),
        "harness_url": source.get("harness_url"),
        "n_tasks_in_set": source.get("n_tasks_in_set"),
        "artifact_generated_at": source.get("artifact_generated_at"),
        "retrieved_date": document.get("retrieved_date"),
        "fetched_from": document.get("fetched_from"),
    }


def _fable5_model_block(model: dict[str, Any]) -> dict[str, Any]:
    """Which model the baseline figures describe, and how precisely it is known.

    `api_model_id` is null on purpose: the site publishes only the short id
    `claude-fable-5`, so a dated API string would have to be reconstructed
    from a plausible-looking guess. The publisher's own explanation is carried
    beside the null so the gap reads as recorded rather than overlooked.
    """
    return {
        "site_model_id": model.get("site_model_id"),
        "display_name": model.get("display_name_on_site"),
        "provider": model.get("provider_used_by_deepswe"),
        "api_model_id": None,
        "api_model_id_note": model.get("note"),
    }


def _fable5_comparability(
    metric: dict[str, Any], source: dict[str, Any], notes: Sequence[str]
) -> dict[str, Any]:
    """The one block a renderer must read before drawing Fable 5 beside a local arm.

    Every field here is a refusal of a specific comparison a chart might
    otherwise make: same harness, same denominator, same kind of error bar.
    All three are false, and each is stated as a boolean or a named string
    rather than only as prose, so the refusal is machine-readable.
    """
    return {
        "like_for_like": False,
        "co_plotting_intervals_allowed": False,
        "baseline_harness": source.get("harness"),
        "local_harness": "claude-code",
        "baseline_interval_type": FABLE5_INTERVAL_TYPE,
        "local_interval_type": LOCAL_PASS_AT_1_INTERVAL_TYPE,
        "baseline_denominator_unit": FABLE5_ATTEMPT_DENOMINATOR_UNIT,
        "local_denominator_unit": LOCAL_PASS_AT_1_DENOMINATOR_UNIT,
        "denominator_note": metric.get("denominator"),
        "interval_note": metric.get("ci_caveat"),
        "harness_note": _note_starting_with(notes, "HARNESS MISMATCH"),
        "headline_metric": metric.get("headline_metric"),
        "failure_accounting": metric.get("failure_accounting"),
        "grading": metric.get("grading"),
    }


def load_fable5_baseline(path: Path = DEFAULT_FABLE5_BASELINE_PATH) -> dict[str, Any]:
    """Read and merge the vendored snapshot; `available: False` if it is not there.

    A missing or unreadable snapshot yields an explicitly unavailable baseline
    carrying no figures at all, never a placeholder one -- the same call
    report.py already makes for `data/leaderboard.json`. A report with no
    official bar is honest; a report with an invented one is not.
    """
    document = load_json_or_none(path)
    if document is None:
        return {"available": False, "reason": f"no readable snapshot at {path}"}
    return build_fable5_baseline(document)


# --------------------------------------------------------------------------
# Output writers
# --------------------------------------------------------------------------


def write_results_json(
    path: Path,
    trials: list[TrialRecord],
    arms: list[ArmAggregate],
    *,
    cells: list[TaskCellAggregate] | None = None,
    schedule_summary: dict[str, Any] | None = None,
    baseline: dict[str, Any] | None = None,
) -> None:
    """Write results.json. The additive `cells`/`schedule`/`baseline` sections
    are keyword-only and default to an explicitly-absent shape, so a caller
    that only has trials and arms (an older test, a partial rebuild) still
    produces a well-formed file rather than one whose new keys are missing
    entirely.

    `cell_state_vocabulary` and `interval_types` are emitted alongside the
    data they describe. They cost a few hundred bytes and remove the need for
    any consumer to infer what `structurally_impossible` means, or to discover
    from prose that two intervals in this file are different statistics.
    """
    payload = {
        "schema_version": RESULTS_SCHEMA_VERSION,
        "trials": [asdict(t) for t in trials],
        "arms": [asdict(a) for a in arms],
        "cells": [asdict(cell) for cell in cells or []],
        "cell_state_vocabulary": CELL_STATE_DESCRIPTIONS,
        "interval_types": INTERVAL_TYPE_DESCRIPTIONS,
        "schedule": schedule_summary or {"available": False, "reason": "not collected"},
        "baseline": {"fable5": baseline or {"available": False, "reason": "not collected"}},
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def task_name_reconciliation(
    trials: list[TrialRecord], known_tasks: Sequence[str]
) -> dict[str, dict[str, str | None]]:
    """The raw-spelling -> resolved-name audit trail, for results.json.

    Delegates to `group_trials_by_task_and_arm` rather than repeating the
    reconciliation loop, so the mapping recorded in the file is by
    construction the same one the cells were built from.
    """
    _, reconciliation = group_trials_by_task_and_arm(trials, known_tasks)
    return reconciliation


def collect_task_cells(
    schedule_path: Path, runs_dir: Path, trials: list[TrialRecord]
) -> tuple[list[TaskCellAggregate], dict[str, Any]]:
    """Impure counterpart of `build_task_cells`: load the schedule and the
    scheduler's state file, then build the cells and describe where they came
    from.

    An unloadable schedule is reported and skipped, not raised: the per-arm
    results are already collected by this point and are perfectly valid
    without the per-cell layer, so taking the whole run down over a config
    file would discard good data to report a bad one. The schedule section
    then says `available: false` with the parser's own message, which is what
    lets a report state that the matrix is unknown rather than draw an empty
    one and imply the cells are empty.
    """
    try:
        sched = schedule.load_schedule(schedule_path)
    except schedule.ScheduleError as error:
        print(f"[collect] WARNING: no per-task cells -- {error}", file=sys.stderr)
        return [], {"available": False, "reason": str(error), "source_path": str(schedule_path)}

    scheduler_state = load_scheduler_state(runs_dir)
    cells = build_task_cells(sched, trials, scheduler_state=scheduler_state)
    summary = {
        "available": True,
        "source_path": str(schedule_path),
        "complexity_levels": list(schedule.COMPLEXITY_LEVELS),
        "vanilla_skill": schedule.VANILLA_SKILL,
        "tasks": [
            {
                "name": task.name,
                "complexity": task.complexity,
                "complexity_rank": schedule.complexity_rank(task.complexity),
            }
            for task in sched.tasks
        ],
        "models": [
            {"name": model.name, "orchestrator": model.orchestrator, "impl": model.impl}
            for model in sched.models
        ],
        "skills": list(sched.skills),
        "n_planned_cells": len(sched.tasks) * len(sched.models) * len(sched.skills),
        "scheduler_state_path": str(runs_dir / SCHEDULER_STATE_FILENAME),
        "scheduler_state_available": bool(scheduler_state),
        "task_name_reconciliation": task_name_reconciliation(
            trials, [task.name for task in sched.tasks]
        ),
    }
    return cells, summary


def write_results_csv(path: Path, trials: list[TrialRecord]) -> None:
    """One row per trial. Field order matches TrialRecord's declaration order."""
    fieldnames = [f.name for f in fields(TrialRecord)]
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for trial in trials:
            writer.writerow(asdict(trial))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate pier's runs/ tree into results.json + results.csv."
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=SCRIPT_DIR / "runs",
        help="Root pier wrote job/trial output under (default: %(default)s).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=SCRIPT_DIR,
        help="Directory to write results.json/results.csv into (default: %(default)s).",
    )
    parser.add_argument(
        "--schedule",
        type=Path,
        default=schedule.DEFAULT_SCHEDULE_PATH,
        help="Schedule file the per-task cells are built against (default: "
        "%(default)s). Same flag and same default as run.py --mode scheduled: "
        "the matrix, its complexity labels and its deliberate skips are read "
        "from here and nowhere else.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_FABLE5_BASELINE_PATH,
        help="Vendored DeepSWE Fable 5 snapshot to merge (default: %(default)s). "
        "It is mini-swe-agent tier-placement context, not a like-for-like "
        "baseline; see collect.py's baseline section.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    trials = collect_trial_records(args.runs_dir)
    run_metadata = load_arm_run_metadata(args.runs_dir)
    arms = aggregate_all_arms(trials, run_metadata)
    cells, schedule_summary = collect_task_cells(args.schedule, args.runs_dir, trials)
    baseline = load_fable5_baseline(args.baseline)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_results_json(
        args.out_dir / "results.json",
        trials,
        arms,
        cells=cells,
        schedule_summary=schedule_summary,
        baseline=baseline,
    )
    write_results_csv(args.out_dir / "results.csv", trials)

    n_errored = sum(1 for t in trials if t.status == "errored")
    n_incomplete = sum(1 for t in trials if t.status == "incomplete")
    n_measured = sum(1 for cell in cells if cell.state == "measured")
    print(
        f"[collect] wrote {len(trials)} trial records "
        f"({n_errored} errored, {n_incomplete} incomplete) "
        f"across {len(arms)} arms to {args.out_dir}"
    )
    # The empty cells are the point, so they are counted out loud: a sweep
    # that has measured 4 of 45 cells should never read as a finished one.
    print(
        f"[collect] {n_measured} of {len(cells)} (task, model, skill) cells measured; "
        f"{len(cells) - n_measured} absent -- see results.json cell_state_vocabulary"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
