#!/usr/bin/env python3
"""Unit tests for collect.py's merge of the vendored DeepSWE Fable 5 snapshot.

WHY THIS FILE IS MOSTLY ABOUT HONESTY, NOT ARITHMETIC
------------------------------------------------------
Merging `data/fable5_official.json` is a dozen dictionary lookups. What is
hard is that every number in it is *almost* comparable to a local one, and
each near-miss is a way to publish a false claim without writing a single
wrong digit:

* Its pass@1 denominator is scored rollout ATTEMPTS (113 tasks x 4 whole
  benchmark passes, minus exclusions), not tasks -- and not the local
  harness's per-cell attempt count either.
* Its interval is a run-to-run standard error across 4 whole-benchmark
  passes. The local harness plots a Wilson binomial interval. Drawing them as
  the same kind of error bar asserts something neither statistic supports.
* Its per-task results are k-of-n counts over 20 attempts, so rendering
  `0.65` without `13/20` reads as a precision the figure does not have.
* It ran on mini-swe-agent, not claude-code. It is tier-placement context.

So these tests assert that the provenance travels WITH each number, in
machine-readable form -- because prose in a docstring cannot stop a chart.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import collect  # sys.path patched by tests/__init__.py

# The vendored snapshot itself, as ground truth. Every expected value below is
# read from here rather than retyped, so a re-fetch that changes DeepSWE's
# published numbers updates the assertions with the data instead of failing.
SOURCE_PATH = collect.DEFAULT_FABLE5_BASELINE_PATH
SOURCE = json.loads(SOURCE_PATH.read_text())


def rates(node: object) -> list[dict]:
    """Every `BaselineRate`-shaped dict anywhere in a merged baseline payload.

    Identified structurally (by carrying `denominator_unit`) rather than by
    key path, so a rate added later is covered by these tests automatically.
    """
    found: list[dict] = []
    if isinstance(node, dict):
        if "denominator_unit" in node:
            found.append(node)
        for value in node.values():
            found.extend(rates(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(rates(value))
    return found


class BaselineMergeTests(unittest.TestCase):
    """The figures that actually make it into results.json."""

    def setUp(self) -> None:
        self.baseline = collect.build_fable5_baseline(SOURCE)

    def test_the_snapshot_on_disk_merges_without_loss_of_provenance(self) -> None:
        self.assertTrue(self.baseline["available"])
        self.assertEqual(self.baseline["source"]["harness"], "mini-swe-agent")
        self.assertEqual(self.baseline["source"]["retrieved_date"], SOURCE["retrieved_date"])
        self.assertEqual(
            self.baseline["source"]["artifact_generated_at"], SOURCE["source"]["artifact_generated_at"]
        )

    def test_the_headline_pass_rate_is_transcribed_exactly(self) -> None:
        headline = SOURCE["aggregate"]["headline"]
        rate = self.baseline["aggregate"]["headline"]["pass_at_1"]
        self.assertEqual(rate["value"], headline["pass_at_1"])
        self.assertEqual(rate["n_numerator"], headline["n_passed"])
        self.assertEqual(rate["n_denominator"], headline["n_attempted_scored"])

    def test_the_headline_cost_and_token_figures_are_carried(self) -> None:
        headline = SOURCE["aggregate"]["headline"]
        merged = self.baseline["aggregate"]["headline"]
        self.assertEqual(merged["mean_cost_usd"], headline["mean_cost_usd"])
        self.assertEqual(merged["mean_output_tokens"], headline["mean_output_tokens"])
        self.assertEqual(merged["mean_input_tokens"], headline["mean_input_tokens"])
        self.assertEqual(merged["mean_agent_steps"], headline["mean_agent_steps"])

    def test_every_one_of_the_three_local_tasks_has_per_task_figures(self) -> None:
        self.assertEqual(set(self.baseline["per_task"]), set(SOURCE["per_task"]))

    def test_per_task_results_carry_their_k_of_n_counts(self) -> None:
        # The three the report will quote: kombu 13/20 pooled and 4/4 at max,
        # cattrs 19/20 and 4/4, abs-stepped-slices 14/20 and 2/4.
        expected = {
            "kombu-single-active-consumer-priority": ((13, 20), (4, 4)),
            "cattrs-partial-structuring-recovery": ((19, 20), (4, 4)),
            "abs-stepped-slices": ((14, 20), (2, 4)),
        }
        for task, (pooled, at_max) in expected.items():
            with self.subTest(task=task):
                merged = self.baseline["per_task"][task]
                pooled_rate = merged["all_efforts_pooled"]["pass_at_1"]
                max_rate = merged["headline_config_max"]["pass_at_1"]
                self.assertEqual((pooled_rate["n_numerator"], pooled_rate["n_denominator"]), pooled)
                self.assertEqual((max_rate["n_numerator"], max_rate["n_denominator"]), at_max)

    def test_the_best_scoring_effort_is_recorded_beside_the_headline(self) -> None:
        # The site's headline row is its highest-EFFORT row, not its
        # best-scoring one; xhigh scores marginally higher for less money, and
        # a report quoting only the headline would understate Fable 5.
        xhigh = SOURCE["aggregate"]["all_reasoning_efforts"]["xhigh"]
        best = self.baseline["aggregate"]["best_scoring_effort"]
        self.assertEqual(best["reasoning_effort"], "xhigh")
        self.assertEqual(best["pass_at_1"]["value"], xhigh["pass_at_1"])
        self.assertTrue(best["outscores_headline"])
        self.assertGreater(best["pass_at_1"]["value"], SOURCE["aggregate"]["headline"]["pass_at_1"])
        self.assertAlmostEqual(best["mean_cost_usd_as_fraction_of_headline"], 0.62, places=2)

    def test_derived_figures_are_named_as_derived(self) -> None:
        # The cost fraction is the only number in the payload DeepSWE does not
        # publish outright; it is a division of two published figures and says so.
        best = self.baseline["aggregate"]["best_scoring_effort"]
        self.assertIn("mean_cost_usd_as_fraction_of_headline", best["derived_fields"])

    def test_the_trial_exclusions_behind_the_denominator_are_carried(self) -> None:
        completeness = SOURCE["aggregate"]["trial_completeness"]
        merged = self.baseline["aggregate"]["trial_completeness"]
        self.assertEqual(merged["n_trials_scored"], completeness["n_trials_scored"])
        self.assertEqual(merged["n_trials_excluded"], completeness["n_trials_excluded"])
        self.assertEqual(merged["site_note_verbatim"], completeness["site_note_verbatim"])


class ProvenanceTravelsWithEveryRateTests(unittest.TestCase):
    """No rate may be readable without its denominator and its interval kind."""

    def setUp(self) -> None:
        self.baseline = collect.build_fable5_baseline(SOURCE)
        self.rates = rates(self.baseline)

    def test_the_payload_actually_contains_rates_to_check(self) -> None:
        # Guards the structural `rates()` walk itself: an empty list would make
        # every assertion below vacuously true.
        self.assertGreaterEqual(len(self.rates), 8)

    def test_no_rate_is_published_without_its_numerator_and_denominator(self) -> None:
        for rate in self.rates:
            with self.subTest(rate=rate):
                self.assertIsInstance(rate["n_numerator"], int)
                self.assertIsInstance(rate["n_denominator"], int)
                self.assertGreater(rate["n_denominator"], 0)

    def test_no_rate_claims_comparability_with_the_local_wilson_interval(self) -> None:
        for rate in self.rates:
            with self.subTest(rate=rate):
                self.assertFalse(rate["comparable_to_local_wilson_interval"])
                self.assertNotEqual(rate["interval_type"], collect.LOCAL_PASS_AT_1_INTERVAL_TYPE)

    def test_attempt_rates_and_task_rates_name_different_denominators(self) -> None:
        # pass@1 counts attempts; pass@4 counts tasks. The site's own metric
        # definition calls them "NOT comparable", and the unit strings are how
        # a renderer can tell without reading prose.
        headline = self.baseline["aggregate"]["headline"]
        self.assertEqual(
            headline["pass_at_1"]["denominator_unit"], collect.FABLE5_ATTEMPT_DENOMINATOR_UNIT
        )
        self.assertEqual(headline["pass_at_4"]["denominator_unit"], collect.FABLE5_TASK_DENOMINATOR_UNIT)
        self.assertNotEqual(
            collect.FABLE5_ATTEMPT_DENOMINATOR_UNIT, collect.LOCAL_PASS_AT_1_DENOMINATOR_UNIT
        )

    def test_the_aggregate_interval_names_the_run_to_run_statistic(self) -> None:
        rate = self.baseline["aggregate"]["headline"]["pass_at_1"]
        self.assertEqual(rate["interval_type"], collect.FABLE5_INTERVAL_TYPE)
        self.assertEqual(rate["interval_low"], SOURCE["aggregate"]["headline"]["ci_lo"])
        self.assertEqual(rate["interval_high"], SOURCE["aggregate"]["headline"]["ci_hi"])
        self.assertEqual(rate["interval_n_runs"], SOURCE["aggregate"]["headline"]["n_runs"])

    def test_per_task_intervals_are_recorded_absent_rather_than_invented(self) -> None:
        # DeepSWE publishes no per-task confidence intervals. A per-task error
        # bar would therefore be fabricated, so the fields are present and null
        # -- an explicit "not published", not a missing key to be defaulted.
        for task, merged in self.baseline["per_task"].items():
            for block in ("all_efforts_pooled", "headline_config_max"):
                with self.subTest(task=task, block=block):
                    rate = merged[block]["pass_at_1"]
                    self.assertIn("interval_low", rate)
                    self.assertIsNone(rate["interval_low"])
                    self.assertIsNone(rate["interval_high"])
                    self.assertIsNone(rate["interval_type"])
                    self.assertIsNone(rate["interval_n_runs"])


class HarnessMismatchDisclosureTests(unittest.TestCase):
    """Fable 5 is tier-placement context, not a like-for-like baseline."""

    def setUp(self) -> None:
        self.comparability = collect.build_fable5_baseline(SOURCE)["comparability"]

    def test_the_payload_states_outright_that_it_is_not_like_for_like(self) -> None:
        self.assertFalse(self.comparability["like_for_like"])
        self.assertFalse(self.comparability["co_plotting_intervals_allowed"])
        self.assertEqual(self.comparability["baseline_harness"], "mini-swe-agent")
        self.assertEqual(self.comparability["local_harness"], "claude-code")

    def test_the_two_interval_kinds_are_both_named_in_one_place(self) -> None:
        self.assertEqual(self.comparability["baseline_interval_type"], collect.FABLE5_INTERVAL_TYPE)
        self.assertEqual(self.comparability["local_interval_type"], collect.LOCAL_PASS_AT_1_INTERVAL_TYPE)
        self.assertNotEqual(
            self.comparability["baseline_interval_type"], self.comparability["local_interval_type"]
        )

    def test_the_sites_own_caveats_are_carried_verbatim_not_paraphrased(self) -> None:
        self.assertEqual(
            self.comparability["interval_note"], SOURCE["metric_definition"]["ci_caveat"]
        )
        self.assertEqual(
            self.comparability["denominator_note"], SOURCE["metric_definition"]["denominator"]
        )
        self.assertIn("HARNESS MISMATCH", self.comparability["harness_note"])

    def test_the_unpublished_fields_are_listed_rather_than_filled_in(self) -> None:
        baseline = collect.build_fable5_baseline(SOURCE)
        self.assertIsNone(baseline["model"]["api_model_id"])
        self.assertTrue(baseline["model"]["api_model_id_note"])
        self.assertTrue(any("per-task confidence intervals" in note for note in baseline["not_published"]))


class MissingSnapshotTests(unittest.TestCase):
    """No snapshot means no baseline -- never a placeholder one."""

    def test_a_missing_file_yields_an_explicitly_unavailable_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline = collect.load_fable5_baseline(Path(tmp) / "nope.json")
        self.assertFalse(baseline["available"])
        self.assertIn("reason", baseline)
        # Nothing numeric may appear beside `available: False`.
        self.assertEqual(rates(baseline), [])

    def test_an_unparseable_file_is_treated_as_missing_not_as_empty_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fable5_official.json"
            path.write_text("{ truncated")
            baseline = collect.load_fable5_baseline(path)
        self.assertFalse(baseline["available"])

    def test_a_snapshot_missing_its_aggregate_block_does_not_invent_one(self) -> None:
        baseline = collect.build_fable5_baseline({"status": "ok", "per_task": {}})
        self.assertFalse(baseline["available"])


if __name__ == "__main__":
    unittest.main()
