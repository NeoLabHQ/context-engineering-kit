#!/usr/bin/env python3
"""Unit tests for report.py's small formatting/color-assignment helpers:
`assign_categorical_color_vars`, `format_pass_at_1_with_ci`, `format_usd`,
`format_count`.
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py


class AssignCategoricalColorVarsTests(unittest.TestCase):
    def test_assigns_series_vars_in_alphabetical_order(self) -> None:
        self.assertEqual(
            report.assign_categorical_color_vars(["vanilla", "skill-a"]),
            {"skill-a": "--series-1", "vanilla": "--series-2"},
        )

    def test_single_slot(self) -> None:
        self.assertEqual(report.assign_categorical_color_vars(["only"]), {"only": "--series-1"})

    def test_exactly_three_slots_is_the_boundary_that_still_works(self) -> None:
        result = report.assign_categorical_color_vars(["a", "b", "c"])
        self.assertEqual(result, {"a": "--series-1", "b": "--series-2", "c": "--series-3"})

    def test_more_than_three_slots_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            report.assign_categorical_color_vars(["a", "b", "c", "d"])


class FormatPassAt1WithCiTests(unittest.TestCase):
    def test_formats_percentage_and_half_width_ci(self) -> None:
        # half_width = (0.70 - 0.54) / 2 * 100 = 8.0
        self.assertEqual(report.format_pass_at_1_with_ci(0.62, 0.54, 0.70), "62% ± 8%")

    def test_none_value_renders_em_dash(self) -> None:
        self.assertEqual(report.format_pass_at_1_with_ci(None, None, None), "—")

    def test_genuine_zero_is_distinguishable_from_no_data(self) -> None:
        # pass_at_1=0.0 (a real "every attempt failed" measurement) must
        # render as an actual number, never the same em dash as null.
        rendered = report.format_pass_at_1_with_ci(0.0, 0.0, 0.3)
        self.assertNotEqual(rendered, "—")
        self.assertEqual(rendered, "0% ± 15%")


class FormatUsdAndCountTests(unittest.TestCase):
    def test_format_usd(self) -> None:
        self.assertEqual(report.format_usd(None), "—")
        self.assertEqual(report.format_usd(1234.5), "$1,234.50")

    def test_format_count(self) -> None:
        self.assertEqual(report.format_count(None), "—")
        self.assertEqual(report.format_count(1234.0), "1,234")


if __name__ == "__main__":
    unittest.main()
