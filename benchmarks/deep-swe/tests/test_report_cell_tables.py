#!/usr/bin/env python3
"""Unit tests for the per-task tables, the Fable 5 comparison table, and the
cell-coverage summary.

The tables are where an absent cell finally gets to say the whole sentence
that a glyph on a chart can only gesture at, so most of these tests are about
a reason reaching the page intact -- and about the leaderboard's numbers
never being rendered in a form that overstates what they are:

  * every per-task Fable 5 figure prints as "13/20", never as "65%";
  * the one interval Fable 5 publishes prints as labelled text in a table
    cell, and is never handed to the whisker renderer;
  * a local single trial prints as "1 of 1 resolved", never as "100%".
"""

from __future__ import annotations

import json
import unittest
from typing import Any

import report  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR
from .report_fixtures import make_cell, make_measured

SCHEDULE: dict[str, Any] = {
    "skills": ["vanilla", "do-and-judge", "do-in-steps"],
    "models": [{"name": "haiku"}, {"name": "sonnet"}],
    "tasks": [{"name": "task-low", "complexity": "low", "complexity_rank": 0}],
    "complexity_levels": ["low", "medium", "high"],
}


def real_results() -> dict[str, Any]:
    return json.loads((BENCHMARK_DIR / "results.json").read_text())


class TaskTableRowTests(unittest.TestCase):
    def test_one_row_per_model_and_skill_in_schedule_order(self) -> None:
        rows = report.task_table_rows("task-low", [], SCHEDULE)
        self.assertEqual(
            [(r["model"], r["skill"]) for r in rows],
            [
                ("haiku", "vanilla"), ("haiku", "do-and-judge"), ("haiku", "do-in-steps"),
                ("sonnet", "vanilla"), ("sonnet", "do-and-judge"), ("sonnet", "do-in-steps"),
            ],
        )

    def test_a_measured_row_reports_counts_cost_and_tokens(self) -> None:
        cells = [
            make_cell(
                task="task-low", model="sonnet", skill="do-in-steps",
                measured=make_measured(avg_cost_usd=22.54, avg_output_tokens=16170.0),
            )
        ]
        row = next(
            r for r in report.task_table_rows("task-low", cells, SCHEDULE)
            if (r["model"], r["skill"]) == ("sonnet", "do-in-steps")
        )
        self.assertEqual(row["outcome"], "1 of 1 resolved")
        self.assertEqual(row["cost"], "$22.54")
        self.assertEqual(row["output_tokens"], "16,170")
        self.assertEqual(row["state"], "measured")
        self.assertEqual(row["reason"], "")

    def test_a_measured_zero_reports_a_zero_count_not_a_dash(self) -> None:
        # The (cattrs, sonnet, do-in-steps) case: an em dash here would file a
        # real failed attempt under "no data".
        cells = [
            make_cell(
                task="task-low", model="sonnet", skill="do-in-steps",
                measured=make_measured(n_resolved=0, pass_at_1=0.0),
            )
        ]
        row = next(
            r for r in report.task_table_rows("task-low", cells, SCHEDULE)
            if (r["model"], r["skill"]) == ("sonnet", "do-in-steps")
        )
        self.assertEqual(row["outcome"], "0 of 1 resolved")
        self.assertNotEqual(row["outcome"], "—")
        self.assertEqual(row["state"], "measured")

    def test_an_absent_row_names_its_state_and_carries_its_reason(self) -> None:
        cells = [
            make_cell(
                task="task-low", model="haiku", skill="vanilla",
                state="deliberately_skipped", reason="too complex for haiku at the vanilla level",
            )
        ]
        row = next(
            r for r in report.task_table_rows("task-low", cells, SCHEDULE)
            if (r["model"], r["skill"]) == ("haiku", "vanilla")
        )
        self.assertEqual(row["outcome"], "—")
        self.assertEqual(row["state"], report.ABSENCE_LABELS["deliberately_skipped"])
        self.assertIn("too complex for haiku", row["reason"])

    def test_a_structurally_impossible_row_points_at_the_model_it_collapses_onto(self) -> None:
        cells = [
            make_cell(
                task="task-low", model="sonnet", skill="vanilla",
                state="structurally_impossible", reason="a mixed pair's vanilla arm is its orchestrator's",
                collapses_onto_model="sonnet",
            )
        ]
        row = next(
            r for r in report.task_table_rows("task-low", cells, SCHEDULE)
            if (r["model"], r["skill"]) == ("sonnet", "vanilla")
        )
        self.assertIn("sonnet", row["reason"])
        self.assertIn("same measurement", row["reason"])

    def test_a_cell_missing_from_results_still_produces_an_honest_row(self) -> None:
        rows = report.task_table_rows("task-low", [], SCHEDULE)
        for row in rows:
            with self.subTest(model=row["model"], skill=row["skill"]):
                self.assertEqual(row["outcome"], "—")
                self.assertTrue(row["state"])

    def test_the_real_kombu_task_has_no_measured_row_at_all(self) -> None:
        # The whole high-complexity row is unmeasured in the committed data;
        # the table must still render every cell with a stated state.
        results = real_results()
        rows = report.task_table_rows(
            "kombu-single-active-consumer-priority", results["cells"], results["schedule"]
        )
        self.assertEqual(len(rows), 15)
        self.assertTrue(all(row["outcome"] == "—" for row in rows))
        self.assertTrue(all(row["state"] for row in rows))


class CellCoverageSummaryTests(unittest.TestCase):
    def test_states_are_counted_in_a_fixed_reporting_order(self) -> None:
        cells = [
            make_cell(state="measured"),
            make_cell(state="not_yet_run"),
            make_cell(state="not_yet_run"),
        ]
        summary = report.summarize_cell_states(cells)
        self.assertEqual(summary["measured"], 1)
        self.assertEqual(summary["not_yet_run"], 2)
        self.assertEqual(summary["technical_failure"], 0)

    def test_every_vocabulary_state_appears_even_at_zero(self) -> None:
        # A state that vanishes when its count is 0 makes "no technical
        # failures" indistinguishable from "we stopped tracking them".
        summary = report.summarize_cell_states([])
        self.assertEqual(set(summary), set(report.CELL_STATE_REPORT_ORDER))

    def test_the_real_matrix_is_mostly_absent(self) -> None:
        results = real_results()
        summary = report.summarize_cell_states(results["cells"])
        self.assertEqual(sum(summary.values()), len(results["cells"]))
        self.assertGreater(sum(summary.values()) - summary["measured"], summary["measured"])


class Fable5FormattingTests(unittest.TestCase):
    def test_a_per_task_figure_prints_as_k_of_n(self) -> None:
        figure = {"n_numerator": 13, "n_denominator": 20, "value": 0.65}
        self.assertEqual(report.format_k_of_n(figure), "13/20")

    def test_a_per_task_figure_never_prints_as_a_bare_rate(self) -> None:
        figure = {"n_numerator": 13, "n_denominator": 20, "value": 0.65}
        rendered = report.format_k_of_n(figure)
        self.assertNotIn("65", rendered)
        self.assertNotIn("%", rendered)

    def test_a_missing_figure_is_an_em_dash(self) -> None:
        self.assertEqual(report.format_k_of_n(None), "—")

    def test_a_null_interval_prints_as_none_recorded_not_as_a_range(self) -> None:
        figure = {"interval_low": None, "interval_high": None, "interval_type": None}
        self.assertEqual(report.format_baseline_interval(figure), "no interval published")

    def test_a_published_interval_prints_with_the_name_of_what_it_is(self) -> None:
        figure = {
            "interval_low": 0.656912963913939,
            "interval_high": 0.7375824489300977,
            "interval_type": "run_to_run_standard_error_across_whole_benchmark_passes",
            "interval_n_runs": 4,
        }
        rendered = report.format_baseline_interval(figure)
        self.assertIn("66%", rendered)
        self.assertIn("74%", rendered)
        # The reader must never be able to mistake this for a binomial CI.
        self.assertIn("run-to-run", rendered)


class Fable5ComparisonTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.results = real_results()
        self.baseline = self.results["baseline"]

    def test_one_row_per_task_the_baseline_actually_covers(self) -> None:
        rows = report.fable5_comparison_rows(
            self.baseline, self.results["cells"], self.results["schedule"]
        )
        names = [row["task"] for row in rows]
        self.assertIn("abs-stepped-slices", names)
        self.assertIn("kombu-single-active-consumer-priority", names)

    def test_both_baseline_views_are_shown_and_each_is_labelled_with_its_n(self) -> None:
        rows = report.fable5_comparison_rows(
            self.baseline, self.results["cells"], self.results["schedule"]
        )
        row = next(r for r in rows if r["task"] == "kombu-single-active-consumer-priority")
        self.assertEqual(row["fable5_pooled"], "13/20")
        self.assertEqual(row["fable5_headline"], "4/4")

    def test_the_local_column_counts_trials_rather_than_quoting_a_rate(self) -> None:
        rows = report.fable5_comparison_rows(
            self.baseline, self.results["cells"], self.results["schedule"]
        )
        row = next(r for r in rows if r["task"] == "cattrs-partial-structuring-recovery")
        # Two measured cells there, both single trials, neither resolved.
        self.assertTrue(row["local"].startswith("0 of 2 attempts"), row["local"])
        self.assertNotIn("%", row["local"])

    def test_the_local_column_names_the_arms_it_pooled(self) -> None:
        # The pool is opportunistic -- different models under different
        # skills -- so a bare count beside Fable 5's whole-benchmark figure
        # would read as a harness-level rate nobody measured.
        rows = report.fable5_comparison_rows(
            self.baseline, self.results["cells"], self.results["schedule"]
        )
        row = next(r for r in rows if r["task"] == "abs-stepped-slices")
        self.assertEqual(
            row["local"],
            "1 of 2 attempts across haiku/do-and-judge and sonnet/do-in-steps",
        )

    def test_a_task_with_no_local_measurement_says_so_rather_than_showing_zero(self) -> None:
        rows = report.fable5_comparison_rows(
            self.baseline, self.results["cells"], self.results["schedule"]
        )
        row = next(r for r in rows if r["task"] == "kombu-single-active-consumer-priority")
        self.assertEqual(row["local"], "—")

    def test_a_task_absent_from_the_baseline_still_shows_its_local_result(self) -> None:
        # `bandit-incremental-cache-control` is measured locally and is not a
        # DeepSWE task; dropping the row would hide a real measurement.
        rows = report.fable5_comparison_rows(
            self.baseline, self.results["cells"], self.results["schedule"]
        )
        row = next(r for r in rows if r["task"] == "bandit-incremental-cache-control")
        self.assertEqual(row["fable5_pooled"], "—")
        self.assertEqual(row["local"], "1 of 1 attempt across sonnet/do-in-steps")

    def test_no_comparison_row_ever_carries_a_plottable_interval(self) -> None:
        rows = report.fable5_comparison_rows(
            self.baseline, self.results["cells"], self.results["schedule"]
        )
        for row in rows:
            with self.subTest(task=row["task"]):
                self.assertNotIn("ci_low", row)
                self.assertNotIn("interval_low", row)


class Fable5AggregateSummaryTests(unittest.TestCase):
    def test_the_headline_interval_is_reported_as_labelled_text(self) -> None:
        baseline = real_results()["baseline"]
        summary = dict(report.fable5_aggregate_summary(baseline))
        interval_text = " ".join(summary.values())
        self.assertIn("run-to-run", interval_text)

    def test_the_headline_rate_is_shown_with_its_denominator(self) -> None:
        baseline = real_results()["baseline"]
        summary = dict(report.fable5_aggregate_summary(baseline))
        self.assertIn("304/436", " ".join(summary.values()))

    def test_an_unavailable_baseline_yields_no_rows_instead_of_placeholders(self) -> None:
        self.assertEqual(report.fable5_aggregate_summary({"fable5": {"available": False}}), [])


if __name__ == "__main__":
    unittest.main()
