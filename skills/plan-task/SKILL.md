---
name: plan-task
description: Refine a draft task specification into a fully planned, implementation-ready task with acceptance criteria, architecture, per-step sub-task files and verifiable phases
---

# Refine Task Workflow

## Role

You are a task refinement orchestrator. Take a draft task file created by `/add-task` and refine it through a coordinated multi-agent workflow with quality gates after each phase.

## Goal

This workflow command refines an existing draft task through:

1. **Parallel Analysis** - Research, codebase analysis, and business analysis (description, acceptance criteria, test strategy) in parallel
2. **Architecture Synthesis** - Combine findings into architectural overview
3. **Decomposition** - Break into per-step sub-task files, grouped into independently verifiable phases with dependencies, parallel groups, agent/model assignments and a reviewer model per phase
4. **Promote** - Move refined task from `draft/` to `todo/`

All model-assigned phases include judge validation to prevent error propagation and ensure quality thresholds are met.

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
| `--fast` | `--fast` | N/A | Alias for `--target-quality 3.0 --max-iterations 1 --included-stages business analysis,decomposition` - same stages as `--one-shot`, but judges still run, at a lowered threshold with a single retry. |
| `--one-shot` | `--one-shot` | N/A | Alias for `--included-stages business analysis,decomposition --skip-judges` - same stages as `--fast`, but no judge runs at all and no quality gate is applied. |
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
| `business analysis` | 2c | Refine description and create acceptance criteria (checklist, regular checks, rubric, test strategy, definition of done) |
| `architecture synthesis` | 3 | Synthesize research and analysis into architecture |
| `decomposition` | 4 | Break into per-step sub-task files grouped into verifiable phases, with dependencies, parallel groups and agent/model assignments |

### Configuration Resolution

Parse `$ARGUMENTS` and resolve configuration as follows:

```

# Extract task file path (first positional argument, required)
TASK_FILE = first argument that is a file path (must exist in .specs/tasks/draft/)

# Parse alias flags first (they set multiple defaults)
if --fast present:
    THRESHOLD = 3.0
    MAX_ITERATIONS = 1
    INCLUDED_STAGES = ["business analysis", "decomposition"]

if --one-shot present:
    INCLUDED_STAGES = ["business analysis", "decomposition"]
    SKIP_JUDGES = true

# Initialize defaults
THRESHOLD ?= --target-quality || 3.5
MAX_ITERATIONS ?= --max-iterations || 3
INCLUDED_STAGES ?= --included-stages || ["research", "codebase analysis", "business analysis", "architecture synthesis", "decomposition"]
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
   | Description / Acceptance Criteria (checklist, regular checks, rubric, test strategy, definition of done) | `business analysis` (Phase 2c) |
   | Architecture Overview | `architecture synthesis` (Phase 3) |
   | Implementation Process (Parallelization Overview / Phase Overview), or any sub-task file under `.specs/sub-tasks/<task-name>/` | `decomposition` (Phase 4) |

   The Implementation Process section and the sub-task files are produced by the same phase, so a change to either re-runs Phase 4 as a whole.

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
   # Runs: architecture synthesis, decomposition
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
/plan .specs/tasks/draft/critical-api.feature.md --target-quality 4.5 --human-in-the-loop 2,3,4

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
       {"content": "Phase 4: Decompose into sub-task files and verifiable phases", "status": "pending", "activeForm": "Decomposing into steps and phases"},
       {"content": "Judge 4: PASS decomposition (> {THRESHOLD})", "status": "pending", "activeForm": "Validating decomposition"},
       {"content": "Move task to todo folder", "status": "pending", "activeForm": "Promoting task"},
       {"content": "Human checkpoint reviews", "status": "pending", "activeForm": "Awaiting human review"}
     ]
   }
   ```

   **Note:** Filter todos based on configuration:
   - If `SKIP_JUDGES` is true, omit ALL Judge todos (Judge 2a, 2b, 2c, 3, 4)
   - If `research` not in `ACTIVE_STAGES`, omit Phase 2a and Judge 2a todos
   - If `codebase analysis` not in `ACTIVE_STAGES`, omit Phase 2b and Judge 2b todos
   - If `business analysis` not in `ACTIVE_STAGES`, omit Phase 2c and Judge 2c todos
   - If `architecture synthesis` not in `ACTIVE_STAGES`, omit Phase 3 and Judge 3 todos
   - If `decomposition` not in `ACTIVE_STAGES`, omit Phase 4 and Judge 4 todos
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
   - `.specs/sub-tasks/` - Per-step sub-task files written by Phase 4 (tracked in git)
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

Assess the **overall task being planned** — the draft task file's title and type plus the user's input — against this table. The matching row is the run's `BASELINE_TIER`. (The same table also tiers a *single unit of work*, which is why Phase 4 receives it verbatim to assign a model per implementation step, and how Judge 4 grades those assignments.)

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
| Phases 2a, 2b, 2c, 4 | Standard | `BASELINE_TIER` |

Every model-assigned phase appears in exactly ONE row, so each resolves to exactly ONE tier. The cap means an `opus` baseline leaves all phases at `opus`. [Promotion](#promote-task) is a file move you perform yourself — no sub-agent, no tier. See [Role Pairing](#role-pairing) for the `--model` override.

**Not to be confused with the per-step tiers inside the plan.** The tiers above govern the *planning* agents you launch. The `Model:` recorded in each sub-task file and the `Reviewer model:` recorded for each phase are decided by Phase 4 for the *implementation* run, from the per-step policy Phase 4's launch prompt carries — they are independent of `BASELINE_TIER`.

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
                    → task file: ## Implementation Process
                    → .specs/sub-tasks/<task-name>/NN-<step-slug>.md
                    Judge 4 (pass: >THRESHOLD)
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

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: structured elicitation and checklist/rubric/test-strategy derivation driven end-to-end by the agent's own STAGES 1-10, not open-ended synthesis — the procedure, not the model, carries the rigour here.
**Agent:** `sdd:business-analyst`
**Depends on:** Task file exists
**Purpose:** Refine the description and produce the single `## Acceptance Criteria` section — checklist, regular checks, rubric, rubric score definitions, test strategy and definition of done, mixing business and technical criteria

Launch agent:

- **Description**: "Business analysis"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>
  Task Title: <title from task file>

  Execute your own Core Process (STAGES 1-10) in full. 

  CRITICAL: DO NOT OUTPUT YOUR BUSINESS ANALYSIS. Create the scratchpad, then write the task file's `# Description` and the single `## Acceptance Criteria` section at your STAGE 10.
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Scope defined (yes/no)
- User scenarios documented
- Checklist items count (essential / important / optional / pitfall)
- Regular checks count
- Rubric dimensions count (weights sum: 1.0)
- Test strategy applies (true/false) and test types selected
- Quality gates and project guidelines discovered

CRITICAL: If the task file's `# Description` or `## Acceptance Criteria` section was not written, launch the agent again with the same prompt.

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
**Purpose:** Validate the refined description and the whole `## Acceptance Criteria` section — checklist, regular checks, rubric, score definitions, test strategy and definition of done
**Weight derivation:** criteria 1-4 are the original business-analysis criteria at their former proportions (0.30/0.35/0.20/0.15) scaled by 0.60, with the 0.01 rounding remainder given to the highest-weighted of them, totalling 0.61; criteria 5-7 — imported when rubric and test-strategy review folded into this judge — split the remaining 0.39 evenly at 0.13 each. Preserve that 0.61/0.39 split when adding or dropping a criterion, so the weights still sum to 1.00.

Launch judge:

- **Description**: "Judge business analysis quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to task file from Phase 2c}

  ### Context
  This is business analysis output. The task file should contain a refined `# Description`
  (with Scope Included/Excluded and User Scenarios) and exactly one `## Acceptance Criteria`
  section holding six sub-blocks in this order: `**Checklist:**` (table
  `| ID | Question | Category | Importance |`, IDs `CK-n`/`HR-n`), `**Regular Checks:**`
  (checkbox list), `**Rubric:**` (table `| Criterion | Weight |`), `**Rubric Score Definitions:**`
  (one `###` section per criterion, each ending in an `Anchors` list carrying `score_2`, `score_4`
  and `contrast` — excerpt anchors that pin 2 and 4, NOT 1-5 bins), `**Test Strategy:**` (Criticality + Test Matrix
  table + `Test Cases to Cover` grouped under `#### CK-N:` headings) and `**Definition of Done:**`.
  Business and technical criteria are mixed inside each sub-block — there is no separate business
  criteria list, and no section other than `## Acceptance Criteria` may carry evaluation content.

  ### Rubric
  1. Description Clarity (weight: 0.18)
     - What/Why/Who clearly explained?
     - Business value stated, constraints named?
     - 1=Vague, 2=Basic, 3=Adequate, 4=Clear, 5=Excellent

  2. Criteria Quality (weight: 0.22)
     - Is every `**Checklist:**` row a boolean YES/NO question that is specific and testable?
     - Are Category (`hard_rule`/`principle`) and Importance filled for every row, with stable `CK-n`/`HR-n` IDs?
     - Do business and technical criteria appear mixed, rather than as a separate business list?
     - Is `**Definition of Done:**` present and derived from those criteria?
     - 1=Missing/vague, 2=Basic, 3=Adequate, 4=Good, 5=Excellent

  3. Scenario Coverage (weight: 0.12)
     - Primary, alternative and error flows documented under **User Scenarios**?
     - Are the error and edge scenarios actually represented by checklist items or test cases?
     - 1=Missing, 2=Basic, 3=Adequate, 4=Good, 5=Comprehensive

  4. Scope Definition (weight: 0.09)
     - In-scope/out-of-scope explicit?
     - No implementation details in the description?
     - No invented file paths — artifacts cited only where the user prompt named them?
     - 1=Missing, 2=Partial, 3=Adequate, 4=Good, 5=Clear

  5. Rubric Quality (weight: 0.13)
     - Are `**Rubric:**` criteria specific to this task (not generic)?
     - Do the weights sum to 1.0?
     - Does EVERY criterion in `**Rubric Score Definitions:**` carry an `Anchors` list naming all three of `score_2`, `score_4` and `contrast`, with no 1-5 bins, ratios, percentages or quality bands in its description or classification/instruction paragraph? (A `score_2`/`score_4` anchor excerpt may legitimately quote a figure — this restriction does not reach the anchors themselves.)
     - Is each `score_2` / `score_4` a concrete excerpt of the deliverable a reader could point at (fenced text), NEVER a description of quality — `score_2` obviously FAILING that dimension and `score_4` obviously SATISFYING it?
     - Do a criterion's two anchors differ on EXACTLY ONE observable thing, with its one-line `contrast` naming that single difference, so a judge can place an artifact between or past them on that axis alone?
     - Is `Project Guidelines Alignment` present when project guideline files exist?
     - 1=Generic/broken rubrics, 2=Adequate, 3=Acceptable, 4=Good custom rubrics, 5=Excellent custom rubrics

  6. Coverage Completeness (weight: 0.13)
     - Are all six sub-blocks present, in order, under a single `## Acceptance Criteria`?
     - Does `**Regular Checks:**` use the project's actual discovered build/lint/test commands rather than placeholders?
     - Is every checklist item carried by at least one rubric criterion, regular check or test case — no orphans?
     - Is the task file free of scoring configuration (threshold values, judge counts, evaluation modes) and of any evaluation section other than `## Acceptance Criteria`?
     - 1=Missing sub-blocks or orphans, 2=Most covered, 3=Acceptable, 4=Good, 5=100% coverage

  7. Test Strategy Coverage (weight: 0.13)
     - When the task carries testable behaviour, is `**Test Strategy:**` present with Criticality, a Test Matrix table (`| Type | Size | Framework | Dependencies | Gate |`) and a `Test Cases to Cover` list?
     - Is every group headed `#### CK-N:` naming a checklist item that exists, with cases in `- [type] description` form?
     - Does every testable checklist item have at least one test case (no orphans), and every Test Matrix row a corresponding case?
     - If the strategy does not apply, is that stated with a reason rather than silently omitted?
     - 1=Missing/empty Test Strategy, 2=Present but orphaned or unheaded groups, 3=All blocks present, 4=Full coverage of testable items, 5=Ideal coverage with boundary cases enumerated
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

**Model:** `BASELINE_TIER` per [Phase Weighting](#phase-weighting) — standard weight: it applies an architecture Phase 3 already settled rather than making open design decisions, but still demands genuine per-step judgment — risks and mitigations specific to this task's own steps, a dependency graph that is neither over- nor under-constrained, and phase boundaries that each land on a working, verifiable milestone (see Judge 4's Risk Coverage, Dependency Accuracy and Phase Design criteria).
**Agent:** `sdd:tech-lead`
**Depends on:** Phase 3 + Judge 3 PASS
**Purpose:** Break the architecture into implementation steps, write each step as its own sub-task file, and group them into independently verifiable phases with dependencies, parallel groups, per-step agent/model assignments and a reviewer model per phase

Launch agent:

- **Description**: "Decompose into sub-task files and phases"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Task File: <TASK_FILE>

  Use agents only from this list: {list ALL available agents with plugin prefix if available, e.g. sdd:developer, review:bug-hunter. Also include general agents: opus, sonnet, haiku}

  Assign each step's model tier per this policy:
  {paste the Selection Rules table plus its Precedence and Tie-breaker paragraphs from the orchestrator's Model Selection Policy verbatim, applied per implementation step; drop the cross-reference links, which do not resolve outside that file}

  CRITICAL: DO NOT OUTPUT YOUR DECOMPOSITION. Create the scratchpad, write ONLY the `## Implementation Process` section (Parallelization Overview + Phase Overview) into the task file, and write every step as its own file under `.specs/sub-tasks/<task-name>/`.
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Sub-task directory (`.specs/sub-tasks/<task-name>/`) and the sub-task files written
- Implementation steps count (and how many were merged)
- Total subtasks count
- Phases count, with each phase's steps and reviewer model
- Critical path steps
- Max parallel width (peak concurrent steps — MUST be 1–5)
- Agent/model distribution
- High priority risks count

CRITICAL: If the `## Implementation Process` section or any sub-task file listed in the Parallelization Overview is missing, launch the agent again with the same prompt.

---

### Judge 4: Validate Decomposition

**Model:** Phase 4's tier — see [Role Pairing](#role-pairing)
**Agent:** `sdd:tech-lead`
**Depends on:** Phase 4 completion
**Purpose:** Validate step quality, sub-task file completeness, dependency and parallelization accuracy, agent/model assignment and phase design

Launch judge:

- **Description**: "Judge decomposition quality"
- **Prompt**:

  ```
  CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

  Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to task file after Phase 4}
  {path to the sub-task directory from Phase 4, e.g. .specs/sub-tasks/<task-name>/} — evaluate EVERY file in it

  ### Context
  This is decomposition output, written across two places. The task file carries ONLY the
  `## Implementation Process` section: the sub-agent execution directive that governs how each step
  is launched and how each phase is reviewed (its required content is spelled out under Completeness
  below), a `### Parallelization Overview` (ASCII diagram with phase boundaries plus a step table
  with columns `Step | Phase | Model | Agent | Depends on | Parallel with | Sub-Task File`) and a
  `### Phase Overview` (per phase: `#### Phase N`, `Steps:`, `Reviewer model:`,
  `Acceptance Criteria that should be fulfiled:`, a `Checklist items:` list citing `CK-n`/`HR-n` IDs from
  the task file's `**Checklist:**` table, and a `Rubrics:` list citing criterion names from its
  `**Rubric:**` table). Every step body lives in its own sub-task file at
  `.specs/sub-tasks/<task-name>/<NN>-<step-slug>.md` with the fields `**Task File:**`, `**Phase:**`,
  `**Model:**`, `**Agent:**`, `**Depends on:**`, `**Parallel with:**`, `**Note:**`, `**Goal:**`, a step
  description, `#### Expected Output`, `#### Success Criteria`, `#### Subtasks` and `#### Blockers & Risks`.

  By design these do NOT belong in the task file and MUST NOT be scored as missing: `### Implementation
  Strategy`, a least-to-most decomposition chain, `### Step N:` bodies, `## Implementation Summary`,
  `## Risks & Blockers Summary`, and a task-level Definition of Done (the Definition of Done lives in
  `## Acceptance Criteria`, written by an earlier phase). Verification is PHASE-level: each phase names
  one reviewer model; there are no per-step verification sections.

  Use agents only from this list: {list ALL available agents with plugin prefix if available, e.g. sdd:developer, review:bug-hunter. Also include general agents: opus, sonnet, haiku}

  ### Rubric
  1. Step Quality (weight: 0.15)
     - Does every sub-task file carry ALL required fields, with `None` written rather than a field omitted?
     - Does each have a clear `**Goal:**`, a real step description, and `#### Expected Output`?
     - Is each step meaningfully sized — neither so large it hides risk nor so small it wastes an agent run?
     - Is each sub-task file standalone-readable, naming every path, symbol and decision it builds on rather than relying on a neighbouring step?
     - 1=Vague/missing fields, 2=Basic, 3=Adequate, 4=Good, 5=Excellent

  2. Success Criteria Testability (weight: 0.12)
     - Are `#### Success Criteria` specific and verifiable, using actual file paths and function names?
     - Are `#### Subtasks` actionable, each naming what it changes and where?
     - Does every step include writing its own tests as a subtask?
     - 1=Vague, 2=Partially testable, 3=Adequate, 4=Good, 5=All testable

  3. Risk Coverage (weight: 0.10)
     - Does each sub-task file's `#### Blockers & Risks` table name blockers with resolutions and risks with mitigations, rated for Impact and Likelihood?
     - Are they specific to this step rather than a generic checklist restated per file?
     - 1=None, 2=Basic, 3=Adequate, 4=Good, 5=Comprehensive

  4. Completeness (weight: 0.15)
     - Does every architecture component and expected change have a corresponding step?
     - Does every row of the Parallelization Overview table have a sub-task file at the recorded path, and every sub-task file a row — no orphans either way?
     - Is the sub-agent execution directive present in `## Implementation Process` — launch one agent per step, parallel steps in parallel, pass the task file path AND the step's sub-task file path, use the step's own Model and Agent, implement exactly that step, and run the code reviewer ONCE per phase at that phase's reviewer model?
     - Is the task file free of the sections listed as out of scope in the Context above?
     - 1=Incomplete, 2=Partial, 3=Adequate, 4=Good, 5=Complete

  5. Dependency Accuracy (weight: 0.15)
     - Are `**Depends on:**` values correct — no false dependencies (steps sequenced that need not be), no missing ones (steps that truly need an earlier artifact)?
     - Do the sub-task files, the Parallelization Overview table and the diagram agree on every dependency?
     - Does each step's dependencies resolve to steps in the same or an earlier phase?
     - 1=Major dependency errors, 2=Mostly correct, 3=Acceptable, 4=Accurate, 5=Precise dependencies

  6. Parallelization Maximized (weight: 0.10)
     - Are genuinely independent steps marked with `**Parallel with:**` rather than left sequential?
     - Is the ASCII diagram logical and does it show the phase boundaries?
     - Is peak concurrent width within 1–5 (target ~3) rather than unbounded?
     - 1=No parallelization/wrong, 2=Some optimization, 3=Acceptable, 4=Well optimized, 5=Maximum parallelization within the width bound

  7. Agent/Model Selection Correctness (weight: 0.08)
     - Are agent types appropriate for what each step OUTPUTS, and drawn only from the provided available agents list?
     - Does each step's `**Model:**` follow the per-step model policy — `opus` earned by a breadth, critical-domain or open-design trigger rather than picked to be safe, `haiku` only for mechanical work?
     - 1=Wrong agents/tiers, 2=Mostly appropriate, 3=Acceptable, 4=Optimal selection, 5=Perfect selection

  8. Phase Design (weight: 0.15)
     - Does EACH phase leave an independently verifiable milestone — a working application/service/solution that could be committed and run, PLUS the tests or other verification artifacts that let a reviewer judge it against the criteria listed for that phase?
     - Is EACH phase's `Reviewer model:` appropriate — never below the highest implementation tier used in that phase, and one tier above it unless the phase is small, uniform and mechanical?
     - Are phase sizes sensible — not one step per phase (review churn), not so many steps that a reviewer's findings force rewriting the whole phase? A single phase for the whole task is acceptable ONLY when no earlier point yields a working, verifiable state.
     - Does every checklist item and every rubric criterion in `## Acceptance Criteria` appear against at least one phase, and does each phase list only criteria genuinely due at that checkpoint rather than end-of-task criteria?
     - Is the task file free of threshold values, scores and judge configuration, which belong to the orchestrator?
     - 1=Phases are arbitrary cuts or leave a broken state, 2=Milestones partly hold or reviewer tiers are off, 3=Acceptable, 4=Well-designed milestones with justified reviewer tiers, 5=Every phase a clean, self-contained, correctly reviewed milestone
  ```

CRITICAL: use prompt exactly as is, do not add anything else. Including output of implementation agent!!!

**Decision Logic:**

- **PASS** (score >= `THRESHOLD`): Decomposition complete, workflow done — promote the task
- **FAIL** (score < `THRESHOLD`): Re-launch Phase 4 with feedback, at the tier per the [Escalation Rule](#escalation-rule) (unless accepted per the [Iteration Discretion Rule](#iteration-discretion-rule))
- **MAX_ITERATIONS reached**: Promote the task regardless of score (log warning)

**Wait for PASS before promoting the task.**

---

## Promote Task

**Purpose:** Move the refined task from draft to todo folder. This is a file move you perform yourself — no sub-agent, no model tier, no judge.

After all phases complete:

1. **Move task file from draft to todo:**

   ```bash
   git mv <TASK_FILE> .specs/tasks/todo/
   # Fallback if git not available: mv <TASK_FILE> .specs/tasks/todo/
   ```

2. **Do NOT move `.specs/sub-tasks/<task-name>/`.** The sub-task folder is created at planning time and stays put while the task file travels `draft/` → `todo/` → `in-progress/` → `done/`, so the paths recorded in the Parallelization Overview never go stale.

3. **Update any references** in research and analysis files if needed

---

## Completion

After all executed phases and judges complete:

1. Use git tool to stage the task file, the sub-task files under `.specs/sub-tasks/<task-name>/`, skill file, analysis file, and scratchpad files (only those that were created)
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
| **Phases** | `<count, each with its reviewer model, or "N/A">` |
| **Max Parallel Width** | `<peak concurrent steps, 1–5, or "N/A">` |
| **Sub-Task Files** | `.specs/sub-tasks/<task-name>/ — <count> files` or `"N/A"` |

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
├── sub-tasks/
│   └── <task-name>/             # One folder per task — NEVER moves with the task file
│       ├── 01-<step-slug>.md    # One sub-task file per implementation step
│       └── 02a-<step-slug>.md
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
