"""Shared `TrialRecord` factory, verifier-rewards bundles, and a synthetic
`runs/` tree builder for `collect.py`'s aggregation/status/filesystem tests.

Kept in its own module (rather than copy-pasted into each test file) so
`test_collect_aggregation.py`, `test_collect_status.py` and
`test_collect_filesystem.py` share one authoritative way to build a
TrialRecord -- and one authoritative idea of what the verifier actually
emits -- instead of definitions able to drift apart.

`write_runs_tree` serves the same purpose one level up, for the tests that
need a whole pier jobs directory rather than one record: the real `runs/` is
a gitignored recording that a fresh checkout does not have, so anything
asserting against it either skips (proving nothing) or pins figures that move
every time another trial is recorded. See `tests/fixtures/README.md`.
"""

from __future__ import annotations

import json
from pathlib import Path

import collect  # sys.path already patched by tests/__init__.py

# Verifier rewards bundles in the real DeepSWE shape. UNRESOLVED_REWARDS is
# copied verbatim from a live run's verifier/reward.json
# (`runs/_preflight/abs-stepped-slices__HyQJyYy/`); the other two apply that
# run's own arithmetic (f2p = f2p_passed/f2p_total, p2p likewise,
# partial = (f2p + p2p)/2, reward = 1 iff f2p == p2p == 1.0) to the two
# outcomes that run did not happen to produce. Any test about *DeepSWE*
# behavior must use these rather than an invented shape like {"pass": 1}:
# synthetic bundles are exactly what let the all-values-equal-1
# classification bug survive 102 passing tests. The one hand-written bundle
# below (LEGACY_BINARY_REWARDS) is named so it can never be read as one.
RESOLVED_REWARDS = {
    "reward": 1,
    "f2p_total": 6,
    "f2p_passed": 6,
    "p2p_total": 6,
    "p2p_passed": 6,
    "f2p": 1.0,
    "p2p": 1.0,
    "partial": 1.0,
}

# Fixed nothing, broke nothing -- the observed real bundle.
UNRESOLVED_REWARDS = {
    "reward": 0,
    "f2p_total": 6,
    "f2p_passed": 0,
    "p2p_total": 6,
    "p2p_passed": 6,
    "f2p": 0.0,
    "p2p": 1.0,
    "partial": 0.5,
}

# Implemented the new behavior but regressed existing tests: high partial
# credit, still not a success.
REGRESSION_REWARDS = {
    "reward": 0,
    "f2p_total": 6,
    "f2p_passed": 6,
    "p2p_total": 6,
    "p2p_passed": 3,
    "f2p": 1.0,
    "p2p": 0.5,
    "partial": 0.75,
}

# The same bundles with the scalar dropped, for `verifier_reports_success`'s
# middle rule (recompute the verdict from `f2p`/`p2p`). Derived from the
# bundles above rather than retyped, so they cannot drift from them. Both
# would be scored FALSE by the last-resort all-ones rule -- `f2p_total: 6`
# is not 1 -- which is what makes them worth testing.
RESOLVED_REWARDS_NO_SCALAR = {k: v for k, v in RESOLVED_REWARDS.items() if k != "reward"}
REGRESSION_REWARDS_NO_SCALAR = {k: v for k, v in REGRESSION_REWARDS.items() if k != "reward"}

# A genuinely binary bundle, as a non-DeepSWE verifier (or a run predating
# the metrics bundle) might emit: no scalar, no ratios, every value already a
# 0/1 verdict. This is the only shape the all-ones rule is the right answer
# for. Named so a grep can never mistake it for a DeepSWE bundle.
LEGACY_BINARY_REWARDS = {"resolved": 1}
LEGACY_BINARY_REWARDS_FAILED = {"resolved": 0}


def make_trial(
    status: str,
    *,
    arm_id: str = "arm-1",
    skill: str | None = "skill-a",
    orchestrator: str = "sonnet",
    impl: str | None = "sonnet",
    cost_usd: float | None = None,
    output_tokens: int | None = None,
    input_tokens: int | None = None,
    cache_tokens: int | None = None,
    n_agent_steps: int | None = None,
    trial_id: str | None = None,
    task_name: str | None = "task-1",
) -> collect.TrialRecord:
    """Build one TrialRecord with every required field filled in, so
    aggregation tests can vary just the fields they care about (status,
    cost/token/step figures) without restating TrialRecord's full 19-field
    shape at every call site.

    `task_name` defaults to the same placeholder every arm-level test has
    always used, so those tests are unaffected; the per-task cell tests pass
    the real pier-namespaced spelling (`datacurve/<task>`) to exercise
    `collect.resolve_trial_task_name`. `input_tokens`/`cache_tokens` became
    parameters for the same reason -- the per-cell token rollups need them,
    and defaulting to None keeps every existing call site identical.
    """
    return collect.TrialRecord(
        arm_id=arm_id,
        skill=skill,
        orchestrator=orchestrator,
        impl=impl,
        task_name=task_name,
        task_checksum="checksum-1",
        resolved=status == "resolved",
        reward={"resolved": 1.0, "unresolved": 0.0, "incomplete": 0.0}.get(status),
        cost_usd=cost_usd,
        output_tokens=output_tokens,
        input_tokens=input_tokens,
        cache_tokens=cache_tokens,
        n_agent_steps=n_agent_steps,
        duration_sec=None,
        status=status,
        plugin_ref="cek@abc123",
        claude_code_version="1.0.0",
        trial_id=trial_id or f"trial-{status}-{id(object())}",
        # Both non-attempt statuses carry a reason in real records; only
        # resolved/unresolved leave it None. See collect.py's TrialRecord.
        error_reason={"errored": "some_infra_error", "incomplete": "no_model_patch"}.get(status),
    )


def write_arm(
    runs_dir: Path,
    *,
    arm_id: str,
    skill: str | None,
    orchestrator: str,
    impl: str,
    created_at: str = "2026-01-01T00:00:00+00:00",
    sample_seed: int | None = None,
) -> Path:
    """Create one job directory with the `arm.json` `collect.py` requires.

    Fields mirror the file `run.py` really writes; an arm whose `arm.json` is
    missing or unreadable has every trial under it skipped with a warning, so
    getting this shape right is what makes the trials below collectable.
    """
    job_dir = runs_dir / arm_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "arm.json").write_text(
        json.dumps(
            {
                "arm_id": arm_id,
                "skill": skill,
                "is_vanilla": skill is None,
                "orchestrator_tier": orchestrator,
                "impl_tier": impl,
                "cek_ref": "cek@test",
                "created_at": created_at,
                "sample_seed": sample_seed,
            }
        )
    )
    return job_dir


def write_trial_result(
    job_dir: Path,
    *,
    trial_id: str,
    task_name: str,
    rewards: dict | None = None,
    cost_usd: float = 1.0,
    model_patch: bool = True,
    final_message: str = "Done; the work is committed.",
    plugin_loaded: bool = True,
) -> Path:
    """Create one trial directory in pier's real on-disk layout.

    `rewards` defaults to the recorded UNRESOLVED bundle -- an honest loss,
    the most common real outcome -- rather than to a success, so a test that
    forgets to state an outcome does not silently assert a passing one.

    The task name is written pier-namespaced (`datacurve/<task>`), which is
    the spelling `collect.resolve_trial_task_name` exists to undo.

    `plugin_loaded` writes the `system`/`init` event reporting a clean `sadd`
    load. It is on by default because a plugin arm whose transcript carries no
    init event is classified `errored`, which would quietly turn every trial
    built here into a non-measurement.
    """
    trial_dir = job_dir / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)

    if model_patch:
        (trial_dir / "artifacts").mkdir(exist_ok=True)
        (trial_dir / "artifacts" / "model.patch").write_text("diff --git a/x b/x\n")

    events = []
    if plugin_loaded:
        events.append(
            {"type": "system", "subtype": "init", "plugins": [{"name": "sadd"}], "plugin_errors": []}
        )
    events.append({"type": "result", "subtype": "success", "result": final_message})

    (trial_dir / "agent").mkdir(exist_ok=True)
    (trial_dir / "agent" / "claude-code.txt").write_text(
        "\n".join(json.dumps(event) for event in events)
    )

    (trial_dir / "result.json").write_text(
        json.dumps(
            {
                "task_name": f"datacurve/{task_name}",
                "task_checksum": f"checksum-{task_name}",
                "verifier_result": {
                    "rewards": UNRESOLVED_REWARDS if rewards is None else rewards
                },
                "exception_info": None,
                "agent_info": {"version": "1.0.0"},
                "agent_result": {
                    "cost_usd": cost_usd,
                    "n_input_tokens": 5000,
                    "n_cache_tokens": 500,
                    "n_output_tokens": 1200,
                    "n_agent_steps": 11,
                },
                "started_at": "2026-01-01T00:00:00+00:00",
                "finished_at": "2026-01-01T00:30:00+00:00",
            }
        )
    )
    return trial_dir


def write_runs_tree(runs_dir: Path) -> Path:
    """A small but structurally complete stand-in for a recorded `runs/` tree.

    Two arms over two tasks, one solve and one loss, so anything reading it
    sees both verdicts and more than one arm to aggregate across -- enough
    for the collect -> report pipeline to produce a report with populated
    tables, which is what the tests using this actually assert about.
    """
    plugin_arm = write_arm(
        runs_dir,
        arm_id="do-in-steps__sonnet-sonnet",
        skill="do-in-steps",
        orchestrator="sonnet",
        impl="sonnet",
    )
    write_trial_result(
        plugin_arm,
        trial_id="abs-stepped-slices__aaa1111",
        task_name="abs-stepped-slices",
        rewards=RESOLVED_REWARDS,
        cost_usd=12.5,
    )
    write_trial_result(
        plugin_arm,
        trial_id="cattrs-partial-structuring-recov__bbb2222",
        task_name="cattrs-partial-structuring-recovery",
        cost_usd=8.0,
    )

    vanilla_arm = write_arm(
        runs_dir,
        arm_id="vanilla__sonnet",
        skill=None,
        orchestrator="sonnet",
        impl="sonnet",
    )
    write_trial_result(
        vanilla_arm,
        trial_id="abs-stepped-slices__ccc3333",
        task_name="abs-stepped-slices",
        cost_usd=3.25,
    )
    return runs_dir
