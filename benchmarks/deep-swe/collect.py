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
`status` is one of `resolved` / `unresolved` / `errored`. Signals are
checked in this order (first match wins), each verified against pier's real
`TrialResult` schema (`/tmp/pier-repo/src/pier/models/trial/result.py`):

| # | Signal                                                        | status     |
|---|----------------------------------------------------------------|------------|
| 1 | result.json missing/corrupt/truncated (can't even be parsed)   | errored    |
| 2 | non-vanilla trial, `sadd` plugin didn't load (system/init event)| errored   |
| 3 | `TrialResult.exception_info` is set (pier's own infra-failure signal: Docker/environment build failure, agent/verifier timeout, non-zero agent exit code, cancellation -- and transitively, an API 529/rate-limit failure that crashed the `claude` process; see `infra_error_category()` for how the raw exception type is normalized into one of these) | errored |
| 4 | `verifier_result` missing, or its `rewards` dict is missing/empty (verifier never produced a scalar) | errored |
| 5 | `rewards["reward"] == 1` -- or, for a bundle carrying no `reward` key, `f2p == 1.0 and p2p == 1.0`, falling back last to every value in `rewards` equalling `1` | resolved |
| 6 | otherwise (verifier ran and did not report success)            | unresolved |

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
and only then the all-ones rule. Note that pier's own `compute_pass_at_k_by_evals` (see
`/tmp/pier-repo/src/pier/utils/pass_at_k.py`) does assume one binary reward
per key, so its Pass@k is not interchangeable with this module's.

PASS@1 DENOMINATOR
-------------------
`errored` trials are EXCLUDED from every per-arm average (Pass@1, avg cost,
avg output tokens, avg steps): they are not task attempts, and their
cost/token/step figures are contaminated by whatever infra failure occurred
(a Docker build failure trial burns ~$0; a timeout can burn substantial
cost before pier kills it, without finishing). `n_errored` is still reported
per arm, separately, so a reader can see how much data was dropped without
it silently disappearing from the numbers.

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
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

SCRIPT_DIR = Path(__file__).resolve().parent

# Bump when TrialRecord/ArmAggregate's field set or meaning changes, so a
# consumer of results.json can detect a shape it wasn't written for instead
# of silently misreading renamed/removed/reordered fields.
#
# v2 (this version): ArmAggregate gained `created_at` and `sample_seed`,
# surfaced from each arm's `arm.json` (see `load_arm_run_metadata`) so
# report.py can render a real run-start date/seed in its header instead of
# the "not recorded" placeholder v1 consumers must still fall back to.
RESULTS_SCHEMA_VERSION = 2

Status = Literal["resolved", "unresolved", "errored"]

# The stream-json event pier tees to `<trial_dir>/agent/claude-code.txt` that
# carries plugin-load information (see run.py's `find_init_event`, verified
# against a live `claude` invocation).
_STREAM_LOG_RELATIVE_PATH = Path("agent") / "claude-code.txt"


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
    # an `errored` row's cause surfaces instead of being silently dropped
    # (required by this task's plugin-load-assertion and error-visibility
    # rules). See "Context for Next Steps" in the handoff notes.
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
    n_errored: int
    n_attempts: int  # resolved + unresolved -- the Pass@1 denominator
    n_total_trials: int  # n_attempts + n_errored -- every trial seen for this arm
    pass_at_1: float | None
    pass_at_1_ci_low: float | None
    pass_at_1_ci_high: float | None
    avg_cost_usd: float | None
    avg_output_tokens: float | None
    avg_n_agent_steps: float | None
    # v2 additions, both sourced from this arm's `arm.json` (see
    # `load_arm_run_metadata`) rather than computed from trials -- every
    # trial in an arm shares one arm.json, so these are constant per arm.
    created_at: str | None  # when run.py started this arm (ISO 8601, UTC)
    sample_seed: int | None  # run.py's pinned SAMPLE_SEED, or None if the
    # run mode wasn't "sample" (the seed plays no role otherwise) -- see
    # run.py's write_arm_metadata docstring.


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
) -> tuple[Status, str | None]:
    """Classify one trial's outcome. Returns (status, error_reason).

    `error_reason` is always None for `resolved`/`unresolved`; for `errored`
    it names which of the rules in this module's docstring table fired. A
    pier exception_info additionally carries a normalized category from
    `infra_error_category()` alongside the raw `exception_type`, so no
    information is lost even though the outcome is always `errored` either
    way. Signal precedence matches the module docstring's table (plugin
    load, then pier's own exception_info, then a missing/empty rewards
    dict, then the verifier's own success verdict).

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


def find_stream_log_init_event(trial_dir: Path) -> dict[str, Any] | None:
    """Locate and return the `system`/`init` event from this trial's
    claude-code.txt transcript, or None if the log or the event is missing.

    Duplicated from run.py's `find_init_event`/`iter_stream_events` rather
    than imported -- see module docstring's "WHY THIS FILE DOES NOT IMPORT
    pier" section.
    """
    stream_log = trial_dir / _STREAM_LOG_RELATIVE_PATH
    if not stream_log.exists():
        return None

    for line in stream_log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            return event
    return None


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
    denominator -- see module docstring's "PASS@1 DENOMINATOR" section.

    Worked example: 10 trials for one arm -- 6 resolved, 2 unresolved, 2
    errored -- yield `n_attempts=8` (6+2, excluding the errored pair),
    `pass_at_1=6/8=0.75`, and a CI from `wilson_score_interval(6, 8)`. The 2
    errored trials count toward `n_errored`/`n_total_trials` only, never the
    denominator or any average.

    `run_metadata` is this arm's `{"created_at", "sample_seed"}` entry from
    `load_arm_run_metadata` (keyed by arm_id), or `None` when the caller has
    no such mapping (e.g. an existing unit test built straight from
    TrialRecords) -- both `created_at`/`sample_seed` fall back to `None`
    rather than raising, keeping this function usable exactly as before.
    """
    first = trials[0]
    resolved = [t for t in trials if t.status == "resolved"]
    unresolved = [t for t in trials if t.status == "unresolved"]
    errored = [t for t in trials if t.status == "errored"]
    attempts = resolved + unresolved

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
        n_errored=len(errored),
        n_attempts=n_attempts,
        n_total_trials=len(trials),
        pass_at_1=pass_at_1,
        pass_at_1_ci_low=ci_low,
        pass_at_1_ci_high=ci_high,
        avg_cost_usd=mean_or_none([t.cost_usd for t in attempts]),
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
# Output writers
# --------------------------------------------------------------------------


def write_results_json(path: Path, trials: list[TrialRecord], arms: list[ArmAggregate]) -> None:
    payload = {
        "schema_version": RESULTS_SCHEMA_VERSION,
        "trials": [asdict(t) for t in trials],
        "arms": [asdict(a) for a in arms],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    trials = collect_trial_records(args.runs_dir)
    run_metadata = load_arm_run_metadata(args.runs_dir)
    arms = aggregate_all_arms(trials, run_metadata)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_results_json(args.out_dir / "results.json", trials, arms)
    write_results_csv(args.out_dir / "results.csv", trials)

    n_errored = sum(1 for t in trials if t.status == "errored")
    print(
        f"[collect] wrote {len(trials)} trial records ({n_errored} errored) "
        f"across {len(arms)} arms to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
