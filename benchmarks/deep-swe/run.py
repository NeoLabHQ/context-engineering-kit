#!/usr/bin/env python3
"""Deep-SWE benchmark matrix runner -- shells out to `pier run` per arm.

WHAT AN "ARM" IS
-----------------
An arm is one (skill, orchestrator tier, impl tier) combination. Two tiers
are involved because two different processes read them:

- The **orchestrator** tier is passed as pier's `-m` flag. Pier turns that
  into the `ANTHROPIC_MODEL` env var for the top-level `claude` process pier
  launches inside the container -- this is the model that reads the task,
  loads the `sadd` plugin, and (for plugin arms) runs the slash command.
- The **impl/judge** tier is baked into the rendered prompt as the slash
  command's own `--model` flag (e.g. `/do-and-judge --model haiku ...`). The
  skill hands that string to the sub-agents *it* dispatches (implementation,
  meta-judge, judge). It never touches pier's CLI.

Crossing these two up is the single easiest way to silently invalidate every
number this harness produces -- get "opus orchestrates, haiku implements"
backwards and you're measuring the opposite comparison from the one you
think you're running. `CELLS` below is the only place tier pairs are listed;
everything downstream reads from it rather than re-deriving pairs.

CELLS x SKILLS = 10 plugin arms. `--with-vanilla` adds 3 no-plugin control
arms (one per model, orchestrating itself with no slash command at all) for
13 total. `--skill` restricts the matrix to one skill's 5 CELLS arms (8 with
`--with-vanilla`); vanilla arms aren't tied to any skill, so `--skill` never
drops or duplicates them -- only `--with-vanilla` governs their presence.
`--model` restricts the matrix to one symmetric tier's arm (1 CELLS arm per
skill in play instead of 5); unlike `--skill`, it also restricts
`--with-vanilla`'s controls to that one tier (1 instead of 3), since vanilla
arms are per-model rather than per-skill. `--skill` and `--model` combine to
select exactly one arm.

RUN LAYOUT (see bottom of file / task handoff notes for the authoritative
version of this -- kept here too so the two can be diffed against drift):

    runs/<arm-id>/                     <- pier's --jobs-dir/--job-name, i.e. its job_dir
        prompt.j2                      <- this arm's rendered slash-command template
        arm.json                       <- (skill, orchestrator, impl) metadata for collect.py
        config.json                    <- pier's own job config (written by pier)
        result.json                    <- pier's own job-level result; finished_at != null <=> job ran to completion
        job.log                        <- pier's own job log
        <task-name>__<uuid4>/          <- one directory per trial (written by pier)
            agent/claude-code.txt      <- claude's --output-format=stream-json transcript
            result.json                <- this trial's TrialResult
            artifacts/model.patch      <- the trial's committed diff; ABSENT when the agent
                                          committed nothing (see find_incomplete_trials)
            config.json, trial.log

Everything under `runs/` past `arm.json`/`prompt.j2` is pier's own doing;
`collect.py` (Step 3) walks `runs/*/*/result.json` for trial results and
reads `runs/*/arm.json` to recover which (skill, orchestrator, impl) produced
them, rather than parsing the arm-id string.

PER-ARM STATUS AND EXIT CODES
------------------------------
Every arm this script runs reports one of three statuses, and the process exit
code mirrors the worst one seen:

    PASS        pier exited 0 and every trial produced a patch and a
                finished-looking final message.                     -> exit 0
    INCOMPLETE  pier exited 0, but at least one trial has no
                `artifacts/model.patch` or ended its turn asking the
                operator a question (see `find_incomplete_trials`,
                whose rules live in collect.py).                    -> exit 3
    FAIL        pier itself exited non-zero for this arm.            -> exit 1

FAIL outranks INCOMPLETE: when pier fails, its own exit code is the more
actionable signal, and the trial artifacts it would have been judged on may
not exist at all. INCOMPLETE gets exit code 3 rather than 2 because argparse
already spends 2 on usage errors (`parser.error`), and a CI job must be able
to tell "you invoked me wrong" from "the agents abandoned their tasks".

`--preflight` uses the same exit code for the same condition: its PASSED
verdict covers the plugin checks it exists to make, and an unfinished preflight
trial is reported and exits 3 rather than being folded into either PASSED or a
plugin failure -- see `run_preflight`.

SEED PINNING
------------
Cross-arm comparison is only meaningful if every arm evaluates the same task
subset. `SAMPLE_SEED` is therefore a hardcoded module constant, not a CLI
flag -- there is no argument an operator could pass differently between two
arms in the same invocation, or forget to repeat on a later resume.

PYTHONPATH / CWD
----------------
Pier is installed as a console-script entry point, so its own process never
has this directory on `sys.path`. Its `--agent-import-path agent:ClaudeCodeSadd`
does `importlib.import_module("agent")`, which raises `ModuleNotFoundError`
unless we put this directory on `PYTHONPATH` for the subprocess -- see
`run_pier()`. That same entry is what lets `agent.py` import its sibling
`stream_cost.py` (verified: importing `agent` succeeds from an unrelated cwd
with only `PYTHONPATH` set, and from this directory with only cwd set).
We also `import agent` ourselves (for its `CEK_REF`/
`CEK_INSTALL_DIR` constants); `sys.path` is patched at the top of this file so
that import works regardless of how `run.py` itself was invoked.

REQUIRES: run.py must itself be executed with a Python that has `pier`
installed (e.g. `uv run python3 run.py ...` from this directory, using the
`pyproject.toml`/`uv.lock` checked in here -- see README.md) -- `agent.py`
subclasses pier's own `ClaudeCode`, so `import agent` transitively needs
`pier` importable even before any subprocess is spawned. This is inherent to
subclassing pier's agent hierarchy, not a workaround; there is nothing to fix
in `agent.py` itself, since pier's own subprocess always has `pier` on its
sys.path already -- only *our* top-level `import agent` needs this.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent  # noqa: E402 -- must follow the sys.path patch above

# collect.py holds the completion-gate rules this script reports live (see
# `find_incomplete_trials`). Importing it here, rather than reimplementing
# them, keeps one definition of "incomplete" for the whole harness. This is
# the only safe direction: collect.py must never import run.py/agent.py,
# because those need `pier` and collect.py is required to run (and be tested)
# without it -- see collect.py's own module docstring.
import collect  # noqa: E402 -- must follow the sys.path patch above

# --------------------------------------------------------------------------
# The matrix. This is the single source of truth for every arm this script
# can produce; nothing downstream re-derives tier pairs or arm counts.
# --------------------------------------------------------------------------

# (orchestrator_tier, impl_tier) -- the 5 cells the task spec calls out.
CELLS: list[tuple[str, str]] = [
    ("haiku", "haiku"),
    ("sonnet", "haiku"),
    ("sonnet", "sonnet"),
    ("opus", "sonnet"),
    ("opus", "opus"),
]

# The symmetric CELLS entries -- same tier on both sides -- are what `--model
# <tier>` selects (the task spec's own "haiku,haiku or sonnet,sonnet" framing).
# Derived from CELLS rather than hardcoded, so this list can never list a tier
# CELLS itself doesn't contain as a symmetric pair.
MODEL_CHOICES: list[str] = [orchestrator for orchestrator, impl in CELLS if orchestrator == impl]

# Both live in the sadd plugin with an identical `<task> [--model tier] [--strict]`
# argument surface (verified against plugins/sadd/skills/{do-and-judge,do-in-steps}/SKILL.md).
SKILLS: list[str] = ["do-and-judge", "do-in-steps"]

# No-plugin control arms added by --with-vanilla: the model orchestrates
# itself directly, no slash command, no sub-agent dispatch.
VANILLA_MODELS: list[str] = ["haiku", "sonnet", "opus"]

# Pinned once, here, for every arm and every invocation -- see module
# docstring's "SEED PINNING" section for why this is not a CLI flag.
SAMPLE_SEED = 20260809

# Orchestrator tier -> concrete model id for pier's `-m` flag.
#
# Verified against the real `claude` binary in this environment (2.1.226) by
# setting ANTHROPIC_MODEL=<alias> and reading the resolved `model` field off
# the `system`/`init` stream-json event (pier sets ANTHROPIC_MODEL from `-m`
# verbatim -- see pier/agents/installed/claude_code.py's `_build_run_command`,
# ~line 1272). Pinning dated ids here -- instead of forwarding the bare alias
# straight through to `-m` -- means a benchmark run stays reproducible even
# if Anthropic later repoints an alias at a newer model.
#
# NOTE: re-verify these when the installed claude-code version changes; the
# resolution command is:
#   ANTHROPIC_MODEL=<alias> claude --output-format=stream-json --print -- hi
#   | jq -r 'select(.subtype=="init") | .model'
ORCHESTRATOR_MODEL_ID: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
}

# The impl/judge tier, by contrast, is never translated -- do-and-judge and
# do-in-steps's own `--model` flag literally expects "haiku"/"sonnet"/"opus"
# (see their argument-hint), so the short tier name is passed straight through.

PLUGIN_DIR = Path(agent.CEK_INSTALL_DIR) / "plugins" / "sadd"


@dataclass(frozen=True)
class Arm:
    """One (skill, orchestrator, impl) combination, or a vanilla control.

    `skill` and `impl` are both `None` together for vanilla arms -- there is
    no slash command, so there is no separate impl tier to speak of.
    """

    skill: str | None
    orchestrator: str
    impl: str | None

    @property
    def is_vanilla(self) -> bool:
        return self.skill is None

    @property
    def id(self) -> str:
        """Stable, filesystem-safe id: pier's --job-name and runs/ subdirectory."""
        if self.is_vanilla:
            return f"vanilla__{self.orchestrator}"
        return f"{self.skill}__{self.orchestrator}-{self.impl}"


def build_arms(
    *, include_vanilla: bool, skill: str | None = None, model: str | None = None
) -> list[Arm]:
    """The full arm matrix: SKILLS x CELLS, plus vanilla controls if requested.

    `skill`, when given, restricts the plugin arms to that one skill's CELLS
    (5 arms instead of 10) -- this is `--skill`'s matrix-filtering effect for
    `--mode single/sample/full`. Vanilla control arms are never filtered by
    it: they orchestrate themselves with no slash command, so they aren't
    "of" any skill in the first place -- `include_vanilla` alone governs them,
    same as before this parameter existed.

    `model`, when given, restricts CELLS to that one symmetric tier pair (1
    CELLS arm per skill in play instead of 5) -- this is `--model`'s
    matrix-filtering effect. Unlike `skill`, `model` DOES also restrict the
    vanilla controls, to just that one tier's control instead of all 3:
    vanilla arms are per-model (one per `VANILLA_MODELS` entry), so leaving
    all 3 in would silently reintroduce the other two tiers the operator just
    asked to exclude, defeating the flag's purpose. `skill` and `model`
    combine to select exactly one plugin arm.
    """
    skills = SKILLS if skill is None else [skill]
    cells = CELLS if model is None else [cell for cell in CELLS if cell == (model, model)]
    arms = [
        Arm(skill=s, orchestrator=orchestrator, impl=impl)
        for s in skills
        for orchestrator, impl in cells
    ]
    if include_vanilla:
        vanilla_models = VANILLA_MODELS if model is None else [m for m in VANILLA_MODELS if m == model]
        arms += [Arm(skill=None, orchestrator=m, impl=None) for m in vanilla_models]
    return arms


# --------------------------------------------------------------------------
# Per-arm prompt template + metadata
# --------------------------------------------------------------------------


# Appended verbatim to EVERY arm's prompt -- plugin arms and vanilla controls
# alike. The recorded `do-in-steps__sonnet-sonnet` run finished with
# `stop_reason: end_turn`, `terminal_reason: completed`, `is_error: false` and
# nothing committed. The abandonment behind that is directly observable in a
# sibling recording, `runs/_preflight-do-in-steps/cattrs-partial-structuring-recov__9ryVMmH`,
# whose final message offers a numbered menu under budget pressure and closes
# "Which approach would you prefer? Or shall I continue with the current
# orchestration pace?" -- under `claude --print` there is no stdin and nobody to
# answer, so a question ends the run instead of pausing it. A prompt that never
# establishes there is no human to ask makes that look like a reasonable move.
#
# SYMMETRIC BY CONSTRUCTION, deliberately: vanilla arms are the control this
# benchmark measures the plugin arms *against*, so any prompt text present in
# one and absent from the other becomes a second, uncontrolled difference
# between them, and a Pass@1 gap could no longer be attributed to the skill.
# Vanilla arms are just as non-interactive (same `--print`, same `</dev/null`),
# so the contract is equally true of them -- there is no arm this text would
# be a lie for. It is spliced in by `render_prompt_template_text` below in one
# place shared by both branches, so the two can never drift apart.
#
# Must stay free of Jinja2 syntax (`{{`, `{%`): this text is part of a
# template body rendered under `StrictUndefined` (see below).
NON_INTERACTIVE_CONTRACT = (
    "You are running non-interactively: there is no human in this session and "
    "no stdin to read an answer from. Never end your turn with a question -- "
    "nobody can answer it, so ending on one abandons the task with the work "
    "unfinished. If a decision is ambiguous or a constraint blocks the "
    "approach you wanted, choose the best available option, state the choice "
    "you made and why, and keep working until the task is complete."
)


def render_prompt_template_text(arm: Arm) -> str:
    """The Jinja2 template body pier renders for this arm.

    HARD CONSTRAINT (verified against pier/utils/templating.py
    `render_prompt_template`): it parses this file under Jinja2
    `StrictUndefined` and calls `template.render(instruction=instruction)` --
    `instruction` is the only variable that will ever be bound. Referencing
    anything else raises `UndefinedError` at run time. Vanilla arms therefore
    get a bare `{{ instruction }}` passthrough with no slash command.

    The invocation line stays FIRST, with `NON_INTERACTIVE_CONTRACT` appended
    below it rather than prepended above it: claude-code only dispatches a
    slash command when the prompt *starts* with it, so prose in front of
    `/do-in-steps` would silently demote the whole plugin arm to a vanilla one
    -- the single worst failure this file could cause. Appending keeps the
    contract inside the text the model reads while leaving the first character
    of every plugin prompt a `/`.
    """
    invocation = (
        "{{ instruction }}"
        if arm.is_vanilla
        else f"/{arm.skill} --model {arm.impl} {{{{ instruction }}}}"
    )
    return f"{invocation}\n\n{NON_INTERACTIVE_CONTRACT}\n"


def write_prompt_template(job_dir: Path, arm: Arm) -> Path:
    """Write this arm's template to disk so the run is self-describing."""
    job_dir.mkdir(parents=True, exist_ok=True)
    template_path = job_dir / "prompt.j2"
    template_path.write_text(render_prompt_template_text(arm))
    return template_path


def write_arm_metadata(job_dir: Path, arm: Arm, *, orchestrator_model_id: str, mode: str) -> None:
    """Archive (skill, orchestrator, impl) so collect.py never has to parse arm.id.

    Written as `runs/<arm-id>/arm.json`, a sibling of pier's own config.json/
    result.json in the same job directory.

    `sample_seed` mirrors the pinned `SAMPLE_SEED` module constant, but only
    when this invocation's dataset filter actually used it -- `--mode single`
    and `--mode full` never sample, so the seed played no role in selecting
    this arm's tasks and recording it would misleadingly imply otherwise.
    `None` here means "not applicable to this run mode", a fact collect.py/
    report.py must be able to tell apart from an older arm.json that predates
    this field entirely (see report.py's honest-disclosure fallback).
    """
    metadata = {
        "arm_id": arm.id,
        "skill": arm.skill,
        "is_vanilla": arm.is_vanilla,
        "orchestrator_tier": arm.orchestrator,
        "orchestrator_model_id": orchestrator_model_id,
        "impl_tier": arm.impl,
        "cek_ref": agent.CEK_REF,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sample_seed": SAMPLE_SEED if mode == "sample" else None,
    }
    (job_dir / "arm.json").write_text(json.dumps(metadata, indent=2) + "\n")


# --------------------------------------------------------------------------
# Dataset filter per run mode
# --------------------------------------------------------------------------


def resolve_task_path(dataset_dir: Path, task: str) -> Path:
    """Resolve `--task` to a concrete path for pier's `-p`.

    Accepts either a path that already exists (absolute, or relative to the
    CWD the operator ran run.py from) or a bare task name living inside
    `dataset_dir`.
    """
    candidate = Path(task)
    if candidate.exists():
        return candidate.resolve()
    return (dataset_dir / task).resolve()


def build_dataset_args(
    mode: str, *, dataset_dir: Path, task: str | None, n_tasks: int | None
) -> list[str]:
    """The dataset-filter flags that differ across the three run modes.

    Everything else about an arm's pier invocation is identical regardless
    of mode -- this is the only place mode branches.
    """
    if mode == "single":
        assert task is not None  # enforced by main()'s argument validation
        return ["-p", str(resolve_task_path(dataset_dir, task))]
    if mode == "sample":
        assert n_tasks is not None
        return ["-p", str(dataset_dir), "-l", str(n_tasks), "--sample-seed", str(SAMPLE_SEED)]
    if mode == "full":
        return ["-p", str(dataset_dir)]
    raise ValueError(f"Unknown run mode: {mode!r}")


# --------------------------------------------------------------------------
# Pier invocation
# --------------------------------------------------------------------------


def build_pier_command(
    arm: Arm,
    *,
    pier_bin: str,
    orchestrator_model_id: str,
    template_path: Path,
    job_name: str,
    jobs_dir: Path,
    agent_timeout_multiplier: float,
    dataset_args: list[str],
) -> list[str]:
    """Every flag here was checked against `pier run --help` on the installed
    `datacurve_pier==0.3.0` (see task handoff notes for the verification
    transcript): --agent-import-path, -m, --ak, --agent-timeout-multiplier,
    --job-name, --jobs-dir, -p, -l, --sample-seed all exist with this exact
    spelling.
    """
    cmd = [
        pier_bin,
        "run",
        "--agent-import-path",
        "agent:ClaudeCodeSadd",
        "-m",
        orchestrator_model_id,
    ]
    if not arm.is_vanilla:
        # Only plugin arms load sadd; vanilla arms are the no-plugin control
        # and must never receive --plugin-dir.
        cmd += ["--ak", f"plugin_dir={PLUGIN_DIR}"]
    cmd += ["--ak", f"prompt_template_path={template_path}"]
    cmd += ["--agent-timeout-multiplier", str(agent_timeout_multiplier)]
    cmd += ["--job-name", job_name, "--jobs-dir", str(jobs_dir)]
    cmd += dataset_args
    return cmd


def run_pier(cmd: list[str]) -> int:
    """Shell out to pier, letting stdout/stderr flow straight to the terminal.

    Deliberately NOT captured: these runs take hours, and an operator staring
    at a silent terminal has no way to tell a hung run from a slow one.

    See module docstring's "PYTHONPATH / CWD" section for why both `cwd` and
    `PYTHONPATH` are set to this directory -- belt-and-suspenders so pier's
    `importlib.import_module("agent")` resolves regardless of which
    resolution strategy its installed version relies on.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(SCRIPT_DIR), env.get("PYTHONPATH")) if part
    )
    return subprocess.run(cmd, cwd=SCRIPT_DIR, env=env).returncode


# --------------------------------------------------------------------------
# Resumability
# --------------------------------------------------------------------------


def is_arm_complete(job_dir: Path) -> bool:
    """Whether a prior invocation for this arm already ran to completion.

    Pier writes `<job_dir>/result.json` twice: once immediately when the job
    starts (empty stats, `finished_at=null`) and again after every trial in
    the job has finished (`finished_at` set) -- see pier/job.py `Job.run()`.
    Checking `finished_at` distinguishes "started but interrupted" from
    "actually finished" without us separately recomputing how many trials the
    dataset filter should have produced. Re-invoking pier for the same arm is
    also independently safe even without this check: pier's own resume logic
    (`Job._maybe_init_existing_job`) skips trials that already have a
    `result.json` as long as the job config matches -- this check only saves
    the overhead of starting pier at all for arms with nothing left to do.
    """
    result_path = job_dir / "result.json"
    if not result_path.exists():
        return False
    try:
        data = json.loads(result_path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return data.get("finished_at") is not None


# --------------------------------------------------------------------------
# Completion gate: did the trials this arm ran actually finish?
# --------------------------------------------------------------------------

# Exit codes main() returns. 0 and 1 are unchanged; see the module docstring's
# "PER-ARM STATUS AND EXIT CODES" section for why INCOMPLETE claims 3 and not
# the tempting 2 (argparse's usage-error code).
EXIT_ARM_FAILED = 1
EXIT_TRIALS_INCOMPLETE = 3


def find_incomplete_trials(job_dir: Path) -> dict[str, str]:
    """Map trial_id -> incompleteness reason for every unfinished trial here.

    Empty dict means every trial under this arm looks finished. The rules
    themselves live in `collect.py` (`find_trial_incompleteness_reason`) so
    that what a run reports live and what `results.json` records later can
    never disagree.

    Globs one level down -- `<job_dir>/<trial>/result.json` -- which is the
    trial depth collect.py's `find_trial_result_paths` reaches two levels
    below `runs/`. A trial that never got far enough to write a `result.json`
    is not judged here: pier itself failed that arm, and its non-zero exit
    code is the signal (FAIL outranks INCOMPLETE).
    """
    incomplete: dict[str, str] = {}
    for result_path in sorted(job_dir.glob("*/result.json")):
        trial_dir = result_path.parent
        reason = collect.find_trial_incompleteness_reason(trial_dir)
        if reason is not None:
            incomplete[trial_dir.name] = reason
    return incomplete


def arm_status_label(exit_code: int, incomplete_trials: dict[str, str]) -> str:
    """The one-line PASS / INCOMPLETE / FAIL verdict printed for an arm.

    Pure so the three-state contract is testable without running pier. See the
    module docstring for the precedence (FAIL, then INCOMPLETE, then PASS) and
    what each state means.

    The INCOMPLETE label carries a per-reason breakdown rather than a list of
    trial ids: an arm can hold ~113 trials, and a reader deciding whether to
    care needs the shape of the problem, not every id. The ids are still
    printed once, in main()'s end-of-run summary.
    """
    if exit_code != 0:
        return f"FAIL (exit {exit_code})"
    if not incomplete_trials:
        return "PASS"

    reason_counts = Counter(incomplete_trials.values())
    breakdown = ", ".join(f"{reason} x{count}" for reason, count in sorted(reason_counts.items()))
    return f"INCOMPLETE ({len(incomplete_trials)} trials -- {breakdown})"


def report_run_summary(
    exit_codes: dict[str, int], incomplete_by_arm: dict[str, dict[str, str]]
) -> int:
    """Print the end-of-run summary; return the exit code main() should exit on.

    `exit_codes` is arm_id -> pier exit code for every arm this invocation
    actually ran; `incomplete_by_arm` is arm_id -> {trial_id: reason} for every
    arm holding unfinished trials, INCLUDING arms that were skipped as already
    complete.

    Both buckets are reported before either decides the exit code, so an
    operator sees everything that went wrong rather than only the worst of it.
    The success line is printed on exactly one condition -- both buckets empty
    -- because the defect this replaced was a summary announcing "all 1 arms
    completed successfully" over a trial that committed nothing.
    """
    failed = {arm_id: code for arm_id, code in exit_codes.items() if code != 0}
    if failed:
        print(f"[run] {len(failed)}/{len(exit_codes)} arms failed: {failed}", file=sys.stderr)
    if incomplete_by_arm:
        # No denominator on this count on purpose: it can include arms this
        # invocation skipped, which are absent from `exit_codes`, so
        # "N/len(exit_codes)" would be a ratio of two different populations.
        print(
            f"[run] {len(incomplete_by_arm)} arm(s) have INCOMPLETE trials "
            f"(no artifacts/model.patch, or a final message that ends in a "
            f"question): {incomplete_by_arm}",
            file=sys.stderr,
        )

    if failed:
        return EXIT_ARM_FAILED
    if incomplete_by_arm:
        return EXIT_TRIALS_INCOMPLETE
    print(f"[run] all {len(exit_codes)} arms completed successfully.")
    return 0


# --------------------------------------------------------------------------
# Preflight: prove the plugin loaded and a sub-agent was actually dispatched
# --------------------------------------------------------------------------

# Leading underscore can never collide with a real arm id (arm ids only ever
# start with a skill name or "vanilla").
PREFLIGHT_JOB_NAME = "_preflight"


def preflight_arm(skill: str, model: str | None = None) -> Arm:
    """The cheapest way to exercise the full plugin-loading + sub-agent-dispatch
    path for `skill`: smallest models on both sides (`CELLS[0]`) -- unless
    `model` is given, in which case that tier's arm is preflighted instead
    (an explicit `--model` overrides the "cheapest by default" behavior, same
    as `--skill` overrides the default skill).

    Delegates to `build_arms` -- the single source of truth for skill/model->
    arm selection -- instead of re-deriving "first cell of this skill" here,
    so a future change to that selection logic (e.g. reordering CELLS, or
    changing how `skill`/`model` pick arms) only has one call site to update.
    `build_arms(include_vanilla=False, skill=skill, model=model)` yields
    exactly one arm when `model` is given (that symmetric tier's cell for
    `skill`), so `[0]` is unambiguous; when `model` is `None` it yields that
    skill's CELLS arms in CELLS order, so `[0]` is this skill's cheapest arm
    -- true today because `CELLS[0]` is the cheapest tier pair ("haiku",
    "haiku"); re-check this comment if that invariant ever changes.
    """
    return build_arms(include_vanilla=False, skill=skill, model=model)[0]


def preflight_job_name(skill: str, model: str | None = None) -> str:
    """Where `run_preflight` writes `prompt.j2`/`arm.json` (and pier its own
    `config.json`/`lock.json`/`result.json`) for `skill`/`model`.

    Two different skills (or two different models of the same skill)
    preflighted back to back must not share a job dir -- pier's own state
    (`config.json`/`lock.json`) and this harness's `prompt.j2` would
    otherwise mix one arm's template with another's pier job state. But the
    *default* skill (`SKILLS[0]`, "do-and-judge") with no `--model` keeps the
    bare `_preflight` name unconditionally: `tests/test_run_dispatch.py` and
    `tests/collect_fixtures.py` pin a recorded transcript at exactly
    `runs/_preflight/abs-stepped-slices__HyQJyYy/agent/claude-code.txt`, and
    every prior `--preflight` invocation (no `--skill`/`--model` flag existed
    before this) wrote there -- moving that path would both break the pinned
    test fixture and orphan the existing recording. Any other skill/model
    combination gets a `-<skill>` and/or `-<model>` suffix instead.
    """
    # `skill == SKILLS[0]` drops the default skill from the suffix so the
    # pinned bare name survives; `model` has no such default to compare
    # against, so it's always included in the suffix when given.
    if skill == SKILLS[0]:
        suffix_parts = [] if model is None else [model]
    else:
        suffix_parts = [skill] if model is None else [skill, model]
    if not suffix_parts:
        return PREFLIGHT_JOB_NAME
    return f"{PREFLIGHT_JOB_NAME}-{'-'.join(suffix_parts)}"


def fail(message: str) -> None:
    """Loud, unambiguous preflight failure -- never pass silently."""
    print(f"[preflight] FAILED: {message}", file=sys.stderr)
    sys.exit(1)


def find_stream_log(job_dir: Path) -> Path | None:
    """Locate the claude-code.txt stream-json transcript pier tees to.

    Verified against pier/agents/installed/claude_code.py: it tees
    `claude --output-format=stream-json ... | tee /logs/agent/claude-code.txt`,
    which mounts from `<trial_dir>/agent/` on the host (`self.logs_dir` is
    constructed as `trial_paths.agent_dir`, per pier/trial/execution.py).
    """
    candidates = sorted(
        job_dir.glob("*/agent/claude-code.txt"), key=lambda p: p.stat().st_mtime
    )
    return candidates[-1] if candidates else None


def iter_stream_events(stream_log: Path):
    """Yield each parseable JSON object from a claude-code.txt transcript."""
    for line in stream_log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def find_init_event(stream_log: Path) -> dict | None:
    """The `{"type": "system", "subtype": "init", ...}` event carrying `plugins`
    and `plugin_errors` -- confirmed against a live `claude` invocation with
    both a working and a broken --plugin-dir (see task handoff notes).
    """
    for event in iter_stream_events(stream_log):
        if event.get("type") == "system" and event.get("subtype") == "init":
            return event
    return None


# Claude Code renamed the sub-agent dispatch tool `Task` -> `Agent` in 2.1.x
# (the container pins 2.1.233). Both names are accepted so transcripts from
# either version are read correctly -- matching only `Task` made a fully
# correct do-and-judge run fail preflight.
SUBAGENT_DISPATCH_TOOLS = {"Agent", "Task"}


def assistant_tool_use_parts(event: dict) -> list[dict]:
    """The `tool_use` content parts of one assistant event; `[]` for anything else.

    Every lookup here is shape-checked rather than assumed. `iter_stream_events`
    yields whatever JSON objects a ~1.2 MB transcript happens to contain, and
    that file is written live -- a run killed mid-write leaves a truncated or
    half-formed event behind. Indexing such an event optimistically raises
    `TypeError`/`AttributeError` out of preflight, replacing the actionable
    failure message `run_preflight` is built to print with a traceback, which
    is the opposite of what a preflight is for.
    """
    if event.get("type") != "assistant":
        return []

    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []

    return [
        part for part in content
        if isinstance(part, dict) and part.get("type") == "tool_use"
    ]


def has_subagent_dispatch(stream_log: Path) -> bool:
    """Whether the orchestrator dispatched a sub-agent anywhere in the run.

    do-and-judge and do-in-steps both work exclusively by dispatching
    sub-agents via the `Agent` tool (`Task` on pre-2.1.x claude-code) -- if
    the transcript never shows one, the skill's instructions were not
    followed (or the skill never loaded), and a preflight that only checked
    `plugin_errors` would miss that entirely.

    A `subagent_type` input is required on top of the tool name because the
    name alone is ambiguous: the unrelated task-tracking tools (`TaskCreate`,
    `TaskUpdate`, ...) live in the same namespace, and only a real dispatch
    names the sub-agent it is launching. That buys immunity to
    `TaskCreate`/`TaskUpdate`-style false positives, and nothing more: the
    name must still be in `SUBAGENT_DISPATCH_TOOLS`, so a *third* rename
    would reproduce the `Task`/`Agent` false negative exactly. Adding the new
    name to that set is the fix if that happens.

    Pinned by `tests/test_run_dispatch.py` against the recorded transcript at
    `runs/_preflight/abs-stepped-slices__HyQJyYy/agent/claude-code.txt`.
    """
    for event in iter_stream_events(stream_log):
        for part in assistant_tool_use_parts(event):
            if part.get("name") not in SUBAGENT_DISPATCH_TOOLS:
                continue
            tool_input = part.get("input")
            if isinstance(tool_input, dict) and "subagent_type" in tool_input:
                return True
    return False


def run_preflight(args: argparse.Namespace) -> int:
    """Run the cheapest arm for `args.skill` (default: `SKILLS[0]`) against one
    task and verify plugin load + dispatch -- or, if `args.model` is given,
    that tier's arm instead of the cheapest one.

    A preflight that passes when the plugin silently failed to load is worse
    than no preflight -- so every failure path below prints to stderr and
    exits non-zero rather than returning a boolean an operator could ignore.

    Returns 0 when the plugin checks pass and the trial finished,
    `EXIT_TRIALS_INCOMPLETE` when they pass but the trial did not finish (the
    plugin verdict and the completion verdict are separate; see the comment at
    the end of this function), and exits 1 via `fail()` on any plugin-check
    failure.
    """
    skill = args.skill or SKILLS[0]
    arm = preflight_arm(skill, args.model)
    job_name = preflight_job_name(skill, args.model)
    job_dir = args.jobs_dir / job_name
    template_path = write_prompt_template(job_dir, arm)
    orchestrator_model_id = ORCHESTRATOR_MODEL_ID[arm.orchestrator]
    # Preflight always resolves one task via "single" mode -- see the
    # build_dataset_args call just below -- so that's the mode recorded here too.
    write_arm_metadata(job_dir, arm, orchestrator_model_id=orchestrator_model_id, mode="single")

    dataset_args = build_dataset_args(
        "single", dataset_dir=args.dataset_dir, task=args.task, n_tasks=None
    )
    cmd = build_pier_command(
        arm,
        pier_bin=args.pier_bin,
        orchestrator_model_id=orchestrator_model_id,
        template_path=template_path,
        job_name=job_name,
        jobs_dir=args.jobs_dir,
        agent_timeout_multiplier=args.agent_timeout_multiplier,
        dataset_args=dataset_args,
    )
    print(f"[preflight] running {arm.id} against task {args.task!r}")
    print(f"[preflight] $ {shlex.join(cmd)}")
    pier_exit_code = run_pier(cmd)

    stream_log = find_stream_log(job_dir)
    if stream_log is None:
        fail("no claude-code.txt stream log was produced -- the agent never started.")

    init_event = find_init_event(stream_log)
    if init_event is None:
        fail(f"no system/init event in {stream_log} -- cannot verify plugin load.")

    plugin_errors = init_event.get("plugin_errors") or []
    if plugin_errors:
        fail(f"plugin failed to load: {plugin_errors}")

    loaded_plugins = {p.get("name") for p in init_event.get("plugins", [])}
    if "sadd" not in loaded_plugins:
        fail(f"'sadd' plugin did not load (loaded plugins: {sorted(loaded_plugins)}).")

    if not has_subagent_dispatch(stream_log):
        fail(
            f"no sub-agent dispatch (tool in {sorted(SUBAGENT_DISPATCH_TOOLS)} with a "
            f"`subagent_type` input) found in {stream_log} -- no sub-agent was ever dispatched."
        )

    # The completion gate applies here too. A preflight trial is a real trial:
    # `runs/_preflight-do-in-steps/cattrs-partial-structuring-recov__9ryVMmH` is
    # the one recorded trial that ends on an abandoning question, and it is a
    # preflight one -- so printing a bare "PASSED" over it is exactly the
    # false-success this harness was fixed to stop doing.
    #
    # It does NOT turn into a preflight failure, though. Preflight asks one
    # question -- did the plugin load and dispatch a sub-agent -- and answers it
    # on the cheapest arm there is (haiku/haiku, one task), which may well
    # abandon or lose the task without saying anything about plugin loading.
    # Conflating the two would make a working plugin fail its own smoke test.
    # So the plugin verdict stays PASSED and is reported as covering exactly
    # that, while the exit code carries the completion state using the same
    # three-state contract main() uses (see this module's docstring).
    incomplete_trials = find_incomplete_trials(job_dir)
    if incomplete_trials:
        print(
            f"[preflight] PASSED (plugin checks only): 'sadd' loaded, sub-agent dispatch "
            f"observed (pier exit code {pier_exit_code}) -- but "
            f"{len(incomplete_trials)} trial(s) did NOT finish the task: {incomplete_trials}. "
            f"The plugin works; the agent did not complete its work.",
            file=sys.stderr,
        )
        return EXIT_TRIALS_INCOMPLETE

    print(
        f"[preflight] PASSED: 'sadd' loaded, sub-agent dispatch observed "
        f"(pier exit code {pier_exit_code})."
    )
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the deep-swe benchmark matrix (skill x model-tier arms) through pier."
    )
    parser.add_argument(
        "--mode",
        choices=["single", "sample", "full"],
        help="Dataset filter to apply to every arm. Required unless --preflight.",
    )
    parser.add_argument(
        "--task",
        help="Task name (resolved under --dataset-dir) or path. Required for "
        "--mode single and for --preflight.",
    )
    parser.add_argument(
        "--n-tasks",
        type=int,
        help="Number of tasks to sample (with the pinned SAMPLE_SEED). Required for --mode sample.",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=SCRIPT_DIR / "data",
        help="Root of the deep-swe task dataset (default: %(default)s).",
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=SCRIPT_DIR / "runs",
        help="Directory pier writes job/trial output under (default: %(default)s).",
    )
    parser.add_argument(
        "--pier-bin",
        default="pier",
        help="pier executable to invoke (default: %(default)s; resolves automatically to "
        "this directory's .venv/bin/pier when run via `uv run`; pass an explicit path "
        "if invoking run.py some other way and pier isn't on PATH).",
    )
    parser.add_argument(
        "--skill",
        choices=SKILLS,
        help="Restrict to one skill's arms (default: all of SKILLS). For --preflight, "
        "preflights that skill's cheapest arm instead of the default "
        f"({SKILLS[0]!r}). For --mode single/sample/full, runs only that skill's "
        "5 CELLS arms (8 with --with-vanilla, which still adds all 3 vanilla "
        "controls) instead of all 10 (13) -- vanilla arms aren't tied to any "
        "skill, so --skill never drops or duplicates them.",
    )
    parser.add_argument(
        "--model",
        choices=MODEL_CHOICES,
        help="Restrict to one symmetric model tier's arm -- same tier orchestrating and "
        f"implementing, e.g. {MODEL_CHOICES[0]!r} means CELLS' ({MODEL_CHOICES[0]!r}, "
        f"{MODEL_CHOICES[0]!r}) cell (default: all of CELLS). For --preflight, preflights "
        "that tier's arm instead of the cheapest one. For --mode single/sample/full, runs "
        "only that tier's 1 CELLS arm per skill in play instead of 5; combine with --skill "
        "to run exactly one arm. Unlike --skill, --model also restricts --with-vanilla to "
        "that one tier's control (1 instead of 3), since vanilla arms are per-model.",
    )
    parser.add_argument(
        "--with-vanilla",
        action="store_true",
        help="Also run the 3 no-plugin vanilla control arms (13 arms total instead of 10; "
        "restricted to 1 with --model).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run arms even if a prior invocation already completed them.",
    )
    parser.add_argument(
        "--agent-timeout-multiplier",
        type=float,
        default=3.0,
        help="Multiplier on pier's agent execution timeout. Judged skills fan out to several "
        "sub-agents per task, so a trial takes far longer than a plain single-agent run; "
        "the default of 1.0 would likely time out mid-judgement (default: %(default)s).",
    )
    # Deliberately NO --max-budget-usd (or any other spend-cap flag): see
    # collect.py's "WHY THERE IS NO 'SPENT MOST OF ITS BUDGET' CONDITION"
    # docstring section and README.md's Cost section. Every trial runs to
    # completion or errors for an unrelated reason; it is never cut off partway
    # through for cost reasons, because a trial killed mid-judgement measures
    # the cap rather than the skill. Do not re-add one.
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pier command for every arm and exit. Writes nothing, runs nothing.",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run one task on the cheapest arm, verify the plugin loaded and a sub-agent was "
        f"dispatched, then exit. Overrides --mode. Defaults to the cheapest arm of "
        f"{SKILLS[0]!r}; pass --skill to preflight a different skill instead.",
    )
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Cross-argument requirements argparse's own `required=` can't express."""
    if args.preflight:
        if not args.task:
            parser.error("--preflight requires --task")
        return
    if not args.mode:
        parser.error("--mode is required unless --preflight is given")
    if args.mode == "single" and not args.task:
        parser.error("--mode single requires --task")
    if args.mode == "sample" and not args.n_tasks:
        parser.error("--mode sample requires --n-tasks")
    # --model needs no cross-argument check here: argparse's `choices=MODEL_CHOICES`
    # (derived from CELLS' symmetric entries, see MODEL_CHOICES's definition) already
    # guarantees any accepted value selects a non-empty arm set, so it composes freely
    # with --skill, --with-vanilla, --preflight, and every --mode in any combination.


def arm_job_dir(jobs_dir: Path, arm: Arm) -> Path:
    """Where pier will write this arm's job output: jobs_dir/<arm-id>."""
    return jobs_dir / arm.id


def run_arm(arm: Arm, args: argparse.Namespace, dataset_args: list[str]) -> tuple[Path, list[str]]:
    """Write one arm's template + metadata and return (job_dir, pier command)."""
    job_dir = arm_job_dir(args.jobs_dir, arm)
    orchestrator_model_id = ORCHESTRATOR_MODEL_ID[arm.orchestrator]
    template_path = write_prompt_template(job_dir, arm)
    write_arm_metadata(job_dir, arm, orchestrator_model_id=orchestrator_model_id, mode=args.mode)
    cmd = build_pier_command(
        arm,
        pier_bin=args.pier_bin,
        orchestrator_model_id=orchestrator_model_id,
        template_path=template_path,
        job_name=arm.id,
        jobs_dir=args.jobs_dir,
        agent_timeout_multiplier=args.agent_timeout_multiplier,
        dataset_args=dataset_args,
    )
    return job_dir, cmd


def preview_arm_command(arm: Arm, args: argparse.Namespace, dataset_args: list[str]) -> list[str]:
    """Build the command --dry-run prints, without writing prompt.j2/arm.json to disk."""
    job_dir = arm_job_dir(args.jobs_dir, arm)
    return build_pier_command(
        arm,
        pier_bin=args.pier_bin,
        orchestrator_model_id=ORCHESTRATOR_MODEL_ID[arm.orchestrator],
        template_path=job_dir / "prompt.j2",
        job_name=arm.id,
        jobs_dir=args.jobs_dir,
        agent_timeout_multiplier=args.agent_timeout_multiplier,
        dataset_args=dataset_args,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    # Normalize to absolute paths up front: run_pier() sets the subprocess's
    # cwd to SCRIPT_DIR (for the agent.py import fix), so any relative path
    # we hand pier must already be absolute or it would resolve against the
    # wrong directory.
    args.dataset_dir = args.dataset_dir.resolve()
    args.jobs_dir = args.jobs_dir.resolve()

    # Fail fast on a broken pier install/PATH instead of discovering it only
    # after per-arm setup work (template/metadata writes) for the first arm.
    # --preflight always shells out to pier regardless of --dry-run (see
    # run_preflight); plain --dry-run never does, so it's the one case this
    # check can skip.
    pier_will_run = args.preflight or not args.dry_run
    if pier_will_run and shutil.which(args.pier_bin) is None:
        parser.error(
            f"pier executable {args.pier_bin!r} not found on PATH -- run this via "
            "`uv run python3 run.py ...` (see README.md), or pass --pier-bin with "
            "an explicit path."
        )

    if args.preflight:
        return run_preflight(args)

    arms = build_arms(include_vanilla=args.with_vanilla, skill=args.skill, model=args.model)
    dataset_args = build_dataset_args(
        args.mode, dataset_dir=args.dataset_dir, task=args.task, n_tasks=args.n_tasks
    )
    skill_label = f", skill={args.skill}" if args.skill else ""
    model_label = f", model={args.model}" if args.model else ""
    print(
        f"[run] {len(arms)} arms ({'with' if args.with_vanilla else 'without'} vanilla), "
        f"mode={args.mode}{skill_label}{model_label}"
    )

    if args.dry_run:
        for arm in arms:
            cmd = preview_arm_command(arm, args, dataset_args)
            print(f"[{arm.id}] {shlex.join(cmd)}")
        print(f"[run] dry-run complete -- {len(arms)} arms, nothing executed.")
        return 0

    exit_codes: dict[str, int] = {}
    incomplete_by_arm: dict[str, dict[str, str]] = {}
    for arm in arms:
        job_dir = arm_job_dir(args.jobs_dir, arm)
        if not args.force and is_arm_complete(job_dir):
            # A skipped arm is still checked: pier finished it, but "finished"
            # is exactly the state that used to hide abandoned trials, and a
            # resumed run must not report success for trials an earlier
            # invocation left incomplete.
            skipped_incomplete = find_incomplete_trials(job_dir)
            if skipped_incomplete:
                incomplete_by_arm[arm.id] = skipped_incomplete
            note = f" -- {len(skipped_incomplete)} INCOMPLETE trials" if skipped_incomplete else ""
            print(f"[{arm.id}] SKIP (already complete; pass --force to re-run){note}")
            continue

        _, cmd = run_arm(arm, args, dataset_args)
        print(f"[{arm.id}] $ {shlex.join(cmd)}")
        exit_code = run_pier(cmd)
        exit_codes[arm.id] = exit_code
        incomplete_trials = find_incomplete_trials(job_dir)
        if incomplete_trials:
            incomplete_by_arm[arm.id] = incomplete_trials
        # Surface the verdict per arm as it happens -- a run spans hours across
        # up to 13 arms, so waiting for the end-of-run summary to learn an
        # early arm failed (or quietly abandoned its tasks) wastes the rest of
        # the run's wall-clock time.
        print(f"[{arm.id}] {arm_status_label(exit_code, incomplete_trials)}")

    return report_run_summary(exit_codes, incomplete_by_arm)


if __name__ == "__main__":
    sys.exit(main())
