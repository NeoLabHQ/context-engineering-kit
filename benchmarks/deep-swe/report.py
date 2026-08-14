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
appear: unfilled (stroke only, no categorical hue), plus a footnote sourced
from leaderboard.json's own `honesty_note`/`snapshot_date`/`source_url`
fields (never hand-duplicated text) explaining why. See `_official_bar`,
`render_bar_mark`, and `render_official_baseline_footnote`.

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
# function's docstring).
EXPECTED_RESULTS_SCHEMA_VERSION = 2
MIN_SCHEMA_VERSION_WITH_RUN_METADATA = 2

# Ordinal capability order -- fixed, not alphabetical (alphabetical would
# print "haiku, opus, sonnet", scrambling the reader's mental model of
# ascending model capability). Every chart/group iterates in this order.
TIER_ORDER: tuple[str, ...] = ("haiku", "sonnet", "opus")


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
class Bar:
    """One bar's value + Wilson (or DeepSWE run-to-run) CI, or an explicit
    absence.

    `present=False` means "there is nothing to draw here" -- a tier missing
    from the leaderboard, an arm that never ran, or an arm that ran but had
    zero valid attempts (collect.py's `pass_at_1 is None` case). Renderers
    must skip these entirely rather than drawing a zero-height bar; see the
    module docstring's "NULL-HANDLING PHILOSOPHY" section.
    """

    slot: str
    present: bool
    value: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    outlined: bool = False  # True only for the official (leaderboard) bar


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
    """
    tier_data = leaderboard.get("tiers", {}).get(tier)
    if tier_data is None or not tier_data.get("present_on_leaderboard"):
        return Bar(slot="official", present=False, outlined=True)
    return Bar(
        slot="official",
        present=True,
        outlined=True,
        value=tier_data["pass_at_1"],
        ci_low=tier_data["ci_low"],
        ci_high=tier_data["ci_high"],
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
    )


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
                "pass_at_1": format_pass_at_1_with_ci(
                    arm["pass_at_1"], arm["pass_at_1_ci_low"], arm["pass_at_1_ci_high"]
                ),
                "avg_cost_usd": format_usd(arm["avg_cost_usd"]),
                "avg_output_tokens": format_count(arm["avg_output_tokens"]),
                "avg_n_agent_steps": format_count(arm["avg_n_agent_steps"]),
                "n_errored": str(arm["n_errored"]),
            }
        )
    return rows


# --------------------------------------------------------------------------
# SVG rendering
# --------------------------------------------------------------------------

WHISKER_CAP_HALF_WIDTH = 5.0


def render_bar_mark(placed: PlacedBar, geometry: ChartGeometry, color_var: str | None) -> str:
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
        return ""

    top, height = bar_vertical_extent(bar.value, geometry)
    path = rounded_top_rect_path(placed.x, top, placed.width, height, radius=4.0)
    center_x = placed.x + placed.width / 2
    tooltip = f"{placed.group_label} · {bar.slot}: {bar.value * 100:.0f}%"

    if bar.outlined:
        # Official baseline: stroke only, no categorical fill -- see module
        # docstring's "THE OFFICIAL-BASELINE BARS..." section for why.
        fill_attr = 'fill="transparent" stroke="var(--official-outline)" stroke-width="2"'
    else:
        fill_attr = f'fill="var({color_var})"'

    parts = [f"<g><title>{html.escape(tooltip)}</title>", f'<path d="{path}" {fill_attr}/>']
    if bar.ci_low is not None and bar.ci_high is not None:
        parts.append(render_whisker(center_x, bar.ci_low, bar.ci_high, geometry))
    parts.append("</g>")
    return "".join(parts)


def render_whisker(center_x: float, ci_low: float, ci_high: float, geometry: ChartGeometry) -> str:
    """A 2px whisker line from ci_low to ci_high with short end caps --
    correctly spans the full plot at ci_low=0/ci_high=1 (see
    whisker_vertical_extent's docstring)."""
    y_high, y_low = whisker_vertical_extent(ci_low, ci_high, geometry)
    cap = WHISKER_CAP_HALF_WIDTH
    return (
        f'<g class="whisker" stroke="var(--text-secondary)" stroke-width="1.5" stroke-linecap="round">'
        f'<line x1="{center_x:.1f}" y1="{y_high:.1f}" x2="{center_x:.1f}" y2="{y_low:.1f}"/>'
        f'<line x1="{center_x - cap:.1f}" y1="{y_high:.1f}" x2="{center_x + cap:.1f}" y2="{y_high:.1f}"/>'
        f'<line x1="{center_x - cap:.1f}" y1="{y_low:.1f}" x2="{center_x + cap:.1f}" y2="{y_low:.1f}"/>'
        f"</g>"
    )


def render_chart_svg(
    groups: list[ChartGroup], geometry: ChartGeometry, color_vars: dict[str, str]
) -> str:
    """The full <svg> for one grouped bar chart: gridlines, baseline, every
    bar/whisker/label, and x-axis group labels. Returns an empty-state
    string instead of a degenerate 0-width svg when there is nothing to
    plot (see components.md's "Empty state" component)."""
    if not groups:
        return '<p class="empty-state">No arms recorded for this chart yet.</p>'

    content_width = chart_content_width(groups, geometry)
    svg_width = geometry.plot_left + content_width + geometry.right_margin
    x_axis_band = 22.0
    svg_height = geometry.plot_top + geometry.plot_height + x_axis_band

    grid_lines = []
    for y, label in y_axis_ticks(geometry):
        grid_lines.append(
            f'<line x1="{geometry.plot_left:.1f}" y1="{y:.1f}" '
            f'x2="{geometry.plot_left + content_width:.1f}" y2="{y:.1f}" '
            f'class="{"baseline" if label == "0%" else "gridline"}"/>'
        )
        grid_lines.append(
            f'<text class="axis-label" x="{geometry.plot_left - 8:.1f}" y="{y + 3:.1f}" '
            f'text-anchor="end">{label}</text>'
        )

    bars = [
        render_bar_mark(placed, geometry, color_vars.get(placed.bar.slot))
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


# --------------------------------------------------------------------------
# HTML assembly
# --------------------------------------------------------------------------


def render_legend(color_vars: dict[str, str], *, include_official: bool) -> str:
    """A legend row: one swatch per categorical series plus, when the chart
    carries an official bar, an outlined swatch explaining it. Always
    present for >=2 series per the dataviz mark spec -- the dependable
    identity channel a reader can rely on instead of color-matching alone.
    """
    items = [
        f'<li><span class="swatch" style="background:var({var})"></span>{html.escape(slot)}</li>'
        for slot, var in sorted(color_vars.items(), key=lambda kv: kv[1])
    ]
    if include_official:
        items.append('<li><span class="swatch swatch-outline"></span>official (mini-swe-agent)</li>')
    return f'<ul class="legend">{"".join(items)}</ul>'


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
) -> str:
    """One <figure> = caption + legend + scrollable svg wrapper. The
    overflow-x wrapper keeps a wide chart from breaking the page's own
    horizontal scroll (see dataviz anti-patterns.md)."""
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
        f"{legend}<div class='chart-scroll'>{svg}</div>{footnote}</figure>"
    )


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
        rows_html.append(
            "<tr>"
            f"<td>{html.escape(row['arm_id'])}</td>"
            f"<td class='num'>{row['pass_at_1']}</td>"
            f"<td class='num'>{row['avg_cost_usd']}</td>"
            f"<td class='num'>{row['avg_output_tokens']}</td>"
            f"<td class='num'>{row['avg_n_agent_steps']}</td>"
            f"<td class='{errored_cell_class}'>{row['n_errored']}</td>"
            "</tr>"
        )
    header = (
        "<tr><th>Arm</th><th class='num'>Pass@1 ± CI</th><th class='num'>Avg cost</th>"
        "<th class='num'>Avg output tokens</th><th class='num'>Avg steps</th>"
        "<th class='num'>Errored</th></tr>"
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
    metadata = summarize_run_metadata(trials, arms, schema_version=results.get("schema_version"))

    matched_groups = build_matched_chart_groups(arms, leaderboard)
    mixed_groups = build_mixed_chart_groups(arms, leaderboard)
    all_slots = {
        bar.slot
        for group in (*matched_groups, *mixed_groups)
        for bar in group.bars
        if bar.slot != "official"
    }
    color_vars = assign_categorical_color_vars(sorted(all_slots))
    geometry = ChartGeometry()

    sections = [
        render_run_metadata_header(metadata, generated_at, n_arms=len(arms)),
        render_chart_figure(
            "Matched arms (orchestrator = impl) vs. official baseline",
            matched_groups,
            geometry,
            color_vars,
            leaderboard,
        ),
        render_chart_figure(
            "Mixed arms (orchestrator ≠ impl) vs. official baseline",
            mixed_groups,
            geometry,
            color_vars,
            leaderboard,
        ),
        "<h2>Official baseline (mini-swe-agent, not claude-code)</h2>",
        render_official_baseline_table(leaderboard),
        "<h2>Arm results</h2>",
        render_arm_table(arms),
    ]
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
