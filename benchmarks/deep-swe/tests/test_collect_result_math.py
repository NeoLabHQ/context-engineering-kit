#!/usr/bin/env python3
"""Unit tests for collect.py's small numeric/result-shape helpers:
`mean_or_none`, `agent_step_count_from_result`, `token_cost_totals_from_result`,
`trial_duration_seconds`.
"""

from __future__ import annotations

import unittest

import collect  # sys.path patched by tests/__init__.py


class MeanOrNoneTests(unittest.TestCase):
    def test_empty_list_is_none(self) -> None:
        self.assertIsNone(collect.mean_or_none([]))

    def test_all_none_values_is_none(self) -> None:
        self.assertIsNone(collect.mean_or_none([None, None]))

    def test_mixed_values_averages_only_the_present_ones(self) -> None:
        # (1 + 2 + 3) / 3 = 2.0 -- the None is excluded from both sum and count.
        self.assertEqual(collect.mean_or_none([1, 2, None, 3]), 2.0)


class AgentStepCountFromResultTests(unittest.TestCase):
    def test_top_level_field_wins(self) -> None:
        self.assertEqual(collect.agent_step_count_from_result({"n_agent_steps": 5}), 5)

    def test_falls_back_to_agent_result(self) -> None:
        trial = {"agent_result": {"n_agent_steps": 7}}
        self.assertEqual(collect.agent_step_count_from_result(trial), 7)

    def test_sums_across_step_results_when_no_top_level_field(self) -> None:
        trial = {
            "step_results": [
                {"agent_result": {"n_agent_steps": 2}},
                {"agent_result": {"n_agent_steps": 3}},
            ]
        }
        self.assertEqual(collect.agent_step_count_from_result(trial), 5)

    def test_no_data_anywhere_is_none(self) -> None:
        self.assertIsNone(collect.agent_step_count_from_result({}))
        self.assertIsNone(
            collect.agent_step_count_from_result({"step_results": [{"agent_result": {}}]})
        )


class TokenCostTotalsFromResultTests(unittest.TestCase):
    def test_single_agent_result(self) -> None:
        trial = {
            "agent_result": {
                "n_input_tokens": 10,
                "n_cache_tokens": 2,
                "n_output_tokens": 5,
                "cost_usd": 0.1,
            }
        }
        self.assertEqual(collect.token_cost_totals_from_result(trial), (10, 2, 5, 0.1))

    def test_no_contexts_is_all_none(self) -> None:
        self.assertEqual(collect.token_cost_totals_from_result({}), (None, None, None, None))

    def test_sums_across_step_results(self) -> None:
        trial = {
            "step_results": [
                {"agent_result": {"n_output_tokens": 3}},
                {"agent_result": {"n_output_tokens": 4, "cost_usd": 0.2}},
            ]
        }
        n_input, n_cache, n_output, cost = collect.token_cost_totals_from_result(trial)
        self.assertIsNone(n_input)
        self.assertIsNone(n_cache)
        self.assertEqual(n_output, 7)
        self.assertEqual(cost, 0.2)


class TrialDurationSecondsTests(unittest.TestCase):
    def test_missing_either_timestamp_is_none(self) -> None:
        self.assertIsNone(collect.trial_duration_seconds(None, "2026-01-01T00:00:00+00:00"))
        self.assertIsNone(collect.trial_duration_seconds("2026-01-01T00:00:00+00:00", None))

    def test_computes_whole_seconds_between_timestamps(self) -> None:
        duration = collect.trial_duration_seconds(
            "2026-01-01T00:00:00+00:00", "2026-01-01T00:01:30+00:00"
        )
        self.assertEqual(duration, 90.0)


if __name__ == "__main__":
    unittest.main()
