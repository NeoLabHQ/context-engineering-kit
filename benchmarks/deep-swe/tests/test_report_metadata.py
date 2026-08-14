#!/usr/bin/env python3
"""Unit tests for report.py's run-metadata derivation: `earliest_arm_created_at`,
`resolve_sample_seed`, `summarize_run_metadata`, `format_run_started_at`,
`format_sample_seed`.
"""

from __future__ import annotations

import unittest
from typing import Any

import report  # sys.path patched by tests/__init__.py

from .report_fixtures import make_arm


class RunMetadataTests(unittest.TestCase):
    def test_earliest_arm_created_at_picks_the_minimum(self) -> None:
        arms = [
            make_arm(arm_id="a1", created_at="2026-02-01T00:00:00+00:00"),
            make_arm(arm_id="a2", created_at="2026-01-01T00:00:00+00:00"),
        ]
        self.assertEqual(report.earliest_arm_created_at(arms), "2026-01-01T00:00:00+00:00")

    def test_earliest_arm_created_at_ignores_arms_without_the_field(self) -> None:
        arms = [make_arm(arm_id="a1", created_at=None)]
        self.assertIsNone(report.earliest_arm_created_at(arms))

    def test_resolve_sample_seed_returns_the_shared_seed(self) -> None:
        arms = [
            make_arm(arm_id="a1", sample_seed=20260809),
            make_arm(arm_id="a2", sample_seed=20260809),
        ]
        self.assertEqual(report.resolve_sample_seed(arms), 20260809)

    def test_resolve_sample_seed_none_when_no_arm_carries_one(self) -> None:
        arms = [make_arm(arm_id="a1", sample_seed=None)]
        self.assertIsNone(report.resolve_sample_seed(arms))

    def test_summarize_run_metadata_populates_fields_at_current_schema_version(self) -> None:
        trials = [{"task_checksum": "c1", "plugin_ref": "cek@abc", "claude_code_version": "1.0"}]
        arms = [make_arm(created_at="2026-01-01T00:00:00+00:00", sample_seed=20260809)]

        metadata = report.summarize_run_metadata(
            trials, arms, schema_version=report.EXPECTED_RESULTS_SCHEMA_VERSION
        )

        self.assertTrue(metadata["has_run_metadata_fields"])
        self.assertEqual(metadata["run_started_at"], "2026-01-01T00:00:00+00:00")
        self.assertEqual(metadata["sample_seed"], 20260809)
        self.assertEqual(metadata["n_tasks"], 1)
        self.assertEqual(metadata["n_trials"], 1)

    def test_summarize_run_metadata_hides_run_fields_for_pre_v2_schema(self) -> None:
        # A v1 results.json never wrote created_at/sample_seed onto arms at
        # all -- even if an arm dict happens to carry the keys (shouldn't
        # happen in practice), schema_version gating must still report
        # has_run_metadata_fields=False and blank out both derived fields.
        trials: list[dict[str, Any]] = []
        arms = [make_arm(created_at="2026-01-01T00:00:00+00:00", sample_seed=20260809)]

        metadata = report.summarize_run_metadata(trials, arms, schema_version=1)

        self.assertFalse(metadata["has_run_metadata_fields"])
        self.assertIsNone(metadata["run_started_at"])
        self.assertIsNone(metadata["sample_seed"])

    def test_summarize_run_metadata_handles_missing_schema_version(self) -> None:
        metadata = report.summarize_run_metadata([], [], schema_version=None)
        self.assertFalse(metadata["has_run_metadata_fields"])


class FormatRunStartedAtAndSeedTests(unittest.TestCase):
    def test_run_started_at_renders_real_timestamp(self) -> None:
        text = report.format_run_started_at(
            "2026-01-01T12:34:00+00:00", has_run_metadata_fields=True
        )
        self.assertEqual(text, "2026-01-01 12:34 UTC")

    def test_run_started_at_v2_schema_but_no_arm_recorded_one(self) -> None:
        text = report.format_run_started_at(None, has_run_metadata_fields=True)
        self.assertEqual(text, "unavailable (no arm recorded a created_at)")

    def test_run_started_at_pre_v2_schema_discloses_field_never_existed(self) -> None:
        text = report.format_run_started_at(None, has_run_metadata_fields=False)
        self.assertIn("not recorded", text)

    def test_sample_seed_renders_real_value(self) -> None:
        self.assertEqual(
            report.format_sample_seed(20260809, has_run_metadata_fields=True), "20260809"
        )

    def test_sample_seed_v2_schema_but_mode_was_not_sample(self) -> None:
        text = report.format_sample_seed(None, has_run_metadata_fields=True)
        self.assertEqual(text, "not applicable (run mode was not 'sample')")

    def test_sample_seed_pre_v2_schema_discloses_field_never_existed(self) -> None:
        text = report.format_sample_seed(None, has_run_metadata_fields=False)
        self.assertIn("not recorded", text)


if __name__ == "__main__":
    unittest.main()
