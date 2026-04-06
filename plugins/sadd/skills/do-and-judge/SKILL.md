---
name: do-and-judge
description: Execute a task with sub-agent implementation and LLM-as-a-judge verification with automatic retry loop
argument-hint: Task description (e.g., "Refactor the UserService class to use dependency injection")
---

# do-and-judge

## Task
Execute a single task by dispatching an implementation sub-agent, verifying with an independent judge, and iterating with feedback until passing or max retries exceeded.

## Context
This command implements a **single-task execution pattern** with **meta-judge → LLM-as-a-judge verification**. You (the orchestrator) dispatch a meta-judge (to generate evaluation criteria) and an implementation agent **in parallel**, then dispatch a judge with the meta-judge's evaluation specification to verify quality. If verification fails, you launch new implementation agent with judge feedback and iterate until passing (score ≥4) or max retries (2) exceeded.

Key benefits:

- **Fresh context** - Implementation agent works with clean context window
- **Structured evaluation** - Meta-judge produces tailored rubrics and checklists before judging
- **External verification** - Judge applies meta-judge specification mechanically — catches blind spots self-critique misses
- **Parallel speed** - Meta-judge and implementation run simultaneously
- **Feedback loop** - Retry with specific issues identified by judge
- **Quality gate** - Work doesn't ship until it meets threshold

**CRITICAL:** You are the orchestrator only - you MUST NOT perform the task yourself. IF you read, write or run bash tools you failed task imidiatly. It is single most critical criteria for you. If you used anyting except sub-agents you will be killed immediatly!!!! Your role is to:

1. Analyze the task and select optimal model
2. Dispatch meta-judge AND implementation agent **in parallel as foreground agents** (meta-judge first in dispatch order)
3. Dispatch judge agent with meta-judge's evaluation specification
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
- Dispatch meta-judge and implementation agent in parallel (meta-judge FIRST in dispatch order)
- Wait for BOTH meta-judge and implementation to complete before dispatching judge
- Pass meta-judge evaluation specification to the judge agent
- Include `CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`` in prompts to meta-judge and judge agents
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

**Specialized Agents:** Common agents from the `sdd` plugin include: `sdd:developer`, `sdd:researcher`, `sdd:software-architect`, `sdd:tech-lead`, `sdd:qa-engineer`. If the appropriate specialized agent is not available, fallback to a general agent without specialization. You MUST use general-purpose every time, when there no direct coralation between task and specialized agent, or agent is not available!

### Phase 2: Dispatch Meta-Judge and Implementation Agent (IN PARALLEL)

**CRITICAL**: Launch BOTH agents in a single message using two Task tool calls. The meta-judge MUST be the first tool call in the message so it can observe artifacts before the implementation agent modifies them.

Both agents run as **foreground** agents. Wait for both to complete before proceeding to Phase 3.

#### 2.1 Meta-Judge Prompt

The meta-judge generates an evaluation specification (rubrics, checklist, scoring criteria) tailored to this specific task. It will return to you the evaluation specification YAML.

```markdown
## Task

Generate an evaluation specification yaml for the following task. You will produce rubrics, checklists, and scoring criteria that a judge agent will use to evaluate the implementation artifact.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt
{Original task description from user}

## Context
{Any relevant codebase context, file paths, constraints}

## Artifact Type
{code | documentation | configuration | etc.}

## Instructions
Return only the final evaluation specification YAML in your response.
```

```
Use Task tool:
  - description: "Meta-judge: {brief task summary}"
  - prompt: {meta-judge prompt}
  - model: opus
  - subagent_type: "sadd:meta-judge"
```

#### 2.2 Implementation Agent Prompt

Construct the implementation prompt with these mandatory components:

**Zero-shot Chain-of-Thought Prefix (REQUIRED - MUST BE FIRST)**

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

**Task Body**

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

**Self-Critique Suffix (REQUIRED - MUST BE LAST)**

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

**Dispatch**

Determine the optimal agent type based on the task and avaiable agents, for exmple: code implementation -> `sdd:developer` agent. If you not sure, better use `general-purpose` agent, than dispatch incorrect agent type.

```
Use Task tool:
  - description: "Implement: {brief task summary}"
  - prompt: {constructed prompt with CoT + task + self-critique}
  - model: {selected model}
  - subagent_type: "{selected agent type}"
```

#### 2.3 Parallel Dispatch Example

Send BOTH Task tool calls in a single message. Meta-judge first, implementation second:

```
Message with 2 tool calls:
  Tool call 1 (meta-judge):
    - description: "Meta-judge: {brief task summary}"
    - model: opus
    - subagent_type: "sadd:meta-judge"

  Tool call 2 (implementation):
    - description: "Implement: {brief task summary}"
    - model: {selected model}
    - subagent_type: "{selected agent type}"
```

Wait for BOTH to return before proceeding to Phase 3.

### Phase 3: Dispatch Judge Agent

After BOTH meta-judge and implementation complete, dispatch the judge agent.

CRITICAL: Provide to the judge EXACT meta-judge's evaluation specification YAML, do not skip or add anything, do not modify it in any way, do not shorten or sumaraize any text in it!

**Extract from meta-judge output:**
- The final evaluation specification YAML

**Extract from implementation output:**
- Summary section (files modified, key changes)
- Paths to files modified

#### 3.1 Analyze the Pre-existing Changes Section

Before dispatching the judge, assess whether there are pre-existing changes in the codebase that the judge needs to be aware of. The "Pre-existing Changes" section prevents the judge from confusing prior modifications with the current implementation agent's work.

**When to include:**

- Previous do-and-judge task runs completed earlier in the same session
- User's manual modifications made before invoking the skill (visible from conversation context or in git)
- Changes from other tools or agents that ran before this task

**When to omit:**

- This is the first task with no known prior changes — omit the section entirely
- On retries within the SAME task, do NOT include the implementation agent's own previous attempt as "pre-existing changes" — those are part of the current task's iteration cycle

**Content guidelines:**

- Use a high-level summary: task description, list of affected files/modules, general nature of changes (created, modified, deleted)
- Do NOT include code blocks, diffs, or line-level details — keep it concise
- Label the source clearly: "Previous Task: {description}", "User modifications (before current task)", etc.
- If multiple sources of pre-existing changes exist, use separate subsections for each

CRITICAL: avoid reading full codebase or git history, just use high-level git diff/status to determine which files were changed, or use conversation context to determine if there are any pre-existing changes.

### 3.2 Launch Judge with prompt and specification YAML

**Judge prompt template:**

```markdown
You are evaluating an implementation artifact against an evaluation specification produced by the meta judge.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt
{Original task description from user}

{IF pre-existing changes are known, include the following section — otherwise omit entirely}

## Pre-existing Changes (Context Only)

The following changes were made BEFORE the current implementation agent started working. They are NOT part of the current task's output. Focus your evaluation on the current task's changes. Only verify pre-existing changed files/logic if they directly relate to the current task requirements.

### {Source of changes: e.g., "Previous Task: {task description}" or "User modifications (before current task)"}
{High-level summary: what was done, which files/modules were created or modified}

{END conditional section}

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

CRITICAL: NEVER provide score threshold, in any format, including `threshold_pass` or anything different. Judge MUST not know what thershold for score is, in order to not be biased!!!

**Dispatch:**

```
Use Task tool:
  - description: "Judge: {brief task summary}"
  - prompt: {judge verification prompt with exact meta-judge specification YAML, and Pre-existing Changes section if applicable}
  - model: opus
  - subagent_type: "sadd:judge"
```
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

IF score ≥ 3.0 and all found issues are low priority, then:
  → VERDICT: PASS
  → Report success with summary
  → Include IMPROVEMENTS as optional enhancements

If score <4:
  → VERDICT: FAIL
  → Check retry count

  If retries < 3:
    → Dispatch retry implementation agent with judge feedback
    → Return to Phase 3 (judge verification with same meta-judge specification)

  If retries ≥ 3:
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

### Example 1: Documentation Update (Pass on First Try)

**Input:**

```
/do-and-judge Rewrite the API authentication section in docs/api-reference.md to cover the new OAuth2 flow
```

**Execution:**

```
Phase 1: Task Analysis
  - Complexity: Medium (rewriting existing documentation with new technical flow)
  - Risk: Low (documentation only, no code changes)
  - Scope: Small (single file, focused section)
  → Model: opus
  → Agent type: general-purpose
    Reasoning: This is a documentation task — writing and restructuring
    prose, not implementing code. The sdd:developer agent is optimized
    for code implementation patterns, not technical writing. A
    general-purpose agent handles documentation tasks more effectively
    because it applies broader writing and reasoning skills without
    code-centric constraints.

Phase 2: Parallel Dispatch (single message, 2 tool calls)
  Tool call 1 — Meta-judge (Opus)...
    Meta-judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ ## Task
    │ Generate an evaluation specification yaml for the
    │ following task. You will produce rubrics, checklists,
    │ and scoring criteria that a judge agent will use to
    │ evaluate the implementation artifact.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## User Prompt
    │ Rewrite the API authentication section in
    │ docs/api-reference.md to cover the new OAuth2 flow
    │
    │ ## Context
    │ Existing docs/api-reference.md contains an outdated
    │ "Authentication" section describing API key auth.
    │ The codebase recently migrated to OAuth2 with PKCE.
    │ Related source: src/auth/oauth2.ts, src/auth/config.ts.
    │
    │ ## Artifact Type
    │ documentation
    │
    │ ## Instructions
    │ Return only the final evaluation specification YAML
    │ in your response.
    └─────────────────────────────────────────────────────────
    → Generated evaluation specification YAML
    → 3 rubric dimensions (accuracy, completeness, clarity)
    → 5 checklist items

  Tool call 2 — Implementation (general-purpose + Opus)...
    Implementation prompt sent (abbreviated):
    ┌─────────────────────────────────────────────────────────
    │ ## Reasoning Approach
    │ Before taking any action, think through this task
    │ systematically.
    │ [... step-by-step reasoning template ...]
    │
    │ ## Task
    │ Rewrite the API authentication section in
    │ docs/api-reference.md to cover the new OAuth2 flow.
    │ Replace the outdated API key auth documentation with
    │ OAuth2 + PKCE flow documentation including token
    │ endpoints, scopes, refresh token handling, and
    │ example requests.
    │
    │ ## Constraints
    │ - Follow existing documentation patterns and conventions
    │ - Make minimal changes to achieve the objective
    │ - Do not introduce new dependencies without justification
    │ - Ensure changes are testable
    │
    │ ## Output
    │ Provide your implementation along with a "Summary"
    │ section containing:
    │ - Files modified (full paths)
    │ - Key changes (3-5 bullet points)
    │ - Any decisions made and rationale
    │ - Potential concerns or follow-up needed
    │
    │ ## Self-Critique Verification (MANDATORY)
    │ [... verification questions and revision process ...]
    └─────────────────────────────────────────────────────────
    → Rewrote Authentication section in docs/api-reference.md
    → Added OAuth2 flow diagram, token endpoints, scopes table
    → Added code examples for authorization and token refresh
    → Summary: 1 file modified, authentication section rewritten

Phase 3: Dispatch Judge (with meta-judge specification)
  NOTE: No pre-existing changes — first task on a clean codebase.
  The "Pre-existing Changes" section is OMITTED from the judge prompt.

  Judge prompt sent:
  ┌─────────────────────────────────────────────────────────
  │ You are evaluating an implementation artifact against
  │ an evaluation specification produced by the meta judge.
  │
  │ CLAUDE_PLUGIN_ROOT=...
  │
  │ ## User Prompt
  │ Rewrite the API authentication section in
  │ docs/api-reference.md to cover the new OAuth2 flow
  │
  │ ## Evaluation Specification
  │ ```yaml
  │ {meta-judge's evaluation specification YAML}
  │ ```
  │
  │ ## Implementation Output
  │ Files: docs/api-reference.md (modified)
  │ Key changes: Replaced API key auth section with OAuth2
  │ + PKCE flow, added token endpoints, scopes table,
  │ and code examples for authorization and refresh...
  │
  │ ## Instructions
  │ Follow your full judge process...
  └─────────────────────────────────────────────────────────

  Judge (sadd:judge + Opus)...
    → VERDICT: PASS, SCORE: 4.2/5.0
    → ISSUES: None
    → IMPROVEMENTS: Add error response examples for expired tokens

Phase 4: Parse Verdict
  → Score 4.2 ≥ 4.0 threshold → PASS
  → No retry needed (Phase 5 skipped)

Phase 6: Final Report
  ✅ PASS on attempt 1
  Files: docs/api-reference.md (modified)
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

Phase 2: Parallel Dispatch (Attempt 1)
  Tool call 1 — Meta-judge (Opus)...
    → Generated evaluation specification YAML
    → 4 rubric dimensions, 8 checklist items
  Tool call 2 — Implementation (sdd:developer + Opus)...
    → Created RateLimiter middleware
    → Added configuration schema

Phase 3: Dispatch Judge (with meta-judge specification)
  Judge (sadd:judge + Opus)...
    → VERDICT: FAIL, SCORE: 3.1/5.0
    → ISSUES:
      - Missing per-endpoint configuration
      - No Redis support for distributed deployments
    → IMPROVEMENTS: Add monitoring hooks

Phase 5: Retry with Feedback
  Implementation (sadd:meta-judge + Opus)...
    → Added endpoint-specific limits
    → Added Redis adapter option

Phase 3: Dispatch Judge (Attempt 2, same meta-judge specification)
  Judge (sadd:judge + Opus)...
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

Phase 2: Parallel Dispatch
  Meta-judge → evaluation specification YAML
  Implementation → initial migration scaffolding

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

### Example 4: Sequential do-and-judge Runs (Pre-existing Changes from Previous Task)

**Input (first run):**

```
/do-and-judge add basic authentication module
```

**Execution (first run):**

```
Phase 1: Task Analysis
  - Complexity: High (new feature, security-sensitive)
  - Risk: High (authentication is critical)
  - Scope: Medium (new module)
  → Model: opus
  - Pre-existing Changes: None

Phase 2: Parallel Dispatch (Attempt 1)
  Tool call 1 — Meta-judge (Opus)...
    Meta-judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ ## Task
    │ Generate an evaluation specification yaml for the
    │ following task. You will produce rubrics, checklists,
    │ and scoring criteria that a judge agent will use to
    │ evaluate the implementation artifact.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## User Prompt
    │ Add basic authentication module
    │
    │ ## Context
    │ Express.js backend, src/auth/ directory does not exist
    │ yet. Existing middleware pattern in src/middleware/.
    │
    │ ## Artifact Type
    │ code
    │
    │ ## Instructions
    │ Return only the final evaluation specification YAML
    │ in your response.
    └─────────────────────────────────────────────────────────
    → Generated evaluation specification YAML
    → 4 rubric dimensions, 7 checklist items

  Tool call 2 — Implementation (sdd:developer + Opus)...
    Implementation prompt sent (abbreviated):
    ┌─────────────────────────────────────────────────────────
    │ ## Reasoning Approach
    │ Before taking any action, think through this task
    │ systematically.
    │ [... step-by-step reasoning template ...]
    │
    │ ## Task
    │ Add basic authentication module to the Express.js
    │ backend. Create login, logout, and register endpoints
    │ with proper middleware for route protection.
    │
    │ ## Constraints
    │ - Follow existing code patterns and conventions
    │ - Make minimal changes to achieve the objective
    │ - Do not introduce new dependencies without
    │   justification
    │ - Ensure changes are testable
    │
    │ ## Output
    │ Provide your implementation along with a "Summary"
    │ section containing:
    │ - Files modified (full paths)
    │ - Key changes (3-5 bullet points)
    │ - Any decisions made and rationale
    │ - Potential concerns or follow-up needed
    │
    │ ## Self-Critique Verification (MANDATORY)
    │ [... verification questions and revision process ...]
    └─────────────────────────────────────────────────────────
    → Created src/auth/AuthService.ts
    → Created src/auth/AuthMiddleware.ts
    → Created src/auth/auth.routes.ts
    → Modified src/app.ts
    → Summary: 4 files changed, auth module added

Phase 3: Dispatch Judge (with meta-judge specification)
  NOTE: No pre-existing changes — this is the first task on a clean codebase.
  The "Pre-existing Changes" section is OMITTED from the judge prompt.

  Judge prompt sent:
  ┌─────────────────────────────────────────────────────────
  │ You are evaluating an implementation artifact against
  │ an evaluation specification produced by the meta judge.
  │
  │ CLAUDE_PLUGIN_ROOT=...
  │
  │ ## User Prompt
  │ Add basic authentication module
  │
  │ ## Evaluation Specification
  │ ```yaml
  │ {meta-judge's evaluation specification YAML}
  │ ```
  │
  │ ## Implementation Output
  │ Files: src/auth/AuthService.ts (new), ...
  │ Key changes: Added login/logout/register endpoints...
  │
  │ ## Instructions
  │ Follow your full judge process...
  └─────────────────────────────────────────────────────────

  Judge (sadd:judge + Opus)...
    → VERDICT: FAIL, SCORE: 3.0/5.0
    → ISSUES:
      - Missing password hashing (plain-text storage)
      - No unit tests for AuthService
    → IMPROVEMENTS: Add rate limiting on login endpoint

Phase 5: Retry with Feedback (Attempt 2)
  Implementation (sdd:developer + Opus)...
    → Added bcrypt password hashing
    → Created tests/auth/AuthService.test.ts
    → Summary: 2 files modified, 1 file created

Phase 3: Dispatch Judge (Attempt 2, same meta-judge specification)
  NOTE: This is a retry within the SAME task — do NOT include the
  implementation agent's previous attempt as "pre-existing changes".
  The "Pre-existing Changes" section is still OMITTED.

  Judge (sadd:judge + Opus)...
    → VERDICT: PASS, SCORE: 4.3/5.0
    → IMPROVEMENTS: Add integration tests

Phase 6: Final Report
  ✅ PASS on attempt 2
  Files: AuthService.ts, AuthMiddleware.ts, auth.routes.ts,
         AuthService.test.ts, app.ts
```

**Input (second run, same session):**

```
/do-and-judge refactor auth module to use dependency injection
```

**Execution (second run):**

```
Phase 1: Task Analysis
  - Complexity: Medium (refactoring existing code)
  - Risk: Medium (modifying working auth module)
  - Scope: Medium (single module refactor)
  → Model: opus
  - Pre-existing Changes: Auth module created in previous task

Phase 2: Parallel Dispatch
  Tool call 1 — Meta-judge (Opus)...
    Meta-judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ ## Task
    │ Generate an evaluation specification yaml for the
    │ following task. You will produce rubrics, checklists,
    │ and scoring criteria that a judge agent will use to
    │ evaluate the implementation artifact.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## User Prompt
    │ Refactor auth module to use dependency injection
    │
    │ ## Context
    │ Existing auth module at src/auth/ with AuthService,
    │ AuthMiddleware, auth.routes. Tests in tests/auth/.
    │
    │ ## Artifact Type
    │ code
    │
    │ ## Instructions
    │ Return only the final evaluation specification YAML
    │ in your response.
    └─────────────────────────────────────────────────────────
    → Generated evaluation specification YAML
    → 3 rubric dimensions, 5 checklist items

  Tool call 2 — Implementation (sdd:developer + Opus)...
    Implementation prompt sent (abbreviated):
    ┌─────────────────────────────────────────────────────────
    │ ## Reasoning Approach
    │ Before taking any action, think through this task
    │ systematically.
    │ [... step-by-step reasoning template ...]
    │
    │ ## Task
    │ Refactor the auth module to use dependency injection.
    │ AuthService should accept its dependencies via
    │ constructor instead of importing them directly.
    │
    │ ## Constraints
    │ - Follow existing code patterns and conventions
    │ - Make minimal changes to achieve the objective
    │ - Do not introduce new dependencies without
    │   justification
    │ - Ensure changes are testable
    │
    │ ## Output
    │ Provide your implementation along with a "Summary"
    │ section containing:
    │ - Files modified (full paths)
    │ - Key changes (3-5 bullet points)
    │ - Any decisions made and rationale
    │ - Potential concerns or follow-up needed
    │
    │ ## Self-Critique Verification (MANDATORY)
    │ [... verification questions and revision process ...]
    └─────────────────────────────────────────────────────────
    → Refactored AuthService to accept dependencies via constructor
    → Created src/auth/AuthServiceFactory.ts
    → Updated tests to use mocked dependencies
    → Summary: 4 files modified, 1 file created

Phase 3: Dispatch Judge (with meta-judge specification)
  NOTE: Pre-existing changes detected — the previous do-and-judge run
  created the auth module. Include "Pre-existing Changes" section so the
  judge does not confuse prior work with the current refactoring task.

  Judge prompt sent:
  ┌─────────────────────────────────────────────────────────
  │ You are evaluating an implementation artifact against
  │ an evaluation specification produced by the meta judge.
  │
  │ CLAUDE_PLUGIN_ROOT=...
  │
  │ ## User Prompt
  │ Refactor auth module to use dependency injection
  │
  │ ## Pre-existing Changes (Context Only)
  │
  │ The following changes were made BEFORE the current
  │ implementation agent started working. They are NOT part
  │ of the current task's output. Focus your evaluation on
  │ the current task's changes. Only verify pre-existing
  │ changed files/logic if they directly relate to the
  │ current task requirements.
  │
  │ ### Previous Task: "Add basic authentication module"
  │ The following files were created/modified as part of a
  │ previous task:
  │ - src/auth/AuthService.ts (new) - Authentication service
  │   with login/logout/register
  │ - src/auth/AuthMiddleware.ts (new) - Express middleware
  │   for route protection
  │ - src/auth/auth.routes.ts (new) - Auth API routes
  │ - tests/auth/AuthService.test.ts (new) - Unit tests for
  │   auth service
  │ - src/app.ts (modified) - Integrated auth routes and
  │   middleware
  │
  │ These files exist in the codebase and may be modified by
  │ the current task, but you should evaluate only the
  │ changes made by the current implementation agent for the
  │ current task (refactoring to dependency injection).
  │
  │ ## Evaluation Specification
  │ ```yaml
  │ {meta-judge's evaluation specification YAML}
  │ ```
  │
  │ ## Implementation Output
  │ Files: src/auth/AuthService.ts (modified), ...
  │ Key changes: Refactored to constructor injection...
  │
  │ ## Instructions
  │ Follow your full judge process...
  └─────────────────────────────────────────────────────────

  Judge (sadd:judge + Opus)...
    → VERDICT: PASS, SCORE: 4.5/5.0
    → ISSUES: None
    → IMPROVEMENTS: Add interface documentation

Phase 6: Final Report
  ✅ PASS on attempt 1
  Files: AuthService.ts (modified), AuthServiceFactory.ts (new),
         AuthMiddleware.ts (modified), AuthService.test.ts (modified),
         app.ts (modified)
```

### Example 5: User-Modified Codebase Before do-and-judge

**Scenario:**

The user has been working on an e-commerce codebase during the conversation. They modified the shopping cart, product catalog, and checkout flow before invoking do-and-judge.

**Input:**

```
/do-and-judge fix shopping cart module bug when it adds duplicated items
```

**Execution:**

```
Phase 1: Task Analysis
  - Complexity: Medium (bug fix in existing module)
  - Risk: Medium (cart logic affects checkout)
  - Scope: Small (focused bug fix)
  → Model: opus
  - Pre-existing Changes: User modified several files before this task

Phase 2: Parallel Dispatch
  Tool call 1 — Meta-judge (Opus)...
    → Generated evaluation specification YAML
    → 3 rubric dimensions, 5 checklist items
  Tool call 2 — Implementation (sdd:developer + Opus)...
    → Fixed duplicate detection in CartService.addItem()
    → Added deduplication guard in cart.routes.ts
    → Added regression test for duplicate item scenario
    → Summary: 3 files modified

Phase 3: Dispatch Judge (with meta-judge specification)
  NOTE: The orchestrator is aware from git diff/status that the user
  modified several files before this task. Include "Pre-existing Changes"
  section so the judge focuses only on the bug fix.

  Judge prompt sent:
  ┌─────────────────────────────────────────────────────────
  │ You are evaluating an implementation artifact against
  │ an evaluation specification produced by the meta judge.
  │
  │ CLAUDE_PLUGIN_ROOT=...
  │
  │ ## User Prompt
  │ Fix shopping cart module bug when it adds duplicated items
  │
  │ ## Pre-existing Changes (Context Only)
  │
  │ The following changes were made BEFORE the current
  │ implementation agent started working. They are NOT part
  │ of the current task's output. Focus your evaluation on
  │ the current task's changes. Only verify pre-existing
  │ changed files/logic if they directly relate to the
  │ current task requirements.
  │
  │ ### User modifications (before current task)
  │ The user made changes to the following files/modules
  │ before this task was started:
  │ - src/cart/CartService.ts (modified) - Shopping cart
  │   business logic updates
  │ - src/cart/cart.routes.ts (modified) - Updated cart API
  │   endpoints
  │ - src/products/ProductCatalog.ts (modified) - Product
  │   listing changes
  │ - src/checkout/CheckoutFlow.ts (modified) - Checkout
  │   process updates
  │ - tests/cart/CartService.test.ts (modified) - Updated
  │   cart tests
  │
  │ The current task focuses specifically on fixing the
  │ duplicate items bug in the shopping cart module.
  │ Pre-existing changes to cart files may overlap with the
  │ current task scope — evaluate whether the implementation
  │ agent's changes correctly address the bug without
  │ breaking the pre-existing modifications.
  │
  │ ## Evaluation Specification
  │ ```yaml
  │ {meta-judge's evaluation specification YAML}
  │ ```
  │
  │ ## Implementation Output
  │ Files: src/cart/CartService.ts (modified), ...
  │ Key changes: Added duplicate item detection...
  │
  │ ## Instructions
  │ Follow your full judge process...
  └─────────────────────────────────────────────────────────

  Judge (sadd:judge + Opus)...
    → VERDICT: PASS, SCORE: 4.1/5.0
    → ISSUES: None
    → IMPROVEMENTS: Consider extracting deduplication logic
      into a shared utility

Phase 6: Final Report
  ✅ PASS on attempt 1
  Files: CartService.ts (modified), cart.routes.ts (modified),
         CartService.test.ts (modified)
```

## Best Practices

### Model Selection

- **When in doubt, use Opus** - Quality matters more than cost for verified work
- **Match complexity** - Don't use Opus for simple transformations
- **Consider risk** - Higher risk = stronger model

### Meta-Judge + Judge Verification

- **Never skip meta-judge** - Tailored evaluation criteria produce better judgments than generic ones
- **Reuse meta-judge spec on retries** - The evaluation specification stays constant across retry attempts; only the implementation changes
- **Parse only headers from judge** - Don't read full reports to avoid context pollution
- **Trust the threshold** - 4/5.0 is the quality gate
- **Include CLAUDE_PLUGIN_ROOT** - Both meta-judge and judge need the resolved plugin root path

### Iteration

- **Focus fixes** - Don't rewrite everything, fix specific issues
- **Pass feedback verbatim** - Let the implementation agent see exact issues
- **Same meta-judge spec** - Do NOT re-run meta-judge on retries; the evaluation criteria don't change
- **Escalate appropriately** - Don't loop forever on fundamental problems

### Context Management

- **Keep it clean** - You orchestrate, sub-agents implement
- **Summarize, don't copy** - Pass summaries, not full file contents
- **Trust sub-agents** - They can read files themselves
- **Meta-judge YAML** - Pass only the meta-judge YAML to the judge, do not add any additional text or comments to it!
- **Track pre-existing changes** - Pass context about prior modifications to the judge to prevent attribution confusion between pre-existing and current changes
