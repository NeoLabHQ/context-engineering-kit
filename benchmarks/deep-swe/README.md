# Deep-SWE benchmark harness

Runs the [DeepSWE](https://deepswe.datacurve.ai/) coding-agent benchmark (113 real-world software-engineering tasks) against `claude-code` running the `sadd` plugin's judged skills (`do-and-judge`, `do-in-steps`), across a 5×2 model-tier matrix, via [pier](https://github.com/datacurve-ai/pier). Produces `results.json`/`results.csv` and a self-contained `report.html` comparing this harness's own arms against DeepSWE's official leaderboard.

**Read [Cost and time](#cost-and-time--read-this-before---mode-full) before running `--mode full`.** A full run is roughly 1,130–1,469 trials of a judged skill that fans out to sub-agents — meaningfully more expensive per task than a plain single-agent benchmark run.

## Prerequisites

1. **Docker** (or a compatible container runtime) running locally — pier provisions a fresh container per trial.

2. **A Python environment where the `pier` package is importable**, not just a shell with the `pier` binary on `PATH`:

   ```bash
   uv tool install git+https://github.com/datacurve-ai/pier
   ```

   This puts the `pier` CLI on `PATH` (used as `--pier-bin`'s default). It does **not** by itself make `run.py` work: `run.py` imports the `pier` package directly at module load (via `agent.py`, which subclasses pier's own `ClaudeCode`), so a bare `python3 run.py` fails immediately —

   ```
   ModuleNotFoundError: No module named 'pier'
   ```

   (verified against this checkout). Run `run.py` itself through an environment that has `pier` installed as a library, e.g.:

   ```bash
   uv run --with pier python3 run.py --preflight --task <task-name>
   ```

   `run.py` also fails fast with a clear message if the `pier` *binary* isn't resolvable via `--pier-bin` (default `pier`) — pass an explicit path (`--pier-bin /path/to/pier`) if it isn't on `PATH` inside whatever environment you use.

   This harness's flags (`--agent-import-path`, `-m`, `--ak`, `--agent-timeout-multiplier`, `--job-name`, `--jobs-dir`, `-p`, `-l`, `--sample-seed`) were verified against `datacurve_pier==0.3.0`. If `pier run --help` disagrees with what's documented below after installing from git `HEAD`, pin the release instead: `uv tool install datacurve-pier==0.3.0`.

3. **Clone the `datacurve-ai/deep-swe` task set** (113 Harbor-format tasks — see [Trial count](#trial-count) for how that number is confirmed):

   ```bash
   git clone https://github.com/datacurve-ai/deep-swe /path/to/deep-swe
   ```

   Pass `--dataset-dir /path/to/deep-swe/tasks` on every `run.py` command below. The default `--dataset-dir` (`benchmarks/deep-swe/data`) is where this repo vendors `data/leaderboard.json` — not the actual task files.

4. **`ANTHROPIC_API_KEY`** — the `claude` process pier launches inside each trial's container needs to authenticate:

   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

## How it works, briefly

`run.py` builds a matrix of **10 plugin arms**: 2 skills (`do-and-judge`, `do-in-steps`) × 5 orchestrator/implementation model-tier pairs (haiku/haiku, sonnet/haiku, sonnet/sonnet, opus/sonnet, opus/opus), plus **3 vanilla control arms** (haiku, sonnet, opus orchestrating themselves with no plugin, no slash command) when `--with-vanilla` is passed — 13 arms total. Each arm is one `pier run` invocation. `agent.py` (`ClaudeCodeSadd`) teaches pier how to load this plugin: it checks out this repo's `plugins/sadd` (pinned at `v3.8.1`) into the container and passes `--plugin-dir`, so a preflight failure here almost always means the plugin didn't load, not that a task failed.

Every arm writes to `runs/<arm-id>/` (job-level `arm.json`/`result.json`/`job.log`, plus one subdirectory per trial). `collect.py` walks that tree into `results.json`/`results.csv`; `report.py` turns those into `report.html`.

## Commands, in order

Run these from `benchmarks/deep-swe/` (or adjust paths). All `run.py` invocations need the `pier`-importable environment from prerequisite 2 above; `collect.py` and `report.py` run under a plain `python3` (verified — they never import `pier`).

### 1. Preflight

Cheapest possible sanity check: runs one task on the cheapest arm (`do-and-judge`, haiku/haiku) and fails loudly unless the `sadd` plugin actually loaded **and** a sub-agent was actually dispatched (checked against the `claude-code.txt` stream-json transcript, not just exit code).

```bash
uv run --with pier python3 run.py --preflight --task <task-name> --dataset-dir /path/to/deep-swe/tasks
```

Always run this before anything else — a broken `--plugin-dir` or a misconfigured container silently produces zero measurement, not an error, on every other command.

### 2. Single-task run

All 10 (or 13, with `--with-vanilla`) arms against exactly one named task:

```bash
uv run --with pier python3 run.py --mode single --task <task-name> --dataset-dir /path/to/deep-swe/tasks
```

### 3. Sample run

All arms against `--n-tasks` tasks, sampled with a pinned seed (`SAMPLE_SEED = 20260809`, hardcoded in `run.py`, identical across every arm and every invocation — no CLI flag to get it wrong) so every arm sees the same subset:

```bash
uv run --with pier python3 run.py --mode sample --n-tasks 20 --dataset-dir /path/to/deep-swe/tasks
```

**Use this to measure your own real per-trial cost and duration before touching `--mode full`.** Everything in the next section is a labeled assumption; a 10–20 task sample gives you real numbers from `results.json` in minutes, not a guess.

### Cost and time — read this before `--mode full`

**No run of this harness has been executed. Every number below is a stated assumption with its derivation shown, not a measurement.** A full run is 1,130–1,469 trials of a *judged* skill that dispatches sub-agents (an implementation pass, plus a separate judge pass — `do-in-steps` runs one judge per step) — categorically more expensive per task than a single plain agent turn. Do not run `--mode full` against a live API key without reading this.

#### Trial count

`data/leaderboard.json`'s own `n_tasks_in_set` field records **113 tasks** in the DeepSWE set — independently confirmed by fetching the live `datacurve-ai/deep-swe` README, which states "113 tasks spanning TypeScript, Go, Python, JavaScript, and Rust." `run.py`'s matrix is 10 plugin arms (2 skills × 5 tier-pair cells), or 13 with `--with-vanilla` (+3 vanilla controls):

| | Arms | Trials |
|---|---|---|
| `--mode full` | 10 | 113 × 10 = **1,130** |
| `--mode full --with-vanilla` | 13 | 113 × 13 = **1,469** |

#### Cost

| Basis | Per-trial | 1,130 trials | 1,469 trials |
|---|---:|---:|---:|
| **Fact** — `run.py`'s own hard cap, `--max-budget-usd` default (source: `build_arg_parser`) | $3.00 | $3,390 | $4,407 |
| **Fact** — official leaderboard's real measured cost for a *bare, non-judged* single agent on these same 113 tasks (`data/leaderboard.json.tiers.{sonnet,opus}.avg_cost_usd` — mini-swe-agent, not this harness) | $11.84 (opus) – $26.40 (sonnet) | $13,379 – $29,832 | $17,393 – $38,782 |
| **Assumption** — a judged trial (implementation pass + judge pass, or a judge per step) costs roughly 1.5–3× that bare-agent baseline | ~$20 (round, blended across tiers/skills) | ~$22,600 | ~$29,380 |

The middle row is the load-bearing fact here, not an estimate: it is real, vendored data showing that a *single, non-judged* agent already costs $12–26 per trial on these tasks — **4×–9× above `run.py`'s own $3 default budget cap.** Since `do-and-judge`/`do-in-steps` do strictly more work than that bare agent, the practical implication is blunt: **at the default `--max-budget-usd`, most sonnet/opus-tier judged trials will likely exhaust their budget before finishing** and end up `status: errored` (excluded from Pass@1, but still billed for whatever ran before the cutoff) rather than completing. Raise `--max-budget-usd` well above $3 (e.g. `--max-budget-usd 25`) before attempting `--mode full`, and use `--mode sample` to see your own real per-trial spend first — `results.json`'s `avg_cost_usd` per arm is ground truth; nothing above is.

**Fact** — Anthropic first-party API pricing per million tokens, fetched from `https://platform.claude.com/docs/en/about-claude/pricing` on 2026-08-09: Haiku 4.5 $1.00 / $5.00 (in/out), Sonnet 5 $2.00 / $10.00 introductory through 2026-08-31 (standard $3.00 / $15.00 from 2026-09-01), Opus 5 $5.00 / $25.00 (in/out). Haiku-tier arms will sit well under the blended $20/trial assumption above; opus/opus arms well above it.

#### Time

| Basis | Per-trial | Total agent-compute-time (sum across trials, not wall-clock) |
|---|---:|---:|
| **Fact** — official leaderboard's real measured step count for a bare agent (`data/leaderboard.json.tiers.{opus,sonnet}.avg_n_agent_steps`: 99 / 268) at an assumed ~15s/step | ~25 min (opus) – ~67 min (sonnet) | — |
| **Assumption** — a judged trial runs ~1.5–2× that (extra implementation/judge pass) | ~38–134 min (1.5× × ~25 min opus low end ≈ 38; 2× × ~67 min sonnet high end ≈ 134; round: ~45 min blended) | 1,130 × 45 min ≈ **848 hours (~35 days)**; 1,469 × 45 min ≈ **1,102 hours (~46 days)** |

**Wall-clock ≠ the totals above.** They're summed agent-compute-time; actual wall-clock is that total divided by however many trials run concurrently, and `run.py` exposes no concurrency flag — it shells out to one `pier run` per arm, sequentially, and pier's own scheduling determines how many trials within an arm run in parallel. `--agent-timeout-multiplier` (default `3.0`) bounds how long pier waits before killing a single stalled trial (judged skills fan out to several sub-agents per task, so the default `1.0` would likely time out mid-judgement) — it is not a total-runtime lever.

### 4. Full run

Once you've raised `--max-budget-usd` based on a `--mode sample` result:

```bash
uv run --with pier python3 run.py --mode full --dataset-dir /path/to/deep-swe/tasks --max-budget-usd 25
# add --with-vanilla for the 3 no-plugin control arms (13 arms, 1,469 trials, instead of 10/1,130)
```

Useful flags: `--dry-run` prints every arm's `pier` command and the arm count without writing anything or executing anything — sanity-check the matrix before spending money. Resumability isn't specific to `--mode full`: any invocation that isn't `--dry-run` or `--preflight` — `--mode single` and `--mode sample` included — skips an arm whose `runs/<arm-id>/result.json` already has `finished_at` set, unless `--force` is passed.

### 5. Collect results

Aggregates `runs/*/*/result.json` into `results.json` + `results.csv`. Runs under a plain `python3` — does not need `pier` importable:

```bash
python3 collect.py
# --runs-dir / --out-dir override the defaults (./runs, this directory)
```

Infrastructure failures (Docker build failures, agent/verifier timeouts, budget exhaustion) are classified `errored` and excluded from the Pass@1 denominator and every average — `n_errored` is reported separately per arm so nothing silently disappears. Re-runnable any time; it rebuilds both output files from scratch rather than merging.

### 6. Generate the report

Renders `results.json` + the vendored `data/leaderboard.json` into a single self-contained `report.html` (inline SVG/CSS/JS, opens directly from disk, no network). Also a plain `python3` script:

```bash
python3 report.py
# --results / --leaderboard / --out override the defaults
```

## Running the tests

```bash
cd benchmarks/deep-swe && python3 -m unittest discover
```

(equivalently, from the repo root: `python3 -m unittest discover -s benchmarks/deep-swe`). No third-party install needed — 102 stdlib-`unittest` tests, runs in well under a second.

**Test coverage is narrower than "the test suite passes" might suggest — don't overclaim it.** All 102 tests cover pure functions in `collect.py` and `report.py` only: Wilson confidence intervals, status classification, chart-geometry math, table formatting. `run.py` and `agent.py`'s actual pier orchestration — building the `pier run` command, checking out the plugin into a container, driving the container lifecycle — is **deliberately not unit-tested**. It's exercised instead by `run.py --dry-run` (prints every command without executing anything) and `run.py --preflight` (actually runs one trial and verifies the plugin loaded and a sub-agent was dispatched). If you change `run.py`'s command-building or `agent.py`'s install steps, `--preflight` — not the test suite — is what tells you whether it still works.

## Regenerating `data/leaderboard.json`

The file documents its own regeneration procedure in its `_comment` field: *"Do not hand-edit -- regenerate by re-fetching `source_data_url` and re-applying `row_selection_rule`, then update `snapshot_date`."* Concretely:

1. Re-fetch `source_data_url` (`https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`) for current data.
2. Re-apply `row_selection_rule`: DeepSWE's own site runs each model at several `reasoning_effort` configs (`low`/`medium`/`high`/`xhigh`/`max`) and its live-leaderboard UI shows one row per model — the one at the **highest available `reasoning_effort`**. Reproduce that same selection so the vendored numbers match what a visitor to the site sees by default.
3. Update `snapshot_date` to the date you regenerated it.

The file also records `harness` (`mini-swe-agent`), `data_version`, and per-tier `absence_reason` when a tier genuinely isn't on the leaderboard (e.g. haiku, as of the current snapshot — there is no `claude-haiku-*` row anywhere in the fetched dataset) — carry these through rather than inventing values for a tier that's actually missing.

## The official leaderboard numbers are not comparable to this harness's own arms

Say this plainly, because `report.html` puts both on the same chart: **every "official" number comes from `data/leaderboard.json`, which benchmarks models with `mini-swe-agent` — a minimal single-agent scaffold, not `claude-code` running the `sadd` plugin this harness measures.** `mini-swe-agent` and `claude-code` differ in tool access, context management, and prompting. The official bars are useful context for where a raw model tier sits on an independent benchmark; they are **not** a like-for-like comparison against this harness's own plugin/vanilla arms. `report.py` renders the official bars with different visual treatment specifically for this reason (unfilled/outlined, never the same categorical color as this harness's own arms) and prints the leaderboard's own `honesty_note` as a footnote wherever an official bar appears — read it there too, not just here.
