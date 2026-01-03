---
description: Create, refine, parallelize, and verify a task with complexity estimation
argument-hint: Task title or description (e.g., "Add validation to form inputs")
allowed-tools: Task, Read, Write, Bash(ls), Bash(mkdir), AskUserQuestion, TodoWrite
---

# Add and Triage Workflow

<task>
You are a task lifecycle orchestrator. Create fully-specified, parallelized, and verification-ready tasks through a coordinated multi-agent workflow with quality gates after each phase.
</task>

<context>
This workflow command orchestrates the complete task lifecycle:

1. **Create** - Generate initial task file with proper structure and complexity estimate
2. **Refine** - Add detailed specification, affected files, resources (can update complexity)
3. **Parallelize** - Reorganize steps for maximum parallel execution
4. **Verify** - Add LLM-as-Judge verification sections

Phases 2-4 are followed by judge validation to prevent error propagation and ensure quality thresholds are met.
</context>

## User Input

```text
$ARGUMENTS
```

## Pre-Flight Checks

Before starting workflow:

1. **Ensure directories exist**:

   ```bash
   mkdir -p .specs/tasks
   mkdir -p .claude/tasks
   ```

2. **Verify task files exist** in `.claude/tasks/`:
   - `create-task.md`
   - `refine-task.md`
   - `parallelize-task.md`
   - `verify-task.md`

   If any are missing, create them based on the task templates below.

## Workflow Execution

You MUST launch for each step a separate agent, instead of performing all steps yourself.

**CRITICAL:** For each agent you MUST:

1. Use the **Agent** type specified in the step
2. Provide the task file path and user input as context
3. Require agent to implement exactly that step, not more, not less
4. After phases 2-4, launch a judge agent to validate quality before proceeding

### Parallelization Overview

```
Phase 1: Create Task
    │
    ▼
Phase 2: Refine Task ──► Judge 2 ──┐
                                    │ (pass threshold: 4.5/5.0)
                                    ▼
Phase 3: Parallelize ──► Judge 3 ──┐
                                    │ (pass threshold: 4.5/5.0)
                                    ▼
Phase 4: Verifications ─► Judge 4 ─► Complete
                                    (pass threshold: 4.5/5.0)
```

Phases 2-4 are sequential - each depends on the previous phase's output AND judge approval.

---

### Phase 1: Create Task

**Model:** `sonnet`
**Agent:** `sonnet`
**Depends on:** None
**Purpose:** Analyze user input, estimate complexity, and generate initial task file

Launch agent:

- **Description**: "Create task with complexity"
- **Prompt**:

  ```
  Read .claude/tasks/create-task.md and execute.

  User Input: $ARGUMENTS
  Target Directory: .specs/tasks/
  ```

**Capture:**

- Task file path (e.g., `.specs/tasks/task-add-validation.md`)
- Generated title
- Issue type (task/bug/feature)
- Complexity estimate (S/M/L/XL)

**Complexity Scale:**

| Size | Criteria |
|------|----------|
| **S** | Single file change, clear scope, <1 hour work |
| **M** | 2-5 files, well-defined scope, <1 day work |
| **L** | 5-15 files, requires design decisions, 1-3 days work |
| **XL** | 15+ files, architectural changes, >3 days work |

**Wait for completion before Phase 2.**

---

### Phase 2: Refine Task

**Model:** `opus`
**Agent:** `sdd:software-architect` or `sdd:tech-lead` based on type of task and complexity. If you task relates to 1-5 files, you should use `sdd:tech-lead`. If you task can affect more than 5 files, you should use `sdd:software-architect`.
**Depends on:** Phase 1
**Purpose:** Add detailed specification, affected files, implementation resources

Launch agent:

- **Description**: "Refine task specification"
- **Prompt**:

  ```
  Read .claude/tasks/refine-task.md and execute.

  Task File: <task file path from Phase 1>
  Initial Complexity: <complexity from Phase 1>

  Note: You may update the complexity estimate if detailed analysis reveals different scope.
  ```

**Capture:**

- Number of files identified
- Number of implementation steps created
- List of useful resources gathered
- Updated complexity (if changed)

---

### Judge 2: Validate Task Refinement

**Model:** `opus`
**Agent:** same like implementation agent
**Depends on:** Phase 2 completion
**Purpose:** Validate specification completeness and implementation readiness

Launch judge:

- **Description**: "Judge task refinement quality"
- **Prompt**:

  ```
  Read  ./plugins/sadd/tasks/judge.md for evaluation methodology and execute using following criteria.

  ### Artifact Path
  {path to refined task file from Phase 2}

  ### Context
  This is the output of Phase 2: Refine Task. The artifact should contain detailed specification,
  affected files, implementation resources, and implementation steps.

  ### Rubric
  1. Specification Completeness (weight: 0.30)
     - Are all requirements captured?
     - Are acceptance criteria defined?
     - 1=Missing major requirements, 2=Core covered, 4=Comprehensive, 5=Perfect

  2. File Identification Accuracy (weight: 0.25)
     - Are affected files correctly identified?
     - Is the scope realistic (not missing files, not over-scoped)?
     - 1=Major files missing/wrong, 2=Mostly correct, 3=Acceptable, 5=Precise identification

  3. Implementation Steps Quality (weight: 0.25)
     - Are steps actionable and clear?
     - Is the sequence logical?
     - 1=Vague/missing steps, 2=Workable, 3=Acceptable, 4=Ready to execute, 5=Perfect

  4. Resource Relevance (weight: 0.20)
     - Are listed resources useful for implementation?
     - Do patterns/references make sense?
     - 1=Irrelevant/missing, 2=Some useful, 3=Acceptable, 5=Perfect
  ```

**Orchestrator Decision Logic:**

1. **Parse judge output** - Extract scores for each criterion from judge's report
2. **Calculate weighted total**:

   ```
   Score = (Spec Completeness × 0.30) + (File Identification × 0.25) +
           (Implementation Steps × 0.25) + (Resource Relevance × 0.20)
   ```

3. **Apply threshold** (4.5/5.0):
   - **PASS** (score ≥ 4.5): Proceed to Phase 3
   - **FAIL** (score < 4.5): Re-launch Phase 2 with judge feedback

**If FAIL, retry Phase 2:**

Re-launch Phase 2 agent with:

- **Description**: "Fix refinement issues - attempt {N}"
- **Prompt**:

  ```
  Read .claude/tasks/refine-task.md and execute.

  Task File: <task file path from Phase 1>

  CRITICAL: Previous attempt failed judge evaluation. Fix these issues:

  ### Judge Feedback
  {Extract "Issues" and "Areas for Improvement" sections from judge report}

  ### Previous Scores
  {Show which criteria scored below 5}
  ```

**Retry limit**: Maximum 2 retries. After 2 failed attempts, report to user and request manual intervention.

**Wait for PASS before Phase 3.**

---

### Phase 3: Parallelize Steps

**Model:** `opus`
**Agent:** `sdd:team-lead`
**Depends on:** Phase 2 + Judge 2 PASS
**Purpose:** Reorganize implementation steps for maximum parallel execution

Launch agent:

- **Description**: "Parallelize implementation steps"
- **Prompt**:

  ```
  Read .claude/tasks/parallelize-task.md and execute.

  Task File: <task file path from Phase 1>
  ```

**Capture:**

- Number of steps reorganized
- Maximum parallelization depth
- Agent distribution summary

---

### Judge 3: Validate Parallelization

**Model:** `opus`
**Agent:** `sdd:team-lead`
**Depends on:** Phase 3 completion
**Purpose:** Validate dependency accuracy and parallelization optimization

Launch judge:

- **Description**: "Judge parallelization quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute using following criteria.

  ### Artifact Path
  {path to parallelized task file from Phase 3}

  ### Context
  This is the output of Phase 3: Parallelize Steps. The artifact should contain implementation steps
  reorganized for maximum parallel execution with explicit dependencies, agent assignments, and
  parallelization diagram.

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
     - Are agent types appropriate for outputs (opus by default, haiku for trivial, sonnet for simple but high in volume)?
     - Does selection follow the Agent Selection Guide?
     - 1=Wrong agents, 2=Mostly appropriate, 3=Acceptable, 4=Optimal selection, 5=Perfect selection

  4. Execution Directive Present (weight: 0.15)
     - Is the sub-agent execution directive present?
     - Are "MUST" requirements for parallel execution clear?
     - 1=Missing directive, 2=Partial, 3=Acceptable, 4=Complete directive, 5=Perfect directive
  ```

**Orchestrator Decision Logic:**

1. **Parse judge output** - Extract scores for each criterion from judge's report
2. **Calculate weighted total**:

   ```
   Score = (Dependency Accuracy × 0.35) + (Parallelization Maximized × 0.30) +
           (Agent Selection × 0.20) + (Execution Directive × 0.15)
   ```

3. **Apply threshold** (4.5/5.0):
   - **PASS** (score ≥ 4.5): Proceed to Phase 4
   - **FAIL** (score < 4.5): Re-launch Phase 3 with judge feedback

**If FAIL, retry Phase 3:**

Re-launch Phase 3 agent with:

- **Description**: "Fix parallelization issues - attempt {N}"
- **Prompt**:

  ```
  Read .claude/tasks/parallelize-task.md and execute.

  Task File: <task file path from Phase 1>

  CRITICAL: Previous attempt failed judge evaluation. Fix these issues:

  ### Judge Feedback
  {Extract "Issues" and "Areas for Improvement" sections from judge report}

  ### Previous Scores
  {Show which criteria scored below 5}
  ```

**Retry limit**: Maximum 2 retries. After 2 failed attempts, report to user and request manual intervention.

**Wait for PASS before Phase 4.**

---

### Phase 4: Define Verifications

**Model:** `opus`
**Agent:** `opus`
**Depends on:** Phase 3 + Judge 3 PASS
**Purpose:** Add LLM-as-Judge verification sections with rubrics

Launch agent:

- **Description**: "Define verification rubrics"
- **Prompt**:

  ```
  Read .claude/tasks/verify-task.md and execute.

  Task File: <task file path from Phase 1>
  ```

**Capture:**

- Number of steps with verification
- Total evaluations defined
- Verification breakdown (Panel/Per-Item/None)

---

### Judge 4: Validate Verifications

**Model:** `opus`
**Agent:** `opus`
**Depends on:** Phase 4 completion
**Purpose:** Validate verification rubrics and thresholds

Launch judge:

- **Description**: "Judge verification quality"
- **Prompt**:

  ```
  Read  ./plugins/sadd/tasks/judge.md for evaluation methodology and execute using following criteria.

  ### Artifact Path
  {path to task file with verifications from Phase 4}

  ### Context
  This is the output of Phase 4: Define Verifications. The artifact should contain LLM-as-Judge
  verification sections for each implementation step, including verification levels, custom rubrics,
  thresholds, and a verification summary table.

  ### Rubric
  1. Verification Level Appropriateness (weight: 0.30)
     - Do verification levels match artifact criticality?
     - HIGH criticality → Panel, MEDIUM → Single/Per-Item, LOW/NONE → None?
     - 1=Mismatched levels, 2=Mostly appropriate, 3=Acceptable, 5=Precisely calibrated

  2. Rubric Quality (weight: 0.30)
     - Are criteria specific to the artifact type (not generic)?
     - Do weights sum to 1.0?
     - Are descriptions clear and measurable?
     - 1=Generic/broken rubrics, 2=Adequate, 3=Acceptable, 5=Excellent custom rubrics

  3. Threshold Appropriateness (weight: 0.20)
     - Are thresholds reasonable (typically 4.0/5.0)?
     - Higher for critical, lower for experimental?
     - 1=Wrong thresholds, 2=Standard applied, 3=Acceptable, 5=Context-appropriate

  4. Coverage Completeness (weight: 0.20)
     - Does every step have a Verification section?
     - Is the Verification Summary table present?
     - 1=Missing verifications, 2=Most covered, 3=Acceptable, 5=100% coverage
  ```

**Orchestrator Decision Logic:**

1. **Parse judge output** - Extract scores for each criterion from judge's report
2. **Calculate weighted total**:

   ```
   Score = (Verification Level × 0.30) + (Rubric Quality × 0.30) +
           (Threshold Appropriateness × 0.20) + (Coverage Completeness × 0.20)
   ```

3. **Apply threshold** (4.5/5.0):
   - **PASS** (score ≥ 4.5): Workflow complete, task ready
   - **FAIL** (score < 4.5): Re-launch Phase 4 with judge feedback

**If FAIL, retry Phase 4:**

Re-launch Phase 4 agent with:

- **Description**: "Fix verification issues - attempt {N}"
- **Prompt**:

  ```
  Read .claude/tasks/verify-task.md and execute.

  Task File: <task file path from Phase 1>

  CRITICAL: Previous attempt failed judge evaluation. Fix these issues:

  ### Judge Feedback
  {Extract "Areas for Improvement" section from judge report}

  ### Previous Scores
  {Show which criteria scored below 5}
  ```

**Retry limit**: Maximum 2 retries. After 2 failed attempts, report to user and request manual intervention.

---

## Completion

After all phases and judges complete with PASS, summarize the workflow results:

### Task Created

| Property | Value |
|----------|-------|
| **File** | `<task file path>` |
| **Title** | `<generated title>` |
| **Type** | `<task/bug/feature>` |
| **Complexity** | `<S/M/L/XL>` |
| **Implementation Steps** | `<count>` |
| **Parallelization Depth** | `<max parallel agents>` |
| **Total Verifications** | `<count>` |

### Quality Gates Summary

| Phase | Judge Score | Verdict |
|-------|-------------|---------|
| Phase 2: Refine | X.X/5.0 | ✅ PASS |
| Phase 3: Parallelize | X.X/5.0 | ✅ PASS |
| Phase 4: Verify | X.X/5.0 | ✅ PASS |

### Files Identified

```
<tree structure of affected files>
```

### Next Steps

1. Review task: `Read <task file path>`
2. Begin implementation: `/implement-task <task-file-name>`

---

## Error Handling

If any phase fails:

1. **Report the failure** with agent output
2. **Suggest manual intervention**:
   - Phase 1 fail → Run `/add-task` manually
   - Phase 2 fail → Run `/refine-task` manually
   - Phase 3 fail → Run `/parallel-task-implementation` manually
   - Phase 4 fail → Run `/define-task-verifications` manually

3. **Do not continue** to dependent phases if a phase fails

If any judge returns FAIL:

1. **Automatic retry**: Re-launch the phase agent with judge feedback (up to 2 retries per phase)
2. **After 2 failures**: Report to user and request manual intervention

---

## Quick Mode

For simpler tasks that don't need full parallelization and verification:

**At workflow start**, ask user: "Full workflow (all 4 phases + judges) or quick mode (create + refine only)?"

**Quick mode:**

- Runs Phase 1 → Phase 2 → Judge 2
- Skips Phases 3 and 4
- Produces a refined task without parallelization analysis or verification rubrics
