---
description: Implement a task with automated LLM-as-Judge verification for critical steps
argument-hint: Task file name (e.g., add-validation.feature.md) with implementation steps defined
allowed-tools: Task, Read, TodoWrite, Bash
---

# Implement Task with Verification

Your job is to implement solution in best quality using task specification and sub-agents. You MUST NOT stop until it critically neccesary or you are done! Avoid asking questions until it is critically neccesary! Launch implementation agent, judges, iterate till issues are fixed and then move to next step!

Execute task implementation steps with automated quality verification using LLM-as-Judge for critical artifacts.

## User Input

```text
Task File: $ARGUMENTS
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
    │    │ Launch developer agent                          │
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
mv .specs/tasks/todo/$TASK_FILE .specs/tasks/in-progress/
```

Update `$TASK_PATH` to `.specs/tasks/in-progress/$TASK_FILE`

**If task is already in `in-progress/`:**
Set `$TASK_PATH` to `.specs/tasks/in-progress/$TASK_FILE`

### Step 0.3: Parse Flags

- `--continue` - If user input contains `--continue` flag, parse the task file, identify which phases and steps are completed and launch next step (that not completed yet) from judges checks. They should verify whether steps that are marked as not completed were started or not. If they not completed, then perform them as usual (start implementation) and continue from there. If they are completed, but not passed judge check, then fix the issues and continue from there. If they completed and passed judge checks, but not marked as done, then mark them as done and continue from there.

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

- **Agent Type**: `developer`
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

- **Agent Type**: `developer`
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

**Use `developer` agent type for evaluations**

**Evaluation 1 & 2** (launch both in parallel with same prompt structure):

```
Read .claude/prompts/judge.md for evaluation methodology.

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

**5. On PASS: Mark Step Complete**

- Update task file:
  - Mark step title with `[DONE]` (e.g., `### Step 2: Create Service [DONE]`)
  - Mark step's subtasks as `[X]` complete
- Update todo to `completed`
- Record judge scores in tracking

**6. On FAIL:**

- Present issues to user
- Ask: "Should I attempt to fix these issues?"
- If yes, re-implement and re-verify (max 2 retries)

---

### Pattern C: Multi-Item Step (Per-Item Evaluations)

For steps that create multiple similar items:

**1. Launch Developer Agents in Parallel (one per item):**

Use Task tool for EACH item (launch all in parallel):

- **Agent Type**: `developer`
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

**Use `developer` agent type for evaluations**

For each item:

```
Read .claude/prompts/judge.md for evaluation methodology.

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

**6. On ALL PASS: Mark Step Complete**

- Update task file:
  - Mark step title with `[DONE]` (e.g., `### Step 3: Create Items [DONE]`)
  - Mark step's subtasks as `[X]` complete
- Update todo to `completed`
- Record pass rate in tracking

**7. If Any FAIL:**

- Present failing items with judge feedback
- Ask: "Should I fix failing items?"
- If yes, re-implement only failing items and re-verify

---

## ⚠️ CHECKPOINT: Before Proceeding to Final Verification

Before moving to final verification, verify you followed the rules:

- [ ] Did you launch developer agents for ALL implementations?
- [ ] Did you launch evaluation agents for ALL verifications?
- [ ] Did you mark steps complete ONLY after judge PASS?
- [ ] Did you avoid reading ANY artifact files yourself?

**If you read files other than the task file, you are doing it wrong. STOP and restart.**

---

## Phase 3: Final Verification

After all implementation steps are complete, verify the task meets all Definition of Done criteria.

### Step 3.1: Launch Definition of Done Verification

**Use Task tool with:**

- **Agent Type**: `developer`
- **Model**: `opus`
- **Description**: "Verify Definition of Done"
- **Prompt**:

```
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
4. Mark each item with one of:
   - ✅ PASS - if the item is complete and verified
   - ❌ FAIL - if the item fails verification, with specific reason why
   - ⚠️ BLOCKED - if the item cannot be verified due to a blocker

Return a structured report:
- List ALL Definition of Done items
- Status for each (PASS/FAIL/BLOCKED)
- Evidence for each status
- Specific issues for any failures
- Overall pass rate

Be thorough - check everything the task requires.
```

### Step 3.2: Review Verification Results

- Receive the verification report
- Note which items PASS and which FAIL
- **DO NOT read any files yourself to verify - trust the judge agent's report**

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
mv .specs/tasks/in-progress/$TASK_FILENAME .specs/tasks/done/
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

### Steps Completed

| Step | Title | Status | Verification | Score | Judge Confirmed |
|------|-------|--------|--------------|-------|-----------------|
| 1    | [Title] | ✅ | Skipped | N/A | - |
| 2    | [Title] | ✅ | Panel (2) | 4.5/5 | ✅ |
| 3    | [Title] | ✅ | Per-Item | 5/5 passed | ✅ |

### Verification Summary

- Total steps: X
- Steps with verification: Y
- Passed on first try: Z
- Required revision: W
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

### Example 1: Implementing a Feature

```
User: /implement-task add-validation.feature.md

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

Step 1: Launching developer agent...
  Agent: "Implement Step 1: Create Directory Structure..."
  Result: ✅ Directories created
  Verification: Skipped (simple operation)
  Status: ✅ COMPLETE

Step 2: Launching developer agent...
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

Launching developer agent...
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

Launching developer agent with feedback...
Agent: "Fix Step 3: Address judge feedback..."
Result: Issues fixed, tests added

Re-launching judge agents...
Judge 1: 4.2/5.0 - PASS
Judge 2: 4.4/5.0 - PASS
Panel Result: 4.3/5.0 ✅
Status: ✅ COMPLETE (Judge Confirmed)
```

---

## Error Handling

### Implementation Failure

If developer agent reports failure:

1. Present the failure details to user
2. Ask clarification questions that could help resolve
3. Launch developer agent again with clarifications

### Judge Disagreement

If judges disagree significantly (difference > 2.0):

1. Present both perspectives with evidence
2. Ask user to resolve: "Judges disagree. Your decision?"
3. Proceed based on user decision

### Max Retries Exceeded

If a step fails verification after 2 retries:

1. Report all attempts and feedback
2. Ask: "Step [N] failed verification 2 times. Options:"
   - Continue anyway (with noted quality concerns)
   - Stop implementation
   - Provide additional guidance and retry

---

## Checklist

Before completing implementation:

### Context Protection (CRITICAL)

- [ ] Read ONLY the task file (`$TASK_PATH` in `.specs/tasks/in-progress/`) - no other files
- [ ] Did NOT read implementation outputs, reference files, or artifacts
- [ ] Used sub-agent reports for status - did NOT read files to "check"

### Delegation

- [ ] ALL implementations done by `developer` agents via Task tool
- [ ] ALL evaluations done by `developer` agents via Task tool
- [ ] Did NOT perform any verification yourself
- [ ] Did NOT skip any verification steps

### Stage Tracking

- [ ] Each step marked complete ONLY after judge PASS
- [ ] Task file updated after each step completion:
  - Step title marked with `[DONE]`
  - Subtasks marked with `[X]`
- [ ] Todo list updated after each step completion

### Execution Quality

- [ ] All steps executed in dependency order
- [ ] Parallel steps launched simultaneously (not sequentially)
- [ ] Each developer agent received focused prompt with exact step
- [ ] All critical artifacts evaluated by judges
- [ ] Panel voting used for high-stakes artifacts
- [ ] Chain-of-thought requirement included in all evaluation prompts
- [ ] Failed evaluations addressed (max 2 retries per step)
- [ ] Final report generated with judge confirmation status
- [ ] User informed of any evaluator disagreements

### Final Verification and Completion

- [ ] Definition of Done verification agent launched
- [ ] All DoD items verified (PASS/FAIL/BLOCKED status)
- [ ] Failing DoD items fixed via developer agents
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

1. After a developer agent completes implementation
2. Read the step's `#### Verification` section in the task file
3. Extract: Level, Artifact paths, Threshold, Rubric, Reference Pattern
4. Launch appropriate judge agent(s) based on Level
5. Provide judges with: Artifact path, Rubric, Threshold, Reference Pattern
6. Aggregate judge results and determine PASS/FAIL
7. If FAIL, launch developer agent to fix issues and re-verify

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
