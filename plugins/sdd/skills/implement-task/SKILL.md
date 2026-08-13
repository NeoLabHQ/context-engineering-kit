---
name: implement-task
description: Implement a task step by step with automated LLM-as-Judge verification at the end of each phase
argument-hint: Task file [--continue] [--refine] [--human-in-the-loop] [--target-quality] [--max-iterations] [--skip-reviews] [--model opus|sonnet|haiku] [--strict]
---

# Implement Task with Verification

Your job is to implement solution in best quality using task specification and sub-agents. You MUST NOT stop until it is critically necessary or you are done! Avoid asking questions until it is critically necessary! Dispatch one implementation agent per step, then — when every step of an implementation phase is done — launch ONE `sdd:code-reviewer` for that phase, iterate till issues are fixed, then move to the next phase!

Execute task implementation steps with automated quality verification using a single `sdd:code-reviewer` agent per implementation phase.

## User Input

```text
$ARGUMENTS
```

---

## Vocabulary (read this first — two different things are called "phase")

| Term | Meaning |
|------|---------|
| **Workflow Phase 0-5** | The stages of THIS skill (select task, load, execute, DoD, move, report). |
| **Implementation phase** / `Phase N` | A milestone in the TASK file's `### Phase Overview`. It groups steps, names a `Reviewer model`, and lists the acceptance criteria due at that milestone. This is the unit of code review. |
| **Step** | One sub-task file at `.specs/sub-tasks/<task-name>/<NN>-<step-slug>.md`. This is the unit of implementation dispatch. The **step name** is that file's basename without `.md`. |

---

## Command Arguments

Parse the following arguments from `$ARGUMENTS`:

### Argument Definitions

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task-file` | Path or filename | Auto-detect | Task file name or path (e.g., `add-validation.feature.md`) |
| `--continue` | `--continue` | None | Continue implementation from the last completed step: resolves the implementation phase in progress, completes its outstanding steps, then reviews that phase — see [Context Resolution for `--continue`](#context-resolution-for---continue). |
| `--refine` | `--refine` | `false` | Incremental refinement mode - detect changes against git, map them to steps, and re-verify from the implementation phase that owns the earliest affected step. |
| `--human-in-the-loop` | `--human-in-the-loop [Phase 1,Phase 3,...]` | None | Implementation phases after whose review to pause for human verification. If no phases specified, pauses after every implementation phase. |
| `--target-quality` | `--target-quality X.X` | `4.0` | Single target threshold value (out of 5.0) applied to every implementation phase review. |
| `--max-iterations` | `--max-iterations N` | `3` | Maximum fix→re-review cycles per implementation phase. Default is 3 iterations. Set to `unlimited` for no limit. |
| `--skip-reviews` | `--skip-reviews` | `false` | Skip all phase reviews - steps proceed without quality gates. |
| `--model` | `opus\|sonnet\|haiku` | Unset | Model for **all** sub-agents (implementation agents AND `sdd:code-reviewer`) that **overrides** every model in the task file; when omitted, step models come from the Parallelization Overview and reviewer models from the Phase Overview. |
| `--strict` | `--strict` | `false` | Disable the [Iteration Discretion Rule](#iteration-discretion-rule) - a phase is marked PASS ONLY when `combined_score >= THRESHOLD`, otherwise iterate until `MAX_ITERATIONS` is reached. |

### Configuration Resolution

Parse `$ARGUMENTS` and resolve configuration as follows:

```
# Extract task file (first positional argument, optional - auto-detect if not provided)
TASK_FILE = first argument that is a file path or filename

# Single quality threshold — there is exactly one, and it is NEVER read from the task file
THRESHOLD = --target-quality value || 4.0

# Initialize other defaults
MODEL_OVERRIDE = --model value (opus|sonnet|haiku) || none  # none = no override; models come from the task file
MAX_ITERATIONS = --max-iterations || 3  # default is 3 iterations
HUMAN_IN_THE_LOOP_PHASES = --human-in-the-loop || [] (empty = none, "*" = all implementation phases)
SKIP_REVIEWS = --skip-reviews || false
REFINE_MODE = --refine || false
CONTINUE_MODE = --continue || false
STRICT_MODE = --strict || false

# Special handling for --human-in-the-loop without a phase list
if --human-in-the-loop present without phase identifiers:
    HUMAN_IN_THE_LOOP_PHASES = "*" (all implementation phases)
```

**`THRESHOLD` is the ONLY quality threshold in this workflow.** There is no separate standard/critical/lenient value, no comma-separated form, and no threshold anywhere in the task file — the planning agents are forbidden from writing one.

### Context Resolution for `--continue`

When `--continue` is used, state is resolved by **implementation phase, then step**:

1. **Phase and Step Resolution:**
   - Read the task file's `### Parallelization Overview` step table and `### Phase Overview`.
   - A step is complete when its row in the step table is marked `[DONE]`.
   - An implementation phase is complete when its `#### Phase N` heading carries **either** marker: `[REVIEWED]` (its review ran and passed) or `[REVIEWED-SKIPPED]` (its steps finished and its review was deliberately suppressed by an earlier `--skip-reviews` run).
   - `RESUME_PHASE` = the first implementation phase marked **neither** `[REVIEWED]` **nor** `[REVIEWED-SKIPPED]`. Treating `[REVIEWED-SKIPPED]` as unfinished would re-run exactly the review the user suppressed.
   - `RESUME_STEPS` = the steps of `RESUME_PHASE` that are not `[DONE]`, in dependency order.
2. **Verify the resumed phase's existing work:**
   - If `RESUME_PHASE` already has some `[DONE]` steps but neither marker, and `RESUME_STEPS` is empty (all steps done, review never ran):
     - **If `SKIP_REVIEWS` is true: launch nothing.** Mark the phase `[REVIEWED-SKIPPED]` and resume at the next implementation phase.
     - Otherwise: launch the `sdd:code-reviewer` for `RESUME_PHASE` (passing the 4 inputs documented in Workflow Phase 2) — **Model**: `MODEL_OVERRIDE` if set — otherwise that phase's `Reviewer model`.
       - If the phase PASSES per the [Iteration Discretion Rule](#iteration-discretion-rule): mark it `[REVIEWED]` and resume at the next implementation phase.
       - Otherwise: enter the [Failure Handling](#failure-handling-reason-about-blast-radius-your-most-critical-judgement) flow for that phase.
   - If `RESUME_STEPS` is non-empty: dispatch those steps first, then review the phase as normal — and `SKIP_REVIEWS` still suppresses that review, marking the phase `[REVIEWED-SKIPPED]` instead.
3. **State Recovery:**
   - Check task file location (`in-progress/`, `todo/`, `done/`)
   - If in `todo/`, move to `in-progress/` before continuing
   - Pre-populate captured values from existing artifacts

### Refine Mode Behavior (`--refine`)

When `--refine` is used, it detects changes to **project files** (not the task file) and maps them to steps, then re-verifies from the implementation phase that owns the earliest affected step.

1. **Detect Changed Project Files:**

   First, determine what to compare against based on git state:

   ```bash
   # Check for staged changes
   STAGED=$(git diff --cached --name-only)

   # Check for unstaged changes
   UNSTAGED=$(git diff --name-only)
   ```

   **Comparison logic:**

   | Staged | Unstaged | Compare Against | Command |
   |--------|----------|-----------------|---------|
   | Yes | Yes | Staged (unstaged only) | `git diff --name-only` |
   | Yes | No | Last commit | `git diff HEAD --name-only` |
   | No | Yes | Last commit | `git diff HEAD --name-only` |
   | No | No | No changes | Exit with message |

   - If **both staged AND unstaged**: Compare working directory vs staging area (unstaged changes only)
   - If **only staged OR only unstaged**: Compare against last commit
   - This ensures refine operates on the most recent work in progress

2. **Map Changes to Steps:**
   - Read the task file's `### Parallelization Overview` to get every step name, its implementation phase, and its `Sub-Task File` path.
   - **Refine mode is the ONE case where you may read sub-task files**: they are specification artifacts (like the task file), not implementation outputs, and their `#### Expected Output` sections are the only place file paths per step are recorded. Read ONLY the `#### Expected Output` and `#### Subtasks` sections you need.
   - Build a mapping: `{changed_file → step name → implementation phase}`

3. **Determine Affected Scope:**
   - Find all steps that have associated changed files
   - `REFINE_FROM_PHASE` = the earliest implementation phase containing an affected step
   - All implementation phases from that point onwards need re-verification
   - Earlier phases (unaffected) are preserved as-is

4. **Refine Execution:**
   - For each affected implementation phase (in order):
     - Launch ONE **`sdd:code-reviewer` agent** to verify the phase (including the user's changes), passing the 4 standard inputs — **Model**: `MODEL_OVERRIDE` if set — otherwise that phase's `Reviewer model`
     - If the phase PASSES per the [Iteration Discretion Rule](#iteration-discretion-rule): mark it `[REVIEWED]`, proceed to the next phase
     - Otherwise: enter the [Failure Handling](#failure-handling-reason-about-blast-radius-your-most-critical-judgement) flow, then re-review
   - User's manual fixes are preserved - implementation agents should build upon them, not overwrite

5. **Example:**

   ```bash
   # User manually fixed src/validation/validation.service.ts
   # (This file is the Expected Output of step `02-validation-service`, in Phase 1)

   /implement my-task.feature.md --refine

   # Detects: src/validation/validation.service.ts modified
   # Maps to: step `02-validation-service` → Phase 1
   # Action: Launch ONE sdd:code-reviewer for Phase 1
   #   - If PASS: User's fix is good, proceed to Phase 2
   #   - If FAIL: reason about blast radius, dispatch fixes for the affected
   #     steps only, without overwriting the user's changes, then re-review
   # Continues: Phase 2, Phase 3... (re-verify all subsequent phases)
   ```

6. **Multiple Files Changed:**

   ```bash
   # User edited an output of a Phase 1 step AND an output of a Phase 3 step

   /implement my-task.feature.md --refine

   # Earliest affected phase: Phase 1
   # Re-verifies: Phase 1, Phase 2, Phase 3...
   # (Phase 2 re-verified even though no direct changes, because it builds on Phase 1)
   ```

7. **Staged vs Unstaged Changes:**

   ```bash
   # Scenario: User staged some changes, then made more edits
   # Staged: src/validation/validation.service.ts (git add done)
   # Unstaged: src/validation/validators/email.validator.ts (still editing)

   /implement my-task.feature.md --refine

   # Detects: Both staged AND unstaged changes exist
   # Mode: Compares unstaged only (working dir vs staging)
   # Only email.validator.ts is considered for refine

   # --

   # Scenario: User only has staged changes (ready to commit)
   # Staged: src/validation/validation.service.ts
   # Unstaged: none

   /implement my-task.feature.md --refine

   # Detects: Only staged changes
   # Mode: Compares against last commit
   ```

### Human-in-the-Loop Behavior

Human verification checkpoints are keyed on **implementation phases**, never on individual steps.

1. **Trigger Conditions:**
   - After an orchestrator-level **PASS** on the review of an implementation phase in `HUMAN_IN_THE_LOOP_PHASES`
   - After a fix iteration completes for such a phase (before the next re-review)
   - If `HUMAN_IN_THE_LOOP_PHASES` is `"*"`, triggers after every implementation phase

2. **At Checkpoint:**
   - Display the phase's step results summary
   - Display generated artifacts with paths
   - Display the reviewer's `combined_score` and consolidated issues
   - Ask user: "Review phase output. Continue? [Y/n/feedback]"
   - If user provides feedback, incorporate into the next iteration or phase
   - If user says "n", pause workflow

3. **Checkpoint Message Format:**

   ```markdown
   ---
   ## 🔍 Human Review Checkpoint - Phase N

   **Phase:** {phase heading}
   **Steps:** {step names}
   **Reviewer model:** {model used}
   **Combined Score:** {combined_score}/5.0 (threshold: {THRESHOLD})
   **Status:** ✅ PASS / ☑️ ACCEPTED / 🔄 ITERATING (attempt {n})

   **Artifacts Created/Modified:**
   - {artifact_path_1}
   - {artifact_path_2}

   **Reviewer Feedback (top issues):**
   {feedback summary — High/Medium issues from reviewer.issues, with the step each belongs to}

   **Action Required:** Review the above artifacts and provide feedback or continue.

   > Continue? [Y/n/feedback]:
   ---
   ```

---

## Task Selection and Status Management

### Task Status Folders

Task status is managed by folder location:

- `.specs/tasks/todo/` - Tasks waiting to be implemented
- `.specs/tasks/in-progress/` - Tasks currently being worked on
- `.specs/tasks/done/` - Completed tasks

The task's sub-task folder `.specs/sub-tasks/<task-name>/` **never moves** while the task file travels between these folders, so the `Sub-Task File` paths recorded in the task file stay valid.

### Status Transitions

| When | Action |
|------|--------|
| Start implementation | Move task from `todo/` to `in-progress/` |
| Final verification PASS | Move task from `in-progress/` to `done/` |
| Implementation failure (user aborts) | Keep in `in-progress/` |

---

## CRITICAL: You Are an ORCHESTRATOR ONLY

**Your role is DISPATCH and AGGREGATE. You do NOT do the work.**

Properly build context of sub agents!

CRITICAL: For each sub-agent you dispatch, you MUST provide:

**For an implementation agent (one per step):**

- Task file path
- **That step's sub-task file path** — exactly one, taken from the `Sub-Task File` column of the Parallelization Overview
- **Value of `${CLAUDE_PLUGIN_ROOT}` so agents can resolve paths like `@${CLAUDE_PLUGIN_ROOT}/scripts/create-scratchpad.sh`**

**For the `sdd:code-reviewer` (one per implementation phase):**

- Task file path
- Phase identifier
- Artifact path(s) reported by that phase's implementation agents
- `CLAUDE_PLUGIN_ROOT`

### What You DO

- Read the task file ONCE (Workflow Phase 1 only)
- Launch sub-agents via Task tool
- Receive reports from sub-agents
- Mark steps and implementation phases complete after the orchestrator-level PASS rule on reviewer output as [DONE]
- Reason about blast radius when a phase review fails, and choose fix / re-review models accordingly
- Aggregate results and report to user

### What You NEVER Do

| Prohibited Action | Why | What To Do Instead |
|-------------------|-----|-------------------|
| Read implementation outputs | Context bloat → command loss | Sub-agent reports what it created |
| Read sub-task files (except `--refine` mapping) | The implementation agent reads its own sub-task file | Pass the path from the Parallelization Overview |
| Read reference files | Sub-agent's job to understand patterns | Include path in sub-agent prompt |
| Read artifacts to "check" them | Context bloat → forget verifications | Launch `sdd:code-reviewer` agent |
| Evaluate code quality yourself | Not your job, causes forgetting | Launch `sdd:code-reviewer` agent |
| Review a step individually | Review is a PHASE-level gate | Review once, at the end of the phase |
| Skip a phase review "because simple" | Every phase review is mandatory unless `--skip-reviews` | Launch `sdd:code-reviewer` anyway |
| Never add comments/marks/notes about results of review, scratchpads, iterations, etc. to the task file. | The task file is a specification artifact, not a log. If task not done, it should be visible from code only! | You can write only [DONE] mark ever, or nothing at all! |

### Anti-Rationalization Rules

**If you think:** "I should read this file to understand what was created"
**→ STOP.** The sub-agent's report tells you what was created. Use that information.

**If you think:** "I'll quickly verify this looks correct"
**→ STOP.** Launch a `sdd:code-reviewer` agent. That's not your job.

**If you think:** "This phase is too simple to need verification"
**→ STOP.** Unless `SKIP_REVIEWS` is true, every implementation phase gets exactly one review. No exceptions.

**If you think:** "This step looks risky, I'll review it before the phase ends"
**→ STOP.** Reviewing per step is exactly what this workflow removed. Wait for the phase to complete.

**If you think:** "I need to read the sub-task file to write a good prompt"
**→ STOP.** Put the sub-task file PATH in the sub-agent prompt. The sub-agent reads it.

### Why This Matters

Orchestrators who read files themselves = context overflow = command loss = forgotten steps. Every time.

Orchestrators who "quickly verify" = skip `sdd:code-reviewer` agents = quality collapse = failed artifacts.

**Your context window is precious. Protect it. Delegate everything.**

---

## CRITICAL

### Configuration Rules

- **Model precedence (`MODEL_OVERRIDE`): if `--model` was given, that model WINS over the task file and over every default in this skill — dispatch EVERY sub-agent with it (implementation agents of any type AND `sdd:code-reviewer`), ignoring the Parallelization Overview's `Model` column and the Phase Overview's `Reviewer model`. It is an override, NOT a fallback. If `--model` was NOT given (`MODEL_OVERRIDE = none`), model selection is unchanged: each step uses the `Model` its Parallelization Overview row names, and each phase review uses that phase's `Reviewer model`, falling back to the default named in each dispatch block.**
- Use the single `THRESHOLD` (default 4.0) for every implementation phase review. There is no per-component, per-criticality or lenient variant.
- **Never read a threshold from the task file.** The planning agents write none; if one somehow appears, ignore it.
- The threshold is applied at THIS orchestrator layer against `combined_score` returned by code-reviewer. **NEVER pass any threshold to the code-reviewer agent — or he will try to reach target score and as result become subjective.**
- A phase PASSES if `combined_score >= THRESHOLD`. If `3.0 <= combined_score < THRESHOLD`, the phase passes ONLY when the [Iteration Discretion Rule](#iteration-discretion-rule) says so — never below the fixed floor of `3.0`. If `combined_score < 3.0`, the phase FAILS unconditionally.
- **Default is 3 iterations** - stop after 3 fix→re-review cycles for an implementation phase and proceed to the next phase (with warning)!
- If `MAX_ITERATIONS` is set to `unlimited`: Iterate until the quality threshold is met (no limit)
- Trigger human-in-the-loop checkpoints ONLY after implementation phases in `HUMAN_IN_THE_LOOP_PHASES` (or all phases if `"*"`)!
- **If `SKIP_REVIEWS` is true: Skip ALL code-reviewer dispatches - proceed directly to the next implementation phase after its steps complete!**
- **If `CONTINUE_MODE` is true: Skip to `RESUME_PHASE` / `RESUME_STEPS` - do not re-implement already completed steps!**
- **If `REFINE_MODE` is true: Detect changed project files, map to steps, re-verify from `REFINE_FROM_PHASE` - preserve user's fixes!**
- **If `STRICT_MODE` is true: The [Iteration Discretion Rule](#iteration-discretion-rule) is DISABLED - a phase passes ONLY on `combined_score >= THRESHOLD`, otherwise iterate until `MAX_ITERATIONS`!**

### Execution & Evaluation Rules

- **Use foreground agents only**: Do not use background agents. Launch parallel agents when possible. Background agents constantly run in permissions issues and other errors.
- **Parallelism comes from the task file**: steps whose `Parallel with:` column names each other MUST be dispatched simultaneously in one message. Never serialize what the plan says is parallel.
- **Never cross a phase boundary in parallel**: a step of `Phase N+1` may only start after `Phase N` has been reviewed and marked `[REVIEWED]` (or marked `[REVIEWED-SKIPPED]` when `SKIP_REVIEWS` is true).

Relaunch the code-reviewer till you get valid results, if following happens:

- Reject Long Reports: If the code-reviewer returns a very long report instead of using the scratchpad as requested, reject the result. This indicates the agent failed to follow the "use scratchpad" instruction.
- Combined Score 5.0 is a Hallucination: If the code-reviewer returns a `combined_score` of exactly 5.0/5.0, treat it as a hallucination or lazy evaluation. Reject it and re-run the agent. This applies to the **weighted aggregate only** — an individual criterion may legitimately score 5 and no score is rationed, but every criterion across spec compliance, code quality and Muda waste analysis landing strictly past its `score_4` anchor at once is not a plausible review outcome. Never use it as a reason to question a single high criterion score.
- Reject Missing Scores: If the code-reviewer's report is missing the `combined_score` (or any sub-score: `spec_compliance_score`, `builtin_score`), reject it. This indicates the agent failed to follow the rubric instructions.
- Reject PASS/FAIL Verdicts in Report: If the code-reviewer's output contains a PASS/FAIL verdict or references a threshold, reject it. The orchestrator owns that decision; the agent must remain threshold-blind.
- Reject Out-of-Scope Findings: If the reviewer penalizes acceptance criteria that the phase's `#### Phase N` block does NOT list — reporting work a LATER phase delivers as "missing" or "incomplete" — reject the report and re-run the agent, restating that a phase is a checkpoint, not the finish line.

#### Iteration Discretion Rule

Your main task is to COMPLETE the task within target quality. Two failure modes are equally real:

- Burning iterations and context on nitpicks so the overall task never completes → **the task is failed**.
- Accepting a result whose quality is genuinely too poor to be considered complete → **an even worse failure**.

Apply to every implementation phase's `combined_score`:

- **`combined_score < 3.0` → FAIL, unconditionally. No discretion.** Iterate with reviewer feedback until the phase passes or `MAX_ITERATIONS` is reached.
- **`3.0 <= combined_score < THRESHOLD` → discretion band.** ONLY inside this band MAY you decide that a phase below the target is acceptable. The fixed floor is `3.0` and the band ceiling is `THRESHOLD`. If `--target-quality` set `THRESHOLD <= 3.0` the band is empty: every score is either an unconditional FAIL (`< 3.0`) or a PASS, and there is no discretion to exercise.
- Inside the band, when the outstanding issues are ONLY `Low`/`Medium` priority (any `High` or `Critical` finding removes discretion entirely) AND none of them breaks an acceptance criterion the phase is responsible for or causes a meaningful defect (i.e. they are nitpicks), you MUST reason FIRST — before dispatching another iteration — about whether iterating (or marking the phase failed) is worth the time and context cost.
- **At most ONE nitpick-driven iteration**, and it counts against `MAX_ITERATIONS`. If it again surfaces only nitpicks, you MUST mark the phase PASS (☑️ ACCEPTED in the summary table), report the outstanding issues in the final report, and continue with the next phase. If it returns a `combined_score` below `3.0`, the FAIL path applies instead.
- **A phase that does not build, lint or test green is NEVER inside the discretion band**, whatever the score says. Each phase must leave a working, committable, CI-green state.
- You MUST be critical, NOT lenient. Stopping short of target MUST be an intentional decision grounded in the absence of real, requirement-breaking issues. A genuine blocking issue that prevents completing the phase within `MAX_ITERATIONS` MUST be reported as a failure, never papered over.
- **If `STRICT_MODE` is true, this whole rule is DISABLED**: stop only when `combined_score >= THRESHOLD` or `MAX_ITERATIONS` is reached. `--strict` changes nothing else — `THRESHOLD`, `MAX_ITERATIONS`, the `< 3.0` unconditional FAIL, human-in-the-loop checkpoints, code-reviewer dispatch and `--skip-reviews` are unaffected. With `--skip-reviews` no `combined_score` is produced at all, so both this rule and `--strict` are inert.

---

## Overview

This command orchestrates multi-step task implementation with:

1. **Sequential execution** respecting step dependencies
2. **Parallel execution** where the plan's `Parallel with:` column allows
3. **One implementation agent per step**, dispatched with the task file path AND its sub-task file path
4. **One automated verification per implementation phase**, at that phase's `Reviewer model`
5. **Blast-radius reasoning** to pick the fix and re-review models when a phase review fails
6. **Progress tracking** with confirmation after each orchestrator-level PASS

---

## Complete Workflow Overview

```
Workflow Phase 0: Select Task & Move to In-Progress
    │
    ├─── Use provided task file name or auto-select from todo/ (if only 1 task)
    ├─── Move task: todo/ → in-progress/
    │
    ▼
Workflow Phase 1: Load Task
    │   Parse ### Parallelization Overview (steps, models, agents, sub-task paths)
    │   Parse ### Phase Overview (phases, steps, reviewer models, criteria due)
    │
    ▼
Workflow Phase 2: Execute Implementation Phases
    │
    ├─── For each implementation phase, in order:
    │    │
    │    ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ For each step of the phase, in dependency order │
    │    │ (parallel steps dispatched simultaneously):     │
    │    │   Launch its agent at its Model with            │
    │    │   task file path + sub-task file path           │
    │    └─────────────────┬───────────────────────────────┘
    │                      │  all steps of the phase reported complete
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Launch ONE sdd:code-reviewer for the PHASE      │
    │    │ at the phase's Reviewer model                   │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Orchestrator reads combined_score and applies   │
    │    │ THRESHOLD:                                      │
    │    │  PASS → Mark phase [REVIEWED], next phase       │
    │    │  FAIL → Reason about BLAST RADIUS, choose fix   │
    │    │         model + scope + re-review model,        │
    │    │         re-review (max MAX_ITERATIONS)          │
    │    └─────────────────────────────────────────────────┘
    │
    ▼
Workflow Phase 3: Definition of Done Verification
    │
    ├─── Verify all Definition of Done items
    │    │
    │    ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Launch sdd:developer agent                      │
    │    │ (verify all DoD items)                          │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ All DoD PASS? → Proceed to Workflow Phase 4     │
    │    │ Any FAIL? → Fix and re-verify (iterate)         │
    │    └─────────────────────────────────────────────────┘
    │
    ▼
Workflow Phase 4: Move Task to Done
    │
    ├─── Move task: in-progress/ → done/
    │
    ▼
Workflow Phase 5: Final Report
```

---

## Workflow Phase 0: Parse User Input and Select Task

Parse user input to get the task file path and arguments.

### Step 0.1: Resolve Task File

**If `$ARGUMENTS` is empty or only contains flags:**

1. **Check in-progress folder first:**

   ```bash
   ls .specs/tasks/in-progress/*.md 2>/dev/null
   ```

   - If exactly 1 file → Set `$TASK_FILE` to that file, `$TASK_FOLDER` to `in-progress`
   - If multiple files → List them and ask user: "Multiple tasks in progress. Which one to continue?"
   - If no files → Continue to step 2

2. **Check todo folder:**

   ```bash
   ls .specs/tasks/todo/*.md 2>/dev/null
   ```

   - If exactly 1 file → Set `$TASK_FILE` to that file, `$TASK_FOLDER` to `todo`
   - If multiple files → List them and ask user: "Multiple tasks in todo. Which one to implement?"
   - If no files → Report "No tasks available. Create one with /add-task first." and STOP

**If `$ARGUMENTS` contains a task file name:**

1. Search for the file in order: `in-progress/` → `todo/` → `done/`
2. Set `$TASK_FILE` and `$TASK_FOLDER` accordingly
3. If not found, report error and STOP

### Step 0.2: Move to In-Progress (if needed)

**If task is in `todo/` folder:**

```bash
git mv .specs/tasks/todo/$TASK_FILE .specs/tasks/in-progress/
# Fallback if git not available: mv .specs/tasks/todo/$TASK_FILE .specs/tasks/in-progress/
```

Update `$TASK_PATH` to `.specs/tasks/in-progress/$TASK_FILE`

**If task is already in `in-progress/`:**
Set `$TASK_PATH` to `.specs/tasks/in-progress/$TASK_FILE`

**Do NOT move the sub-task folder.** `.specs/sub-tasks/<task-name>/` stays where planning created it; the `Sub-Task File` paths in the task file already point there.

### Step 0.3: Parse Flags and Initialize Configuration

Parse all flags from `$ARGUMENTS` and initialize configuration.
**Display resolved configuration:**

```markdown
### Configuration

| Setting | Value |
|---------|-------|
| **Task File** | {TASK_PATH} |
| **Model Override** | {MODEL_OVERRIDE or "None (models from task file)"} |
| **Threshold** | {THRESHOLD}/5.0 |
| **Max Iterations** | {MAX_ITERATIONS or "3"} |
| **Human Checkpoints** | {HUMAN_IN_THE_LOOP_PHASES as comma-separated or "All phases" or "None"} |
| **Skip Reviews** | {SKIP_REVIEWS} |
| **Continue Mode** | {CONTINUE_MODE} |
| **Refine Mode** | {REFINE_MODE} |
| **Strict Mode** | {STRICT_MODE} |
```

### Step 0.4: Handle Continue Mode

**If `CONTINUE_MODE` is true:** resolve `RESUME_PHASE` and `RESUME_STEPS` per [Context Resolution for `--continue`](#context-resolution-for---continue), then in Workflow Phase 2 skip every implementation phase before `RESUME_PHASE` and every `[DONE]` step inside it.

### Step 0.5: Handle Refine Mode

**If `REFINE_MODE` is true:**

1. **Detect Changed Project Files:**

   ```bash
   # Check for staged and unstaged changes
   STAGED=$(git diff --cached --name-only)
   UNSTAGED=$(git diff --name-only)
   ```

   **Determine comparison mode:**

   ```
   if STAGED is not empty AND UNSTAGED is not empty:
       # Both staged and unstaged - use unstaged only
       CHANGED_FILES = git diff --name-only  # working dir vs staging
       COMPARISON_MODE = "unstaged_only"
   elif STAGED is not empty OR UNSTAGED is not empty:
       # Only one type - compare against last commit
       CHANGED_FILES = git diff HEAD --name-only
       COMPARISON_MODE = "vs_last_commit"
   else:
       # No changes
       Report: "No project changes detected. Make edits first, then run --refine."
       Exit
   ```

2. **Build the Step→File Mapping:**
   - Read the task file's `### Parallelization Overview` for step names, phases and `Sub-Task File` paths
   - Read those sub-task files' `#### Expected Output` and `#### Subtasks` sections for file paths (the one permitted exception to context protection — see [Refine Mode Behavior](#refine-mode-behavior---refine))
   - Build mapping: `STEP_FILE_MAP = {step name → [file paths]}` and `STEP_PHASE_MAP = {step name → implementation phase}`

3. **Map Changed Files to Steps:**

   ```
   AFFECTED_STEPS = []
   for each changed_file:
       for step_name, file_list in STEP_FILE_MAP:
           if changed_file matches any path in file_list:
               AFFECTED_STEPS.append(step_name)
   ```

   - If no steps matched: "Changed files don't map to any step's Expected Output. Verify manually."

4. **Determine Refine Scope:**
   - `REFINE_FROM_PHASE` = the earliest implementation phase among `STEP_PHASE_MAP[AFFECTED_STEPS]`
   - All implementation phases from `REFINE_FROM_PHASE` onwards need re-verification
   - Phases before `REFINE_FROM_PHASE` are preserved as-is

5. **Store Changed Files Context:**
   - `CHANGED_FILES` = list of changed file paths
   - `USER_CHANGES_CONTEXT` = git diff output for affected files
   - Pass this context to the implementation agents you dispatch for fixes
   - Agents should build upon user's fixes, not overwrite them

## Workflow Phase 1: Load and Analyze Task

**This is the ONLY phase where you read a file** (plus the sub-task `#### Expected Output` sections in `--refine` mode).

### Step 1.1: Load Task Details

Read the task file ONCE:

```bash
Read $TASK_PATH
```

**After this read, you MUST NOT read any other files for the rest of execution.**

### Step 1.2: Parse the Implementation Process

Parse the `## Implementation Process` section into two working structures.

**From `### Parallelization Overview`** — the step table has columns `| Step | Phase | Model | Agent | Depends on | Parallel with | Sub-Task File |`. Build, per step name:

| Field | Source | Used for |
|-------|--------|----------|
| Step name | `Step` column (backtick-quoted sub-task basename) | Identity in all other lists |
| Implementation phase | `Phase` column | Which review gate it belongs to |
| Model | `Model` column | The `model` of its dispatch (unless `MODEL_OVERRIDE`) |
| Agent | `Agent` column | The `sdd:` agent type to dispatch |
| Depends on | `Depends on` column | Ordering |
| Parallel with | `Parallel with` column | Which steps to dispatch in ONE message |
| Sub-Task File | `Sub-Task File` column | The path you pass to the agent |

**From `### Phase Overview`** — for each `#### Phase N` block, record `Steps:`, `Reviewer model:`, the `Checklist items:` list and the `Rubrics:` list. You use `Reviewer model:` to dispatch the review; the criteria lists are the reviewer's business, not yours — do NOT paste them into any prompt.

There is **no threshold, no verification level and no judge count** in the task file. Do not look for them.

### Step 1.3: Create Todo List

Create TodoWrite with one entry per step plus one entry per implementation phase review:

```json
{
  "todos": [
    {"content": "Phase 1 / Step 01-foundation [haiku]", "status": "pending", "activeForm": "Implementing 01-foundation"},
    {"content": "Phase 1 / Step 02a-service [sonnet]", "status": "pending", "activeForm": "Implementing 02a-service"},
    {"content": "Phase 1 review [reviewer: sonnet]", "status": "pending", "activeForm": "Reviewing Phase 1"},
    {"content": "Phase 2 / Step 03-integration [sonnet]", "status": "pending", "activeForm": "Implementing 03-integration"},
    {"content": "Phase 2 review [reviewer: opus]", "status": "pending", "activeForm": "Reviewing Phase 2"}
  ]
}
```

---

## Workflow Phase 2: Execute Implementation Phases

Process implementation phases **in order**. Within a phase, process steps in dependency order, dispatching `Parallel with:` groups simultaneously. When every step of the phase has reported completion, run the phase review — once.

There is exactly ONE dispatch pattern, and it applies to every implementation phase without exception.

### The Phase Review Pattern

```
for each implementation phase P, in order:
    for each dependency-ordered group G of steps in P:
        dispatch every step of G in ONE message (parallel), each with:
            agent type   = its Agent column
            model        = MODEL_OVERRIDE if set, else its Model column
            prompt       = task file path + its sub-task file path
        collect each agent's reported artifact paths

    if SKIP_REVIEWS:
        mark P [REVIEWED-SKIPPED]; continue to the next phase

    dispatch ONE sdd:code-reviewer for P with the 4 inputs
        model = MODEL_OVERRIDE if set, else P's `Reviewer model`

    apply THRESHOLD to combined_score
        PASS      → mark P [REVIEWED]; human checkpoint if due; next phase
        FAIL      → Failure Handling (blast radius) → re-review; up to MAX_ITERATIONS
```

### Step Dispatch (one implementation agent per step)

Use Task tool, one call per step (all steps of a `Parallel with:` group in a single message):

- **Agent Type**: the step's `Agent` column, prefixed `sdd:` (e.g. `sdd:developer`, `sdd:tech-writer`)
- **Model**: `MODEL_OVERRIDE` if set — otherwise the step's `Model` column — otherwise `sonnet`
- **Description**: "Implement step [step-name]"
- **Prompt**:

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

Implement step `[step-name]`.

Task File: $TASK_PATH
Sub-Task File: [the Sub-Task File path from the Parallelization Overview]

Your task:
- Read the sub-task file first — it IS your step
- Read the task file for Description, Acceptance Criteria (including the Test Strategy) and Architecture Overview
- Execute ONLY this step. Do NOT execute any other step, even one you can see in the Parallelization Overview
- Follow the sub-task file's Expected Output, Success Criteria and Subtasks exactly
- Your phase is a checkpoint, not the finish line: implement what this step delivers, and do not pull later phases' work forward
- Leave the tree building, linting and testing green

When complete, report:
1. What files were created/modified (paths)
2. Confirmation that the sub-task's success criteria are met
3. Self-critique summary
4. Any issues encountered
```

**Do NOT** paste the step's goal, expected output, success criteria or subtasks into the prompt. The agent reads its sub-task file. Passing the path is the contract; pasting the content is context bloat and drift.

Collect the artifact paths from each report. **Do NOT read the artifacts.**

### Code-Reviewer Input Contract (NON-NEGOTIABLE)

Every `sdd:code-reviewer` dispatch MUST include exactly these 4 inputs and NOTHING else that resembles a threshold or pass/fail expectation (the Task tool's `model` parameter is a dispatch setting, not a prompt input — see `MODEL_OVERRIDE`):

1. **Task file path**: `$TASK_PATH`
2. **Phase identifier**: the phase being reviewed, exactly as written in `### Phase Overview` (e.g. `Phase 2`)
3. **Artifact path(s)**: every file path the phase's implementation agents reported as created or modified
4. **CLAUDE_PLUGIN_ROOT**: The plugin root path

**Dispatch prompt:**

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

Apply your full evaluation process (Stages 0-12) and return a single combined report.

Inputs:

1. Task file path:
   $TASK_PATH

2. Phase identifier:
   [e.g. Phase 2]

3. Artifact path(s):
   [every file path reported by this phase's implementation agents]

4. CLAUDE_PLUGIN_ROOT: ${CLAUDE_PLUGIN_ROOT}
```

**You MUST NOT pass to the code-reviewer:**

- Any score threshold, target quality, or passing-line value
- Any PASS/FAIL expectation
- Any rubric or checklist you wrote yourself (only the task file's `## Acceptance Criteria`, narrowed by the Phase Overview, is authoritative)
- The sub-task file paths — **the reviewer resolves them itself** from the Phase Overview's `Steps:` line and the Parallelization Overview's `Sub-Task File` column
- The task description or acceptance criteria text — the agent reads the task file itself

### Threshold Application (Orchestrator-Level Only)

After receiving the code-reviewer's report, the orchestrator (this skill) applies the threshold:

```
combined_score = reviewer.combined_score
all_issues     = reviewer.issues          # each carries the step it belongs to
blast_radius   = reviewer.blast_radius

# PASS rule (orchestrator decides):
if combined_score >= THRESHOLD:
    PASS
elif 3.0 <= combined_score < THRESHOLD and not STRICT_MODE:
    apply the Iteration Discretion Rule → accepted: PASS | declined: FAIL → fix
else:
    FAIL → fix
```

The `combined_score` already incorporates spec_compliance + code_quality + Muda waste analysis (the reviewer aggregates them internally per its STAGE 9). The orchestrator does NOT need to re-aggregate sub-scores; only `combined_score`, `issues` and `blast_radius` matter for the gate decision.

### Failure Handling: Reason About Blast Radius (YOUR MOST CRITICAL JUDGEMENT)

**This is the single most important judgement you make in this workflow. Think thoroughly before you dispatch anything.**

There is no rule table here, and you must not build yourself one. There is a principle:

> **Match the capability of the agent that fixes the phase — and of the agent that re-reviews the fix — to the BLAST RADIUS of the reviewer's findings, not to the models that originally built the phase.**

Before dispatching a single fix, reason **explicitly and in writing** through:

1. **Scope** — which steps do the findings touch? Use `issues[].step` and `blast_radius.affected_steps`. Which steps are demonstrably sound?
2. **Depth** — is this a local defect inside a step, or did the phase come out structurally wrong (`blast_radius.requires_phase_rework`)?
3. **Coupling** — does fixing the affected steps force rewriting the unaffected ones? If yes, the unit of repair is the phase, not the step.
4. **Severity** — High/Critical findings that break an acceptance criterion the phase owns, or Low/Medium nitpicks?
5. **Ceiling** — does the failure look like the implementing model ran out of capability? If a model already failed once on the same finding, dispatching it again at the same tier will fail again. Escalate.

Then decide three things:

- **The fix model** — it may be higher OR lower than the model that originally built the step, and it may differ per step.
- **The fix scope** — which sub-task files to re-dispatch. Never re-dispatch a step whose work is sound; that is how good work gets destroyed.
- **The re-review model** — at least the phase's `Reviewer model`. When you escalate the fix because the phase came out structurally wrong, escalate the re-review too: a review at the tier that let the defect through is not a check.

**Worked example (the anchor case).** A phase of three steps, all built by `haiku`, reviewer `sonnet`, fails its review. The same failure verdict points at two very different repairs depending only on blast radius:

- *Case A — the whole phase failed.* The reviewer reports High findings in all three steps, `requires_phase_rework: true`, and the design of the phase's shared abstraction is wrong. Blast radius = the whole phase; depth = structural; coupling = total; ceiling = `haiku` clearly could not carry this design. **Decision:** re-dispatch the whole phase's steps to `sonnet` (or `opus` if the abstraction is genuinely hard), and re-review at `opus` rather than the phase's `sonnet` — the `sonnet` review is what passed the broken shape to you.
- *Case B — one step failed.* The reviewer reports a single High finding, `affected_steps: [02b-token-service]`, `requires_phase_rework: false`, and the other two steps are clean. Blast radius = one step; depth = local; coupling = none; ceiling = not reached, the defect is a missed edge case rather than a design failure. **Decision:** re-dispatch ONLY `02b-token-service`, still at `haiku`, with the reviewer's issues for that step; leave the other two steps untouched; re-review at the phase's `sonnet`.

**Everything else is DERIVED from that principle, not enumerated.** A mixed-model phase, a phase that fails only on tests, a phase that fails a second time, a phase where two of five steps are coupled — none of these has a pre-written answer. Walk scope → depth → coupling → severity → ceiling, write down your reasoning, and choose. Do NOT reach for a decision matrix; the situations are too varied for one, and a matrix would make you stop thinking exactly where thinking matters most.

Record the reasoning and the choice in the final report so the user can see why each fix model was picked.

### Retry Feedback Construction

For each step you decided to re-dispatch, build this prompt (one per step, parallel where the steps are independent):

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

Fix step `[step-name]` — Phase [N] review iteration [K] of [MAX_ITERATIONS]

Task File: $TASK_PATH
Sub-Task File: [that step's Sub-Task File path]

The phase this step belongs to failed its quality review. Reviewer combined_score: [X.XX] / threshold [THRESHOLD]

Issues attributed to THIS step:
[paste the reviewer.issues entries whose `step` is this step (plus any `phase-wide` entries), verbatim: source, priority, description, evidence (file:line), impact, suggestion]

Full reviewer report (for additional context, do NOT skim — use the issues list as your primary work list):
[path to reviewer's scratchpad report file under .specs/scratchpad/<hex>.md]

Your task:
- Address every High priority issue attributed to this step
- Address every Medium priority issue attributed to this step
- Do NOT introduce functionality beyond your sub-task file's Expected Output
- Do NOT modify files owned by steps that were NOT re-dispatched
- Re-run tests/lint/build to ensure no regressions

When complete, report:
1. Files changed (paths)
2. Per-issue resolution status (Fixed / Partially Fixed / Skipped with justification)
3. Any new concerns introduced by the fix
```

After every re-dispatched step reports completion, dispatch the code-reviewer again for the SAME phase with the SAME 4 inputs (the artifact list may have grown — pass the union). Iterate until PASS or `MAX_ITERATIONS` is reached.

If `MAX_ITERATIONS` is reached:

- Log warning: "Phase [N] did not pass after {MAX_ITERATIONS} iterations (final combined_score: X.XX, threshold: {THRESHOLD})"
- Proceed to the next implementation phase (do not block indefinitely)

### On PASS: Mark the Phase Complete

- Update the task file:
  - Mark each completed step in the `### Parallelization Overview` table with `[DONE]` next to its step name
  - Mark the phase heading `[REVIEWED]` (e.g. `#### Phase 1: Foundation [REVIEWED]`), or `[REVIEWED-SKIPPED]` when `SKIP_REVIEWS` is true
- Update the todos to `completed`
- Record `combined_score` in tracking

The steps' own `#### Subtasks` and `#### Success Criteria` checkboxes are marked by the implementation agents inside their sub-task files — not by you.

### Human-in-the-Loop Checkpoint (if applicable)

**Only after the implementation phase PASSES**, if the phase identifier is in `HUMAN_IN_THE_LOOP_PHASES` (or `HUMAN_IN_THE_LOOP_PHASES == "*"`), display the checkpoint from [Human-in-the-Loop Behavior](#human-in-the-loop-behavior).

- If user provides feedback: store for the next phase or re-dispatch the affected steps with the feedback
- If user says "n": pause workflow, report current progress
- If user says "Y" or continues: proceed to the next implementation phase

---

## ⚠️ CHECKPOINT: Before Proceeding to Definition-of-Done Verification

Before moving to DoD verification, verify you followed the rules:

- [ ] Did you dispatch ONE implementation agent per step, with the task file path AND its sub-task file path?
- [ ] Did you dispatch every step at the model its Parallelization Overview row names (unless `MODEL_OVERRIDE`)?
- [ ] Did you launch exactly ONE `sdd:code-reviewer` at the END of every implementation phase (unless `SKIP_REVIEWS`), at that phase's `Reviewer model`?
- [ ] Did you avoid reviewing any individual step?
- [ ] Did you apply `THRESHOLD` yourself against `combined_score`, and pass no threshold to the reviewer?
- [ ] Did you reason about blast radius in writing before choosing every fix and re-review model?
- [ ] Did you mark phases `[REVIEWED]` ONLY after the orchestrator-level PASS rule was satisfied?
- [ ] Did you avoid reading ANY artifact files yourself?

**If you read files other than the task file (and sub-task Expected Outputs in `--refine`), you are doing it wrong. STOP and restart.**

---

## Workflow Phase 3: Definition of Done Verification

After all implementation phases are complete, verify the task meets all Definition of Done criteria.

### Step 3.1: Launch Definition of Done Verification

**Use Task tool with:**

- **Agent Type**: `sdd:developer`
- **Model**: `MODEL_OVERRIDE` if set — otherwise `opus`
- **Description**: "Verify Definition of Done"
- **Prompt**:

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

Verify all Definition of Done items in the task file.

Task File: $TASK_PATH

Your task:
1. Read the task file and locate the `## Acceptance Criteria` section, then its `**Definition of Done:**` sub-block
2. Go through each checkbox item one by one
3. For each item, verify if it passes by:
   - Running appropriate tests (unit tests, E2E tests)
   - Checking build/compilation status
   - Verifying file existence and correctness
   - Checking code patterns and linting
4. You MUST mark each item in the task file that passed verification with `[X]`
5. Return a structured report:
- List ALL Definition of Done items
- Status for each:
   - ✅ PASS - if the item is complete and verified
   - ❌ FAIL - if the item fails verification, with specific reason why
   - ⚠️ BLOCKED - if the item cannot be verified due to a blocker
- Evidence for each status
- Specific issues for any failures
- Overall pass rate

This is the TASK-LEVEL check, run once, after every implementation phase is done. Unlike a phase review, nothing here is "not yet due" — every Definition of Done item must hold now.

Be thorough - check everything the task requires.
```

### Step 3.2: Review Verification Results

- Receive the Definition of Done verification report
- Note which DoD items PASS and which FAIL
- If the verification agent reports that all DoD items PASS, you MUST confirm at the end of the task file that all DoD items are marked with `[X]`

### Step 3.3: Fix Failing DoD Items (If Any)

If any Definition of Done items FAIL:

**1. Launch an implementation agent for each failing item** — **Model**: `MODEL_OVERRIDE` if set — otherwise `opus`:

```
Fix Definition of Done item: [Item Description]

Task File: $TASK_PATH

Current Status:
[paste failure details from verification report]

Your task:
1. Fix the specific issue identified
2. Verify the fix resolves the problem
3. Ensure no regressions (all tests still pass)

Return:
- What was fixed
- Confirmation the item now passes
- Any related changes made
```

**2. Re-verify After Fixes:**

Launch the verification agent again (Step 3.1) to confirm all items now PASS.

**3. Iterate if Needed:**

Repeat fix → verify cycle until all Definition of Done items PASS.

---

## Workflow Phase 4: Move Task to Done

Once ALL Definition of Done items PASS, move the task to the done folder.

### Step 4.1: Verify Completion

Confirm all Definition of Done items are marked complete in the task file.

### Step 4.2: Move Task

```bash
# Extract just the filename from $TASK_PATH
TASK_FILENAME=$(basename $TASK_PATH)

# Move from in-progress to done
git mv .specs/tasks/in-progress/$TASK_FILENAME .specs/tasks/done/
# Fallback if git not available: mv .specs/tasks/in-progress/$TASK_FILENAME .specs/tasks/done/
```

**Do NOT move `.specs/sub-tasks/<task-name>/`.** It stays where it is; the task file's recorded paths must keep resolving.

---

## Workflow Phase 5: Aggregation and Reporting

### Final Report

After all implementation phases complete and DoD verification passes:

```markdown
## Implementation Summary

### Task Status
- Task Status: `done` ✅
- All Definition of Done items: X/X PASS (100%)

### Configuration Used

| Setting | Value |
|---------|-------|
| **Model Override** | {MODEL_OVERRIDE or "None (models from task file)"} |
| **Threshold** | {THRESHOLD}/5.0 |
| **Max Iterations** | {MAX_ITERATIONS or "3"} |
| **Human Checkpoints** | {HUMAN_IN_THE_LOOP_PHASES or "None"} |
| **Skip Reviews** | {SKIP_REVIEWS} |
| **Continue Mode** | {CONTINUE_MODE} |
| **Refine Mode** | {REFINE_MODE} |
| **Strict Mode** | {STRICT_MODE} |

### Steps Completed

| Step | Phase | Model Used | Status |
|------|-------|------------|--------|
| `01-foundation` | Phase 1 | haiku | ✅ |
| `02a-service` | Phase 1 | sonnet | ✅ |
| `03-integration` | Phase 2 | sonnet | ✅ (re-dispatched at opus in iteration 1) |

### Phase Reviews

| Phase | Steps | Reviewer Model | Combined Score | Iterations | Status |
|-------|-------|----------------|----------------|------------|--------|
| Phase 1 | 2 | sonnet | 4.3/5 | 1 | ✅ |
| Phase 2 | 1 | opus | 3.6/5 | 2 | ☑️ |

**Legend:**
- ✅ PASS - `combined_score >= THRESHOLD`
- ☑️ ACCEPTED - Score in discretion band `3.0 <= combined_score < THRESHOLD` accepted per the [Iteration Discretion Rule](#iteration-discretion-rule) (outstanding nitpicks listed under Recommendations)
- ⚠️ MAX_ITER - Did not pass but MAX_ITERATIONS reached, proceeded anyway
- ⏭️ SKIPPED - Review skipped (`--skip-reviews`, continue or refine mode); the phase heading carries `[REVIEWED-SKIPPED]`, not `[REVIEWED]`

### Fix Decisions (blast-radius reasoning)

| Phase | Iteration | Findings scope | Fix model chosen | Re-review model | Reasoning |
|-------|-----------|----------------|------------------|-----------------|-----------|
| Phase 2 | 1 | 1 of 1 step, structural | opus (was sonnet) | opus (was opus) | Shared abstraction wrong; sonnet had already failed on it |

### Review Summary

- Total implementation phases: X
- Phases reviewed: Y
- Passed on first review: Z
- Accepted below target per Iteration Discretion Rule: U (outstanding nitpicks listed under Recommendations)
- Required fix iterations: W
- Total iterations across all phases: V
- Final pass rate: 100%

### Definition of Done Verification

| Item | Status | Evidence |
|------|--------|----------|
| [DoD Item 1] | ✅ PASS | [Brief evidence] |
| [DoD Item 2] | ✅ PASS | [Brief evidence] |
| ... | ... | ... |

**Issues Fixed During Verification:**
1. [Issue]: [How it was fixed]
2. [Issue]: [How it was fixed]

### Human Review Summary (if --human-in-the-loop used)

| Phase | Checkpoint | User Action | Feedback Incorporated |
|-------|------------|-------------|----------------------|
| Phase 1 | After PASS | Continued | - |
| Phase 2 | After iteration 1 | Feedback | "Improve error messages" |

### Task File Updated

- Task moved from `in-progress/` to `done/` folder
- All step rows marked `[DONE]` in the Parallelization Overview
- All phase headings marked `[REVIEWED]` in the Phase Overview — or `[REVIEWED-SKIPPED]` for phases whose review `--skip-reviews` suppressed
- All Definition of Done items marked `[X]`
- Sub-task files' subtasks marked `[X]` by their implementation agents

### Recommendations

1. [Any follow-up actions]
2. [Suggested improvements]
```

---

## Execution Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                IMPLEMENT TASK WITH VERIFICATION               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Workflow Phase 0: Select Task                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Use provided name or auto-select from todo/ (if 1 task) │  │
│  │ → Move task from todo/ to in-progress/                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Workflow Phase 1: Load Task                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Read $TASK_PATH → Parse Parallelization Overview        │  │
│  │ (steps, models, agents, sub-task paths) + Phase         │  │
│  │ Overview (phases, reviewer models) → TodoWrite          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Workflow Phase 2: Execute Implementation Phases              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  For each implementation phase:                          │  │
│  │                                                          │  │
│  │  ┌──────────────┐                                        │  │
│  │  │ step agent   │─┐                                      │  │
│  │  ├──────────────┤ │ (parallel where the plan says so)    │  │
│  │  │ step agent   │─┤                                      │  │
│  │  ├──────────────┤ │                                      │  │
│  │  │ step agent   │─┘                                      │  │
│  │  └──────────────┘ │                                      │  │
│  │                   ▼                                      │  │
│  │        ┌─────────────────────┐    ┌───────────┐          │  │
│  │        │ ONE code-reviewer   │───▶│ PASS?     │          │  │
│  │        │ for the whole phase │    │           │          │  │
│  │        └─────────────────────┘    └───────────┘          │  │
│  │                                     │      │             │  │
│  │                                   PASS   FAIL            │  │
│  │                                     │      │             │  │
│  │                                     ▼      ▼             │  │
│  │                            ┌──────────┐  Blast-radius    │  │
│  │                            │ Mark     │  reasoning →     │  │
│  │                            │[REVIEWED]│  fix model +     │  │
│  │                            └──────────┘  scope + re-     │  │
│  │                                          review model ↺  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Workflow Phase 3: Definition of Done Verification            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  ┌──────────────┐    ┌───────────────┐    ┌───────────┐ │  │
│  │  │ DoD Verifier │───▶│ All DoD       │───▶│ All PASS? │ │  │
│  │  │ Agent        │    │ items checked │    │           │ │  │
│  │  └──────────────┘    └───────────────┘    └───────────┘ │  │
│  │                                                │   │    │  │
│  │                                               Yes  No   │  │
│  │                                                │   │    │  │
│  │                                                ▼   ▼    │  │
│  │                                                Fix &    │  │
│  │                                                Retry    │  │
│  │                                                ↺        │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Workflow Phase 4: Move Task to Done                          │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ mv in-progress/$TASK → done/$TASK                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Workflow Phase 5: Aggregate & Report                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Collect all phase review results                        │  │
│  │ → Calculate aggregate metrics                           │  │
│  │ → Generate final report                                 │  │
│  │ → Present to user                                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Basic Usage

```bash
# Implement a specific task
/implement add-validation.feature.md

# Auto-select task from todo/ or in-progress/ (if only 1 task)
/implement

# Continue from the last completed step
/implement add-validation.feature.md --continue

# Refine after user fixes project files (detects changes, re-verifies affected phases)
/implement add-validation.feature.md --refine

# Human review after every implementation phase
/implement add-validation.feature.md --human-in-the-loop

# Human review after specific phases only
/implement add-validation.feature.md --human-in-the-loop "Phase 1,Phase 3"

# Higher quality threshold (stricter)
/implement add-validation.feature.md --target-quality 4.5

# Lower quality threshold (faster convergence)
/implement add-validation.feature.md --target-quality 3.5

# Unlimited iterations (default is 3)
/implement add-validation.feature.md --max-iterations unlimited

# Skip all phase reviews (fast but no quality gates)
/implement add-validation.feature.md --skip-reviews

# Strict mode: never accept a phase below target - iterate until threshold or MAX_ITERATIONS
/implement add-validation.feature.md --strict

# Force ALL sub-agents (implementers + code-reviewer) onto one model, overriding the task file
/implement add-validation.feature.md --model sonnet

# Combined: continue with human review
/implement add-validation.feature.md --continue --human-in-the-loop
```

### Example 1: Implementing a Feature

```
User: /implement add-validation.feature.md

Workflow Phase 0: Task Selection...
Found task in: .specs/tasks/todo/add-validation.feature.md
Moving to in-progress: .specs/tasks/in-progress/add-validation.feature.md

Workflow Phase 1: Loading task...
Task: "Add form validation service"
Parallelization Overview: 4 steps
Phase Overview: 2 implementation phases
- Phase 1: 01-validation-types, 02-validation-service — reviewer sonnet
- Phase 2: 03a-email-validator, 03b-phone-validator — reviewer opus
Threshold: 4.0/5.0

Workflow Phase 2: Executing...

Phase 1 / step 01-validation-types [haiku]
  Prompt: task file + .specs/sub-tasks/add-validation/01-validation-types.md
  Result: ✅ src/validation/types.ts

Phase 1 / step 02-validation-service [sonnet]
  Prompt: task file + .specs/sub-tasks/add-validation/02-validation-service.md
  Result: ✅ src/validation/validation.service.ts + spec

  Launching 1 sdd:code-reviewer for Phase 1 (model: sonnet)...
  Inputs: task file path, "Phase 1", 3 artifact paths, CLAUDE_PLUGIN_ROOT
  combined_score 4.3/5.0 ≥ threshold 4.0 → PASS ✅
  Marking Phase 1 [REVIEWED]

Phase 2 / steps 03a-email-validator, 03b-phone-validator [haiku, haiku] — dispatched in parallel
  Result: ✅ 2 validators + specs

  Launching 1 sdd:code-reviewer for Phase 2 (model: opus)...
  combined_score 4.5/5.0 ≥ threshold 4.0 → PASS ✅

Workflow Phase 3: Definition of Done Verification...
  Result: 4/4 items PASS ✅

Workflow Phase 4: Moving task to done...

Workflow Phase 5: Final Report
Implementation complete.
- 4/4 steps completed, 2/2 phases reviewed
- All passed first review
- Definition of Done: 4/4 PASS
- Task location: .specs/tasks/done/add-validation.feature.md ✅
```

### Example 2: Handling DoD Item Failure

```
[All implementation phases complete and reviewed...]

Workflow Phase 3: Definition of Done Verification...
Launching DoD verification agent...
  Result: 3/4 items PASS, 1 FAIL ❌

Failing item:
- "Code follows ESLint rules": 356 errors found

Should I attempt to fix this issue? [Y/n]

User: Y

Launching sdd:developer agent...
  Result: Fixed 356 errors, 0 warnings ✅

Re-launching DoD verification agent...
  Result: 4/4 items PASS ✅

Workflow Phase 4: Moving task to done...
All DoD checkboxes marked complete ✅
```

Examples 3 and 4 below are the two halves of the SAME anchor case from [Failure Handling](#failure-handling-reason-about-blast-radius-your-most-critical-judgement), shown end-to-end as session logs. They are NOT a catalogue of situations — every other failure is reasoned out from the principle, never looked up.

### Example 3: Phase Review Failure — Case A of the anchor example, as a session log

```
Phase 2 complete: steps 03a, 03b, 03c — all built by haiku.
Launching 1 sdd:code-reviewer for Phase 2 (model: sonnet)...

combined_score 2.1/5.0 — below threshold 4.0 and below the 3.0 floor → FAIL (no discretion)

Reviewer blast_radius:
  affected_steps: [03a-parser, 03b-evaluator, 03c-formatter]
  unaffected_steps: []
  requires_phase_rework: true

Blast-radius reasoning:
- Scope: all 3 steps carry High findings
- Depth: structural — the shared Rule interface the three steps agreed on is wrong
- Coupling: total — fixing one forces rewriting the other two
- Severity: 4 High findings, 2 of them break CK-3 and CK-4, which Phase 2 owns
- Ceiling: haiku produced three mutually inconsistent takes on the same interface
→ Fix model: sonnet for all three steps (was haiku)
→ Fix scope: whole phase
→ Re-review model: opus (was sonnet) — the sonnet review is what let this shape through

Iteration 1/3: re-dispatching 03a, 03b, 03c at sonnet with their per-step issues...
Re-launching sdd:code-reviewer for Phase 2 at opus...
combined_score 4.4/5.0 ≥ threshold 4.0 → PASS ✅
Marking Phase 2 [REVIEWED]
```

### Example 4: Phase Review Failure — Case B of the anchor example, as a session log

```
Phase 1 complete: steps 01a, 01b, 01c — all built by haiku.
Launching 1 sdd:code-reviewer for Phase 1 (model: sonnet)...

combined_score 3.4/5.0 — below threshold 4.0, inside discretion band → but a High finding removes discretion → FAIL

Reviewer blast_radius:
  affected_steps: [01b-token-service]
  unaffected_steps: [01a-user-model, 01c-config]
  requires_phase_rework: false

Blast-radius reasoning:
- Scope: 1 of 3 steps
- Depth: local — a missed expiry edge case, not a design failure
- Coupling: none — 01a and 01c do not touch the token path
- Severity: 1 High, breaks CK-2 which Phase 1 owns
- Ceiling: not reached — the step's design is right, one branch is missing
→ Fix model: haiku (unchanged)
→ Fix scope: 01b-token-service ONLY — 01a and 01c are not re-dispatched
→ Re-review model: sonnet (the phase's Reviewer model, unchanged)

Iteration 1/3: re-dispatching 01b-token-service at haiku...
Re-launching sdd:code-reviewer for Phase 1 at sonnet...
combined_score 4.2/5.0 ≥ threshold 4.0 → PASS ✅
```

### Example 5: Continue from Interruption

```
User: /implement add-validation.feature.md --continue

Workflow Phase 0: Parsing flags...
Configuration:
- Continue Mode: true
- Threshold: 4.0/5.0 (default)

Scanning task file...
Parallelization Overview: 01-... [DONE], 02-... [DONE], 03-..., 04-...
Phase Overview: Phase 1 [REVIEWED], Phase 2 (not reviewed)
RESUME_PHASE = Phase 2
RESUME_STEPS = 03-..., 04-...

Resuming: dispatching 03-... and 04-... (parallel per the plan)...
[both complete]

Launching 1 sdd:code-reviewer for Phase 2 (model: opus)...
combined_score 4.3/5.0 ≥ threshold 4.0 → PASS ✅
```

### Example 6: Refine After User Fixes

```
# User manually fixed src/validation/validation.service.ts
# (Expected Output of step 02-validation-service, in Phase 1)

User: /implement add-validation.feature.md --refine

Workflow Phase 0: Parsing flags...
Configuration:
- Refine Mode: true

Detecting changed project files...
- src/validation/validation.service.ts (modified)

Mapping files to steps (reading sub-task Expected Output sections)...
- src/validation/validation.service.ts → 02-validation-service → Phase 1

Earliest affected phase: Phase 1
Preserving: nothing earlier
Re-verifying from: Phase 1 onwards

Launching 1 sdd:code-reviewer for Phase 1...
combined_score 4.3/5.0 ≥ threshold 4.0 → PASS ✅

Launching 1 sdd:code-reviewer for Phase 2...
combined_score 2.8/5.0 — High finding "typescript error in src/validation/index.ts" → FAIL
Blast radius: 1 step (04-barrel-exports), local, no coupling, ceiling not reached
→ re-dispatch 04-barrel-exports at its original model with the user's diff as context

Re-launching sdd:code-reviewer for Phase 2...
combined_score 4.5/5.0 → PASS ✅

All phases verified with user's changes incorporated ✅
```

### Example 7: Human-in-the-Loop Review

```
User: /implement add-validation.feature.md --human-in-the-loop

Configuration:
- Human Checkpoints: All phases

Phase 1 / steps 01-..., 02-... dispatched...
Result: ✅ complete

Launching 1 sdd:code-reviewer for Phase 1 (model: sonnet)...
combined_score 4.4/5.0 ≥ threshold 4.0 → PASS ✅

---
## 🔍 Human Review Checkpoint - Phase 1

**Phase:** Phase 1: Validation Core
**Steps:** `01-validation-types`, `02-validation-service`
**Reviewer model:** sonnet
**Combined Score:** 4.4/5.0 (threshold: 4.0)
**Status:** ✅ PASS

**Artifacts Created/Modified:**
- src/validation/types.ts
- src/validation/validation.service.ts
- src/validation/tests/validation.service.spec.ts

**Reviewer Feedback (top issues):**
- [Low] `02-validation-service` — Error messages could be more descriptive

**Action Required:** Review the above artifacts and provide feedback or continue.

> Continue? [Y/n/feedback]: The error messages could be more descriptive
---

Incorporating feedback: re-dispatching 02-validation-service with the feedback...
[iteration continues]
```

### Example 8: Strict Quality Threshold

```
User: /implement add-validation.feature.md --strict

Configuration:
- Strict Mode: true (Iteration Discretion Rule DISABLED)
- Threshold: 4.0/5.0 (default)
- Max Iterations: 3 (default)

Phase 1 / steps 01-..., 02-... dispatched...

Launching 1 sdd:code-reviewer for Phase 1 (model: sonnet)...
combined_score 3.6/5.0 — outstanding issues are 2 Low nitpicks only
Without --strict this would sit in the discretion band (3.0 <= 3.6 < 4.0) and be ☑️ ACCEPTED.
--strict disables that discretion → FAIL, iterate.

Blast radius: 1 step (02-validation-service), local → re-dispatch it with the reviewer feedback
Re-launching sdd:code-reviewer for Phase 1 (iteration 2)...
combined_score 4.2/5.0 ≥ threshold 4.0 → PASS ✅
Marking Phase 1 [REVIEWED]
```

---

## Error Handling

### Implementation Failure

If an implementation agent reports failure:

1. Present the failure details to user
2. Ask clarification questions that could help resolve
3. Re-dispatch the agent for that step with the clarifications
4. A step failure delays the phase's review; it never skips it. Once every step of the phase reports completion, the phase review runs exactly as normal (unless `SKIP_REVIEWS`).

### Reviewer Returns an Invalid Report

If the `sdd:code-reviewer` returns a report that trips any rule in [Execution & Evaluation Rules](#execution--evaluation-rules) — a 5.0 `combined_score`, a missing `combined_score`, a PASS/FAIL verdict, or findings against acceptance criteria the phase does not own — reject it and re-run the agent with the same 4 inputs. Never repair its report yourself.

### Refine Mode: No Changes Detected

If `--refine` mode finds no git changes in the project:

1. Report: "No project file changes detected since last commit."
2. Suggest: "Make edits to project files first, then run --refine again."
3. Alternatively: "Run without --refine to re-implement all steps."

### Refine Mode: Changes Don't Map to Steps

If `--refine` mode finds changed files but none map to a step's Expected Output:

1. Report: "Changed files don't match any step's Expected Output."
2. List the changed files detected
3. Suggest: "Verify manually or run without --refine to re-verify all phases."

### Missing Sub-Task File

If the `Sub-Task File` path in the Parallelization Overview does not exist:

1. Try `.specs/sub-tasks/<task-file-basename-without-extension>/<step-name>.md` — the folder never moves, so a stale path is usually recoverable
2. If still missing, report it to the user and STOP. Do NOT invent the step's content, and do NOT dispatch the agent with only the task file.

---

## Checklist

Before completing implementation:

### Configuration Handling

- [ ] Parsed all flags from `$ARGUMENTS` correctly
- [ ] Applied the `MODEL_OVERRIDE` precedence rule for `--model` (see [Configuration Rules](#configuration-rules))
- [ ] Used the single `THRESHOLD` (default 4.0) for every implementation phase review
- [ ] Read NO threshold from the task file
- [ ] Iterated until the orchestrator-level PASS rule was satisfied (or `MAX_ITERATIONS` reached, default 3)
- [ ] Applied the [Iteration Discretion Rule](#iteration-discretion-rule) only inside the discretion band `3.0 <= combined_score < THRESHOLD`, never accepted below `3.0`, treated `< 3.0` as unconditional FAIL, and spent at most ONE nitpick-driven iteration
- [ ] Passed NO threshold, floor or band value to the code-reviewer — the agent stayed threshold-blind
- [ ] If `STRICT_MODE` is true: Ignored the Iteration Discretion Rule and iterated until `THRESHOLD` or `MAX_ITERATIONS`
- [ ] Triggered human-in-the-loop checkpoints ONLY for implementation phases in `HUMAN_IN_THE_LOOP_PHASES`
- [ ] If `SKIP_REVIEWS` is true: Skipped ALL code-reviewer dispatches
- [ ] If `CONTINUE_MODE` is true: Resolved `RESUME_PHASE` + `RESUME_STEPS` and resumed correctly
- [ ] If `REFINE_MODE` is true: Detected changed project files, mapped to steps, re-verified from the earliest affected implementation phase

### Context Protection (CRITICAL)

- [ ] Read ONLY the task file (`$TASK_PATH` in `.specs/tasks/in-progress/`) — plus sub-task `#### Expected Output` sections in `--refine` mode, and nothing else
- [ ] Did NOT read implementation outputs, reference files, or artifacts
- [ ] Used sub-agent reports for status - did NOT read files to "check"

### Delegation

- [ ] EVERY step implemented by its own sub-agent via Task tool, with the task file path AND its sub-task file path
- [ ] Every step dispatched at the model and agent type its Parallelization Overview row names (unless `MODEL_OVERRIDE`)
- [ ] EXACTLY ONE `sdd:code-reviewer` dispatched per implementation phase, at that phase's `Reviewer model` (unless `SKIP_REVIEWS`)
- [ ] Did NOT review any individual step
- [ ] Did NOT perform any verification yourself

### Progress Tracking

- [ ] Each step row marked `[DONE]` in the Parallelization Overview after its agent reported completion
- [ ] Each phase heading marked `[REVIEWED]` ONLY after the orchestrator-level PASS (or `[REVIEWED-SKIPPED]` if `SKIP_REVIEWS`)
- [ ] Todo list updated after each step and each phase review

### Execution Quality

- [ ] All steps executed in dependency order
- [ ] `Parallel with:` groups launched simultaneously in one message (not sequentially)
- [ ] No step of a later phase started before the previous phase was reviewed
- [ ] Blast-radius reasoning written out BEFORE choosing each fix model, fix scope and re-review model
- [ ] Only affected steps re-dispatched — sound steps left untouched
- [ ] Failed reviews iterated using the reviewer's `issues` (attributed per step) as feedback until orchestrator-level PASS
- [ ] Final report generated with phase review results and fix decisions

### Human-in-the-Loop (if enabled)

- [ ] Displayed a checkpoint after each implementation phase in `HUMAN_IN_THE_LOOP_PHASES`
- [ ] Incorporated user feedback into subsequent iterations/phases
- [ ] Paused workflow when user requested

### Final Verification and Completion

- [ ] Definition of Done verification agent launched, reading `## Acceptance Criteria` → `**Definition of Done:**`
- [ ] All DoD items verified (PASS/FAIL/BLOCKED status)
- [ ] Failing DoD items fixed via implementation agents
- [ ] Re-verification performed after fixes
- [ ] Task moved from `in-progress/` to `done/` folder (sub-task folder left in place)
- [ ] All DoD checkboxes marked `[X]` in task file
- [ ] Final verification report presented to user

---

## Appendix A: What the Task File and Sub-Task Files Provide

This appendix documents the artifacts this skill consumes. It is a reading guide, not an instruction to read more files than Workflow Phase 1 allows.

### Task File Structure

A planned task file contains exactly these sections:

| Section | Written by | What this skill uses it for |
|---------|-----------|------------------------------|
| `# Description` | `sdd:business-analyst` | Nothing directly — the sub-agents read it |
| `## Acceptance Criteria` | `sdd:business-analyst` | Only its `**Definition of Done:**` sub-block, in Workflow Phase 3 |
| `## Architecture Overview` | `sdd:software-architect` | Nothing directly — the sub-agents read it |
| `## Implementation Process` | `sdd:tech-lead` | Everything: dispatch, models, phases, review gates |

`## Acceptance Criteria` has exactly six sub-blocks, in order: `**Checklist:**`, `**Regular Checks:**`, `**Rubric:**`, `**Rubric Score Definitions:**`, `**Test Strategy:**`, `**Definition of Done:**`. The first five are the **reviewer's** input, narrowed per phase — you never parse or forward them.

**A task file carries no scoring configuration at all** — no threshold, no judge count, no per-step review metadata. Scoring is orchestrator config only. If a task file contains any section not listed in the table above, it is a stale artifact from an older plan; ignore it and note it in the final report.

### `## Implementation Process`

```markdown
## Implementation Process

[sub-agent execution directive: launch one agent per step; verify at PHASE level]

### Parallelization Overview

[ASCII dependency diagram]

| Step | Phase | Model | Agent | Depends on | Parallel with | Sub-Task File |
|------|-------|-------|-------|------------|---------------|---------------|
| `01-foundation` | Phase 1 | haiku | developer | None | None | `.specs/sub-tasks/<task-name>/01-foundation.md` |
| `02a-service` | Phase 1 | sonnet | developer | `01-foundation` | `02b-docs` | `.specs/sub-tasks/<task-name>/02a-service.md` |

### Phase Overview

#### Phase 1

Steps: `01-foundation`, `02a-service`
Reviewer model: `sonnet`
Acceptance Criteria that should be fulfiled:
Checklist items:
- `CK-1` — ...
- `CK-2` — ...

Rubrics:
- `Contract Correctness`
```

- The **phase identifier** is `Phase N` (a title may follow: `#### Phase 1: Foundation`). This exact identifier is what you pass to the reviewer.
- `Reviewer model:` is one of `haiku`, `sonnet`, `opus`. It is the model of that phase's single review dispatch.
- The `Checklist items:` and `Rubrics:` lists scope the reviewer's scoring. **They are the reviewer's input, not yours** — it reads them from the task file itself. Never paste them into a prompt.

### Sub-Task Files

One per step, at `.specs/sub-tasks/<task-name>/<NN>-<step-slug>.md`, where `<task-name>` is the task filename without its extension. The folder never moves.

```markdown
# Step NN: [Title]

**Task File:** `.specs/tasks/todo/<task-name>.md`
**Phase:** Phase N
**Model:** haiku | sonnet | opus
**Agent:** [agent type]
**Depends on:** [step names or None]
**Parallel with:** [step names or None]
**Note:** [or None]

**Goal:** ...

[step description]

#### Expected Output
#### Success Criteria
#### Subtasks
#### Blockers & Risks
```

The **step name** is the file's basename without `.md`. It is the identity used in `Steps:`, `Depends on:`, `Parallel with:` and in the reviewer's per-issue attribution.

### Scoring Scale

The `sdd:code-reviewer` scores every criterion on a 1-5 integer scale defined by its own `## Scoring Scale` section. That section is the sole definition and is **deliberately not reproduced here** — the reviewer owns scoring; you do not score anything, you only compare `combined_score` against `THRESHOLD`. Never restate the scale, or your own version of it, in any prompt or report.

**The one consequence for you:** when applying the [Iteration Discretion Rule](#iteration-discretion-rule), read a score as a placement, never as an intuitive "out of 5" feel or a word like *adequate* or *excellent*.

### Using These Artifacts During Execution

**During Workflow Phase 2:**

1. Dispatch each step's agent with the task file path AND its sub-task file path, at its `Model`
2. Wait for every step of the implementation phase to report completion
3. Launch ONE `sdd:code-reviewer` at that phase's `Reviewer model` — **Model**: `MODEL_OVERRIDE` if set — otherwise the phase's `Reviewer model` — otherwise `opus`
4. Pass exactly the 4 inputs (task file path, phase identifier, artifact paths, `CLAUDE_PLUGIN_ROOT`) — **NEVER a threshold, NEVER the sub-task paths**
5. Receive the reviewer's combined report
6. Apply `THRESHOLD` against `combined_score` at this layer
7. If FAIL, reason about blast radius, dispatch fixes for the affected steps only, and re-review the phase
