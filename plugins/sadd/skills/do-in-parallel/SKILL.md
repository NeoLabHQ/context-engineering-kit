---
name: sadd:do-in-parallel
description: Launch multiple sub-agents in parallel to execute tasks across files or targets with intelligent model selection, quality-focused prompting, and meta-judge → LLM-as-a-judge verification
argument-hint: Task description [--files "file1.ts,file2.ts,..."] [--targets "target1,target2,..."] [--model opus|sonnet|haiku] [--output <path>]
---

# do-in-parallel

<task>
Launch multiple sub-agents in parallel to execute the same task across different files or targets. Analyze the task to intelligently select the optimal model, generate quality-focused prompts with Zero-shot Chain-of-Thought reasoning and mandatory self-critique, then dispatch one meta-judge per target (all in parallel), followed by implementors for each target in parallel, with LLM-as-a-judge verification using target-specific evaluation specs after each completes.
</task>

<context>
This command implements the **Supervisor/Orchestrator pattern** with parallel dispatch and **meta-judge → LLM-as-a-judge verification**. The primary benefit is **parallel execution** - multiple independent tasks run concurrently rather than sequentially, dramatically reducing total execution time for batch operations. One meta-judge per task generates tailored evaluation criteria specific to that task, then each parallel implementor is verified by an independent judge using its task-specific specification, with automatic retry on failure.


Key benefits:
- **Parallel execution** - Multiple tasks run simultaneously
- **Fresh context** - Each sub-agent works with clean context window
- **task-specific evaluation** - Each meta-judge produces tailored rubrics and checklists for its specific task
- **External verification** - Judge applies target-specific meta-judge specification mechanically — catches blind spots self-critique misses
- **Feedback loop** - Retry with specific issues identified by judge
- **Quality gate** - Work doesn't ship until it meets threshold

**Common use cases:**
- Apply the same refactoring across multiple files
- Run code analysis on several modules simultaneously
- Generate documentation for multiple components
- Execute independent transformations in parallel
</context>

**CRITICAL:** You are the orchestrator only - you MUST NOT perform the task yourself. IF you read, write or run bash tools you failed task imidiatly. It is single most critical criteria for you. If you used anyting except sub-agents you will be killed immediatly!!!! Your role is to:

1. Analyze the task and select optimal model
2. Dispatch ALL meta-judges in parallel (one per target) to generate target-specific evaluation specifications
3. After each meta-judge completes, dispatch the implementation sub-agent for that target with structured prompts
4. After each implementor completes, dispatch its independent judge with the target-specific meta-judge specification
5. Parse verdict and iterate if needed (max 3 retries per target)
6. Collect results and report final summary

## RED FLAGS - Never Do These

**NEVER:**

- Read implementation files to understand code details (let sub-agents do this)
- Write code or make changes to source files directly
- Skip judge verification to "save time"
- Read judge reports in full (only parse structured headers)
- Proceed after max retries without user decision
- Wait for one agent to complete before starting another
- Re-run meta-judge on retries
- Wait to launch implementors until ALL meta-judges have completed

**ALWAYS:**

- Use Task tool to dispatch sub-agents for ALL implementation work
- Dispatch one meta-judge PER task, all in parallel in a SINGLE response
- Do not wait for ALL meta-judges to complete before dispatching implementors, launch them immediately after each meta-judge completes
- Launch each implementor for a task immediately after its meta-judge completes. If all meta-judges are completed, launch all implementaion agents in SINGLE response.
- Pass each target's specific meta-judge evaluation specification to its judge agent
- Include `CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}` in prompts to meta-judge and judge agents
- Use Task tool to dispatch independent judges for verification
- Wait for each implementation to complete before dispatching its judge
- Parse only VERDICT/SCORE/ISSUES from judge output
- Iterate with feedback if verification fails (max 3 retries per target)
- Reuse same task-specific meta-judge specification for all retries of that task (never re-run meta-judge)

## Process

### Phase 1: Parse Input and Identify Targets

Extract targets from the command arguments:

```
Input patterns:
1. --files "src/a.ts,src/b.ts,src/c.ts"    --> File-based targets
2. --targets "UserService,OrderService"    --> Named targets
3. Infer from task description             --> Parse file paths from task
```

**Parsing rules:**
- If `--files` provided: Split by comma, validate each path exists
- If `--targets` provided: Split by comma, use as-is
- If neither: Attempt to extract file paths or target names from task description

### Phase 2: Task Analysis with Zero-shot CoT

Before dispatching, analyze the task systematically:

```
Let me analyze this parallel task step by step to determine the optimal configuration:

1. **Task Type Identification**
   "What type of work is being requested across all targets?"
   - Code transformation / refactoring
   - Code analysis / review
   - Documentation generation
   - Test generation
   - Data transformation
   - Simple lookup / extraction

2. **Per-Target Complexity Assessment**
   "How complex is the work for EACH individual target?"
   - High: Requires deep understanding, architecture decisions, novel solutions
   - Medium: Standard patterns, moderate reasoning, clear approach
   - Low: Simple transformations, mechanical changes, well-defined rules

3. **Per-Target Output Size**
   "How extensive is each target's expected output?"
   - Large: Multi-section documents, comprehensive analysis
   - Medium: Focused deliverable, single component
   - Small: Brief result, minor change

4. **Independence Check**
   "Are the targets truly independent?"
   - Yes: No shared state, no cross-dependencies, order doesn't matter
   - Partial: Some shared context needed, but can run in parallel
   - No: Dependencies exist --> Use sequential execution instead
```

#### Independence Validation (REQUIRED before parallel dispatch)

Verify tasks are truly independent before proceeding:

| Check | Question | If NO |
|-------|----------|-------|
| File Independence | Do targets share files? | Cannot parallelize - files conflict |
| State Independence | Do tasks modify shared state? | Cannot parallelize - race conditions |
| Order Independence | Does execution order matter? | Cannot parallelize - sequencing required |
| Output Independence | Does any target read another's output? | Cannot parallelize - data dependency |

**Independence Checklist:**
- [ ] No target reads output from another target
- [ ] No target modifies files another target reads
- [ ] Order of completion doesn't matter
- [ ] No shared mutable state
- [ ] No database transactions spanning targets

If ANY check fails: STOP and inform user why parallelization is unsafe. Recommend `/launch-sub-agent` for sequential execution.

### Phase 3: Model and Agent Selection

Select the optimal model and specialized agent based on task analysis. **Same configuration for all parallel agents** (ensures consistent quality):

#### 3.1 Model Selection

| Task Profile | Recommended Model | Rationale |
|--------------|-------------------|-----------|
| **Complex per-target** (architecture, design) | `opus` | Maximum reasoning capability per task |
| **Specialized domain** (code review, security) | `opus` | Domain expertise matters |
| **Medium complexity, large output** | `sonnet` | Good capability, cost-efficient for volume |
| **Simple transformations** (rename, format) | `haiku` | Fast, cheap, sufficient for mechanical tasks |
| **Default** (when uncertain) | `opus` | Optimize for quality over cost |

**Decision Tree:**

```
Is EACH target's task COMPLEX (architecture, novel problem, critical decision)?
|
+-- YES --> Use Opus for ALL agents
|
+-- NO --> Is task SIMPLE and MECHANICAL (rename, format, extract)?
           |
           +-- YES --> Use Haiku for ALL agents
           |
           +-- NO --> Is output LARGE but task not complex?
                      |
                      +-- YES --> Use Sonnet for ALL agents
                      |
                      +-- NO --> Use Opus for ALL agents (default)
```

#### 3.2 Specialized Agent Selection (Optional)

If the task matches a specialized domain, include the relevant agent prompt in ALL parallel agents. Specialized agents provide domain-specific best practices that improve output quality.

**Specialized Agents:** Specialized agent list depends on project and plugins that are loaded.

**Decision:** Use specialized agent when:
- Task clearly benefits from domain expertise
- Consistency across all parallel agents is important
- Task is NOT trivial (overhead not justified for simple tasks)

Skip specialized agent when:
- Task is simple/mechanical (Haiku-tier)
- No clear domain match exists
- General-purpose execution is sufficient

### Phase 3.5: Dispatch Meta-Judges (One Per Target, All in Parallel)

Before dispatching implementation agents, dispatch one meta-judge per target in parallel. Each meta-judge receives task-specific context so it produces a tailored evaluation specification for that specific task. Each meta-judge produces rubrics, checklists, and scoring criteria tailored to the specific task. Each target's specification is reused for all retries of that target ONLY.


Important: Follow context isolation principle - Pass each agent only context relevant to its specific target.

**Meta-judge prompt template (per target):**

```markdown
## Task

Generate an evaluation specification yaml for the following task applied to a specific target. You will produce rubrics, checklists, and scoring criteria that a judge agent will use to evaluate the implementation artifact for this specific target.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`


## Task from User Prompt
{Specific target for this meta-judge: file path, component name, etc. extracted from User Prompt}


## Context
{Any relevant codebase context, file paths, constraints}

## Artifact Type
{code | documentation | configuration | etc.}

## Instructions
Return only the final evaluation specification YAML in your response.
```

**Dispatch ALL meta-judges in a SINGLE response:**

```
Use Task tool (one per target, all in same message):

[Meta-judge for Target A]
  - description: "Meta-judge: {brief task summary} for {target_A}"
  - prompt: {meta-judge prompt with target_A context}
  - model: opus
  - subagent_type: "sadd:meta-judge"

[Meta-judge for Target B]
  - description: "Meta-judge: {brief task summary} for {target_B}"
  - prompt: {meta-judge prompt with target_B context}
  - model: opus
  - subagent_type: "sadd:meta-judge"

[Meta-judge for Target C]
  - description: "Meta-judge: {brief task summary} for {target_C}"
  - prompt: {meta-judge prompt with target_C context}
  - model: opus
  - subagent_type: "sadd:meta-judge"

[All meta-judges launched simultaneously - wait for ALL to complete before Phase 4]
```

**CRITICAL:** Do not wait for ALL meta-judges to complete before proceeding to Phase 4. Launch implementors immediately after each meta-judge completes. If all meta-judges are completed, launch all implementaion agents in SINGLE response.

### Phase 4: Construct Per-Target Prompts

Build identical prompt structure for each target, customized only with target-specific details:

#### 4.1 Zero-shot Chain-of-Thought Prefix (REQUIRED - MUST BE FIRST)

```markdown
## Reasoning Approach

Let's think step by step.

Before taking any action, think through the problem systematically:

1. "Let me first understand what is being asked for this specific target..."
   - What is the core objective?
   - What are the explicit requirements?
   - What constraints must I respect?

2. "Let me analyze this specific target..."
   - What is the current state?
   - What patterns or conventions exist?
   - What context is relevant?

3. "Let me plan my approach..."
   - What are the concrete steps?
   - What could go wrong?
   - Is there a simpler approach?

Work through each step explicitly before implementing.
```

#### 4.2 Task Body (Customized per target)

```markdown
<task>
{Task description from $ARGUMENTS}
</task>

<target>
{Specific target for this agent: file path, component name, etc.}
</target>

<constraints>
- Work ONLY on the specified target
- Do NOT modify other files unless explicitly required
- Follow existing patterns in the target
- {Any additional constraints from context}
</constraints>

<output>
{Expected deliverable location and format}

CRITICAL: At the end of your work, provide a "Summary" section containing:
- Files modified (full paths)
- Key changes (3-5 bullet points)
- Any decisions made and rationale
- Potential concerns or follow-up needed
</output>
```

#### 4.3 Self-Critique Suffix (REQUIRED - MUST BE LAST)

```markdown
## Self-Critique Verification (MANDATORY)

Before completing, verify your work for this target. Do not submit unverified changes.

### 1. Generate Verification Questions

Create questions specific to your task and target. There examples of questions:

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | Did I achieve the stated objective for this target? | Incomplete work = failed task |
| 2 | Are my changes consistent with patterns in this file/codebase? | Inconsistency creates technical debt |
| 3 | Did I introduce any regressions or break existing functionality? | Breaking changes are unacceptable |
| 4 | Are edge cases and error scenarios handled appropriately? | Edge cases cause production issues |
| 5 | Is my output clear, well-formatted, and ready for review? | Unclear output reduces value |

### 2. Answer Each Question with Evidence

For each question, provide specific evidence from your work:

[Q1] Objective Achievement:
- Required: [what was asked]
- Delivered: [what you did]
- Gap analysis: [any gaps]

[Q2] Pattern Consistency:
- Existing pattern: [observed pattern]
- My implementation: [how I followed it]
- Deviations: [any intentional deviations and why]

[Q3] Regression Check:
- Functions affected: [list]
- Tests that would catch issues: [if known]
- Confidence level: [HIGH/MEDIUM/LOW]

[Q4] Edge Cases:
- Edge case 1: [scenario] - [HANDLED/NOTED]
- Edge case 2: [scenario] - [HANDLED/NOTED]

[Q5] Output Quality:
- Well-organized: [YES/NO]
- Self-documenting: [YES/NO]
- Ready for PR: [YES/NO]

### 3. Fix Issues Before Submitting

If ANY verification reveals a gap:
1. **FIX** - Address the specific issue
2. **RE-VERIFY** - Confirm the fix resolves the issue
3. **DOCUMENT** - Note what was changed and why

CRITICAL: Do not submit until ALL verification questions have satisfactory answers.
```

### Phase 5: Parallel Implementation Dispatch and Judge Verification

After ALL meta-judges complete, launch all implementation sub-agents simultaneously, then verify each with an independent judge using the target-specific meta-judge evaluation specification.

#### 5.1 Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   Phase 3.5: Meta-Judge Batch (ALL in parallel)                         │
│                                                                         │
│   Target A              Target B              Target C                  │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│   │ Meta-Judge A  │      │ Meta-Judge B  │      │ Meta-Judge C  │         │
│   │ (Opus)        │      │ (Opus)        │      │ (Opus)        │         │
│   │ → Spec YAML A │      │ → Spec YAML B │      │ → Spec YAML C │         │
│   └──────┬───────┘      └──────┬───────┘      └──────┬───────┘          │
│          │                     │                     │                   │
│          ▼                     ▼                     ▼                   │
│   Phase 5: Implementation Batch  (after each meta-judge completes)      │
│                             │                                           │
│   Target A              Target B              Target C                  │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│   │ Implementer A │      │ Implementer B │      │ Implementer C │         │
│   │ (parallel)    │      │ (parallel)    │      │ (parallel)    │         │
│   └──────┬───────┘      └──────┬───────┘      └──────┬───────┘          │
│          │                     │                     │                   │
│          ▼                     ▼                     ▼                   │
│   Phase 5.2: Judge per target (after each implementor completes)        │
│                                                                         │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│   │  Judge A      │      │  Judge B      │      │  Judge C      │         │
│   │ +Spec YAML A  │      │ +Spec YAML B  │      │ +Spec YAML C  │         │
│   └──────┬───────┘      └──────┬───────┘      └──────┬───────┘          │
│          │                     │                     │                   │
│          ▼                     ▼                     ▼                   │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │ Parse Verdict (per target)                                │          │
│   │ ├─ PASS (≥4)? → Complete                                  │          │
│   │ ├─ Soft PASS (≥3 + low priority issues)? → Complete       │          │
│   │ └─ FAIL (<4)? → Retry (max 3 per target, reuse Spec YAML)│          │
│   └──────────────────────────────────────────────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**CRITICAL: Parallel Dispatch Pattern**

Launch ALL implementation agents in a SINGLE response. Do NOT wait for one agent to complete before starting another:

```markdown
## Dispatching 3 parallel tasks

[Task 1]
Use Task tool:
  description: "Parallel: simplify error handling in src/services/user.ts"
  prompt: [CoT prefix + task body for user.ts + critique suffix]
  model: sonnet

[Task 2]
Use Task tool:
  description: "Parallel: simplify error handling in src/services/order.ts"
  prompt: [CoT prefix + task body for order.ts + critique suffix]
  model: sonnet

[Task 3]
Use Task tool:
  description: "Parallel: simplify error handling in src/services/payment.ts"
  prompt: [CoT prefix + task body for payment.ts + critique suffix]
  model: sonnet

[All 3 tasks launched simultaneously - results collected when all complete]
```

**Parallelization Guidelines:**
- Launch ALL independent tasks in a single batch (same response)
- Do NOT wait for one task before starting another
- Do NOT make sequential Task tool calls
- Task tool handles parallelization automatically
- Results collected after all complete

**Context Isolation (IMPORTANT):**
- Pass only context relevant to each specific target
- Do NOT pass the full list of all targets to each agent
- Let sub-agents discover local patterns through file reading
- Each agent works in clean context without accumulated confusion

#### 5.2 Judge Verification Protocol

After each implementation agent completes, dispatch an **independent judge** for that target using that target's specific meta-judge evaluation specification.

CRITICAL: Provide to the judge the EXACT meta-judge evaluation specification YAML for that specific target, do not skip or add anything, do not modify it in any way, do not shorten or summarize any text in it! Each target's judge receives only that target's meta-judge YAML, not another target's specification or some combination of them.

**Judge prompt template:**

```markdown
You are evaluating an implementation artifact for target {target_name} against an evaluation specification produced by the meta judge.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt
{Original task description from user}

## Target
{Specific target: file path or component name}

## Evaluation Specification

```yaml
{meta-judge's evaluation specification YAML}
```

## Implementation Output
{Summary section from implementation agent}
{Paths to files modified}

## Instructions

Follow your full judge process as defined in your agent instructions!

## Output

CRITICAL: You must reply with this exact structured evaluation report format in YAML at the START of your response!
```

CRITICAL: NEVER provide score threshold, in any format, including `threshold_pass` or anything different. Judge MUST not know what threshold for score is, in order to not be biased!!!

**Dispatch judge for each target:**

```
Use Task tool:
  - description: "Judge: {target name}"
  - prompt: {judge verification prompt with exact meta-judge specification YAML}
  - model: opus
  - subagent_type: "sadd:judge"
```

#### 5.3 Parse Verdict and Iterate

Parse judge output for each target (DO NOT read full report):

```
Extract from judge reply:
- VERDICT: PASS or FAIL
- SCORE: X.X/5.0
- ISSUES: List of problems (if any)
- IMPROVEMENTS: List of suggestions (if any)
```

**Decision logic per target:**

```
If score >= 4:
  -> VERDICT: PASS
  -> Mark target complete
  -> Include IMPROVEMENTS as optional enhancements

IF score >= 3.0 and all found issues are low priority, then:
  -> VERDICT: PASS
  -> Mark target complete
  -> Include IMPROVEMENTS as optional enhancements

If score < 4:
  -> VERDICT: FAIL
  -> Check retry count for this target

  If retries < 3:
    -> Dispatch retry implementation agent with judge feedback
    -> Return to judge verification with same target-specific meta-judge specification

  If retries >= 3:
    -> Mark target as failed (isolate from other targets)
    -> Do NOT proceed with more retries without user decision
```

**IMPORTANT: Failures are isolated**
- One target failing does NOT affect other targets
- Other parallel tasks continue independently
- Only the failed target is retried

#### 5.4 Retry with Feedback (If Needed)

**Retry prompt template:**

```markdown
## Retry Required for Target: {target_name}

Your previous implementation did not pass judge verification.

## Original Task
{Original task description}

## Target
{Specific target}

## Judge Feedback
VERDICT: FAIL
SCORE: {score}/5.0
ISSUES:
{list of issues from judge}

## Your Previous Changes
{files modified in previous attempt}

## Instructions
Let's fix the identified issues step by step.

1. Review each issue the judge identified
2. For each issue, determine the root cause
3. Plan the fix for each issue
4. Implement ALL fixes
5. Verify your fixes address each issue
6. Provide updated Summary section

CRITICAL: Focus on fixing the specific issues identified. Do not rewrite everything.
```

### Phase 6: Collect and Summarize Results

After all agents complete (with retries as needed), aggregate results:

```markdown
## Parallel Execution Summary

### Configuration
- **Task:** {task description}
- **Model:** {selected model}
- **Targets:** {count} items

### Results

| Target | Model | Judge Score | Retries | Status | Summary |
|--------|-------|-------------|---------|--------|---------|
| {target_1} | {model} | {X.X}/5.0 | {0-3} | SUCCESS | {brief outcome} |
| {target_2} | {model} | {X.X}/5.0 | {0-3} | SUCCESS | {brief outcome} |
| {target_3} | {model} | {X.X}/5.0 | {3} | FAILED | {failure reason} |
| ... | ... | ... | ... | ... | ... |

### Overall Assessment
- **Completed:** {X}/{total}
- **Failed:** {Y}/{total}
- **Total Retries:** {sum of all retries}
- **Common patterns:** {any patterns across results}

### Verification Summary
{Aggregate judge verification results - any common issues?}

### Files Modified
- {list of all modified files}

### Failed Targets (If Any)
{For each failed target after max retries}
- **Target:** {name}
- **Final Score:** {X.X}/5.0
- **Persistent Issues:** {issues that weren't resolved}
- **Options:** Retry with guidance / Skip / Manual fix

### Next Steps
{If any failures, suggest remediation}
```

**Failure Handling:**
- Report failed tasks clearly with error details
- Successful tasks are NOT affected by failures
- Failed targets isolated after max retries
- Suggest options: provide guidance, skip, or manual fix

## Examples

### Example 1: Code Simplification Across Modules

**Input:**
```
/do-in-parallel "Simplify error handling to use early returns instead of nested if-else" \
  --files "src/services/user.ts,src/services/order.ts,src/services/payment.ts"
```

**Analysis:**
- Task type: Code transformation / refactoring
- Per-target complexity: Medium (pattern-based transformation)
- Output size: Medium (modified file)
- Independence: Yes (separate files, no cross-dependencies)

**Model Selection:** Sonnet (pattern-based, medium complexity)

**Execution:**

```
Phase 3.5: Dispatch Meta-Judges (3 in parallel, one per target)
  [All 3 meta-judges launched simultaneously]
  Meta-judge for user.ts (Opus)...
    → Generated target-specific evaluation specification YAML
    → 3 rubric dimensions, 5 checklist items tailored to user.ts
  Meta-judge for order.ts (Opus)...
    → Generated target-specific evaluation specification YAML
    → 3 rubric dimensions, 6 checklist items tailored to order.ts
  Meta-judge for payment.ts (Opus)...
    → Generated target-specific evaluation specification YAML
    → 3 rubric dimensions, 5 checklist items tailored to payment.ts

Phase 5: Parallel Implementation Dispatch (after all meta-judges complete)
  [All 3 implementation agents launched simultaneously]

  Target: user.ts
    Implementation (Sonnet)...
      -> Converted 4 nested if-else blocks to early returns
    Judge Verification (Opus, with user.ts meta-judge spec)...
      -> VERDICT: PASS, SCORE: 4.2/5.0
      -> IMPROVEMENTS: Consider extracting complex conditions

  Target: order.ts
    Implementation (Sonnet)...
      -> Converted 6 nested if-else blocks to early returns
    Judge Verification (Opus, with order.ts meta-judge spec)...
      -> VERDICT: PASS, SCORE: 4.0/5.0
      -> ISSUES: None

  Target: payment.ts
    Implementation (Sonnet)...
      -> Converted 3 nested if-else blocks
    Judge Verification (Opus, with payment.ts meta-judge spec)...
      -> VERDICT: FAIL, SCORE: 3.2/5.0
      -> ISSUES: Missing edge case for null amount
    Retry Implementation (Sonnet)...
      -> Added null check for payment amount
    Judge Verification (Opus, with same payment.ts meta-judge spec)...
      -> VERDICT: PASS, SCORE: 4.1/5.0
```

**Result:**
```markdown
## Parallel Execution Summary

### Configuration
- **Task:** Simplify error handling to use early returns
- **Model:** Sonnet
- **Targets:** 3 files

### Results

| Target | Model | Judge Score | Retries | Status | Summary |
|--------|-------|-------------|---------|--------|---------|
| src/services/user.ts | sonnet | 4.2/5.0 | 0 | SUCCESS | Converted 4 nested if-else blocks |
| src/services/order.ts | sonnet | 4.0/5.0 | 0 | SUCCESS | Converted 6 nested if-else blocks |
| src/services/payment.ts | sonnet | 4.1/5.0 | 1 | SUCCESS | Converted 3 blocks, added null check |

### Overall Assessment
- **Completed:** 3/3
- **Total Retries:** 1
- **Total Agents:** 11 (3 meta-judges + 3 implementations + 1 retry + 4 judges)
- **Common patterns:** All files followed consistent early return pattern
```

---

### Example 2: Documentation Generation

**Input:**
```
/do-in-parallel "Generate JSDoc documentation for all public methods" \
  --files "src/api/users.ts,src/api/products.ts,src/api/orders.ts,src/api/auth.ts"
```

**Analysis:**
- Task type: Documentation generation
- Per-target complexity: Low (mechanical documentation)
- Output size: Medium (inline comments)
- Independence: Yes

**Model Selection:** Haiku (mechanical, well-defined rules)

**Dispatch:** 4 meta-judges (parallel) → 4 implementors (parallel) → 4 judges

**Execution Summary:**

| Target | Model | Judge Score | Retries | Status |
|--------|-------|-------------|---------|--------|
| src/api/users.ts | haiku | 4.0/5.0 | 0 | SUCCESS |
| src/api/products.ts | haiku | 3.8/5.0 | 0 | SUCCESS |
| src/api/orders.ts | haiku | 4.2/5.0 | 0 | SUCCESS |
| src/api/auth.ts | haiku | 4.1/5.0 | 0 | SUCCESS |

Total Agents: 12 (4 meta-judges + 4 implementations + 4 judges)

---

### Example 3: Security Analysis

**Input:**
```
/do-in-parallel "Analyze for potential SQL injection vulnerabilities and suggest fixes" \
  --files "src/db/queries.ts,src/db/migrations.ts,src/api/search.ts"
```

**Analysis:**
- Task type: Security analysis
- Per-target complexity: High (security requires careful analysis)
- Output size: Medium (analysis report + suggestions)
- Independence: Yes

**Model Selection:** Opus (security-critical, requires deep analysis)

**Dispatch:** 3 meta-judges (parallel) → 3 implementors (parallel) → 3 judges + retries

**Execution Summary:**

| Target | Model | Judge Score | Retries | Status |
|--------|-------|-------------|---------|--------|
| src/db/queries.ts | opus | 4.5/5.0 | 0 | SUCCESS |
| src/db/migrations.ts | opus | 4.3/5.0 | 0 | SUCCESS |
| src/api/search.ts | opus | 4.0/5.0 | 1 | SUCCESS |

Total Agents: 11 (3 meta-judges + 3 implementations + 1 retry + 4 judges)

---

### Example 4: Test Generation with Partial Failure

**Input:**
```
/do-in-parallel "Generate unit tests achieving 80% coverage" \
  --targets "UserService,OrderService,PaymentService,NotificationService"
```

**Analysis:**
- Task type: Test generation
- Per-target complexity: Medium (follow testing patterns)
- Output size: Large (multiple test files)
- Independence: Yes (separate services)

**Model Selection:** Sonnet (pattern-based, extensive output)

**Dispatch:** 4 meta-judges (parallel) → 4 implementors (parallel) → judges + retries

**Execution:**

```
Phase 3.5: Meta-judge Batch (4 in parallel, one per target)
  [All 4 meta-judges launched simultaneously]
  Meta-judge for UserService (Opus) → target-specific evaluation spec YAML
  Meta-judge for OrderService (Opus) → target-specific evaluation spec YAML
  Meta-judge for PaymentService (Opus) → target-specific evaluation spec YAML
  Meta-judge for NotificationService (Opus) → target-specific evaluation spec YAML

Phase 5: Implementation Batch (4 in parallel, after all meta-judges complete)
  [All 4 implementors launched simultaneously]

Target: UserService
  -> Judge (Opus, with UserService meta-judge spec): PASS, 4.3/5.0

Target: OrderService
  -> Judge (Opus, with OrderService meta-judge spec): FAIL, 3.2/5.0 (missing edge cases)
  -> Retry: Judge (Opus, same OrderService spec): PASS, 4.0/5.0

Target: PaymentService
  -> Judge (Opus, with PaymentService meta-judge spec): FAIL, 2.8/5.0 (wrong mock patterns)
  -> Retry 1: Judge (Opus, same PaymentService spec): FAIL, 3.0/5.0 (still missing scenarios)
  -> Retry 2: Judge (Opus, same PaymentService spec): FAIL, 3.1/5.0 (coverage only 65%)
  -> Retry 3: Judge (Opus, same PaymentService spec): FAIL, 3.2/5.0 (coverage at 72%)
  -> MARKED FAILED after max retries

Target: NotificationService
  -> Judge (Opus, with NotificationService meta-judge spec): PASS, 4.1/5.0
```

**Result:**

| Target | Model | Judge Score | Retries | Status |
|--------|-------|-------------|---------|--------|
| UserService | sonnet | 4.3/5.0 | 0 | SUCCESS |
| OrderService | sonnet | 4.0/5.0 | 1 | SUCCESS |
| PaymentService | sonnet | 3.2/5.0 | 3 | FAILED |
| NotificationService | sonnet | 4.1/5.0 | 0 | SUCCESS |

**Overall:** 3/4 completed, 1 failed

**Escalation for PaymentService:**
```markdown
### Failed Target: PaymentService
- **Final Score:** 3.2/5.0
- **Persistent Issues:**
  - Test coverage at 72%, target is 80%
  - Complex async scenarios not fully covered
- **Options:**
  1. Provide guidance on specific async patterns to test
  2. Accept 72% coverage as sufficient
  3. Manual test writing for complex scenarios
```

---

### Example 5: Inferred Targets from Task

**Input:**
```
/do-in-parallel "Apply consistent logging format to src/handlers/user.ts, src/handlers/order.ts, and src/handlers/product.ts"
```

**Analysis:**
- Targets inferred: 3 files extracted from task description
- Task type: Code transformation
- Complexity: Low
- Independence: Yes

**Model Selection:** Haiku (simple, mechanical)

**Dispatch:** 3 meta-judges (parallel) → 3 implementors (parallel) → 3 judges

**Execution Summary:**

| Target | Model | Judge Score | Retries | Status |
|--------|-------|-------------|---------|--------|
| src/handlers/user.ts | haiku | 4.2/5.0 | 0 | SUCCESS |
| src/handlers/order.ts | haiku | 4.0/5.0 | 0 | SUCCESS |
| src/handlers/product.ts | haiku | 4.1/5.0 | 0 | SUCCESS |

Total Agents: 9 (3 meta-judges + 3 implementations + 3 judges)

## Best Practices

### Target Selection

- **Be specific:** List exact files when possible
- **Use globs carefully:** Review expanded list before confirming
- **Limit scope:** 10-15 targets max per batch for manageability
- **Group by similarity:** Similar targets benefit from consistent patterns

### Model Selection Guidelines

| Scenario | Model | Reason |
|----------|-------|--------|
| Security analysis | Opus | Critical reasoning required |
| Architecture decisions | Opus | Quality over speed |
| Simple refactoring | Haiku | Fast, sufficient |
| Documentation generation | Haiku | Mechanical task |
| Code review per file | Sonnet | Balanced capability |
| Test generation | Sonnet | Extensive but patterned |

### Meta-Judge + Judge Verification

- **One meta-judge per target** - Each target gets its own tailored evaluation specification, producing more relevant and precise judgments than a shared generic one
- **Batch meta-judges first** - Launch all meta-judges in parallel, then launch implementors
- **Reuse target-specific spec on retries** - Each target's evaluation specification stays constant across retries; only the implementation changes
- **Parse only headers from judge** - Don't read full reports to avoid context pollution
- **Include CLAUDE_PLUGIN_ROOT** - Both meta-judge and judge need the resolved plugin root path
- **Target-specific YAML** - Pass only the target's own meta-judge YAML to its judge, do not add any additional text or comments to it!

### Judge Selection

| Implementation Model | Judge Model | Rationale |
|---------------------|-------------|-----------|
| Opus | Opus | Critical work needs strong verification |
| Sonnet | Opus | Tailored evaluation requires strong reasoning |
| Haiku | Opus | Verify simple work with strong evaluation |

**Guideline:** Judges always use Opus for consistent, high-quality evaluation across all targets.

### Context Isolation

- **Minimal context:** Each sub-agent gets only what it needs
- **No cross-references:** Don't tell Agent A about Agent B's target
- **Let them discover:** Sub-agents read files to understand patterns
- **File system as truth:** Changes are coordinated through the filesystem

### Quality Assurance

- **Three-layer verification:** Self-critique (internal) + Target-specific meta-judge specification (structured) + Judge (external)
- **Self-critique first:** Implementation agents verify own work before submission
- **Target-specific meta-judge specification:** Each target gets tailored rubrics that account for its unique characteristics, producing more precise evaluation criteria
- **External judge second:** Independent judge applies target-specific meta-judge specification mechanically — catches blind spots self-critique misses
- **Iteration loop:** Retry with feedback until passing or max retries
- **Isolated failures:** One target failing doesn't affect others
- **Review the summary:** Check for failed or partial completions
- **Run tests after:** Parallel changes may have subtle interactions
- **Commit atomically:** All changes from one batch = one commit

#### Error Handling

| Failure Type | Description | Recovery Action |
|--------------|-------------|-----------------|
| **Recoverable** | Judge found issues, retry available | Retry with judge feedback (max 3 per target) |
| **Approach Failure** | The approach for this target is wrong | Escalate to user with options |
| **Foundation Issue** | Requirements unclear or impossible | Escalate to user for clarification |
| **Max Retries Exceeded** | Target failed after 3 retries | Mark failed, continue other targets, report at end |

**Critical Rules:**
- NEVER continue past max retries without user input
- NEVER try to "fix forward" without addressing judge issues
- NEVER skip judge verification
- STOP and report if context is missing (don't guess)
- ISOLATE failures - one target failing doesn't stop others
