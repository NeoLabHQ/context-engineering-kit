"""Shared arm-dict factory and real-leaderboard loader for `report.py` tests.

Kept in its own module so every `test_report_*.py` file shares one
authoritative arm shape and one loader for the real vendored leaderboard
snapshot, rather than each file restating its own copy.
"""

from __future__ import annotations

import json
from typing import Any

from . import BENCHMARK_DIR

REAL_LEADERBOARD_PATH = BENCHMARK_DIR / "data" / "leaderboard.json"


def load_real_leaderboard() -> dict[str, Any]:
    """The actual vendored snapshot, not a synthetic stand-in -- used to test
    the genuinely-absent-tier behavior (haiku) against real data rather than
    a fixture that could drift from what's really shipped.
    """
    return json.loads(REAL_LEADERBOARD_PATH.read_text())


def make_arm(
    *,
    arm_id: str = "arm-1",
    skill: str | None = "skill-a",
    orchestrator: str = "sonnet",
    impl: str | None = "sonnet",
    is_vanilla: bool = False,
    pass_at_1: float | None = 0.5,
    pass_at_1_ci_low: float | None = 0.4,
    pass_at_1_ci_high: float | None = 0.6,
    avg_cost_usd: float | None = 1.0,
    max_cost_usd: float | None = 2.0,
    avg_output_tokens: float | None = 100.0,
    avg_n_agent_steps: float | None = 10.0,
    n_incomplete: int = 0,
    n_errored: int = 0,
    created_at: str | None = None,
    sample_seed: int | None = None,
) -> dict[str, Any]:
    """A `results.json`-shaped arm dict with every field build_*_chart_groups/
    arm_table_rows/etc. reads, so tests can vary just what they care about.
    """
    return {
        "arm_id": arm_id,
        "skill": skill,
        "orchestrator": orchestrator,
        "impl": impl,
        "is_vanilla": is_vanilla,
        "n_resolved": 5,
        "n_unresolved": 5,
        "n_incomplete": n_incomplete,
        "n_errored": n_errored,
        "n_attempts": 10 + n_incomplete,
        "n_total_trials": 10 + n_incomplete + n_errored,
        "pass_at_1": pass_at_1,
        "pass_at_1_ci_low": pass_at_1_ci_low,
        "pass_at_1_ci_high": pass_at_1_ci_high,
        "avg_cost_usd": avg_cost_usd,
        "max_cost_usd": max_cost_usd,
        "avg_output_tokens": avg_output_tokens,
        "avg_n_agent_steps": avg_n_agent_steps,
        "created_at": created_at,
        "sample_seed": sample_seed,
    }


def make_measured(
    *,
    n_resolved: int = 1,
    n_attempts: int = 1,
    pass_at_1: float | None = 1.0,
    is_single_trial: bool = True,
    pass_at_1_ci_low: float | None = None,
    pass_at_1_ci_high: float | None = None,
    avg_cost_usd: float | None = 2.5,
    avg_output_tokens: float | None = 1200.0,
) -> dict[str, Any]:
    """A `cells[].measured` sub-dict. Defaults mirror the shape every cell in
    the current `results.json` actually has -- a single trial whose Wilson
    bounds are both `null`, which is the case the report must never draw a
    whisker from.
    """
    return {
        "n_resolved": n_resolved,
        "n_unresolved": max(0, n_attempts - n_resolved),
        "n_incomplete": 0,
        "n_attempts": n_attempts,
        "pass_at_1": pass_at_1,
        "is_single_trial": is_single_trial,
        "pass_at_1_ci_low": pass_at_1_ci_low,
        "pass_at_1_ci_high": pass_at_1_ci_high,
        "pass_at_1_interval_type": "wilson_binomial",
        "pass_at_1_denominator_unit": "local_trial_attempts",
        "total_cost_usd": avg_cost_usd,
        "avg_cost_usd": avg_cost_usd,
        "max_cost_usd": avg_cost_usd,
        "total_output_tokens": avg_output_tokens,
        "avg_output_tokens": avg_output_tokens,
        "total_input_tokens": 5000.0,
        "avg_input_tokens": 5000.0,
        "total_cache_tokens": 500.0,
        "avg_cache_tokens": 500.0,
        "avg_n_agent_steps": 11.0,
    }


def make_cell(
    *,
    task: str = "task-a",
    model: str = "haiku",
    skill: str = "do-in-steps",
    complexity: str | None = "low",
    complexity_rank: int | None = 0,
    state: str = "measured",
    measured: dict[str, Any] | None = None,
    reason: str = "a stated reason",
    collapses_onto_model: str | None = None,
) -> dict[str, Any]:
    """A `results.json` `cells[]` entry. `measured`/`absence` are populated
    from `state` so a fixture cannot accidentally describe a cell that is
    simultaneously measured and absent -- the one shape collect.py never
    writes.
    """
    is_measured = state == "measured"
    return {
        "task": task,
        "model": model,
        "skill": skill,
        "complexity": complexity,
        "complexity_rank": complexity_rank,
        "arm_id": f"{skill}__{model}",
        "in_schedule": complexity_rank is not None,
        "state": state,
        "measured": (measured if measured is not None else make_measured()) if is_measured else None,
        "absence": None
        if is_measured
        else {
            "reason": reason,
            "source": "schedule.yaml",
            "collapses_onto_model": collapses_onto_model,
        },
        "schedule_skip_reason": None if is_measured else reason,
        "scheduler_outcome": None,
        "scheduler_reason": None,
        "scheduler_attempts": None,
        "n_trials_seen": 1 if is_measured else 0,
        "n_errored_trials": 0,
        "trial_ids": ["t-1"] if is_measured else [],
    }
