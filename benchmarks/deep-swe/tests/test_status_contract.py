#!/usr/bin/env python3
"""Cross-module tests that every `collect.Status` value is understood end to end.

`status` is produced in `collect.py`, aggregated into `ArmAggregate`, and
rendered by `report.py`. Adding a value to the literal without also adding its
per-arm count and its report column would leave a status only one module
understands -- a trial silently missing from the table an operator reads. These
tests derive the expectation from `typing.get_args(collect.Status)` rather than
a hand-kept list, so a fifth state cannot be added without either wiring it
through or failing here.

Stdlib only, no `pier`: both modules under test import neither.
"""

from __future__ import annotations

import unittest
from dataclasses import fields
from typing import get_args

import collect  # sys.path patched by tests/__init__.py
import report

from .collect_fixtures import make_trial
from .report_fixtures import make_arm

# `resolved` is reported as the Pass@1 numerator (`n_resolved`) rather than as a
# problem column, so it is the one status with no report.py column of its own --
# its count is what `pass_at_1` is computed from. Every other status must be
# visible in the arm table, because every other one is a way a trial did not
# succeed.
STATUSES_WITHOUT_REPORT_COLUMN = {"resolved", "unresolved"}


class StatusContractTests(unittest.TestCase):
    def test_the_four_known_statuses_are_the_whole_literal(self) -> None:
        # A canary on the literal itself: if this fails, the rest of this file
        # is telling you which wiring the new value still needs.
        self.assertEqual(
            set(get_args(collect.Status)),
            {"resolved", "unresolved", "incomplete", "errored"},
        )

    def test_every_status_has_an_arm_aggregate_count_field(self) -> None:
        aggregate_field_names = {field.name for field in fields(collect.ArmAggregate)}
        for status in get_args(collect.Status):
            with self.subTest(status=status):
                self.assertIn(f"n_{status}", aggregate_field_names)

    def test_every_status_is_counted_by_aggregate_arm(self) -> None:
        # One trial per status through the real aggregator: each must land in
        # its own count, and nothing may be double-counted.
        statuses = get_args(collect.Status)
        aggregate = collect.aggregate_arm([make_trial(status) for status in statuses])

        for status in statuses:
            with self.subTest(status=status):
                self.assertEqual(getattr(aggregate, f"n_{status}"), 1)
        self.assertEqual(aggregate.n_total_trials, len(statuses))
        # Every status except `errored` is an attempt -- see collect.py's
        # "PASS@1 DENOMINATOR" docstring section.
        self.assertEqual(aggregate.n_attempts, len(statuses) - 1)

    def test_every_problem_status_reaches_the_report_arm_table(self) -> None:
        arm = make_arm()
        row = report.arm_table_rows([arm])[0]
        table_html = report.render_arm_table([arm])

        for status in get_args(collect.Status):
            if status in STATUSES_WITHOUT_REPORT_COLUMN:
                continue
            with self.subTest(status=status):
                self.assertIn(f"n_{status}", row)
                self.assertIn(f"<th class='num'>{status.capitalize()}</th>", table_html)

    def test_report_expects_the_schema_version_collect_writes(self) -> None:
        # report.py mirrors the constant rather than importing it (see its
        # docstring); this is what keeps the copy honest.
        self.assertEqual(
            report.EXPECTED_RESULTS_SCHEMA_VERSION, collect.RESULTS_SCHEMA_VERSION
        )


if __name__ == "__main__":
    unittest.main()
