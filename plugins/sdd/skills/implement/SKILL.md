---
name: sdd:implement
description: Implement a task with per-step automated code-reviewer verification (combines spec compliance, code quality, and Muda waste analysis)
argument-hint: Task file [options] (e.g., "add-validation.feature.md --continue --human-in-the-loop")
---

# Implement Task with Verification

Your job is to implement solution in best quality using task specification and sub-agents. You MUST NOT stop until it is critically necessary or you are done! Avoid asking questions until it is critically necessary! Launch the developer agent, then the `sdd:code-reviewer`, iterate till issues are fixed, then move to next step!

Execute task implementation steps with automated quality verification using `sdd:code-reviewer` agents for non-trivial artifacts.

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
| `task-file` | Path or filename | Auto-detect | Task file name or path (e.g., `add-validation.feature.md`) |
| `--continue` | `--continue` | None | Continue implementation from last completed step. Launches `sdd:code-reviewer` first to verify state, then iterates with the developer agent. |
| `--refine` | `--refine` | `false` | Incremental refinement mode - detect changes against git and re-implement only affected steps (from modified step onwards). |
| `--human-in-the-loop` | `--human-in-the-loop [step1,step2,...]` | None | Steps after which to pause for human verification. If no steps specified, pauses after every step. |
| `--target-quality` | `--target-quality X.X` or `--target-quality X.X,Y.Y` | `4.0` (standard) / `4.5` (critical) | Target threshold value (out of 5.0). Single value sets both. Two comma-separated values set standard,critical. |
| `--max-iterations` | `--max-iterations N` | `3` | Maximum fix→verify cycles per step. Default is 3 iterations. Set to `unlimited` for no limit. |
| `--skip-reviews` | `--skip-reviews` | `false` | Skip all per-step code-reviewer checks - steps proceed without quality gates. |
| `--lenient-threshold` | `--lenient-threshold X.X` | `3.5` | Lenient threshold (out of 5.0) used for steps with verification level explicitly marked lenient by qa-engineer. |

### Configuration Resolution

Parse `$ARGUMENTS` and resolve configuration as follows:

```
# Extract task file (first positional argument, optional - auto-detect if not provided)
TASK_FILE = first argument that is a file path or filename

# Parse --target-quality (supports single value or two comma-separated values)
if --target-quality has single value X.X:
    THRESHOLD_FOR_STANDARD_COMPONENTS = X.X
    THRESHOLD_FOR_CRITICAL_COMPONENTS = X.X
elif --target-quality has two values X.X,Y.Y:
    THRESHOLD_FOR_STANDARD_COMPONENTS = X.X
    THRESHOLD_FOR_CRITICAL_COMPONENTS = Y.Y
else:
    THRESHOLD_FOR_STANDARD_COMPONENTS = 4.0  # default
    THRESHOLD_FOR_CRITICAL_COMPONENTS = 4.5  # default

# Initialize other defaults
MAX_ITERATIONS = --max-iterations || 3  # default is 3 iterations
HUMAN_IN_THE_LOOP_STEPS = --human-in-the-loop || [] (empty = none, "*" = all)
SKIP_REVIEWS = --skip-reviews || false
LENIENT_THRESHOLD = --lenient-threshold || 3.5
REFINE_MODE = --refine || false
CONTINUE_MODE = --continue || false

# Special handling for --human-in-the-loop without step list
if --human-in-the-loop present without step numbers:
    HUMAN_IN_THE_LOOP_STEPS = "*" (all steps)
```

### Context Resolution for `--continue`

When `--continue` is used:

1. **Step Resolution:**
   - Parse the task file for `[DONE]` markers on step titles
   - Identify the last incompleted step
   - Launch the `sdd:code-reviewer` agent to verify the last INCOMPLETE step's artifacts (using the step's `#### Verification` specification embedded in the task file)
   - If `combined_score >= threshold` (or `>= 3.0` with only Low-priority issues): Mark step as done and resume from the next step
   - Otherwise: Re-implement the step using the reviewer's issues as feedback and iterate until PASS

2. **State Recovery:**
   - Check task file location (`in-progress/`, `todo/`, `done/`)
   - If in `todo/`, move to `in-progress/` before continuing
   - Pre-populate captured values from existing artifacts

### Refine Mode Behavior (`--refine`)

When `--refine` is used, it detects changes to **project files** (not the task file) and maps them to implementation steps to determine what needs re-verification.

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

2. **Map Changes to Implementation Steps:**
   - Read the task file to get the list of implementation steps
   - For each changed file, determine which step created/modified it:
     - Check step's "Expected Output" section for file paths
     - Check step's subtasks for file references
     - Check step's artifacts in `#### Verification` section
   - Build a mapping: `{changed_file → step_number}`

3. **Determine Affected Steps:**
   - Find all steps that have associated changed files
   - The **earliest affected step** is the starting point
   - All steps from that point onwards need re-verification
   - Earlier steps (unaffected) are preserved as-is

4. **Refine Execution:**
   - For each affected step (in order):
     - Launch the **`sdd:code-reviewer` agent** to verify the step's artifacts (including user's changes), passing the 5 standard inputs
     - If `combined_score >= threshold` (or `>= 3.0` with only Low-priority issues): Mark step done, proceed to next
     - Otherwise: Launch the developer agent with user's changes AND the reviewer's issues as feedback, then re-verify
   - User's manual fixes are preserved - the developer agent should build upon them, not overwrite

5. **Example:**

   ```bash
   # User manually fixed src/validation/validation.service.ts
   # (This file was created in Step 2)
   
   /implement my-task.feature.md --refine
   
   # Detects: src/validation/validation.service.ts modified
   # Maps to: Step 2 (Create ValidationService)
   # Action: Launch sdd:code-reviewer for Step 2
   #   - If PASS: User's fix is good, proceed to Step 3
   #   - If FAIL: Developer agent aligns rest of the code with user changes (using reviewer's issues feedback) without overwriting user's changes
   # Continues: Step 3, Step 4... (re-verify all subsequent steps)
   ```

6. **Multiple Files Changed:**

   ```bash
   # User edited files from Step 2 AND Step 4
   
   /implement my-task.feature.md --refine
   
   # Detects: Files from Step 2 and Step 4 modified
   # Earliest affected: Step 2
   # Re-verifies: Step 2, Step 3, Step 4, Step 5...
   # (Step 3 re-verified even though no direct changes, because it depends on Step 2)
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
   # Staged changes are preserved, not re-verified
   
   # --
   
   # Scenario: User only has staged changes (ready to commit)
   # Staged: src/validation/validation.service.ts
   # Unstaged: none
   
   /implement my-task.feature.md --refine
   
   # Detects: Only staged changes
   # Mode: Compares against last commit
   # validation.service.ts changes are verified
   ```

### Human-in-the-Loop Behavior

Human verification checkpoints occur:

1. **Trigger Conditions:**
   - After developer + `sdd:code-reviewer` orchestrator-level **PASS** for a step in `HUMAN_IN_THE_LOOP_STEPS`
   - After developer + reviewer + developer retry (before the next reviewer retry)
   - If `HUMAN_IN_THE_LOOP_STEPS` is `"*"`, triggers after every step

2. **At Checkpoint:**
   - Display current step results summary
   - Display generated artifacts with paths
   - Display reviewer's `combined_score` and consolidated issues
   - Ask user: "Review step output. Continue? [Y/n/feedback]"
   - If user provides feedback, incorporate into next iteration or step
   - If user says "n", pause workflow

3. **Checkpoint Message Format:**

   ```markdown
   ---
   ## 🔍 Human Review Checkpoint - Step X

   **Step:** {step title}
   **Verification Level:** {None / Single Judge / Panel of 2 Judges / Per-Item Judges}
   **Combined Score:** {combined_score}/5.0 (threshold: {threshold})
   **Status:** ✅ PASS / 🔄 ITERATING (attempt {n})

   **Artifacts Created/Modified:**
   - {artifact_path_1}
   - {artifact_path_2}

   **Reviewer Feedback (top issues):**
   {feedback summary — High/Medium issues from reviewer.issues}

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

CRITICAL: For each sub-agent (implementation and evaluation), you need to provide:

- Task file path
- Step number
- Item number (if applicable)
- Artifact path (if applicable)
- **Value of `${CLAUDE_PLUGIN_ROOT}` so agents can resolve paths like `@${CLAUDE_PLUGIN_ROOT}/scripts/create-scratchpad.sh`**

### What You DO

- Read the task file ONCE (Phase 1 only)
- Launch sub-agents via Task tool
- Receive reports from sub-agents
- Mark stages complete after orchestrator-level PASS rule on reviewer output
- Aggregate results and report to user

### What You NEVER Do

| Prohibited Action | Why | What To Do Instead |
|-------------------|-----|-------------------|
| Read implementation outputs | Context bloat → command loss | Sub-agent reports what it created |
| Read reference files | Sub-agent's job to understand patterns | Include path in sub-agent prompt |
| Read artifacts to "check" them | Context bloat → forget verifications | Launch `sdd:code-reviewer` agent |
| Evaluate code quality yourself | Not your job, causes forgetting | Launch `sdd:code-reviewer` agent |
| Skip verification "because simple" | ALL non-`None` verifications are mandatory | Launch `sdd:code-reviewer` agent anyway |

### Anti-Rationalization Rules

**If you think:** "I should read this file to understand what was created"
**→ STOP.** The sub-agent's report tells you what was created. Use that information.

**If you think:** "I'll quickly verify this looks correct"
**→ STOP.** Launch a `sdd:code-reviewer` agent. That's not your job.

**If you think:** "This is too simple to need verification"
**→ STOP.** If the task specifies verification (Level is not `None`), launch the `sdd:code-reviewer`. No exceptions.

**If you think:** "I need to read the reference file to write a good prompt"
**→ STOP.** Put the reference file PATH in the sub-agent prompt. Sub-agent reads it.

### Why This Matters

Orchestrators who read files themselves = context overflow = command loss = forgotten steps. Every time.

Orchestrators who "quickly verify" = skip `sdd:code-reviewer` agents = quality collapse = failed artifacts.

**Your context window is precious. Protect it. Delegate everything.**

---

## CRITICAL

### Configuration Rules

- Use `THRESHOLD_FOR_STANDARD_COMPONENTS` (default 4.0) for standard steps (Verification Level: `Single Judge`)!
- Use `THRESHOLD_FOR_CRITICAL_COMPONENTS` (default 4.5) for high-stakes steps (Verification Level: `Panel of 2 Judges`)!
- Use `LENIENT_THRESHOLD` (default 3.5) only when the step's verification specification explicitly marks it as lenient.
- The threshold is applied at THIS orchestrator layer against `combined_score` returned by code-reviewer. **NEVER pass any threshold to the code-reviewer agent — it is threshold-blind by design.**
- A step PASSES if `combined_score >= threshold` OR (`combined_score >= 3.0` AND every issue in code-reviewer's report has priority `Low`).
- **Default is 3 iterations** - stop after 3 fix→verify cycles and proceed to next step (with warning)!
- If `MAX_ITERATIONS` is set to `unlimited`: Iterate until quality threshold is met (no limit)
- Trigger human-in-the-loop checkpoints ONLY after steps in `HUMAN_IN_THE_LOOP_STEPS` (or all steps if `"*"`)!
- **If `SKIP_REVIEWS` is true: Skip ALL code-reviewer dispatches - proceed directly to next step after each implementation completes!**
- **If `CONTINUE_MODE` is true: Skip to `RESUME_FROM_STEP` - do not re-implement already completed steps!**
- **If `REFINE_MODE` is true: Detect changed project files, map to steps, re-verify from `REFINE_FROM_STEP` - preserve user's fixes!**

### Execution & Evaluation Rules

- **Use foreground agents only**: Do not use background agents. Launch parallel agents when possible. Background agents constantly run in permissions issues and other errors.

Relaunch the code-reviewer till you get valid results, if following happens:

- Reject Long Reports: If the code-reviewer returns a very long report instead of using the scratchpad as requested, reject the result. This indicates the agent failed to follow the "use scratchpad" instruction.
- Combined Score 5.0 is a Hallucination: If the code-reviewer returns a `combined_score` of 5.0/5.0, treat it as a hallucination or lazy evaluation. Reject it and re-run the agent. Perfect scores are practically impossible in this rigorous framework.
- Reject Missing Scores: If the code-reviewer's report is missing the `combined_score` (or any sub-score: `spec_compliance_score`, `builtin_score`), reject it. This indicates the agent failed to follow the rubric instructions.
- Reject PASS/FAIL Verdicts in Report: If the code-reviewer's output contains a PASS/FAIL verdict or references a threshold, reject it. The orchestrator owns that decision; the agent must remain threshold-blind.

---

## Overview

This command orchestrates multi-step task implementation with:

1. **Sequential execution** respecting step dependencies
2. **Parallel execution** where dependencies allow
3. **Automated verification** using `sdd:code-reviewer` agents per step (combined per-step spec verification + code quality + Muda waste analysis)
4. **Panel of LLMs (PoLL)** for high-stakes artifacts
5. **Aggregated voting** with position bias mitigation
6. **Stage tracking** with confirmation after each orchestrator-level PASS

---

## Complete Workflow Overview

```
Phase 0: Select Task & Move to In-Progress
    │
    ├─── Use provided task file name or auto-select from todo/ (if only 1 task)
    ├─── Move task: todo/ → in-progress/
    │
    ▼
Phase 1: Load Task
    │
    ▼
Phase 2: Execute Steps
    │
    ├─── For each step in dependency order:
    │    │
    │    ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Launch sdd:developer agent                      │
    │    │ (implementation)                                │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Launch sdd:code-reviewer agent(s)               │
    │    │ (per-step spec verification + code quality      │
    │    │  + Muda waste analysis — single combined report)│
    │    │ Count depends on Verification Level:            │
    │    │  None → 0 reviewers (skip)                      │
    │    │  Single Judge → 1 reviewer                      │
    │    │  Panel of 2 Judges → 2 reviewers (median vote)  │
    │    │  Per-Item → 1 reviewer per item                 │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Orchestrator reads combined_score and applies   │
    │    │ threshold:                                      │
    │    │  PASS → Mark step complete in task file         │
    │    │  FAIL → Fix using reviewer's issues feedback    │
    │    │         and re-verify (max MAX_ITERATIONS)      │
    │    └─────────────────────────────────────────────────┘
    │
    ▼
Phase 3: Definition of Done Verification
    │
    ├─── Verify all Definition of Done items
    │    │
    │    ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Launch DoD verification agent                   │
    │    │ (verify all DoD items)                          │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ All DoD PASS? → Proceed to Phase 4              │
    │    │ Any FAIL? → Fix and re-verify (iterate)         │
    │    │ NOTE: Code quality is already enforced per-step │
    │    │ via the code-reviewer in Phase 2 — there is no  │
    │    │ separate end-of-task code quality phase.        │
    │    └─────────────────────────────────────────────────┘
    │
    ▼
Phase 4: Move Task to Done
    │
    ├─── Move task: in-progress/ → done/
    │
    ▼
Phase 5: Final Report
```

---

## Phase 0: Parse User Input and Select Task

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

### Step 0.3: Parse Flags and Initialize Configuration

Parse all flags from `$ARGUMENTS` and initialize configuration.
**Display resolved configuration:**

```markdown
### Configuration

| Setting | Value |
|---------|-------|
| **Task File** | {TASK_PATH} |
| **Standard Components Threshold** | {THRESHOLD_FOR_STANDARD_COMPONENTS}/5.0 |
| **Critical Components Threshold** | {THRESHOLD_FOR_CRITICAL_COMPONENTS}/5.0 |
| **Max Iterations** | {MAX_ITERATIONS or "3"} |
| **Human Checkpoints** | {HUMAN_IN_THE_LOOP_STEPS as comma-separated or "All steps" or "None"} |
| **Skip Reviews** | {SKIP_REVIEWS} |
| **Lenient Threshold** | {LENIENT_THRESHOLD}/5.0 |
| **Continue Mode** | {CONTINUE_MODE} |
| **Refine Mode** | {REFINE_MODE} |
```

### Step 0.4: Handle Continue Mode

**If `CONTINUE_MODE` is true:**

1. **Identify Last Completed Step:**
   - Parse task file for `[DONE]` markers on step titles
   - Find the highest step number marked `[DONE]`
   - Set `LAST_COMPLETED_STEP` to that number (or 0 if none)

2. **Verify Last Completed Step (if any):**
   - If `LAST_COMPLETED_STEP > 0`:
     - Launch the `sdd:code-reviewer` agent to verify the artifacts from that step (passing the 5 inputs documented in Phase 2)
     - If reviewer's `combined_score >= threshold` (or `>= 3.0` with only Low-priority issues): Set `RESUME_FROM_STEP = LAST_COMPLETED_STEP + 1`
     - Otherwise: Set `RESUME_FROM_STEP = LAST_COMPLETED_STEP` (re-implement using reviewer feedback)

3. **Skip to Resume Point:**
   - In Phase 2, skip all steps before `RESUME_FROM_STEP`
   - Continue execution from `RESUME_FROM_STEP`

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

2. **Load Task File and Extract Step→File Mapping:**
   - Read the task file to get implementation steps
   - For each step, extract the files it creates/modifies from:
     - "Expected Output" sections
     - Subtask descriptions mentioning file paths
     - `#### Verification` artifact paths
   - Build mapping: `STEP_FILE_MAP = {step_number → [file_paths]}`

3. **Map Changed Files to Steps:**

   ```
   AFFECTED_STEPS = []
   for each changed_file:
       for step_number, file_list in STEP_FILE_MAP:
           if changed_file matches any path in file_list:
               AFFECTED_STEPS.append(step_number)
   ```

   - If no steps matched: "Changed files don't map to any implementation step. Verify manually."

4. **Determine Refine Scope:**
   - `REFINE_FROM_STEP` = min(AFFECTED_STEPS)  # earliest affected step
   - All steps from `REFINE_FROM_STEP` onwards need re-verification
   - Steps before `REFINE_FROM_STEP` are preserved as-is

5. **Store Changed Files Context:**
   - `CHANGED_FILES` = list of changed file paths
   - `USER_CHANGES_CONTEXT` = git diff output for affected files
   - Pass this context to the code-reviewer and developer agents
   - Agents should build upon user's fixes, not overwrite them

### Step 0.6: Set Up Reports Directory

Before launching any sub-agents, ensure the reports directory exists. Run this once:

```bash
mkdir -p .specs/reports
```

This directory holds per-step code-reviewer reports so the orchestrator can reference reviewer scratchpad paths in retry feedback and the final summary.

## Phase 1: Load and Analyze Task

**This is the ONLY phase where you read a file.**

### Step 1.1: Load Task Details

Read the task file ONCE:

```bash
Read $TASK_PATH
```

**After this read, you MUST NOT read any other files for the rest of execution.**

### Step 1.2: Identify Implementation Steps

Parse the `## Implementation Process` section:

- List all steps with dependencies
- Identify which steps have `Parallel with:` annotations
- Classify each step's verification needs from the qa-engineer-authored `#### Verification` subsections (the qa-engineer ran during `/sdd:plan` and embedded these specifications directly into the task file):

| Verification Level (in task file) | When to Use | Code-Reviewer Dispatch | Threshold |
|-----------------------------------|-------------|------------------------|-----------|
| `None` | Simple operations (mkdir, delete, schema-validated config) | Skip the code-reviewer entirely | N/A |
| `Single Judge` | Non-critical artifacts | 1 `sdd:code-reviewer` agent | `THRESHOLD_FOR_STANDARD_COMPONENTS` (default 4.0) |
| `Panel of 2 Judges` (a.k.a. `Panel of 2`) | Critical / high-stakes artifacts | 2 `sdd:code-reviewer` agents in parallel; aggregate by median voting on `combined_score` | `THRESHOLD_FOR_CRITICAL_COMPONENTS` (default 4.5) |
| `Per-Item Judges` (a.k.a. `Per-Item`) | Multiple similar items in one step | 1 `sdd:code-reviewer` per item, all in parallel | Per-item threshold matches step's level (standard or critical as marked) |

Honor the labels exactly as they appear in the task file — `Single Judge`, `Panel of 2 Judges`, `Per-Item Judges`, `None` — these are the labels emitted by the qa-engineer's templates.

### Step 1.3: Create Todo List

Create TodoWrite with all implementation steps, marking verification requirements:

```json
{
  "todos": [
    {"content": "Step 1: [Title] - [Verification Level]", "status": "pending", "activeForm": "Implementing Step 1"},
    {"content": "Step 2: [Title] - [Verification Level]", "status": "pending", "activeForm": "Implementing Step 2"}
  ]
}
```

---

## Phase 2: Execute Implementation Steps

For each step in dependency order, select the dispatch pattern by reading the step's `#### Verification` Level:

| Verification Level | Pattern |
|--------------------|---------|
| `None` | **Pattern A** — developer only, no code-reviewer |
| `Single Judge` | **Pattern B** — developer + 1 `sdd:code-reviewer` |
| `Panel of 2 Judges` | **Pattern B-Panel** — developer + 2 `sdd:code-reviewer` agents in parallel (median voting) |
| `Per-Item Judges` | **Pattern C** — 1 developer per item + 1 `sdd:code-reviewer` per item, all in parallel |

If `SKIP_REVIEWS` is true, all reviewer dispatches are skipped (Patterns B/B-Panel/C effectively degrade to Pattern A) — proceed directly after the developer reports completion.

### Code-Reviewer Input Contract (NON-NEGOTIABLE)

Every `sdd:code-reviewer` dispatch — regardless of pattern — MUST include exactly these 5 inputs and NOTHING else that resembles a threshold or pass/fail expectation:

1. **Artifact Path(s)**: The file paths the developer reports as created or modified for this step (or item, in Pattern C)
2. **Step Description**: The full step text from the task file — Description, Acceptance Criteria, Expected Outputs (copy these inline; do NOT ask the reviewer to read the entire task file)
3. **Verification Specification Path**: Path to the per-step verification specification authored by qa-engineer. Two options, in this priority order:
   - **Preferred**: If the task file's `#### Verification` subsection contains a `verification_spec_path:` field pointing to a separate YAML file produced during planning, pass that path directly.
   - **Fallback**: If the spec is inlined inside the `#### Verification` markdown subsection, extract the rubric/checklist YAML to a temporary file under `.specs/reports/step-<N>-verification-spec.yaml` and pass that path. The temp file MUST contain the qa-engineer's rubric_dimensions and checklist exactly as written.
4. **Original Task Description**: The overall task being implemented — copy the top-of-task-file Description and Acceptance Criteria inline (kept short; this is for context only)
5. **CLAUDE_PLUGIN_ROOT**: The plugin root path (so the reviewer can resolve `@${CLAUDE_PLUGIN_ROOT}/scripts/create-scratchpad.sh`)

**You MUST NOT pass to the code-reviewer:**

- Any score threshold, target quality, or passing-line value
- Any PASS/FAIL expectation
- Any rubric or checklist you wrote yourself (only the qa-engineer's per-step spec is authoritative)
- The full task file path as a substitute for inlining Step Description / Original Task Description (the reviewer is intentionally narrow-scoped)

### Threshold Application (Orchestrator-Level Only)

After receiving the code-reviewer's report, the orchestrator (this skill) applies the threshold:

```
threshold = THRESHOLD_FOR_CRITICAL_COMPONENTS  if Verification Level is "Panel of 2 Judges"
          = THRESHOLD_FOR_STANDARD_COMPONENTS  if Verification Level is "Single Judge" or "Per-Item Judges"
          = LENIENT_THRESHOLD                  if the verification spec explicitly marks the step as lenient

# For Panel of 2: aggregate first
combined_score = median(reviewer1.combined_score, reviewer2.combined_score)
                  # for Single Judge / Per-Item: combined_score = reviewer.combined_score

all_issues = reviewer.issues  (or merged issues from both reviewers in Panel)

# PASS rule (orchestrator decides):
if combined_score >= threshold:
    PASS
elif combined_score >= 3.0 and every issue.priority == "Low":
    PASS  (acceptable: minor polish only, no high/medium issues)
else:
    FAIL → retry
```

The `combined_score` already incorporates spec_compliance + code_quality + Muda waste analysis (the reviewer aggregates them internally per its STAGE 8). The orchestrator does NOT need to re-aggregate sub-scores; only `combined_score` and `issues` matter for the gate decision.

### Retry Feedback Construction

When a step FAILs the orchestrator-level threshold and `MAX_ITERATIONS` is not yet exhausted, dispatch the developer again with this feedback structure:

```
Re-implement Step [N]: [Step Title] — Iteration [K] of [MAX_ITERATIONS]

Task File: $TASK_PATH
Step Number: [N]

Previous attempt failed quality review. Reviewer combined_score: [X.XX] / threshold [Y.Y]

Issues to fix (consolidated from spec_compliance, code_quality, and waste analysis — High → Medium → Low):
[paste reviewer.issues list verbatim, including source field, priority, description, evidence (file:line), impact, and suggestion]

Full reviewer report (for additional context, do NOT skim — use issues list as primary work list):
[path to reviewer's scratchpad report file under .specs/scratchpad/<hex>.md]

Your task:
- Address every High priority issue
- Address every Medium priority issue
- Preserve any user-edited code (refine mode) — build on top of it, do not overwrite
- Do NOT introduce new functionality beyond the original step's Expected Output
- Re-run tests/lint/build to ensure no regressions

When complete, report:
1. Files changed (paths)
2. Per-issue resolution status (Fixed / Partially Fixed / Skipped with justification)
3. Any new concerns introduced by the fix
```

After the developer completes the retry, dispatch the code-reviewer again with the SAME 5 inputs (the spec hasn't changed). Iterate until PASS or `MAX_ITERATIONS` reached.

### Pattern A: Simple Step (No Verification)

**1. Launch Developer Agent:**

Use Task tool with:

- **Agent Type**: `sdd:developer`
- **Model**: As specified in step or `opus` by default
- **Description**: "Implement Step [N]: [Title]"
- **Prompt**:

```
Implement Step [N]: [Step Title]

Task File: $TASK_PATH
Step Number: [N]

Your task:
- Execute ONLY Step [N]: [Step Title]
- Do NOT execute any other steps
- Follow the Expected Output and Success Criteria exactly

When complete, report:
1. What files were created/modified (paths)
2. Confirmation that success criteria are met
3. Any issues encountered
```

**2. Use Agent's Report (No Verification)**

- Agent reports what was created → Use this information
- **DO NOT read the created files yourself**
- This pattern has NO verification (simple operations)

**3. Mark Step Complete**

- Update task file:
  - Mark step title with `[DONE]` (e.g., `### Step 1: Setup [DONE]`)
  - Mark step's subtasks as `[X]` complete
- Update todo to `completed`

---

### Pattern B: Verified Step (Single Reviewer or Panel of 2)

Use this pattern for steps with `Single Judge` (1 reviewer) or `Panel of 2 Judges` (2 reviewers in parallel) verification levels.

**1. Launch Developer Agent:**

Use Task tool with:

- **Agent Type**: `sdd:developer`
- **Model**: As specified in step or `opus` by default
- **Description**: "Implement Step [N]: [Title]"
- **Prompt**:

```
Implement Step [N]: [Step Title]

Task File: $TASK_PATH
Step Number: [N]

Your task:
- Execute ONLY Step [N]: [Step Title]
- Do NOT execute any other steps
- Follow the Expected Output and Success Criteria exactly

When complete, report:
1. What files were created/modified (paths)
2. Confirmation of completion
3. Self-critique summary
```

**2. Wait for Completion**

- Receive the agent's report
- Note the artifact path(s) from the report
- **DO NOT read the artifact yourself**
- If `SKIP_REVIEWS` is true, skip directly to step 7 (Mark Step Complete)

**3. Prepare the Verification Specification Path:**

- Read the step's `#### Verification` subsection (already in memory from Phase 1).
- If a `verification_spec_path:` field is present, use that path directly.
- Otherwise, extract the embedded rubric/checklist YAML to `.specs/reports/step-<N>-verification-spec.yaml` and use that path.

**4. Launch Code-Reviewer Agent(s) in Parallel (MANDATORY):**

**⚠️ MANDATORY: You MUST launch the reviewer(s). Do NOT skip. Do NOT verify yourself.**

- For `Single Judge`: launch **1** `sdd:code-reviewer` agent.
- For `Panel of 2 Judges`: launch **2** `sdd:code-reviewer` agents in parallel with identical prompts.

Each reviewer receives EXACTLY the 5 inputs from the [Code-Reviewer Input Contract](#code-reviewer-input-contract-non-negotiable) above. Use this prompt structure:

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

You are the sdd:code-reviewer agent. Apply your full evaluation process (Stages 0-11) and return a single combined report.

Inputs:

1. Artifact Path(s):
   [list of file paths from the developer's report]

2. Step Description:
   [paste the step's Description, Acceptance Criteria, and Expected Output verbatim from the task file's Step [N] section]

3. Verification Specification Path:
   [absolute path to the qa-engineer's per-step verification YAML — see step 3 above]

4. Original Task Description:
   [paste the task file's top-level Description and Acceptance Criteria — keep this short, it is for context only]

5. CLAUDE_PLUGIN_ROOT: ${CLAUDE_PLUGIN_ROOT}

Reminder: You are threshold-blind. Do NOT compute or report a PASS/FAIL verdict. The orchestrator owns that decision. Return your combined report exactly per Stage 11 of your agent specification, including: spec_compliance_report, code_quality_report, waste_analysis (inside code_quality_report), combined_score, executive_summary, issues, strengths, rules_generated, and confidence.
```

**5. Aggregate Reviewer Results (orchestrator-side):**

- For `Single Judge`:
  - `combined_score = reviewer.combined_score`
  - `all_issues = reviewer.issues`
- For `Panel of 2 Judges`:
  - `combined_score = median(reviewer1.combined_score, reviewer2.combined_score)`
  - `all_issues = reviewer1.issues + reviewer2.issues` (de-duplicate by description+evidence)
  - Flag high-variance criteria where `|reviewer1.score − reviewer2.score| > 2.0` (per the Panel Voting Algorithm in Phase 5)

**6. Determine Threshold and Apply Gate:**

- Look up `threshold` from the [Threshold Application](#threshold-application-orchestrator-level-only) rules above (Single Judge → standard, Panel → critical, lenient marker → `LENIENT_THRESHOLD`).
- Apply the orchestrator-level PASS rule:
  - PASS if `combined_score >= threshold`
  - PASS if `combined_score >= 3.0` AND every entry in `all_issues` has `priority == "Low"`
  - Otherwise FAIL → retry

**On FAIL: Iterate Until PASS (max `MAX_ITERATIONS`, default 3)**

- Build retry feedback per the [Retry Feedback Construction](#retry-feedback-construction) section above
- Re-launch the developer agent with that feedback (preserve user's changes if in refine mode)
- Re-launch the code-reviewer(s) with the SAME 5 inputs after the developer reports completion
- **Iterate until PASS** or until `MAX_ITERATIONS` reached
- If `MAX_ITERATIONS` reached:
  - Log warning: "Step [N] did not pass after {MAX_ITERATIONS} iterations (final combined_score: X.XX, threshold: Y.Y)"
  - Proceed to next step (do not block indefinitely)

**7. On PASS: Mark Step Complete**

- Update task file:
  - Mark step title with `[DONE]` (e.g., `### Step 2: Create Service [DONE]`)
  - Mark step's subtasks as `[X]` complete
- Update todo to `completed`
- Record `combined_score` and reviewer scratchpad path(s) in tracking for the final summary

**8. Human-in-the-Loop Checkpoint (if applicable):**

**Only after step PASSES**, if step number is in `HUMAN_IN_THE_LOOP_STEPS` (or `HUMAN_IN_THE_LOOP_STEPS == "*"`):

```markdown
---
## 🔍 Human Review Checkpoint - Step [N]

**Step:** [Step Title]
**Combined Score:** [combined_score]/5.0 (threshold: [threshold])
**Status:** ✅ PASS

**Artifacts Created/Modified:**
- [artifact_path_1]
- [artifact_path_2]

**Reviewer Feedback (issues):**
[feedback summary — high/medium issues from reviewer.issues, even though step passed]

**Action Required:** Review the above artifacts and provide feedback or continue.

> Continue? [Y/n/feedback]:
---
```

- If user provides feedback: Store for next step or re-implement current step with feedback
- If user says "n": Pause workflow, report current progress
- If user says "Y" or continues: Proceed to next step

---

### Pattern C: Multi-Item Step (Per-Item Evaluations)

For steps that create multiple similar items:

**1. Launch Developer Agents in Parallel (one per item):**

Use Task tool for EACH item (launch all in parallel):

- **Agent Type**: `sdd:developer`
- **Model**: As specified or `opus` by default
- **Description**: "Implement Step [N], Item: [Name]"
- **Prompt**:

```
Implement Step [N], Item: [Item Name]

Task File: $TASK_PATH
Step Number: [N]
Item: [Item Name]

Your task:
- Create ONLY [item_name] from Step [N]
- Do NOT create other items or steps
- Follow the Expected Output and Success Criteria exactly

When complete, report:
1. File path created
2. Confirmation of completion
3. Self-critique summary
```

**2. Wait for All Completions**

- Collect all agent reports
- Note all artifact paths
- **DO NOT read any of the created files yourself**

**3. Prepare the Verification Specification Path (once for the step):**

- The qa-engineer's per-step verification spec is shared across all items in the step. Resolve its path the same way as Pattern B step 3 (use `verification_spec_path:` if present, otherwise extract embedded YAML to `.specs/reports/step-<N>-verification-spec.yaml`).

**4. Launch Code-Reviewer Agents in Parallel (one per item):**

**⚠️ MANDATORY: Launch reviewer agents. Do NOT skip. Do NOT verify yourself.**

For each item, dispatch one `sdd:code-reviewer` agent in parallel. Each reviewer gets the SAME 5 inputs from the [Code-Reviewer Input Contract](#code-reviewer-input-contract-non-negotiable), with `Artifact Path(s)` scoped to that single item:

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

You are the sdd:code-reviewer agent. Apply your full evaluation process (Stages 0-11) and return a single combined report.

Inputs:

1. Artifact Path(s):
   [path to ONLY this item from the developer's report]

2. Step Description:
   [paste the step's Description, Acceptance Criteria, Expected Output verbatim, plus a one-line note: "Reviewing only Item: [Item Name]"]

3. Verification Specification Path:
   [absolute path to the qa-engineer's per-step verification YAML]

4. Original Task Description:
   [paste the task file's top-level Description and Acceptance Criteria — short]

5. CLAUDE_PLUGIN_ROOT: ${CLAUDE_PLUGIN_ROOT}

Reminder: You are threshold-blind. Do NOT compute or report a PASS/FAIL verdict. The orchestrator owns that decision.
```

**5. Collect All Results and Apply the Gate per Item:**

For each item's reviewer report, apply the orchestrator-level threshold (per the [Threshold Application](#threshold-application-orchestrator-level-only) rules — Per-Item uses `THRESHOLD_FOR_STANDARD_COMPONENTS` unless the spec marks the step lenient or critical):

- PASS if `combined_score >= threshold` OR (`combined_score >= 3.0` AND every issue is Low priority)
- Otherwise FAIL → that specific item needs retry

**6. Report Aggregate:**

- Items passed: X/Y
- Items needing revision: [list with combined_score and top 3 issues per failing item]

**7. If Any FAIL: Iterate Until ALL PASS**

- For each failing item, build retry feedback per [Retry Feedback Construction](#retry-feedback-construction)
- Re-launch the developer agent for ONLY the failing items (preserve user's changes if in refine mode)
- Re-launch the code-reviewer for each re-implemented item with the SAME 5 inputs
- **Iterate until ALL items PASS** or until `MAX_ITERATIONS` reached
- If `MAX_ITERATIONS` reached:
  - Log warning: "Step [N] has {X} items that did not pass after {MAX_ITERATIONS} iterations"
  - Proceed to next step (do not block indefinitely)

**8. On ALL PASS: Mark Step Complete**

- Update task file:
  - Mark step title with `[DONE]` (e.g., `### Step 3: Create Items [DONE]`)
  - Mark step's subtasks as `[X]` complete
- Update todo to `completed`
- Record pass rate and per-item `combined_score` values in tracking

**9. Human-in-the-Loop Checkpoint (if applicable):**

**Only after ALL items PASS**, if step number is in `HUMAN_IN_THE_LOOP_STEPS` (or `HUMAN_IN_THE_LOOP_STEPS == "*"`):

```markdown
---
## 🔍 Human Review Checkpoint - Step [N]

**Step:** [Step Title]
**Items Passed:** X/Y
**Status:** ✅ ALL PASS

**Artifacts Created:**
- [item_1_path] — combined_score: X.XX
- [item_2_path] — combined_score: X.XX
- ...

**Action Required:** Review the above artifacts and provide feedback or continue.

> Continue? [Y/n/feedback]:
---
```

- If user provides feedback: Store for next step or re-implement items with feedback
- If user says "n": Pause workflow, report current progress
- If user says "Y" or continues: Proceed to next step

---

## ⚠️ CHECKPOINT: Before Proceeding to Definition-of-Done Verification

Before moving to DoD verification, verify you followed the rules:

- [ ] Did you launch `sdd:developer` agents for ALL implementations?
- [ ] Did you launch `sdd:code-reviewer` agents for ALL non-`None` verification levels (unless `SKIP_REVIEWS`)?
- [ ] Did you pass exactly the 5 reviewer inputs (no threshold)?
- [ ] Did you apply the threshold yourself against `combined_score`?
- [ ] Did you mark steps complete ONLY after the orchestrator-level PASS rule was satisfied?
- [ ] Did you avoid reading ANY artifact files yourself?

**If you read files other than the task file, you are doing it wrong. STOP and restart.**

---

## Phase 3: Definition of Done Verification

After all implementation steps are complete, verify the task meets all Definition of Done criteria.

> **Note:** Code quality (duplication, naming, architecture, control flow, error handling, size limits, Muda waste) is already enforced **per step** in Phase 2 by the `sdd:code-reviewer` agent — there is no separate end-of-task code quality phase. Phase 3 only confirms task-level Definition of Done items.

### Step 3.1: Launch Definition of Done Verification

**Use Task tool with:**

- **Agent Type**: `sdd:developer`
- **Model**: `opus`
- **Description**: "Verify Definition of Done"
- **Prompt**:

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

Verify all Definition of Done items in the task file.

Task File: $TASK_PATH

Your task:
1. Read the task file and locate the "## Definition of Done (Task Level)" section
2. Go through each checkbox item one by one
3. For each item, verify if it passes by:
   - Running appropriate tests (unit tests, E2E tests)
   - Checking build/compilation status
   - Verifying file existence and correctness
   - Checking code patterns and linting
4. You MUST mark each item in task file that passed verification with `[X]`
5. Return a structured report:
- List ALL Definition of Done items
- Status for each:
   - ✅ PASS - if the item is complete and verified
   - ❌ FAIL - if the item fails verification, with specific reason why
   - ⚠️ BLOCKED - if the item cannot be verified due to a blocker
- Evidence for each status
- Specific issues for any failures
- Overall pass rate

Be thorough - check everything the task requires.
```

### Step 3.2: Review Verification Results

- Receive the Definition of Done verification report
- Note which DoD items PASS and which FAIL
- If the verification agent reports that all DoD items PASS, you MUST confirm at the end of the task file that all DoD items are marked with `[X]`

### Step 3.3: Fix Failing DoD Items (If Any)

If any Definition of Done items FAIL:

**1. Launch Developer Agent for Each Failing Item:**

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

## Phase 4: Move Task to Done

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

---

## Phase 5: Aggregation and Reporting

### Panel Voting Algorithm (`Panel of 2 Judges`)

When dispatching 2 `sdd:code-reviewer` agents in parallel, aggregate their reports as follows. Think in steps, output each step result separately, do not skip steps.

#### Step 1: Collect combined_score and Per-Criterion Scores

The reviewers each return a full report (per Stage 11 of `sdd:code-reviewer`). Build two tables:

**Top-level scores:**

| Score | Reviewer 1 | Reviewer 2 | Median | Difference |
|-------|------------|------------|--------|------------|
| `combined_score` | X.X | X.X | ? | ? |
| `spec_compliance_score` (sub-score) | X.X | X.X | ? | ? |
| `builtin_score` (sub-score) | X.X | X.X | ? | ? |

**Per-criterion scores** (from both `spec_compliance_report.rubric_scores` and `code_quality_report.rubric_scores`):

| Source | Criterion | Reviewer 1 | Reviewer 2 | Median | Difference |
|--------|-----------|------------|------------|--------|------------|
| spec_compliance | [Name 1] | X.X | X.X | ? | ? |
| code_quality | [Name 2] | X.X | X.X | ? | ? |

#### Step 2: Calculate Median

For 2 reviewers: **Median = (Score1 + Score2) / 2**

The orchestrator's gate uses `median(combined_score)`, NOT a re-aggregation of sub-scores. Each reviewer already aggregated internally per its STAGE 8.

#### Step 3: Check for High Variance

**High variance** = reviewers disagree significantly (difference > 2.0 points on any score).

Formula: `|Reviewer1 - Reviewer2| > 2.0` → flag.

#### Step 4: Merge Issues Lists

Concatenate `reviewer1.issues` and `reviewer2.issues`, then de-duplicate by (description, evidence) pair. Keep the highest priority on duplicates. This merged list is what gets passed to the developer in retry feedback.

#### Step 5: Apply Orchestrator-Level Gate

- `panel_combined_score = median(reviewer1.combined_score, reviewer2.combined_score)`
- PASS if `panel_combined_score >= threshold`
- PASS if `panel_combined_score >= 3.0` AND every entry in the merged issues list has `priority == "Low"`
- Otherwise FAIL → retry

---

### Handling Disagreement

If reviewers significantly disagree (difference > 2.0 on `combined_score` or on any rubric criterion):

1. Flag the criterion (or the combined_score gap)
2. Present both reviewers' reasoning and issues with evidence
3. Ask user: "Reviewers disagree on [criterion]. Review manually?"
4. If yes: present evidence, get user decision
5. If no: use median (conservative approach)

### Final Report

After all steps complete and DoD verification passes:

```markdown
## Implementation Summary

### Task Status
- Task Status: `done` ✅
- All Definition of Done items: X/X PASS (100%)

### Configuration Used

| Setting | Value |
|---------|-------|
| **Standard Components Threshold** | {THRESHOLD_FOR_STANDARD_COMPONENTS}/5.0 |
| **Critical Components Threshold** | {THRESHOLD_FOR_CRITICAL_COMPONENTS}/5.0 |
| **Max Iterations** | {MAX_ITERATIONS or "3"} |
| **Human Checkpoints** | {HUMAN_IN_THE_LOOP_STEPS or "None"} |
| **Skip Reviews** | {SKIP_REVIEWS} |
| **Lenient Threshold** | {LENIENT_THRESHOLD}/5.0 |
| **Continue Mode** | {CONTINUE_MODE} |
| **Refine Mode** | {REFINE_MODE} |

### Steps Completed

| Step | Title | Status | Verification | Combined Score | Iterations | Reviewer Confirmed |
|------|-------|--------|--------------|----------------|------------|--------------------|
| 1    | [Title] | ✅ | None | N/A | 1 | - |
| 2    | [Title] | ✅ | Panel of 2 | 4.5/5 | 1 | ✅ |
| 3    | [Title] | ✅ | Per-Item | 5/5 passed | 2 | ✅ |
| 4    | [Title] | ✅ | Single Judge | 4.2/5 | 3 | ✅ |

**Legend:**
- ✅ PASS - Score >= threshold for step type
- ⚠️ MAX_ITER - Did not pass but MAX_ITERATIONS reached, proceeded anyway
- ⏭️ SKIPPED - Step skipped (continue/refine mode)

### Verification Summary

- Total steps: X
- Steps with verification: Y
- Passed on first try: Z
- Required iteration: W
- Total iterations across all steps: V
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

### High-Variance Criteria (Reviewers Disagreed)

- [Criterion] in [Step]: Reviewer 1 scored X, Reviewer 2 scored Y

### Human Review Summary (if --human-in-the-loop used)

| Step | Checkpoint | User Action | Feedback Incorporated |
|------|------------|-------------|----------------------|
| 2    | After PASS | Continued | - |
| 4    | After iteration 2 | Feedback | "Improve error messages" |
| 6    | After PASS | Continued | - |

### Task File Updated

- Task moved from `in-progress/` to `done/` folder
- All step titles marked `[DONE]`
- All step subtasks marked `[X]`
- All Definition of Done items marked `[X]`

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
│  Phase 0: Select Task                                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Use provided name or auto-select from todo/ (if 1 task) │  │
│  │ → Move task from todo/ to in-progress/                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Phase 1: Load Task                                           │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Read $TASK_PATH → Parse steps                           │  │
│  │ → Extract #### Verification specs → Create TodoWrite    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Phase 2: Execute Steps (Respecting Dependencies)             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  For each step:                                          │  │
│  │                                                          │  │
│  │  ┌──────────────┐    ┌───────────────┐    ┌───────────┐ │  │
│  │  │ developer    │───▶│ code-reviewer │───▶│ Orches-   │ │  │
│  │  │ Agent        │    │ Agent(s)      │    │ trator    │ │  │
│  │  │              │    │ (per-step     │    │ Threshold │ │  │
│  │  │              │    │  spec + code  │    │ Gate vs.  │ │  │
│  │  │              │    │  quality +    │    │ combined_ │ │  │
│  │  │              │    │  Muda)        │    │ score     │ │  │
│  │  └──────────────┘    └───────────────┘    └───────────┘ │  │
│  │                                                │   │     │  │
│  │                                               PASS FAIL  │  │
│  │                                                │   │     │  │
│  │                                                ▼   ▼     │  │
│  │                                    ┌────────┐  Retry  │  │  │
│  │                                    │ Mark   │  with   │  │  │
│  │                                    │Complete│  issues │  │  │
│  │                                    └────────┘  ↺     │  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Phase 3: Definition of Done Verification                     │
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
│  Phase 4: Move Task to Done                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ mv in-progress/$TASK → done/$TASK                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Phase 5: Aggregate & Report                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Collect all verification results                        │  │
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

# Continue from last completed step
/implement add-validation.feature.md --continue

# Refine after user fixes project files (detects changes, re-verifies affected steps)
/implement add-validation.feature.md --refine

# Human review after every step
/implement add-validation.feature.md --human-in-the-loop

# Human review after specific steps only
/implement add-validation.feature.md --human-in-the-loop 2,4,6

# Higher quality threshold (stricter) - sets both standard and critical to 4.5
/implement add-validation.feature.md --target-quality 4.5

# Different thresholds for standard (3.5) and critical (4.5) components
/implement add-validation.feature.md --target-quality 3.5,4.5

# Lower quality threshold for both (faster convergence)
/implement add-validation.feature.md --target-quality 3.5

# Unlimited iterations (default is 3)
/implement add-validation.feature.md --max-iterations unlimited

# Skip all per-step code-reviewer checks (fast but no quality gates)
/implement add-validation.feature.md --skip-reviews

# Custom lenient threshold for steps marked lenient by qa-engineer
/implement add-validation.feature.md --lenient-threshold 3.0

# Combined: continue with human review
/implement add-validation.feature.md --continue --human-in-the-loop
```

### Example 1: Implementing a Feature

```
User: /implement add-validation.feature.md

Phase 0: Task Selection...
Found task in: .specs/tasks/todo/add-validation.feature.md
Moving to in-progress: .specs/tasks/in-progress/add-validation.feature.md

Phase 1: Loading task...
Task: "Add form validation service"
Steps identified: 4 steps

Verification plan (from #### Verification sections):
- Step 1: No verification (directory creation)
- Step 2: Panel of 2 evaluations (ValidationService)
- Step 3: Per-item evaluations (3 validators)
- Step 4: Single evaluation (integration)

Phase 2: Executing...

Step 1: Launching sdd:developer agent...
  Agent: "Implement Step 1: Create Directory Structure..."
  Result: ✅ Directories created
  Verification: Skipped (simple operation)
  Status: ✅ COMPLETE

Step 2: Launching sdd:developer agent...
  Agent: "Implement Step 2: Create ValidationService..."
  Result: Files created, tests passing

  Launching 2 sdd:code-reviewer agents in parallel (Panel of 2)...
  Reviewer 1: combined_score 4.3/5.0
  Reviewer 2: combined_score 4.5/5.0
  Panel median: 4.4/5.0 (threshold 4.5) — issues all Low priority → PASS ✅
  Status: ✅ COMPLETE (Reviewer Confirmed)

[Continue for all steps...]

Phase 3: Definition of Done Verification...
Launching DoD verification agent...
  Agent: "Verify all Definition of Done items..."
  Result: 4/4 items PASS ✅

Phase 4: Moving task to done...
  mv .specs/tasks/in-progress/add-validation.feature.md .specs/tasks/done/

Phase 5: Final Report
Implementation complete.
- 4/4 steps completed
- 6 artifacts verified
- All passed first try
- Definition of Done: 4/4 PASS
- Task location: .specs/tasks/done/add-validation.feature.md ✅
```

### Example 2: Handling DoD Item Failure

```
[All steps complete...]

Phase 3: Definition of Done Verification...
Launching DoD verification agent...
  Agent: "Verify all Definition of Done items..."
  Result: 3/4 items PASS, 1 FAIL ❌

Failing item:
- "Code follows ESLint rules": 356 errors found

Should I attempt to fix this issue? [Y/n]

User: Y

Launching sdd:developer agent...
  Agent: "Fix ESLint errors..."
  Result: Fixed 356 errors, 0 warnings ✅

Re-launching DoD verification agent...
  Agent: "Re-verify all Definition of Done items..."
  Result: 4/4 items PASS ✅

Phase 4: Moving task to done...
All DoD checkboxes marked complete ✅

Phase 5: Final Report
Task verification complete.
- All DoD items now PASS
- 1 issue fixed (ESLint errors)
- Task location: .specs/tasks/done/ ✅
```

### Example 3: Handling Verification Failure

```
Step 3 Implementation complete.
Launching 2 sdd:code-reviewer agents in parallel (Panel of 2)...

Reviewer 1: combined_score 3.5/5.0
Reviewer 2: combined_score 3.2/5.0
Panel median: 3.35/5.0 — below threshold 4.5 → FAIL

Issues found (consolidated from spec_compliance + code_quality + waste):
- [High] Spec compliance — Test Coverage criterion scored 2/5
  Evidence: src/decision/decision.service.spec.ts (no edge-case tests)
  Suggestion: Add empty-input and null-input tests
- [High] Code quality — Reuse: custom Result type duplicates existing one
  Evidence: src/decision/types.ts:12 vs src/types/result.ts:5
  Suggestion: Import and use the project-standard Result<T, E>
- [Medium] Waste — Inventory: 3 unused imports in decision.service.ts
  Suggestion: Remove unused imports

Launching sdd:developer agent with consolidated reviewer feedback...
Agent: "Fix Step 3: Address reviewer issues (High → Medium)..."
Result: Issues fixed, tests added, imports cleaned

Re-launching 2 sdd:code-reviewer agents in parallel...
Reviewer 1: combined_score 4.5/5.0
Reviewer 2: combined_score 4.6/5.0
Panel median: 4.55/5.0 ≥ threshold 4.5 → PASS ✅
Status: ✅ COMPLETE (Reviewer Confirmed)
```

### Example 4: Continue from Interruption

```
User: /implement add-validation.feature.md --continue

Phase 0: Parsing flags...
Configuration:
- Continue Mode: true
- Target Quality: 4.0/5.0 (default)

Scanning task file for completed steps...
Found: Step 1 [DONE], Step 2 [DONE]
Last completed: Step 2

Verifying Step 2 artifacts...
Launching sdd:code-reviewer for Step 2...
Reviewer: combined_score 4.3/5.0 ≥ threshold 4.0 → PASS ✅
Marking step as complete in task file...

Resuming from Step 3...

Step 3: Launching sdd:developer agent...
[continues normally]
```

### Example 5: Refine After User Fixes

```
# User manually fixed src/validation/validation.service.ts
# (This file was created in Step 2: Create ValidationService)

User: /implement add-validation.feature.md --refine

Phase 0: Parsing flags...
Configuration:
- Refine Mode: true

Detecting changed project files...
Changed files:
- src/validation/validation.service.ts (modified)

Mapping files to implementation steps...
- src/validation/validation.service.ts → Step 2 (Create ValidationService)

Earliest affected step: Step 2
Preserving: Step 1 (unchanged)
Re-verifying from: Step 2 onwards

Step 2: Launching sdd:code-reviewer to verify with user's changes...
Reviewer: combined_score 4.3/5.0 ≥ threshold 4.0 → PASS ✅
Rest of logic is not affected, proceeding...

Step 3: Launching sdd:code-reviewer to verify...
Reviewer: combined_score 2.8/5.0 — issues include "typescript error in file" (High priority) → FAIL
Launching sdd:developer agent with reviewer issues to fix the error and align logic with user's changes...

Re-launching sdd:code-reviewer to verify fixed logic...
Reviewer: combined_score 4.5/5.0 → PASS ✅

[continues verifying remaining steps...]

All steps verified with user's changes incorporated ✅
```

### Example 6: Human-in-the-Loop Review

```
User: /implement add-validation.feature.md --human-in-the-loop

Configuration:
- Human Checkpoints: All steps

Step 1: Launching sdd:developer agent...
Result: Directories created ✅

---
## 🔍 Human Review Checkpoint - Step 1

**Step:** Create Directory Structure
**Combined Score:** N/A (verification level: None)
**Status:** ✅ COMPLETE

**Artifacts Created:**
- src/validation/
- src/validation/tests/

**Action Required:** Review the above artifacts and provide feedback or continue.

> Continue? [Y/n/feedback]: Y
---

Step 2: Launching sdd:developer agent...
Result: ValidationService created ✅

Launching 2 sdd:code-reviewer agents in parallel (Panel of 2)...
Reviewer 1: combined_score 4.5/5.0
Reviewer 2: combined_score 4.3/5.0
Panel median: 4.4/5.0 ≥ threshold (lenient mode in this example) → PASS ✅

---
## 🔍 Human Review Checkpoint - Step 2

**Step:** Create ValidationService
**Combined Score:** 4.4/5.0 (threshold: 4.0)
**Status:** ✅ PASS

**Artifacts Created:**
- src/validation/validation.service.ts
- src/validation/tests/validation.service.spec.ts

**Reviewer Feedback (issues):**
- [Low] Error messages could be more descriptive (Suggestion-level only)

**Action Required:** Review the above artifacts and provide feedback or continue.

> Continue? [Y/n/feedback]: The error messages could be more descriptive
---

Incorporating feedback: "error messages could be more descriptive"
Re-launching sdd:developer agent with feedback...
[iteration continues]
```

### Example 7: Strict Quality Threshold

```
User: /implement critical-api.feature.md --target-quality 4.5

Configuration:
- Target Quality: 4.5/5.0

Step 2: Implementing critical API endpoint...
Result: Endpoint created

Launching 2 sdd:code-reviewer agents (Panel of 2)...
Reviewer 1: combined_score 4.2/5.0
Reviewer 2: combined_score 4.3/5.0
Panel median: 4.25/5.0 — below threshold 4.5 → FAIL

Iteration 1: Re-launching developer with consolidated reviewer issues...
[fixes applied]

Re-launching 2 sdd:code-reviewer agents...
Reviewer 1: combined_score 4.4/5.0
Reviewer 2: combined_score 4.5/5.0
Panel median: 4.45/5.0 — below threshold 4.5 → FAIL

Iteration 2: Re-launching developer with reviewer issues...
[more fixes applied]

Re-launching 2 sdd:code-reviewer agents...
Reviewer 1: combined_score 4.6/5.0
Reviewer 2: combined_score 4.5/5.0
Panel median: 4.55/5.0 ≥ threshold 4.5 → PASS ✅

Status: ✅ COMPLETE (passed on iteration 2)
```

---

## Error Handling

### Implementation Failure

If sdd:developer agent reports failure:

1. Present the failure details to user
2. Ask clarification questions that could help resolve
3. Launch sdd:developer agent again with clarifications

### Reviewer Disagreement (Panel of 2)

If the two `sdd:code-reviewer` reports disagree significantly on `combined_score` (difference > 2.0) or on any individual rubric criterion (difference > 2.0):

1. Present both reviewers' reasoning and issues with evidence
2. Ask user to resolve: "Reviewers disagree on [criterion]. Your decision?"
3. Proceed based on user decision (or use median if user defers)

### Refine Mode: No Changes Detected

If `--refine` mode finds no git changes in the project:

1. Report: "No project file changes detected since last commit."
2. Suggest: "Make edits to project files first, then run --refine again."
3. Alternatively: "Run without --refine to re-implement all steps."

### Refine Mode: Changes Don't Map to Steps

If `--refine` mode finds changed files but none map to implementation steps:

1. Report: "Changed files don't match any implementation step's expected outputs."
2. List the changed files detected
3. Suggest: "Verify manually or run without --refine to re-verify all steps."

---

## Checklist

Before completing implementation:

### Configuration Handling

- [ ] Parsed all flags from `$ARGUMENTS` correctly
- [ ] Used `THRESHOLD_FOR_STANDARD_COMPONENTS` for `Single Judge` and `Per-Item Judges` steps
- [ ] Used `THRESHOLD_FOR_CRITICAL_COMPONENTS` for `Panel of 2 Judges` steps
- [ ] Used `LENIENT_THRESHOLD` only for steps the qa-engineer's spec marks lenient
- [ ] Iterated until orchestrator-level PASS rule satisfied (or `MAX_ITERATIONS` reached, default 3)
- [ ] Triggered human-in-the-loop checkpoints ONLY for steps in `HUMAN_IN_THE_LOOP_STEPS`
- [ ] If `SKIP_REVIEWS` is true: Skipped ALL code-reviewer dispatches
- [ ] If `CONTINUE_MODE` is true: Verified last step (via code-reviewer) and resumed correctly
- [ ] If `REFINE_MODE` is true: Detected changed project files, mapped to steps, re-verified from earliest affected step

### Context Protection (CRITICAL)

- [ ] Read ONLY the task file (`$TASK_PATH` in `.specs/tasks/in-progress/`) - no other files
- [ ] Did NOT read implementation outputs, reference files, or artifacts
- [ ] Used sub-agent reports for status - did NOT read files to "check"

### Delegation

- [ ] ALL implementations done by `sdd:developer` agents via Task tool
- [ ] ALL per-step verifications done by `sdd:code-reviewer` agents via Task tool
- [ ] Did NOT perform any verification yourself
- [ ] Did NOT skip any verification steps (unless `SKIP_REVIEWS` is true)

### Reviewer Input Contract

- [ ] Passed exactly the 5 reviewer inputs (artifact, step desc, verification spec path, original task desc, CLAUDE_PLUGIN_ROOT)
- [ ] Did NOT pass any threshold, target quality, or PASS/FAIL expectation to the reviewer
- [ ] Resolved verification spec path from `verification_spec_path:` field OR exported the embedded YAML to `.specs/reports/step-<N>-verification-spec.yaml`
- [ ] Applied threshold logic at orchestrator level against `combined_score` (not inside reviewer)
- [ ] Rejected any reviewer report containing PASS/FAIL verdict or threshold reference

### Stage Tracking

- [ ] Each step marked complete ONLY after orchestrator-level PASS (or immediately if `SKIP_REVIEWS`)
- [ ] Task file updated after each step completion:
  - Step title marked with `[DONE]`
  - Subtasks marked with `[X]`
- [ ] Todo list updated after each step completion

### Execution Quality

- [ ] All steps executed in dependency order
- [ ] Parallel steps launched simultaneously (not sequentially)
- [ ] Each `sdd:developer` agent received focused prompt with exact step
- [ ] All non-`None` verification levels were reviewed by `sdd:code-reviewer` (unless `SKIP_REVIEWS`)
- [ ] Panel-of-2 used 2 reviewers in parallel with median voting on `combined_score`
- [ ] Per-Item used one reviewer per item in parallel
- [ ] Failed reviews iterated using reviewer's `issues` as feedback until orchestrator-level PASS
- [ ] Final report generated with reviewer confirmation status
- [ ] User informed of any reviewer disagreements (Panel high-variance criteria)

### Human-in-the-Loop (if enabled)

- [ ] Displayed checkpoint after each step in `HUMAN_IN_THE_LOOP_STEPS`
- [ ] Incorporated user feedback into subsequent iterations/steps
- [ ] Paused workflow when user requested

### Final Verification and Completion

- [ ] Definition of Done verification agent launched
- [ ] All DoD items verified (PASS/FAIL/BLOCKED status)
- [ ] Failing DoD items fixed via sdd:developer agents
- [ ] Re-verification performed after fixes
- [ ] Task moved from `in-progress/` to `done/` folder
- [ ] All DoD checkboxes marked `[X]` in task file
- [ ] Final verification report presented to user

---

## Appendix A: Verification Specifications Reference

This appendix documents how verification is specified in task files. During Phase 2 (Execute Steps), you will reference these specifications to understand how to verify each artifact.

### How Task Files Define Verification

Task files define verification requirements in `#### Verification` sections within each implementation step. These sections are authored by the qa-engineer agent during the planning phase (`/sdd:plan`) and serve as the **per-step verification specification** consumed by `sdd:code-reviewer` at implementation time.

### Required Elements

1. **Level**: Verification complexity (this label drives how many `sdd:code-reviewer` agents are dispatched, see Phase 2)
   - `None` - Simple operations (mkdir, delete, schema-validated config) - skip code-reviewer entirely
   - `Single Judge` - Non-critical artifacts - 1 reviewer dispatched; orchestrator threshold 4.0/5.0
   - `Panel of 2 Judges` - Critical artifacts - 2 reviewers dispatched in parallel, median voting on `combined_score`; orchestrator threshold 4.5/5.0
   - `Per-Item Judges` - Multiple similar items - 1 reviewer per item dispatched in parallel; orchestrator threshold 4.0/5.0 per item

2. **Artifact(s)**: Path(s) to file(s) being reviewed
   - Example: `src/decision/decision.service.ts`, `src/decision/tests/decision.service.spec.ts`

3. **Verification Specification YAML**: The qa-engineer's per-step rubric_dimensions and checklist (either inlined inside the `#### Verification` section as a YAML code block, or referenced by `verification_spec_path:`). The orchestrator passes this YAML's path to the code-reviewer; the code-reviewer is threshold-blind.

4. **Reference Pattern** (Optional): Path to example of good implementation
   - Example: `src/app.service.ts` for NestJS service patterns
   - Embedded inside the verification spec, the code-reviewer applies it as part of its Stage 2 reference result.

> **Note on threshold:** The threshold is NOT stored in the verification spec or in the task file. It is selected by the orchestrator from `THRESHOLD_FOR_STANDARD_COMPONENTS` / `THRESHOLD_FOR_CRITICAL_COMPONENTS` / `LENIENT_THRESHOLD` based on the Level label. The code-reviewer never sees a threshold.

### Rubric Format

Rubrics in task files use this markdown table format:

```markdown
| Criterion | Weight | Description |
|-----------|--------|-------------|
| [Name 1]  | 0.XX   | [What to evaluate] |
| [Name 2]  | 0.XX   | [What to evaluate] |
| ...       | ...    | ...         |
```

**Requirements:**

- Weights MUST sum to 1.0
- Each criterion has a clear, measurable description
- Typically 3-6 criteria per rubric

**Example:**

```markdown
| Criterion | Weight | Description |
|-----------|--------|-------------|
| Type Correctness | 0.35 | Types match specification exactly |
| API Contract Alignment | 0.25 | Aligns with documented API contract |
| Export Structure | 0.20 | Barrel exports correctly expose all types |
| Code Quality | 0.20 | Follows project TypeScript conventions |
```

### Scoring Scale

When the `sdd:code-reviewer` evaluates artifacts, it uses this 5-point scale for each criterion (per its built-in [Scoring Scale](../../agents/code-reviewer.md) section):

- **1 (Poor)**: Does not meet requirements
  - Missing essential elements
  - Fundamental misunderstanding of requirements

- **2 (Below Average)**: Multiple issues, partially meets requirements
  - Some correct elements, but significant gaps
  - Would require substantial rework

- **3 (Adequate)**: Meets basic requirements
  - Functional but minimal
  - Room for improvement in quality or completeness

- **4 (Good)**: Meets all requirements, few minor issues
  - Solid implementation
  - Minor polish could improve it

- **5 (Excellent)**: Exceeds requirements
  - Exceptional quality
  - Goes beyond what was asked
  - Could serve as reference implementation

### Using Verification Specs During Execution

**During Phase 2 (Execute Steps):**

1. After a `sdd:developer` agent completes implementation
2. Read the step's `#### Verification` subsection (already in memory from Phase 1's single read of the task file)
3. Extract: Level, Artifact paths, the verification spec YAML (or its path)
4. Resolve the verification spec path: use `verification_spec_path:` if present, otherwise export the embedded YAML to `.specs/reports/step-<N>-verification-spec.yaml`
5. Launch the appropriate count of `sdd:code-reviewer` agent(s) based on Level (see Phase 2 dispatch patterns)
6. Pass exactly the 5 inputs to each reviewer (artifact, step desc, spec path, original task desc, CLAUDE_PLUGIN_ROOT) — **NEVER a threshold**
7. Receive the reviewer's combined report; aggregate (median for Panel)
8. Apply the orchestrator-level threshold gate against `combined_score`
9. If FAIL, launch `sdd:developer` with the consolidated reviewer issues as feedback and re-verify

**Example Verification Section in Task File:**

```markdown
#### Verification

**Level:** Panel of 2 Judges with Aggregated Voting
**Artifact:** `src/decision/decision.service.ts`, `src/decision/tests/decision.service.spec.ts`

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Routing Logic | 0.20 | Correctly routes by customerType |
| Drip Feed Implementation | 0.25 | 2% random approval for rejected New customers only |
| Response Formatting | 0.20 | Correct decision outcome, triggeredRules preserved, ISO 8601 timestamp |
| Testability | 0.15 | Injectable randomGenerator enables deterministic testing |
| Test Coverage | 0.20 | Unit tests cover approval, rejection, drip feed, routing, timestamp |

**Reference Pattern:** NestJS service patterns, ZenEngineService API
```

This specification tells you to:

- Launch 2 `sdd:code-reviewer` agents in parallel (Panel of 2 → Pattern B-Panel)
- Pass them the artifact paths (service + test files), the step description, the path to the per-step verification spec YAML (which contains the 5-criterion rubric and checklist authored by qa-engineer), the original task description, and `${CLAUDE_PLUGIN_ROOT}`
- Do NOT pass any threshold to the reviewers — they are threshold-blind by design
- Receive each reviewer's `combined_score`; the orchestrator computes `median(combined_score)` and applies `THRESHOLD_FOR_CRITICAL_COMPONENTS` (default 4.5) at this layer
- If FAIL, dispatch the developer with consolidated reviewer issues; iterate up to `MAX_ITERATIONS`
