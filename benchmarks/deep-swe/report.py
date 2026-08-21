#!/usr/bin/env python3
"""Deep-SWE benchmark report generator -- turns collect.py's `results.json`
(plus the vendored `data/leaderboard.json` snapshot) into a single
self-contained `report.html`: two grouped-bar-chart comparisons, an
Pass@1/cost/token/step table (one row per arm), and a run-metadata header.

SELF-CONTAINED IS A HARD CONSTRAINT
------------------------------------
Every chart is inline SVG built by hand below; every style rule lives in one
<style> block; there is no CDN script, no external stylesheet, no charting
library. The output file must render correctly opened directly from disk
with the network disconnected. See `build_report_html`'s assembly for the
full page skeleton.

WHY THIS FILE DOES NOT IMPORT `run.py` OR `agent.py`
-------------------------------------------------------
Same reason as collect.py (see its module docstring): both transitively
`import pier`, which is only installed in the dedicated pier venv, not the
plain interpreter this script (and Step 5's unit tests) run under. Unlike
`run.py`/`agent.py`, `collect.py` itself has no pier dependency -- but this
file still doesn't import it, because nothing here needs its Wilson-CI or
status-classification logic: `results.json`'s `arms` already carry
precomputed `pass_at_1_ci_low`/`_high`, so there is no computation left to
share, only a couple of small constants (schema version) not worth a
cross-file coupling for.

THE OFFICIAL-BASELINE BARS ARE DELIBERATELY NOT A NORMAL DATA SERIES
------------------------------------------------------------------------
Every "official" bar comes from `data/leaderboard.json` (a vendored snapshot
of https://deepswe.datacurve.ai/), which benchmarks models with
mini-swe-agent -- a different agent scaffold than the claude-code + sadd
plugin arms this harness measures. Treating that number as just another bar
in the same categorical palette would imply a like-for-like comparison that
isn't true. So official bars get their own visual language everywhere they
appear: unfilled (stroke only, no categorical hue), no whisker (its CI is
DeepSWE's own run-to-run standard error, not a Wilson interval, so it is
printed as labelled text on the bar instead of drawn into the same whisker
channel as this harness's own Wilson bounds), plus a footnote sourced from
leaderboard.json's own `honesty_note`/`snapshot_date`/`source_url` fields
(never hand-duplicated text) explaining why. See `_official_bar`,
`render_bar_mark`, and `render_official_baseline_footnote`.

THREE OUTCOMES, NOT TWO
--------------------------
`collect.py` classifies every trial `resolved` / `unresolved` / `incomplete` /
`errored`, and this file must keep the last two apart everywhere it shows
them. `incomplete` is a trial the agent abandoned (no `artifacts/model.patch`,
or a final message that ends in a question asked of an operator who was never
there); it counts as a failed attempt inside Pass@1. `errored` is a trial the
infrastructure lost, and it is excluded from Pass@1 entirely. Summing them
into one "problems" column would merge a denominator-included number with a
denominator-excluded one, so the arm table carries a separate column for each.

NULL-HANDLING PHILOSOPHY
---------------------------
`collect.py` already decided that a zero-attempt arm reports `pass_at_1` (and
every `avg_*`/CI field) as JSON `null`, not `0.0` -- see its "PASS@1
DENOMINATOR" docstring section. This file's only job is to never launder
that `null` back into a number: `_arm_bar`/`_official_bar` both normalize
"no data" (arm absent, arm present but valueless, or tier missing from the
leaderboard) into the same `Bar(present=False, ...)`, and every renderer
skips drawing a bar/whisker/label for `present=False` rather than drawing a
misleading zero-height mark. See `Bar`'s docstring for the contract.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_PATH = SCRIPT_DIR / "results.json"
DEFAULT_LEADERBOARD_PATH = SCRIPT_DIR / "data" / "leaderboard.json"
DEFAULT_OUT_PATH = SCRIPT_DIR / "report.html"

# Mirrors collect.py's RESULTS_SCHEMA_VERSION -- duplicated as a single int
# rather than imported (see module docstring's "WHY THIS FILE DOES NOT
# IMPORT" section): a version-mismatch warning is a nicety, not worth a
# cross-file coupling for one constant.
#
# v2 is also the line `summarize_run_metadata` uses to decide whether an
# arm dict can even carry "created_at"/"sample_seed" keys at all -- a v1
# results.json (from a collect.py older than this change) never wrote them,
# which is different from a v2 arm recording them as `null` (see that
# function's docstring). That floor stays at 2 even though the expected
# version has moved on: v3 did not change those two fields.
#
# v3 added collect.py's third trial outcome, `incomplete` (a trial the agent
# abandoned -- no `artifacts/model.patch`, or a final message that ends in a
# question), plus the `n_incomplete` and `max_cost_usd` arm fields this file
# renders in the arm table. Reading a v2 file with this script leaves both
# columns missing rather than wrong, hence a warning and not a hard failure.
EXPECTED_RESULTS_SCHEMA_VERSION = 4
MIN_SCHEMA_VERSION_WITH_RUN_METADATA = 2

# Ordinal capability order -- fixed, not alphabetical (alphabetical would
# print "haiku, opus, sonnet", scrambling the reader's mental model of
# ascending model capability). Every chart/group iterates in this order.
TIER_ORDER: tuple[str, ...] = ("haiku", "sonnet", "opus")

# --- The per-cell absence vocabulary -------------------------------------
#
# `collect.py` classifies every (task, model, skill) cell into one of five
# states and documents them in results.json's own `cell_state_vocabulary`.
# Exactly one of them carries numbers; the report's job is to keep the other
# four visually distinct from each other AND from a measured zero.
#
# WHY "CANNOT" IS DRAWN LOUDLY AND "NOT YET RUN" IS DRAWN FAINTLY
# ----------------------------------------------------------------
# The three "cannot" states are findings -- a stated exclusion, a trial that
# cannot exist, an attempt the infrastructure lost -- and leaving a finding
# blank is how a report accidentally reports "no result" for a decision
# somebody made deliberately. Those get a full-height hatched slot and a
# glyph.
#
# `not_yet_run` carries no finding, so it gets the least ink that can still
# be seen: one small dot ON the baseline. Not zero ink, which was the earlier
# design and was wrong twice over -- the legend advertises a swatch for the
# state, and a legend entry with nothing on the chart to match is a promise
# the chart does not keep; and a printed or greyscale chart could not then
# distinguish "awaiting a run" from an empty page. The dot sits exactly on
# the baseline, where the axis already draws ink, so it cannot be read off
# the y scale as a quantity.
MEASURED_STATE = "measured"
NOT_YET_RUN_STATE = "not_yet_run"

# A sixth state, produced by this report and never by `collect.py`: a chart
# or table slot that no run was ever planned for.
#
# It is deliberately NOT `not_yet_run`. That state's own published definition
# is "runnable and simply has not been run", which is a promise about a cell
# that IS in the plan; borrowing it for a combination nobody scheduled states
# the opposite of what happened. `bandit-incremental-cache-control` is the
# live example -- it was measured once but never entered schedule.yaml, so 14
# of its 15 (model, skill) slots were never planned at all.
#
# Kept out of `CELL_STATE_REPORT_ORDER` on purpose: that tuple drives the
# matrix-coverage table, which counts collect.py's states, and a row that is
# structurally always zero there would be noise.
NOT_IN_SCHEDULE_STATE = "not_in_schedule"

# The two states that mean "this arm was never going to attempt this" -- as
# opposed to `technical_failure` (it attempted and the attempt was lost) and
# `not_yet_run` (it has not attempted yet). Grouped because the reader's
# question is "did this model decline, fail, or simply not get there?".
CANNOT_STATES: tuple[str, ...] = ("deliberately_skipped", "structurally_impossible")

# One glyph per HATCHED absence state. `not_yet_run` and `not_in_schedule`
# are deliberately missing: their absence from this map is what routes them
# to the faint-dot rendering instead (see `render_absence_mark`), so adding a
# key here would silently promote 29 of the 46 current cells to a full-height
# hatched slot that reads as a finding.
ABSENCE_GLYPHS: dict[str, str] = {
    "deliberately_skipped": "⊘",
    "structurally_impossible": "≡",
    "technical_failure": "⚠",
}

# Short human labels for the legend and the per-task tables. Full prose lives
# in each cell's own `absence.reason` (written by collect.py from
# schedule.yaml) and is never restated here -- these are the one-glance
# summary, not a second copy of the reason that could drift from it.
ABSENCE_LABELS: dict[str, str] = {
    "deliberately_skipped": "excluded by schedule.yaml",
    "structurally_impossible": "no such trial exists",
    "technical_failure": "attempted, never fairly attempted",
    NOT_YET_RUN_STATE: "not yet run",
    NOT_IN_SCHEDULE_STATE: "not in schedule.yaml",
}

# When one chart slot pools several tasks (the per-complexity charts) and
# those tasks disagree about why they are absent, this decides which fact the
# single slot reports. Ordered most-to-least conclusive: a structural
# impossibility is a property of the matrix, a deliberate skip is a decision,
# a technical failure is an accident, and "not yet run" is the only one that
# might change tomorrow. Reporting the most conclusive one keeps the slot
# from claiming the situation is more open than it is.
ABSENCE_PRECEDENCE: tuple[str, ...] = (
    "structurally_impossible",
    "deliberately_skipped",
    "technical_failure",
    "not_yet_run",
)


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------


def load_results(path: Path) -> dict[str, Any]:
    """Parse `results.json`, warning (not failing) on an unexpected schema
    version -- a shape mismatch should degrade to "some fields might be
    missing", not crash the whole report."""
    data = json.loads(path.read_text())
    version = data.get("schema_version")
    if version != EXPECTED_RESULTS_SCHEMA_VERSION:
        print(
            f"[report] WARNING: {path} has schema_version={version!r}, "
            f"expected {EXPECTED_RESULTS_SCHEMA_VERSION} -- fields may not "
            "match what this script expects.",
            file=sys.stderr,
        )
    return data


def load_leaderboard(path: Path) -> dict[str, Any]:
    """Parse the vendored `data/leaderboard.json` snapshot (see that file's
    own `_comment`/`row_selection_rule` fields for how it was produced)."""
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# Bar / chart-group data model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class AbsenceMark:
    """Why a slot has no bar, in the vocabulary `collect.py` writes into each
    cell's `state` field (and documents in `cell_state_vocabulary`).

    Exists so `present=False` can stop being a single undifferentiated
    "nothing here". Four different facts share that flag and only one of them
    means "no data yet"; the other three are answers, and an answer that
    renders as blank page is an answer the reader never receives. See
    `render_absence_mark` for how each one is drawn.

    `collapses_onto_model` is populated only for `structurally_impossible`
    cells, where the trial does not exist because it IS another model's
    trial (a mixed pair's vanilla arm is its orchestrator's vanilla arm).
    Surfacing it turns "this cell is blank" into "the same number, over
    there", which is a materially different statement about the model.
    """

    state: str
    reason: str
    collapses_onto_model: str | None = None


@dataclass(frozen=True)
class Bar:
    """One bar's value + Wilson (or DeepSWE run-to-run) CI, or an explicit
    absence.

    `present=False` means "there is nothing to draw here" -- a tier missing
    from the leaderboard, an arm that never ran, or an arm that ran but had
    zero valid attempts (collect.py's `pass_at_1 is None` case). Renderers
    must skip these entirely rather than drawing a zero-height bar; see the
    module docstring's "NULL-HANDLING PHILOSOPHY" section.

    `absence` upgrades that skip from "draw nothing" to "draw *why*" for the
    per-cell charts, where most slots are absent and the reason is the
    finding. It stays `None` for the two aggregation charts, whose absent
    slots are genuinely just missing data.

    `display` is the exact-value text for the hover tooltip and (where a
    chart labels its marks) the on-chart label. It exists because not every
    bar is a percentage any more: a cost bar reads "$22.54" and a Fable 5
    bar reads "13/20", and formatting `value * 100` for those would be
    nonsense. `None` keeps the original percent formatting.
    """

    slot: str
    present: bool
    value: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    outlined: bool = False  # True only for the official (leaderboard) bar
    absence: AbsenceMark | None = None
    display: str | None = None


@dataclass(frozen=True)
class ChartGroup:
    """One x-axis category (a model tier) and its bars. `bars` must be the
    same length and slot order across every group in one chart -- that
    alignment is what makes a grouped bar chart readable as "compare slot N
    across groups"; `build_matched_chart_groups`/`build_mixed_chart_groups`
    both guarantee it by building every group from the same slot list.
    """

    label: str
    bars: tuple[Bar, ...]


def _official_bar(tier: str, leaderboard: dict[str, Any]) -> Bar:
    """The outlined leaderboard bar for one tier, or an explicitly-absent
    Bar if that tier isn't on the leaderboard. Reads only what
    `data/leaderboard.json` actually recorded -- never invents a number for
    a tier its `present_on_leaderboard` flag marks as missing (e.g. haiku,
    as of the vendored snapshot).

    Carries NO `ci_low`/`ci_high`, on purpose, even though leaderboard.json
    has both: that interval is DeepSWE's own run-to-run standard error, not a
    Wilson interval, and `render_bar_mark` draws every bar's `ci_low`/
    `ci_high` into the same whisker channel as this harness's own Wilson
    bounds. Drawing it there would silently plot two different statistics as
    if they were peers -- exactly the confusion `render_official_baseline_
    footnote`'s `ci_note` already warns against in prose on the same chart.
    So this bar gets the Fable 5 treatment instead (see `fable5_pass_bar`):
    outline, no whisker, the interval folded into `display` as labelled text
    (`render_bar_mark` prints it because the bar is `outlined`).
    """
    tier_data = leaderboard.get("tiers", {}).get(tier)
    if tier_data is None or not tier_data.get("present_on_leaderboard"):
        return Bar(slot="official", present=False, outlined=True)
    return Bar(
        slot="official",
        present=True,
        outlined=True,
        value=tier_data["pass_at_1"],
        display=format_pass_at_1_with_ci(
            tier_data["pass_at_1"], tier_data["ci_low"], tier_data["ci_high"]
        ),
    )


def _arm_bar(slot: str, arm: dict[str, Any] | None) -> Bar:
    """One skill/vanilla bar from a `results.json` arm dict. Normalizes two
    different "no data" cases -- the arm never existed at all, and the arm
    existed but had zero valid attempts (collect.py sets `pass_at_1` to
    `None` there) -- to the same `present=False`, since both must render
    identically (an absent bar, not a zero-height one).
    """
    if arm is None or arm["pass_at_1"] is None:
        return Bar(slot=slot, present=False)
    return Bar(
        slot=slot,
        present=True,
        value=arm["pass_at_1"],
        ci_low=arm["pass_at_1_ci_low"],
        ci_high=arm["pass_at_1_ci_high"],
        display=format_pass_at_1_with_ci(
            arm["pass_at_1"], arm["pass_at_1_ci_low"], arm["pass_at_1_ci_high"]
        ),
    )


def is_cannot_state(state: str) -> bool:
    """True for the two states meaning "this arm was never going to attempt
    this" -- the ones the user must be able to see at a glance."""
    return state in CANNOT_STATES


def absence_mark_for_cell(cell: dict[str, Any] | None) -> AbsenceMark:
    """The `AbsenceMark` for a non-measured cell (or for no cell at all).

    Falls back to `ABSENCE_LABELS` only when collect.py wrote no `reason`,
    so the drawn explanation is the schedule's own words wherever those
    exist rather than a paraphrase maintained here.
    """
    if cell is None:
        # collect.py enumerates every (task, model, skill) that schedule.yaml
        # plans, so "results.json has no cell here" means the combination was
        # never planned -- not that it is planned and still pending. Saying
        # "not yet run" here would contradict that state's own definition
        # ("runnable and simply has not been run"), so this gets its own.
        return AbsenceMark(
            state=NOT_IN_SCHEDULE_STATE,
            reason=(
                "results.json records no cell here. collect.py enumerates every "
                "(task, model, skill) schedule.yaml plans, so a missing cell means this "
                "combination was never scheduled — not that it is scheduled and pending."
            ),
        )
    state = cell["state"]
    absence = cell.get("absence") or {}
    return AbsenceMark(
        state=state,
        reason=absence.get("reason") or ABSENCE_LABELS.get(state, state),
        collapses_onto_model=absence.get("collapses_onto_model"),
    )


def _absent_cell_bar(slot: str, cell: dict[str, Any] | None) -> Bar:
    """The single constructor for every absent per-cell bar, so a cost bar
    and a pass@1 bar can never disagree about why a cell is blank."""
    return Bar(slot=slot, present=False, absence=absence_mark_for_cell(cell))


def cell_pass_bar(slot: str, cell: dict[str, Any] | None) -> Bar:
    """The pass@1 bar for one (task, model, skill) cell.

    Two rules carry the honesty weight here:

    1. A measured `pass_at_1` of 0.0 stays `present=True`. It is a
       measurement, and it must not fall into the same branch as an absence
       -- see `render_bar_mark`'s minimum-height floor for how a zero is then
       made visible on the chart rather than collapsing to nothing.
    2. `is_single_trial` is branched on BEFORE the CI bounds are read. With
       n=1 there is no interval to draw whatever the bounds happen to say,
       and a whisker grown from a single observation is a confidence claim
       nothing in the data supports.
    """
    if cell is None or cell["state"] != MEASURED_STATE or cell["measured"] is None:
        return _absent_cell_bar(slot, cell)

    measured = cell["measured"]
    if measured["pass_at_1"] is None:
        return _absent_cell_bar(slot, cell)

    single = measured["is_single_trial"]
    return Bar(
        slot=slot,
        present=True,
        value=measured["pass_at_1"],
        ci_low=None if single else measured["pass_at_1_ci_low"],
        ci_high=None if single else measured["pass_at_1_ci_high"],
        display=format_cell_outcome(measured),
    )


def cell_measure_bar(
    slot: str, cell: dict[str, Any] | None, field: str, formatter: Any
) -> Bar:
    """The bar for one non-proportion cell measurement (cost, tokens).

    Carries no `ci_low`/`ci_high` at all: the only interval collect.py
    computes per cell is a Wilson interval over pass@1, which says nothing
    about a dollar amount. Attaching it here would draw a whisker whose ends
    mean nothing -- so this deliberately reaches for the same absence
    handling as `cell_pass_bar` and none of its interval handling.

    Every cost/token field is `float | None`, so a measured cell whose cost
    was never recorded is an absent bar, not a zero-dollar one.
    """
    if cell is None or cell["state"] != MEASURED_STATE or cell["measured"] is None:
        return _absent_cell_bar(slot, cell)

    value = cell["measured"].get(field)
    if value is None:
        return _absent_cell_bar(slot, cell)
    return Bar(slot=slot, present=True, value=value, display=formatter(value))


def _tier_sort_key(tier: str) -> int:
    """Sorts a dict's tier keys into TIER_ORDER; unknown tiers sort last
    rather than raising, so a future tier name doesn't crash the report."""
    return TIER_ORDER.index(tier) if tier in TIER_ORDER else len(TIER_ORDER)


def matched_arms_by_tier(arms: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Non-vanilla arms where orchestrator == impl (the "matched" cells),
    grouped by tier. Derived structurally from the two fields rather than
    re-deriving run.py's CELLS list, so this needs no import of run.py."""
    matched: dict[str, list[dict[str, Any]]] = {}
    for arm in arms:
        if arm["is_vanilla"] or arm["orchestrator"] != arm["impl"]:
            continue
        matched.setdefault(arm["orchestrator"], []).append(arm)
    return dict(sorted(matched.items(), key=lambda kv: _tier_sort_key(kv[0])))


def mixed_arms_by_orchestrator(arms: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Non-vanilla arms where orchestrator != impl (the "mixed" cells),
    grouped by orchestrator tier."""
    mixed: dict[str, list[dict[str, Any]]] = {}
    for arm in arms:
        if arm["is_vanilla"] or arm["orchestrator"] == arm["impl"]:
            continue
        mixed.setdefault(arm["orchestrator"], []).append(arm)
    return dict(sorted(mixed.items(), key=lambda kv: _tier_sort_key(kv[0])))


def vanilla_arm_by_tier(arms: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Vanilla (no-plugin) arms keyed by their tier (vanilla's `orchestrator`
    field, since vanilla has no separate impl -- see collect.py's schema)."""
    return {arm["orchestrator"]: arm for arm in arms if arm["is_vanilla"]}


def build_matched_chart_groups(
    arms: list[dict[str, Any]], leaderboard: dict[str, Any]
) -> list[ChartGroup]:
    """Chart 1's data: one group per matched tier (orchestrator == impl),
    bars = [official, <skills, alphabetical>, vanilla?]. The vanilla slot is
    included only if at least one vanilla arm exists anywhere in the run
    (per spec: "rendered only when vanilla arms are present in the data").
    A tier is dropped entirely only if every one of its bars is absent --
    an official-only tier (no experimental runs yet) still renders.
    """
    by_tier = matched_arms_by_tier(arms)
    vanilla_by_tier = vanilla_arm_by_tier(arms)
    skill_names = sorted({arm["skill"] for tier_arms in by_tier.values() for arm in tier_arms})
    include_vanilla = bool(vanilla_by_tier)

    groups = []
    for tier in TIER_ORDER:
        tier_arms = {arm["skill"]: arm for arm in by_tier.get(tier, [])}
        bars = [_official_bar(tier, leaderboard)]
        bars += [_arm_bar(skill, tier_arms.get(skill)) for skill in skill_names]
        if include_vanilla:
            bars.append(_arm_bar("vanilla", vanilla_by_tier.get(tier)))
        if any(bar.present for bar in bars):
            groups.append(ChartGroup(label=tier, bars=tuple(bars)))
    return groups


def build_mixed_chart_groups(
    arms: list[dict[str, Any]], leaderboard: dict[str, Any]
) -> list[ChartGroup]:
    """Chart 2's data: one group per orchestrator tier that has at least one
    mixed arm, bars = [official, <skills, alphabetical>]. Vanilla never
    appears here -- a vanilla arm has no orchestrator/impl split to be
    "mixed" about.
    """
    by_orchestrator = mixed_arms_by_orchestrator(arms)
    skill_names = sorted(
        {arm["skill"] for tier_arms in by_orchestrator.values() for arm in tier_arms}
    )

    groups = []
    for tier in TIER_ORDER:
        tier_arms = {arm["skill"]: arm for arm in by_orchestrator.get(tier, [])}
        if not tier_arms:
            continue
        bars = [_official_bar(tier, leaderboard)]
        bars += [_arm_bar(skill, tier_arms.get(skill)) for skill in skill_names]
        groups.append(ChartGroup(label=tier, bars=tuple(bars)))
    return groups


# --------------------------------------------------------------------------
# Per-cell chart groups (per-complexity pass@1, per-task cost/tokens)
# --------------------------------------------------------------------------

# The Fable 5 numbers get their own x-axis category rather than a bar inside
# every model group. Repeating one official figure across five model groups
# would read as five per-model official numbers, which do not exist -- the
# leaderboard publishes one figure per task, for one model, on a different
# harness. A category of its own says "this is a different thing" in the
# chart's own grammar, and the outlined-only mark (never a categorical hue)
# says it again.
OFFICIAL_SLOT = "official"
FABLE5_GROUP_LABEL = "Fable 5"

# Of the two per-task views the baseline carries, charts show the pooled one:
# n=20 (5 reasoning efforts x 4 runs) versus n=4 for the headline config.
# Both are in the comparison table; the chart shows the larger denominator
# and says so in its caption.
FABLE5_PER_TASK_VIEW = "all_efforts_pooled"

# The one phrase that names that view in prose, written once so a chart
# caption and a comparison-table header can never describe the same bar
# differently.
FABLE5_POOLED_VIEW_PHRASE = "all reasoning efforts pooled"

# The whole-benchmark view the aggregation charts show. `headline`, not
# `best_scoring_effort`: it is the figure the leaderboard itself leads with,
# and it is the one `fable5_aggregate_summary` already prints in the
# official-baseline section, so the chart and the table state the same
# number rather than two defensible different ones.
FABLE5_AGGREGATE_VIEW = "headline"

# Floor for an absolute-valued axis (cost, tokens) when nothing is measured
# yet, so `value_to_y`'s max_value is never 0 -- which would flatten every
# later bar onto the baseline instead of scaling it.
EMPTY_AXIS_MAX = 1.0

# How many equal gridlines an absolute axis (cost, tokens) draws, shared by
# `chart_max_value`'s ceiling rounding and `y_axis_value_ticks`'s own default
# so the two can never disagree about how finely the axis is divided.
ABSOLUTE_AXIS_TICK_COUNT = 4

# "Nice" per-tick multiples (Sparks/D3's classic axis algorithm): the
# smallest of these, at whatever power of ten, that is >= a rough per-tick
# step is the step every gridline actually uses. Using only these five
# multiples is what guarantees each resulting tick is a number a reader can
# estimate against without doing arithmetic -- "$10, $20, $30, $40" rather
# than "$5.63, $11.27, $16.90, $22.54".
_NICE_AXIS_STEP_MULTIPLES: tuple[float, ...] = (1.0, 2.0, 2.5, 5.0, 10.0)


def nice_axis_step(raw_max: float, *, n_ticks: int) -> float:
    """The smallest "nice" per-tick step such that `n_ticks` of them cover
    `raw_max`. Undefined for a non-positive `raw_max` (every caller here
    guards that case before reaching this function).
    """
    rough_step = raw_max / n_ticks
    magnitude = 10 ** math.floor(math.log10(rough_step))
    for multiple in _NICE_AXIS_STEP_MULTIPLES:
        step = multiple * magnitude
        if step >= rough_step:
            return step
    # Unreachable: 10.0 * magnitude is always >= rough_step by construction
    # (rough_step / magnitude is in [1, 10) after the floor(log10(...)) above).
    return 10.0 * magnitude


def round_up_to_readable_ceiling(raw_max: float, *, n_ticks: int = ABSOLUTE_AXIS_TICK_COUNT) -> float:
    """The smallest axis ceiling >= `raw_max` whose `n_ticks` equal gridlines
    all land on round numbers (Fix: axis ceilings). $22.54 becomes $40 (four
    $10 steps), not the raw quarters of $22.54 that used to label the
    cost/token charts' gridlines with amounts like "$5.63"/"$11.27"."""
    return nice_axis_step(raw_max, n_ticks=n_ticks) * n_ticks


def schedule_model_names(schedule: dict[str, Any]) -> list[str]:
    """The matrix's model names in schedule.yaml's declaration order. That
    order is meaningful (the three matched pairs, then the mixed ones) and
    alphabetising it would scramble it, so it is passed through untouched."""
    return [model["name"] for model in schedule.get("models", [])]


def schedule_skill_names(schedule: dict[str, Any]) -> list[str]:
    """The skills in declaration order, which puts `vanilla` -- the no-plugin
    control every other bar is read against -- first in each group."""
    return list(schedule.get("skills", []))


def tasks_in_report_order(
    schedule: dict[str, Any], cells: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Every task the report has something to say about, easiest first.

    Starts from the schedule (the authoritative task -> complexity mapping;
    this file never restates it) and appends any task that appears in `cells`
    without being in the schedule. Those extras are real measurements of a
    task nobody planned -- dropping them would hide data, but they carry no
    complexity, so they sort last and are excluded from the complexity axis
    by `complexity_rank is None` rather than by name.
    """
    scheduled = {
        task["name"]: {
            "name": task["name"],
            "complexity": task.get("complexity"),
            "complexity_rank": task.get("complexity_rank"),
        }
        for task in schedule.get("tasks", [])
    }
    for cell in cells:
        if cell["task"] in scheduled:
            continue
        scheduled[cell["task"]] = {
            "name": cell["task"],
            "complexity": cell.get("complexity"),
            "complexity_rank": cell.get("complexity_rank"),
        }
    return sorted(
        scheduled.values(),
        key=lambda t: (t["complexity_rank"] is None, t["complexity_rank"] or 0, t["name"]),
    )


def cells_for_slot(
    cells: list[dict[str, Any]], *, model: str, skill: str, tasks: set[str]
) -> list[dict[str, Any]]:
    """Every cell belonging to one (model, skill) chart slot within `tasks`."""
    return [
        cell
        for cell in cells
        if cell["model"] == model and cell["skill"] == skill and cell["task"] in tasks
    ]


def _pooled_absent_bar(slot: str, cells: list[dict[str, Any]]) -> Bar:
    """The absence for a slot where no contributing cell was measured.

    When the contributing tasks disagree, the most conclusive state wins
    (see `ABSENCE_PRECEDENCE`) and the reason says how much of the slot it
    actually accounts for -- so "excluded" never quietly stands in for a
    slot that is half excluded and half simply not run yet.
    """
    if not cells:
        return _absent_cell_bar(slot, None)

    states = [cell["state"] for cell in cells]
    chosen = min(
        states,
        key=lambda s: ABSENCE_PRECEDENCE.index(s) if s in ABSENCE_PRECEDENCE else len(ABSENCE_PRECEDENCE),
    )
    representative = next(cell for cell in cells if cell["state"] == chosen)
    mark = absence_mark_for_cell(representative)
    if len(cells) > 1:
        n_matching = sum(1 for state in states if state == chosen)
        mark = AbsenceMark(
            state=mark.state,
            reason=f"{n_matching} of {len(cells)} tasks at this level: {mark.reason}",
            collapses_onto_model=mark.collapses_onto_model,
        )
    return Bar(slot=slot, present=False, absence=mark)


def pool_pass_bar(slot: str, cells: list[dict[str, Any]]) -> Bar:
    """One pass@1 bar for a slot fed by one or more tasks' cells.

    A single contributing cell delegates to `cell_pass_bar` so it keeps
    whatever interval collect.py computed for it. Two or more are pooled by
    summing resolved/attempts -- and the pooled bar carries NO interval:
    collect.py's Wilson bounds are computed against each cell's own
    denominator and do not compose, and recomputing a statistic inside a
    renderer is how a chart ends up asserting a number no other artifact
    agrees with. The counts are shown instead, which is the honest summary
    of a pooled handful of single trials.
    """
    measured = [
        cell
        for cell in cells
        if cell["state"] == MEASURED_STATE
        and cell["measured"] is not None
        and cell["measured"]["pass_at_1"] is not None
    ]
    if not measured:
        return _pooled_absent_bar(slot, cells)
    if len(measured) == 1:
        return cell_pass_bar(slot, measured[0])

    n_resolved = sum(cell["measured"]["n_resolved"] for cell in measured)
    n_attempts = sum(cell["measured"]["n_attempts"] for cell in measured)
    return Bar(
        slot=slot,
        present=True,
        value=n_resolved / n_attempts if n_attempts else 0.0,
        display=f"{n_resolved} of {n_attempts} resolved (pooled over {len(measured)} tasks)",
    )


def _model_groups(
    models: list[str], skills: list[str], bar_for: Any
) -> list[ChartGroup]:
    """One group per model, slots = [official, *skills] in a fixed order.

    The official slot is present-but-empty in every model group so that all
    groups -- including the Fable 5 group that actually fills it -- carry an
    identical slot list, which is what `layout_chart_bars` requires to place
    slot N in the same column across groups.
    """
    return [
        ChartGroup(
            label=model,
            bars=(
                Bar(slot=OFFICIAL_SLOT, present=False, outlined=True),
                *(bar_for(model, skill) for skill in skills),
            ),
        )
        for model in models
    ]


def _fable5_group(skills: list[str], official_bar: Bar) -> ChartGroup:
    """The Fable 5 x-axis category: the outlined official bar, then one empty
    slot per skill so the group matches every model group's slot list."""
    return ChartGroup(
        label=FABLE5_GROUP_LABEL,
        bars=(official_bar, *(Bar(slot=skill, present=False) for skill in skills)),
    )


def fable5_per_task(baseline: dict[str, Any], task: str) -> dict[str, Any] | None:
    """The `baseline.fable5.per_task` entry for one task, or None when the
    baseline is unavailable or the task is not on the leaderboard."""
    fable5 = baseline.get("fable5") or {}
    if not fable5.get("available"):
        return None
    entry = (fable5.get("per_task") or {}).get(task)
    if entry is None or not entry.get("present_on_site"):
        return None
    return entry


def format_k_of_n(figure: dict[str, Any] | None) -> str:
    """A Fable 5 rate as the count it actually is: "13/20", never "0.65".

    Per-task leaderboard figures are k-of-n over scored rollout ATTEMPTS
    (5 reasoning efforts x 4 whole-benchmark runs). Rendering the ratio alone
    hides that n, and an n of 20 attempts on one task is a different claim
    from an n of 4 -- both of which the baseline carries.
    """
    if figure is None:
        return "—"
    return f"{figure['n_numerator']}/{figure['n_denominator']}"


def fable5_pass_bar(
    baseline: dict[str, Any], tasks: list[str], *, view: str = FABLE5_PER_TASK_VIEW
) -> Bar:
    """The outlined Fable 5 pass@1 bar, pooled over `tasks` by summing k and
    n (counts compose; the rate is then k/n over the pooled attempts).

    Carries no `ci_low`/`ci_high` at any point. Every per-task `interval_*`
    field in the baseline is null, and the one interval Fable 5 does publish
    is a run-to-run standard error across whole-benchmark passes, which
    `comparability.co_plotting_intervals_allowed = false` forbids drawing
    beside this harness's Wilson whiskers. It is reported as text in the
    comparison table instead -- never as a mark in the whisker channel.
    """
    figures = [
        (fable5_per_task(baseline, task) or {}).get(view, {}).get("pass_at_1") for task in tasks
    ]
    figures = [figure for figure in figures if figure is not None]
    if not figures:
        return Bar(slot=OFFICIAL_SLOT, present=False, outlined=True)

    numerator = sum(figure["n_numerator"] for figure in figures)
    denominator = sum(figure["n_denominator"] for figure in figures)
    if not denominator:
        return Bar(slot=OFFICIAL_SLOT, present=False, outlined=True)
    return Bar(
        slot=OFFICIAL_SLOT,
        present=True,
        outlined=True,
        value=numerator / denominator,
        display=f"{numerator}/{denominator}",
    )


def fable5_measure_bar(
    baseline: dict[str, Any],
    task: str,
    field: str,
    formatter: Any,
    *,
    view: str = FABLE5_PER_TASK_VIEW,
) -> Bar:
    """The outlined Fable 5 bar for one absolute per-task measure (mean cost,
    mean output tokens). Absent when the task is not on the leaderboard."""
    entry = (fable5_per_task(baseline, task) or {}).get(view) or {}
    value = entry.get(field)
    if value is None:
        return Bar(slot=OFFICIAL_SLOT, present=False, outlined=True)
    return Bar(
        slot=OFFICIAL_SLOT, present=True, outlined=True, value=value, display=formatter(value)
    )


def fable5_aggregate_headline(baseline: dict[str, Any]) -> dict[str, Any]:
    """The baseline's whole-benchmark headline block, or `{}` when the
    baseline is unavailable. One reader for it, so the aggregation chart and
    the official-baseline summary cannot end up quoting different configs."""
    fable5 = baseline.get("fable5") or {}
    if not fable5.get("available"):
        return {}
    return (fable5.get("aggregate") or {}).get(FABLE5_AGGREGATE_VIEW) or {}


def fable5_aggregate_bar(baseline: dict[str, Any]) -> Bar:
    """The outlined whole-benchmark Fable 5 bar for an aggregation chart.

    Carries `n_numerator/n_denominator` as its `display` for the same reason
    every other Fable 5 bar does -- the denominator is scored rollout
    attempts, not tasks, and a bare height would leave the reader with a rate
    whose unit they cannot see. Sets no `ci_low`/`ci_high` at any point: the
    interval the baseline publishes for this figure is a run-to-run standard
    error across whole-benchmark passes, and
    `comparability.co_plotting_intervals_allowed` is false, so it is reported
    as text in the official-baseline section and never as a whisker.
    """
    figure = fable5_aggregate_headline(baseline).get("pass_at_1") or {}
    denominator = figure.get("n_denominator")
    if not denominator:
        return Bar(slot=OFFICIAL_SLOT, present=False, outlined=True)
    return Bar(
        slot=OFFICIAL_SLOT,
        present=True,
        outlined=True,
        value=figure["n_numerator"] / denominator,
        display=f"{figure['n_numerator']}/{denominator}",
    )


def with_fable5_aggregate_group(
    groups: list[ChartGroup], baseline: dict[str, Any]
) -> list[ChartGroup]:
    """`groups` plus a Fable 5 x-axis category carrying the whole-benchmark
    figure, or `groups` untouched when the baseline has no such figure.

    An ADDITION to an existing chart, never a modification of it: every bar
    already in `groups` is passed through by identity, so the aggregation
    charts this extends keep drawing exactly what they drew before. The new
    category reuses the incoming chart's own slot list -- which
    `layout_chart_bars` requires to be identical across groups -- and fills
    every non-official slot with an explicit absence, so the Fable 5 column
    holds one outlined bar and nothing that could be read as a claude-code
    arm.
    """
    if not groups:
        return groups
    bar = fable5_aggregate_bar(baseline)
    if not bar.present:
        return groups

    slots = [existing.slot for existing in groups[0].bars]
    bars = tuple(
        bar if slot == OFFICIAL_SLOT else Bar(slot=slot, present=False) for slot in slots
    )
    return [*groups, ChartGroup(label=FABLE5_GROUP_LABEL, bars=bars)]


def build_complexity_chart_groups(
    complexity: str,
    cells: list[dict[str, Any]],
    schedule: dict[str, Any],
    baseline: dict[str, Any],
) -> list[ChartGroup]:
    """Chart data for one complexity level: a group per model, a bar per
    skill, plus the Fable 5 group. Membership comes from each cell's own
    `complexity` field (written by collect.py from schedule.yaml), so a task
    the schedule never ranked simply never appears on a complexity chart.
    """
    tasks = {cell["task"] for cell in cells if cell.get("complexity") == complexity}
    skills = schedule_skill_names(schedule)

    def bar_for(model: str, skill: str) -> Bar:
        return pool_pass_bar(skill, cells_for_slot(cells, model=model, skill=skill, tasks=tasks))

    groups = _model_groups(schedule_model_names(schedule), skills, bar_for)
    groups.append(_fable5_group(skills, fable5_pass_bar(baseline, sorted(tasks))))
    return groups


def build_task_measure_chart_groups(
    task: str,
    cells: list[dict[str, Any]],
    schedule: dict[str, Any],
    baseline: dict[str, Any],
    cell_field: str,
    baseline_field: str,
    formatter: Any,
) -> list[ChartGroup]:
    """Chart data for one task's cost or token chart -- same model grouping
    and slot order as the complexity charts, reading an absolute measure
    instead of a proportion."""
    skills = schedule_skill_names(schedule)
    by_key = {(cell["model"], cell["skill"]): cell for cell in cells if cell["task"] == task}

    def bar_for(model: str, skill: str) -> Bar:
        return cell_measure_bar(skill, by_key.get((model, skill)), cell_field, formatter)

    groups = _model_groups(schedule_model_names(schedule), skills, bar_for)
    groups.append(
        _fable5_group(skills, fable5_measure_bar(baseline, task, baseline_field, formatter))
    )
    return groups


def chart_max_value(groups: list[ChartGroup], *, fixed_max: float | None) -> float:
    """The value the y-axis top represents.

    A pass@1 chart passes `fixed_max=1.0`: rescaling a proportion chart to
    its own tallest bar would make 0.66 look like a perfect score and make
    two charts side by side incomparable. An absolute chart (dollars,
    tokens) has no natural ceiling, so it scales to its own largest bar --
    falling back to a positive floor when every bar is absent, since a max
    of 0 would flatten everything drawn later onto the baseline.
    """
    if fixed_max is not None:
        return fixed_max
    # `is not None`, never truthiness: a measured 0.0 is falsy, and dropping
    # it here would be one more place this report quietly treats a real zero
    # as no data.
    values = [
        bar.value for group in groups for bar in group.bars if bar.present and bar.value is not None
    ]
    largest = max(values) if values else 0.0
    # A chart whose every measured value is 0 would otherwise produce a
    # zero-high axis labelled "$0.00" five times over. The floor keeps the
    # axis meaningful; the bars still sit on the baseline, lifted only by
    # `min_measured_height` so they read as "measured, and zero".
    if largest <= 0:
        return EMPTY_AXIS_MAX
    # Rounded UP to a readable ceiling (Fix: axis ceilings) rather than
    # returned raw -- the raw largest bar is what used to produce gridlines
    # like "$5.63"/"$11.27"/"$16.90"/"$22.54". This is also why the tallest
    # bar no longer touches the very top of the plot: headroom above it is
    # the trade a reader makes for every gridline being a round number.
    return round_up_to_readable_ceiling(largest)


def assign_categorical_color_vars(slot_names: list[str]) -> dict[str, str]:
    """Maps each non-official bar slot to a fixed CSS custom-property name
    (`--series-1`, `--series-2`, `--series-3`) in alphabetical slot-name
    order. The actual hex values live once in the page's <style> block
    (palette.md's validated categorical slots 1-3: blue/orange/aqua) --
    this function only decides *which* slot gets *which* var, and it does
    so by sorted name so a series keeps the same color everywhere it
    appears (never by a chart's current row order, which would repaint a
    series when the chart layout changes -- see dataviz anti-patterns.md's
    "recolor-on-filter").
    """
    ordered = sorted(slot_names)
    if len(ordered) > 3:
        raise ValueError(
            f"only 3 categorical slots are validated for this report's palette; got {ordered}"
        )
    return {name: f"--series-{i + 1}" for i, name in enumerate(ordered)}


# --------------------------------------------------------------------------
# Complexity chart: series over the low -> medium -> high axis
# --------------------------------------------------------------------------

# WHY THIS CHART USES TWO ENCODING CHANNELS
# ------------------------------------------
# 5 models x 3 skills is up to 15 series, and `assign_categorical_color_vars`
# refuses more than 3 -- rightly: a 15-hue chart is a color-matching puzzle,
# not a chart. Rather than weakening that guard, identity is split across two
# channels that each stay inside their own legible limit:
#
#   hue   -> skill  (exactly 3, which is exactly what the palette validates)
#   shape -> model  (5 shapes, each distinguishable at marker size and in
#                    greyscale, so the encoding survives print and CVD)
#
# The legend renders both channels separately, so a reader decodes "orange
# triangle" as "do-and-judge, opus" by reading two short lists rather than
# memorising fifteen swatches.
MODEL_MARKER_SHAPES: tuple[str, ...] = ("circle", "square", "triangle", "diamond", "cross")

# Column width per complexity level and the horizontal step between dodged
# series within a column. The dodge exists because many series land on the
# same (complexity, value) point -- with n=1 everywhere, most values are
# exactly 0.0 or 1.0 -- and perfectly overlapping markers would render 15
# series as 2 visible dots. The offset is a fixed function of series index,
# never a random jitter, so two builds of the same report are identical.
COMPLEXITY_COLUMN_WIDTH = 150.0
COMPLEXITY_DODGE_STEP = 9.0
COMPLEXITY_MARKER_RADIUS = 4.5


@dataclass(frozen=True)
class ComplexityPoint:
    """One (series, complexity level) observation.

    `is_single_trial` and the raw counts travel with the point because the
    chart's honesty depends on them: a point at 100% built from one attempt
    is a different object from a point at 100% built from twenty, and the
    connector rule and the hover label both need to know which this is.
    """

    complexity_rank: int
    complexity: str
    value: float
    n_resolved: int
    n_attempts: int
    is_single_trial: bool
    label: str


@dataclass(frozen=True)
class ComplexitySeries:
    """One (model, skill) pair's points, ordered by complexity rank."""

    model: str
    skill: str
    points: tuple[ComplexityPoint, ...]


def assign_model_marker_shapes(model_names: list[str]) -> dict[str, str]:
    """Maps each model to a marker shape by its position in the schedule's
    model list, so a model keeps its shape across every chart and across
    report builds.

    Raises above the number of declared shapes for the same reason
    `assign_categorical_color_vars` raises above 3 slots: two models sharing
    a shape makes the legend a lie, and a loud failure is better than a
    chart that quietly cannot be decoded.
    """
    if len(model_names) > len(MODEL_MARKER_SHAPES):
        raise ValueError(
            f"only {len(MODEL_MARKER_SHAPES)} distinguishable marker shapes are defined "
            f"for the model channel; got {model_names}"
        )
    return {name: MODEL_MARKER_SHAPES[i] for i, name in enumerate(model_names)}


def _complexity_ranks(schedule: dict[str, Any]) -> dict[str, int]:
    """complexity level -> rank, from the schedule's declared level order."""
    return {level: rank for rank, level in enumerate(schedule.get("complexity_levels", []))}


def _point_from_cells(
    complexity: str, rank: int, cells: list[dict[str, Any]]
) -> ComplexityPoint | None:
    """Pool one (model, skill, complexity) group of measured cells into one
    plotted point, or None when nothing there was measured."""
    measured = [
        cell
        for cell in cells
        if cell["state"] == MEASURED_STATE
        and cell["measured"] is not None
        and cell["measured"]["pass_at_1"] is not None
    ]
    if not measured:
        return None

    n_resolved = sum(cell["measured"]["n_resolved"] for cell in measured)
    n_attempts = sum(cell["measured"]["n_attempts"] for cell in measured)
    tasks = ", ".join(sorted({cell["task"] for cell in measured}))
    return ComplexityPoint(
        complexity_rank=rank,
        complexity=complexity,
        value=n_resolved / n_attempts if n_attempts else 0.0,
        n_resolved=n_resolved,
        n_attempts=n_attempts,
        is_single_trial=n_attempts == 1,
        label=f"{tasks}: {n_resolved} of {n_attempts} resolved",
    )


def build_complexity_series(
    cells: list[dict[str, Any]], schedule: dict[str, Any]
) -> list[ComplexitySeries]:
    """One series per (model, skill) that has at least one measured point.

    A cell with no `complexity` (a task the schedule never ranked) is
    excluded outright rather than pinned to some default rung -- it has no
    position on this axis, and inventing one would put a real measurement
    under a complexity claim nobody made.
    """
    ranks = _complexity_ranks(schedule)
    series: list[ComplexitySeries] = []

    for model in schedule_model_names(schedule):
        for skill in schedule_skill_names(schedule):
            points = []
            for complexity, rank in ranks.items():
                group = [
                    cell
                    for cell in cells
                    if cell["model"] == model
                    and cell["skill"] == skill
                    and cell.get("complexity") == complexity
                ]
                point = _point_from_cells(complexity, rank, group)
                if point is not None:
                    points.append(point)
            if points:
                points.sort(key=lambda p: p.complexity_rank)
                series.append(ComplexitySeries(model=model, skill=skill, points=tuple(points)))
    return series


# The two ways a connector can be drawn. `solid` asserts a trend; every point
# under it has replication behind it. `provisional` is a reading aid -- it
# joins the marks of one series in complexity order so the reader can follow
# it through a crowded column, while its dashes and low opacity say the shape
# is not a claim. The distinction exists because the honest caveat and the
# requested line are not in conflict: withholding the line entirely, as an
# earlier draft did, deletes the deliverable for the whole single-trial data
# regime instead of qualifying it.
CONNECTOR_SOLID = "solid"
CONNECTOR_PROVISIONAL = "provisional"

# Stroke treatment per style: (opacity, dash pattern or None).
CONNECTOR_STROKE: dict[str, tuple[float, str | None]] = {
    CONNECTOR_SOLID: (0.75, None),
    CONNECTOR_PROVISIONAL: (0.4, "4 3"),
}


def contiguous_measured_runs(series: ComplexitySeries) -> list[tuple[ComplexityPoint, ...]]:
    """The series' points split into runs of ADJACENT complexity ranks.

    This is the whole reason the connector is not one polyline over
    `series.points`. `build_complexity_series` compresses unmeasured ranks
    out of the list, so two neighbouring entries can be low and high with an
    unmeasured medium between them -- and a single polyline over the list
    would draw a straight segment across that gap, asserting a measurement
    nobody took at exactly the level the reader is most likely to read off.
    Adjacency has to be decided on the ranks themselves, never on list
    position.
    """
    runs: list[list[ComplexityPoint]] = []
    for point in series.points:
        if runs and point.complexity_rank == runs[-1][-1].complexity_rank + 1:
            runs[-1].append(point)
            continue
        runs.append([point])
    return [tuple(run) for run in runs]


def series_connector_style(series: ComplexitySeries) -> str:
    """How firmly this series' connector may be drawn.

    One single-trial point downgrades the whole series: a line is read end to
    end, so a segment anchored on one 0-or-1 observation makes the entire
    shape provisional, not just that segment.
    """
    if any(point.is_single_trial for point in series.points):
        return CONNECTOR_PROVISIONAL
    return CONNECTOR_SOLID


def series_connector_runs(series: ComplexitySeries) -> list[tuple[ComplexityPoint, ...]]:
    """The runs long enough to draw a line through. A run of one is a lone
    marker -- there is no second point to join it to."""
    return [run for run in contiguous_measured_runs(series) if len(run) > 1]


def series_has_connector(series: ComplexitySeries) -> bool:
    """Whether this series draws any connecting line at all -- true as soon
    as two measured points sit at adjacent complexity levels."""
    return bool(series_connector_runs(series))


def complexity_column_x(
    rank: int, geometry: ChartGeometry, *, column_width: float = COMPLEXITY_COLUMN_WIDTH
) -> float:
    """Centre x of the column for one complexity rank."""
    return geometry.plot_left + (rank + 0.5) * column_width


def series_dodge_offset(
    index: int, n_series: int, *, step: float = COMPLEXITY_DODGE_STEP
) -> float:
    """Horizontal nudge for series `index` of `n_series`, centred on 0 so the
    whole fan stays symmetric about its column and a lone series sits exactly
    on the column centre."""
    return (index - (n_series - 1) / 2) * step


def render_marker(shape: str, cx: float, cy: float, color_var: str) -> str:
    """One data marker in the series hue. Shape carries the model channel, so
    an unrecognised shape raises rather than silently drawing nothing (an
    invisible point would read as "no measurement", the exact confusion this
    whole file is built to prevent)."""
    r = COMPLEXITY_MARKER_RADIUS
    fill = f'fill="var({color_var})"'
    if shape == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" {fill}/>'
    if shape == "square":
        return (
            f'<rect x="{cx - r:.1f}" y="{cy - r:.1f}" width="{2 * r:.1f}" '
            f'height="{2 * r:.1f}" {fill}/>'
        )
    if shape == "triangle":
        points = f"{cx:.1f},{cy - r * 1.2:.1f} {cx - r:.1f},{cy + r * 0.8:.1f} {cx + r:.1f},{cy + r * 0.8:.1f}"
        return f'<polygon points="{points}" {fill}/>'
    if shape == "diamond":
        points = f"{cx:.1f},{cy - r * 1.3:.1f} {cx + r * 1.1:.1f},{cy:.1f} {cx:.1f},{cy + r * 1.3:.1f} {cx - r * 1.1:.1f},{cy:.1f}"
        return f'<polygon points="{points}" {fill}/>'
    if shape == "cross":
        arm = r * 0.42
        points = (
            f"{cx - arm:.1f},{cy - r:.1f} {cx + arm:.1f},{cy - r:.1f} {cx + arm:.1f},{cy - arm:.1f} "
            f"{cx + r:.1f},{cy - arm:.1f} {cx + r:.1f},{cy + arm:.1f} {cx + arm:.1f},{cy + arm:.1f} "
            f"{cx + arm:.1f},{cy + r:.1f} {cx - arm:.1f},{cy + r:.1f} {cx - arm:.1f},{cy + arm:.1f} "
            f"{cx - r:.1f},{cy + arm:.1f} {cx - r:.1f},{cy - arm:.1f} {cx - arm:.1f},{cy - arm:.1f}"
        )
        return f'<polygon points="{points}" {fill}/>'
    raise ValueError(f"unknown marker shape {shape!r}; expected one of {MODEL_MARKER_SHAPES}")


# --------------------------------------------------------------------------
# Chart geometry (pure -- Step 5 unit-tests these directly)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ChartGeometry:
    """Pixel budget for one grouped bar chart. Bar/gap widths follow the
    dataviz skill's mark spec (bars <=24px thick, a 2px surface gap between
    touching marks); `plot_width` is deliberately absent -- it is always
    computed from the data via `chart_content_width`, never fixed, so the
    chart never reserves dead space for a shorter chart or overflows a
    wider one.
    """

    bar_width: float = 20.0
    bar_gap: float = 2.0
    group_gap: float = 32.0
    plot_left: float = 46.0
    plot_top: float = 30.0
    plot_height: float = 200.0
    right_margin: float = 16.0
    # Minimum drawn height for a bar that IS a measurement, so a measured
    # 0.0 does not render as literally nothing and become indistinguishable
    # from the four ways a cell can be absent.
    #
    # Defaults to 0.0 -- OFF -- because the two aggregation charts do not
    # need it: their zero bars carry a Wilson whisker, which is already
    # visible ink saying "this was measured". The per-cell charts turn it on
    # (see CELL_CHART_GEOMETRY), because every cell there is a single trial
    # with null bounds and therefore has no whisker to be seen by.
    #
    # The floor does exaggerate any very small value, not only zero: on a
    # cost axis topping out near $36, a $0.14 cell draws at the floor rather
    # than at its true sub-pixel height. That is the deliberate trade -- a
    # floored bar means "measured, and very small", which is a true and
    # useful statement, whereas the untraded alternative is an invisible bar
    # that means "measured" and reads as "absent". The exact figure is one
    # hover away and is printed in the per-task table either way.
    min_measured_height: float = 0.0


def _slots_per_group(groups: list[ChartGroup]) -> int:
    return len(groups[0].bars) if groups else 0


def _group_width(groups: list[ChartGroup], geometry: ChartGeometry) -> float:
    """Pixel width of one group's bar cluster (bars + inner gaps, no outer
    group gap) -- shared by layout_chart_bars/chart_content_width/
    group_label_positions so all three agree on where a group starts."""
    n = _slots_per_group(groups)
    if n == 0:
        return 0.0
    return n * geometry.bar_width + (n - 1) * geometry.bar_gap


def chart_content_width(groups: list[ChartGroup], geometry: ChartGeometry) -> float:
    """Total pixel width spanned by every group's bars and the gaps between
    them (excludes plot_left/right_margin) -- used to size the SVG viewBox
    to the data instead of guessing a fixed width."""
    if not groups:
        return 0.0
    group_width = _group_width(groups, geometry)
    return len(groups) * group_width + (len(groups) - 1) * geometry.group_gap


@dataclass(frozen=True)
class PlacedBar:
    """A Bar with x/width pixel geometry attached -- the output of layout,
    the input to rendering. Kept separate from Bar so layout stays a pure
    function of (groups, geometry) with no SVG-string concerns mixed in."""

    group_label: str
    bar: Bar
    x: float
    width: float


def layout_chart_bars(groups: list[ChartGroup], geometry: ChartGeometry) -> list[PlacedBar]:
    """Assigns an x position to every bar slot, left to right. Every group
    gets the same number of slots (guaranteed by build_*_chart_groups) so
    slot N always lands in the same horizontal position across groups.
    Absent bars still consume a slot -- a missing official number leaves a
    visible gap rather than shifting its neighbors left -- but are skipped
    by the SVG renderer (render_bar_mark checks `bar.present`).
    """
    group_width = _group_width(groups, geometry)
    placed: list[PlacedBar] = []
    for i, group in enumerate(groups):
        cursor = geometry.plot_left + i * (group_width + geometry.group_gap)
        for bar in group.bars:
            placed.append(PlacedBar(group_label=group.label, bar=bar, x=cursor, width=geometry.bar_width))
            cursor += geometry.bar_width + geometry.bar_gap
    return placed


def group_label_positions(
    groups: list[ChartGroup], geometry: ChartGeometry
) -> list[tuple[str, float]]:
    """(group_label, center_x) for the x-axis category labels centered
    beneath each group's bar cluster."""
    group_width = _group_width(groups, geometry)
    positions = []
    for i, group in enumerate(groups):
        left = geometry.plot_left + i * (group_width + geometry.group_gap)
        positions.append((group.label, left + group_width / 2))
    return positions


def value_to_y(value: float, geometry: ChartGeometry, *, max_value: float = 1.0) -> float:
    """Pixel y-coordinate on the plot for `value` in [0, max_value]. SVG y
    grows downward, so value=0 maps to the baseline (plot_top + plot_height)
    and value=max_value maps to plot_top -- this inversion is the one
    "upside-down" piece of arithmetic in this module, so it is centralized
    here rather than re-derived at each call site. Clamped to [0, 1] so a
    CI bound that drifts fractionally outside range (float rounding, not
    expected but cheap to guard) never draws outside the axis.
    """
    fraction = 0.0 if max_value <= 0 else value / max_value
    fraction = max(0.0, min(1.0, fraction))
    return geometry.plot_top + geometry.plot_height * (1 - fraction)


def bar_vertical_extent(
    value: float, geometry: ChartGeometry, *, max_value: float = 1.0
) -> tuple[float, float]:
    """(top_y, height) in SVG pixels for a bar reaching `value`. Grows from
    the shared baseline (plot_top + plot_height) the same way every bar
    does, whether value is 0 (zero height, baseline only) or max_value (full
    plot height)."""
    top = value_to_y(value, geometry, max_value=max_value)
    baseline = geometry.plot_top + geometry.plot_height
    return top, baseline - top


def floored_bar_extent(
    value: float, geometry: ChartGeometry, *, max_value: float = 1.0
) -> tuple[float, float]:
    """`bar_vertical_extent` with the visible-zero floor applied.

    Kept separate from `bar_vertical_extent` rather than folded into it: that
    function is the honest pixel arithmetic ("this value is this many pixels
    tall") and several callers depend on it staying exactly that. This one is
    a rendering decision layered on top -- "a measurement must leave a mark
    even at zero" -- and a rendering decision does not belong inside the
    arithmetic it adjusts.
    """
    top, height = bar_vertical_extent(value, geometry, max_value=max_value)
    if height >= geometry.min_measured_height:
        return top, height
    baseline = geometry.plot_top + geometry.plot_height
    return baseline - geometry.min_measured_height, geometry.min_measured_height


def y_axis_value_ticks(
    geometry: ChartGeometry,
    max_value: float,
    formatter: Any,
    *,
    n_ticks: int = ABSOLUTE_AXIS_TICK_COUNT,
) -> list[tuple[float, str]]:
    """[(pixel_y, label), ...] for an ABSOLUTE axis (dollars, tokens),
    labelled in the chart's own units by `formatter`.

    The percentage twin (`y_axis_ticks`) is left untouched: a cost axis
    labelled "0%..100%" would be meaningless, and a proportion axis labelled
    "$0.00" equally so, so the two stay separate functions rather than one
    with a mode flag.

    Divides `max_value` evenly into `n_ticks` steps without rounding
    anything itself -- `max_value` is expected to already be a readable
    ceiling (see `round_up_to_readable_ceiling`, applied by `chart_max_value`
    before it ever reaches here) rather than a chart's raw largest bar.
    """
    return [
        (
            value_to_y(max_value * i / n_ticks, geometry, max_value=max_value),
            formatter(max_value * i / n_ticks),
        )
        for i in range(n_ticks + 1)
    ]


def whisker_vertical_extent(
    ci_low: float, ci_high: float, geometry: ChartGeometry, *, max_value: float = 1.0
) -> tuple[float, float]:
    """(y_high, y_low) pixel y-positions for a CI whisker -- y_high is
    nearer the top of the plot (the ci_high end), y_low nearer the
    baseline. Reuses value_to_y so the whisker and its bar always agree on
    where 0% and 100% sit; at ci_low=0/ci_high=1 this correctly spans the
    full plot height rather than clipping."""
    return (
        value_to_y(ci_high, geometry, max_value=max_value),
        value_to_y(ci_low, geometry, max_value=max_value),
    )


def y_axis_ticks(geometry: ChartGeometry, *, step: float = 0.25) -> list[tuple[float, str]]:
    """[(pixel_y, label), ...] for horizontal gridlines at each `step`
    fraction from 0% to 100% (default: every 25%)."""
    ticks = []
    fraction = 0.0
    while fraction <= 1.0 + 1e-9:
        ticks.append((value_to_y(fraction, geometry), f"{round(fraction * 100)}%"))
        fraction += step
    return ticks


def rounded_top_rect_path(x: float, y: float, width: float, height: float, radius: float) -> str:
    """SVG path data for a rectangle with rounded top corners and square
    bottom corners -- the mark spec's "4px rounded data-end, square at the
    baseline" bar shape. SVG's <rect> only offers uniform corner rounding,
    so the outline is drawn explicitly with two quadratic arcs at the top.
    `radius` is clamped to half the bar's own width/height so a very thin
    or short bar never produces a self-intersecting path.
    """
    r = max(0.0, min(radius, width / 2, height))
    if height <= 0:
        return ""
    return (
        f"M{x},{y + height} "
        f"L{x},{y + r} "
        f"Q{x},{y} {x + r},{y} "
        f"L{x + width - r},{y} "
        f"Q{x + width},{y} {x + width},{y + r} "
        f"L{x + width},{y + height} "
        f"Z"
    )


# --------------------------------------------------------------------------
# Formatting helpers (pure -- used by both the table and the chart labels)
# --------------------------------------------------------------------------


def format_pass_at_1_with_ci(
    value: float | None, ci_low: float | None, ci_high: float | None
) -> str:
    """'62% ± 8%' style summary, or an em dash for an arm/tier with no data
    (collect.py's null-propagation rule: value/ci_low/ci_high are None
    together whenever n_attempts == 0)."""
    if value is None or ci_low is None or ci_high is None:
        return "—"
    half_width = (ci_high - ci_low) / 2 * 100
    return f"{value * 100:.0f}% ± {half_width:.0f}%"


def format_arm_pass_at_1_cell(arm: dict[str, Any]) -> str:
    """The Arm results table's 'Pass@1 ± CI' cell: the same summary
    `format_pass_at_1_with_ci` produces, with the attempt count folded in.

    A rate on its own reads as established over some number of tries; the
    table's own arms currently include one whose Wilson interval is "0% ±
    40%" over a single attempt, and printing that without a denominator
    reads as a wide-but-confident measurement rather than one coin flip.
    `format_cell_outcome` states the same reasoning for the per-cell table.
    Skipped for a zero-attempt arm (`summary == "—"`): "— (n=0)" would repeat
    the same fact twice in two different vocabularies for nothing.
    """
    summary = format_pass_at_1_with_ci(
        arm["pass_at_1"], arm["pass_at_1_ci_low"], arm["pass_at_1_ci_high"]
    )
    if summary == "—":
        return summary
    return f"{summary} (n={arm['n_attempts']})"


def format_cell_outcome(measured: dict[str, Any] | None) -> str:
    """One cell's result, phrased so its sample size is unavoidable.

    Every measured cell in the current results.json is `is_single_trial`, and
    "100%" is the wrong way to report one coin flip: it reads as a rate
    established over some number of tries, when the number of tries is one.
    So a single-trial cell reports "1 of 1 resolved" and never a percentage
    at all -- the reader gets the numerator, the denominator, and no implied
    reliability.

    A multi-trial cell earns the rate, and shows its Wilson interval beside
    the counts that produced it -- unless collect.py left the bounds null, in
    which case the rate is still shown and the interval simply is not (never
    a "± —", which reads as an interval of unknown width rather than none).
    """
    if measured is None:
        return "—"

    n_resolved, n_attempts = measured["n_resolved"], measured["n_attempts"]
    counts = f"{n_resolved} of {n_attempts} resolved"
    if measured["is_single_trial"]:
        return counts

    interval = format_pass_at_1_with_ci(
        measured["pass_at_1"], measured["pass_at_1_ci_low"], measured["pass_at_1_ci_high"]
    )
    if interval == "—":
        rate = measured["pass_at_1"]
        interval = "—" if rate is None else f"{rate * 100:.0f}%"
    return f"{interval} ({counts})"


def format_usd(value: float | None) -> str:
    return "—" if value is None else f"${value:,.2f}"


def format_count(value: float | None) -> str:
    return "—" if value is None else f"{value:,.0f}"


# --------------------------------------------------------------------------
# Run-metadata header (pure reshaping over trials -- no wall-clock reads)
# --------------------------------------------------------------------------


def earliest_arm_created_at(arms: list[dict[str, Any]]) -> str | None:
    """The run's start time: the earliest `created_at` across every arm.

    `created_at` is written once per arm by run.py, at the moment that arm's
    `pier run` was launched (see run.py's `write_arm_metadata`) -- the
    earliest one is therefore the moment the whole matrix run began. `None`
    when no arm carries the field at all (a v1 results.json, or a v2 one
    with zero arms), which the caller must render as "not recorded" rather
    than a guess -- see `format_run_started_at`.
    """
    created_ats = [arm["created_at"] for arm in arms if arm.get("created_at")]
    return min(created_ats) if created_ats else None


def resolve_sample_seed(arms: list[dict[str, Any]]) -> int | None:
    """The pinned `SAMPLE_SEED` every arm in a `--mode sample` run shares.

    `None` covers two different underlying facts collect.py's per-arm data
    cannot itself distinguish -- run.py's `sample_seed` field recorded `null`
    because the run mode wasn't "sample", or no arm carries the field at all
    (a v1 results.json). `render_run_metadata_header` tells them apart using
    `schema_version`, not this return value alone.
    """
    seeds = {arm["sample_seed"] for arm in arms if arm.get("sample_seed") is not None}
    return next(iter(seeds)) if seeds else None


def summarize_run_metadata(
    trials: list[dict[str, Any]], arms: list[dict[str, Any]], *, schema_version: int | None
) -> dict[str, Any]:
    """Derive header facts from `results.json`'s `trials` and `arms`.

    `run_started_at`/`sample_seed` are only ever populated from a
    schema_version >= `MIN_SCHEMA_VERSION_WITH_RUN_METADATA` results.json --
    collect.py didn't surface `arm.json`'s `created_at`/`sample_seed` onto
    arm records before that version, so an older file has no such data to
    read regardless of what `earliest_arm_created_at`/`resolve_sample_seed`
    would compute from its (absent) fields. `has_run_metadata_fields` records
    which case this is so `render_run_metadata_header` can render an honest
    "not recorded" instead of a guess (see this module's docstring's
    null-handling philosophy). Deliberately takes no wall-clock reading (no
    `datetime.now()`) so this stays a pure function of its input, fully
    unit-testable.
    """
    task_keys = {
        t.get("task_checksum") or t.get("task_name")
        for t in trials
        if t.get("task_checksum") or t.get("task_name")
    }
    plugin_refs = sorted({t["plugin_ref"] for t in trials if t.get("plugin_ref")})
    cc_versions = sorted({t["claude_code_version"] for t in trials if t.get("claude_code_version")})
    has_run_metadata_fields = (
        schema_version is not None and schema_version >= MIN_SCHEMA_VERSION_WITH_RUN_METADATA
    )
    return {
        "n_tasks": len(task_keys),
        "n_trials": len(trials),
        "plugin_refs": plugin_refs,
        "claude_code_versions": cc_versions,
        "run_started_at": earliest_arm_created_at(arms) if has_run_metadata_fields else None,
        "sample_seed": resolve_sample_seed(arms) if has_run_metadata_fields else None,
        "has_run_metadata_fields": has_run_metadata_fields,
    }


def arm_table_rows(arms: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Pre-formatted display strings for one arm-table row per arm. Kept
    separate from the HTML-emitting function so the formatting logic is
    unit-testable without parsing HTML back out."""
    rows = []
    for arm in arms:
        rows.append(
            {
                "arm_id": arm["arm_id"],
                "pass_at_1": format_arm_pass_at_1_cell(arm),
                "avg_cost_usd": format_usd(arm["avg_cost_usd"]),
                # The costliest single trial, next to the average that hides
                # it -- with no spend cap in the harness (see collect.py's
                # "WHY THERE IS NO ..." docstring section), an outlier here is
                # the only cost anomaly warning a reader gets.
                "max_cost_usd": format_usd(arm["max_cost_usd"]),
                "avg_output_tokens": format_count(arm["avg_output_tokens"]),
                "avg_n_agent_steps": format_count(arm["avg_n_agent_steps"]),
                # Two separate counts, never summed: `n_incomplete` trials
                # the agent abandoned (counted in Pass@1's denominator) and
                # `n_errored` trials the infrastructure lost (excluded from
                # it). See collect.py's classification table.
                "n_incomplete": str(arm["n_incomplete"]),
                "n_errored": str(arm["n_errored"]),
            }
        )
    return rows


# --------------------------------------------------------------------------
# Per-cell tables (per task, the Fable 5 comparison, and matrix coverage)
# --------------------------------------------------------------------------

# Reporting order for the coverage summary: the state that carries numbers
# first, then the absences in the order a reader asks about them (what was
# excluded, what could not exist, what broke, what is simply pending).
CELL_STATE_REPORT_ORDER: tuple[str, ...] = (
    MEASURED_STATE,
    "deliberately_skipped",
    "structurally_impossible",
    "technical_failure",
    NOT_YET_RUN_STATE,
)

# The order absence states are listed in a chart legend: the reporting order
# plus this module's own `not_in_schedule`, which `CELL_STATE_REPORT_ORDER`
# deliberately omits (it counts collect.py's states, and this one is never
# counted). Legends read from this tuple so an unplanned slot on a chart is
# always explained by that chart's own legend.
ABSENCE_STATE_RENDER_ORDER: tuple[str, ...] = (*CELL_STATE_REPORT_ORDER, NOT_IN_SCHEDULE_STATE)


def summarize_cell_states(cells: list[dict[str, Any]]) -> dict[str, int]:
    """How many cells sit in each state, every state present even at zero.

    A zero that disappears is indistinguishable from a state nobody tracks
    any more, and "0 technical failures" is a thing the reader specifically
    wants to be told rather than left to infer from a missing row.
    """
    counts = {state: 0 for state in CELL_STATE_REPORT_ORDER}
    for cell in cells:
        state = cell["state"]
        counts[state] = counts.get(state, 0) + 1
    return counts


def _absence_reason_text(mark: AbsenceMark) -> str:
    """The reason a reader sees for an absent cell, with the collapse target
    spelled out when there is one -- "the same measurement, over there" is a
    different fact from "this arm has no result", and only the second one is
    a gap."""
    if mark.collapses_onto_model is None:
        return mark.reason
    return (
        f"{mark.reason} This is the same measurement as the "
        f"{mark.collapses_onto_model} arm's."
    )


def task_table_rows(
    task: str, cells: list[dict[str, Any]], schedule: dict[str, Any]
) -> list[dict[str, str]]:
    """Pre-formatted rows for one task's breakdown, one per (model, skill).

    Every planned cell gets a row whether or not it was measured: this table
    is the exact-value twin of the task's charts, and a chart that shows a
    hatched "excluded" slot needs a table row saying which exclusion. Absent
    rows carry an em dash in every numeric column -- never a zero, which
    would be a measurement -- plus the state and its stated reason.
    """
    by_key = {(cell["model"], cell["skill"]): cell for cell in cells if cell["task"] == task}
    rows = []
    for model in schedule_model_names(schedule):
        for skill in schedule_skill_names(schedule):
            cell = by_key.get((model, skill))
            measured = cell["measured"] if cell and cell["state"] == MEASURED_STATE else None
            if measured is not None:
                rows.append(
                    {
                        "model": model,
                        "skill": skill,
                        "outcome": format_cell_outcome(measured),
                        "cost": format_usd(measured.get("avg_cost_usd")),
                        "output_tokens": format_count(measured.get("avg_output_tokens")),
                        "state": MEASURED_STATE,
                        "reason": "",
                    }
                )
                continue

            mark = absence_mark_for_cell(cell)
            rows.append(
                {
                    "model": model,
                    "skill": skill,
                    "outcome": "—",
                    "cost": "—",
                    "output_tokens": "—",
                    "state": ABSENCE_LABELS.get(mark.state, mark.state),
                    "reason": _absence_reason_text(mark),
                }
            )
    return rows


def measured_cells_for_task(cells: list[dict[str, Any]], task: str) -> list[dict[str, Any]]:
    """Every cell for one task that actually carries numbers."""
    return [
        cell
        for cell in cells
        if cell["task"] == task and cell["state"] == MEASURED_STATE and cell["measured"] is not None
    ]


def local_totals_for_task(cells: list[dict[str, Any]], task: str) -> tuple[int, int]:
    """(resolved, attempts) summed over every measured cell for one task.

    Counts, not a rate: the local numbers are a handful of single trials, and
    a percentage over four attempts invites comparison with a leaderboard
    figure computed over 452.
    """
    measured = [cell["measured"] for cell in measured_cells_for_task(cells, task)]
    return (
        sum(m["n_resolved"] for m in measured),
        sum(m["n_attempts"] for m in measured),
    )


def format_arm_list(arms: list[str]) -> str:
    """"a", "a and b", "a, b and c" -- an English list, so a pooled cell can
    name its contributors inside a table cell without a nested list."""
    if len(arms) == 1:
        return arms[0]
    return f"{', '.join(arms[:-1])} and {arms[-1]}"


def format_local_attempts(cells: list[dict[str, Any]], task: str) -> str:
    """One task's local result for the Fable 5 comparison table, with the
    arms it was pooled from named.

    The pool here is opportunistic, not a harness-level rate: for
    `abs-stepped-slices` it is one haiku run under one skill plus one sonnet
    run under a different skill. Printed as a bare "1 of 2 resolved" beside
    Fable 5's whole-benchmark "14/20", that reads as this harness scoring
    50%, which is a claim nobody measured. Naming the arms in the cell makes
    the pool's composition part of the figure.
    """
    contributing = measured_cells_for_task(cells, task)
    if not contributing:
        return "—"

    n_resolved, n_attempts = local_totals_for_task(cells, task)
    arms = sorted({f"{cell['model']}/{cell['skill']}" for cell in contributing})
    attempts = "attempt" if n_attempts == 1 else "attempts"
    return f"{n_resolved} of {n_attempts} {attempts} across {format_arm_list(arms)}"


def format_baseline_interval(figure: dict[str, Any] | None) -> str:
    """A Fable 5 interval as TEXT, named for what it actually is.

    This is the only place a leaderboard interval is ever rendered, and it is
    rendered into a table cell -- never into the whisker channel that carries
    this harness's Wilson intervals. `comparability.co_plotting_intervals_
    allowed` is false for a concrete reason: Fable 5's interval is a
    run-to-run standard error across 4 whole-benchmark passes, and this
    harness's is a binomial interval over one cell's attempts. Drawn as peer
    error bars they would look like the same kind of uncertainty, which is
    the misreading the name in this string exists to block.
    """
    if figure is None:
        return "—"
    low, high = figure.get("interval_low"), figure.get("interval_high")
    if low is None or high is None:
        return "no interval published"
    n_runs = figure.get("interval_n_runs")
    runs = f" across {n_runs} whole-benchmark passes" if n_runs else ""
    return f"{low * 100:.0f}%–{high * 100:.0f}% (run-to-run SE{runs}, not a binomial CI)"


def _fable5_view_figure(baseline: dict[str, Any], task: str, view: str) -> dict[str, Any] | None:
    """One task's pass@1 figure under one of the baseline's two per-task
    views, or None when the task is not on the leaderboard."""
    entry = fable5_per_task(baseline, task)
    if entry is None:
        return None
    return (entry.get(view) or {}).get("pass_at_1")


def fable5_comparison_rows(
    baseline: dict[str, Any], cells: list[dict[str, Any]], schedule: dict[str, Any]
) -> list[dict[str, str]]:
    """The Fable 5 vs. local comparison, one row per task in report order.

    Both baseline views appear side by side, each as a k-of-n count with its
    own denominator visible: 20 pooled scored attempts (5 reasoning efforts x
    4 whole-benchmark runs) against 4 for the headline config. Showing only
    one would let a reader compare a 4-attempt figure with a 20-attempt one
    without noticing.

    Tasks the baseline does not cover keep their row rather than being
    dropped -- an unscheduled task measured locally is still a measurement,
    and hiding it to tidy the table would hide data.
    """
    rows = []
    for task in tasks_in_report_order(schedule, cells):
        name = task["name"]
        pooled = _fable5_view_figure(baseline, name, "all_efforts_pooled")
        headline = _fable5_view_figure(baseline, name, "headline_config_max")
        entry = fable5_per_task(baseline, name) or {}
        rows.append(
            {
                "task": name,
                "complexity": task["complexity"] or "not in schedule.yaml",
                "fable5_pooled": format_k_of_n(pooled),
                "fable5_headline": format_k_of_n(headline),
                "fable5_cost": format_usd(
                    (entry.get("all_efforts_pooled") or {}).get("mean_cost_usd")
                ),
                "local": format_local_attempts(cells, name),
            }
        )
    return rows


def fable5_aggregate_summary(baseline: dict[str, Any]) -> list[tuple[str, str]]:
    """(label, value) pairs for the baseline's whole-benchmark headline row.

    Returns an empty list -- not a table of dashes -- when the baseline is
    unavailable, so the page omits the section entirely rather than showing
    an empty frame that looks like a failed lookup.
    """
    headline = fable5_aggregate_headline(baseline)
    if not headline:
        return []

    pass_at_1 = headline.get("pass_at_1") or {}
    comparability = (baseline.get("fable5") or {}).get("comparability") or {}
    return [
        ("Config", str(headline.get("config", "—"))),
        (
            "Pass@1 (whole benchmark)",
            f"{format_k_of_n(pass_at_1)} {pass_at_1.get('denominator_unit', '')}".strip(),
        ),
        ("Interval", format_baseline_interval(pass_at_1)),
        ("Harness", f"{comparability.get('baseline_harness', '—')} "
                    f"(this harness: {comparability.get('local_harness', '—')})"),
        ("Mean cost per attempt", format_usd(headline.get("mean_cost_usd"))),
        ("Mean output tokens", format_count(headline.get("mean_output_tokens"))),
    ]


# --------------------------------------------------------------------------
# SVG rendering
# --------------------------------------------------------------------------

WHISKER_CAP_HALF_WIDTH = 5.0

# The diagonal hatch every drawn absence is filled with, defined once in a
# page-level <defs> block (see `render_shared_svg_defs`) and referenced from
# every chart. Hatch, not a flat grey: a flat fill is one shade away from a
# real bar, whereas a hatch reads as "this area is not data" at a glance and
# survives greyscale printing.
ABSENCE_HATCH_ID = "absence-hatch"
ABSENCE_HATCH_URL = f"url(#{ABSENCE_HATCH_ID})"

# Radius of the baseline dot that marks a glyph-less absence. Small enough
# that it cannot be mistaken for a bar, large enough to survive printing.
ABSENCE_DOT_RADIUS = 1.6


def render_shared_svg_defs() -> str:
    """A zero-size <svg> carrying the one <pattern> every chart references.

    One document-level definition rather than a copy inside each chart: SVG
    ids are document-global in HTML, so repeating the pattern per chart would
    emit duplicate ids -- invalid markup, and browsers resolve `url(#id)` to
    whichever copy they saw first anyway.
    """
    return (
        f'<svg width="0" height="0" aria-hidden="true" class="svg-defs"><defs>'
        f'<pattern id="{ABSENCE_HATCH_ID}" width="6" height="6" '
        f'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="6" height="6" fill="var(--absence-fill)"/>'
        f'<line x1="0" y1="0" x2="0" y2="6" stroke="var(--absence-ink)" stroke-width="1.5"/>'
        f"</pattern></defs></svg>"
    )


def render_absence_mark(placed: PlacedBar, geometry: ChartGeometry) -> str:
    """How a slot with no measurement says why.

    Three renderings, and the difference between them is the whole point:

    * A DRAWN absence (`ABSENCE_GLYPHS`) gets a hatched slot spanning the
      full plot height plus its glyph. Full height, deliberately: a
      part-height block would sit somewhere on the y axis and read as a
      value, whereas a block touching the top of the plot cannot be read as
      a quantity at all. It never uses a categorical hue, because hue is
      this report's signal for "this is a measurement".
    * A glyph-less state (`not_yet_run`, `not_in_schedule`) gets a
      transparent hover target plus ONE faint dot on the baseline. There is
      no finding to report, so the ink is the least that can still be seen;
      but "seen" is the requirement, because the legend advertises a swatch
      for these states and because a printed or greyscale chart has to
      distinguish "awaiting a run" from an empty page. The dot sits on the
      baseline, where the axis draws ink anyway, so it cannot be read off
      the y scale as a value.
    * A bar with no `AbsenceMark` at all (the empty official slot inside
      each model group) gets nothing, not even a tooltip -- there is no
      story about it to tell.
    """
    mark = placed.bar.absence
    if mark is None:
        return ""

    label = ABSENCE_LABELS.get(mark.state, mark.state)
    tooltip = f"{placed.group_label} · {placed.bar.slot} — {label}: {_absence_reason_text(mark)}"
    title = f"<title>{html.escape(tooltip)}</title>"
    rect = (
        f'<rect x="{placed.x:.1f}" y="{geometry.plot_top:.1f}" '
        f'width="{placed.width:.1f}" height="{geometry.plot_height:.1f}"'
    )

    center_x = placed.x + placed.width / 2
    glyph = ABSENCE_GLYPHS.get(mark.state)
    if glyph is None:
        return _faint_absence_mark(title, rect, center_x, geometry)
    return _hatched_absence_mark(title, rect, center_x, geometry, glyph)


def _faint_absence_mark(
    title: str, rect: str, center_x: float, geometry: ChartGeometry
) -> str:
    """A glyph-less absence: the full-height hover target, plus one dot ON
    the baseline so the slot is not literally blank."""
    baseline_y = geometry.plot_top + geometry.plot_height
    return (
        f'<g class="absence absence-blank">{title}{rect} fill="transparent"/>'
        f'<circle class="absence-dot" cx="{center_x:.1f}" cy="{baseline_y:.1f}" '
        f'r="{ABSENCE_DOT_RADIUS}"/></g>'
    )


def _hatched_absence_mark(
    title: str, rect: str, center_x: float, geometry: ChartGeometry, glyph: str
) -> str:
    """A findings absence: the full-height hatched slot and its glyph."""
    return (
        f'<g class="absence">{title}'
        f'{rect} fill="{ABSENCE_HATCH_URL}" stroke="var(--absence-ink)" '
        f'stroke-width="1" stroke-dasharray="3 3"/>'
        f'<text class="absence-glyph" x="{center_x:.1f}" '
        f'y="{geometry.plot_top + 18:.1f}" text-anchor="middle">{glyph}</text>'
        f"</g>"
    )


def render_bar_mark(
    placed: PlacedBar,
    geometry: ChartGeometry,
    color_var: str | None,
    *,
    max_value: float = 1.0,
) -> str:
    """One bar + its CI whisker, or an empty string if the bar has no data --
    the single place that enforces "absent, not zero-height" for every bar
    this report ever draws.

    Deliberately does NOT draw a value label on every bar: marks-and-
    anatomy.md is explicit that a number beside every mark is chaos and
    goes unread, and with 3-4 bars per group plus whiskers, a tip label on
    each one collided with its neighbor's in an early draft (two adjacent
    tall bars with close values overlapped, e.g. "54%"/"60%"). The exact
    value is reachable two other ways instead -- the `<title>` hover
    tooltip below, and the arm table underneath the chart -- which also
    means this satisfies the palette's contrast-relief rule for the
    light-mode aqua ("vanilla") bar without needing on-chart text.
    """
    bar = placed.bar
    if not bar.present:
        # Absent, not zero -- and for a per-cell chart, absent WITH a reason.
        # `render_absence_mark` returns "" for the plain no-data case, which
        # preserves this function's original "draw nothing" behaviour.
        return render_absence_mark(placed, geometry)

    top, height = floored_bar_extent(bar.value, geometry, max_value=max_value)
    path = rounded_top_rect_path(placed.x, top, placed.width, height, radius=4.0)
    center_x = placed.x + placed.width / 2
    # `display` carries the value already formatted in its own units -- a
    # count for a single trial, a dollar amount for a cost bar, a k-of-n for
    # a leaderboard bar, a "62% ± 8%" summary for an aggregation-chart arm.
    # There is deliberately NO percentage fallback here: every constructor
    # that sets `present=True` (`_official_bar`, `_arm_bar`, `cell_pass_bar`,
    # `cell_measure_bar`, every `fable5_*_bar`) sets `display` too, so a bare
    # `f"{value*100:.0f}%"` reachable from here would mean one of them forgot
    # -- and this asserts loudly instead of quietly rendering that bug.
    # NOTE: `assert` is compiled out under `python -O` / `PYTHONOPTIMIZE=1`,
    # which would silently drop this safety net -- run report.py as a plain
    # `python3 report.py` (see README's "Generate the report" step).
    assert bar.display is not None, (
        f"present Bar for slot {bar.slot!r} has no display text -- every Bar "
        "constructor must set one; see this function's docstring"
    )
    value_text = bar.display
    tooltip = f"{placed.group_label} · {bar.slot}: {value_text}"

    if bar.outlined:
        # Official baseline: stroke only, no categorical fill -- see module
        # docstring's "THE OFFICIAL-BASELINE BARS..." section for why.
        fill_attr = 'fill="transparent" stroke="var(--official-outline)" stroke-width="2"'
    else:
        fill_attr = f'fill="var({color_var})"'

    parts = [f"<g><title>{html.escape(tooltip)}</title>", f'<path d="{path}" {fill_attr}/>']
    if bar.outlined and bar.display is not None:
        # The one bar in a per-task chart that gets a printed label. The
        # module docstring argues against labelling every mark (they collide
        # and go unread) -- but a leaderboard figure is a k-of-n count, and a
        # bar height alone would leave the reader with the rate and no
        # denominator, which is precisely the misreading these charts exist
        # to avoid. There is at most one such bar per chart, so nothing to
        # collide with.
        parts.append(
            f'<text class="bar-value-label" x="{center_x:.1f}" y="{top - 5:.1f}" '
            f'text-anchor="middle">{html.escape(bar.display)}</text>'
        )
    # A whisker is drawn ONLY from two real bounds. Every per-cell bar in the
    # current data has `ci_low`/`ci_high` of None (single trial), and every
    # Fable 5 bar has them None by construction (`fable5_pass_bar` never sets
    # them, because a run-to-run standard error must not be drawn in the same
    # channel as a Wilson interval). Both therefore fall through this branch
    # rather than being special-cased anywhere.
    if bar.ci_low is not None and bar.ci_high is not None:
        parts.append(render_whisker(center_x, bar.ci_low, bar.ci_high, geometry, max_value=max_value))
    parts.append("</g>")
    return "".join(parts)


def render_whisker(
    center_x: float,
    ci_low: float,
    ci_high: float,
    geometry: ChartGeometry,
    *,
    max_value: float = 1.0,
) -> str:
    """A 2px whisker line from ci_low to ci_high with short end caps --
    correctly spans the full plot at ci_low=0/ci_high=1 (see
    whisker_vertical_extent's docstring)."""
    y_high, y_low = whisker_vertical_extent(ci_low, ci_high, geometry, max_value=max_value)
    cap = WHISKER_CAP_HALF_WIDTH
    return (
        f'<g class="whisker" stroke="var(--text-secondary)" stroke-width="1.5" stroke-linecap="round">'
        f'<line x1="{center_x:.1f}" y1="{y_high:.1f}" x2="{center_x:.1f}" y2="{y_low:.1f}"/>'
        f'<line x1="{center_x - cap:.1f}" y1="{y_high:.1f}" x2="{center_x + cap:.1f}" y2="{y_high:.1f}"/>'
        f'<line x1="{center_x - cap:.1f}" y1="{y_low:.1f}" x2="{center_x + cap:.1f}" y2="{y_low:.1f}"/>'
        f"</g>"
    )


def render_chart_svg(
    groups: list[ChartGroup],
    geometry: ChartGeometry,
    color_vars: dict[str, str],
    *,
    max_value: float = 1.0,
    tick_formatter: Any | None = None,
) -> str:
    """The full <svg> for one grouped bar chart: gridlines, baseline, every
    bar/whisker/label, and x-axis group labels. Returns an empty-state
    string instead of a degenerate 0-width svg when there is nothing to
    plot (see components.md's "Empty state" component).

    `max_value`/`tick_formatter` default to the proportion axis the two
    aggregation charts have always used, so their output is unchanged; the
    per-task cost and token charts pass their own maximum and unit
    formatter instead.
    """
    if not groups:
        return '<p class="empty-state">No arms recorded for this chart yet.</p>'

    content_width = chart_content_width(groups, geometry)
    svg_width = geometry.plot_left + content_width + geometry.right_margin
    x_axis_band = 22.0
    svg_height = geometry.plot_top + geometry.plot_height + x_axis_band

    ticks = (
        y_axis_ticks(geometry)
        if tick_formatter is None
        else y_axis_value_ticks(geometry, max_value, tick_formatter)
    )
    baseline_y = geometry.plot_top + geometry.plot_height
    grid_lines = []
    for y, label in ticks:
        grid_lines.append(
            f'<line x1="{geometry.plot_left:.1f}" y1="{y:.1f}" '
            f'x2="{geometry.plot_left + content_width:.1f}" y2="{y:.1f}" '
            # Identified by position, not by the label reading "0%": an
            # absolute axis labels its floor "$0.00" or "0", and matching on
            # the text would silently drop the baseline from those charts.
            f'class="{"baseline" if abs(y - baseline_y) < 0.01 else "gridline"}"/>'
        )
        grid_lines.append(
            f'<text class="axis-label" x="{geometry.plot_left - 8:.1f}" y="{y + 3:.1f}" '
            f'text-anchor="end">{html.escape(label)}</text>'
        )

    bars = [
        render_bar_mark(placed, geometry, color_vars.get(placed.bar.slot), max_value=max_value)
        for placed in layout_chart_bars(groups, geometry)
    ]

    group_labels = [
        f'<text class="axis-label group-label" x="{x:.1f}" '
        f'y="{geometry.plot_top + geometry.plot_height + 16:.1f}" text-anchor="middle">'
        f"{html.escape(label)}</text>"
        for label, x in group_label_positions(groups, geometry)
    ]

    body = "".join(grid_lines) + "".join(bars) + "".join(group_labels)
    return (
        f'<svg viewBox="0 0 {svg_width:.1f} {svg_height:.1f}" '
        f'width="{svg_width:.0f}" height="{svg_height:.0f}" role="img">{body}</svg>'
    )


def render_connector(points_attr: str, color_var: str, style: str) -> str:
    """One polyline over one contiguous run of measured points.

    Raises on an unknown style for the same reason `render_marker` does: a
    connector that silently fell back to the solid treatment would upgrade a
    reading aid into an asserted trend, which is the one thing the two styles
    exist to keep apart.
    """
    if style not in CONNECTOR_STROKE:
        raise ValueError(f"unknown connector style {style!r}; expected one of {sorted(CONNECTOR_STROKE)}")
    opacity, dash = CONNECTOR_STROKE[style]
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<polyline class="connector connector-{style}" points="{points_attr}" fill="none" '
        f'stroke="var({color_var})" stroke-width="1.5" stroke-opacity="{opacity}"{dash_attr}/>'
    )


def _complexity_series_marks(
    series: ComplexitySeries,
    index: int,
    n_series: int,
    geometry: ChartGeometry,
    color_var: str,
    shape: str,
) -> str:
    """One series: a connector per contiguous run, then every marker.

    Connectors are emitted before markers so the markers sit on top of the
    line rather than under it -- SVG paints in document order, and a line
    crossing a marker would blur the one thing that is actually a
    measurement.
    """
    dx = series_dodge_offset(index, n_series)

    def point_xy(point: ComplexityPoint) -> tuple[float, float]:
        return (
            complexity_column_x(point.complexity_rank, geometry) + dx,
            value_to_y(point.value, geometry),
        )

    style = series_connector_style(series)
    parts = [
        render_connector(
            " ".join(f"{x:.1f},{y:.1f}" for x, y in map(point_xy, run)), color_var, style
        )
        for run in series_connector_runs(series)
    ]

    for point in series.points:
        x, y = point_xy(point)
        tooltip = f"{series.model} · {series.skill} · {point.complexity} — {point.label}"
        parts.append(
            f"<g><title>{html.escape(tooltip)}</title>"
            f"{render_marker(shape, x, y, color_var)}</g>"
        )
    return "".join(parts)


def render_complexity_chart_svg(
    series: list[ComplexitySeries],
    geometry: ChartGeometry,
    color_vars: dict[str, str],
    shapes: dict[str, str],
    complexity_levels: list[str],
) -> str:
    """The complexity chart: pass@1 against the ordinal low -> medium -> high
    axis, one series per (model, skill).

    Hue comes from `color_vars` (skill) and marker shape from `shapes`
    (model), which is how up to 15 series fit inside a 3-color palette
    without touching `assign_categorical_color_vars`' guard. Series are
    dodged horizontally within their column so co-located points -- and with
    single-trial data almost every point is exactly 0.0 or 1.0 -- stay
    individually visible.
    """
    if not series:
        return '<p class="empty-state">No measured cells carry a complexity level yet.</p>'

    content_width = COMPLEXITY_COLUMN_WIDTH * len(complexity_levels)
    svg_width = geometry.plot_left + content_width + geometry.right_margin
    svg_height = geometry.plot_top + geometry.plot_height + 22.0
    baseline_y = geometry.plot_top + geometry.plot_height

    grid = []
    for y, label in y_axis_ticks(geometry):
        grid.append(
            f'<line x1="{geometry.plot_left:.1f}" y1="{y:.1f}" '
            f'x2="{geometry.plot_left + content_width:.1f}" y2="{y:.1f}" '
            f'class="{"baseline" if abs(y - baseline_y) < 0.01 else "gridline"}"/>'
        )
        grid.append(
            f'<text class="axis-label" x="{geometry.plot_left - 8:.1f}" y="{y + 3:.1f}" '
            f'text-anchor="end">{label}</text>'
        )

    marks = [
        _complexity_series_marks(
            item,
            index,
            len(series),
            geometry,
            color_vars.get(item.skill, "--text-secondary"),
            shapes.get(item.model, MODEL_MARKER_SHAPES[0]),
        )
        for index, item in enumerate(series)
    ]

    axis_labels = [
        f'<text class="axis-label group-label" x="{complexity_column_x(rank, geometry):.1f}" '
        f'y="{baseline_y + 16:.1f}" text-anchor="middle">{html.escape(level)}</text>'
        for rank, level in enumerate(complexity_levels)
    ]

    body = "".join(grid) + "".join(marks) + "".join(axis_labels)
    return (
        f'<svg viewBox="0 0 {svg_width:.1f} {svg_height:.1f}" '
        f'width="{svg_width:.0f}" height="{svg_height:.0f}" role="img">{body}</svg>'
    )


# --------------------------------------------------------------------------
# HTML assembly
# --------------------------------------------------------------------------


def render_legend(
    color_vars: dict[str, str],
    *,
    include_official: bool,
    official_label: str = "official (mini-swe-agent)",
    absence_states: tuple[str, ...] = (),
) -> str:
    """A legend row: one swatch per categorical series plus, when the chart
    carries an official bar, an outlined swatch explaining it. Always
    present for >=2 series per the dataviz mark spec -- the dependable
    identity channel a reader can rely on instead of color-matching alone.

    `absence_states` extends it to the per-cell charts, where most slots are
    absent and an unexplained hatch is just noise. Only the states actually
    drawn on that chart are listed -- a legend entry with nothing on the
    chart to match it to is worse than no entry.
    """
    items = [
        f'<li><span class="swatch" style="background:var({var})"></span>{html.escape(slot)}</li>'
        for slot, var in sorted(color_vars.items(), key=lambda kv: kv[1])
    ]
    if include_official:
        items.append(
            f'<li><span class="swatch swatch-outline"></span>{html.escape(official_label)}</li>'
        )
    for state in absence_states:
        glyph = ABSENCE_GLYPHS.get(state)
        # The blank swatch carries a dot because the chart now draws one --
        # a swatch showing something the chart does not draw is a legend
        # that lies about its own chart.
        swatch = (
            f'<span class="swatch swatch-hatch">{glyph}</span>'
            if glyph
            else '<span class="swatch swatch-blank"><span class="swatch-dot"></span></span>'
        )
        items.append(f"<li>{swatch}{html.escape(ABSENCE_LABELS.get(state, state))}</li>")
    return f'<ul class="legend">{"".join(items)}</ul>'


def render_complexity_legend(color_vars: dict[str, str], shapes: dict[str, str]) -> str:
    """The complexity chart's two-channel legend, as two labelled rows.

    Split deliberately rather than merged into one row of fifteen entries:
    the chart encodes skill and model on separate channels, so the legend
    that decodes it has to teach those channels separately -- "find the hue,
    then find the shape" -- instead of asking the reader to memorise every
    combination.
    """
    hues = "".join(
        f'<li><span class="swatch" style="background:var({var})"></span>{html.escape(skill)}</li>'
        for skill, var in sorted(color_vars.items(), key=lambda kv: kv[1])
    )
    marks = "".join(
        f'<li><svg class="legend-shape" viewBox="0 0 14 14" aria-hidden="true">'
        f'{render_marker(shape, 7.0, 7.0, "--text-secondary")}</svg>{html.escape(model)}</li>'
        for model, shape in shapes.items()
    )
    return (
        f'<ul class="legend"><li class="legend-channel">colour = skill</li>{hues}</ul>'
        f'<ul class="legend"><li class="legend-channel">shape = model</li>{marks}</ul>'
    )


def render_official_baseline_footnote(leaderboard: dict[str, Any]) -> str:
    """The honesty footnote required wherever an official bar appears --
    sourced entirely from leaderboard.json's own fields so the wording
    single-sources from the vendored snapshot rather than being duplicated
    (and potentially drifting) in this file."""
    note = html.escape(leaderboard.get("honesty_note", ""))
    snapshot_date = html.escape(leaderboard.get("snapshot_date", "unknown"))
    source_url = html.escape(leaderboard.get("source_url", ""))
    ci_note = html.escape(leaderboard.get("field_notes", {}).get("ci_low / ci_high", ""))
    return (
        '<p class="footnote">'
        f"{note} Snapshot date: {snapshot_date}. Source: "
        f'<a href="{source_url}">{source_url}</a>. {ci_note}'
        "</p>"
    )


def official_baseline_table_rows(leaderboard: dict[str, Any]) -> list[dict[str, str]]:
    """Pre-formatted display strings for the official-baseline table, one
    row per tier in TIER_ORDER. This is the table-view twin of the outlined
    bars specifically (the arm table below only covers this harness's own
    arms, never leaderboard.json's tiers) -- required by the dataviz
    skill's accessibility rule that every chart has a WCAG-clean table
    equivalent. An absent tier (e.g. haiku, as of the vendored snapshot)
    renders its `absence_reason` instead of dashes standing in unexplained.
    """
    rows = []
    for tier in TIER_ORDER:
        tier_data = leaderboard.get("tiers", {}).get(tier)
        if tier_data is None or not tier_data.get("present_on_leaderboard"):
            reason = (tier_data or {}).get("absence_reason", "not on the leaderboard")
            rows.append({"tier": tier, "pass_at_1": "—", "avg_cost_usd": "—",
                         "avg_output_tokens": "—", "avg_n_agent_steps": "—", "note": reason})
            continue
        rows.append(
            {
                "tier": tier,
                "pass_at_1": format_pass_at_1_with_ci(
                    tier_data["pass_at_1"], tier_data["ci_low"], tier_data["ci_high"]
                ),
                "avg_cost_usd": format_usd(tier_data["avg_cost_usd"]),
                "avg_output_tokens": format_count(tier_data["avg_output_tokens"]),
                "avg_n_agent_steps": format_count(tier_data["avg_n_agent_steps"]),
                "note": f"reasoning_effort={tier_data['reasoning_effort']}",
            }
        )
    return rows


def render_official_baseline_table(leaderboard: dict[str, Any]) -> str:
    """The exact-value table view for the outlined official bars -- see
    official_baseline_table_rows's docstring for why this exists
    separately from render_arm_table."""
    header = (
        "<tr><th>Tier</th><th class='num'>Pass@1 ± CI</th><th class='num'>Avg cost</th>"
        "<th class='num'>Avg output tokens</th><th class='num'>Avg steps</th><th>Note</th></tr>"
    )
    body = "".join(
        "<tr>"
        f"<td>{html.escape(row['tier'])}</td>"
        f"<td class='num'>{row['pass_at_1']}</td>"
        f"<td class='num'>{row['avg_cost_usd']}</td>"
        f"<td class='num'>{row['avg_output_tokens']}</td>"
        f"<td class='num'>{row['avg_n_agent_steps']}</td>"
        f"<td class='muted-cell'>{html.escape(row['note'])}</td>"
        "</tr>"
        for row in official_baseline_table_rows(leaderboard)
    )
    return f"<div class='table-scroll'><table class='arm-table'><thead>{header}</thead><tbody>{body}</tbody></table></div>"


def render_chart_figure(
    title: str,
    groups: list[ChartGroup],
    geometry: ChartGeometry,
    color_vars: dict[str, str],
    leaderboard: dict[str, Any],
    *,
    extra_footnote: str = "",
) -> str:
    """One <figure> = caption + legend + scrollable svg wrapper. The
    overflow-x wrapper keeps a wide chart from breaking the page's own
    horizontal scroll (see dataviz anti-patterns.md).

    `extra_footnote` appends one more already-rendered paragraph after the
    leaderboard footnote, for a chart that carries an official mark the
    leaderboard footnote does not describe. Defaults to nothing, so a caller
    that adds no such mark gets byte-identical output to before.
    """
    chart_slots = {bar.slot for group in groups for bar in group.bars}
    has_official = "official" in chart_slots
    # `color_vars` is assigned once globally (so a series keeps the same
    # color across both charts -- see assign_categorical_color_vars), but
    # the legend must only list series this particular chart can actually
    # show: e.g. chart 2 never has a "vanilla" bar, so showing a vanilla
    # swatch there would be a legend entry with nothing on the chart to
    # match it to.
    chart_color_vars = {slot: var for slot, var in color_vars.items() if slot in chart_slots}
    svg = render_chart_svg(groups, geometry, color_vars)
    legend = render_legend(chart_color_vars, include_official=has_official)
    footnote = render_official_baseline_footnote(leaderboard) if has_official else ""
    return (
        f"<figure class='chart-figure'><figcaption>{html.escape(title)}</figcaption>"
        f"{legend}<div class='chart-scroll'>{svg}</div>{footnote}{extra_footnote}</figure>"
    )


# The per-cell charts' geometry: identical to the aggregation charts except
# for the visible-zero floor, which those charts do not need and this one
# cannot do without (see `ChartGeometry.min_measured_height`).
CELL_CHART_GEOMETRY = ChartGeometry(min_measured_height=4.0)

FABLE5_CHART_OFFICIAL_LABEL = "Fable 5 official (mini-swe-agent, k of n)"

# The disclosure for `ChartGeometry.min_measured_height`, on the page rather
# than only in that field's comment. The floor exaggerates any very small
# value, not just zero -- a $0.14 cell against a $36 axis draws at the same
# height as a true 0.0 -- and a reader who never hovers has no other way to
# learn that, which makes the two pixel-identical and unexplained.
FLOORED_BAR_NOTE = (
    "Every measured bar is drawn at a minimum visible height, so the shortest bars mean "
    "\"measured and very small\" rather than necessarily zero; the exact figure is in the "
    "per-task table below."
)


def drawn_absence_states(groups: list[ChartGroup]) -> tuple[str, ...]:
    """The absence states this particular chart actually contains, in the
    fixed reporting order, so its legend explains those and only those."""
    present = {bar.absence.state for group in groups for bar in group.bars if bar.absence}
    return tuple(state for state in ABSENCE_STATE_RENDER_ORDER if state in present)


def _schedule_cell_bars(groups: list[ChartGroup]) -> list[Bar]:
    """Every bar EXCEPT the official/Fable 5 one -- the schedule's own
    (task, model, skill) cells, which is what "all cells absent" is about.

    The official slot comes from a wholly different source (the vendored
    DeepSWE snapshot) and can be present even when this harness has not run
    a single trial for the task yet -- exactly the current state of
    `kombu-single-active-consumer-priority`, whose Fable 5 bar has data
    while every one of its own cells is still `not_yet_run` or skipped.
    Counting that bar as "measured" would hide the very thing this chart's
    empty state exists to say.
    """
    return [bar for group in groups for bar in group.bars if bar.slot != OFFICIAL_SLOT]


def all_cells_absent(groups: list[ChartGroup]) -> bool:
    """Whether every one of THIS chart's own schedule cells is absent.

    `render_chart_svg`'s own empty-state branch only fires when `groups`
    itself is empty. A per-task or per-complexity chart still produces one
    group per model even when none of its cells have ever been measured --
    the `kombu-single-active-consumer-priority` task's cost/token charts and
    its "high complexity" chart are exactly this today, since the schedule
    has not been run yet -- so that branch never sees this case and the
    chart renders as a wall of hatched absence marks with no summary line.
    """
    bars = _schedule_cell_bars(groups)
    return bool(bars) and not any(bar.present for bar in bars)


def empty_cell_chart_note(groups: list[ChartGroup]) -> str:
    """The empty-state sentence for a chart with zero measured cells,
    composed from the absence states its own bars already carry -- the same
    source `drawn_absence_states`/`render_legend` read -- so the wording can
    never name a state the chart's own legend does not also explain.
    """
    counts: dict[str, int] = {}
    for bar in _schedule_cell_bars(groups):
        if bar.absence:
            counts[bar.absence.state] = counts.get(bar.absence.state, 0) + 1
    total = sum(counts.values())
    breakdown = ", ".join(
        f"{counts[state]} {ABSENCE_LABELS.get(state, state)}"
        for state in ABSENCE_STATE_RENDER_ORDER
        if counts.get(state)
    )
    return f"No cell here has been measured yet: all {total} are {breakdown}."


def render_cell_chart_figure(
    title: str,
    caption: str,
    groups: list[ChartGroup],
    color_vars: dict[str, str],
    *,
    max_value: float = 1.0,
    tick_formatter: Any | None = None,
) -> str:
    """One per-cell <figure>: caption, two-part legend, chart, sub-caption.

    Separate from `render_chart_figure` rather than a mode of it: this one
    always carries the absence legend, always uses the cell geometry, and
    takes a prose caption naming which baseline view it plots -- three
    things the aggregation figures neither need nor should acquire.

    Prepends an `empty-state` paragraph, ABOVE the `<figure>`, whenever every
    cell this chart could show is absent (see `all_cells_absent`) -- a wall
    of hatched marks with no summary line reads as a rendering bug rather
    than as "nothing measured here yet", which is the one thing this chart
    is actually reporting.
    """
    chart_slots = {bar.slot for group in groups for bar in group.bars}
    chart_color_vars = {slot: var for slot, var in color_vars.items() if slot in chart_slots}
    has_official = any(
        bar.slot == OFFICIAL_SLOT and bar.present for group in groups for bar in group.bars
    )
    legend = render_legend(
        chart_color_vars,
        include_official=has_official,
        official_label=FABLE5_CHART_OFFICIAL_LABEL,
        absence_states=drawn_absence_states(groups),
    )
    svg = render_chart_svg(
        groups,
        CELL_CHART_GEOMETRY,
        color_vars,
        max_value=max_value,
        tick_formatter=tick_formatter,
    )
    empty_state = (
        f"<p class='empty-state'>{html.escape(empty_cell_chart_note(groups))}</p>"
        if all_cells_absent(groups)
        else ""
    )
    return (
        f"{empty_state}"
        f"<figure class='chart-figure'><figcaption>{html.escape(title)}</figcaption>"
        f"{legend}<div class='chart-scroll'>{svg}</div>"
        f"<p class='footnote'>{html.escape(caption)}</p></figure>"
    )


def complexity_connector_note(series: list[ComplexitySeries]) -> str:
    """The reading instructions for the complexity chart's lines.

    Three separate facts, and the reader needs all three: which segments are
    drawn at all, what a break in a line means, and what a dashed line means.
    Built from the series themselves rather than written as a fixed sentence
    so the note cannot drift from what the chart actually drew once the data
    grows past its current single-trial regime.
    """
    connected = [item for item in series if series_has_connector(item)]
    if not connected:
        return (
            "No line is drawn: no series here has measured points at two adjacent complexity "
            "levels. Every mark is one lone observation."
        )

    provisional = [
        item for item in connected if series_connector_style(item) == CONNECTOR_PROVISIONAL
    ]
    # Phrased to avoid subject-verb agreement on a count that is 1 today and
    # will not be tomorrow -- "1 of 3 series are joined up" is wrong English
    # and a footnote about honesty cannot afford to read as unproofed.
    parts = [
        f"Lines are drawn for {len(connected)} of {len(series)} series. A line joins only "
        "adjacent complexity levels that were both measured, so a series measured at low and "
        "high but not medium is drawn as two separate marks — never as one line across the "
        "unmeasured level."
    ]
    if provisional:
        parts.append(
            f"Dashed, faded lines — {len(provisional)} of {len(connected)} here — have at least "
            "one single-trial point behind them: such a line orders the marks for reading, it "
            "does not assert a trend, since one 0-or-1 observation cannot establish one. A solid "
            "line means every point behind it has more than one attempt."
        )
    return " ".join(parts)


def render_complexity_figure(
    series: list[ComplexitySeries],
    color_vars: dict[str, str],
    shapes: dict[str, str],
    complexity_levels: list[str],
) -> str:
    """The complexity chart's <figure>, with the footnote that teaches the
    reader how to read its lines."""
    connector_note = complexity_connector_note(series)
    return (
        "<figure class='chart-figure'>"
        "<figcaption>Pass@1 across task complexity</figcaption>"
        f"{render_complexity_legend(color_vars, shapes)}"
        f"<div class='chart-scroll'>"
        f"{render_complexity_chart_svg(series, CELL_CHART_GEOMETRY, color_vars, shapes, complexity_levels)}"
        f"</div><p class='footnote'>{html.escape(connector_note)}</p></figure>"
    )


def render_task_table(task: str, cells: list[dict[str, Any]], schedule: dict[str, Any]) -> str:
    """One task's exact-value table -- the twin of its charts, and the only
    place an absent cell's full stated reason is readable without hovering."""
    rows_html = []
    for row in task_table_rows(task, cells, schedule):
        state_class = "muted-cell" if row["state"] != MEASURED_STATE else "muted-cell measured-cell"
        rows_html.append(
            "<tr>"
            f"<td>{html.escape(row['model'])}</td>"
            f"<td>{html.escape(row['skill'])}</td>"
            f"<td>{html.escape(row['outcome'])}</td>"
            f"<td class='num'>{row['cost']}</td>"
            f"<td class='num'>{row['output_tokens']}</td>"
            f"<td class='{state_class}'>{html.escape(row['state'])}</td>"
            f"<td class='muted-cell reason-cell'>{html.escape(row['reason'])}</td>"
            "</tr>"
        )
    header = (
        "<tr><th>Model</th><th>Skill</th><th>Outcome</th><th class='num'>Avg cost</th>"
        "<th class='num'>Avg output tokens</th><th>State</th><th>Why, if absent</th></tr>"
    )
    return (
        "<div class='table-scroll'><table class='arm-table'>"
        f"<thead>{header}</thead><tbody>{''.join(rows_html)}</tbody></table></div>"
    )


def render_cell_coverage(cells: list[dict[str, Any]], vocabulary: dict[str, str]) -> str:
    """How much of the planned matrix has actually been measured, state by
    state, each row carrying collect.py's own definition of that state.

    Leads the per-cell sections deliberately: with 41 of 46 cells absent, a
    reader who meets the charts first will read a page of blank slots as a
    page of failures. The counts up front reframe every later chart.
    """
    counts = summarize_cell_states(cells)
    total = sum(counts.values())
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(state)}</td>"
        f"<td class='num'>{counts[state]}</td>"
        f"<td class='muted-cell reason-cell'>{html.escape(vocabulary.get(state, ''))}</td>"
        "</tr>"
        for state in CELL_STATE_REPORT_ORDER
    )
    return (
        f"<p class='footnote'>{total} cells in the (task × model × skill) matrix.</p>"
        "<div class='table-scroll'><table class='arm-table'><thead>"
        "<tr><th>State</th><th class='num'>Cells</th><th>What it means</th></tr>"
        f"</thead><tbody>{rows}</tbody></table></div>"
    )


def render_fable5_summary(baseline: dict[str, Any]) -> str:
    """The Fable 5 whole-benchmark headline as a definition list.

    Its interval appears here as TEXT and nowhere else. `comparability.
    co_plotting_intervals_allowed` is false, and a table cell reading
    "run-to-run SE across 4 whole-benchmark passes, not a binomial CI" is
    the only rendering of it that cannot be mistaken for a peer error bar.
    """
    pairs = fable5_aggregate_summary(baseline)
    if not pairs:
        return ""
    rows = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in pairs)
    return f"<dl class='run-metadata'>{rows}</dl>"


def render_fable5_comparison_table(
    baseline: dict[str, Any], cells: list[dict[str, Any]], schedule: dict[str, Any]
) -> str:
    """Fable 5 against this harness, per task -- counts on both sides.

    Every leaderboard figure is a k-of-n so its denominator travels with it,
    and the local column counts trials for the same reason. Nothing in this
    table is a bare rate, because the two sides' rates are not comparable
    (different harness, different denominator unit) and putting them side by
    side as percentages would invite exactly the subtraction that
    `comparability.like_for_like = false` rules out.
    """
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td class='muted-cell'>{html.escape(row['complexity'])}</td>"
        f"<td class='num'>{html.escape(row['fable5_pooled'])}</td>"
        f"<td class='num'>{html.escape(row['fable5_headline'])}</td>"
        f"<td class='num'>{html.escape(row['fable5_cost'])}</td>"
        f"<td>{html.escape(row['local'])}</td>"
        "</tr>"
        for row in fable5_comparison_rows(baseline, cells, schedule)
    )
    header = (
        "<tr><th>Task</th><th>Complexity</th>"
        "<th class='num'>Fable 5, all efforts pooled (k/n, n=20)</th>"
        "<th class='num'>Fable 5, headline max config (k/n, n=4)</th>"
        "<th class='num'>Fable 5 mean cost</th>"
        "<th>This harness (claude-code), contributing arms named</th></tr>"
    )
    return (
        "<div class='table-scroll'><table class='arm-table'>"
        f"<thead>{header}</thead><tbody>{rows}</tbody></table></div>"
    )


def render_fable5_aggregate_note(baseline: dict[str, Any]) -> str:
    """Names what the Fable 5 category on an aggregation chart actually is.

    Every field in the sentence is read from the baseline rather than
    written here, so the config name and the denominator unit printed under
    the chart are the same strings the official-baseline table prints.
    """
    headline = fable5_aggregate_headline(baseline)
    if not headline:
        return ""
    figure = headline.get("pass_at_1") or {}
    comparability = (baseline.get("fable5") or {}).get("comparability") or {}
    text = (
        f"The outlined Fable 5 column is that model's whole-benchmark headline figure "
        f"({headline.get('config', 'config not named in the snapshot')}): "
        f"{format_k_of_n(figure)} {figure.get('denominator_unit', '')} on "
        f"{comparability.get('baseline_harness', 'a different harness')}. It is a different "
        f"model on a different harness from every other bar here — outlined rather than "
        f"coloured for that reason, and not a like-for-like comparison. Its published "
        f"interval is a run-to-run standard error, not a binomial CI, so it is reported as "
        f"text in the official-baseline section below and never drawn as a whisker."
    )
    return f"<p class='footnote'>{html.escape(text)}</p>"


def render_fable5_footnote(baseline: dict[str, Any]) -> str:
    """The honesty footnote for every Fable 5 rendering, sourced from the
    baseline's own `comparability` fields so the caveat cannot drift from
    the data it qualifies."""
    fable5 = baseline.get("fable5") or {}
    if not fable5.get("available"):
        return ""
    comparability = fable5.get("comparability") or {}
    source = fable5.get("source") or {}
    parts = [
        comparability.get("harness_note", ""),
        comparability.get("interval_note", ""),
        comparability.get("denominator_note", ""),
        f"Retrieved {source.get('retrieved_date', 'unknown')} from {source.get('site', '')}.",
    ]
    return f"<p class='footnote'>{html.escape(' '.join(p for p in parts if p))}</p>"


def render_arm_table(arms: list[dict[str, Any]]) -> str:
    """The table-view twin of both charts -- every value plotted above is
    also reachable here without hovering anything (dataviz accessibility
    rule: a table view exists for every chart)."""
    rows_html = []
    for row in arm_table_rows(arms):
        # A single combined `class` attribute -- two separate class="..."
        # attributes on one element is invalid HTML and silently drops the
        # second one in most browsers, which would make has-errors a no-op.
        errored_cell_class = "num has-errors" if row["n_errored"] != "0" else "num"
        # Same emphasis treatment as Errored: both are counts an operator
        # wants to read as zero, and a bolded non-zero is what makes an
        # abandoned trial visible at a glance instead of blending into the
        # numbers beside it.
        incomplete_cell_class = "num has-errors" if row["n_incomplete"] != "0" else "num"
        rows_html.append(
            "<tr>"
            f"<td>{html.escape(row['arm_id'])}</td>"
            f"<td class='num'>{row['pass_at_1']}</td>"
            f"<td class='num'>{row['avg_cost_usd']}</td>"
            f"<td class='num'>{row['max_cost_usd']}</td>"
            f"<td class='num'>{row['avg_output_tokens']}</td>"
            f"<td class='num'>{row['avg_n_agent_steps']}</td>"
            f"<td class='{incomplete_cell_class}'>{row['n_incomplete']}</td>"
            f"<td class='{errored_cell_class}'>{row['n_errored']}</td>"
            "</tr>"
        )
    header = (
        "<tr><th>Arm</th><th class='num'>Pass@1 ± CI</th><th class='num'>Avg cost</th>"
        "<th class='num'>Max cost</th>"
        "<th class='num'>Avg output tokens</th><th class='num'>Avg steps</th>"
        "<th class='num'>Incomplete</th><th class='num'>Errored</th></tr>"
    )
    return (
        "<div class='table-scroll'><table class='arm-table'>"
        f"<thead>{header}</thead><tbody>{''.join(rows_html)}</tbody></table></div>"
    )


_RUN_DATE_NOT_RECORDED_TEXT = "not recorded in results.json (see run.py's arm.json created_at field)"
_SEED_NOT_RECORDED_TEXT = "not recorded in results.json (see run.py's pinned SAMPLE_SEED)"


def format_run_started_at(run_started_at: str | None, *, has_run_metadata_fields: bool) -> str:
    """The header's "Run started" value: the real run-start timestamp when
    `results.json` carries one, or an honest disclosure of its absence --
    never a substitute value (report-build time is a different moment
    entirely and must not occupy this slot silently)."""
    if run_started_at is not None:
        return f"{datetime.fromisoformat(run_started_at):%Y-%m-%d %H:%M UTC}"
    if has_run_metadata_fields:
        return "unavailable (no arm recorded a created_at)"
    return _RUN_DATE_NOT_RECORDED_TEXT


def format_sample_seed(sample_seed: int | None, *, has_run_metadata_fields: bool) -> str:
    """The header's "Sample seed" value. A `results.json` new enough to carry
    the field but showing `None` means the run mode simply wasn't "sample"
    (the seed plays no role then); an older `results.json` never captured
    the field at all -- these are different facts and get different text."""
    if sample_seed is not None:
        return str(sample_seed)
    if has_run_metadata_fields:
        return "not applicable (run mode was not 'sample')"
    return _SEED_NOT_RECORDED_TEXT


def render_run_metadata_header(metadata: dict[str, Any], generated_at: datetime, n_arms: int) -> str:
    """The run-metadata header: run-start date, report-build timestamp, task
    count, seed, pinned CEK ref(s), Claude Code version(s). "Run started" and
    "Sample seed" both fall back to an honest disclosure rather than a
    guessed or substituted value when `results.json` predates the schema
    version that captures them -- see `summarize_run_metadata`'s docstring.
    """
    has_run_metadata_fields = metadata["has_run_metadata_fields"]
    run_started_text = format_run_started_at(
        metadata["run_started_at"], has_run_metadata_fields=has_run_metadata_fields
    )
    seed_text = format_sample_seed(
        metadata["sample_seed"], has_run_metadata_fields=has_run_metadata_fields
    )
    plugin_refs = ", ".join(html.escape(ref) for ref in metadata["plugin_refs"]) or "—"
    cc_versions = ", ".join(html.escape(v) for v in metadata["claude_code_versions"]) or "—"
    items = [
        ("Run started", run_started_text),
        ("Report generated", generated_at.strftime("%Y-%m-%d %H:%M UTC")),
        ("Tasks", str(metadata["n_tasks"])),
        ("Trials", str(metadata["n_trials"])),
        ("Arms", str(n_arms)),
        ("Sample seed", seed_text),
        ("Plugin ref (CEK)", plugin_refs),
        ("Claude Code version", cc_versions),
    ]
    rows = "".join(f"<dt>{html.escape(k)}</dt><dd>{v}</dd>" for k, v in items)
    return f"<dl class='run-metadata'>{rows}</dl>"


def build_complexity_sections(
    cells: list[dict[str, Any]],
    schedule: dict[str, Any],
    baseline: dict[str, Any],
    color_vars: dict[str, str],
) -> list[str]:
    """One pass@1 chart per complexity level, plus the complexity chart."""
    sections = ["<h2>Pass@1 by task complexity</h2>"]
    for level in schedule.get("complexity_levels", []):
        groups = build_complexity_chart_groups(level, cells, schedule, baseline)
        sections.append(
            render_cell_chart_figure(
                f"{level} complexity — pass@1 by model and skill",
                "Bars are this harness (claude-code). The outlined Fable 5 bar is "
                f"mini-swe-agent, {FABLE5_POOLED_VIEW_PHRASE}, labelled as k of n scored "
                f"rollout attempts — not a like-for-like comparison. {FLOORED_BAR_NOTE}",
                groups,
                color_vars,
            )
        )

    series = build_complexity_series(cells, schedule)
    shapes = assign_model_marker_shapes(schedule_model_names(schedule))
    sections.append(
        render_complexity_figure(series, color_vars, shapes, schedule.get("complexity_levels", []))
    )
    return sections


def build_per_task_sections(
    cells: list[dict[str, Any]],
    schedule: dict[str, Any],
    baseline: dict[str, Any],
    color_vars: dict[str, str],
) -> list[str]:
    """Per task: a cost chart, a token chart, and the exact-value table."""
    sections = ["<h2>Per-task detail</h2>"]
    for task in tasks_in_report_order(schedule, cells):
        name = task["name"]
        complexity = task["complexity"] or "not ranked in schedule.yaml"
        sections.append(f"<h3>{html.escape(name)} <span class='muted'>({html.escape(complexity)})</span></h3>")

        for cell_field, baseline_field, formatter, label in (
            ("avg_cost_usd", "mean_cost_usd", format_usd, "cost per attempt"),
            ("avg_output_tokens", "mean_output_tokens", format_count, "output tokens per attempt"),
        ):
            groups = build_task_measure_chart_groups(
                name, cells, schedule, baseline, cell_field, baseline_field, formatter
            )
            sections.append(
                render_cell_chart_figure(
                    f"{name} — {label}",
                    "Absent cells carry no cost or token figures at all; a missing bar is a "
                    "missing measurement, never a zero. The outlined bar is Fable 5's mean "
                    f"on mini-swe-agent, {FABLE5_POOLED_VIEW_PHRASE}, shown for scale rather "
                    f"than as a peer. {FLOORED_BAR_NOTE}",
                    groups,
                    color_vars,
                    max_value=chart_max_value(groups, fixed_max=None),
                    tick_formatter=formatter,
                )
            )
        sections.append(render_task_table(name, cells, schedule))
    return sections


def build_baseline_sections(
    leaderboard: dict[str, Any],
    baseline: dict[str, Any],
    cells: list[dict[str, Any]],
    schedule: dict[str, Any],
) -> list[str]:
    """The official-baseline block: the pre-existing leaderboard table, then
    the Fable 5 headline and the per-task comparison beneath the same
    heading -- extending the established "official data lives here, outlined
    and footnoted" convention rather than opening a rival section for it."""
    sections = [
        "<h2>Official baseline (mini-swe-agent, not claude-code)</h2>",
        render_official_baseline_table(leaderboard),
    ]
    summary = render_fable5_summary(baseline)
    if summary:
        sections += [
            "<h3>Fable 5, whole benchmark</h3>",
            summary,
            "<h3>Fable 5 vs. this harness, per task</h3>",
            render_fable5_comparison_table(baseline, cells, schedule),
            render_fable5_footnote(baseline),
        ]
    return sections


def assign_page_color_vars(
    aggregation_groups: list[ChartGroup], schedule: dict[str, Any]
) -> dict[str, str]:
    """One colour assignment for the whole page.

    Built from the union of every skill any chart can show -- the
    aggregation charts' arm skills plus the schedule's declared skills --
    so a skill keeps the same hue from the top of the page to the bottom.
    Assigning per chart would repaint a series as the reader scrolled,
    which is the "recolor-on-filter" anti-pattern the sorted-name rule in
    `assign_categorical_color_vars` exists to prevent.

    The 3-slot cap still applies here, unweakened: the per-cell charts stay
    inside it by putting their 5 models on the marker-shape channel rather
    than asking the palette for more hues.
    """
    arm_slots = {
        bar.slot
        for group in aggregation_groups
        for bar in group.bars
        if bar.slot != OFFICIAL_SLOT
    }
    return assign_categorical_color_vars(sorted(arm_slots | set(schedule_skill_names(schedule))))


def build_report_html(
    results: dict[str, Any], leaderboard: dict[str, Any], *, generated_at: datetime
) -> str:
    """Assembles the full report page. The only impure input is
    `generated_at` (supplied by main() from a single `datetime.now()` call)
    -- everything else here is a deterministic function of `results` and
    `leaderboard`, so the whole page is reproducible byte-for-byte given
    the same three inputs.
    """
    arms = results.get("arms", [])
    trials = results.get("trials", [])
    cells = results.get("cells", [])
    schedule = results.get("schedule", {})
    baseline = results.get("baseline", {})
    metadata = summarize_run_metadata(trials, arms, schema_version=results.get("schema_version"))

    matched_groups = build_matched_chart_groups(arms, leaderboard)
    mixed_groups = build_mixed_chart_groups(arms, leaderboard)
    color_vars = assign_page_color_vars([*matched_groups, *mixed_groups], schedule)
    geometry = ChartGeometry()

    sections = [
        render_shared_svg_defs(),
        render_run_metadata_header(metadata, generated_at, n_arms=len(arms)),
        render_chart_figure(
            "Matched arms (orchestrator = impl) vs. official baseline",
            # Extended here, not inside `build_matched_chart_groups`, so that
            # builder keeps describing exactly the matched arms it always did.
            with_fable5_aggregate_group(matched_groups, baseline),
            geometry,
            color_vars,
            leaderboard,
            extra_footnote=render_fable5_aggregate_note(baseline),
        ),
        render_chart_figure(
            "Mixed arms (orchestrator ≠ impl) vs. official baseline",
            mixed_groups,
            geometry,
            color_vars,
            leaderboard,
        ),
    ]
    if cells:
        sections += [
            "<h2>Matrix coverage</h2>",
            render_cell_coverage(cells, results.get("cell_state_vocabulary", {})),
        ]
        sections += build_complexity_sections(cells, schedule, baseline, color_vars)
        sections += build_per_task_sections(cells, schedule, baseline, color_vars)

    sections += build_baseline_sections(leaderboard, baseline, cells, schedule)
    sections += ["<h2>Arm results</h2>", render_arm_table(arms)]
    # A plain marker + str.replace, not str.format -- PAGE_CSS/THEME_TOGGLE_
    # SCRIPT are already baked into PAGE_TEMPLATE and are full of literal
    # `{`/`}` (CSS rules, JS blocks), which .format() would misparse as
    # format fields.
    return PAGE_TEMPLATE.replace("__REPORT_BODY__", "".join(sections))


# --------------------------------------------------------------------------
# Page chrome: CSS + the theme toggle's tiny inline script
# --------------------------------------------------------------------------

# Palette values are the dataviz skill's validated default categorical
# slots 1-3 (blue/orange/aqua) and its documented chart chrome/ink roles --
# see references/palette.md. Re-validated for this report's actual 3-series
# use with `node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a"
# --mode light` / `--mode dark`: all hard gates pass (worst adjacent CVD
# 9.2 light / 9.4 dark; light-mode aqua sits below 3:1 contrast, mitigated
# below by the bar tip's direct value label -- the palette's own documented
# "relief rule").
PAGE_CSS = """
:root {
  color-scheme: light;
  --surface-page: #f9f9f7;
  --surface-1: #fcfcfb;
  --text-primary: #0b0b0b;
  --text-secondary: #52514e;
  --text-muted: #898781;
  --grid-line: #e1e0d9;
  --axis-line: #c3c2b7;
  --border: rgba(11, 11, 11, 0.10);
  --official-outline: #52514e;
  --absence-fill: rgba(11, 11, 11, 0.035);
  --absence-ink: #a9a79f;
  --accent: #2a78d6;
  --series-1: #2a78d6;
  --series-2: #eb6834;
  --series-3: #1baf7a;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --surface-page: #0d0d0d;
    --surface-1: #1a1a19;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #898781;
    --grid-line: #2c2c2a;
    --axis-line: #383835;
    --border: rgba(255, 255, 255, 0.10);
    --official-outline: #c3c2b7;
    --absence-fill: rgba(255, 255, 255, 0.045);
    --absence-ink: #6b6a65;
    --accent: #3987e5;
    --series-1: #3987e5;
    --series-2: #d95926;
    --series-3: #199e70;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --surface-page: #0d0d0d;
  --surface-1: #1a1a19;
  --text-primary: #ffffff;
  --text-secondary: #c3c2b7;
  --text-muted: #898781;
  --grid-line: #2c2c2a;
  --axis-line: #383835;
  --border: rgba(255, 255, 255, 0.10);
  --official-outline: #c3c2b7;
  --absence-fill: rgba(255, 255, 255, 0.045);
  --absence-ink: #6b6a65;
  --accent: #3987e5;
  --series-1: #3987e5;
  --series-2: #d95926;
  --series-3: #199e70;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 24px 64px;
  background: var(--surface-page);
  color: var(--text-primary);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
main { max-width: 880px; margin: 0 auto; }
h1 { font-size: 20px; margin: 0 0 4px; }
h2 { font-size: 15px; margin: 32px 0 12px; color: var(--text-primary); }
p.subtitle { color: var(--text-secondary); margin: 0 0 24px; }
.theme-toggle {
  position: fixed; top: 16px; right: 16px;
  border: 1px solid var(--border); background: var(--surface-1);
  color: var(--text-primary); border-radius: 6px; padding: 6px 10px;
  font: 12px system-ui, sans-serif; cursor: pointer;
}
.theme-toggle:focus-visible { outline: 2px solid var(--accent); }
dl.run-metadata {
  display: grid; grid-template-columns: max-content 1fr;
  column-gap: 12px; row-gap: 4px; margin: 0 0 32px;
  font-variant-numeric: tabular-nums;
}
dl.run-metadata dt { color: var(--text-muted); }
dl.run-metadata dd { margin: 0; color: var(--text-secondary); }
.chart-figure {
  margin: 0 0 8px; padding: 16px; background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 8px;
}
.chart-figure figcaption { font-weight: 600; margin-bottom: 8px; }
.chart-scroll { overflow-x: auto; }
.legend { list-style: none; display: flex; flex-wrap: wrap; gap: 12px 16px; padding: 0; margin: 0 0 8px; color: var(--text-secondary); }
.legend li { display: flex; align-items: center; gap: 6px; }
.swatch { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.swatch-outline { border: 2px solid var(--official-outline); background: transparent; box-sizing: border-box; }
/* --text-secondary, not --text-muted: this footnote carries the official-bar
   honesty caveat, normal-size body text that must clear WCAG AA's 4.5:1 --
   --text-muted (#898781 vs light surface #f9f9f7) only reaches 3.41:1. */
.footnote { color: var(--text-secondary); font-size: 12px; margin: 12px 0 0; }
.footnote a { color: var(--text-secondary); }
.empty-state { color: var(--text-muted); font-style: italic; }
.gridline { stroke: var(--grid-line); stroke-width: 1; }
.baseline { stroke: var(--axis-line); stroke-width: 1; }
.axis-label { fill: var(--text-muted); font-size: 10px; font-family: system-ui, sans-serif; }
.group-label { fill: var(--text-secondary); font-size: 11px; }
.table-scroll { overflow-x: auto; }
table.arm-table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
table.arm-table th, table.arm-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); text-align: left; }
table.arm-table th.num, table.arm-table td.num { text-align: right; }
table.arm-table td.has-errors { font-weight: 600; }
table.arm-table td.muted-cell { color: var(--text-muted); font-size: 12px; }
table.arm-table thead th { color: var(--text-muted); font-weight: 500; font-size: 12px; }
h3 { font-size: 14px; margin: 24px 0 8px; color: var(--text-primary); }
.muted { color: var(--text-muted); font-weight: 400; }
svg.svg-defs { position: absolute; width: 0; height: 0; overflow: hidden; }
/* The glyph is the only text inside an absence slot and must stay legible
   against the hatch at 20px of bar width -- hence --text-secondary (WCAG AA
   against both surfaces) rather than the fainter --absence-ink the hatch
   strokes themselves use. */
.absence-glyph { fill: var(--text-secondary); font-size: 11px; font-family: system-ui, sans-serif; }
.bar-value-label { fill: var(--text-secondary); font-size: 10px; font-family: system-ui, sans-serif; }
.legend-channel { color: var(--text-muted); font-size: 12px; }
.legend-shape { width: 14px; height: 14px; }
.swatch-hatch {
  border: 1px dashed var(--absence-ink); background: var(--absence-fill);
  width: 14px; height: 14px; border-radius: 2px; display: inline-flex;
  align-items: center; justify-content: center; font-size: 9px;
  color: var(--text-secondary); box-sizing: border-box;
}
.swatch-blank {
  border: 1px dotted var(--absence-ink); background: transparent; box-sizing: border-box;
  width: 14px; height: 14px; display: inline-flex; align-items: flex-end; justify-content: center;
}
/* The swatch's dot and the chart's dot are the same statement -- both sit on
   the bottom edge of their box, because on the chart that edge is the axis
   baseline. */
.swatch-dot { width: 3px; height: 3px; border-radius: 50%; background: var(--absence-ink); margin-bottom: 1px; }
.absence-dot { fill: var(--absence-ink); }
/* Reasons are full sentences from schedule.yaml and are the point of the
   column, so they wrap instead of stretching the table off the page. */
table.arm-table td.reason-cell { max-width: 340px; white-space: normal; }
table.arm-table td.measured-cell { color: var(--text-secondary); }
"""

# Manual light/dark override on top of prefers-color-scheme -- persists to
# localStorage so a reader's choice survives a reload of this same file.
THEME_TOGGLE_SCRIPT = """
(function () {
  var root = document.documentElement;
  var stored = localStorage.getItem('deep-swe-report-theme');
  if (stored) root.setAttribute('data-theme', stored);
  var button = document.getElementById('theme-toggle');
  button.addEventListener('click', function () {
    var current = root.getAttribute('data-theme')
      || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = current === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('deep-swe-report-theme', next);
  });
})();
"""

PAGE_TEMPLATE = (
    "<!doctype html><html lang='en'><head><meta charset='utf-8'/>"
    "<meta name='viewport' content='width=device-width, initial-scale=1'/>"
    "<title>Deep-SWE benchmark report</title>"
    f"<style>{PAGE_CSS}</style></head><body>"
    "<button id='theme-toggle' class='theme-toggle' type='button'>Toggle theme</button>"
    "<main><h1>Deep-SWE benchmark report</h1>"
    "<p class='subtitle'>claude-code + sadd plugin arms vs. the official DeepSWE leaderboard</p>"
    "__REPORT_BODY__</main>"
    f"<script>{THEME_TOGGLE_SCRIPT}</script>"
    "</body></html>"
)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render results.json + the vendored leaderboard snapshot into a self-contained report.html."
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="collect.py's output to render (default: %(default)s).",
    )
    parser.add_argument(
        "--leaderboard",
        type=Path,
        default=DEFAULT_LEADERBOARD_PATH,
        help="Vendored DeepSWE leaderboard snapshot (default: %(default)s).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_PATH,
        help="Where to write the HTML report (default: %(default)s).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    results = load_results(args.results)
    leaderboard = load_leaderboard(args.leaderboard)
    html_text = build_report_html(results, leaderboard, generated_at=datetime.now(timezone.utc))

    args.out.write_text(html_text)
    print(
        f"[report] wrote {args.out} "
        f"({len(results.get('arms', []))} arms, {len(results.get('trials', []))} trials)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
