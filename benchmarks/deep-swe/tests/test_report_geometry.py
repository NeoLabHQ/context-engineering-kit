#!/usr/bin/env python3
"""Unit tests for report.py's pure chart-geometry functions -- see
report.py's "Chart geometry (pure -- Step 5 unit-tests these directly)"
section, which explicitly calls this module out for direct testing.
"""

from __future__ import annotations

import unittest

import report  # sys.path patched by tests/__init__.py


def _present_bar(slot: str) -> report.Bar:
    """A minimal present Bar for geometry tests that don't care about its
    value, just that it occupies a slot."""
    return report.Bar(slot=slot, present=True, value=0.5, ci_low=0.4, ci_high=0.6)


class ChartGeometryTests(unittest.TestCase):
    """Expected pixel coordinates below are computed independently by plain
    arithmetic on `ChartGeometry`'s own default field values (plot_left=46,
    plot_top=30, plot_height=200, bar_width=20, bar_gap=2, group_gap=32),
    following the formulas documented in report.py's docstrings -- never by
    calling the function under test a second time to produce its own
    expectation.
    """

    def setUp(self) -> None:
        self.geometry = report.ChartGeometry()  # defaults from the dataclass

    def test_value_to_y_maps_0_and_1_to_baseline_and_top(self) -> None:
        # y = plot_top + plot_height * (1 - fraction): 0 -> baseline (230),
        # 1 -> plot_top (30), 0.5 -> the midpoint (130).
        self.assertEqual(report.value_to_y(0.0, self.geometry), 230.0)
        self.assertEqual(report.value_to_y(1.0, self.geometry), 30.0)
        self.assertEqual(report.value_to_y(0.5, self.geometry), 130.0)

    def test_value_to_y_clamps_out_of_range_fractions(self) -> None:
        # A value below 0 or above max_value must not draw outside the axis.
        self.assertEqual(report.value_to_y(-1.0, self.geometry), 230.0)
        self.assertEqual(report.value_to_y(2.0, self.geometry), 30.0)

    def test_value_to_y_guards_against_non_positive_max_value(self) -> None:
        # max_value <= 0 must not divide by zero; falls back to fraction=0.
        self.assertEqual(report.value_to_y(0.7, self.geometry, max_value=0.0), 230.0)

    def test_bar_vertical_extent_grows_from_shared_baseline(self) -> None:
        baseline = self.geometry.plot_top + self.geometry.plot_height  # 230.0
        self.assertEqual(report.bar_vertical_extent(0.0, self.geometry), (230.0, 0.0))
        self.assertEqual(report.bar_vertical_extent(0.5, self.geometry), (130.0, 100.0))
        self.assertEqual(report.bar_vertical_extent(1.0, self.geometry), (30.0, baseline - 30.0))

    def test_whisker_at_full_range_stays_within_plot_bounds(self) -> None:
        # ci_low=0/ci_high=1 must span exactly [plot_top, plot_top+plot_height]
        # -- neither end may fall outside the SVG's viewBox (no clipping).
        y_high, y_low = report.whisker_vertical_extent(0.0, 1.0, self.geometry)
        self.assertEqual(y_high, self.geometry.plot_top)  # 30.0: nearest the top
        self.assertEqual(y_low, self.geometry.plot_top + self.geometry.plot_height)  # 230.0
        self.assertGreaterEqual(y_high, 0.0)
        self.assertLessEqual(y_low, self.geometry.plot_top + self.geometry.plot_height)

    def test_y_axis_ticks_at_default_25_percent_step(self) -> None:
        ticks = report.y_axis_ticks(self.geometry)
        expected = [
            (230.0, "0%"),
            (180.0, "25%"),
            (130.0, "50%"),
            (80.0, "75%"),
            (30.0, "100%"),
        ]
        self.assertEqual(ticks, expected)

    def test_rounded_top_rect_path_matches_hand_derived_svg_path(self) -> None:
        # x=10, y=20, width=20, height=100, radius=4 (well within width/2=10
        # and height=100, so r stays 4 unclamped). Path traced by hand from
        # the docstring's "M -> L -> Q -> L -> Q -> L -> Z" recipe:
        #   start bottom-left (10,120), up the left edge to (10,24), quarter
        #   arc to the top edge at (14,20), across to (26,20), quarter arc
        #   down to the right edge at (30,24), down to bottom-right (30,120),
        #   close.
        path = report.rounded_top_rect_path(x=10, y=20, width=20, height=100, radius=4)
        self.assertEqual(
            path, "M10,120 L10,24 Q10,20 14,20 L26,20 Q30,20 30,24 L30,120 Z"
        )

    def test_rounded_top_rect_path_clamps_radius_to_bar_size(self) -> None:
        # radius=10 requested on a 6-wide, 2-tall bar: r = min(10, width/2=3,
        # height=2) = 2, so the path must use r=2, not the requested 10.
        path = report.rounded_top_rect_path(x=0, y=0, width=6, height=2, radius=10)
        self.assertEqual(path, "M0,2 L0,2 Q0,0 2,0 L4,0 Q6,0 6,2 L6,2 Z")

    def test_rounded_top_rect_path_empty_for_non_positive_height(self) -> None:
        self.assertEqual(report.rounded_top_rect_path(0, 0, 20, 0, radius=4), "")

    def test_layout_chart_bars_places_slots_left_to_right(self) -> None:
        groups = [
            report.ChartGroup(label="sonnet", bars=(_present_bar("a"), _present_bar("b"))),
            report.ChartGroup(label="opus", bars=(_present_bar("a"), _present_bar("b"))),
        ]
        placed = report.layout_chart_bars(groups, self.geometry)
        # group width = 2*20 + 1*2 = 42; group 0 starts at plot_left=46,
        # group 1 starts at 46 + (42 + 32) = 120 (group_gap=32 between them).
        xs = [(p.group_label, p.bar.slot, p.x) for p in placed]
        self.assertEqual(
            xs,
            [
                ("sonnet", "a", 46.0),
                ("sonnet", "b", 68.0),  # 46 + bar_width(20) + bar_gap(2)
                ("opus", "a", 120.0),
                ("opus", "b", 142.0),
            ],
        )

    def test_chart_content_width_sums_groups_and_gaps(self) -> None:
        groups = [
            report.ChartGroup(label="sonnet", bars=(_present_bar("a"), _present_bar("b"))),
            report.ChartGroup(label="opus", bars=(_present_bar("a"), _present_bar("b"))),
        ]
        # 2 groups * group_width(42) + 1 gap * group_gap(32) = 116.
        self.assertEqual(report.chart_content_width(groups, self.geometry), 116.0)

    def test_chart_content_width_empty_groups_is_zero(self) -> None:
        self.assertEqual(report.chart_content_width([], self.geometry), 0.0)

    def test_group_label_positions_centered_under_each_cluster(self) -> None:
        groups = [
            report.ChartGroup(label="sonnet", bars=(_present_bar("a"), _present_bar("b"))),
            report.ChartGroup(label="opus", bars=(_present_bar("a"), _present_bar("b"))),
        ]
        positions = report.group_label_positions(groups, self.geometry)
        # group_width=42 -> center = left + 21: group 0 left=46 -> 67.0;
        # group 1 left=120 -> 141.0.
        self.assertEqual(positions, [("sonnet", 67.0), ("opus", 141.0)])


if __name__ == "__main__":
    unittest.main()
