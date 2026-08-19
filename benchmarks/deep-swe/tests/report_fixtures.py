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
