---
title: Add evaluation benchmarks
---

## Initial User Prompt

add evaluation benchmarks

### Requirements

- Create benchmarks/deep-swe/ folder
- Add there scripts tha capable to run https://deepswe.datacurve.ai/run benchmark
- It should run benchmark with few specifics:
    - Use claude-code, not mini-swe-bench agent.
    - Claude code should have context-engineering-kit/sdd plugin enabled. - this probbaly require extending pier config https://github.com/datacurve-ai/pier for claude code, TODO: research how to do it.
    - tasks should be run as `/do-and-judge --model <model-for-benchmark> <task-as-regular>` - TODO: research how to do it.
- It should provides scripts to do following:
    - run a single task
    - run sample of tasks
    - run full benchmark
- regardless prompt and model, it should support following cases to benchmark:
    - haiku as orcestrator + implementation/judge haiku
    - sonnet as orcestrator + implemenetation/judge haiku
    - sonnet as orcestrator + implementation/judge sonnet
    - haiku as orcestrator + implementation/judge haiku
    - opus as orcestrator + implementation/judge sonnet
    - opus as orcestrator + implementation/judge opus
- It should save results of benchmark in json/csv format.
- Add script that can generate minimal html report from results. It should include vertical bar chart of model group comparision, in each group model itself, compaired agains skill benchmar where it orccestartor and implementation. Plus separatly, vertical bar chart of model group comparision, in each group model itself, compaired agains skill benchmar where orcestrator and implementaion are different, grouped by orcestrator model. Use vercel style for charts. Include official model benchmarks: https://deepswe.datacurve.ai/
- Add benchmarks/deep-swe/README.md how to run benchmarks.

### Target Approach

Resolved from brainstorming. Supersedes the raw bullets above where they conflict.

#### Resolved Decisions

| Question | Decision |
|---|---|
| Which plugin | `plugins/sadd` — NOT `sdd`. `/do-and-judge` and `/do-in-steps` live in `sadd`, along with the `sadd:judge` and `sadd:meta-judge` agents they dispatch. Matches `.specs/benchmarks-roadmap.md`. |
| Skills under test | Both `/do-and-judge` and `/do-in-steps` (per roadmap). Identical argument surface: `<task> [--model haiku\|sonnet\|opus] [--strict]`. |
| Runtime | Docker only. No Modal, no `--env` flag, no cloud docs. |
| Matrix cells | 5 unique cells (the prompt above lists haiku/haiku twice): haiku/haiku, sonnet/haiku, sonnet/sonnet, opus/sonnet, opus/opus. |
| Arms | skill x cell = 10. `--all` runs all 10. `--with-vanilla` adds 3 no-plugin arms (haiku, sonnet, opus) = 13. |
| Baseline bar | Official DeepSWE leaderboard numbers (vendored snapshot). Vanilla claude-code arm supported but opt-in; report renders it when present. |
| Pier extension | Custom agent subclass via `--agent-import-path`. No fork, no patch. |
| Config style | Generated at run time by a single `run.py`; no committed per-cell YAML. |

#### Pier Research Findings (both TODOs resolved)

- Pier has **no** plugin support (`skills_dir`, `memory_dir`, `mcp_servers` only). `skills_dir` is insufficient: it copies skills but not plugin **agents**, which both skills require.
- `pier run --agent-import-path module:ClassName` is a first-class CLI flag; `--ak key=value` passes agent kwargs. Custom agents need no fork.
- `BaseInstalledAgent` accepts `prompt_template_path` (Jinja2). `render_prompt_template` validates under `StrictUndefined` and passes **only** `instruction` — templates cannot carry other variables.
- Claude Code headless docs: *"User-invoked skills and custom commands work in `-p` mode: include `/skill-name` in the prompt string and Claude Code expands it before running."* Pier already invokes `claude --print -- <instruction>`.
- Claude Code supports `--plugin-dir <path>`; the `system/init` stream event reports `plugins` and `plugin_errors` for verification.
- `TrialResult` provides `task_name`, `verifier_result`, `compute_token_cost_totals()` (input/cache/output tokens, cost USD), `agent_step_count()`, timings.
- Official leaderboard (21 models, snapshot 2026-08-07) has **no JSON/CSV export or API** and is produced with **mini-swe-agent, not claude-code**.

#### Structure

```
benchmarks/deep-swe/
  agent.py          # ClaudeCodeSadd(ClaudeCode) — the only pier extension
  run.py            # matrix table + entrypoint (preflight / single / sample / full)
  collect.py        # runs/ → results.json + results.csv
  report.py         # results.json → report.html
  data/
    leaderboard.json # vendored official scores + snapshot date + source URL
  README.md
```

#### agent.py

Subclasses pier's `ClaudeCode`, changing exactly three things:

1. Appends `CliFlag("plugin_dir", cli="--plugin-dir", type="str")` to `CLI_FLAGS`; pier renders it into the `claude --print` invocation.
2. Extends `install_spec()` with a step cloning `context-engineering-kit` at a **pinned ref** into the container.
3. Overrides `network_allowlist()` to add `github.com`, so the clone survives tasks declaring `allow_internet = false`.

#### run.py

- Matrix as a table at module top: `CELLS`, `SKILLS`, `VANILLA_MODELS`. An arm is `(skill, orchestrator, impl)`.
- Model mapping: `agent.model_name` → `ANTHROPIC_MODEL` = **orchestrator**; `--model <tier>` inside the slash command = **implementation/judge sub-agents**.
- Writes a one-line prompt template per arm into `runs/<arm-id>/prompt.j2` (e.g. `/do-in-steps --model sonnet {{ instruction }}`), archived with results; passes `--ak prompt_template_path=...`.
- Shells out to `pier run --agent-import-path agent:ClaudeCodeSadd -m ... --ak plugin_dir=... --job-name <arm-id> --jobs-dir runs/`, streaming pier output through.
- Single / sample / full differ only in dataset filter (`-p <task>` vs `-l N --sample-seed S`). **Seed pinned and identical across arms** so every arm sees the same subset.
- Resumable: arms are separate pier jobs; skips arms with a complete set of `result.json` unless `--force`.
- `--dry-run` prints pier commands and arm count without executing.
- `--preflight` runs one task on the cheapest arm, failing loudly unless the plugin loaded AND sub-agents were dispatched.
- Sets `--max-budget-usd` per trial and an agent-timeout multiplier above 1 (judged skills fan out and are slower per task).

#### collect.py

Walks `runs/*/<trial>/result.json` → `results.json` (per-trial, full fidelity) + `results.csv` (flat).

Fields: `arm_id`, `skill`, `orchestrator`, `impl`, `task_name`, `task_checksum`, `resolved`, `reward`, `cost_usd`, `output_tokens`, `input_tokens`, `cache_tokens`, `n_agent_steps`, `duration_sec`, `status`, `plugin_ref`, `claude_code_version`.

- `status` is `resolved` / `unresolved` / `errored`. Infra failures (build failure, API 529, plugin-not-loaded) MUST be `errored` and MUST NOT count as task failures.
- Asserts via the `system/init` event in `claude-code.txt` that the plugin loaded for every non-vanilla trial.
- Per-arm aggregation mirrors the leaderboard columns: Pass@1, avg cost, output tokens, steps — plus **Wilson 95% CI**.
- Re-runnable and merges everything under `runs/`.

#### report.py

Self-contained `report.html` via Python stdlib + inline SVG. No CDN, no JS dependencies.

- **Chart 1 (matched arms):** groups = model (haiku, sonnet, opus); bars = official, `do-and-judge`, `do-in-steps`, vanilla (when present).
- **Chart 2 (mixed arms):** groups = orchestrator (sonnet, opus); bars = that orchestrator's official number + each skill's mixed-tier result.
- Wilson CI whiskers on both charts.
- Official bars rendered **outlined, not filled**, with a footnote stating they were produced with mini-swe-agent rather than claude-code, plus leaderboard snapshot date and source URL.
- Arm table (Pass@1 ± CI, avg cost, output tokens, steps, errored count) and run-metadata header (date, task count, seed, pinned CEK commit, Claude Code version).
- Vercel/Geist styling: near-monochrome, one accent, hairline grid, system sans, light + dark. Chart work follows the `dataviz` skill.

#### README.md

Prerequisites (Docker, `uv tool install git+https://github.com/datacurve-ai/pier`, clone `datacurve-ai/deep-swe` tasks, `ANTHROPIC_API_KEY`), then commands in order: preflight → single → sample → full → collect → report. Includes a blunt cost and wall-clock table (full run is 1130 trials, 1469 with vanilla).

#### Tests

Unit tests for pure functions in `collect.py` and `report.py`: Wilson interval, per-arm aggregation, error classification. The harness itself is verified by `--dry-run` and `--preflight`.

## Description

// Will be filled in future stages by business analyst
