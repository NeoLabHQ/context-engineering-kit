#!/usr/bin/env python3
"""Checks README.md's factual claims against this tree, so documentation drift
fails a test run instead of being noticed by a reader.

WHY THIS FILE EXISTS
---------------------
Two documentation defects shipped in this harness's own history, both of the
same shape -- a sentence that the repo's data falsifies:

1. "Every cost this harness reported before that override was understated" --
   false, because `runs/_preflight/abs-stepped-slices__HyQJyYy` has a single
   `result` event and its recorded cost was always correct.
2. A "Cost and time" section that opened with "No run of this harness has been
   executed. Every number below is ... not a measurement", 38 lines above a
   table of measurements taken from `runs/`.

Both are checked below, along with every other claim in the README that data in
this tree can settle. `.claude/rules/scope-documented-claims-to-what-was-measured.md`
and `.claude/rules/retire-superseded-evidence-disclaimers.md` are the rules
these tests enforce mechanically.

WHAT THIS FILE DOES NOT COVER
------------------------------
The skip counts the README quotes for the two test commands are NOT checked
here: a skip count cannot be known without running the suite, and pinning it
would make every future test addition fail an unrelated assertion. Those
numbers are maintained by hand and re-measured by running the suite -- which is
also why no test count is repeated in this docstring.

Stdlib only, no `pier`, no `jinja2`.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

import collect  # sys.path patched by tests/__init__.py

from . import BENCHMARK_DIR
from .test_collect_completion_gate import recorded_final_messages

README_PATH = BENCHMARK_DIR / "README.md"


def readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def readme_section(heading: str) -> str:
    """The body of one `### heading` section, up to the next `### ` heading."""
    body = readme().split(f"### {heading}", 1)
    assert len(body) == 2, f"README has no '### {heading}' section"
    return body[1].split("\n### ", 1)[0]


def error_reasons_the_code_produces() -> set[str]:
    """Every `error_reason` string this codebase can attach to a trial record.

    Built by calling the real classifiers rather than by copying literals out of
    `collect.py`, so a renamed reason changes this set too.
    """
    reasons = {
        collect.incompleteness_reason_from_signals(has_model_patch=False, final_message=None),
        collect.incompleteness_reason_from_signals(
            has_model_patch=True, final_message="Which would you like?"
        ),
        # Rule 4 of the classification table: verifier produced no rewards.
        collect.classify_status(
            exception_type=None, rewards=None, plugin_load_error=None, incompleteness_reason=None
        )[1],
        # Rule 3: pier's own infra-failure signal, normalized.
        collect.classify_status(
            exception_type="AgentTimeoutError",
            rewards=None,
            plugin_load_error=None,
            incompleteness_reason=None,
        )[1],
        # Rule 2: the plugin-load reasons.
        collect.plugin_load_error_from_init_event(None),
        collect.plugin_load_error_from_init_event({"plugins": [{"name": "other"}]}),
    }

    # Rule 1 needs a trial directory whose result.json cannot be parsed.
    with tempfile.TemporaryDirectory() as tmp:
        trial_dir = Path(tmp) / "trial-1"
        trial_dir.mkdir()
        (trial_dir / "result.json").write_text("{not valid json")
        record = collect.build_trial_record(
            trial_dir,
            {"arm_id": "a", "orchestrator_tier": "sonnet", "impl_tier": "sonnet", "is_vanilla": True},
        )
        reasons.add(record.error_reason)

    return {reason for reason in reasons if reason}


def readme_error_reason_tokens() -> set[str]:
    """Every backticked value in the `error_reason` column of the status table."""
    tokens: set[str] = set()
    for line in readme().splitlines():
        if not line.startswith("| `") or line.count("|") < 5:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[0].strip("`") not in {"resolved", "unresolved", "incomplete", "errored"}:
            continue
        tokens.update(re.findall(r"`([^`]+)`", cells[2]))
    return tokens


class SupersededDisclaimerTests(unittest.TestCase):
    """Defect 2: a blanket "nothing below is measured" claim over measured data.

    Each pattern below is a sentence this README actually carried while also
    presenting measurements. They are pinned as forbidden rather than described,
    so re-adding one fails here.
    """

    SUPERSEDED_CLAIMS = {
        "No run of this harness has been executed": "three trials are recorded under runs/",
        "Every number below is a stated assumption": "the Cost section presents measured figures",
        "Everything in the next section is a labeled assumption": (
            "the next section's per-trial cost figures are measured"
        ),
    }

    def test_the_one_trial_per_recorded_job_claim_is_true(self) -> None:
        # The narrowed disclaimer's factual basis: no multi-task run exists.
        # Re-derived from the committed corpus of recorded trials, whose keys
        # are `<job-dir>/<trial-dir>` -- one entry per recorded trial. If any
        # job had held two, two entries would share a job-dir prefix.
        self.assertIn("hold exactly one trial each", readme())
        job_dirs = [record["trial"].split("/")[0] for record in recorded_final_messages()]
        self.assertTrue(job_dirs, "corpus lists no recorded trials")
        self.assertEqual(len(job_dirs), len(set(job_dirs)))

    def test_no_superseded_blanket_disclaimer_remains(self) -> None:
        text = readme()
        for claim, why_false in self.SUPERSEDED_CLAIMS.items():
            with self.subTest(claim=claim):
                self.assertNotIn(claim, text, f"README claim is false: {why_false}")

    def test_the_cost_section_labels_its_measurements_where_it_disclaims(self) -> None:
        # The narrowed disclaimer has to actually distinguish projections from
        # measurements -- not merely drop the offending sentence.
        section = readme_section("Cost and time — read this before `--mode full`")
        self.assertIn("Measured", section)
        self.assertRegex(section, r"Every projected \*total\* below is therefore an extrapolation")
        self.assertRegex(section, r"labeled \*Measured\* are real measurements")
        self.assertIn("recorded under `runs/`", section)


class MeasuredCostClaimTests(unittest.TestCase):
    """Defect 1: the cost table and the generalization drawn from it.

    WHAT MOVED, AND WHY
    --------------------
    This class used to re-derive each cost-table row from the artifacts under
    `runs/` and compare them. That comparison could not survive being detached
    from `runs/`: its whole content was "the README's figures equal these
    particular recordings' figures", and without the recordings there is
    nothing left to compare against -- a version of it built on constructed
    fixtures would be asserting that a number the fixture states matches a
    number the README states, which is a tautology dressed as a measurement.

    So the artifact half is gone, and with it the guarantee that the three
    quoted dollar figures still match the streams they were read from. That
    was a documentation-accuracy check against unreproducible measurements,
    not a unit test, and it had already stopped holding: the trial the top row
    names is no longer among the recordings in this tree.

    What remains is everything about the table that does NOT need the
    recordings -- that it is present, internally consistent, and still says
    what the code does. `collect.py`'s cost behaviour, the actual rule the
    bottom test is about, is pinned directly on a staged trial rather than on
    a recording.
    """

    def cost_section(self) -> str:
        return readme_section("Cost and time — read this before `--mode full`")

    def table_rows(self) -> list[str]:
        """The cost table's data rows -- `| \\`<job-dir>/...\\` | n | ... |`."""
        return [
            line
            for line in self.cost_section().splitlines()
            if line.startswith("| `") and "→" in line
        ]

    def test_the_cost_table_is_still_present_with_its_rows(self) -> None:
        # Guards every assertion below: a table that lost its rows would make
        # the per-row checks vacuously true.
        rows = self.table_rows()
        self.assertGreaterEqual(len(rows), 3)

    def test_every_table_row_is_internally_consistent(self) -> None:
        # Each row states an event count, a first→last pair and a verdict. The
        # verdict has to follow from the pair: equal figures mean the recorded
        # cost was correct, and a rise means it was understated by the ratio
        # the row itself quotes. A row can drift out of agreement with its own
        # numbers without anyone noticing; this is what catches that.
        for row in self.table_rows():
            with self.subTest(row=row[:48]):
                figures = [float(match) for match in re.findall(r"\$(\d+\.\d+)", row)]
                self.assertEqual(len(figures), 3, "expected first, last and recorded")
                first, last, recorded = figures

                # Pier recorded the FIRST event -- the defect being fixed.
                self.assertEqual(recorded, first)

                if first == last:
                    self.assertIn("correct", row)
                else:
                    self.assertIn(f"understated {round(last / first)}x", row)

    def test_the_single_event_row_is_the_one_called_correct(self) -> None:
        # The bounded claim's own evidence: the README says single-`result`-
        # event trials were always correct, so exactly the rows reporting one
        # event may be the rows calling the recorded figure correct.
        for row in self.table_rows():
            with self.subTest(row=row[:48]):
                n_events = int(re.search(r"\|\s*(\d+)\s*\|", row).group(1))
                self.assertEqual(n_events == 1, "correct" in row)

    def test_the_generalization_stays_bounded_rather_than_universal(self) -> None:
        # The sentence whose universally-quantified predecessor was false.
        # Pinned verbatim because the failure mode is prose drifting back to
        # "every cost was understated", which the table below it disproves.
        self.assertIn(
            "any trial whose stream carries more than one `result` event was understated "
            "the same way, and single-`result`-event trials were always correct",
            readme(),
        )

    def test_collect_still_reports_the_recorded_cost_as_the_readme_says(self) -> None:
        # "Trials already recorded in runs/ keep whatever figure pier wrote at
        # the time" -- true only while collect.py reads the cost out of
        # result.json instead of re-deriving it from the stream. Staged with
        # the two deliberately DISAGREEING, which is the whole point: a
        # collector that re-derived would report the stream's larger total and
        # silently restate figures for runs already on disk.
        self.assertIn(
            "**Trials already recorded in `runs/` keep whatever figure pier wrote at the time**",
            readme(),
        )
        recorded_cost, stream_total = 0.392, 26.530

        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial-1"
            (trial_dir / "agent").mkdir(parents=True)
            (trial_dir / "agent" / "claude-code.txt").write_text(
                "\n".join(
                    json.dumps({"type": "result", "subtype": "success", "total_cost_usd": cost})
                    for cost in (recorded_cost, 12.0, stream_total)
                )
            )
            (trial_dir / "result.json").write_text(
                json.dumps(
                    {
                        "task_name": "datacurve/task-1",
                        "task_checksum": "checksum-1",
                        "verifier_result": {"rewards": {"reward": 0, "f2p": 0.0, "p2p": 1.0}},
                        "exception_info": None,
                        "agent_info": {"version": "1.0.0"},
                        "agent_result": {"cost_usd": recorded_cost},
                    }
                )
            )
            record = collect.build_trial_record(
                trial_dir,
                {
                    "arm_id": "do-in-steps__sonnet-sonnet",
                    "orchestrator_tier": "sonnet",
                    "impl_tier": "sonnet",
                    "skill": "do-in-steps",
                    "is_vanilla": True,  # skips the plugin-load check; irrelevant to cost
                    "cek_ref": "cek@test",
                },
            )

        self.assertEqual(record.cost_usd, recorded_cost)
        self.assertNotEqual(record.cost_usd, stream_total)


class QuotedTranscriptTests(unittest.TestCase):
    """The README quotes recorded agent prose; it must be verbatim and current.

    Checked against `tests/fixtures/recorded-final-messages.txt` -- the
    committed copy of every recorded trial's closing prose -- rather than
    against `runs/` itself, so the quote stays grounded in a checkout that
    does not have the recordings. The fixture is verbatim (see that
    directory's README), which is what makes "verbatim" checkable here.
    """

    QUESTION_TRIAL = "_preflight-do-in-steps/cattrs-partial-structuring-recov__9ryVMmH"
    QUOTED = "Which approach would you prefer? Or shall I continue with the current orchestration pace?"

    def test_the_quoted_final_message_is_verbatim(self) -> None:
        self.assertIn(self.QUOTED, readme())
        recorded = next(
            record
            for record in recorded_final_messages()
            if record["trial"] == self.QUESTION_TRIAL
        )
        self.assertTrue(recorded["closing_region"].strip().endswith(self.QUOTED))

    def test_the_readmes_claim_about_the_heuristic_is_true(self) -> None:
        # "…while the other recorded trials … are correctly left alone": the
        # quoted trial is the only recording the heuristic fires on.
        caught = {
            record["trial"]
            for record in recorded_final_messages()
            if collect.message_ends_in_question(record["closing_region"])
        }
        self.assertEqual(caught, {self.QUESTION_TRIAL})


class DocumentedStatusContractTests(unittest.TestCase):
    """Every status and `error_reason` value the README names must be real."""

    def test_the_status_table_names_exactly_the_statuses_that_exist(self) -> None:
        from typing import get_args

        table = readme()
        for status in get_args(collect.Status):
            with self.subTest(status=status):
                self.assertIn(f"| `{status}` |", table)

    def test_both_incompleteness_reasons_the_code_emits_are_named_in_the_readme(self) -> None:
        # code -> README. The two incompleteness reasons come from one function,
        # so this direction can be checked exhaustively rather than by string
        # search. The opposite direction is the test below.
        emitted = {
            collect.incompleteness_reason_from_signals(
                has_model_patch=False, final_message=None
            ),
            collect.incompleteness_reason_from_signals(
                has_model_patch=True, final_message="Which would you like?"
            ),
        }
        self.assertEqual(emitted, {"no_model_patch", "final_message_is_question"})
        for reason in emitted:
            with self.subTest(reason=reason):
                self.assertIn(f"`{reason}`", readme())

    def test_every_error_reason_the_readme_names_is_one_the_code_produces(self) -> None:
        """README -> code, the direction the test above does not cover.

        Reads the `error_reason` cells straight out of the README's status
        table and requires every backticked value there to be a string the code
        really produces -- or, for the one templated form, to match the shape it
        produces. Without this the table could name a reason nothing emits, and
        the three `errored` forms in particular were never checked at all.
        """
        produced = error_reasons_the_code_produces()

        documented = readme_error_reason_tokens()
        self.assertTrue(documented, "no error_reason values found in the README status table")

        for token in documented:
            with self.subTest(error_reason=token):
                if "<" in token:
                    # A template such as `pier_exception:<category>:<type>`:
                    # require something the code produces to match its shape.
                    # Literal parts are escaped; each `<placeholder>` becomes a
                    # one-segment wildcard.
                    pattern = re.compile(
                        "^"
                        + "".join(
                            "[^:]+" if part.startswith("<") else re.escape(part)
                            for part in re.split(r"(<[^>]+>)", token)
                        )
                        + "$"
                    )
                    self.assertTrue(
                        any(pattern.match(reason) for reason in produced),
                        f"README documents the form {token!r}, which nothing produces",
                    )
                else:
                    self.assertIn(token, produced)

    def test_the_readme_documents_how_to_re_run_an_incomplete_arm(self) -> None:
        self.assertRegex(readme(), r"re-run it with `--force`")

    def test_the_incomplete_recipe_pairs_force_with_deleting_the_trial_directory(
        self,
    ) -> None:
        """Pins the fragment that makes the `--force` recipe above correct.

        The assertion above only pins "...re-run it with `--force`" in
        isolation. On its own that fragment is *wrong* -- README lines just
        above it explain `--force` alone cannot re-attempt an INCOMPLETE
        trial, because pier's per-trial resume still skips a trial directory
        that already has a `result.json`. The step that makes `--force`
        correct is deleting that trial's own directory first, so `result.json`
        stops existing for pier to skip.

        A future edit could delete that directory-deletion clause and leave
        "...re-run it with `--force`" standing alone; the assertion above
        would keep passing while the recipe silently regressed to the wrong
        claim it currently corrects. Requiring "own directory" to appear
        shortly before "re-run it with `--force`" (bounded, so it cannot
        match the unrelated STUCK recipe's "job directory" elsewhere in this
        file) catches that regression.
        """
        self.assertRegex(readme(), r"own directory.{0,60}re-run it with `--force`")


class NoSpendCapTests(unittest.TestCase):
    """The forbidden flag must not reappear in the docs either."""

    def test_no_spend_cap_flag_is_documented(self) -> None:
        for forbidden in ("--max-budget-usd", "--max-budget", "max_budget_usd"):
            with self.subTest(flag=forbidden):
                self.assertNotIn(forbidden, readme())

    def test_the_readme_still_says_there_is_no_cap(self) -> None:
        self.assertIn("This harness enforces no per-trial spend cap", readme())


if __name__ == "__main__":
    unittest.main()
