---
description: Create, refine, parallelize, and verify a task with complexity estimation
argument-hint: Task title or description (e.g., "Add validation to form inputs")
allowed-tools: Task, Read, Write, Bash(ls), Bash(mkdir), AskUserQuestion, TodoWrite
---

# Add and Triage Workflow

## Role

You are a task lifecycle orchestrator. Create fully-specified, parallelized, and verification-ready tasks through a coordinated multi-agent workflow with quality gates after each phase.

## Goal

This workflow command orchestrates the complete task lifecycle:

1. **Create** - Generate initial task file with proper structure and complexity estimate
2. **Parallel Analysis** - Research, codebase analysis, and business analysis in parallel
3. **Architecture Synthesis** - Combine findings into architectural overview
4. **Decomposition** - Break into implementation steps with risks
5. **Parallelize** - Reorganize steps for maximum parallel execution
6. **Verify** - Add LLM-as-Judge verification sections

All phases include judge validation to prevent error propagation and ensure quality thresholds are met.

## User Input

```text
$ARGUMENTS
```

## Pre-Flight Checks

Before starting workflow:

1. **Initialize workflow progress tracking** using TodoWrite:

   ```json
   {
     "todos": [
       {"content": "Ensure directories exist", "status": "pending", "activeForm": "Ensuring directories exist"},
       {"content": "Phase 1: Create task file with complexity estimate", "status": "pending", "activeForm": "Creating task file"},
       {"content": "Phase 2a: Research relevant resources and documentation", "status": "pending", "activeForm": "Researching resources"},
       {"content": "Phase 2b: Analyze codebase impact and affected files", "status": "pending", "activeForm": "Analyzing codebase impact"},
       {"content": "Phase 2c: Business analysis and acceptance criteria", "status": "pending", "activeForm": "Analyzing business requirements"},
       {"content": "Phase 3: Architecture synthesis from research and analysis", "status": "pending", "activeForm": "Synthesizing architecture"},
       {"content": "Phase 4: Decompose into implementation steps", "status": "pending", "activeForm": "Decomposing into steps"},
       {"content": "Phase 5: Parallelize implementation steps", "status": "pending", "activeForm": "Parallelizing steps"},
       {"content": "Phase 6: Define verification rubrics", "status": "pending", "activeForm": "Defining verifications"}
     ]
   }
   ```

1. **Ensure directories exist**:

   ```bash
   mkdir -p .specs/tasks .specs/research .specs/analysis .specs/scratchpad .claude/tasks
   ```

Update each todo to `in_progress` when starting a phase and `completed` when judge passes.

## Workflow Execution

You MUST launch for each step a separate agent, instead of performing all steps yourself.

**CRITICAL:** For each agent you MUST:

1. Use the **Agent** type and **Model** specified in the step
2. Provide the task file path and user input as context
3. Require agent to implement exactly that step, not more, not less
4. After each sub-phase, launch a judge agent to validate quality before proceeding

### Complete Workflow Overview

```
Phase 1: Create Task [sonnet]
    │
    ▼
Phase 2: Parallel Analysis
    │
    ├─────────────────────┬─────────────────────┐
    ▼                     ▼                     ▼
Phase 2a:             Phase 2b:             Phase 2c:
Research              Codebase Analysis     Business Analysis
[researcher sonnet]   [code-explorer sonnet]  [business-analyst opus]
Judge 2a              Judge 2b              Judge 2c
(pass: 4.5/5.0)       (pass: 4.5/5.0)       (pass: 4.5/5.0)
    │                     │                     │
    └─────────────────────┴─────────────────────┘
                          │
                          ▼
                    Phase 3: Architecture Synthesis
                    [software-architect opus]
                    Judge 3 (pass: 4.5/5.0)
                          │
                          ▼
                    Phase 4: Decomposition
                    [tech-lead opus]
                    Judge 4 (pass: 4.5/5.0)
                          │
                          ▼
                    Phase 5: Parallelize [team-lead opus]
                    Judge 5 (pass: 4.5/5.0)
                          │
                          ▼
                    Phase 6: Verifications [opus]
                    Judge 6 (pass: 4.5/5.0)
                          │
                          ▼
                    Complete
```

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

## Phase 2: Parallel Analysis

Phase 2 launches three analysis phases in parallel, each with its own judge validation.

### Phase 2a/2b/2c: Parallel Sub-Phases

Launch these three phases **in parallel** immediately after Phase 1 completes:

---

#### Phase 2a: Research

**Model:** `sonnet`
**Agent:** `researcher`
**Depends on:** Phase 1
**Purpose:** Gather relevant resources, documentation, libraries, and prior art

Launch agent:

- **Description**: "Research task resources"
- **Prompt**:

  ```
  Task File: <task file path from Phase 1>
  Task Title: <title from Phase 1>
  ```

**Capture:**

- Research file path (e.g., `.specs/research/research-{name}.md`)
- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Number of resources gathered
- Key recommendation summary

---

#### Phase 2b: Codebase Impact Analysis

**Model:** `sonnet`
**Agent:** `code-explorer`
**Depends on:** Phase 1
**Purpose:** Identify affected files, interfaces, and integration points

Launch agent:

- **Description**: "Analyze codebase impact"
- **Prompt**:

  ```
  Task File: <task file path from Phase 1>
  Task Title: <title from Phase 1>
  ```

**Capture:**

- Analysis file path (e.g., `.specs/analysis/analysis-{name}.md`)
- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Files affected count (modify/create/delete)
- Risk level assessment
- Key integration points

---

#### Phase 2c: Business Analysis

**Model:** `opus`
**Agent:** `sdd:business-analyst`
**Depends on:** Phase 1
**Purpose:** Refine description and create acceptance criteria

Launch agent:

- **Description**: "Business analysis"
- **Prompt**:

  ```
  Read .claude/tasks/business-analysis-task.md and execute.

  Task File: <task file path from Phase 1>
  ```

**Capture:**

- Acceptance criteria count
- Scope defined (yes/no)
- User scenarios documented

---

### Judge 2a/2b/2c: Validate Parallel Phases

After **each** parallel phase completes, launch its respective judge **with the same agent type and model**.

#### Judge 2a: Validate Research

**Model:** `sonnet`
**Agent:** `researcher`
**Depends on:** Phase 2a completion
**Purpose:** Validate research completeness and relevance

Launch judge:

- **Description**: "Judge research quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to research file from Phase 2a}

  ### Context
  This is research output for task: {task title}. Evaluate comprehensiveness and relevance.

  ### Rubric
  1. Resource Coverage (weight: 0.35)
     - Documentation and references gathered?
     - Libraries and tools identified?
     - 1=Missing critical resources, 2=Basic coverage, 3=Adequate, 4=Comprehensive, 5=Excellent

  2. Pattern Relevance (weight: 0.30)
     - Are identified patterns applicable to this task?
     - Are recommendations actionable?
     - 1=Irrelevant, 2=Somewhat useful, 3=Adequate, 4=Well-targeted, 5=Perfect fit

  3. Issue Anticipation (weight: 0.20)
     - Potential issues identified with mitigations?
     - 1=None identified, 2=Few issues, 3=Adequate, 4=Good coverage, 5=Comprehensive

  4. Format & Links (weight: 0.15)
     - All resources have links/paths?
     - Fits in context window?
     - 1=Missing links, 2=Partial, 3=Adequate, 4=Good, 5=All linked
  ```

**Decision Logic:**

- **PASS** (score >= 4.5): Research complete
- **FAIL** (score < 4.5): Re-launch Phase 2a with feedback (max 2 retries)

---

#### Judge 2b: Validate Codebase Analysis

**Model:** `sonnet`
**Agent:** `code-explorer`
**Depends on:** Phase 2b completion
**Purpose:** Validate file identification accuracy and integration mapping

Launch judge:

- **Description**: "Judge codebase analysis quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute.

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

**Decision Logic:**

- **PASS** (score >= 4.5): Analysis complete
- **FAIL** (score < 4.5): Re-launch Phase 2b with feedback (max 2 retries)

---

#### Judge 2c: Validate Business Analysis

**Model:** `opus`
**Agent:** `sdd:business-analyst`
**Depends on:** Phase 2c completion
**Purpose:** Validate acceptance criteria quality and scope definition

Launch judge:

- **Description**: "Judge business analysis quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute.

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

**Decision Logic:**

- **PASS** (score >= 4.5): Business analysis complete
- **FAIL** (score < 4.5): Re-launch Phase 2c with feedback (max 2 retries)

---

### Synchronization Point

**Wait for ALL three parallel phases (2a, 2b, 2c) AND their judges to PASS before proceeding to Phase 3.**

---

## Phase 3: Architecture Synthesis

**Model:** `opus`
**Agent:** `software-architect`
**Depends on:** Phase 2a + Judge 2a PASS, Phase 2b + Judge 2b PASS, Phase 2c + Judge 2c PASS
**Purpose:** Synthesize research, analysis, and business requirements into architectural overview

Launch agent:

- **Description**: "Architecture synthesis"
- **Prompt**:

  ```
  Task File: <task file path from Phase 1>
  Research File: <research file path from Phase 2a>
  Analysis File: <analysis file path from Phase 2b>
  ```

**Capture:**

- Scratchpad file path (e.g., `.specs/scratchpad/<hex-id>.md`)
- Sections added to task file
- Key architectural decisions count
- Components identified (if applicable)
- Contracts defined (if applicable)

---

### Judge 3: Validate Architecture Synthesis

**Model:** `opus`
**Agent:** `software-architect`
**Depends on:** Phase 3 completion
**Purpose:** Validate architectural coherence and completeness

Launch judge:

- **Description**: "Judge architecture synthesis quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute.

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

**Decision Logic:**

- **PASS** (score >= 4.5): Architecture synthesis complete
- **FAIL** (score < 4.5): Re-launch Phase 3 with feedback (max 2 retries)

**Wait for PASS before Phase 4.**

---

## Phase 4: Decomposition

**Model:** `opus`
**Agent:** `sdd:tech-lead`
**Depends on:** Phase 3 + Judge 3 PASS
**Purpose:** Break architecture into implementation steps with success criteria and risks

Launch agent:

- **Description**: "Decompose into implementation steps"
- **Prompt**:

  ```
  Read .claude/tasks/decompose-task.md and execute.

  Task File: <task file path from Phase 1>
  ```

**Capture:**

- Implementation steps count
- Total subtasks count
- Critical path steps
- High priority risks count

---

### Judge 4: Validate Decomposition

**Model:** `opus`
**Agent:** `sdd:tech-lead`
**Depends on:** Phase 4 completion
**Purpose:** Validate implementation steps quality and completeness

Launch judge:

- **Description**: "Judge decomposition quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute.

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
     - 1=Vague, 2=Partially testable, 3=Adequate, 4=Good, 5=All testable

  3. Risk Coverage (weight: 0.25)
     - Blockers identified with resolutions?
     - Risks identified with mitigations?
     - High priority risks flagged?
     - 1=None, 2=Basic, 3=Adequate, 4=Good, 5=Comprehensive

  4. Completeness (weight: 0.20)
     - All architecture components have corresponding steps?
     - Implementation summary table present?
     - Definition of Done included?
     - 1=Incomplete, 2=Partial, 3=Adequate, 4=Good, 5=Complete
  ```

**Decision Logic:**

- **PASS** (score >= 4.5): Decomposition complete, proceed to Phase 5
- **FAIL** (score < 4.5): Re-launch Phase 4 with feedback (max 2 retries)

**Wait for PASS before Phase 5.**

---

## Phase 5: Parallelize Steps

**Model:** `opus`
**Agent:** `sdd:team-lead`
**Depends on:** Phase 4 + Judge 4 PASS
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

### Judge 5: Validate Parallelization

**Model:** `opus`
**Agent:** `sdd:team-lead`
**Depends on:** Phase 5 completion
**Purpose:** Validate dependency accuracy and parallelization optimization

Launch judge:

- **Description**: "Judge parallelization quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to parallelized task file from Phase 5}

  ### Context
  This is the output of Phase 5: Parallelize Steps. The artifact should contain implementation steps
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

**Decision Logic:**

- **PASS** (score >= 4.5): Proceed to Phase 6
- **FAIL** (score < 4.5): Re-launch Phase 5 with feedback (max 2 retries)

**Wait for PASS before Phase 6.**

---

## Phase 6: Define Verifications

**Model:** `opus`
**Agent:** `opus`
**Depends on:** Phase 5 + Judge 5 PASS
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

### Judge 6: Validate Verifications

**Model:** `opus`
**Agent:** `opus`
**Depends on:** Phase 6 completion
**Purpose:** Validate verification rubrics and thresholds

Launch judge:

- **Description**: "Judge verification quality"
- **Prompt**:

  ```
  Read ./plugins/sadd/tasks/judge.md for evaluation methodology and execute.

  ### Artifact Path
  {path to task file with verifications from Phase 6}

  ### Context
  This is the output of Phase 6: Define Verifications. The artifact should contain LLM-as-Judge
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

**Decision Logic:**

- **PASS** (score >= 4.5): Workflow complete, task ready
- **FAIL** (score < 4.5): Re-launch Phase 6 with feedback (max 2 retries)

---

## Completion

After all phases and judges complete with PASS:

1. Use git tool to stage the task file, research file, analysis file, and scratchpad file
2. Summarize the workflow results and output to user:

```markdown
### Task Created

| Property | Value |
|----------|-------|
| **File** | `<task file path>` |
| **Title** | `<generated title>` |
| **Type** | `<task/bug/feature>` |
| **Complexity** | `<S/M/L/XL>` |
| **Research** | `<research file path>` |
| **Analysis** | `<analysis file path>` |
| **Scratchpad** | `<scratchpad file path>` |
| **Implementation Steps** | `<count>` |
| **Parallelization Depth** | `<max parallel agents>` |
| **Total Verifications** | `<count>` |

### Quality Gates Summary

| Phase | Judge Score | Verdict |
|-------|-------------|---------|
| Phase 2a: Research | X.X/5.0 | ✅ PASS |
| Phase 2b: Codebase Analysis | X.X/5.0 | ✅ PASS |
| Phase 2c: Business Analysis | X.X/5.0 | ✅ PASS |
| Phase 3: Architecture Synthesis | X.X/5.0 | ✅ PASS |
| Phase 4: Decomposition | X.X/5.0 | ✅ PASS |
| Phase 5: Parallelize | X.X/5.0 | ✅ PASS |
| Phase 6: Verify | X.X/5.0 | ✅ PASS |

### Artifacts Generated

```

.specs/
├── tasks/
│   └── task-<name>.md        # Complete task specification
├── research/
│   └── research-<name>.md    # Research document
├── analysis/
│   └── analysis-<name>.md    # Codebase impact analysis
└── scratchpad/
    └── <hex-id>.md           # Architecture thinking scratchpad

```

### Next Steps

1. Review task: `<task file path>`
   - Edit the task file directly to make corrections
   - Add `//` comments to lines that need clarification or changes
   - Run `/refine-task` to incorporate your feedback — it detects changes against git and propagates updates **top-to-bottom** (editing a section only affects sections below it, not above)
2. If everything is fine, begin implementation: `/implement-task`
```

---

## Error Handling

If any phase fails:

1. Report the failure with agent output
2. Ask clarification questions from user that can help resolve the issue
3. Launch the phase agent again with list of questions and answers to resolve the issue

If any judge returns FAIL:

1. **Automatic retry**: Re-launch the phase agent with judge feedback (up to 2 retries per phase)
2. **After 2 failures**: Report to user with agent and judge output
3. Ask clarification questions from user that can help resolve the issue
4. Launch the phase agent again with list of questions and answers to resolve the issue
