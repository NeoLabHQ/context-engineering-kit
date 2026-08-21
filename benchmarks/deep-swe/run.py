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

    runs/scheduler-state.json          <- `--mode scheduled`'s resume record ONLY; not
                                           pier's, not per-arm. One entry per planned
                                           run of schedule.yaml -- see scheduler.py's
                                           module docstring for the schema.
    runs/<arm-id>/                     <- pier's --jobs-dir/--job-name, i.e. its job_dir
                                           (--mode single suffixes this with
                                           "__<task-slug>" -- see arm_job_dir --
                                           so two different tasks for the same
                                           skill+model never share a job_dir;
                                           --mode sample/full run their whole
                                           dataset filter as one job and keep
                                           the bare <arm-id> name; --mode
                                           scheduled runs one task per arm and
                                           so shares --mode single's naming
                                           exactly -- see single_task_args)
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

`--mode scheduled` reports on the same three-state contract, but per planned
run rather than per arm, and adds one distinction the other modes have no need
for: whether a failure was the model's. A trial the agent attempted and lost
is the benchmark's product and is recorded once; a trial that never got a fair
attempt (dead container, quota denial, API 529) is backed off and retried, at
most `scheduler.MAX_TECHNICAL_RETRIES` times. `triage.py` draws that line and
explains at length what evidence it is drawn from; `scheduler.py` owns the
pacing, the retry bound and the resume record. Neither knows what pier is --
this file supplies every side effect they drive, which is what lets both be
tested without a container or a two-hour wait.

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

# The `--mode scheduled` stack. All three import only stdlib + collect/yaml,
# so they stay importable (and testable) without `pier` -- the same property
# collect.py has, and the reason the scheduling policy lives there rather
# than in this file. See scheduler.py's module docstring.
import schedule  # noqa: E402
import scheduler  # noqa: E402
import triage  # noqa: E402

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

# Env vars pier forwards into the `claude --print` process (its `--ae` flag).
#
# CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 -- "wait indefinitely" -- is load
# bearing, not a tuning knob. In `--print` mode Claude Code keeps the session
# alive past a final assistant message only while background tasks might still
# notify it, and it gives up after a 600s default ceiling: it then kills every
# live sub-agent and exits 0, which pier reads as a clean finish. Every skill
# this harness benchmarks orchestrates by dispatching background sub-agents and
# yielding, so *every* dispatch is a race against that ceiling. Observed in the
# do-in-steps__sonnet-sonnet / cattrs-partial-structuring-recovery run: 22 such
# waits, two of which cleared 600s by 15s and 27s, and the 22nd (a step whose
# sub-agent had launched a background full-suite pytest of its own, so it never
# notified the parent) did not -- the run was terminated mid-step at 602s with
# ~2h of uncommitted work in the container and scored 0.
#
# Zero disables the ceiling only; pier's own --agent-timeout-multiplier remains
# the actual bound on a stalled trial, which is where that bound belongs.
AGENT_ENV: dict[str, str] = {
    "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
}


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

    Written as `<job_dir>/arm.json`, a sibling of pier's own config.json/
    result.json in the same job directory (see `arm_job_dir` for what
    `job_dir` is named for a given mode).

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


def task_slug(dataset_dir: Path, task: str) -> str:
    """Filesystem-safe id for one `--mode single` task: its resolved task
    directory's own basename.

    Going through `resolve_task_path` rather than using `task` verbatim means
    a bare name ("foo") and an equivalent path ("tasks/foo") resolve to the
    same on-disk task directory and therefore produce the same slug -- see
    `arm_job_dir`, which keys a job dir on this so two different tasks for
    the same skill+model never collide.
    """
    return resolve_task_path(dataset_dir, task).name


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
    transcript): --agent-import-path, -m, --ak, --ae, --agent-timeout-multiplier,
    --job-name, --jobs-dir, -p, -l, --sample-seed all exist with this exact
    spelling.

    `--ae` is emitted for every arm, vanilla included: AGENT_ENV guards against
    a Claude Code runtime behaviour (see its comment), not against anything the
    sadd plugin does, so a vanilla control needs it just as much.
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
    for key, value in AGENT_ENV.items():
        cmd += ["--ae", f"{key}={value}"]
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


def recorded_single_task_name(job_dir: Path) -> str | None:
    """The one task pier's own `config.json` ran in `job_dir`, or `None`.

    `None` covers every case where that answer isn't a single unambiguous
    task name: no `config.json`, an unreadable one, or a job whose `tasks`
    list doesn't have exactly one entry (as `--mode sample`/`--mode full`
    jobs never do -- those run many tasks per job, on purpose). Only
    `resolve_completed_job_dir`'s pre-fix-compatibility check needs this,
    since a `--mode single` job always plans exactly one task.
    """
    config_path = job_dir / "config.json"
    try:
        config = json.loads(config_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    tasks = config.get("tasks") or []
    if len(tasks) != 1:
        return None
    task_path = tasks[0].get("path")
    return Path(task_path).name if task_path else None


def resolve_completed_job_dir(
    job_dir: Path, *, mode: str, jobs_dir: Path, arm: Arm, task: str | None, dataset_dir: Path
) -> Path | None:
    """The job dir whose on-disk state already covers `job_dir`'s task, or
    `None` when nothing does (this task must run).

    Usually `job_dir` itself, once its own `result.json` says finished. For
    `--mode sample`/`--mode full` that is the whole answer: one pier job
    covers the entire dataset filter, so there is nowhere else to look.

    For `--mode single`, `job_dir` is keyed by task (see `arm_job_dir`), so a
    task that has never run under that naming has nothing to check there yet
    -- but a run recorded before task-aware naming existed (the pre-fix flat
    `jobs_dir/<arm-id>` directory, still on disk for every arm this harness
    ran before this fix) must still count as complete for the one task it
    actually ran, or the very next invocation would silently re-run it.
    `recorded_single_task_name` confirms that directory's own `config.json`
    ran THIS task before trusting its `finished_at` -- without that check,
    the exact bug this function exists to close (one arm-id's completion
    state leaking across every task ever single-run under it) would just
    move one call frame deeper. Returning the legacy dir (not just `True`)
    lets the caller run `find_incomplete_trials` against wherever the
    trials actually live, rather than the (possibly empty) new job_dir.
    """
    if is_arm_complete(job_dir):
        return job_dir
    if mode != "single":
        return None

    assert task is not None  # enforced by validate_args for --mode single
    legacy_job_dir = jobs_dir / arm.id
    legacy_ran_this_task = recorded_single_task_name(legacy_job_dir) == task_slug(dataset_dir, task)
    if legacy_ran_this_task and is_arm_complete(legacy_job_dir):
        return legacy_job_dir
    return None


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
        choices=["single", "sample", "full", "scheduled"],
        help="Dataset filter to apply to every arm. Required unless --preflight. "
        "'scheduled' is the odd one out: instead of applying one filter across the "
        "arm matrix, it walks the (task, model, skill) plan in --schedule, running "
        "each cell as its own single-task job, pacing between them and retrying "
        "technical failures. See --schedule.",
    )
    parser.add_argument(
        "--schedule",
        type=Path,
        default=schedule.DEFAULT_SCHEDULE_PATH,
        help="Schedule file --mode scheduled executes (default: %(default)s). It "
        "declares the tasks, model pairs, skills, pacing and deliberate skips; "
        "nothing else re-derives them.",
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


# `--mode scheduled` takes its whole matrix from the schedule file, so the
# flags that filter or extend the matrix for the other modes have nothing left
# to mean. Each is REJECTED rather than ignored: a flag that silently does
# nothing is how an operator ends up believing they ran a subset when they ran
# everything (or the reverse), and this mode's runs cost hours each.
#
# Rejecting is also the honest choice over inventing a filtering semantic.
# schedule.yaml already has one -- `skips`, with a mandatory reason attached --
# and a second, undocumented one reachable only from the command line would
# make the file stop being the answer to "why did this cell not run".
_SCHEDULED_INCOMPATIBLE_FLAGS: tuple[tuple[str, str], ...] = (
    ("task", "--task"),
    ("n_tasks", "--n-tasks"),
    ("skill", "--skill"),
    ("model", "--model"),
    ("with_vanilla", "--with-vanilla"),
)


def _reject_matrix_flags_under_scheduled(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    """Refuse the matrix flags that `--mode scheduled` cannot honour."""
    offenders = [flag for attribute, flag in _SCHEDULED_INCOMPATIBLE_FLAGS if getattr(args, attribute)]
    if not offenders:
        return
    parser.error(
        f"--mode scheduled takes its tasks, models and skills from {args.schedule}, so "
        f"{', '.join(offenders)} cannot apply. To run a subset, edit that file's `skips` "
        f"(the reason is recorded and shown in the report) or point --schedule at another file."
    )


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
    if args.mode == "scheduled":
        _reject_matrix_flags_under_scheduled(parser, args)
    # --model needs no cross-argument check here: argparse's `choices=MODEL_CHOICES`
    # (derived from CELLS' symmetric entries, see MODEL_CHOICES's definition) already
    # guarantees any accepted value selects a non-empty arm set, so it composes freely
    # with --skill, --with-vanilla, --preflight, and every --mode in any combination.


def arm_job_dir(
    jobs_dir: Path, arm: Arm, *, mode: str, task: str | None = None, dataset_dir: Path | None = None
) -> Path:
    """Where pier will write this arm's job output.

    `--mode sample`/`--mode full` run their whole dataset filter as one pier
    job, so `jobs_dir/<arm-id>` names it uniquely on its own -- unchanged from
    before this function took `mode`/`task`/`dataset_dir`.

    `--mode single` runs exactly one task per invocation, but a later
    invocation of the same skill+model against a DIFFERENT task is exactly as
    likely as a genuine re-run of the same one. Suffixing with `task_slug`
    gives each task its own job dir, so pier never sees two different task
    sets show up under one job (which it treats as an unresumable config
    conflict -- see pier's `Job._maybe_init_existing_job`) and
    `resolve_completed_job_dir` never mistakes "this arm finished task A"
    for "this arm finished task B".
    """
    if mode != "single":
        return jobs_dir / arm.id
    assert task is not None and dataset_dir is not None  # enforced by validate_args
    return jobs_dir / f"{arm.id}__{task_slug(dataset_dir, task)}"


def run_arm(arm: Arm, args: argparse.Namespace, dataset_args: list[str]) -> tuple[Path, list[str]]:
    """Write one arm's template + metadata and return (job_dir, pier command)."""
    job_dir = arm_job_dir(
        args.jobs_dir, arm, mode=args.mode, task=args.task, dataset_dir=args.dataset_dir
    )
    orchestrator_model_id = ORCHESTRATOR_MODEL_ID[arm.orchestrator]
    template_path = write_prompt_template(job_dir, arm)
    write_arm_metadata(job_dir, arm, orchestrator_model_id=orchestrator_model_id, mode=args.mode)
    cmd = build_pier_command(
        arm,
        pier_bin=args.pier_bin,
        orchestrator_model_id=orchestrator_model_id,
        template_path=template_path,
        # job_dir.name, not arm.id: for --mode single this carries the
        # task-slug suffix `arm_job_dir` added, and pier's --job-name must
        # agree with the job_dir we just wrote prompt.j2/arm.json into.
        job_name=job_dir.name,
        jobs_dir=args.jobs_dir,
        agent_timeout_multiplier=args.agent_timeout_multiplier,
        dataset_args=dataset_args,
    )
    return job_dir, cmd


def preview_arm_command(arm: Arm, args: argparse.Namespace, dataset_args: list[str]) -> list[str]:
    """Build the command --dry-run prints, without writing prompt.j2/arm.json to disk."""
    job_dir = arm_job_dir(
        args.jobs_dir, arm, mode=args.mode, task=args.task, dataset_dir=args.dataset_dir
    )
    return build_pier_command(
        arm,
        pier_bin=args.pier_bin,
        orchestrator_model_id=ORCHESTRATOR_MODEL_ID[arm.orchestrator],
        template_path=job_dir / "prompt.j2",
        job_name=job_dir.name,
        jobs_dir=args.jobs_dir,
        agent_timeout_multiplier=args.agent_timeout_multiplier,
        dataset_args=dataset_args,
    )


# --------------------------------------------------------------------------
# --mode scheduled: bind scheduler.py's policy to this file's mechanisms
#
# Everything below is the side-effecting half. `scheduler.py` decides WHEN a
# run happens, whether it is retried and what is written down; these functions
# are WHAT it does when it decides to. Keeping the split at this boundary is
# what lets the loop be tested without pier, a container or a two-hour wait.
# --------------------------------------------------------------------------

COLLECT_SCRIPT = SCRIPT_DIR / "collect.py"
REPORT_SCRIPT = SCRIPT_DIR / "report.py"


def single_task_args(args: argparse.Namespace, task_name: str) -> argparse.Namespace:
    """`args` restated as the equivalent `--mode single --task <task_name>` run.

    A scheduled run IS a single-task run of one arm: same pier invocation,
    same `<arm-id>__<task-slug>` job directory, same `arm.json`. Handing the
    existing single-mode helpers a Namespace that says exactly that keeps the
    claim literally true rather than approximately true -- `run_arm`,
    `arm_job_dir` and `resolve_completed_job_dir` are then used unchanged, so
    a scheduled run and a hand-typed `--mode single` of the same cell land in
    the same directory and resume one another.

    Copied rather than mutated: `args` is walked once per planned run, and a
    loop that left `args.task` pointing at whichever task it happened to touch
    last would be a resumability bug waiting to happen.
    """
    single = argparse.Namespace(**vars(args))
    single.mode = "single"
    single.task = task_name
    return single


def arm_for_planned_run(planned: schedule.PlannedRun) -> Arm:
    """The `Arm` one planned run corresponds to.

    Performs schedule.yaml's `vanilla` -> `Arm(skill=None, impl=None)`
    translation (see schedule.py's module docstring for why the file and the
    code spell the control arm differently). `schedule.arm_id_for` already
    mirrors `Arm.id` for the same pair and
    `tests/test_schedule.py::ArmIdResolutionTests` pins the two together, so
    this builds the arm rather than parsing an id back into one.
    """
    if planned.is_vanilla:
        return Arm(skill=None, orchestrator=planned.model.orchestrator, impl=None)
    return Arm(
        skill=planned.skill, orchestrator=planned.model.orchestrator, impl=planned.model.impl
    )


def scheduled_job_dir(args: argparse.Namespace, planned: schedule.PlannedRun) -> Path:
    """Where this planned run's pier job lives -- `--mode single`'s naming."""
    return arm_job_dir(
        args.jobs_dir,
        arm_for_planned_run(planned),
        mode="single",
        task=planned.task.name,
        dataset_dir=args.dataset_dir,
    )


def execute_planned_run(
    planned: schedule.PlannedRun, args: argparse.Namespace
) -> scheduler.RunAttempt:
    """Run one planned cell through pier, then triage what it left on disk.

    The pier exit code is printed but deliberately NOT fed into the triage.
    Every way pier can fail already reaches `triage.py` through an artifact:
    a job that died before producing a trial leaves no `result.json`
    (-> `no_trial_result`), and one that died during a trial leaves
    `exception_info` set. Adding the exit code as a fourth signal would mean
    inventing a rule for a combination -- pier non-zero over a clean, scored,
    resolved trial -- that nothing in `runs/` demonstrates, which is exactly
    the speculative generality this harness has been cutting back.
    """
    single = single_task_args(args, planned.task.name)
    arm = arm_for_planned_run(planned)
    dataset_args = build_dataset_args(
        "single", dataset_dir=single.dataset_dir, task=single.task, n_tasks=None
    )
    job_dir, cmd = run_arm(arm, single, dataset_args)

    print(f"[{arm.id}] $ {shlex.join(cmd)}")
    exit_code = run_pier(cmd)
    print(f"[{arm.id}] pier exited {exit_code}")

    return scheduler.RunAttempt(
        verdict=triage.triage_job_dir(job_dir),
        incomplete_trials=find_incomplete_trials(job_dir),
    )


def find_completed_planned_run(
    planned: schedule.PlannedRun, args: argparse.Namespace
) -> scheduler.RunAttempt | None:
    """An already-finished attempt for this cell, or `None` if it must run.

    Reuses `resolve_completed_job_dir` verbatim, so a scheduled run inherits
    both of its behaviours for free: it recognises its own completed job dirs,
    and it recognises the pre-task-naming flat `runs/<arm-id>` directories
    left by earlier invocations of this harness. Those are re-triaged from
    their artifacts rather than assumed successful -- a finished job is not
    the same as a solved task, which is the confusion the completion gate was
    added to end.
    """
    arm = arm_for_planned_run(planned)
    completed = resolve_completed_job_dir(
        scheduled_job_dir(args, planned),
        mode="single",
        jobs_dir=args.jobs_dir,
        arm=arm,
        task=planned.task.name,
        dataset_dir=args.dataset_dir,
    )
    if completed is None:
        return None
    return scheduler.RunAttempt(
        verdict=triage.triage_job_dir(completed),
        incomplete_trials=find_incomplete_trials(completed),
    )


def describe_completed(planned: schedule.PlannedRun, args: argparse.Namespace) -> str | None:
    """How an already-finished cell would be reported, or `None` if it must run.

    `--dry-run`'s read-only view of `find_completed_planned_run`. Reading the
    artifacts is still writing nothing and running nothing, which is what
    `--dry-run` promises; showing a stale count instead would make the preview
    the one place that disagrees with what the run will do.

    Mirrors `scheduler._resume`'s rule that a technical verdict does NOT count
    as done, for exactly that reason -- a preview that promised to skip a cell
    the run will actually execute would misstate the schedule's length in the
    one direction an operator cannot afford.
    """
    completed = find_completed_planned_run(planned, args)
    if completed is None or completed.verdict.is_technical:
        return None
    return f"{completed.verdict} (job dir already complete)"


def run_collect_and_report(jobs_dir: Path, out_dir: Path = SCRIPT_DIR) -> str | None:
    """Re-derive results.json/results.csv and report.html; describe any failure.

    Returns `None` on success and a one-line description otherwise -- it never
    raises, because `scheduler.py` calls this after every single run and a
    reporting failure must not be able to end a multi-day benchmark. The
    artifacts both scripts read stay on disk regardless, so a run whose report
    step failed can always be re-derived afterwards by invoking them by hand.

    Shells out with `sys.executable` rather than importing and calling
    `collect.main()`/`report.main()` in-process for the reason `run_pier`
    already shells out: a crash, a leaked file handle or a `sys.exit` inside
    either script is then that subprocess's problem and not the scheduler's.
    Output is left uncaptured, same as `run_pier`, so an operator watching a
    multi-day run sees each step happen.

    `out_dir` defaults to this directory -- the location both scripts default
    to on their own, and where README.md tells operators to look for
    `results.json`/`report.html`. It is a parameter only so the test suite can
    exercise this wiring for real against a scratch directory instead of
    overwriting the committed artifacts; nothing in production passes it.
    Every path is made explicit on both command lines rather than relying on
    those defaults, so the two steps cannot end up pointing at different
    directories.
    """
    steps = (
        ("collect.py", [sys.executable, str(COLLECT_SCRIPT),
                        "--runs-dir", str(jobs_dir), "--out-dir", str(out_dir)]),
        ("report.py", [sys.executable, str(REPORT_SCRIPT),
                       "--results", str(out_dir / "results.json"),
                       "--out", str(out_dir / "report.html")]),
    )
    for name, cmd in steps:
        try:
            exit_code = subprocess.run(cmd, cwd=SCRIPT_DIR).returncode
        except OSError as error:
            return f"{name} could not be started: {error}"
        if exit_code != 0:
            return f"{name} exited {exit_code}"
    return None


def build_schedule_harness(args: argparse.Namespace) -> scheduler.Harness:
    """Bind the scheduler's abstract side effects to this file's real ones.

    `sleep`/`monotonic` are left at their defaults (the real ones) -- only the
    test suite ever substitutes those.
    """
    return scheduler.Harness(
        execute=lambda planned: execute_planned_run(planned, args),
        find_completed=lambda planned: find_completed_planned_run(planned, args),
        collect_and_report=lambda: run_collect_and_report(args.jobs_dir),
    )


def stuck_technical_reports(outcome: scheduler.ScheduleOutcome) -> list[scheduler.RunReport]:
    """Technical failures whose job directory already holds a finished trial
    -- the ones no future `--mode scheduled` invocation will clear on its own.

    `triage.NO_TRIAL_RESULT_REASON` is the one technical reason where pier
    never wrote a trial `result.json` at all (the container/environment never
    came up); with nothing on disk yet, the NEXT `pier run` for that cell
    genuinely attempts it. Every OTHER technical reason -- an API fault, a
    missing verifier reward, an ambiguous nonzero exit -- means a trial DID
    finish and write a `result.json`, and that is exactly what pier's own
    per-trial resume (`Job._maybe_init_existing_job`) treats as already done:
    it skips re-running that trial regardless of how many more times
    `scheduler.py` retries or how many later invocations run. So these cells
    keep re-triaging the same stale verdict forever unless their job
    directory is removed by hand first -- see `report_scheduled_summary`.
    """
    return [
        report
        for report in outcome.reports
        if report.verdict is not None
        and report.verdict.outcome == triage.TECHNICAL_FAILURE
        and report.verdict.reason != triage.NO_TRIAL_RESULT_REASON
    ]


def report_scheduled_summary(
    outcome: scheduler.ScheduleOutcome, args: argparse.Namespace | None = None
) -> int:
    """Print `--mode scheduled`'s end-of-run summary; return main()'s exit code.

    Extends `report_run_summary`'s conventions rather than inventing a second
    scheme: every bucket is printed before any of them decides the exit code,
    so an operator sees everything that went wrong instead of only the worst
    of it, and the success line prints on exactly one condition -- nothing in
    any failure bucket.

    The exit codes are the existing two, mapped by what they already mean:

      EXIT_ARM_FAILED (1)         a run the harness could not obtain a fair
                                  attempt for (technical failure, retries
                                  spent), or a collect/report step that
                                  failed. Both are "this invocation did not
                                  do its job", which is what 1 means for the
                                  other three modes.
      EXIT_TRIALS_INCOMPLETE (3)  every run was attempted, but at least one
                                  agent abandoned its task (no model.patch,
                                  or a final message that ends in a
                                  question) -- identical to the other modes.
      0                           everything ran. Note that a MODEL failure
                                  alone is a 0: an agent that attempted a
                                  task and scored it wrong is a successful
                                  benchmark measurement, exactly as an
                                  unresolved `--mode single` trial is today.

    No new exit code is introduced. "The model lost" is a result, not a
    harness error, and giving it a code of its own would break every caller
    that reads non-zero as "something needs fixing".

    `args` names the run's `--jobs-dir`/`--dataset-dir`, so a STUCK cell (see
    `stuck_technical_reports`) can be reported with its exact job directory
    and the exact recipe that clears it. Optional and defaulting to `None`
    only so callers that never had an `args.Namespace` to hand -- the test
    suite's synthetic outcomes -- still get a summary; production always
    passes it (see `run_scheduled`).
    """
    skipped = outcome.with_disposition(scheduler.SKIPPED)
    resumed = outcome.with_disposition(scheduler.RESUMED)
    executed = outcome.with_disposition(scheduler.RAN)
    technical = [report for report in outcome.reports if report.verdict is not None
                 and report.verdict.outcome == triage.TECHNICAL_FAILURE]
    stuck = stuck_technical_reports(outcome)
    model_failed = outcome.with_outcome(triage.MODEL_FAILURE)
    succeeded = outcome.with_outcome(triage.SUCCESS)

    print(
        f"[schedule] {len(executed)} run(s) executed, {len(resumed)} already done, "
        f"{len(skipped)} deliberately skipped; {len(succeeded)} resolved, "
        f"{len(model_failed)} model failures, {len(technical)} technical failures. "
        f"Waited {sum(outcome.waits_requested):.0f}s across {len(outcome.waits_requested)} "
        f"pause(s); elapsed {outcome.elapsed_seconds:.0f}s."
    )
    for report in skipped:
        print(f"[schedule] SKIPPED {report.label}: {report.planned.skip_reason}")
    for report in model_failed:
        print(f"[schedule] MODEL FAILURE {report.label}: {report.verdict.reason} (not retried)")
    for report in technical:
        print(
            f"[schedule] TECHNICAL FAILURE {report.label}: {report.verdict.reason} "
            f"after {report.attempts} attempt(s)",
            file=sys.stderr,
        )
    for report in stuck:
        job_dir = str(scheduled_job_dir(args, report.planned)) if args is not None else "<job-dir>"
        print(
            f"[schedule] STUCK {report.label}: {report.verdict.reason} -- pier will keep "
            f"skipping this trial's existing result.json on every future invocation, so "
            f"retries alone will not clear it. `--force` alone will not either: it only "
            f"skips run.py's own already-done check, and pier's per-trial resume still "
            f"skips the trial underneath it. Remove the job directory first, then re-run "
            f"WITHOUT --force (every other cell is still terminal and settles instantly "
            f"from the state file; --force would instead replay all of them through pier "
            f"and re-pay the pacing wait between each one):\n"
            f"    rm -rf {job_dir} && uv run python3 run.py --mode scheduled",
            file=sys.stderr,
        )
    for failure in outcome.collect_failures:
        print(f"[schedule] COLLECT/REPORT FAILURE: {failure}", file=sys.stderr)

    incomplete_by_arm = outcome.incomplete_by_arm
    if incomplete_by_arm:
        print(
            f"[schedule] {len(incomplete_by_arm)} arm(s) have INCOMPLETE trials "
            f"(no artifacts/model.patch, or a final message that ends in a "
            f"question): {incomplete_by_arm}",
            file=sys.stderr,
        )

    if technical or outcome.collect_failures:
        return EXIT_ARM_FAILED
    if incomplete_by_arm:
        return EXIT_TRIALS_INCOMPLETE
    print(f"[schedule] all {len(outcome.reports)} planned run(s) accounted for.")
    return 0


def run_scheduled(args: argparse.Namespace) -> int:
    """`--mode scheduled`: walk `--schedule`'s plan, pacing and triaging as it goes.

    The schedule file is read exactly once, here, and its pacing travels with
    the plan it came from -- a second read could pick up a mid-run edit and
    pace the back half of a sweep differently from the front half.
    """
    declared = schedule.load_schedule(args.schedule)
    plan = schedule.expand_schedule(declared)
    state_path = scheduler.state_path_for(args.jobs_dir)
    runnable = sum(1 for planned in plan if not planned.skipped)
    print(
        f"[schedule] {args.schedule}: {len(plan)} planned run(s), {runnable} runnable, "
        f"{len(plan) - runnable} skipped by rule"
    )

    if args.dry_run:
        for line in scheduler.preview_schedule(
            plan,
            between_runs_seconds=declared.between_runs_seconds,
            backoff_seconds=declared.technical_failure_backoff_seconds,
            state=None if args.force else scheduler.load_state(state_path),
            already_done=None if args.force else lambda planned: describe_completed(planned, args),
        ):
            print(line)
        print("[schedule] dry-run complete -- nothing executed, nothing written.")
        return 0

    outcome = scheduler.run_schedule(
        plan,
        harness=build_schedule_harness(args),
        between_runs_seconds=declared.between_runs_seconds,
        backoff_seconds=declared.technical_failure_backoff_seconds,
        state_path=state_path,
        force=args.force,
    )
    return report_scheduled_summary(outcome, args)


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

    # Dispatched before the arm matrix is built: `--mode scheduled` has no
    # matrix of its own -- it derives one arm per planned run from the
    # schedule file instead (see run_scheduled).
    if args.mode == "scheduled":
        return run_scheduled(args)

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
        job_dir = arm_job_dir(
            args.jobs_dir, arm, mode=args.mode, task=args.task, dataset_dir=args.dataset_dir
        )
        completed_job_dir = (
            None
            if args.force
            else resolve_completed_job_dir(
                job_dir,
                mode=args.mode,
                jobs_dir=args.jobs_dir,
                arm=arm,
                task=args.task,
                dataset_dir=args.dataset_dir,
            )
        )
        if completed_job_dir is not None:
            # A skipped arm is still checked: pier finished it, but "finished"
            # is exactly the state that used to hide abandoned trials, and a
            # resumed run must not report success for trials an earlier
            # invocation left incomplete. Checked against completed_job_dir,
            # not job_dir -- for a --mode single task recognized only through
            # the pre-fix flat directory (see resolve_completed_job_dir),
            # that is where the trials actually live.
            skipped_incomplete = find_incomplete_trials(completed_job_dir)
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
