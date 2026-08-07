---
name: plan-task
description: Refine, parallelize, and verify a draft task specification into a fully planned implementation-ready task
argument-hint: Path to draft task file (e.g., ".specs/tasks/draft/add-validation.feature.md") [--continue] [--refine] [--target-quality] [--max-iterations] [--included-stages] [--skip] [--fast] [--strict] [--model haiku|sonnet|opus]
---

# Refine Task Workflow

## Role

You are a task refinement orchestrator. Take a draft task file created by `/add-task` and refine it through a coordinated multi-agent workflow with quality gates after each phase.

## Goal

This workflow command refines an existing draft task through:

1. **Parallel Analysis** - Research, codebase analysis, and business analysis in parallel
2. **Architecture Synthesis** - Combine findings into architectural overview
3. **Decomposition** - Break into implementation steps with risks
4. **Parallelize** - Reorganize steps for maximum parallel execution
5. **Verify** - Add LLM-as-Judge verification sections
6. **Promote** - Move refined task from `draft/` to `todo/`

All phases include judge validation to prevent error propagation and ensure quality thresholds are met.

## User Input

```text
$ARGUMENTS
```

---

## Command Arguments

Parse the following arguments from `$ARGUMENTS`:

### Argument Definitions

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task-file` | Path to task file | **Required** | Path to draft task file (e.g., `.specs/tasks/draft/add-validation.feature.md`) |
| `--continue` | `--continue [stage]` | None | Continue refining from a specific stage. Stage is optional - resolve from context if not provided. |
| `--target-quality` | `--target-quality X.X` | `3.5` | Target threshold value (out of 5.0) for judge pass/fail decisions. |
| `--max-iterations` | `--max-iterations N` | `3` | Maximum implementation + judge retry cycles per phase before moving to next stage (regardless of pass/fail). |
| `--included-stages` | `--included-stages stage1,stage2,...` | All stages | Comma-separated list of stages to include. |
| `--skip` | `--skip stage1,stage2,...` | None | Comma-separated list of stages to exclude. |
| `--fast` | `--fast` | N/A | Alias for `--target-quality 3.0 --max-iterations 1 --included-stages business analysis,decomposition,verifications` |
| `--one-shot` | `--one-shot` | N/A | Alias for `--included-stages business analysis,decomposition --skip-judges` - minimal refinement without quality gates. |
| `--human-in-the-loop` | `--human-in-the-loop phase1,phase2,...` | None | Phases after which to pause for human verification. |
| `--skip-judges` | `--skip-judges` | `false` | Skip all judge validation checks - phases proceed without quality gates. |
| `--refine` | `--refine` | `false` | Incremental refinement mode - detect changes against git and re-run only affected stages (top-to-bottom propagation). |
| `--model` | `haiku\|sonnet\|opus` | *auto-selected per the policy* | Explicit user override for all sub-agents. When omitted, resolve each phase's tier per the [Model Selection Policy](#model-selection-policy). See [Role Pairing](#role-pairing) for the override's effect and the [Escalation Rule](#escalation-rule) for how escalation interacts with it. |
| `--strict` | `--strict` | `false` | Disable the [Iteration Discretion Rule](#iteration-discretion-rule) - a phase passes ONLY when `score >= THRESHOLD`, otherwise retry until `MAX_ITERATIONS` is reached. |

### Stage Names (for `--included-stages` / `--skip`)

| Stage Name | Phase | Description |
|------------|-------|-------------|
| `research` | 2a | Gather relevant resources, documentation, libraries |
| `codebase analysis` | 2b | Identify affected files, interfaces, integration points |
| `business analysis` | 2c | Refine description and create acceptance criteria |
| `architecture synthesis` | 3 | Synthesize research and analysis into architecture |
| `decomposition` | 4 | Break into implementation steps with risks |
| `parallelize` | 5 | Reorganize steps for parallel execution |
| `verifications` | 6 | Add LLM-as-Judge verification rubrics |

### Configuration Resolution

Parse `$ARGUMENTS` and resolve configuration as follows:

```

# Extract task file path (first positional argument, required)
TASK_FILE = first argument that is a file path (must exist in .specs/tasks/draft/)

# Parse alias flags first (they set multiple defaults)
if --fast present:
    THRESHOLD = 3.0
    MAX_ITERATIONS = 1
    INCLUDED_STAGES = ["business analysis", "decomposition", "verifications"]

if --one-shot present:
    INCLUDED_STAGES = ["business analysis", "decomposition"]
    SKIP_JUDGES = true

# Initialize defaults
THRESHOLD ?= --target-quality || 3.5
MAX_ITERATIONS ?= --max-iterations || 3
INCLUDED_STAGES ?= --included-stages || ["research", "codebase analysis", "business analysis", "architecture synthesis", "decomposition", "parallelize", "verifications"]
SKIP_STAGES = --skip || []
HUMAN_IN_THE_LOOP_PHASES = --human-in-the-loop || []
SKIP_JUDGES = --skip-judges || false
REFINE_MODE = --refine || false
STRICT_MODE = --strict || false
CONTINUE_STAGE = null

# Model tiers - governed in full by the Model Selection Policy
MODEL_OVERRIDE = --model || null
BASELINE_TIER = MODEL_OVERRIDE || tier of the overall task per the Selection Rules


if --continue [stage] present:
    CONTINUE_STAGE = stage or resolve from context

# Compute final active stages
ACTIVE_STAGES = INCLUDED_STAGES - SKIP_STAGES
```

### Context Resolution for `--continue`

When `--continue` is used without explicit stage:

1. **Stage Resolution:**
   - Parse the task file for completion markers (e.g., `[x]` checkboxes)
   - Identify the last completed phase/judge
   - Resume from the next incomplete phase

### Refine Mode Behavior (`--refine`)

When `--refine` is used:

1. **Change Detection:**
   - First check file status: `git status --porcelain -- <TASK_FILE>`
   - Compare current task file against last git commit: `git diff HEAD -- <TASK_FILE>`
     - This captures both staged and unstaged changes vs HEAD
   - If file is untracked or has no git history, compare against the original task structure
   - Identify which sections have been modified by the user
   - Look for `//` comment markers indicating user feedback/corrections

2. **Top-to-Bottom Propagation:**
   - Determine the **earliest modified section** (highest in document)
   - Re-run only stages that correspond to or come **after** the modified section
   - Earlier stages (above the modification) are preserved as-is

3. **Section-to-Stage Mapping:**

   | Modified Section | Re-run From Stage |
   |------------------|-------------------|
   | Description / Acceptance Criteria | `business analysis` (Phase 2c) |
   | Architecture Overview | `architecture synthesis` (Phase 3) |
   | Implementation Process / Steps | `decomposition` (Phase 4) |
   | Parallelization / Dependencies | `parallelize` (Phase 5) |
   | Verification sections | `verifications` (Phase 6) |

4. **Refine Execution:**
   - Skip research (2a) and codebase analysis (2b) unless explicitly requested
   - Pass user modifications and `//` comments as additional context to agents
   - Agents should incorporate user feedback while preserving unchanged content

5. **Example:**

   ```bash
   # User edited the Architecture Overview section
   /plan .specs/tasks/todo/my-task.feature.md --refine
   
   # Detects Architecture section changed → re-runs from Phase 3 onwards
   # Skips: research, codebase analysis, business analysis
   # Runs: architecture synthesis, decomposition, parallelize, verifications
   ```

### Human-in-the-Loop Behavior

Human verification checkpoints occur:

1. **Trigger Conditions:**
   - After implementation + judge verification **PASS** for a phase in `HUMAN_IN_THE_LOOP_PHASES`
   - After implementation + judge + implementation retry (before the next judge retry)

2. **At Checkpoint:**
   - Display current phase results summary
   - Display generated artifacts with paths
   - Display judge score and feedback
   - Ask user: "Review phase output. Continue? [Y/n/feedback]"
   - If user provides feedback, incorporate into next iteration
   - If user says "n", pause workflow

3. **Checkpoint Message Format:**

   ```markdown
   ---
   ## 🔍 Human Review Checkpoint - Phase X

   **Phase:** {phase name}
   **Judge Score:** {score}/{THRESHOLD} threshold
   **Status:** ✅ PASS / ☑️ ACCEPTED / ⚠️ RETRY {n}/{MAX_ITERATIONS}

   **Artifacts:**
   - {artifact_path_1}
   - {artifact_path_2}

   **Judge Feedback:**
   {feedback summary}

   **Action Required:** Review the above artifacts and provide feedback or continue.

   > Continue? [Y/n/feedback]:
   ---
   ```

---

## Usage Examples

```bash
# Refine a draft task with all stages
/plan .specs/tasks/draft/add-validation.feature.md

# Fast refinement with minimal stages
/plan .specs/tasks/draft/quick-fix.bug.md --fast

# Continue from a specific stage
/plan .specs/tasks/draft/complex-feature.feature.md --continue decomposition

# High-quality refinement with checkpoints
/plan .specs/tasks/draft/critical-api.feature.md --target-quality 4.5 --human-in-the-loop 2,3,4,5,6

# Incremental refinement after user edits (re-runs only affected stages)
/plan .specs/tasks/todo/my-task.feature.md --refine

# Strict mode: never accept a phase below target - retry until THRESHOLD or MAX_ITERATIONS
/plan .specs/tasks/draft/critical-api.feature.md --strict
```

## Pre-Flight Checks

Before starting workflow:

1. **Validate task file exists:**
   - If `REFINE_MODE` is false: Check that `TASK_FILE` exists in `.specs/tasks/draft/`
   - If `REFINE_MODE` is true: Check that `TASK_FILE` exists in `.specs/tasks/todo/` or `.specs/tasks/draft/`
   - If not found, show error and exit

2. **Parse and display resolved configuration:**

   ```markdown
   ### Configuration

   | Setting | Value |
   |---------|-------|
   | **Task File** | {TASK_FILE} |
   | **Target Quality** | {THRESHOLD}/5.0 |
   | **Max Iterations** | {MAX_ITERATIONS} |
   | **Active Stages** | {ACTIVE_STAGES as comma-separated list} |
   | **Human Checkpoints** | Phase {HUMAN_IN_THE_LOOP_PHASES as comma-separated} |
   | **Skip Judges** | {SKIP_JUDGES} |
   | **Refine Mode** | {REFINE_MODE} |
   | **Strict Mode** | {STRICT_MODE} |
   | **Continue From** | {CONTINUE_STAGE} or "Start" |
   | **Model** | `{MODEL_OVERRIDE}` (user override) or "auto — baseline `{BASELINE_TIER}`: {one-line justification}" |
   ```

3. **Handle `--continue` mode:**

   If `CONTINUE_STAGE` is set:
   - Read the task file to get current state
   - Identify completed phases from task file content
   - Skip to `CONTINUE_STAGE` (or auto-detected next incomplete stage)
   - Pre-populate captured values from existing artifacts
   - Resume workflow from the appropriate phase

4. **Handle `--refine` mode:**

   If `REFINE_MODE` is true:
   - Check file status: `git status --porcelain -- <TASK_FILE>`
     - `M` (staged) or `M` (unstaged) or `MM` (both) → proceed with diff
     - `??` (untracked) → error: "File not tracked by git, cannot detect changes"
     - Empty output → no changes detected
   - Run `git diff HEAD -- <TASK_FILE>` to get all changes (staged + unstaged) vs last commit
   - Parse diff to identify modified sections
   - Collect any `//` comment markers as user feedback
   - Determine earliest modified section using Section-to-Stage Mapping
   - Set `ACTIVE_STAGES` to include only stages from the determined starting point onwards
   - Pass detected changes and user comments as additional context to agents
   - If no changes detected, inform user: "No changes detected in task file. Edit the file first, then run --refine." and exit

5. **Extract task info from file:**
   - Read task file to extract title and type from filename
   - Parse frontmatter for title and depends_on

6. **Initialize workflow progress tracking** using TodoWrite:

   Only include todos for phases in `ACTIVE_STAGES`. If continuing, mark completed phases as `completed`.

   ```json
   {
     "todos": [
       {"content": "Ensure directories exist", "status": "pending", "activeForm": "Ensuring directories exist"},
       {"content": "Phase 2a: Research relevant resources and documentation", "status": "pending", "activeForm": "Researching resources"},
       {"content": "Judge 2a: PASS research quality (> {THRESHOLD})", "status": "pending", "activeForm": "Validating research"},
       {"content": "Phase 2b: Analyze codebase impact and affected files", "status": "pending", "activeForm": "Analyzing codebase impact"},
       {"content": "Judge 2b: PASS codebase analysis (> {THRESHOLD})", "status": "pending", "activeForm": "Validating codebase analysis"},
       {"content": "Phase 2c: Business analysis and acceptance criteria", "status": "pending", "activeForm": "Analyzing business requirements"},
       {"content": "Judge 2c: PASS business analysis (> {THRESHOLD})", "status": "pending", "activeForm": "Validating business analysis"},
       {"content": "Phase 3: Architecture synthesis from research and analysis", "status": "pending", "activeForm": "Synthesizing architecture"},
       {"content": "Judge 3: PASS architecture synthesis (> {THRESHOLD})", "status": "pending", "activeForm": "Validating architecture"},
       {"content": "Phase 4: Decompose into implementation steps", "status": "pending", "activeForm": "Decomposing into steps"},
       {"content": "Judge 4: PASS decomposition (> {THRESHOLD})", "status": "pending", "activeForm": "Validating decomposition"},
       {"content": "Phase 5: Parallelize implementation steps", "status": "pending", "activeForm": "Parallelizing steps"},
       {"content": "Judge 5: PASS parallelization (> {THRESHOLD})", "status": "pending", "activeForm": "Validating parallelization"},
       {"content": "Phase 6: Define verification rubrics", "status": "pending", "activeForm": "Defining verifications"},
       {"content": "Judge 6: PASS verifications (> {THRESHOLD})", "status": "pending", "activeForm": "Validating verifications"},
       {"content": "Move task to todo folder", "status": "pending", "activeForm": "Promoting task"},
       {"content": "Human checkpoint reviews", "status": "pending", "activeForm": "Awaiting human review"}
     ]
   }
   ```

   **Note:** Filter todos based on configuration:
   - If `SKIP_JUDGES` is true, omit ALL Judge todos (Judge 2a, 2b, 2c, 3, 4, 5, 6)
   - If `research` not in `ACTIVE_STAGES`, omit Phase 2a and Judge 2a todos
   - If `codebase analysis` not in `ACTIVE_STAGES`, omit Phase 2b and Judge 2b todos
   - If `business analysis` not in `ACTIVE_STAGES`, omit Phase 2c and Judge 2c todos
   - If `architecture synthesis` not in `ACTIVE_STAGES`, omit Phase 3 and Judge 3 todos
   - If `decomposition` not in `ACTIVE_STAGES`, omit Phase 4 and Judge 4 todos
   - If `parallelize` not in `ACTIVE_STAGES`, omit Phase 5 and Judge 5 todos
   - If `verifications` not in `ACTIVE_STAGES`, omit Phase 6 and Judge 6 todos
   - If `HUMAN_IN_THE_LOOP_PHASES` is empty, omit human checkpoint todo

7. **Ensure directories exist**:

   Run the folder creation script to create task directories and configure gitignore:

   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/create-folders.sh
   ```

   This creates:

   - `.specs/tasks/draft/` - New tasks awaiting analysis
   - `.specs/tasks/todo/` - Tasks ready to implement
   - `.specs/tasks/in-progress/` - Currently being worked on
   - `.specs/tasks/done/` - Completed tasks
   - `.specs/scratchpad/` - Temporary working files (gitignored)
   - `.specs/analysis/` - Codebase impact analysis files
   - `.claude/skills/` - Reusable skill documents

Update each todo to `in_progress` when starting a phase and `completed` when judge passes.

## CRITICAL

- Never record a verdict the judge report does not support: no PASS without a passing rubric result, and no ☑️ ACCEPTED without the [Iteration Discretion Rule](#iteration-discretion-rule) actually permitting it. Otherwise retry the judge after each implementation change till it passes the check!
- Do not read task files in .claude or .specs directories, your job is orchestrate agents that will do the work, not do it by yourself!
- Use `THRESHOLD` (default 3.5) for all judge pass/fail decisions, not hardcoded values!
- Use `MAX_ITERATIONS` (default 3) for retry limits, not hardcoded values!
- **After `MAX_ITERATIONS` reached: PROCEED to next stage automatically - do NOT ask user unless phase is in `HUMAN_IN_THE_LOOP_PHASES`!**
- Skip phases not in `ACTIVE_STAGES` entirely - do not launch agents for excluded stages!
- Trigger human-in-the-loop checkpoints ONLY after phases in `HUMAN_IN_THE_LOOP_PHASES`!
- **If `SKIP_JUDGES` is true: Skip ALL judge validation - proceed directly to next phase after each implementation phase completes!**
- **Task file must exist in `.specs/tasks/draft/` before running this command (unless `--refine` mode)!**
- **If `REFINE_MODE` is true: Detect changes via git diff, skip unchanged stages, pass user feedback to agents!**
- **If `STRICT_MODE` is true: The [Iteration Discretion Rule](#iteration-discretion-rule) is DISABLED - a phase passes ONLY on `score >= THRESHOLD`, otherwise retry until `MAX_ITERATIONS`!**

### Execution & Evaluation Rules

- **Use foreground agents only**: Do not use background agents. Launch parallel agents when possible. Background agents constantly run in permissions issues and other errors.

Relaunch judge till you get valid results, of following happens:

- Reject Long Reports: If an agent returns a very long report instead of using the scratchpad as requested, reject the result. This indicates the agent failed to follow the "use scratchpad" instruction.
- Judge Score 5.0 is a Hallucination: If a judge returns a score of 5.0/5.0, treat it as a hallucination or lazy evaluation. Reject it and re-run the judge. Perfect scores are practically impossible in this rigorous framework.
- Reject Missing Scores: If a judge report is missing the numerical score, reject it. This indicates the judge failed to read or follow the rubric instructions.

#### Iteration Discretion Rule

Your main task is to COMPLETE the planning within target quality. Two failure modes are equally real:

- Burning iterations and context on nitpicks so the overall task never completes → **the task is failed**.
- Promoting a plan whose quality is genuinely too poor to be considered complete → **an even worse failure**.

This rule governs the `**Decision Logic:**` block of every phase:

- **`score < 3.0` → FAIL, unconditionally. No discretion.** Re-launch the phase with judge feedback until it passes or `MAX_ITERATIONS` is reached.
- **`3.0 <= score < 5.0` → discretion band.** ONLY inside this band MAY you decide that a phase below `THRESHOLD` (default 3.5) is acceptable.
- **Bounded drop:** NEVER accept a score more than `1.0` below `THRESHOLD` — the effective floor is `max(3.0, THRESHOLD - 1.0)`, i.e. `3.0` at the default `THRESHOLD` 3.5 and `3.5` at `--target-quality 4.5`. With `THRESHOLD <= 3.0` (e.g. `--fast`) there is no discretion band at all.
- Inside the band, when the outstanding issues are ONLY `Low`/`Medium` priority (any `High` or `Critical` finding removes discretion entirely) AND none of them breaks a target requirement of the phase or causes a meaningful defect (i.e. they are nitpicks), you MUST reason FIRST — before re-launching the phase — about whether iterating (or marking the phase failed) is worth the time and context cost.
- **At most ONE nitpick-driven iteration**, and it counts against `MAX_ITERATIONS`. If it again surfaces only nitpicks, you MUST mark the phase PASS (☑️ ACCEPTED in the summary table), report the outstanding issues in the completion summary, and continue with the next phase. If it returns a score below the floor `max(3.0, THRESHOLD - 1.0)`, the FAIL path applies instead.
- You MUST be critical, NOT lenient. Stopping short of target MUST be an intentional decision grounded in the absence of real, requirement-breaking issues. A genuine blocking issue that prevents completing the phase within `MAX_ITERATIONS` MUST be reported as a failure, never papered over.
- **If `STRICT_MODE` is true, this whole rule is DISABLED**: stop only when `score >= THRESHOLD` or `MAX_ITERATIONS` is reached. `--strict` changes nothing else — `THRESHOLD`, `MAX_ITERATIONS`, the `< 3.0` unconditional FAIL, human-in-the-loop checkpoints, judge dispatch and `--skip-judges` are unaffected. With `--skip-judges` (or `--one-shot`) no score is produced at all, so both this rule and `--strict` are inert.

## Model Selection Policy

Picking the model is the **single highest-leverage decision** you make — more than any prompt wording, it decides whether the plan comes back correct and how long the run takes. You MUST NOT treat it as a formality: name the tier and give a one-line justification before dispatching **each** phase agent. Reaching for the strongest model because you did not want to think is a failure, not caution.

**Tier default:** `sonnet` is the working default, and `sonnet`/`haiku` cover the majority of runs. `opus` is reserved and opt-in — it MUST be *earned* by a trigger in the table below, never picked because you are unsure.

### Selection Rules

Assess the **overall task being planned** — the draft task file's title and type plus the user's input — against this table. The matching row is the run's `BASELINE_TIER`. (The same table also tiers a *single unit of work*, which is how Judge 5 grades the per-step model assignments produced by Phase 5.)

| Task shape | Tier | Examples |
|---|---|---|
| **Straightforward** — one already-understood change with an obvious shape: a single file, and an established pattern, no new dependency, no open design question, and "done" is already evident from the draft | `haiku` | Fix a typo in one README, add a config flag, bump a dependency version, correct a log message |
| **Typical** — ordinary feature, fix or refactor work: a handful of files inside one module or service, established patterns, local design choices only | `sonnet` | Add a REST endpoint to an existing service, add form validation, extract a helper and its tests |
| **Complex** — **breadth** (~3+ modules/services, or any breadth when a shared contract changes) OR **critical domain** (auth, payments/billing, data integrity, irreversible migration, public API break) OR **open design** (concurrency, non-trivial algorithms, a new subsystem, architecture not yet decided) | `opus` | Re-architect the payments subsystem across 12 modules, design a new event pipeline, plan a schema migration |

**Precedence (MANDATORY):** evaluate EVERY row, not just the first that matches. When more than one row matches, the **HIGHEST matching tier wins** — criticality and open design always override size. The **critical domain** list is exhaustive, not illustrative: shipping to production, touching real users, or *adding* to an existing public API are NOT triggers, so a new endpoint with validation in one service stays `sonnet`. **Mechanical-breadth carve-out:** breadth alone is not complexity — for one identical, rule-driven edit repeated across many files with no logic and no contract change, only the **breadth** trigger does not apply (critical domain and open design still do); tier it on a **single occurrence**, so a mechanical rename across 40 files is `haiku`, while the same rename confined to `src/auth/` is `opus`.

**Tie-breaker:** ONLY when no row matches cleanly — the task sits genuinely between two tiers — pick `sonnet`, the working default. You MUST NOT bias up to `opus` to hedge; the [Escalation Rule](#escalation-rule) makes a modest first guess recoverable, and one recovered phase costs far less than over-provisioning every phase of every run.

### Phase Weighting

`BASELINE_TIER` is the tier of **every** model-assigned phase, with exactly one stated deviation:

| Phase | Weight | Tier |
|---|---|---|
| Phase 3: Architecture Synthesis | **Heavy** — the only phase that makes open design decisions rather than applying settled ones; three inputs are synthesized here and every later phase, plus the implementation itself, inherits the result | **one tier above `BASELINE_TIER`**, capped at `opus` |
| Phases 2a, 2b, 2c, 4, 5, 6 | Standard | `BASELINE_TIER` |

Every model-assigned phase appears in exactly ONE row, so each resolves to exactly ONE tier. The cap means an `opus` baseline leaves all phases at `opus`. Phase 7 (Promote) is a file move you perform yourself — no sub-agent, no tier. See [Role Pairing](#role-pairing) for the `--model` override.

### Role Pairing

This pipeline has two model-assigned roles per phase: the **producer** (the phase agent) and the **evaluator** (its judge). **A judge ALWAYS runs at the tier of the phase it validates**, including after escalation. You MUST NOT tier a judge independently of its phase.

**An explicit `--model` supersedes this entire policy (the ONLY statement of this rule):** every phase agent and every judge runs at the user's tier, the `BASELINE_TIER` assessment does NOT run, and [Phase Weighting](#phase-weighting) never deviates from it.

### Escalation Rule

Bump **BOTH the phase agent and its judge** one tier for the next iteration of that phase when either trigger fires:

1. **Low first-iteration quality** — a low score, or judge issues showing the model misunderstood the phase rather than merely missing details.
2. **The user complains** that quality is too low or the results are wrong — at any point, including after a reported PASS or a finished run.

Ladder: `haiku` → `sonnet` → `opus`. `opus` is the **ceiling** — there is no further tier. If `opus`-tier work still fails, report it and escalate to the **user**; never loop.

- **Sole exception — hold the tier (the ONLY statement of this rule, trigger (1) only):** when trigger (1) fires but the judge's issues are a specific, fixable defect rather than a capability gap (narrow, precisely specified problems the model clearly understood), you MAY hold the tier and re-launch the phase at the SAME tier with the judge's exact feedback instead of bumping. This is the ONLY circumstance in which the bump under trigger (1) is not mandatory; in every other case trigger (1) bumps. Trigger (2) has NO such exception — it always bumps immediately, per the carve-out below.
- **Explicit `--model` carve-out (the ONLY statement of this rule):** an explicit `--model` is a user override, so trigger (1) MUST NOT silently overrule it — report the low-quality evidence, *propose* the bump, and re-launch at the user's tier unless they approve. Trigger (2) IS that approval, so it bumps immediately.
- **`--skip-judges` carve-out (the ONLY statement of this rule):** with no judge running, there is no score or judge issue for trigger (1) to read, so trigger (1) cannot fire. Trigger (2) is user-initiated, not judge-derived, so it is unaffected — a user complaint under `--skip-judges` (or `--one-shot`) still bumps the tier for that phase's re-launch.
- **Scoped to the failing phase.** An escalated tier applies to that phase's remaining iterations only; every later phase resumes from its own [Phase Weighting](#phase-weighting) tier.
- Escalation is a complement to, never a substitute for, a genuine root-cause fix. You MUST still pass the judge's specific feedback into the re-launch; re-launching the same prompt at a higher tier and hoping is prohibited.
- Escalation is orthogonal to `THRESHOLD`, `MAX_ITERATIONS`, `STRICT_MODE` and the [Iteration Discretion Rule](#iteration-discretion-rule) — it changes *which model* runs the next iteration, never *whether* one is warranted. When the Iteration Discretion Rule accepts a phase, no iteration happens, so nothing escalates.
- **Re-entry after a finished phase (the ONLY statement of this rule):** a ✅ PASS or ☑️ ACCEPTED does NOT close the work. A later user quality complaint re-enters that phase under trigger (2) — through `--continue` or `--refine` — and `MAX_ITERATIONS` **resets** for it, with the phase and its judge running at the bumped tier.

### Cross-Provider Equivalence

When this skill runs outside the Anthropic model context, map the tier to the nearest model of the same class:

| Tier | Role | Comparable models from other providers |
|---|---|---|
| `haiku` | Fast and cheap; mechanical work | `gemini-flash-lite`, `gemma` class, `gpt-oss` class, small open-weight models |
| `sonnet` | Balanced workhorse; most planning phases | `gemini-pro` class and full `gemini-flash` (**not** the `-lite` variant, which is `haiku`-tier), `GPT-5-mini` class, large `Qwen` / `DeepSeek` class |
| `opus` | Frontier reasoning; critical or complex work | whatever the provider sells as its extended / deliberate-reasoning tier — currently `GPT-5.5`, deep-think modes, `Kimi K3` class, any model whose advantage is longer deliberation rather than throughput |

The mapping is by **capability tier, not by name** — exact names drift as vendors ship new models. Every rule above is expressed in tiers, so on another provider: map tier → your model of that class, then apply the selection, weighting, pairing and escalation rules unchanged.

## Workflow Execution

You MUST launch for each step a separate agent, instead of performing all steps yourself.

**CRITICAL:** For each agent you MUST:

1. Use the **Agent** type specified in the phase, and the **Model** tier resolved per the [Model Selection Policy](#model-selection-policy)
2. Provide the task file path and user input as context
3. **Provide the value of `${CLAUDE_PLUGIN_ROOT}` so agents can resolve paths like `@${CLAUDE_PLUGIN_ROOT}/scripts/create-scratchpad.sh`**
4. Require agent to implement exactly that step, not more, not less
5. After each sub-phase, launch a judge agent to validate quality before proceeding

### Complete Workflow Overview

**Note:** Phases not in `ACTIVE_STAGES` are skipped. If `SKIP_JUDGES` is true, all judge steps are skipped entirely. Human checkpoints (🔍) occur after phases in
`HUMAN_IN_THE_LOOP_PHASES`.

```
Input: Draft Task File (.specs/tasks/draft/*.md)
    │
    ▼
Phase 2: Parallel Analysis
    │
    ├─────────────────────┬─────────────────────┐
    ▼                     ▼                     ▼
Phase 2a:             Phase 2b:             Phase 2c:
Research              Codebase Analysis     Business Analysis
[sdd:researcher]      [sdd:code-explorer]   [sdd:business-analyst]
all three at baseline tier
Judge 2a              Judge 2b              Judge 2c
(pass: >THRESHOLD)     (pass: >THRESHOLD)     (pass: >THRESHOLD)
    │                     │                     │
    └─────────────────────┴─────────────────────┘
                          │
                          ▼
                    Phase 3: Architecture Synthesis
                    [sdd:software-architect] baseline+1 (cap opus)
                    Judge 3 (pass: >THRESHOLD)
                          │
                          ▼
                    Phase 4: Decomposition
                    [sdd:tech-lead] baseline
                    Judge 4 (pass: >THRESHOLD)
                          │
                          ▼
                    Phase 5: Parallelize
                    [sdd:team-lead] baseline
                    Judge 5 (pass: >THRESHOLD)
                          │
                          ▼
                    Phase 6: Verifications
                    [sdd:qa-engineer] baseline
                    Judge 6 (pass: >THRESHOLD)
                          │
                          ▼
                    Move task: draft/ → todo/
                          │
                          ▼
                    Complete
```

---

## Phase 2: Parallel Analysis

Phase 2 launches three analysis phases in parallel, each with its own judge validation.

### Phase 2a/2b/2c: Parallel Sub-Phases

Launch these three phases **in parallel** immediately:

---

#### Phase 2a: Research

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: gathering and summarizing resources for an already-scoped task, no design decisions.
**Agent:** `sdd:researcher`
**Depends on:** Task file exists
**Purpose:** Gather relevant resources, documentation, libraries, and prior art. Creates or updates a reusable skill.

Launch agent:

- **Description**: "Research task resources and create/update skill"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>
  Task Title: <title from task file>

  CRITICAL: DO NOT OUTPUT YOUR RESEARCH, ONLY CREATE THE SCRATCHPAD AND SKILL FILE.
  ```

**Capture:**

- Skill file path (e.g., `.claude/skills/<skill-name>/SKILL.md`)
- Skill action (Created new / Updated existing)
- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Number of resources gathered
- Key recommendation summary

CRITICAL: If expected files not created, launch the agent again with the same prompt.

---

#### Phase 2b: Codebase Impact Analysis

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: reading the codebase to locate files and integration points scales with the task's own breadth, which the baseline already reflects.
**Agent:** `sdd:code-explorer`
**Depends on:** Task file exists
**Purpose:** Identify affected files, interfaces, and integration points

Launch agent:

- **Description**: "Analyze codebase impact"
- **Prompt**:

  ```text
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>
  Task Title: <title from task file>

  CRITICAL: DO NOT OUTPUT YOUR ANALYSIS, ONLY CREATE THE SCRATCHPAD AND ANALYSIS FILE.
  ```

**Capture:**

- Analysis file path (e.g., `.specs/analysis/analysis-{name}.md`)
- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Files affected count (modify/create/delete)
- Risk level assessment
- Key integration points

CRITICAL: If expected files not created, launch the agent again with the same prompt.

---

#### Phase 2c: Business Analysis

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: structured elicitation driven end-to-end by `analyse-business-requirements.md`, not open-ended synthesis — the procedure, not the model, carries the rigour here.
**Agent:** `sdd:business-analyst`
**Depends on:** Task file exists
**Purpose:** Refine description and create acceptance criteria

Launch agent:

- **Description**: "Business analysis"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read ${CLAUDE_PLUGIN_ROOT}/skills/plan-task/analyse-business-requirements.md and execute it exactly as is!

  Task File: <TASK_FILE>
  Task Title: <title from task file>

  CRITICAL: DO NOT OUTPUT YOUR BUSINESS ANALYSIS, ONLY CREATE THE SCRATCHPAD AND UPDATE THE TASK FILE.
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Acceptance criteria count
- Scope defined (yes/no)
- User scenarios documented

---

### Judge 2a/2b/2c: Validate Parallel Phases

After **each** parallel phase completes, launch its respective judge **with the same agent type** as that phase, at the tier [Role Pairing](#role-pairing) gives it.

#### Judge 2a: Validate Research/Skill

**Model:** Phase 2a's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:researcher`
**Depends on:** Phase 2a completion
**Purpose:** Validate skill completeness and relevance

Launch judge:

- **Description**: "Judge skill quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to skill file from Phase 2a}

  ### Context
  This is a skill document for task: {task title}. Evaluate comprehensiveness and reusability.

  ### Rubric
  1. Resource Coverage (weight: 0.30)
     - Documentation and references gathered?
     - Libraries and tools identified with recommendations?
     - 1=Missing critical resources, 2=Basic coverage, 3=Adequate, 4=Comprehensive, 5=Excellent

  2. Pattern Relevance (weight: 0.25)
     - Are identified patterns applicable?
     - Are recommendations actionable?
     - 1=Irrelevant, 2=Somewhat useful, 3=Adequate, 4=Well-targeted, 5=Perfect fit

  3. Issue Anticipation (weight: 0.20)
     - Common pitfalls identified with solutions?
     - 1=None identified, 2=Few issues, 3=Adequate, 4=Good coverage, 5=Comprehensive

  4. Reusability (weight: 0.15)
     - Is the skill general enough to help multiple tasks?
     - Does it avoid task-specific details?
     - 1=Too specific, 2=Limited reuse, 3=Adequate, 4=Good, 5=Highly reusable

  5. Task Integration (weight: 0.10)
     - Was task file updated with skill reference?
     - 1=Not updated, 3=Updated, 5=Updated with clear instructions
  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Research complete, proceed
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 2a with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Proceed to next stage regardless of score (log warning)

---

#### Judge 2b: Validate Codebase Analysis

**Model:** Phase 2b's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:code-explorer`
**Depends on:** Phase 2b completion
**Purpose:** Validate file identification accuracy and integration mapping

Launch judge:

- **Description**: "Judge codebase analysis quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to analysis file from Phase 2b}

  ### Context
  This is codebase impact analysis for task: {task title}. Evaluate accuracy and completeness.

  ### Rubric
  1. File Identification Accuracy (weight: 0.35)
     - All affected files identified with specific paths?
     - New files and modifications distinguished?
     - 1=Major files missing, 2=Mostly correct, 3=Adequate, 4=Precise, 5=Complete

  2. Interface Documentation (weight: 0.25)
     - Key functions/classes documented with signatures?
     - Change requirements clear?
     - 1=Missing, 2=Partial, 3=Adequate, 4=Good, 5=Complete

  3. Integration Point Mapping (weight: 0.25)
     - Integration points identified with impact?
     - Similar patterns in codebase found?
     - 1=Missing, 2=Partial, 3=Adequate, 4=Good, 5=Comprehensive

  4. Risk Assessment (weight: 0.15)
     - High risk areas identified with mitigations?
     - 1=No assessment, 2=Basic, 3=Adequate, 4=Good, 5=Thorough
  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Analysis complete, proceed
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 2b with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Proceed to next stage regardless of score (log warning)

---

#### Judge 2c: Validate Business Analysis

**Model:** Phase 2c's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:business-analyst`
**Depends on:** Phase 2c completion
**Purpose:** Validate acceptance criteria quality and scope definition

Launch judge:

- **Description**: "Judge business analysis quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to task file from Phase 2c}

  ### Context
  This is business analysis output. Evaluate description clarity and acceptance criteria quality.

  ### Rubric
  1. Description Clarity (weight: 0.30)
     - What/Why clearly explained?
     - Scope boundaries defined?
     - 1=Vague, 2=Basic, 3=Adequate, 4=Clear, 5=Excellent

  2. Acceptance Criteria Quality (weight: 0.35)
     - Criteria specific and testable?
     - Given/When/Then format for complex criteria?
     - 1=Missing/vague, 2=Basic, 3=Adequate, 4=Good, 5=Excellent

  3. Scenario Coverage (weight: 0.20)
     - Primary flow documented?
     - Error scenarios considered?
     - 1=Missing, 2=Basic, 3=Adequate, 4=Good, 5=Comprehensive

  4. Scope Definition (weight: 0.15)
     - In-scope/out-of-scope explicit?
     - No implementation details in description?
     - 1=Missing, 2=Partial, 3=Adequate, 4=Good, 5=Clear
  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Business analysis complete, proceed
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 2c with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Proceed to next stage regardless of score (log warning)

---

### Synchronization Point

**Wait for ALL three parallel phases (2a, 2b, 2c) AND their judges to PASS before proceeding to Phase 3.**

---

## Phase 3: Architecture Synthesis

**Model:** One tier above `BASELINE_TIER`, capped at `opus`, per [Phase Weighting](#phase-weighting) — the sole **heavy** phase: it decides the solution strategy and trade-offs that every later phase and the implementation inherit.
**Agent:** `sdd:software-architect`
**Depends on:** Phase 2a + Judge 2a PASS, Phase 2b + Judge 2b PASS, Phase 2c + Judge 2c PASS
**Purpose:** Synthesize research, analysis, and business requirements into architectural overview

Launch agent:

- **Description**: "Architecture synthesis"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>
  Skill File: <skill file path from Phase 2a>
  Analysis File: <analysis file path from Phase 2b>

  CRITICAL: DO NOT OUTPUT YOUR ARCHITECTURE SYNTHESIS, ONLY CREATE THE SCRATCHPAD AND UPDATE THE TASK FILE.
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Sections added to task file
- Key architectural decisions count
- Components identified (if applicable)
- Contracts defined (if applicable)

---

### Judge 3: Validate Architecture Synthesis

**Model:** Phase 3's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:software-architect`
**Depends on:** Phase 3 completion
**Purpose:** Validate architectural coherence and completeness

Launch judge:

- **Description**: "Judge architecture synthesis quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to task file after Phase 3}

  ### Context
  This is architecture synthesis output. The Architecture Overview section should contain
  solution strategy, key decisions, and only relevant architectural sections.

  ### Rubric
  1. Solution Strategy Clarity (weight: 0.30)
     - Approach clearly explained?
     - Key decisions documented with reasoning?
     - Trade-offs stated?
     - 1=Missing/unclear, 2=Basic, 3=Adequate, 4=Clear, 5=Excellent

  2. Reference Integration (weight: 0.20)
     - Links to research and analysis files?
     - Insights from both integrated?
     - 1=No links, 2=Partial, 3=Adequate, 4=Good, 5=Fully integrated

  3. Section Relevance (weight: 0.25)
     - Only relevant sections included (not all)?
     - Sections appropriate for task complexity?
     - 1=Wrong sections, 2=Mostly appropriate, 3=Adequate, 4=Good, 5=Precisely targeted

  4. Expected Changes Accuracy (weight: 0.25)
     - Files to create/modify listed?
     - Consistent with codebase analysis?
     - 1=Missing/inconsistent, 2=Partial, 3=Adequate, 4=Good, 5=Complete

  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Architecture synthesis complete, proceed
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 3 with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Proceed to Phase 4 regardless of score (log warning)

**Wait for PASS before Phase 4.**

---

## Phase 4: Decomposition

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: it applies an architecture Phase 3 already settled rather than making open design decisions, but still demands genuine per-step judgment — risks and mitigations specific to this task's own steps, not a generic checklist (see Judge 4's Risk Coverage criterion).
**Agent:** `sdd:tech-lead`
**Depends on:** Phase 3 + Judge 3 PASS
**Purpose:** Break architecture into implementation steps with success criteria and risks

Launch agent:

- **Description**: "Decompose into implementation steps"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>

  CRITICAL: DO NOT OUTPUT YOUR DECOMPOSITION, ONLY CREATE THE SCRATCHPAD AND UPDATE THE TASK FILE.
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Implementation steps count
- Total subtasks count
- Critical path steps
- High priority risks count

---

### Judge 4: Validate Decomposition

**Model:** Phase 4's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:tech-lead`
**Depends on:** Phase 4 completion
**Purpose:** Validate implementation steps quality and completeness

Launch judge:

- **Description**: "Judge decomposition quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to task file after Phase 4}

  ### Context
  This is decomposition output. The Implementation Process section should contain
  ordered steps with success criteria, subtasks, blockers, and risks.

  ### Rubric
  1. Step Quality (weight: 0.30)
     - Each step has clear goal, output, success criteria?
     - Steps ordered by dependency?
     - No step too large (>Large estimate)?
     - 1=Vague/missing, 2=Basic, 3=Adequate, 4=Good, 5=Excellent

  2. Success Criteria Testability (weight: 0.25)
     - Criteria specific and verifiable?
     - Use actual file paths, function names?
     - Subtasks clearly defined with actionable descriptions?
     - 1=Vague, 2=Partially testable, 3=Adequate, 4=Good, 5=All testable

  3. Risk Coverage (weight: 0.25)
     - Blockers identified with resolutions?
     - Risks identified with mitigations?
     - High-risk tasks identified with decomposition recommendations?
     - 1=None, 2=Basic, 3=Adequate, 4=Good, 5=Comprehensive

  4. Completeness (weight: 0.20)
     - All architecture components have corresponding steps?
     - Implementation summary table present?
     - Definition of Done included?
     - Phases organized: Setup → Foundational → User Stories → Polish?
     - 1=Incomplete, 2=Partial, 3=Adequate, 4=Good, 5=Complete
  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Decomposition complete, proceed to Phase 5
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 4 with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Proceed to Phase 5 regardless of score (log warning)

**Wait for PASS before Phase 5.**

---

## Phase 5: Parallelize Steps

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: dependency-graph bookkeeping over steps that already declare their dependencies, plus agent/model assignment from a supplied list.
**Agent:** `sdd:team-lead`
**Depends on:** Phase 4 + Judge 4 PASS
**Purpose:** Reorganize implementation steps for maximum parallel execution

Launch agent:

- **Description**: "Parallelize implementation steps"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>

  Use agents only from this list: {list ALL available agents with plugin prefix if available, e.g. sdd:developer, review:bug-hunter. Also include general agents: opus, sonnet, haiku}

  Assign each step's model tier per this policy:
  {paste the Selection Rules table plus its Precedence and Tie-breaker paragraphs from the orchestrator's Model Selection Policy verbatim, applied per implementation step; drop the cross-reference links, which do not resolve outside that file}

  CRITICAL: DO NOT OUTPUT YOUR PARALLELIZATION, ONLY CREATE THE SCRATCHPAD AND UPDATE THE TASK FILE.
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Number of steps reorganized
- Maximum parallelization depth
- Agent distribution summary

---

### Judge 5: Validate Parallelization

**Model:** Phase 5's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:team-lead`
**Depends on:** Phase 5 completion
**Purpose:** Validate dependency accuracy and parallelization optimization

Launch judge:

- **Description**: "Judge parallelization quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to parallelized task file from Phase 5}

  ### Context
  This is the output of Phase 5: Parallelize Steps. The artifact should contain implementation steps
  reorganized for maximum parallel execution with explicit dependencies, agent assignments, and
  parallelization diagram.

  Use agents only from this list: {list ALL available agents with plugin prefix if available, e.g. sdd:developer, review:bug-hunter. Also include general agents: opus, sonnet, haiku}

  ### Rubric
  1. Dependency Accuracy (weight: 0.35)
     - Are step dependencies correctly identified?
     - No false dependencies (steps marked dependent when they're not)?
     - No missing dependencies (steps that actually depend on others)?
     - 1=Major dependency errors, 2=Mostly correct, 3=Acceptable, 5=Precise dependencies

  2. Parallelization Maximized (weight: 0.30)
     - Are parallelizable steps correctly marked with "Parallel with:"?
     - Is the parallelization diagram logical?
     - 1=No parallelization/wrong, 2=Some optimization, 3=Acceptable, 5=Maximum parallelization

  3. Agent Selection Correctness (weight: 0.20)
     - Are agent types appropriate for outputs?
     - Does selection follow the Agent Selection Guide?
     - Are only agents from the provided available agents list used?
     - 1=Wrong agents, 2=Mostly appropriate, 3=Acceptable, 4=Optimal selection, 5=Perfect selection

  4. Execution Directive Present (weight: 0.15)
     - Is the sub-agent execution directive present?
     - Are "MUST" requirements for parallel execution clear?
     - 1=Missing directive, 2=Partial, 3=Acceptable, 4=Complete directive, 5=Perfect directive
  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Proceed to Phase 6
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 5 with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Proceed to Phase 6 regardless of score (log warning)

**Wait for PASS before Phase 6.**

---

## Phase 6: Define Verifications

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: it derives rubrics and test strategies from acceptance criteria already settled rather than making open design decisions, but still demands genuine per-artifact judgment — criteria and test cases tailored to each artifact, not a generic template (see Judge 6's Rubric Quality and Test Strategy Coverage criteria, which reject generic output).
**Agent:** `sdd:qa-engineer`
**Depends on:** Phase 5 + Judge 5 PASS
**Purpose:** Add LLM-as-Judge verification sections with rubrics

Launch agent:

- **Description**: "Define verification rubrics"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>

  CRITICAL: DO NOT OUTPUT YOUR VERIFICATIONS, ONLY CREATE THE SCRATCHPAD AND UPDATE THE TASK FILE.
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Number of steps with verification
- Total evaluations defined
- Verification breakdown (Panel/Per-Item/None)

---

### Judge 6: Validate Verifications

**Model:** Phase 6's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:qa-engineer`
**Depends on:** Phase 6 completion
**Purpose:** Validate verification rubrics and thresholds

Launch judge:

- **Description**: "Judge verification quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to task file with verifications from Phase 6}

  ### Context
  This is the output of Phase 6: Define Verifications. The artifact should contain LLM-as-Judge
  verification sections for each implementation step, including verification levels, custom rubrics,
  thresholds, and a verification summary table.

  ### Rubric
  1. Verification Level Appropriateness (weight: 0.25)
     - Do verification levels match artifact criticality?
     - HIGH criticality → Panel, MEDIUM → Single/Per-Item, LOW/NONE → None?
     - 1=Mismatched levels, 2=Mostly appropriate, 3=Acceptable, 5=Precisely calibrated

  2. Rubric Quality (weight: 0.20)
     - Are criteria specific to the artifact type (not generic)?
     - Do weights sum to 1.0?
     - Are descriptions clear and measurable?
     - 1=Generic/broken rubrics, 2=Adequate, 3=Acceptable, 5=Excellent custom rubrics

  3. Threshold Appropriateness (weight: 0.15)
     - Are thresholds reasonable (typically 4.0/5.0)?
     - Higher for critical, lower for experimental?
     - 1=Wrong thresholds, 2=Standard applied, 3=Acceptable, 5=Context-appropriate

  4. Coverage Completeness (weight: 0.20)
     - Does every step have a Verification section?
     - Is the Verification Summary table present?
     - 1=Missing verifications, 2=Most covered, 3=Acceptable, 5=100% coverage

  5. Test Strategy Coverage (weight: 0.20)
     - Does every applicable step (test_strategy.applies = true) have a `**Test Strategy:**` block (Test Matrix table + Test Cases to Cover bullet list)?
     - Does each `Test Cases to Cover` cover every acceptance criterion (no orphans)?
     - Does the **Test Cases to Cover** list appear under every applicable step and use the format `- [type] description` under each acceptance criterion?
     - 1=Missing/empty Test Strategy blocks, 2=Present but Test Cases to Cover orphans or no Test Cases to Cover list, 3=All blocks present, 5=Ideal coverage with full BVA boundaries, and matched bullet list per step
  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Workflow complete, promote task
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 6 with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Complete workflow regardless of score (log warning)

---

## Phase 7: Promote Task

**Purpose:** Move the refined task from draft to todo folder

After all phases complete:

1. **Move task file from draft to todo:**

   ```bash
   git mv <TASK_FILE> .specs/tasks/todo/
   # Fallback if git not available: mv <TASK_FILE> .specs/tasks/todo/
   ```

2. **Update any references** in research and analysis files if needed

---

## Completion

After all executed phases and judges complete:

1. Use git tool to stage the task file, skill file, analysis file, and scratchpad files (only those that were created)
2. Summarize the workflow results and output to user:

```markdown
### Task Refined

| Property | Value |
|----------|-------|
| **Original File** | `<original TASK_FILE path>` |
| **Final Location** | `.specs/tasks/todo/<filename>` (ready for implementation) |
| **Title** | `<task title>` |
| **Type** | `<feature/bug/refactor/test/docs/chore/ci>` (from filename) |
| **Skill** | `<skill file path or "Skipped">` |
| **Skill Action** | `<Created new / Updated existing / Skipped>` |
| **Analysis** | `<analysis file path or "Skipped">` |
| **Scratchpad** | `<scratchpad file path>` |
| **Implementation Steps** | `<count or "N/A">` |
| **Parallelization Depth** | `<max parallel agents or "N/A">` |
| **Total Verifications** | `<count or "N/A">` |

### Configuration Used

| Setting | Value |
|---------|-------|
| **Target Quality** | {THRESHOLD}/5.0 |
| **Max Iterations** | {MAX_ITERATIONS} |
| **Active Stages** | {ACTIVE_STAGES as comma-separated list} |
| **Skipped Stages** | {SKIP_STAGES or stages not in ACTIVE_STAGES} |
| **Human Checkpoints** | Phase {HUMAN_IN_THE_LOOP_PHASES as comma-separated} |
| **Skip Judges** | {SKIP_JUDGES} |
| **Refine Mode** | {REFINE_MODE} |
| **Strict Mode** | {STRICT_MODE} |

### Quality Gates Summary

| Phase | Judge Score | Verdict |
|-------|-------------|---------|
| Phase 2a: Research | X.X/5.0 | ✅ PASS / ☑️ ACCEPTED / ⚠️ PROCEEDED (max iter) / ⏭️ SKIPPED |
| Phase 2b: Codebase Analysis | X.X/5.0 | ✅ PASS / ☑️ ACCEPTED / ⚠️ PROCEEDED (max iter) / ⏭️ SKIPPED |
| Phase 2c: Business Analysis | X.X/5.0 | ✅ PASS / ☑️ ACCEPTED / ⚠️ PROCEEDED (max iter) / ⏭️ SKIPPED |
| Phase 3: Architecture Synthesis | X.X/5.0 | ✅ PASS / ☑️ ACCEPTED / ⚠️ PROCEEDED (max iter) / ⏭️ SKIPPED |
| Phase 4: Decomposition | X.X/5.0 | ✅ PASS / ☑️ ACCEPTED / ⚠️ PROCEEDED (max iter) / ⏭️ SKIPPED |
| Phase 5: Parallelize | X.X/5.0 | ✅ PASS / ☑️ ACCEPTED / ⚠️ PROCEEDED (max iter) / ⏭️ SKIPPED |
| Phase 6: Verify | X.X/5.0 | ✅ PASS / ☑️ ACCEPTED / ⚠️ PROCEEDED (max iter) / ⏭️ SKIPPED |

**Threshold Used:** {THRESHOLD}/5.0 (or N/A if SKIP_JUDGES)

**Legend:**
- ✅ PASS - Score >= THRESHOLD
- ☑️ ACCEPTED - Score in `max(3.0, THRESHOLD - 1.0)..THRESHOLD` accepted per the [Iteration Discretion Rule](#iteration-discretion-rule) (outstanding nitpicks listed below the table)
- ⚠️ PROCEEDED (max iter) - Score < THRESHOLD but MAX_ITERATIONS reached, proceeded anyway
- ⏭️ SKIPPED - Stage not in ACTIVE_STAGES

**Outstanding Issues (accepted below THRESHOLD):**

{For each ☑️ ACCEPTED phase: phase, remaining nitpicks with priority — omit this block when no phase was accepted}

### Artifacts Generated

```

.claude/
└── skills/
    └── <skill-name>/
        └── SKILL.md             # Reusable skill document (if research stage ran)

.specs/
├── tasks/
│   ├── draft/                   # Draft tasks (source - now empty for this task)
│   ├── todo/
│   │   └── <name>.<type>.md     # Complete task specification (ready for implementation)
│   ├── in-progress/             # Tasks being implemented (empty)
│   └── done/                    # Completed tasks (empty)
├── analysis/
│   └── analysis-<name>.md       # Codebase impact analysis (if codebase analysis stage ran)
└── scratchpad/
    └── <hex-id>.md              # Architecture thinking scratchpad

```

### Task Status Management

Task status is managed by folder location:
- `draft/` - Tasks created but not yet refined
- `todo/` - Tasks ready for implementation
- `in-progress/` - Tasks currently being worked on
- `done/` - Completed tasks

### Next Steps

1. Review task: `.specs/tasks/todo/<filename>`
   - Edit the task file directly to make corrections
   - Add `//` comments to lines that need clarification or changes
   - Run `/plan` again with `--refine` to incorporate your feedback — it detects changes against git and propagates updates **top-to-bottom** (editing a section only affects sections below it, not above)
2. If everything is fine, begin implementation: `/implement` (will auto-select the task from todo/)
```

---

## Error Handling

### Phase Agent Failure (Exception/Crash)

If any phase agent fails unexpectedly:

1. Report the failure with agent output
2. Ask clarification questions from user that can help resolve the issue
3. Launch the phase agent again with list of questions and answers to resolve the issue

### Judge Returns FAIL

If any judge returns FAIL (score < `THRESHOLD`):

0. **Apply the [Iteration Discretion Rule](#iteration-discretion-rule) first**: if `score < 3.0` (or `STRICT_MODE` is true), always retry. If `max(3.0, THRESHOLD - 1.0) <= score < THRESHOLD` and only nitpicks remain, decide deliberately whether retrying is worth it — if you accept, mark the phase ☑️ ACCEPTED, list its outstanding nitpicks in the summary, and proceed to the next phase instead of steps 1-4; otherwise continue with step 1
1. **Automatic retry**: Re-launch the phase agent with judge feedback, at the tier decided per the [Escalation Rule](#escalation-rule) — which governs in full, including its sole hold exception and its `--model` carve-out. Retry-specific anchors on top of it: trigger (1) is anchored at `score < 3.0` here (or judge issues showing the model misunderstood the phase); re-judge at the same tier as the re-launched phase; state the tier decision in the phase summary
2. **Human-in-the-loop check**: If phase is in `HUMAN_IN_THE_LOOP_PHASES`, trigger human checkpoint **before** the next judge retry (after implementation retry but before re-judging)
3. **After `MAX_ITERATIONS` reached**: **Proceed to next stage automatically** (do NOT ask user unless `--human-in-the-loop` includes this phase)
4. Log warning in completion summary: `⚠️ Phase X did not pass quality threshold (X.X/THRESHOLD) after MAX_ITERATIONS iterations`

### Retry Flow

```
Implementation → Judge FAIL → Implementation Retry → Judge Retry
                                                          ↓
                              PASS → Continue to next stage
                              FAIL → Repeat until MAX_ITERATIONS
                                          ↓
                              MAX_ITERATIONS reached → Proceed to next stage (with warning)
```

### Retry Flow with Human-in-the-Loop

When phase is in `HUMAN_IN_THE_LOOP_PHASES`:

```
Implementation → Judge FAIL → Implementation Retry
                                    ↓
                    🔍 Human Checkpoint (optional feedback)
                                    ↓
                              Judge Retry
                                    ↓
                    PASS → Continue | FAIL → Repeat until MAX_ITERATIONS
                                                    ↓
                              MAX_ITERATIONS → 🔍 Final Human Checkpoint
                                                    ↓
                                    User confirms → Proceed to next stage
```
