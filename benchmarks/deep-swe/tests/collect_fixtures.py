"""Shared `TrialRecord` factory and verifier-rewards bundles for `collect.py`'s
aggregation/status/filesystem tests.

Kept in its own module (rather than copy-pasted into each test file) so
`test_collect_aggregation.py`, `test_collect_status.py` and
`test_collect_filesystem.py` share one authoritative way to build a
TrialRecord -- and one authoritative idea of what the verifier actually
emits -- instead of definitions able to drift apart.
"""

from __future__ import annotations

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
    n_agent_steps: int | None = None,
    trial_id: str | None = None,
) -> collect.TrialRecord:
    """Build one TrialRecord with every required field filled in, so
    aggregation tests can vary just the fields they care about (status,
    cost/token/step figures) without restating TrialRecord's full 19-field
    shape at every call site.
    """
    return collect.TrialRecord(
        arm_id=arm_id,
        skill=skill,
        orchestrator=orchestrator,
        impl=impl,
        task_name="task-1",
        task_checksum="checksum-1",
        resolved=status == "resolved",
        reward={"resolved": 1.0, "unresolved": 0.0, "incomplete": 0.0}.get(status),
        cost_usd=cost_usd,
        output_tokens=output_tokens,
        input_tokens=None,
        cache_tokens=None,
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
