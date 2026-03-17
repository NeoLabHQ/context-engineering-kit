---
name: do-and-judge
description: Execute a task with sub-agent implementation and LLM-as-a-judge verification with automatic retry loop
argument-hint: Task description (e.g., "Refactor the UserService class to use dependency injection")
---

# do-and-judge

<task>
Execute a single task by dispatching an implementation sub-agent, verifying with an independent judge, and iterating with feedback until passing or max retries exceeded.
</task>

<context>
This command implements a **single-task execution pattern** with **LLM-as-a-judge verification**. You (the orchestrator) dispatch a focused sub-agent to implement the task, then dispatch an independent judge to verify quality. If verification fails, you iterate with judge feedback until passing (score ≥4) or max retries (2) exceeded.

Key benefits:

- **Fresh context** - Implementation agent works with clean context window
- **External verification** - Judge catches blind spots self-critique misses
- **Feedback loop** - Retry with specific issues identified by judge
- **Quality gate** - Work doesn't ship until it meets threshold
</context>

CRITICAL: You are the orchestrator - you MUST NOT perform the task yourself. Your role is to:

1. Analyze the task and select optimal model
2. Dispatch implementation sub-agent with structured prompt
3. Dispatch judge sub-agent to verify
4. Parse verdict and iterate if needed (max 2 retries)
5. Report final results or escalate

## RED FLAGS - Never Do These

**NEVER:**

- Read implementation files to understand code details (let sub-agents do this)
- Write code or make changes to source files directly
- Skip judge verification to "save time"
- Read judge reports in full (only parse structured headers)
- Proceed after max retries without user decision

**ALWAYS:**

- Use Task tool to dispatch sub-agents for ALL implementation work
- Use Task tool to dispatch independent judges for verification
- Wait for implementation to complete before dispatching judge
- Parse only VERDICT/SCORE/ISSUES from judge output
- Iterate with feedback if verification fails

## Process

### Phase 1: Task Analysis and Model Selection

Analyze the task to select the optimal model:

```
Let me analyze this task to determine the optimal configuration:

1. **Complexity Assessment**
   - High: Architecture decisions, novel problem-solving, critical logic
   - Medium: Standard patterns, moderate refactoring, API updates
   - Low: Simple transformations, straightforward updates

2. **Risk Assessment**
   - High: Breaking changes, security-sensitive, data integrity
   - Medium: Internal changes, reversible modifications
   - Low: Non-critical utilities, isolated changes

3. **Scope Assessment**
   - Large: Multiple files, complex interactions
   - Medium: Single component, focused changes
   - Small: Minor modifications, single file
```

**Model Selection Guide:**

| Model | When to Use | Examples |
|-------|-------------|----------|
| `opus` | **Default/standard choice**. Safe for any task. Use when correctness matters, decisions are nuanced, or you're unsure. | Most implementation, code writing, business logic, architectural decisions |
| `sonnet` | Task is **not complex but high volume** - many similar steps, large context to process, repetitive work. | Bulk file updates, processing many similar items, large refactoring with clear patterns |
| `haiku` | **Trivial operations only**. Simple, mechanical tasks with no decision-making. | Directory creation, file deletion, simple config edits, file copying/moving |

**Specialized Agents:** Common agents from the `sdd` plugin include: `sdd:developer`, `sdd:researcher`, `sdd:software-architect`, `sdd:tech-lead`, `sdd:qa-engineer`. If the appropriate specialized agent is not available, fallback to a general agent without specialization.

### Phase 2: Dispatch Implementation Agent

Construct the implementation prompt with these mandatory components:

#### 2.1 Zero-shot Chain-of-Thought Prefix (REQUIRED - MUST BE FIRST)

```markdown
## Reasoning Approach

Before taking any action, think through this task systematically.

Let's approach this step by step:

1. "Let me understand what this task requires..."
   - What is the specific objective?
   - What constraints exist?
   - What is the expected outcome?

2. "Let me explore the relevant code..."
   - What files are involved?
   - What patterns exist in the codebase?
   - What dependencies need consideration?

3. "Let me plan my approach..."
   - What specific modifications are needed?
   - What order should I make them?
   - What could go wrong?

4. "Let me verify my approach before implementing..."
   - Does my plan achieve the objective?
   - Am I following existing patterns?
   - Is there a simpler way?

Work through each step explicitly before implementing.
```

#### 2.2 Task Body

```markdown
## Task
{Task description from user}

## Constraints
- Follow existing code patterns and conventions
- Make minimal changes to achieve the objective
- Do not introduce new dependencies without justification
- Ensure changes are testable

## Output
Provide your implementation along with a "Summary" section containing:
- Files modified (full paths)
- Key changes (3-5 bullet points)
- Any decisions made and rationale
- Potential concerns or follow-up needed
```

#### 2.3 Self-Critique Suffix (REQUIRED - MUST BE LAST)

```markdown
## Self-Critique Verification (MANDATORY)

Before completing, verify your work. Do not submit unverified changes.

### Verification Questions

| # | Question | Evidence Required |
|---|----------|-------------------|
| 1 | Does my solution address ALL requirements? | [Specific evidence] |
| 2 | Did I follow existing code patterns? | [Pattern examples] |
| 3 | Are there any edge cases I missed? | [Edge case analysis] |
| 4 | Is my solution the simplest approach? | [Alternatives considered] |
| 5 | Would this pass code review? | [Quality check] |

### Answer Each Question with Evidence

Examine your solution and provide specific evidence for each question.

### Revise If Needed

If ANY verification question reveals a gap:
1. **FIX** - Address the specific gap identified
2. **RE-VERIFY** - Confirm the fix resolves the issue
3. **UPDATE** - Update the Summary section

CRITICAL: Do not submit until ALL verification questions have satisfactory answers.
```

#### 2.4 Dispatch

```
Use Task tool:
  - description: "Implement: {brief task summary}"
  - prompt: {constructed prompt with CoT + task + self-critique}
  - model: {selected model}
  - subagent_type: "sdd:developer"
```

### Phase 3: Dispatch Judge Agent

After implementation completes, dispatch an independent judge.

**Judge prompt template:**

```markdown
You are verifying completion of a task.

## Task Requirements
{Original task description from user}

## Implementation Output
{Summary section from implementation agent}
{Paths to files modified}

## Evaluation Criteria
1. **Correctness** (35%) - Does the implementation meet requirements?
2. **Quality** (25%) - Is the code well-structured and maintainable?
3. **Completeness** (25%) - Are all required elements present?
4. **Patterns** (15%) - Does it follow existing codebase conventions?

## Output
CRITICAL: You must reply with this exact structured header format:

---
VERDICT: [PASS/FAIL]
SCORE: [X.X]/5.0
ISSUES:
  - {issue_1 or "None"}
  - {issue_2 or "None"}
IMPROVEMENTS:
  - {improvement_1 or "None"}
---

[Detailed evaluation follows]

## Instructions
1. Read the implementation files
2. Verify each requirement was met with specific evidence
3. Identify any gaps, issues, or missing elements
4. Score each criterion and calculate weighted total

CRITICAL: List specific issues that must be fixed for retry.

## Scoring Scale

**DEFAULT SCORE IS 2. You must justify ANY deviation upward.**

| Score | Meaning | Evidence Required | Your Attitude |
|-------|---------|-------------------|---------------|
| 1 | Unacceptable | Clear failures, missing requirements | Easy call |
| 2 | Below Average | Multiple issues, partially meets requirements | Common result |
| 3 | Adequate | Meets basic requirements, minor issues | Need proof that it meets basic requirements |
| 4 | Good | Meets ALL requirements, very few minor issues | Prove it deserves this |
| 5 | Excellent | Exceeds requirements, genuinely exemplary | **Extremely rare** - requires exceptional evidence |

### Score Distribution Reality Check

- **Score 5**: Should be given in <5% of evaluations. If you're giving more 5s, you're too lenient.
- **Score 4**: Reserved for genuinely solid work. Not "pretty good" - actually good.
- **Score 3**: This is where refined work lands. Not average.
- **Score 2**: Common for first attempts. Don't be afraid to use it.
- **Score 1**: Reserved for fundamental failures. But don't avoid it when deserved.

```

**Dispatch:**

```
Use Task tool:
  - description: "Judge: {brief task summary}"
  - prompt: {judge verification prompt}
  - model: {same as implementation or sonnet}
  - subagent_type: "general-purpose"
```

### Phase 4: Parse Verdict and Iterate

Parse judge output (DO NOT read full report):

```
Extract from judge reply:
- VERDICT: PASS or FAIL
- SCORE: X.X/5.0
- ISSUES: List of problems (if any)
- IMPROVEMENTS: List of suggestions (if any)
```

**Decision logic:**

```
If score ≥4:
  → VERDICT: PASS
  → Report success with summary
  → Include IMPROVEMENTS as optional enhancements

If score <4:
  → VERDICT: FAIL
  → Check retry count

  If retries < 2:
    → Dispatch retry implementation agent with judge feedback
    → Return to Phase 3 (judge verification)

  If retries ≥ 2:
    → Escalate to user (see Error Handling)
    → Do NOT proceed without user decision
```

### Phase 5: Retry with Feedback (If Needed)

**Retry prompt template:**

```markdown
## Retry Required

Your previous implementation did not pass judge verification.

## Original Task
{Original task description}

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

### Phase 6: Final Report

After task passes verification:

```markdown
## Execution Summary

**Task:** {original task description}
**Result:** ✅ PASS

### Verification
| Attempt | Score | Status |
|---------|-------|--------|
| 1 | {X.X}/5.0 | {PASS/FAIL} |
| 2 | {X.X}/5.0 | {PASS/FAIL} | (if retry occurred)

### Files Modified
- {file1}: {what changed}
- {file2}: {what changed}

### Key Changes
- {change 1}
- {change 2}

### Suggested Improvements (Optional)
{IMPROVEMENTS from judge, if any}
```

## Error Handling

### If Max Retries Exceeded

When task fails verification twice:

1. **STOP** - Do not proceed
2. **Report** - Provide failure analysis:
   - Original task requirements
   - All judge verdicts and scores
   - Persistent issues across retries
3. **Escalate** - Present options to user:
   - Provide additional context/guidance for retry
   - Modify task requirements
   - Abort task
4. **Wait** - Do NOT proceed without user decision

**Escalation Report Format:**

```markdown
## Task Failed Verification (Max Retries Exceeded)

### Task Requirements
{original task description}

### Verification History
| Attempt | Score | Key Issues |
|---------|-------|------------|
| 1 | {X.X}/5.0 | {issues} |
| 2 | {X.X}/5.0 | {issues} |
| 3 | {X.X}/5.0 | {issues} |

### Persistent Issues
{Issues that appeared in multiple attempts}

### Options
1. **Provide guidance** - Give additional context for another retry
2. **Modify requirements** - Simplify or clarify task
3. **Abort** - Stop execution

Awaiting your decision...
```

## Examples

### Example 1: Simple Refactoring (Pass on First Try)

**Input:**

```
/do-and-judge Extract the validation logic from UserController into a separate UserValidator class
```

**Execution:**

```
Phase 1: Task Analysis
  → Model: Opus

Phase 2: Dispatch Implementation
  Implementation (Opus + sdd:developer)...
    → Created UserValidator.ts
    → Updated UserController to use validator
    → Summary: 2 files modified, validation extracted

Phase 3: Dispatch Judge
  Judge Verification (Opus)...
    → VERDICT: PASS, SCORE: 4.2/5.0
    → ISSUES: None
    → IMPROVEMENTS: Add input validation for edge cases

Phase 6: Final Report
  ✅ PASS on attempt 1
  Files: UserValidator.ts (new), UserController.ts (modified)
```

### Example 2: Complex Task (Pass After Retry)

**Input:**

```
/do-and-judge Implement rate limiting middleware with configurable limits per endpoint
```

**Execution:**

```
Phase 1: Task Analysis
  - Complexity: High (new feature, multiple concerns)
  - Risk: High (affects all endpoints)
  - Scope: Medium (single middleware)
  → Model: opus

Phase 2: Dispatch Implementation (Attempt 1)
  Implementation (Opus + sdd:developer)...
    → Created RateLimiter middleware
    → Added configuration schema

Phase 3: Dispatch Judge
  Judge Verification (Opus)...
    → VERDICT: FAIL, SCORE: 3.1/5.0
    → ISSUES:
      - Missing per-endpoint configuration
      - No Redis support for distributed deployments
    → IMPROVEMENTS: Add monitoring hooks

Phase 5: Retry with Feedback
  Implementation (Opus + sdd:developer)...
    → Added endpoint-specific limits
    → Added Redis adapter option

Phase 3: Dispatch Judge (Attempt 2)
  Judge Verification (Opus)...
    → VERDICT: PASS, SCORE: 4.4/5.0
    → IMPROVEMENTS: Add metrics export

Phase 6: Final Report
  ✅ PASS on attempt 2
  Files: RateLimiter.ts, config/rateLimits.ts, adapters/RedisAdapter.ts
```

### Example 3: Task Requiring Escalation

**Input:**

```
/do-and-judge Migrate the database schema to support multi-tenancy
```

**Execution:**

```
Phase 1: Task Analysis
  - Complexity: High
  - Risk: High (database schema change)
  → Model: opus

Attempt 1: FAIL (2.8/5.0) - Missing tenant isolation in queries
Attempt 2: FAIL (3.2/5.0) - Incomplete migration script
Attempt 3: FAIL (3.3/5.0) - Edge cases in existing data migration

ESCALATION:
  Persistent issue: Existing data migration requires business decisions
  about how to handle orphaned records.

  Options presented to user:
  1. Provide guidance on orphan handling
  2. Simplify to new tenants only
  3. Abort

User chose: Option 1 - "Delete orphaned records older than 1 year"

Attempt 4 (with guidance): PASS (4.1/5.0)
```

## Best Practices

### Model Selection

- **When in doubt, use Opus** - Quality matters more than cost for verified work
- **Match complexity** - Don't use Opus for simple transformations
- **Consider risk** - Higher risk = stronger model

### Judge Verification

- **Never skip** - The judge catches what self-critique misses
- **Parse only headers** - Don't read full reports to avoid context pollution
- **Trust the threshold** - 4/5.0 is the quality gate

### Iteration

- **Focus fixes** - Don't rewrite everything, fix specific issues
- **Pass feedback verbatim** - Let the implementation agent see exact issues
- **Escalate appropriately** - Don't loop forever on fundamental problems

### Context Management

- **Keep it clean** - You orchestrate, sub-agents implement
- **Summarize, don't copy** - Pass summaries, not full file contents
- **Trust sub-agents** - They can read files themselves
