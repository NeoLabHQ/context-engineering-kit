"""Shared `TrialRecord` factory for `collect.py`'s aggregation/status tests.

Kept in its own module (rather than copy-pasted into each test file) so
`test_collect_aggregation.py` and `test_collect_filesystem.py` share one
authoritative way to build a TrialRecord instead of two definitions able to
drift apart.
"""

from __future__ import annotations

import collect  # sys.path already patched by tests/__init__.py


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
        reward={"resolved": 1.0, "unresolved": 0.0}.get(status),
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
        error_reason="some_infra_error" if status == "errored" else None,
    )
