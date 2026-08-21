# Deep-SWE benchmark harness

Runs the [DeepSWE](https://deepswe.datacurve.ai/) coding-agent benchmark (113 real-world software-engineering tasks) against `claude-code` running the `sadd` plugin's judged skills (`do-and-judge`, `do-in-steps`), across a 5×2 model-tier matrix, via [pier](https://github.com/datacurve-ai/pier). Produces `results.json`/`results.csv` and a self-contained `report.html` comparing this harness's own arms against DeepSWE's official leaderboard.

**Read [Cost and time](#cost-and-time--read-this-before---mode-full) before running `--mode full`.** A full run is 1,130 trials of a judged skill that fans out to sub-agents — 1,469 with `--with-vanilla`, whose extra 339 are single-agent control trials running no skill at all. The judged trials are meaningfully more expensive per task than a plain single-agent benchmark run.

## Prerequisites

1. **Docker** (or a compatible container runtime) running locally — pier provisions a fresh container per trial.

2. **[uv](https://docs.astral.sh/uv/)** — install it with the official standalone installer if you don't already have it (lands in `~/.local/bin`):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   and a sync environment:

   ```bash
   cd benchmarks/deep-swe
   uv sync
   ```

3. **Clone the `datacurve-ai/deep-swe` task set** (113 Harbor-format tasks — see [Trial count](#trial-count) for how that number is confirmed):

   ```bash
   git clone https://github.com/datacurve-ai/deep-swe /path/to/deep-swe
   ```

   Pass `--dataset-dir /path/to/deep-swe/tasks` on every `run.py` command below. The default `--dataset-dir` (`benchmarks/deep-swe/data`) is where this repo vendors `data/leaderboard.json` — not the actual task files.

4. **Authentication** for the `claude` process pier launches inside each trial's container. `run.py` does `os.environ.copy()` before shelling out to `pier run`, so whatever you `export` on the host propagates through to pier, then into the container — no harness-level flag is needed for any option below. Pier itself builds the container's `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, and `CLAUDE_CODE_OAUTH_TOKEN` from the host env and then drops whichever ones are empty (`ClaudeCode.run()`, `src/pier/agents/installed/claude_code.py:1261`, comment: "Remove empty auth credentials to allow Claude CLI to prioritize the available method") — so set only the credential for the method you're using and leave the others unset.

   - **API key** (pay-per-token, the default most people reach for first):

     ```bash
     export ANTHROPIC_API_KEY=sk-ant-...
     ```

   - **Claude subscription, via a long-lived OAuth token** — no code change needed, pier already reads this. Generate a token with `claude setup-token` (requires an active Claude subscription), then:

     ```bash
     export CLAUDE_CODE_OAUTH_TOKEN=...
     ```

     Leave `ANTHROPIC_API_KEY` unset so pier's env-stripping picks the OAuth token.

     **Unverified — hedge this before trusting the [Cost and time](#cost-and-time--read-this-before---mode-full) numbers below under this auth mode:** whether per-trial cost parsing (`total_cost_usd` from the stream — this harness overrides pier's own `_parse_total_cost_from_stream_json` in `agent.py`, see [Cost](#cost)) reports meaningful, correct dollar figures under subscription/OAuth auth — as opposed to first-party API-key billing — was **not tested** as part of this change. Subscription auth also carries its own rate limits this harness has no visibility into. Run `--mode sample` first and inspect `results.json`'s `avg_cost_usd` yourself before relying on it under OAuth auth.

   - **AWS Bedrock:**

     ```bash
     export CLAUDE_CODE_USE_BEDROCK=1
     # plus the standard AWS credential chain (or AWS_BEARER_TOKEN_BEDROCK), and optionally:
     export AWS_REGION=us-east-1  # pier's default if unset
     ```

   - **Gateway / proxy routing:**

     ```bash
     export ANTHROPIC_AUTH_TOKEN=...
     export ANTHROPIC_BASE_URL=https://your-gateway.example.com
     ```

     Pier's container network allowlist is decided in this order (`claude_code.py:177-187`, method `network_allowlist`): Bedrock mode is checked **first** and returns `.amazonaws.com`, so it wins even when `ANTHROPIC_BASE_URL` is also set; otherwise `ANTHROPIC_BASE_URL`'s own hostname when that is set; else `api.anthropic.com`. Whichever pier picks is not the final list here — `agent.py`'s `ClaudeCodeSadd.network_allowlist` appends `github.com` to it, so the container can clone the pinned plugin checkout.

   Pier also has generic `--ae/--agent-env KEY=VALUE` and `--env-file <path>` flags for injecting arbitrary container env (`src/pier/cli/jobs.py:348-354` for `--ae/--agent-env`, `:491-497` for `--env-file`), but `run.py` builds its own fixed `pier run` command with no pass-through for extra flags — for this harness, exporting the variables above on the host before invoking `run.py` is the only route; there is nothing to add to `run.py` itself for any of these modes.

## How it works, briefly

`run.py` builds a matrix of **10 plugin arms**: 2 skills (`do-and-judge`, `do-in-steps`) × 5 orchestrator/implementation model-tier pairs (haiku/haiku, sonnet/haiku, sonnet/sonnet, opus/sonnet, opus/opus), plus **3 vanilla control arms** (haiku, sonnet, opus orchestrating themselves with no plugin, no slash command) when `--with-vanilla` is passed — 13 arms total. Pass `--skill do-and-judge` or `--skill do-in-steps` to restrict `--mode single/sample/full` to that one skill's 5 tier-pair arms instead of both skills' 10 (8 instead of 13 with `--with-vanilla` — vanilla arms aren't tied to a skill, so `--skill` never drops or duplicates them). Pass `--model haiku`, `--model sonnet`, or `--model opus` to restrict to that one *symmetric* tier pair — same tier orchestrating and implementing — instead of all 5 CELLS (1 arm per skill in play instead of 5); combine `--skill` and `--model` to run exactly one arm. Unlike `--skill`, `--model` **also** restricts `--with-vanilla`'s controls to that one tier (1 instead of 3), since vanilla arms are per-model rather than per-skill — leaving all 3 in would silently reintroduce the other two tiers a `--model` filter was meant to exclude. Each arm is one `pier run` invocation. `agent.py` (`ClaudeCodeSadd`) teaches pier how to load this plugin: it checks out this repo's `plugins/sadd` (pinned at `v3.8.1`) into the container and passes `--plugin-dir`, so a preflight failure here almost always means the plugin didn't load, not that a task failed.

Every arm writes to `runs/<arm-id>/` (job-level `arm.json`/`result.json`/`job.log`, plus one subdirectory per trial). `collect.py` walks that tree into `results.json`/`results.csv`; `report.py` turns those into `report.html`.

## Commands, in order

Run these from `benchmarks/deep-swe/` (or adjust paths). All `run.py` invocations need the `pier`-importable environment from prerequisite 2 above; `collect.py` and `report.py` run under a plain `python3` (verified — they never import `pier`).

### 1. Preflight

Cheapest sanity check that still runs something: one task on the cheapest arm of one skill (default `do-and-judge`, haiku/haiku), failing loudly unless the `sadd` plugin actually loaded **and** a sub-agent was actually dispatched (checked against the `claude-code.txt` stream-json transcript, not just exit code). Cheapest is relative, not free — the two preflight trials recorded under `runs/` took **31.9 and 41.1 minutes** each (`finished_at − started_at`), so plan on a coffee-break's wait rather than seconds.

```bash
uv run python3 run.py --preflight --task <task-name> --dataset-dir /path/to/deep-swe/tasks
```

Example: 
- max complexity: `uv run python3 run.py --preflight --task --skill do-in-steps  "gql-incremental-graphql-delivery" --dataset-dir ../../../../../../benchmarks/deep-swe/tasks`
- high complexity: `uv run python3 run.py --preflight --task --skill do-in-steps "kombu-single-active-consumer-priority" --dataset-dir ../../../../../../benchmarks/deep-swe/tasks`
- medium-high complexity: `uv run python3 run.py --preflight --task --skill do-in-steps "cattrs-partial-structuring-recovery" --dataset-dir ../../../../../../benchmarks/deep-swe/tasks`
- medium complexity: `uv run python3 run.py --preflight --task --skill do-in-steps  "bandit-incremental-cache-control" --dataset-dir ../../../../../../benchmarks/deep-swe/tasks`
- low complexity: `uv run python3 run.py --preflight --skill do-in-steps --task "abs-stepped-slices" --dataset-dir ../../../../../../benchmarks/deep-swe/tasks`

Pass `--skill do-in-steps` to preflight that skill's cheapest arm (haiku/haiku) instead of the default `do-and-judge`:

```bash
uv run python3 run.py --preflight --skill do-in-steps --task <task-name> --dataset-dir /path/to/deep-swe/tasks
```

A preflight trial is a real trial, so the [completion gate](#5-collect-results) applies to it: if it produced no `artifacts/model.patch` or ended its turn on a question, `--preflight` still reports `PASSED (plugin checks only)` — the plugin loaded and dispatched, which is all preflight asks — and exits `3` instead of `0`, naming the trial and reason on stderr. It is not treated as a plugin failure: preflight runs one task on the cheapest arm, which can lose or abandon that task with the plugin working perfectly.

`--skill`'s job directory is `runs/_preflight-<skill>/` for any skill other than the default, so the two skills' preflight runs never collide; the default skill keeps the original `runs/_preflight/` name.

Pass `--model sonnet` (or `haiku`/`opus`) to preflight that tier's arm instead of the cheapest one — useful to smoke-test a specific tier pair before committing to it in `--mode single/sample/full`. Note that this preflight is itself a real-money trial at that tier: the one uncapped sonnet-tier `do-in-steps` trial recorded under `runs/` — not a preflight, but the same per-trial work — really cost **$26.530** (its stream's cumulative total; pier recorded the understated $0.392, see [Cost](#cost)) and ran **127.7 minutes**.

```bash
uv run python3 run.py --preflight --skill do-in-steps --model sonnet --task <task-name> --dataset-dir /path/to/deep-swe/tasks
```

Same job-directory rule applies: any `--model` other than none appends a `-<model>` suffix (e.g. `runs/_preflight-sonnet/`, or `runs/_preflight-do-in-steps-sonnet/` combined with a non-default `--skill`), so preflighting the same skill at different tiers back to back never overwrites a prior run's `prompt.j2`/`arm.json`. `runs/_preflight/` is the directory whenever the skill in effect is the default `do-and-judge` — left implicit *or* passed explicitly, since `run_preflight` resolves `--skill` before naming the job — and no `--model` is given.

Always run this before anything else — a broken `--plugin-dir` or a misconfigured container silently produces zero measurement, not an error, on every other command.

### 2. Single-task run

All 10 (or 13, with `--with-vanilla`) arms against exactly one named task:

```bash
uv run python3 run.py --mode single --task <task-name> --dataset-dir /path/to/deep-swe/tasks
```

Add `--skill do-and-judge` or `--skill do-in-steps` to run only that skill's 5 arms (8 with `--with-vanilla`) instead of both skills' 10 (13).

Add `--model haiku`, `--model sonnet`, or `--model opus` to run only that tier's arm per skill in play (1 instead of 5, so 2 across both skills instead of 10). Combine both flags to run **exactly one arm**:

```bash
uv run python3 run.py --mode single --task <task-name> --skill do-in-steps --model sonnet --dataset-dir /path/to/deep-swe/tasks
```

### 3. Sample run

All arms against `--n-tasks` tasks, sampled with a pinned seed (`SAMPLE_SEED = 20260809`, hardcoded in `run.py`, identical across every arm and every invocation — no CLI flag to get it wrong) so every arm sees the same subset:

```bash
uv run python3 run.py --mode sample --n-tasks 20 --dataset-dir /path/to/deep-swe/tasks
```

**Use this to measure your own real per-trial cost and duration before touching `--mode full`.** Every projected *total* in the next section is labeled with its basis — **Fact** (vendored data) or **Assumption** (a stated estimate) — and the *Measured* per-trial figures there come from three individually recorded trials, not from a run of the matrix.

**A sample run is not a quick check — budget days, not minutes.** `--n-tasks 20` is 20 tasks × 10 arms = 200 trials. Derivation from what this repo records: `run.py` runs arms sequentially (one `pier run` per arm), every recorded `runs/*/config.json` has `n_concurrent_trials: 4`, and the three trials under `runs/` took 31.9 / 41.1 / 127.7 minutes (`finished_at − started_at` in each `result.json`). That gives 10 arms × ⌈20/4⌉ batches × 32–128 min ≈ **27–106 hours of wall-clock**; `--n-tasks 10` brings it to ≈ **16–64 hours** — not half, because ⌈10/4⌉ is 3 batches per arm rather than 5. Two of those three trials ran under the $3 cap described below, which truncates a trial, so a sample without that cap skews toward the high end. What a sample buys is *measured* numbers in place of the estimates below — not speed.

### Cost and time — read this before `--mode full`

**No multi-task run of this matrix has been executed: the three jobs recorded under `runs/` hold exactly one trial each (two from `--preflight`, one single-task arm run). Every projected *total* below is therefore an extrapolation, not a measurement of this harness.** Each row names its basis: **Fact** rows are vendored or published data (measured elsewhere, by someone else, on a different agent scaffold), **Assumption** rows are estimates with their derivation shown, and the per-trial figures under [Cost](#cost) labeled *Measured* are real measurements taken from those three recorded trials. A full run is 1,130 trials of a *judged* skill that dispatches sub-agents (an implementation pass, plus a separate judge pass — `do-in-steps` runs one judge per step), or 1,469 with `--with-vanilla`, whose extra 339 are single-agent control trials running no skill. The judged ones are categorically more expensive per task than a single plain agent turn. Do not run `--mode full` against a live API key without reading this.

#### Trial count

`data/leaderboard.json`'s own `n_tasks_in_set` field records **113 tasks** in the DeepSWE set — independently confirmed by fetching the live `datacurve-ai/deep-swe` README, which states "113 tasks spanning TypeScript, Go, Python, JavaScript, and Rust." `run.py`'s matrix is 10 plugin arms (2 skills × 5 tier-pair cells), or 13 with `--with-vanilla` (+3 vanilla controls). Passing `--skill` restricts this to one skill's 5 tier-pair cells (8 with `--with-vanilla`, since the 3 vanilla controls aren't tied to a skill). Passing `--model` restricts this to one *symmetric* tier-pair cell per skill in play (1 instead of 5) — and, unlike `--skill`, also restricts the vanilla controls to that one tier (1 instead of 3), since vanilla arms are per-model:

| | Arms | Trials |
|---|---|---|
| `--mode full` | 10 | 113 × 10 = **1,130** |
| `--mode full --with-vanilla` | 13 | 113 × 13 = **1,469** |
| `--mode full --skill <skill>` | 5 | 113 × 5 = **565** |
| `--mode full --skill <skill> --with-vanilla` | 8 | 113 × 8 = **904** |
| `--mode full --model <tier>` | 2 | 113 × 2 = **226** |
| `--mode full --model <tier> --with-vanilla` | 3 | 113 × 3 = **339** |
| `--mode full --skill <skill> --model <tier>` | 1 | 113 × 1 = **113** |
| `--mode full --skill <skill> --model <tier> --with-vanilla` | 2 | 113 × 2 = **226** |

The projected cost and time *totals* below are all derived from the unfiltered 10/13-arm counts; a `--skill`- and/or `--model`-filtered full run's cost and time scale down proportionally with its arm count (e.g. 565/1,130 for `--skill` alone, 226/1,130 for `--model` alone, 113/1,130 for both together, of the totals below).

#### Cost

| Basis | Per-trial | 1,130 trials | 1,469 trials |
|---|---:|---:|---:|
| **Fact** — official leaderboard's real measured cost for a *bare, non-judged* single agent on these same 113 tasks (`data/leaderboard.json.tiers.{sonnet,opus}.avg_cost_usd` — mini-swe-agent, not this harness) | $11.84 (opus) – $26.40 (sonnet) | $13,379 – $29,832 | $17,393 – $38,782 |
| **Assumption** — a judged trial (implementation pass + judge pass, or a judge per step) costs roughly 1.5–3× that bare-agent baseline | ~$20 (round, blended across tiers/skills) | ~$22,600 | ~$29,380 |

The top row is the load-bearing fact here, not an estimate: it is real, vendored data showing that a *single, non-judged* agent already costs $12–26 per trial on these tasks. Since `do-and-judge`/`do-in-steps` do strictly more work than that bare agent, a full run is a real financial commitment at the blended per-trial estimate above. This harness enforces no per-trial spend cap — every trial runs to completion or errors for an unrelated infra reason, it is never cut off partway through for cost reasons — so use `--mode sample` first to see your own real per-trial spend before committing to `--mode full`; for a run made with the cost override described below in place, `results.json`'s `avg_cost_usd` and `max_cost_usd` per arm are ground truth, nothing above is. Read `max_cost_usd` too, not just the average: with no cap to bound a runaway trial, a single expensive one is invisible in an average over dozens.

`agent.py` overrides pier's `_parse_total_cost_from_stream_json` so those figures can be trusted going forward. Pier returned the FIRST `{"type":"result"}` event in a trial's stream, but a `claude --print` session with async sub-agents emits one such event per resumption, each carrying the session's *cumulative* spend. `ClaudeCodeSadd` takes the maximum across all of them instead; the rule itself lives in `stream_cost.py` (kept out of `agent.py` so it is testable without `pier`), whose docstring carries the last-vs-max and partial-data decisions.

Measured on the three trials recorded under `runs/`:

| Recorded trial | `result` events | first → last | pier recorded |
|---|---:|---|---|
| `do-in-steps__sonnet-sonnet/…ZsbwRdJ` | 22 | $0.392 → $26.530 | $0.392 — understated 68x |
| `_preflight-do-in-steps/…9ryVMmH` | 11 | $0.140 → $1.804 | $0.140 — understated 13x |
| `_preflight/abs-stepped-slices__HyQJyYy` | 1 | $1.865 → $1.865 | $1.865 — correct |

So the defect is conditional, not universal: **any trial whose stream carries more than one `result` event was understated the same way, and single-`result`-event trials were always correct** (for those, first and last are the same event). Whether a given trial is affected depends on whether its session ever resumed, which is what a sub-agent completion does.

**Provenance — two of those three trials ran under a spend cap this harness no longer has.** Both `_preflight*` jobs record a $3.00 per-trial budget cap in the pier `config.json`/`lock.json` they were run with, so their spend was bounded at $3 and says nothing about what an uncapped trial costs; the `do-in-steps__sonnet-sonnet` job carries no such key and is the one uncapped trial here, at $26.530. The cap was removed from this harness (there is no flag for it — see [Cost](#cost) above), so an uncapped run can cost several times what the two capped rows show, as that third row does.

**Trials already recorded in `runs/` keep whatever figure pier wrote at the time** — understated for the two multi-`result`-event trials above, already correct for the single-event one. `collect.py` reports the cost pier wrote into each trial's `result.json` and deliberately does not re-derive it from the stream — re-deriving would silently restate numbers for runs already on disk, leaving `results.json` disagreeing with the `result.json` files it was built from. The override corrects runs made from here on; to see the real total for an already-recorded trial, read the last `result` event of its `agent/claude-code.txt` directly.

**Fact** — Anthropic first-party API pricing per million tokens, fetched from `https://platform.claude.com/docs/en/about-claude/pricing` on 2026-08-09: Haiku 4.5 $1.00 / $5.00 (in/out), Sonnet 5 $2.00 / $10.00 introductory through 2026-08-31 (standard $3.00 / $15.00 from 2026-09-01), Opus 5 $5.00 / $25.00 (in/out). Haiku-tier arms will sit well under the blended $20/trial assumption above; opus/opus arms well above it.

#### Time

| Basis | Per-trial | Total agent-compute-time (sum across trials, not wall-clock) |
|---|---:|---:|
| **Fact** — official leaderboard's real measured step count for a bare agent (`data/leaderboard.json.tiers.{opus,sonnet}.avg_n_agent_steps`: 99 / 268) at an assumed ~15s/step | ~25 min (opus) – ~67 min (sonnet) | — |
| **Assumption** — a judged trial runs ~1.5–2× that (extra implementation/judge pass) | ~38–134 min (1.5× × ~25 min opus low end ≈ 38; 2× × ~67 min sonnet high end ≈ 134; round: ~45 min blended) | 1,130 × 45 min ≈ **848 hours (~35 days)**; 1,469 × 45 min ≈ **1,102 hours (~46 days)** |

**Wall-clock ≠ the totals above.** They're summed agent-compute-time; actual wall-clock is that total divided by however many trials run concurrently, and `run.py` exposes no concurrency flag — it shells out to one `pier run` per arm, sequentially, and pier's own scheduling determines how many trials within an arm run in parallel. `--agent-timeout-multiplier` (default `3.0`) bounds how long pier waits before killing a single stalled trial (judged skills fan out to several sub-agents per task, so the default `1.0` would likely time out mid-judgement) — it is not a total-runtime lever.

### 4. Full run

Once you've reviewed your real per-trial spend from a `--mode sample` result (see [Cost](#cost) above):

```bash
uv run python3 run.py --mode full --dataset-dir /path/to/deep-swe/tasks
# add --with-vanilla for the 3 no-plugin control arms (13 arms, 1,469 trials, instead of 10/1,130)
# add --skill do-and-judge (or do-in-steps) to run only that skill's 5 arms, 565 trials
# (8 arms, 904 trials, with --with-vanilla) instead of both skills' 10/1,130 (13/1,469)
# add --model haiku/sonnet/opus to run only that tier's 1 arm per skill in play, 226 trials
# across both skills (113 trials with --skill too); --model also shrinks --with-vanilla's
# controls to 1 instead of 3 -- see the Trial count table for every combination
```

Each arm prints one of three verdicts as it finishes — `PASS`, `INCOMPLETE` or `FAIL` — and the process exit code mirrors the worst one seen: `0` all clean, `3` at least one arm has INCOMPLETE trials, `1` pier itself failed an arm (which outranks INCOMPLETE). An arm is INCOMPLETE when a trial produced no `artifacts/model.patch` (missing or zero-byte — both mean it committed nothing) or ended its turn asking a question nobody could answer — see [Collect results](#5-collect-results) for what that means and why. The end-of-run summary only says "completed successfully" when nothing is in either bucket, and arms skipped as already-complete are re-checked so a resumed run cannot claim success for trials an earlier invocation abandoned. Exit code `3` and not `2`, because argparse already spends `2` on usage errors.

Every arm's prompt — plugin and vanilla control alike — also carries a short non-interactive contract telling the agent there is no human to answer it and to choose, state the choice, and keep going. It is identical text in both, deliberately: the vanilla arms are the control the plugin arms are measured against, so prompt text in one and not the other would be a second uncontrolled difference between them.

Useful flags: `--dry-run` prints every arm's `pier` command and the arm count without writing anything or executing anything — sanity-check the matrix before spending money. It honors `--skill` and `--model` identically to a real run, so the printed commands and count reflect exactly the filtered matrix that would execute — combine `--dry-run` with `--skill`/`--model` to confirm the filter before committing budget. Resumability isn't specific to `--mode full`: any invocation that isn't `--dry-run` or `--preflight` — `--mode single` and `--mode sample` included — skips an arm whose `runs/<arm-id>/result.json` already has `finished_at` set, unless `--force` is passed.

### 4b. Scheduled run (`--mode scheduled`)

The other three modes apply one filter across `run.py`'s own arm matrix. `--mode scheduled` is different: it takes its *entire* matrix — which tasks, which model pairs, which skills, how fast to walk through them, and which combinations to skip — from `--schedule` (default `schedule.yaml`, see [The schedule file](#the-schedule-file-scheduleyaml) below), and walks it unattended for days: one task per model-pair-and-skill cell, paced two hours apart, retrying a cell that failed for a reason that wasn't the model's fault.

```bash
uv run python3 run.py --mode scheduled --dataset-dir /path/to/deep-swe/tasks
# --schedule <path> to run a different schedule file instead of the committed one
# --force re-runs every cell regardless of the state file or an on-disk result --
#   see "The retry bound and --force" (below, under Scheduler outcomes) for the
#   one case where this alone is NOT enough to un-stick a cell
```

Because the matrix is entirely declared in the schedule file, `--task`, `--n-tasks`, `--skill`, `--model`, and `--with-vanilla` all conflict with `--mode scheduled` and are rejected outright rather than silently ignored — a flag that quietly did nothing here is how an operator ends up believing they ran a subset when they ran everything. To run a subset, edit `schedule.yaml`'s `skips` (each one carries a mandatory reason, so the report can show "deliberately not run, because X") or point `--schedule` at a different file.

`--dry-run` (combined with `--mode scheduled`) prints the full walk order, every skip with its reason, and the pacing/retry arithmetic below without executing or writing anything — read it before committing to a schedule. For the schedule committed in this repo, it prints:

```
[schedule] schedule.yaml: 45 planned run(s), 33 runnable, 12 skipped by rule
  ...
  pacing: 33 still to run, 7200s between runs => 230400s (64.0h) of pacing alone, excluding run time.
  retries: at most 2 technical retries per run, 7200s backoff each => at most 99 executions and 475200s (132.0h) of extra backoff.
```

**Wall-clock cost of a full scheduled run.** Like the [Cost and time](#cost-and-time--read-this-before---mode-full) section above, every total here is a projection, not a measurement: no scheduled run of this matrix has ever executed.

| Basis | Figure |
|---|---:|
| **Fact** — cells in the committed `schedule.yaml`'s matrix (3 tasks × 5 model pairs × 3 skills) | 45 |
| **Fact** — runnable after `skips` (12 cells are deliberately excluded) | 33 |
| **Fact** — pacing alone, 2h between the 33 runnable cells (deterministic: `between_runs: 2h` × 32 gaps) | 230,400s (64.0h) |
| **Assumption** — run time per cell, carried over from [Time](#time) above's ~45 min/trial blended estimate (this mode runs exactly one task per cell, i.e. one trial) | ~24.75h (33 × 45 min) |
| **Assumption + Fact** — baseline total with zero technical failures (pacing + run time) | ~88.75h (**~3.7 days**) |
| **Fact** — worst-case EXTRA backoff if every runnable cell exhausts its retries (deterministic: 33 cells × 2 retries × 2h backoff) | 475,200s (132.0h) |
| **Assumption + Fact** — worst-case total (baseline + worst-case backoff + up to 2 extra run-time attempts per cell) | up to ~270h (**~11.3 days**) |

Both the pacing and worst-case-backoff rows are exact arithmetic over the committed `schedule.yaml` and `scheduler.MAX_TECHNICAL_RETRIES`, reproducible with `--dry-run`; the run-time rows inherit the same estimate (and the same caveat) as the rest of this README. `--skill`/`--model`/`--with-vanilla` cannot narrow a scheduled run (see above) — the only way to shrink these numbers is to edit `schedule.yaml` itself.

Every executed cell is re-collected and re-reported immediately (`collect.py` then `report.py`, both re-derived from scratch) — `results.json`/`report.html` are always current as of the last cell to finish, not just at the end of the whole run. See [Scheduler outcomes, triage, and resumability](#scheduler-outcomes-triage-and-resumability) for what each cell's outcome means, [`runs/scheduler-state.json`](#runsscheduler-statejson) for what survives a restart, and [Report visual grammar](#report-visual-grammar) for how the report renders a matrix that is mostly still unrun.

### 5. Collect results

Aggregates `runs/*/*/result.json` into `results.json` + `results.csv`. Runs under a plain `python3` — does not need `pier` importable:

```bash
python3 collect.py
# --runs-dir / --out-dir override the defaults (./runs, this directory)
```

`results.csv` is one row per trial. Its `reward` column is the verifier's own scalar binary verdict — `0` or `1`, the `reward` key of the `rewards` bundle each trial's verifier writes, blank when a bundle carries no such key. It is **not** a sum or score over that bundle: the verifier reports `rewards` as a metrics bundle (test counts, `f2p`/`p2p` ratios, a `partial` graded-credit score) alongside the one binary `reward`, and only the scalar answers "was this task solved". `resolved`/`status` are derived from that same scalar whenever the bundle carries one; for a bundle that does not, the verdict is recomputed from `f2p`/`p2p` and, failing that, from an all-values-equal-1 rule — see `verifier_reports_success()` in `collect.py` for why those two fallbacks are ordered that way.

Every trial gets one of **four** statuses, carried in the `status` column of `results.csv` (and each trial's entry in `results.json`). The two failure-ish ones are deliberately not the same thing:

| `status` | Meaning | `error_reason` | In Pass@1's denominator? |
|---|---|---|---|
| `resolved` | The verifier says the task was solved. | blank | Yes (as a success) |
| `unresolved` | The agent finished and got it wrong. | blank | Yes (as a failure) |
| `incomplete` | The agent never finished: no `artifacts/model.patch` for the trial (absent or zero-byte), or its final message ends in a question asked of an operator who was never there. | `no_model_patch` or `final_message_is_question` | Yes (as a failure) |
| `errored` | Infrastructure failure — Docker build failure, agent/verifier timeout, API rate-limit failure, plugin that didn't load. | `pier_exception:<category>:<type>`, `missing_verifier_rewards`, `malformed_result_json`, or a plugin-load reason | **No** — excluded from every average too |

**Read `error_reason` to find out *why* a given trial is `incomplete` or `errored`** — it is a `results.csv` column (and a `results.json` trial field) carrying the specific reason, alongside `trial_id`, which names the `runs/<arm-id>/<trial_id>/` directory to go read.

**`--force` alone does not re-attempt an INCOMPLETE trial.** An INCOMPLETE trial already has a `result.json` — the agent and verifier both ran to completion; it is only the model-patch/final-message heuristic above that flags it after the fact — so pier's own per-trial resume skips it on every subsequent invocation exactly like a STUCK technical-failure trial does (see "The retry bound and `--force`" under [Scheduler outcomes, triage, and resumability](#scheduler-outcomes-triage-and-resumability) for the full mechanism). And unlike that STUCK recipe, re-running *without* `--force` will not help here either: `run.py`'s own arm-level skip check (`is_arm_complete`, [Full run](#4-full-run)) reads only the arm's own `runs/<arm-id>/result.json`, whose `finished_at` stays set no matter what you delete inside the arm's directory — so without `--force` the whole arm is skipped before pier ever gets a chance to resume it. To actually re-attempt one INCOMPLETE trial: remove *just that trial's* own directory, then re-run it with `--force` — the missing directory has no `result.json` left for pier to skip, while every other trial in the arm still has its own intact `result.json` and resolves instantly without re-running:

```bash
rm -rf runs/<arm-id>/<trial-id>
uv run python3 run.py --force  # plus whichever --mode/--dataset-dir/--skill/--model flags produced this arm originally
```

For example, against a trial actually recorded in this tree: `rm -rf runs/do-in-steps__sonnet-sonnet__abs-stepped-slices/abs-stepped-slices__tqkGk6o`.

`n_incomplete` and `n_errored` are both reported per arm, and never summed: an `incomplete` trial is the agent's own abandonment and counts against the arm, while an `errored` one is the harness's fault and is dropped from the numbers entirely (so nothing silently disappears either way). Keeping `incomplete` in the denominator is deliberate — excluding it would let an arm raise its Pass@1 by walking away from the tasks it was losing. A verifier-certified success is never downgraded to `incomplete`, and an infra failure is never relabelled as one; see `classify_status()` in `collect.py` for the full precedence table.

The "ends in a question" test is a conservative heuristic: it looks only at the last prose line of the final `result` event, ignores anything inside a code fence, and stays quiet on quoted or rhetorical questions. See `message_ends_in_question()` in `collect.py` for exactly what it will and won't catch. It is validated against real recorded prose, not just invented examples: `runs/_preflight-do-in-steps/…9ryVMmH` ends its final message with "Which approach would you prefer? Or shall I continue with the current orchestration pace?" after offering the operator a numbered menu under budget pressure — the abandonment this whole gate exists for — while the other two recorded trials end on a bolded status line and a progress note and are correctly left alone (`tests/test_collect_completion_gate.py` pins all three). There is no "spent most of its budget" condition, because there is no spend cap in this harness for a cost to approach — cost anomalies surface through `cost_usd`/`max_cost_usd` instead.

Re-runnable any time; it rebuilds both output files from scratch rather than merging.

### 6. Generate the report

Renders `results.json` + the vendored `data/leaderboard.json` into a single self-contained `report.html` (inline SVG/CSS/JS, opens directly from disk, no network). Also a plain `python3` script:

```bash
python3 report.py
# --results / --leaderboard / --out override the defaults
```

Run it as a plain `python3 report.py`, not under `-O`/`PYTHONOPTIMIZE=1`: `render_bar_mark`'s `assert bar.display is not None` is the only thing standing between a forgotten `display` field and a silently wrong percentage on the page, and `assert` statements are compiled out entirely under `-O`.

## Running the tests

```bash
cd benchmarks/deep-swe && python3 -m unittest discover
```

(equivalently, from the repo root: `python3 -m unittest discover -s benchmarks/deep-swe`). No third-party install needed — the whole suite is stdlib `unittest` and runs in about a second. Nothing fails without the optional pieces; some tests skip instead, and none of them is a rule this harness decides anything by:

- **7 skip in a tree that has `runs/`.** 6 need `pier`: 2 check that the cost override is what inheritance resolves to and that it still delegates to the pure rule, 3 cover the file-opening shell around that rule, and 1 compares the override against pier's own implementation on the recorded stream. The 7th renders a prompt template through `jinja2`; the specific property it proves — that pier can render every arm's template with only `instruction` bound — is *also* checked by a stdlib equivalent that always runs, so that one property does not depend on jinja2 being installed.
- **19 skip in a fresh clone**, because `.gitignore` is exactly `runs/`: the recorded evidence is untracked, so 12 more tests that read it skip too. The test count is unchanged and the suite is still green — this is a visibility gap, not a correctness one. Fix 1's regression proof in particular survives: 13 of `tests/test_stream_cost.py`'s 14 tests still run from the committed 3 KB fixture, including the 22-event, `$0.392`-first, `$26.530`-max assertions; only the fixture-versus-original drift check needs `runs/`.

Run `uv run --with pytest python3 -m pytest tests/ -q` to execute everything (`pier` and `jinja2` both present), and re-measure any of the counts above with `python3 -m unittest discover -v`.

**Test coverage is narrower than "the test suite passes" might suggest — don't overclaim it.** Most tests cover pure functions in `collect.py`, `report.py` and `stream_cost.py`: Wilson confidence intervals, status classification, the completion-gate/question heuristic, cost-stream parsing, chart-geometry math, table formatting.

Judgment logic is deliberately kept out of `agent.py` for this reason. Anything importing `pier` is unreachable under the default command above, so a rule living there would have tests that *skip* rather than run — a green suite proving nothing. The cost rule therefore lives in `stream_cost.py` (stdlib `json` only) with `tests/test_stream_cost.py` covering it unconditionally, and `ClaudeCodeSadd._parse_total_cost_from_stream_json` is reduced to opening the file and calling it. Same split `collect.py` already uses for `plugin_load_error_from_init_event` / `incompleteness_reason_from_signals`. `tests/test_status_contract.py` closes the other end, deriving its expectations from `typing.get_args(collect.Status)` so a fifth trial status cannot be added without wiring it through `ArmAggregate` and `report.py`'s arm table. `tests/test_readme_claims.py` does the same for this file: it checks the cost table and the bounded claim drawn from it against the artifacts under `runs/`, that the quoted transcript line is verbatim, that the `error_reason` values line up with the code in both directions (every reason the code emits is named here, and every reason named here — including the templated `pier_exception:<category>:<type>` form — is one the code can produce), and that no superseded "nothing below is measured" disclaimer has crept back in — the two documentation defects this harness actually shipped. It does not check the test counts in this section; those are maintained by hand. Four files cover `run.py`, importing it via `tests/run_fixtures.py` (which stubs the `agent` module when `pier` isn't installed): `tests/test_run_dispatch.py` pins the preflight dispatch predicate (`has_subagent_dispatch`) — the tool-name matcher that decides whether a sub-agent was ever dispatched, there because that predicate silently broke on a claude-code tool rename (`Task` → `Agent`) while the whole suite stayed green — `tests/test_run_arm_matrix.py` pins the `--skill` and `--model` flags' arm-matrix filtering, preflight arm/job-name selection, and argparse validation, `tests/test_run_completion_gate.py` pins the PASS/INCOMPLETE/FAIL contract and its exit codes, and `tests/test_run_prompt_template.py` pins the prompt template (plugin arms still start with their slash command, both arm types carry identical contract text). `tests/test_agent_cost_parsing.py` is the one file covering `agent.py`, and now only what genuinely needs pier: the override's resolution order, that the method stayed a shell delegating to `stream_cost`, its file-reading edge cases, and an end-to-end comparison against upstream on the real recorded stream in `runs/`.

**Everything else in `run.py`, and the rest of `agent.py`, remains not unit-tested**: building the `pier run` command, checking out the plugin into a container, driving the container lifecycle. Those are exercised instead by `run.py --dry-run` (prints every command without executing anything) and `run.py --preflight` (actually runs one trial and verifies the plugin loaded and a sub-agent was dispatched). If you change `run.py`'s command-building or `agent.py`'s install steps, `--preflight` — not the test suite — is what tells you whether it still works.

## The schedule file (`schedule.yaml`)

`schedule.yaml` is the single source of truth for everything `--mode scheduled` runs: the task/model/skill matrix, the pacing between runs, the combinations deliberately left unrun, and the complexity label each task carries. `schedule.py` is the only code that reads it; `run.py --mode scheduled` executes exactly what it expands to, `collect.py` records every cell it declares (even an unrun one, with an honest absence reason — see [`results.json` schema v4](#resultsjson-schema-v4) below), and `report.py` groups its per-complexity charts by the labels it carries. Nothing downstream re-derives any of this: if a combination is not in the matrix the file expands to, it does not run, and if a cell is missing from the report, the schedule file is where the answer is.

It has five top-level sections, all required:

| Section | What it declares | Committed value |
|---|---|---|
| `models` | Named `(orchestrator, impl)` tier pairs, each pinned to one of `run.py`'s `CELLS` | 5: `haiku`, `sonnet`, `opus`, `sonnet-haiku`, `opus-sonnet` |
| `skills` | The arm types to schedule a task under | 3: `vanilla`, `do-and-judge`, `do-in-steps` |
| `duration` | Two pacing knobs: `between_runs` (gap after any finished trial, success or failure) and `technical_failure_backoff` (gap before a technical retry) | both `2h` |
| `tasks` | The deep-swe tasks in the sweep, each with an ordered `complexity` (`low`/`medium`/`high`) | 3: `kombu-single-active-consumer-priority` (high), `cattrs-partial-structuring-recovery` (medium), `abs-stepped-slices` (low) |
| `skips` | Combinations deliberately left unrun, each with a **mandatory** reason and an optional `tasks`/`models`/`skills` selector (omitted = "all") | 3 rules, covering 12 of the 45 expanded cells |

The matrix is every `(task, model, skill)` triple — 3 × 5 × 3 = **45 cells** for the committed file — and `expand_schedule` walks it in file declaration order (tasks outer, then models, then skills), checking each cell against the skip rules in the order they're written; the first rule that matches supplies the reason. A skipped cell stays in the expansion rather than being dropped, so the report can draw it as "deliberately not run, because X" instead of a gap the reader has to guess about.

`vanilla` is a real skill in this file's vocabulary even though `run.py` has no such string (its `SKILLS` constant holds only the two plugin skills, and models the no-plugin control as `Arm(skill=None, ...)`); `schedule.py` translates at the boundary, and `Arm.id`/`arm_id_for` agree exactly. One consequence worth knowing before editing `models` or `skips`: a vanilla arm has no implementer tier, so `sonnet-haiku` and `opus-sonnet` collapse onto their orchestrator's own vanilla arm (`vanilla__sonnet`, `vanilla__opus`) — running both would pay twice for one measurement, which is why the committed file's third skip rule excludes the two mixed pairs from `vanilla` outright.

`schedule.py` is deliberately unforgiving: it rejects unknown top-level or nested keys, duplicate names, an empty (as opposed to omitted) skip selector, and an unparseable duration, rather than defaulting past any of them. This isn't caution for its own sake — a schedule file that fails to validate stops a run before it starts money moving; one that validates but means the wrong thing produces a clean-looking run that measured something other than what was intended. The example the file's own comments give: `model:` typoed for `models:` in a skip rule silently widens that rule from one named model to every model, and nothing about the resulting run would look broken. `tests/test_schedule.py` loads the exact committed file and asserts it validates, so a bad edit fails the test suite before it fails a multi-day run.

## Scheduler outcomes, triage, and resumability

Every executed cell settles into exactly one of three scheduler outcomes — `triage.py`'s own vocabulary, deliberately distinct from `collect.py`'s four trial `status` values (`resolved`/`unresolved`/`incomplete`/`errored`, [documented above](#5-collect-results)): those describe *what a trial was*, these describe *what the scheduler does next*.

| Outcome | Meaning | Retried? |
|---|---|---|
| `success` | The verifier says the task was solved. | Never — terminal. |
| `model_failure` | The agent got a fair attempt and did not solve it (a real `unresolved`, or the completion gate fired — `no_model_patch`/`final_message_is_question`). | Never — terminal. Re-running a model failure would turn this benchmark's declared n=1 sweep into a quiet best-of-N. |
| `technical_failure` | The agent never got a fair, uncontaminated attempt: no trial `result.json` at all, a pier infrastructure exception, no verifier rewards, or an API-side refusal found in the transcript (see below). | Yes, up to the retry bound (next section) within one invocation — and again on a later invocation, since this outcome is never written down as final. |

The precedence `triage.verdict_from_signals` applies — and the one place it is genuinely hard — is deciding *technical* vs. *model failure* when pier reports an abnormal, non-zero process exit with no further explanation (pier's `NonZeroAgentExitCodeError`, which covers everything from a killed container to a crashed `claude` process to a genuine agent bug, all with the same exception type). The transcript is scanned first for two concrete signals of an API-side refusal — a `result` event's `api_error_status` set to anything but `null`, or a `rate_limit_event` whose `rate_limit_info.status` isn't `"allowed"` — and if either fires, the outcome is `technical_failure` regardless of what pier's own exit code said. **When the transcript offers no such evidence, the ambiguous case defaults to `technical_failure` too** (`triage.AMBIGUOUS_NONZERO_EXIT_REASON`, `ambiguous_nonzero_exit`), not to `model_failure`. The two possible mistakes are not symmetric: calling a real model failure "technical" costs one bounded, visible retry — expensive but self-limiting, and once the retry cap is spent the cell is honestly recorded as no data. Calling a real technical failure "a model failure" writes a permanent zero for a trial the model never fairly attempted, and resumability then guarantees it is never revisited — cheap in the moment, and silently corrupts the one number this benchmark exists to produce. So the default absorbs the bounded, visible cost rather than risk the silent, permanent one.

### `runs/scheduler-state.json`

Written at `<jobs-dir>/scheduler-state.json` (`runs/scheduler-state.json` for the default `--jobs-dir`), rewritten in full after every cell that reaches a terminal-for-this-invocation outcome:

```json
{
  "version": 1,
  "updated_at": "<ISO-8601 UTC>",
  "runs": {
    "<task>::<model>::<skill>": {
      "arm_id": "do-in-steps__opus-opus",
      "outcome": "success",
      "reason": "resolved",
      "attempts": 2,
      "recorded_at": "<ISO-8601 UTC>"
    }
  }
}
```

Keyed on `<task>::<model>::<skill>` — `schedule.yaml`'s own vocabulary for a planned run, not `arm_id` — because that identity survives a schedule edit that renames nothing, and because a vanilla cell's collapsed `arm_id` (see above) would otherwise let one state-file entry answer for two different planned cells. A file that is missing, unreadable, or written by a future `version` is treated as no record at all (run everything) rather than a reason to refuse to start: the safe direction costs money on a re-run, but can never silently drop a cell.

**`success` and `model_failure` are terminal across restarts — a cell recorded as either is never executed again short of `--force`.** `technical_failure` is deliberately NOT terminal: an operator restarting the scheduler after a quota window closed is explicitly asking for that cell to be tried again, and permanently abandoning it to a transient fault would lose real data.

### The retry bound and `--force`

Within one invocation, a technical failure is retried up to `scheduler.MAX_TECHNICAL_RETRIES` times — **2**, i.e. 3 attempts total per cell — waiting `technical_failure_backoff` (2h in the committed file) before each retry. There is no unbounded `while` loop anywhere in this path: the attempt count is a bounded `for` loop, so the total work one schedule can ever do is computable in advance (`len(runnable) * 3` executions, worst case). The bound is set to outlast the one quota window every recorded transcript in this repository actually shows (`"rateLimitType": "five_hour"`): two 2-hour backoffs plus the run time of the two failed attempts comfortably spans five hours, and it also caps how much the ambiguous-exit default above can cost — at most two extra executions of a cell, never an unbounded spend, if it turns out to have mis-triaged a genuine, repeated model crash as technical.

`--force` re-runs a cell (or, since `--mode scheduled` has no per-cell filter, every cell) even when the state file or an on-disk job directory already says it's done. **It is not, by itself, the fix for a stuck technical cell.** A cell whose job directory is already complete but keeps triaging `technical_failure` gets re-attempted on *every* invocation regardless of `--force` — the scheduler's own resume logic already falls through to executing it, because a technical verdict never counts as "done". The problem is that the re-attempt accomplishes nothing: pier's own resume logic (`Job._maybe_init_existing_job`) skips any trial whose directory already has a `result.json`, technical failure or not, so the "retry" just re-triages the same stale file and burns a full backoff for nothing — and `--force` changes none of that, because it only affects whether `run.py`/`scheduler.py` skip their *own* already-done check, not what pier does with an existing trial directory underneath it.

The actual fix is to remove that cell's job directory and re-run *without* `--force`, so the state-file fast path still settles every other cell instantly instead of replaying all of them through pier and re-paying the full pacing wait for each one. `report_scheduled_summary` (the end-of-run summary `--mode scheduled` prints) names these cells specifically — labelled `STUCK`, distinct from the generic `TECHNICAL FAILURE` line — and prints the exact command. Verbatim (only re-wrapped here for width; `run.py` prints it as one line):

```
[schedule] STUCK cattrs-partial-structuring-recovery / do-in-steps__opus-opus: api_fault:api_error_status=529 -- pier
will keep skipping this trial's existing result.json on every future invocation, so retries alone will not clear it.
`--force` alone will not either: it only skips run.py's own already-done check, and pier's per-trial resume still
skips the trial underneath it. Remove the job directory first, then re-run WITHOUT --force (every other cell is
still terminal and settles instantly from the state file; --force would instead replay all of them through pier
and re-pay the pacing wait between each one):
    rm -rf runs/do-in-steps__opus-opus__cattrs-partial-structuring-recovery && uv run python3 run.py --mode scheduled
```

The one technical reason this does NOT apply to is `no_trial_result` — pier never wrote a trial `result.json` at all (a container or environment that never came up), so there is nothing on disk for its resume logic to skip, and the very next invocation genuinely re-attempts it. Every other technical reason (`api_fault:...`, `missing_verifier_rewards`, `pier_exception:...`, `ambiguous_nonzero_exit`) means a trial DID finish and write a `result.json`, which is exactly the STUCK case above.

## `results.json` schema v4

`collect.RESULTS_SCHEMA_VERSION` / `report.EXPECTED_RESULTS_SCHEMA_VERSION` are both **4**, and the two are asserted equal in the test suite so they cannot drift apart. Versions 2 and 3 are documented in `collect.py`'s own docstring (`created_at`/`sample_seed` on each arm; the `incomplete` status and its `n_incomplete`/`max_cost_usd` fields). Version 4 is the step where `report.py` learned to actually draw the three sections below — they were added as purely additive top-level keys before this version and could be safely ignored by an older reader, but from v4 on a reader is entitled to expect them:

- **`cells`** — one entry per `(task, model, skill)` triple the schedule declares (plus any "extra" cell `collect.py` finds recorded under `runs/` that the schedule does not — kept, not dropped, with `in_schedule: false`). Each entry carries `state` — one of the [five cell states](#report-visual-grammar) below — plus `measured` (populated only when `state == "measured"`; `null` otherwise, so a consumer that forgets to check `state` gets a `TypeError` rather than a plausible zero) and `absence` (populated for every other state, naming why). This is what lets the report draw a matrix that is mostly still `not_yet_run` without lying about what it knows.
- **`schedule`** — the expanded matrix itself: every declared task (with its complexity and rank), model pair, and skill; `n_planned_cells` (45 for the committed file); the path to `scheduler-state.json` and whether it currently exists; and `task_name_reconciliation`, which records how each trial's pier-side task spelling (e.g. `datacurve/abs-stepped-slices`) was resolved back to `schedule.yaml`'s own name for it.
- **`baseline`** — the vendored Fable 5 snapshot (`baseline.fable5`), read for the per-task DeepSWE comparison. See [Fable 5, the per-task comparison](#fable-5-the-per-task-comparison) below for what it is and how it is (and is deliberately not) drawn.

## Report visual grammar

The per-task and per-complexity charts (cost, tokens, Pass@1 by complexity) draw every cell of the schedule's matrix, not just the measured ones, so most of what they draw is an explanation of absence rather than a value. Every cell is in exactly one of **five states**, each with its own mark:

| Cell state | Mark |
|---|---|
| `measured`, value > 0 | A filled bar in the skill's categorical hue, height proportional to the value. |
| `measured`, value == 0.0 | The same filled hue bar, clamped to a 4px minimum visible height (see below) — a real measurement, never collapsed into an absence. |
| `deliberately_skipped` | A full-height hatched slot with a `⊘` glyph — `schedule.yaml` excluded this cell, with a stated reason. |
| `structurally_impossible` | A full-height hatched slot with a `≡` glyph — there is no such trial to run (a mixed model pair's vanilla cell, which collapses onto its orchestrator's own vanilla arm). |
| `technical_failure` | A full-height hatched slot with a `⚠` glyph — attempted, but never fairly attempted (every trial was an infra failure, or the scheduler recorded one). |
| `not_yet_run` | One faint dot sitting on the baseline, still reachable on hover — no data, because nobody has run it yet. |

(A sixth, `not_in_schedule`, exists only in `report.py`'s own rendering vocabulary — for a cell `results.json` carries no entry for at all, meaning the combination was never scheduled in the first place. It draws the same faint dot as `not_yet_run` but is never confused with it in the legend or the coverage table.)

**The complexity chart's two-channel encoding**: hue encodes *skill* (the same categorical palette the other charts use) and marker shape encodes *model* (`assign_model_marker_shapes`, one of `circle`/`square`/`triangle`/`diamond`/`cross` per model, in schedule declaration order). Splitting the two channels is what fits up to 15 (model × skill) series onto a chart without exceeding the palette's validated 3-hue cap.

**The connector rule**: a line is drawn joining one series' points ONLY across a run of two or more adjacent, measured complexity levels — never across an unmeasured level in between (a series measured at `low` and `high` but not `medium` draws as two separate marks, never one line skipping over the gap it would otherwise assert), and never for a single lone point. If every point behind a series is a single trial, the whole line is drawn faded and dashed (`connector-provisional`) rather than solid, because a line read end to end that is anchored on even one 0-or-1 observation is not a claim the data supports; a series backed entirely by multi-trial points draws a solid line (`connector-solid`).

**The 4px zero-floor**: `CELL_CHART_GEOMETRY.min_measured_height` is 4px. Without it, a genuinely measured `0.0` (the agent tried and solved nothing) would render pixel-identical to an absent cell — nothing above the baseline either way. With it, every measured bar — including a true zero — gets at least 4px of visible height. The trade this makes explicit on the page (in the footnote beside every chart the floor applies to): a floored bar means "measured, and very small" rather than necessarily zero, because a genuinely tiny non-zero value (a $0.14 cost cell against a $40 axis, say) floors to the exact same height as a true zero. The exact figure is always in the per-task table underneath the chart, which never floors anything.

**The empty-state sentence**: when every cell a per-task or per-complexity chart could draw is absent (`all_cells_absent`), `report.py` prepends a plain-language line above the figure — "No cell here has been measured yet: all N are `<count> <absence label>`, ..." (`empty_cell_chart_note`, built from the same per-state counts and labels the chart's own legend uses) — instead of leaving a wall of hatched marks with no summary to explain itself.

**Axis ceilings**: the cost/token charts' y-axis never gridlines on the raw maximum value. `round_up_to_readable_ceiling` rounds up to the smallest "nice" ceiling (1/2/2.5/5/10 × a power of ten) whose four equal gridlines all land on round numbers, so a raw max of $22.54 labels its axis "$10, $20, $30, $40", not "$5.63, $11.27, $16.90, $22.54".

**The Arm results table's `(n=N)` suffix**: every non-empty "Pass@1 ± CI" cell in the Arm results table carries its attempt count, e.g. "0% ± 40% (n=1)" (`format_arm_pass_at_1_cell`) — the same "a rate needs its denominator" rule the per-cell table already states, applied here so a wide Wilson interval over a single attempt cannot be misread as an established measurement.

## Regenerating `data/leaderboard.json`

The file documents its own regeneration procedure in its `_comment` field: *"Do not hand-edit -- regenerate by re-fetching `source_data_url` and re-applying `row_selection_rule`, then update `snapshot_date`."* Concretely:

1. Re-fetch `source_data_url` (`https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`) for current data.
2. Re-apply `row_selection_rule`: DeepSWE's own site runs each model at several `reasoning_effort` configs (`low`/`medium`/`high`/`xhigh`/`max`) and its live-leaderboard UI shows one row per model — the one at the **highest available `reasoning_effort`**. Reproduce that same selection so the vendored numbers match what a visitor to the site sees by default.
3. Update `snapshot_date` to the date you regenerated it.

The file also records `harness` (`mini-swe-agent`), `data_version`, and per-tier `absence_reason` when a tier genuinely isn't on the leaderboard (e.g. haiku, as of the current snapshot — there is no `claude-haiku-*` row anywhere in the fetched dataset) — carry these through rather than inventing values for a tier that's actually missing.

## The official leaderboard numbers are not comparable to this harness's own arms

Say this plainly, because `report.html` puts both on the same chart: **every "official" number comes from `data/leaderboard.json`, which benchmarks models with `mini-swe-agent` — a minimal single-agent scaffold, not `claude-code` running the `sadd` plugin this harness measures.** `mini-swe-agent` and `claude-code` differ in tool access, context management, and prompting. The official bars are useful context for where a raw model tier sits on an independent benchmark; they are **not** a like-for-like comparison against this harness's own plugin/vanilla arms. `report.py` renders the official bars with different visual treatment specifically for this reason (unfilled/outlined, never the same categorical color as this harness's own arms, and never carrying a whisker — see below) and prints the leaderboard's own `honesty_note` as a footnote wherever an official bar appears — read it there too, not just here.

## Fable 5, the per-task comparison

`results.json`'s `baseline.fable5` section (vendored from DeepSWE's own published v1.1 artifacts, `data/fable5_official.json`) carries a second, more specific official comparison than the aggregate leaderboard bars above: a per-task and whole-benchmark figure for one specific model, DeepSWE's site id `claude-fable-5`. Three facts about it matter for reading the report correctly:

1. **It ran on `mini-swe-agent`, not `claude-code`.** Same harness mismatch as every other official number in this file (see above) — `claude-fable-5` is a model, benchmarked with a different scaffold than the one this harness measures, so it is context for where that model sits on DeepSWE's own benchmark, not a peer arm.
2. **Its figures are k-of-n over scored rollout attempts, never a single pass/fail.** DeepSWE runs each task 4 times per reasoning effort across 5 efforts (20 attempts per task); this harness reads two views of that — `all_efforts_pooled` (pooled across all 20) and `headline_config_max` (the 4 attempts at the site's headline `reasoning_effort`, `"max"`) — and always displays a count (`"13/20"`, `"4/4"`), never a bare rate. Every Fable 5 bar carries this count as its own printed `display` label, the same treatment every other present bar on the page carries (see [Report visual grammar](#report-visual-grammar)).
3. **Its confidence interval is a run-to-run standard error across 4 whole-benchmark passes, NOT a Wilson interval** — a different statistic over a different denominator (`scored_rollout_attempts`, not `local_trial_attempts`) than the Wilson interval this harness computes for its own arms. `results.json` labels this explicitly (`baseline.fable5.comparability.co_plotting_intervals_allowed: false`, `interval_type: "run_to_run_standard_error_across_whole_benchmark_passes"`), and `report.py` honors it structurally: **no Fable 5 bar, anywhere in the report, ever carries `ci_low`/`ci_high`.** `fable5_pass_bar`/`fable5_measure_bar`/`fable5_aggregate_bar` never set them, so there is nothing for `render_bar_mark`'s whisker branch to draw — the interval is folded into the bar's own count/percentage label as text instead, and the aggregation charts' comparison table states the two interval types side by side in prose rather than co-plotting them as if they were peers. The aggregate leaderboard bars discussed above get the identical treatment for the identical reason: outlined, labelled by text, never a whisker in the same channel as this harness's own Wilson bounds.

Where it appears: the per-task cost/token charts' outlined bar (labelled by count or dollar amount), the two aggregation charts' `Fable 5` x-axis column (the model's whole-benchmark headline figure), and the "Fable 5 vs. this harness, per task" table under "Official baseline" — which states both DeepSWE's `all_efforts_pooled`/`headline_config_max` counts and this harness's own local result side by side, with a footnote (`render_fable5_footnote`, sourced from `baseline.fable5.comparability`/`source`) repeating the harness-mismatch and interval-incomparability facts above wherever the comparison appears.
