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

README_PATH = BENCHMARK_DIR / "README.md"
RUNS_DIR = BENCHMARK_DIR / "runs"


def readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def readme_section(heading: str) -> str:
    """The body of one `### heading` section, up to the next `### ` heading."""
    body = readme().split(f"### {heading}", 1)
    assert len(body) == 2, f"README has no '### {heading}' section"
    return body[1].split("\n### ", 1)[0]


def recorded_trial_costs() -> dict[str, tuple[int, float, float, float | None]]:
    """Per recorded trial: (n result events, first cost, last cost, cost pier recorded).

    Derived from the artifacts themselves -- the stream for the events, the
    trial's `result.json` for what pier wrote down -- so these tests compare the
    README against data rather than against another copy of the README.
    """
    measured: dict[str, tuple[int, float, float, float | None]] = {}
    for result_path in sorted(RUNS_DIR.glob("*/*/result.json")):
        trial_dir = result_path.parent
        costs = [
            event["total_cost_usd"]
            for event in collect.iter_stream_events(
                trial_dir / "agent" / "claude-code.txt"
            )
            if event.get("type") == "result" and event.get("total_cost_usd") is not None
        ]
        if not costs:
            continue
        recorded = (
            json.loads(result_path.read_text()).get("agent_result") or {}
        ).get("cost_usd")
        measured[f"{trial_dir.parent.name}/{trial_dir.name}"] = (
            len(costs),
            costs[0],
            costs[-1],
            recorded,
        )
    return measured


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
        if not RUNS_DIR.exists():
            self.skipTest(f"recorded runs not present at {RUNS_DIR}")
        self.assertIn("hold exactly one trial each", readme())
        for job_dir in sorted(p for p in RUNS_DIR.iterdir() if p.is_dir()):
            with self.subTest(job=job_dir.name):
                trials = list(job_dir.glob("*/result.json"))
                self.assertEqual(len(trials), 1)

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


@unittest.skipUnless(RUNS_DIR.exists(), f"recorded runs not present at {RUNS_DIR}")
class MeasuredCostClaimTests(unittest.TestCase):
    """Defect 1: the cost table and the generalization drawn from it."""

    # Each README row, as (README label, events, first, last, understatement).
    # `None` understatement means the row claims the recorded cost was correct.
    TABLE_ROWS = {
        "do-in-steps__sonnet-sonnet/cattrs-partial-structuring-recov__ZsbwRdJ": (22, 0.392, 26.530, 68),
        "_preflight-do-in-steps/cattrs-partial-structuring-recov__9ryVMmH": (11, 0.140, 1.804, 13),
        "_preflight/abs-stepped-slices__HyQJyYy": (1, 1.865, 1.865, None),
    }

    def test_every_table_row_matches_the_artifacts(self) -> None:
        measured = recorded_trial_costs()
        self.assertEqual(sorted(measured), sorted(self.TABLE_ROWS))

        for trial, (events, first, last, understatement) in self.TABLE_ROWS.items():
            with self.subTest(trial=trial):
                n_events, actual_first, actual_last, recorded = measured[trial]
                self.assertEqual(n_events, events)
                self.assertEqual(round(actual_first, 3), first)
                self.assertEqual(round(actual_last, 3), last)
                # Pier recorded the FIRST event -- the defect being fixed.
                self.assertEqual(recorded, actual_first)
                if understatement is None:
                    self.assertEqual(recorded, actual_last)
                else:
                    self.assertEqual(round(actual_last / recorded), understatement)

    def test_the_table_rows_appear_in_the_readme_with_these_numbers(self) -> None:
        section = readme_section("Cost and time — read this before `--mode full`")
        for trial, (events, first, last, understatement) in self.TABLE_ROWS.items():
            with self.subTest(trial=trial):
                # Match on `<job-dir>/` including the slash: `_preflight` is a
                # prefix of `_preflight-do-in-steps`, so a prefix match would
                # find the wrong row.
                job_dir_name = trial.split("/")[0]
                row = next(
                    (
                        line
                        for line in section.splitlines()
                        if line.startswith(f"| `{job_dir_name}/")
                    ),
                    None,
                )
                self.assertIsNotNone(row, f"no cost-table row for {job_dir_name}/")
                self.assertIn(f"| {events} |", row)
                self.assertIn(f"${first:.3f}", row)
                self.assertIn(f"${last:.3f}", row)
                expected_verdict = (
                    "correct" if understatement is None else f"understated {understatement}x"
                )
                self.assertIn(expected_verdict, row)

    def test_the_bounded_generalization_holds_for_every_recorded_trial(self) -> None:
        # The README's claim, in code: multi-event streams were understated,
        # single-event ones were always correct. This is the assertion whose
        # universally-quantified predecessor was false.
        self.assertIn(
            "any trial whose stream carries more than one `result` event was understated "
            "the same way, and single-`result`-event trials were always correct",
            readme(),
        )
        for trial, (n_events, first, last, recorded) in recorded_trial_costs().items():
            with self.subTest(trial=trial):
                if n_events == 1:
                    self.assertEqual(recorded, last)
                else:
                    self.assertEqual(recorded, first)
                    self.assertNotEqual(recorded, last)

    def test_collect_still_reports_the_recorded_cost_as_the_readme_says(self) -> None:
        # "Trials already recorded in runs/ keep their original, understated
        # figure" -- true only while collect.py reads result.json instead of
        # re-deriving from the stream.
        self.assertIn(
            "**Trials already recorded in `runs/` keep whatever figure pier wrote at the time**",
            readme(),
        )
        arm_meta = {
            "arm_id": "do-in-steps__sonnet-sonnet",
            "orchestrator_tier": "sonnet",
            "impl_tier": "sonnet",
            "skill": "do-in-steps",
            "is_vanilla": True,  # skips the plugin-load check; irrelevant to cost
            "cek_ref": "cek@test",
        }
        trial_dir = RUNS_DIR / "do-in-steps__sonnet-sonnet" / "cattrs-partial-structuring-recov__ZsbwRdJ"
        record = collect.build_trial_record(trial_dir, arm_meta)
        n_events, first, last, recorded = recorded_trial_costs()[
            "do-in-steps__sonnet-sonnet/cattrs-partial-structuring-recov__ZsbwRdJ"
        ]
        self.assertEqual(record.cost_usd, recorded)
        self.assertNotEqual(record.cost_usd, last)


@unittest.skipUnless(RUNS_DIR.exists(), f"recorded runs not present at {RUNS_DIR}")
class QuotedTranscriptTests(unittest.TestCase):
    """The README quotes recorded agent prose; it must be verbatim and current."""

    QUESTION_TRIAL = "_preflight-do-in-steps/cattrs-partial-structuring-recov__9ryVMmH"
    QUOTED = "Which approach would you prefer? Or shall I continue with the current orchestration pace?"

    def test_the_quoted_final_message_is_verbatim(self) -> None:
        self.assertIn(self.QUOTED, readme())
        trial_dir = RUNS_DIR / Path(self.QUESTION_TRIAL)
        final_message = collect.find_stream_log_final_message(trial_dir)
        self.assertIsNotNone(final_message)
        self.assertTrue(final_message.strip().endswith(self.QUOTED))

    def test_the_readmes_claim_about_the_heuristic_is_true(self) -> None:
        # "…while the other two recorded trials … are correctly left alone".
        verdicts = {}
        for result_path in sorted(RUNS_DIR.glob("*/*/result.json")):
            trial_dir = result_path.parent
            key = f"{trial_dir.parent.name}/{trial_dir.name}"
            verdicts[key] = collect.message_ends_in_question(
                collect.find_stream_log_final_message(trial_dir)
            )
        self.assertTrue(verdicts.pop(self.QUESTION_TRIAL))
        self.assertEqual(set(verdicts.values()), {False})


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
