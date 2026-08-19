#!/usr/bin/env python3
"""Filesystem-backed unit tests for collect.py's `load_arm_run_metadata` and
`build_trial_record` -- real temp-directory `arm.json`/`result.json` files,
no mocking, no `pier`.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import collect  # sys.path patched by tests/__init__.py
from .collect_fixtures import LEGACY_BINARY_REWARDS, RESOLVED_REWARDS, UNRESOLVED_REWARDS


class LoadArmRunMetadataTests(unittest.TestCase):
    """Writes real `arm.json` files under a temp `runs/` tree so this
    exercises the actual glob + JSON-parsing code path, not a mock of it.
    """

    def test_v1_style_arm_json_missing_sample_seed_defaults_to_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"

            # v1-style: no "sample_seed" key at all (predates that field).
            v1_arm_dir = runs_dir / "arm-1"
            v1_arm_dir.mkdir(parents=True)
            (v1_arm_dir / "arm.json").write_text(
                json.dumps({"arm_id": "arm-1", "created_at": "2026-01-01T00:00:00+00:00"})
            )

            # v2-style: carries both fields.
            v2_arm_dir = runs_dir / "arm-2"
            v2_arm_dir.mkdir(parents=True)
            (v2_arm_dir / "arm.json").write_text(
                json.dumps(
                    {
                        "arm_id": "arm-2",
                        "created_at": "2026-02-01T00:00:00+00:00",
                        "sample_seed": 20260809,
                    }
                )
            )

            metadata = collect.load_arm_run_metadata(runs_dir)

            self.assertEqual(
                metadata["arm-1"],
                {"created_at": "2026-01-01T00:00:00+00:00", "sample_seed": None},
            )
            self.assertEqual(
                metadata["arm-2"],
                {"created_at": "2026-02-01T00:00:00+00:00", "sample_seed": 20260809},
            )

    def test_unreadable_or_incomplete_arm_json_is_skipped_not_raised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"

            malformed_dir = runs_dir / "arm-malformed"
            malformed_dir.mkdir(parents=True)
            (malformed_dir / "arm.json").write_text("{not valid json")

            no_id_dir = runs_dir / "arm-no-id"
            no_id_dir.mkdir(parents=True)
            (no_id_dir / "arm.json").write_text(json.dumps({"created_at": "2026-01-01"}))

            metadata = collect.load_arm_run_metadata(runs_dir)

            self.assertEqual(metadata, {})


class BuildTrialRecordTests(unittest.TestCase):
    """End-to-end checks of build_trial_record's plugin-load/status wiring,
    using real result.json/claude-code.txt files under a temp directory.
    """

    ARM_META = {
        "arm_id": "arm-x",
        "orchestrator_tier": "sonnet",
        "impl_tier": "sonnet",
        "skill": "skill-a",
        "is_vanilla": False,
        "cek_ref": "cek@abc123",
    }
    VANILLA_ARM_META = {**ARM_META, "skill": None, "is_vanilla": True}

    RESOLVED_RESULT = {
        "task_name": "task-1",
        "task_checksum": "checksum-1",
        "verifier_result": {"rewards": RESOLVED_REWARDS},
        "started_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-01T00:01:00+00:00",
        "agent_info": {"version": "1.0.0"},
    }

    def test_malformed_result_json_is_errored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            trial_dir.mkdir()
            (trial_dir / "result.json").write_text("{not valid json")

            record = collect.build_trial_record(trial_dir, self.ARM_META)

            self.assertEqual(record.status, "errored")
            self.assertEqual(record.error_reason, "malformed_result_json")

    def test_vanilla_trial_skips_plugin_load_check_even_without_stream_log(self) -> None:
        # A vanilla (no-plugin) arm never runs the sadd plugin, so a missing
        # claude-code.txt (which would otherwise mean "missing_init_event")
        # must not affect it -- see build_trial_record's `is_vanilla` guard.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            trial_dir.mkdir()
            (trial_dir / "result.json").write_text(json.dumps(self.RESOLVED_RESULT))

            record = collect.build_trial_record(trial_dir, self.VANILLA_ARM_META)

            self.assertEqual(record.status, "resolved")
            self.assertIsNone(record.error_reason)

    def test_non_vanilla_trial_without_stream_log_is_errored(self) -> None:
        # Same result.json as above, but a non-vanilla (plugin) arm: no
        # claude-code.txt means plugin_load_error_from_init_event(None) ==
        # "missing_init_event", which outranks the verifier's success verdict.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            trial_dir.mkdir()
            (trial_dir / "result.json").write_text(json.dumps(self.RESOLVED_RESULT))

            record = collect.build_trial_record(trial_dir, self.ARM_META)

            self.assertEqual(record.status, "errored")
            self.assertEqual(record.error_reason, "missing_init_event")

    def test_reward_field_is_the_scalar_not_the_bundle_sum(self) -> None:
        # A perfect bundle sums to 28.0 across its counts and ratios, which is
        # a meaningless figure to publish in results.csv -- the row must carry
        # the verifier's own binary verdict instead.
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            trial_dir.mkdir()
            (trial_dir / "result.json").write_text(json.dumps(self.RESOLVED_RESULT))

            record = collect.build_trial_record(trial_dir, self.VANILLA_ARM_META)

            self.assertEqual(record.reward, 1)
            self.assertEqual(sum(RESOLVED_REWARDS.values()), 28.0)

    def test_real_failing_bundle_is_unresolved_with_zero_reward(self) -> None:
        # The bundle observed in runs/_preflight/abs-stepped-slices__HyQJyYy:
        # every pass-to-pass test green, no fail-to-pass test fixed.
        result = {**self.RESOLVED_RESULT, "verifier_result": {"rewards": UNRESOLVED_REWARDS}}
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            trial_dir.mkdir()
            (trial_dir / "result.json").write_text(json.dumps(result))
            # This trial genuinely attempted the task and lost, which is only
            # distinguishable from an abandoned one by the patch it committed
            # -- without it the completion gate would (correctly) call this
            # `incomplete` instead. See collect.py's classification table.
            (trial_dir / "artifacts").mkdir()
            (trial_dir / "artifacts" / "model.patch").write_text("diff --git a/x b/x\n")

            record = collect.build_trial_record(trial_dir, self.VANILLA_ARM_META)

            self.assertEqual(record.status, "unresolved")
            self.assertFalse(record.resolved)
            self.assertEqual(record.reward, 0)

    def test_bundle_without_reward_key_yields_none_reward_field(self) -> None:
        # Fallback bundles have no scalar to report; the row records None
        # rather than inventing one. Classification still succeeds via the
        # all-ones fallback -- see verifier_reports_success.
        result = {
            **self.RESOLVED_RESULT,
            "verifier_result": {"rewards": LEGACY_BINARY_REWARDS},
        }
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            trial_dir.mkdir()
            (trial_dir / "result.json").write_text(json.dumps(result))

            record = collect.build_trial_record(trial_dir, self.VANILLA_ARM_META)

            self.assertEqual(record.status, "resolved")
            self.assertIsNone(record.reward)


if __name__ == "__main__":
    unittest.main()
