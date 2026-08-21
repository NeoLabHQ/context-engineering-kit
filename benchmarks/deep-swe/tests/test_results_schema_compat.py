#!/usr/bin/env python3
"""`report.py` must keep working against the `results.json` `collect.py` writes.

WHY THIS FILE EXISTS
---------------------
`collect.py` writes `results.json`; `report.py` reads it. Their agreement is
two separate claims, and this file tests only the second one:

  1. The mirrored `schema_version` integers match. That is an integer
     comparison, it lives in `tests/test_status_contract.py`, and it is
     asserted there ONCE -- duplicating it here only produced two copies to
     weaken independently.
  2. The PAYLOAD is actually readable end to end. That is a claim about
     behaviour, so the tests below run the real `report.main()` over a real
     `collect.main()` output and assert a complete report comes out.

(2) is the guarantee an integer cannot give: it would catch a `results.json`
that carried the right version number and an unreadable body. It is also not
a substitute for (1), which catches the mirrored constant silently drifting.

`collect.py` grew three top-level sections -- `cells`, `schedule` and
`baseline` -- without a version bump, because they are purely ADDITIVE: no
`TrialRecord`/`ArmAggregate` field changed, and a consumer detects them by key
presence. `test_the_added_sections_kept_every_field_the_report_reads` is that
rule written as a check rather than left as a promise.
"""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from dataclasses import fields
from pathlib import Path
from tempfile import TemporaryDirectory

import collect  # sys.path patched by tests/__init__.py
import report


def collect_into(out_dir: Path) -> dict:
    """Run the real collector over the committed `runs/` tree, returning its JSON."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exit_code = collect.main(
            ["--runs-dir", str(collect.SCRIPT_DIR / "runs"), "--out-dir", str(out_dir)]
        )
    assert exit_code == 0, exit_code
    return json.loads((out_dir / "results.json").read_text())


class AdditiveSchemaTests(unittest.TestCase):
    """The version integers are guarded in `test_status_contract.py`; what is
    guarded here is the rule that let the new sections skip a bump at all."""

    def test_the_added_sections_kept_every_field_the_report_reads(self) -> None:
        # The additive rule, stated as a check rather than a promise.
        for name in ("arm_id", "skill", "orchestrator", "impl", "is_vanilla", "pass_at_1", "created_at"):
            with self.subTest(field=name):
                self.assertIn(name, {f.name for f in fields(collect.ArmAggregate)})


class ReportStillRendersTests(unittest.TestCase):
    """The end-to-end property: collect writes, report reads, a report appears."""

    def test_report_main_renders_a_full_report_from_the_current_schema(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            results = collect_into(out_dir)
            self.assertEqual(results["schema_version"], collect.RESULTS_SCHEMA_VERSION)

            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = report.main(
                    [
                        "--results",
                        str(out_dir / "results.json"),
                        "--out",
                        str(out_dir / "report.html"),
                    ]
                )

            self.assertEqual(exit_code, 0)
            html = (out_dir / "report.html").read_text()

        # The two constants agree, so there is nothing to warn about. A
        # warning here would mean the mirror had drifted -- and a per-run
        # warning nobody can act on is how operators learn to ignore stderr.
        self.assertNotIn("schema_version", stderr.getvalue())
        # Every section the report had before is still rendered.
        for marker in ("<table", "Official baseline (mini-swe-agent, not claude-code)", "</html>"):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_the_new_sections_are_present_but_do_not_disturb_the_old_ones(self) -> None:
        with TemporaryDirectory() as tmp:
            results = collect_into(Path(tmp))

        self.assertEqual(set(results) >= {"trials", "arms", "cells", "schedule", "baseline"}, True)
        # The two keys report.py reads are untouched in shape.
        self.assertIsInstance(results["trials"], list)
        self.assertIsInstance(results["arms"], list)
        for arm in results["arms"]:
            self.assertIn("pass_at_1", arm)


if __name__ == "__main__":
    unittest.main()
