---
description: Implement a task with automated LLM-as-Judge verification for critical steps 
argument-hint: Task file [options] (e.g., "add-validation.feature.md --continue --human-in-the-loop")
---

# Implement Task with Verification

Your job is to implement solution in best quality using task specification and sub-agents. You MUST NOT stop until it critically neccesary or you are done! Avoid asking questions until it is critically neccesary! Launch implementation agent, judges, iterate till issues are fixed and then move to next step!

Execute task implementation steps with automated quality verification using LLM-as-Judge for critical artifacts.

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
| `--continue` | `--continue` | None | Continue implementation from last completed step. Launches judge first to verify state, then iterates with implementation agent. |
| `--refine` | `--refine` | `false` | Incremental refinement mode - detect changes against git and re-implement only affected steps (from modified step onwards). |
| `--human-in-the-loop` | `--human-in-the-loop [step1,step2,...]` | None | Steps after which to pause for human verification. If no steps specified, pauses after every step. |
| `--target-quality` | `--target-quality X.X` or `--target-quality X.X,Y.Y` | `4.0` (standard) / `4.5` (critical) | Target threshold value (out of 5.0). Single value sets both. Two comma-separated values set standard,critical. |
| `--max-iterations` | `--max-iterations N` | `3` | Maximum fix→verify cycles per step. Default is 3 iterations. Set to `unlimited` for no limit. |
| `--skip-judges` | `--skip-judges` | `false` | Skip all judge validation checks - steps proceed without quality gates. |

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
SKIP_JUDGES = --skip-judges || false
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
   - Launch judge to verify the last INCOMPLETE step's artifacts
   - If judge PASS: Mark step as done and resume from the next step
   - If judge FAIL: Re-implement the step and iterate until PASS

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
     - Launch **judge agent** to verify the step's artifacts (including user's changes)
     - If judge PASS: Mark step done, proceed to next
     - If judge FAIL: Launch implementation agent with user's changes as context, then re-verify
   - User's manual fixes are preserved - implementation agent should build upon them, not overwrite

5. **Example:**

   ```bash
   # User manually fixed src/validation/validation.service.ts
   # (This file was created in Step 2)
   
   /implement my-task.feature.md --refine
   
   # Detects: src/validation/validation.service.ts modified
   # Maps to: Step 2 (Create ValidationService)
   # Action: Launch judge for Step 2
   #   - If PASS: User's fix is good, proceed to Step 3
   #   - If FAIL: Implementation agent align rest of the code with user changes, without overwriting user's changes
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
   - After implementation + judge verification **PASS** for a step in `HUMAN_IN_THE_LOOP_STEPS`
   - After implementation + judge + implementation retry (before the next judge retry)
   - If `HUMAN_IN_THE_LOOP_STEPS` is `"*"`, triggers after every step

2. **At Checkpoint:**
   - Display current step results summary
   - Display generated artifacts with paths
   - Display judge score and feedback
   - Ask user: "Review step output. Continue? [Y/n/feedback]"
   - If user provides feedback, incorporate into next iteration or step
   - If user says "n", pause workflow

3. **Checkpoint Message Format:**

   ```markdown
   ---
   ## 🔍 Human Review Checkpoint - Step X

   **Step:** {step title}
   **Step Type:** {standard/critical}
   **Judge Score:** {score}/{threshold for step type} threshold
   **Status:** ✅ PASS / 🔄 ITERATING (attempt {n})

   **Artifacts Created/Modified:**
   - {artifact_path_1}
   - {artifact_path_2}

   **Judge Feedback:**
   {feedback summary}

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
- Mark stages complete after judge confirmation
- Aggregate results and report to user

### What You NEVER Do

| Prohibited Action | Why | What To Do Instead |
|-------------------|-----|-------------------|
| Read implementation outputs | Context bloat → command loss | Sub-agent reports what it created |
| Read reference files | Sub-agent's job to understand patterns | Include path in sub-agent prompt |
| Read artifacts to "check" them | Context bloat → forget verifications | Launch judge agent |
| Evaluate code quality yourself | Not your job, causes forgetting | Launch judge agent |
| Skip verification "because simple" | ALL verifications are mandatory | Launch judge agent anyway |

### Anti-Rationalization Rules

**If you think:** "I should read this file to understand what was created"
**→ STOP.** The sub-agent's report tells you what was created. Use that information.

**If you think:** "I'll quickly verify this looks correct"
**→ STOP.** Launch a judge agent. That's not your job.

**If you think:** "This is too simple to need verification"
**→ STOP.** If the task specifies verification, launch the judge. No exceptions.

**If you think:** "I need to read the reference file to write a good prompt"
**→ STOP.** Put the reference file PATH in the sub-agent prompt. Sub-agent reads it.

### Why This Matters

Orchestrators who read files themselves = context overflow = command loss = forgotten steps. Every time.

Orchestrators who "quickly verify" = skip judge agents = quality collapse = failed artifacts.

**Your context window is precious. Protect it. Delegate everything.**

---

## CRITICAL Configuration Rules

- Use `THRESHOLD_FOR_STANDARD_COMPONENTS` (default 4.0) for standard steps!
- Use `THRESHOLD_FOR_CRITICAL_COMPONENTS` (default 4.5) for steps marked as critical in task file!
- **Default is 3 iterations** - stop after 3 fix→verify cycles and proceed to next step (with warning)!
- If `MAX_ITERATIONS` is set to `unlimited`: Iterate until quality threshold is met (no limit)
- Trigger human-in-the-loop checkpoints ONLY after steps in `HUMAN_IN_THE_LOOP_STEPS` (or all steps if `"*"`)!
- **If `SKIP_JUDGES` is true: Skip ALL judge validation - proceed directly to next step after each implementation completes!**
- **If `CONTINUE_MODE` is true: Skip to `RESUME_FROM_STEP` - do not re-implement already completed steps!**
- **If `REFINE_MODE` is true: Detect changed project files, map to steps, re-verify from `REFINE_FROM_STEP` - preserve user's fixes!**

---

## Overview

This command orchestrates multi-step task implementation with:

1. **Sequential execution** respecting step dependencies
2. **Parallel execution** where dependencies allow
3. **Automated verification** using judge agents for critical steps
4. **Panel of LLMs (PoLL)** for high-stakes artifacts
5. **Aggregated voting** with position bias mitigation
6. **Stage tracking** with confirmation after each judge passes

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
    │    │ Launch sdd:developer agent                          │
    │    │ (implementation)                                │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Launch judge agent(s)                           │
    │    │ (verification per #### Verification section)    │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Judge PASS? → Mark step complete in task file   │
    │    │ Judge FAIL? → Fix and re-verify (max 2 retries) │
    │    └─────────────────────────────────────────────────┘
    │
    ▼
Phase 3: Final Verification
    │
    ├─── Verify all Definition of Done items
    │    │
    │    ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ Launch judge agent                              │
    │    │ (verify all DoD items)                          │
    │    └─────────────────┬───────────────────────────────┘
    │                      │
    │                      ▼
    │    ┌─────────────────────────────────────────────────┐
    │    │ All PASS? → Proceed to Phase 4                  │
    │    │ Any FAIL? → Fix and re-verify (iterate)         │
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
| **Skip Judges** | {SKIP_JUDGES} |
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
     - Launch judge agent to verify the artifacts from that step
     - If judge PASS: Set `RESUME_FROM_STEP = LAST_COMPLETED_STEP + 1`
     - If judge FAIL: Set `RESUME_FROM_STEP = LAST_COMPLETED_STEP` (re-implement)

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
   - Pass this context to judge and implementation agents
   - Agents should build upon user's fixes, not overwrite them

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
- Classify each step's verification needs from `#### Verification` sections:

| Verification Level | When to Use | Judge Configuration |
|--------------------|-------------|---------------------|
| None | Simple operations (mkdir, delete) | Skip verification |
| Single Judge | Non-critical artifacts | 1 judge, threshold 4.0/5.0 |
| Panel of 2 Judges | Critical artifacts | 2 judges, median voting, threshold 4.5/5.0 |
| Per-Item Judges | Multiple similar items | 1 judge per item, parallel |

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

For each step in dependency order:

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

### Pattern B: Critical Step (Panel of 2 Evaluations)

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

**3. Launch 2 Evaluation Agents in Parallel (MANDATORY):**

**⚠️ MANDATORY: This pattern requires launching evaluation agents. You MUST launch these evaluations. Do NOT skip. Do NOT verify yourself.**

**Use `sdd:developer` agent type for evaluations**

**Evaluation 1 & 2** (launch both in parallel with same prompt structure):

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology.

Evaluate artifact at: [artifact_path from implementation agent report]

**Chain-of-Thought Requirement:** Justification MUST be provided BEFORE score for each criterion.

Rubric:
[paste rubric table from #### Verification section]

Context:
- Read $TASK_PATH
- Verify Step [N] ONLY: [Step Title]
- Threshold: [from #### Verification section]
- Reference pattern: [if specified in #### Verification section]

You can verify the artifact works - run tests, check imports, validate syntax.

Return: scores per criterion with evidence, overall weighted score, PASS/FAIL, improvements if FAIL.
```

**4. Aggregate Results:**

- Calculate median score per criterion
- Flag high-variance criteria (std > 1.0)
- Pass if median overall ≥ threshold

**5. Determine Threshold:**

- Check if step is marked as critical in task file (in `#### Verification` section or step metadata)
- If critical: use `THRESHOLD_FOR_CRITICAL_COMPONENTS`
- If standard: use `THRESHOLD_FOR_STANDARD_COMPONENTS`

**6. On FAIL: Iterate Until PASS (max 3 iterations by default)**

- Present issues to implementation agent with judge feedback
- Re-implement with judge feedback incorporated (align code with requirements, preserve user's changes if in refine mode)
- Re-verify with judge
- **Iterate until PASS** - continue fix → verify cycle until quality threshold is met or max iterations reached
- If `MAX_ITERATIONS` reached (default 3):
  - Log warning: "Step [N] did not pass after {MAX_ITERATIONS} iterations"
  - Proceed to next step (do not block indefinitely)

**7. On PASS: Mark Step Complete**

- Update task file:
  - Mark step title with `[DONE]` (e.g., `### Step 2: Create Service [DONE]`)
  - Mark step's subtasks as `[X]` complete
- Update todo to `completed`
- Record judge scores in tracking

**8. Human-in-the-Loop Checkpoint (if applicable):**

**Only after step PASSES**, if step number is in `HUMAN_IN_THE_LOOP_STEPS` (or `HUMAN_IN_THE_LOOP_STEPS == "*"`):

```markdown
---
## 🔍 Human Review Checkpoint - Step [N]

**Step:** [Step Title]
**Judge Score:** [score]/[threshold for step type] threshold
**Status:** ✅ PASS

**Artifacts Created/Modified:**
- [artifact_path_1]
- [artifact_path_2]

**Judge Feedback:**
[feedback summary from judges]

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

**3. Launch Evaluation Agents in Parallel (one per item)**

**⚠️ MANDATORY: Launch evaluation agents. Do NOT skip. Do NOT verify yourself.**

**Use `sdd:developer` agent type for evaluations**

For each item:

```
CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}

Read @${CLAUDE_PLUGIN_ROOT}/prompts/judge.md for evaluation methodology.

Evaluate artifact at: [item_path from implementation agent report]

**Chain-of-Thought Requirement:** Justification MUST be provided BEFORE score for each criterion.

Rubric:
[paste rubric from #### Verification section]

Context:
- Read $TASK_PATH
- Verify Step [N]: [Step Title]
- Verify ONLY this Item: [Item Name]
- Threshold: [from #### Verification section]

You can verify the artifact works - run tests, check syntax, confirm dependencies.

Return: scores with evidence, overall score, PASS/FAIL, improvements if FAIL.
```

**4. Collect All Results**

**5. Report Aggregate:**

- Items passed: X/Y
- Items needing revision: [list with specific issues]

**6. Determine Threshold:**

- Check if step is marked as critical in task file (in `#### Verification` section or step metadata)
- If critical: use `THRESHOLD_FOR_CRITICAL_COMPONENTS`
- If standard: use `THRESHOLD_FOR_STANDARD_COMPONENTS`

**7. If Any FAIL: Iterate Until ALL PASS**

- Present failing items with judge feedback to implementation agent
- Re-implement only failing items with feedback incorporated (preserve user's changes if in refine mode)
- Re-verify failing items with judge
- **Iterate until ALL PASS** - continue fix → verify cycle until all items meet quality threshold or max iterations reached
- If `MAX_ITERATIONS` reached (default 3):
  - Log warning: "Step [N] has {X} items that did not pass after {MAX_ITERATIONS} iterations"
  - Proceed to next step (do not block indefinitely)

**8. On ALL PASS: Mark Step Complete**

- Update task file:
  - Mark step title with `[DONE]` (e.g., `### Step 3: Create Items [DONE]`)
  - Mark step's subtasks as `[X]` complete
- Update todo to `completed`
- Record pass rate in tracking

**9. Human-in-the-Loop Checkpoint (if applicable):**

**Only after ALL items PASS**, if step number is in `HUMAN_IN_THE_LOOP_STEPS` (or `HUMAN_IN_THE_LOOP_STEPS == "*"`):

```markdown
---
## 🔍 Human Review Checkpoint - Step [N]

**Step:** [Step Title]
**Items Passed:** X/Y
**Status:** ✅ ALL PASS

**Artifacts Created:**
- [item_1_path]
- [item_2_path]
- ...

**Action Required:** Review the above artifacts and provide feedback or continue.

> Continue? [Y/n/feedback]:
---
```

- If user provides feedback: Store for next step or re-implement items with feedback
- If user says "n": Pause workflow, report current progress
- If user says "Y" or continues: Proceed to next step

---

## ⚠️ CHECKPOINT: Before Proceeding to Final Verification

Before moving to final verification, verify you followed the rules:

- [ ] Did you launch sdd:developer agents for ALL implementations?
- [ ] Did you launch evaluation agents for ALL verifications?
- [ ] Did you mark steps complete ONLY after judge PASS?
- [ ] Did you avoid reading ANY artifact files yourself?

**If you read files other than the task file, you are doing it wrong. STOP and restart.**

---

## Phase 3: Final Verification

After all implementation steps are complete, verify the task meets all Definition of Done criteria.

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

- Receive the verification report
- Note which items PASS and which FAIL
- if judge report that all items PASS, you MUST read end of task file to verify that all DoD items are marked with `[X]`

### Step 3.3: Fix Failing Items (If Any)

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

### Panel Voting Algorithm

When using 2+ evaluations, follow these manual computation steps:

- Think in steps, output each step result separately!
- Do not skip steps!

#### Step 1: Collect Scores per Criterion

Create a table with each criterion and scores from all evaluations:

| Criterion | Eval 1 | Eval 2 | Median | Difference |
|-----------|--------|--------|--------|------------|
| [Name 1]  | X.X    | X.X    | ?      | ?          |
| [Name 2]  | X.X    | X.X    | ?      | ?          |

#### Step 2: Calculate Median for Each Criterion

For 2 evaluations: **Median = (Score1 + Score2) / 2**

For 3+ evaluations: Sort scores, take middle value (or average of two middle values if even count)

#### Step 3: Check for High Variance

**High variance** = evaluators disagree significantly (difference > 2.0 points)

Formula: `|Eval1 - Eval2| > 2.0` → Flag as high variance

#### Step 4: Calculate Weighted Overall Score

Multiply each criterion's median by its weight and sum:

```
Overall = (Criterion1_Median × Weight1) + (Criterion2_Median × Weight2) + ...
```

#### Step 5: Determine Pass/Fail

Compare overall score to threshold:

- `Overall ≥ Threshold` → **PASS** ✅
- `Overall < Threshold` → **FAIL** ❌

---

### Handling Disagreement

If evaluations significantly disagree (difference > 2.0 on any criterion):

1. Flag the criterion
2. Present both evaluators' reasoning
3. Ask user: "Evaluators disagree on [criterion]. Review manually?"
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
| **Skip Judges** | {SKIP_JUDGES} |
| **Continue Mode** | {CONTINUE_MODE} |
| **Refine Mode** | {REFINE_MODE} |

### Steps Completed

| Step | Title | Status | Verification | Score | Iterations | Judge Confirmed |
|------|-------|--------|--------------|-------|------------|-----------------|
| 1    | [Title] | ✅ | Skipped | N/A | 1 | - |
| 2    | [Title] | ✅ | Panel (2) | 4.5/5 | 1 | ✅ |
| 3    | [Title] | ✅ | Per-Item | 5/5 passed | 2 | ✅ |
| 4    | [Title] | ✅ | Single | 4.2/5 | 3 | ✅ |

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

### High-Variance Criteria (Evaluators Disagreed)

- [Criterion] in [Step]: Eval 1 scored X, Eval 2 scored Y

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
│  │  │ developer    │───▶│ Judge Agent   │───▶│ PASS?     │ │  │
│  │  │ Agent        │    │ (verify)      │    │           │ │  │
│  │  └──────────────┘    └───────────────┘    └───────────┘ │  │
│  │                                                │   │     │  │
│  │                                               Yes  No    │  │
│  │                                                │   │     │  │
│  │                                                ▼   ▼     │  │
│  │                                    ┌────────┐  Fix & │   │  │
│  │                                    │ Mark   │  Retry │   │  │
│  │                                    │Complete│  ↺     │   │  │
│  │                                    └────────┘        │   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  Phase 3: Final Verification                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  ┌──────────────┐    ┌───────────────┐    ┌───────────┐ │  │
│  │  │ Judge Agent  │───▶│ All DoD       │───▶│ All PASS? │ │  │
│  │  │ (verify DoD) │    │ items checked │    │           │ │  │
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

# Skip all judge verifications (fast but no quality gates)
/implement add-validation.feature.md --skip-judges

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

  Launching 2 judge agents in parallel...
  Judge 1: 4.3/5.0 - PASS
  Judge 2: 4.5/5.0 - PASS
  Panel Result: 4.4/5.0 ✅
  Status: ✅ COMPLETE (Judge Confirmed)

[Continue for all steps...]

Phase 3: Final Verification...
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

Phase 3: Final Verification...
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
Launching judge agents...

Judge 1: 3.5/5.0 - FAIL (threshold 4.0)
Judge 2: 3.2/5.0 - FAIL

Issues found:
- Test Coverage: 2.5/5
  Evidence: "Missing edge case tests for empty input"
  Justification: "Success criteria requires edge case coverage"
- Pattern Adherence: 3.0/5
  Evidence: "Uses custom Result type instead of project standard"
  Justification: "Should use existing Result<T, E> from src/types"

Should I attempt to fix these issues? [Y/n]

User: Y

Launching sdd:developer agent with feedback...
Agent: "Fix Step 3: Address judge feedback..."
Result: Issues fixed, tests added

Re-launching judge agents...
Judge 1: 4.2/5.0 - PASS
Judge 2: 4.4/5.0 - PASS
Panel Result: 4.3/5.0 ✅
Status: ✅ COMPLETE (Judge Confirmed)
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
Launching judge agent for Step 3...
Judge: 4.3/5.0 - PASS ✅
Marking step as complete in task file...

Resuming from Step 4...

Step 3: Launching sdd:developer agent...
[continues normally from Step 4]
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

Step 2: Launching judge to verify rest of logic with user's changes...
Judge: 4.3/5.0 - PASS ✅
Rest of logic is not affected, proceeding...

Step 3: Launching judge to verify...
Judge: typescript error detected in file
Launching imeplementation agent to fix the error, and align logic with user's changes...

Launching judge to verify fixed logic...
Judge: 4.5/5.0 - PASS ✅

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
**Judge Score:** N/A (no verification)
**Status:** ✅ COMPLETE

**Artifacts Created:**
- src/validation/
- src/validation/tests/

**Action Required:** Review the above artifacts and provide feedback or continue.

> Continue? [Y/n/feedback]: Y
---

Step 2: Launching sdd:developer agent...
Result: ValidationService created ✅

Launching judge agents...
Judge 1: 4.5/5.0 - PASS
Judge 2: 4.3/5.0 - PASS
Panel Result: 4.4/5.0 ✅

---
## 🔍 Human Review Checkpoint - Step 2

**Step:** Create ValidationService
**Judge Score:** 4.4/5.0 (threshold: 4.0)
**Status:** ✅ PASS

**Artifacts Created:**
- src/validation/validation.service.ts
- src/validation/tests/validation.service.spec.ts

**Judge Feedback:**
- All criteria met
- Test coverage comprehensive

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

Launching judge agents...
Judge 1: 4.2/5.0 - FAIL (threshold: 4.5)
Judge 2: 4.3/5.0 - FAIL

Iteration 1: Re-implementing with feedback...
[fixes applied]

Launching judge agents...
Judge 1: 4.4/5.0 - FAIL
Judge 2: 4.5/5.0 - PASS

Iteration 2: Re-implementing with feedback...
[more fixes applied]

Launching judge agents...
Judge 1: 4.6/5.0 - PASS
Judge 2: 4.5/5.0 - PASS
Panel Result: 4.55/5.0 ✅

Status: ✅ COMPLETE (passed on iteration 2)
```

---

## Error Handling

### Implementation Failure

If sdd:developer agent reports failure:

1. Present the failure details to user
2. Ask clarification questions that could help resolve
3. Launch sdd:developer agent again with clarifications

### Judge Disagreement

If judges disagree significantly (difference > 2.0):

1. Present both perspectives with evidence
2. Ask user to resolve: "Judges disagree. Your decision?"
3. Proceed based on user decision

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
- [ ] Used `THRESHOLD_FOR_STANDARD_COMPONENTS` for standard steps
- [ ] Used `THRESHOLD_FOR_CRITICAL_COMPONENTS` for critical steps
- [ ] Iterated until quality threshold met (or `MAX_ITERATIONS` reached, default 3)
- [ ] Triggered human-in-the-loop checkpoints ONLY for steps in `HUMAN_IN_THE_LOOP_STEPS`
- [ ] If `SKIP_JUDGES` is true: Skipped ALL judge validation
- [ ] If `CONTINUE_MODE` is true: Verified last step and resumed correctly
- [ ] If `REFINE_MODE` is true: Detected changed project files, mapped to steps, re-verified from earliest affected step

### Context Protection (CRITICAL)

- [ ] Read ONLY the task file (`$TASK_PATH` in `.specs/tasks/in-progress/`) - no other files
- [ ] Did NOT read implementation outputs, reference files, or artifacts
- [ ] Used sub-agent reports for status - did NOT read files to "check"

### Delegation

- [ ] ALL implementations done by `sdd:developer` agents via Task tool
- [ ] ALL evaluations done by `sdd:developer` agents via Task tool
- [ ] Did NOT perform any verification yourself
- [ ] Did NOT skip any verification steps (unless `SKIP_JUDGES` is true)

### Stage Tracking

- [ ] Each step marked complete ONLY after judge PASS (or immediately if `SKIP_JUDGES`)
- [ ] Task file updated after each step completion:
  - Step title marked with `[DONE]`
  - Subtasks marked with `[X]`
- [ ] Todo list updated after each step completion

### Execution Quality

- [ ] All steps executed in dependency order
- [ ] Parallel steps launched simultaneously (not sequentially)
- [ ] Each sdd:developer agent received focused prompt with exact step
- [ ] All critical artifacts evaluated by judges (unless `SKIP_JUDGES`)
- [ ] Panel voting used for high-stakes artifacts
- [ ] Chain-of-thought requirement included in all evaluation prompts
- [ ] Failed evaluations iterated until quality threshold met
- [ ] Final report generated with judge confirmation status
- [ ] User informed of any evaluator disagreements

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

Task files define verification requirements in `#### Verification` sections within each implementation step. These sections specify:

### Required Elements

1. **Level**: Verification complexity
   - `None` - Simple operations (mkdir, delete) - skip verification
   - `Single Judge` - Non-critical artifacts - 1 judge, threshold 4.0/5.0
   - `Panel of 2 Judges` - Critical artifacts - 2 judges, median voting, threshold 4.0/5.0 or 4.5/5.0
   - `Per-Item Judges` - Multiple similar items - 1 judge per item, parallel execution

2. **Artifact(s)**: Path(s) to file(s) being verified
   - Example: `src/decision/decision.service.ts`, `src/decision/tests/decision.service.spec.ts`

3. **Threshold**: Minimum passing score
   - Typically 4.0/5.0 for standard quality
   - Sometimes 4.5/5.0 for critical components

4. **Rubric**: Weighted criteria table (see format below)

5. **Reference Pattern** (Optional): Path to example of good implementation
   - Example: `src/app.service.ts` for NestJS service patterns

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

When judges evaluate artifacts, they use this 5-point scale for each criterion:

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

1. After a sdd:developer agent completes implementation
2. Read the step's `#### Verification` section in the task file
3. Extract: Level, Artifact paths, Threshold, Rubric, Reference Pattern
4. Launch appropriate judge agent(s) based on Level
5. Provide judges with: Artifact path, Rubric, Threshold, Reference Pattern
6. Aggregate judge results and determine PASS/FAIL
7. If FAIL, launch sdd:developer agent to fix issues and re-verify

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

- Launch 2 judge agents in parallel
- Have them evaluate both service and test files
- Use the 5-criterion rubric with specified weights
- Do not pass threshold to judges, only use it to compare it with the average score of the judges
- Reference existing NestJS patterns for comparison
