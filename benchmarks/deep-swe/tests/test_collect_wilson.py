#!/usr/bin/env python3
"""Unit tests for `collect.wilson_score_interval`."""

from __future__ import annotations

import math
import unittest

import collect  # sys.path patched by tests/__init__.py


class WilsonScoreIntervalTests(unittest.TestCase):
    """Wilson interval reference values below are independently derived from
    `statsmodels.stats.proportion.proportion_confint(successes, n, alpha=0.05,
    method="wilson")` (statsmodels 0.14, run once offline; NOT imported here
    -- see collect.py's module docstring). Baked in as literals so the
    committed suite needs no third-party package:

        proportion_confint(0, 1, method="wilson")  -> (0.0, 0.7934506856227627)
        proportion_confint(1, 1, method="wilson")  -> (0.2065493143772374, 1.0)
        proportion_confint(3, 4, method="wilson")  -> (0.30064184258240184, 0.9544127391902995)
        proportion_confint(1, 3, method="wilson")  -> (0.06149194472039626, 0.7923403991979523)
        proportion_confint(5, 20, method="wilson") -> (0.11186170140766563, 0.4687008776187441)
        proportion_confint(0, 2, method="wilson")  -> (0.0, 0.657619772493347)
        proportion_confint(2, 2, method="wilson")  -> (0.342380227506653, 1.0)
    """

    def test_n_zero_returns_full_uncertainty_without_raising(self) -> None:
        # "No data" must be (0.0, 1.0), never NaN, never a ZeroDivisionError.
        low, high = collect.wilson_score_interval(0, 0)
        self.assertEqual((low, high), (0.0, 1.0))
        self.assertFalse(math.isnan(low) or math.isnan(high))

    def test_zero_percent_success_matches_independent_reference(self) -> None:
        low, high = collect.wilson_score_interval(0, 1)
        self.assertAlmostEqual(low, 0.0, places=12)
        self.assertAlmostEqual(high, 0.7934506856227627, places=12)

    def test_hundred_percent_success_matches_independent_reference(self) -> None:
        low, high = collect.wilson_score_interval(1, 1)
        self.assertAlmostEqual(low, 0.2065493143772374, places=12)
        self.assertAlmostEqual(high, 1.0, places=12)

    def test_generic_proportions_match_independent_reference(self) -> None:
        cases = [
            (3, 4, 0.30064184258240184, 0.9544127391902995),
            (1, 3, 0.06149194472039626, 0.7923403991979523),
            (5, 20, 0.11186170140766563, 0.4687008776187441),
            (0, 2, 0.0, 0.657619772493347),
            (2, 2, 0.342380227506653, 1.0),
        ]
        for successes, n, expected_low, expected_high in cases:
            with self.subTest(successes=successes, n=n):
                low, high = collect.wilson_score_interval(successes, n)
                self.assertAlmostEqual(low, expected_low, places=12)
                self.assertAlmostEqual(high, expected_high, places=12)

    def test_successes_greater_than_n_raises(self) -> None:
        with self.assertRaises(ValueError):
            collect.wilson_score_interval(5, 4)

    def test_negative_successes_raises(self) -> None:
        with self.assertRaises(ValueError):
            collect.wilson_score_interval(-1, 4)


if __name__ == "__main__":
    unittest.main()
