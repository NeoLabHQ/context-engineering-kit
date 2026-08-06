---
name: do-and-judge
description: Execute a task with sub-agent implementation and LLM-as-a-judge verification with automatic retry loop
argument-hint: Task description [--model haiku|sonnet|opus] [--strict] (e.g., "Refactor the UserService class to use dependency injection")
---

# do-and-judge

## Task
Execute a single task by dispatching an implementation sub-agent, verifying with an independent judge, and iterating with feedback until passing or max retries exceeded.

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task` | Free-form text | **Required** | Task description to execute |
| `--model` | `haiku\|sonnet\|opus` | *auto-selected* | Explicit user override for **all** sub-agents: implementation, meta-judge, and judge. When omitted, you MUST select the model per the [Model Selection Policy](#model-selection-policy) — there is no fixed fallback tier. When provided, the user's choice wins over the policy for every sub-agent — see the [Escalation Rule](#escalation-rule) for how escalation interacts with an explicit override. |
| `--strict` | `--strict` | `false` | Disable the [Iteration Discretion Rule](#iteration-discretion-rule) - the task passes ONLY when `score >= 4.0`, otherwise retry until max retries is reached. |

Example: `/do-and-judge Refactor the UserService class to use dependency injection --strict`

## Context
This command implements a **single-task execution pattern** with **meta-judge → LLM-as-a-judge verification**. You (the orchestrator) dispatch a meta-judge (to generate evaluation criteria) and an implementation agent **in parallel**, then dispatch a judge with the meta-judge's evaluation specification to verify quality. If verification fails, you launch new implementation agent with judge feedback and iterate until passing (score ≥4, or accepted per the [Iteration Discretion Rule](#iteration-discretion-rule)) or max retries (3) exceeded.

Key benefits:

- **Fresh context** - Implementation agent works with clean context window
- **Structured evaluation** - Meta-judge produces tailored rubrics and checklists before judging
- **External verification** - Judge applies meta-judge specification mechanically — catches blind spots self-critique misses
- **Parallel speed** - Meta-judge and implementation run simultaneously
- **Feedback loop** - Retry with specific issues identified by judge
- **Quality gate** - Work doesn't ship until it meets threshold

**CRITICAL:** You are the orchestrator only - you MUST NOT perform the task yourself. IF you read, write or run bash tools you failed task imidiatly. It is single most critical criteria for you. If you used anyting except sub-agents you will be killed immediatly!!!! Your role is to:

1. Analyze the task and select the model per the [Model Selection Policy](#model-selection-policy) — `sonnet`/`haiku` by default, `opus` only when earned
2. Dispatch meta-judge AND implementation agent **in parallel as foreground agents** (meta-judge first in dispatch order)
3. Dispatch judge agent with meta-judge's evaluation specification
4. Parse verdict and iterate if needed (max 3 retries)
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

## Model Selection Policy

Picking the model is the **single highest-leverage decision** you make — more than any prompt wording, it decides whether the task comes back correct and how long it takes. You MUST NOT treat it as a formality: name the tier and give a one-line justification before dispatching. Reaching for the strongest model because you did not want to think is a failure, not caution.

**Tier default:** `sonnet` and `haiku` are the default. `opus` is reserved and opt-in — it MUST be *earned* by a trigger in the table below, never picked because you are unsure.

### Selection Rules

| Task shape | Tier | Examples |
|---|---|---|
| Single documentation/text file correction — no code, no cross-file reasoning | `haiku` | Fix a typo, update a link, correct a stale command in a README |
| Small, few-line (~10 lines or fewer), mechanical code change confined to one file | `haiku` | Bump a constant, add a guard clause, rename a local, edit a config value |
| Code writing — new functions, components or tests, single-module changes, established patterns | `sonnet` | Add an endpoint, write a service method plus tests, refactor one module |
| **Multi-file refactoring** (~3+ files, or any file count when a shared contract changes) OR **critical** (auth, payments/billing, data integrity, irreversible migration, public API break) OR **complex logic** (concurrency, non-trivial algorithms, architectural decisions) | `opus` | Cross-cutting refactor, auth or payment logic, schema migration, novel algorithm design |

**Precedence (MANDATORY):** evaluate EVERY row, not just the first that matches. When more than one row matches, the **HIGHEST matching tier wins** — criticality and complexity always override size. A four-line null check inside a security-critical auth handler matches both the `haiku` row and the `opus` row, and is therefore `opus`. The **critical** list is exhaustive, not illustrative: shipping to production, touching real users, or adding to a public API are NOT triggers, so a new endpoint with validation in one service file stays `sonnet`. **Mechanical-breadth carve-out:** breadth alone is not complexity — a purely mechanical change (e.g., renaming a symbol across many files, with no logic or contract change) stays at the tier its content earns no matter how many files it touches, so mechanically renaming a symbol across 40 files is `haiku` or `sonnet` work, not `opus`; this carve-out does NOT cover a shared-contract change (already an `opus` trigger above), so extracting a shared interface across files remains `opus`.

**Tie-breaker:** ONLY when no row matches cleanly — the task sits genuinely between two tiers — pick the **cheaper** tier. You MUST NOT bias up to `opus` to hedge; the [Escalation Rule](#escalation-rule) makes a cheap first guess recoverable, and one recovered run costs far less than over-provisioning every run.

### Role Pairing

Any model-assigned pipeline has up to three roles — **producer** (does the work), **criteria-setter** (defines what "correct" means), **evaluator** (checks the work against those criteria); in this skill they instantiate as implementation / meta-judge / judge. **Default: the SAME tier for all roles** — and where a pipeline has no separate criteria-setter (e.g. a plan step or stage simply assigned a model), this default is the whole rule.

**Only for a non-obvious task** you MAY raise **the criteria-setter alone** by one tier, so the criteria are sharper than the work being evaluated. *Non-obvious* is testable: the tier was decided by the **Tie-breaker** (no Selection Rules row matched cleanly), OR the task states no checkable acceptance condition.

| Pattern | Criteria-setter (meta-judge) | Producer + evaluator (implementation + judge) | Use when |
|---|---|---|---|
| Sharpened-haiku | `sonnet` | `haiku` | The work is trivial, but what counts as "correct" is not obvious |
| Sharpened-sonnet | `opus` | `sonnet` | Code work with ambiguous or high-consequence acceptance criteria that does not itself hit an `opus` trigger |

Producer and evaluator MAY be a differnt tier. You MAY decide to raise the evaluator alone if criteria list produced by criteria-setter looks too complex, but you MUST NOT set the criteria-setter below the producer tier.

### Escalation Rule

Bump **BOTH producer and evaluator** (implementation and judge) one tier for the next iteration when either trigger fires:

1. **Low first-iteration quality** — a low score, or issues showing the model misunderstood the task rather than merely missing details.
2. **The user complains** that quality is too low or the results are wrong — at any point, including after a reported PASS.

Ladder: `haiku` → `sonnet` → `opus`. `opus` is the **ceiling** — there is no further tier. If `opus`-tier work still fails, escalate to the **user**, never loop.

- **Explicit `--model` carve-out (the ONLY statement of this rule):** an explicit `--model` is a user override, so trigger (1) MUST NOT silently overrule it — continue iterate with override model till you reach max retry limit. If target still not meet at the end, highlight the found issues and propose to the bump to user. Trigger (2) IS that approval, so it bumps immediately.
- Escalation moves producer and evaluator only. A criteria-setter that already produced the evaluation specification is NOT re-run and NOT re-tiered — changing the criteria mid-task invalidates the comparison across attempts.
- Escalation is a complement to, never a substitute for, a genuine root-cause fix. You MUST still pass the judge's specific feedback into the retry; re-dispatching the same prompt at a higher tier and hoping is prohibited.
- Escalation is orthogonal to the score thresholds and the [Iteration Discretion Rule](#iteration-discretion-rule) — it changes *which model* runs the next iteration, never *whether* an iteration is warranted.

### Cross-Provider Equivalence

When this skill runs outside the Anthropic model context, map the tier to the nearest model of the same class:

| Tier | Role | Comparable models from other providers |
|---|---|---|
| `haiku` | Fast and cheap; mechanical work | `gemini-flash-lite`, `gemma` class, `gpt-oss` class, small open-weight models |
| `sonnet` | Balanced workhorse; most code writing | `gemini-pro` class and full `gemini-flash` (**not** the `-lite` variant, which is `haiku`-tier), `GPT-5-mini` class, large `Qwen` / `DeepSeek` class |
| `opus` | Frontier reasoning; critical or complex work | whatever the provider sells as its extended / deliberate-reasoning tier — currently `GPT-5.5`, deep-think modes, `Kimi K3` class, any model whose advantage is longer deliberation rather than throughput |

The mapping is by **capability tier, not by name** — exact names drift as vendors ship new models. Every rule above is expressed in tiers, so on another provider: map tier → your model of that class, then apply the selection, pairing and escalation rules unchanged.

## Process

### Phase 1: Task Analysis and Model Selection

Resolve configuration first: `STRICT_MODE = --strict present || false`. Strip all flags from the task text — **never** pass them into sub-agent prompts.

Unless the user passed `--model`, assess the task on three axes, then read the tier straight off the [Selection Rules](#selection-rules) table:

- **Scope** — one file, one module, or multiple files?
- **Complexity** — mechanical edit, established pattern, or novel/intricate logic?
- **Risk** — isolated and reversible, internal, or **critical** per the exhaustive list in the [Selection Rules](#selection-rules) `opus` row?

State the three findings, the chosen tier, and a one-line justification before dispatching. Then apply [Role Pairing](#role-pairing) to decide the meta-judge tier — same tier as implementation unless the task is genuinely non-obvious. **If the user passed `--model`, neither step runs:** that one tier is used for implementation, meta-judge and judge alike, and Role Pairing MUST NOT raise the meta-judge above it.

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
  - model: {meta-judge model — the user's `--model` if one was passed; otherwise same as implementation, or one tier up per Role Pairing}
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
- Critical: you not allowed to use any mutation git commands, including, but not limited: commit, stash, push, checkout, reset, revert, etc. Except cases when task EXPLICITLY allows or requires it. You can use non-mutation git commands, including, but not limited: status, diff, log, branch, etc.

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
  - model: {selected implementation model}
  - subagent_type: "{selected agent type}"
```

#### 2.3 Parallel Dispatch Example

Send BOTH Task tool calls in a single message. Meta-judge first, implementation second:

```
Message with 2 tool calls:
  Tool call 1 (meta-judge):
    - description: "Meta-judge: {brief task summary}"
    - model: {meta-judge model — the user's `--model` if one was passed; otherwise same as implementation, or one tier up per Role Pairing}
    - subagent_type: "sadd:meta-judge"

  Tool call 2 (implementation):
    - description: "Implement: {brief task summary}"
    - model: {selected implementation model}
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
  - model: {judge model — MUST equal the current implementation model, including after escalation}
  - subagent_type: "sadd:judge"
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

If 3.0 ≤ score <4 and NOT STRICT_MODE:
  → Apply the Iteration Discretion Rule below
    → accepted → VERDICT: PASS (report outstanding issues)
    → declined → VERDICT: FAIL → go to "Check retry count" below

Otherwise (score <3.0, or score <4 with STRICT_MODE):
  → VERDICT: FAIL
  → Check retry count

  If retries < 3:
    → Decide the retry tier per Phase 5 "Model Escalation on Retry" (bump BOTH implementation and judge, or hold)
    → Dispatch retry implementation agent with judge feedback
    → Return to Phase 3 (judge verification with same meta-judge specification)

  If retries ≥ 3:
    → Escalate to user (see Error Handling)
    → Do NOT proceed without user decision
```

Note: `retries` counts attempts within the CURRENT cycle only. This budget **resets** on re-entry after a reported PASS (see [Phase 6 Re-entry](#phase-6-final-report)) — a later user quality complaint opens a fresh cycle of up to 3 retries even if a prior cycle already reached the limit above.

#### Iteration Discretion Rule

Your main task is to COMPLETE the task within target quality. Two failure modes are equally real:

- Burning retries and context on nitpicks so the task never completes on time → **the task is failed**; a developer is waiting on this result and may have dependent work blocked, so implementation effort MUST stay proportionate to the task's size.
- Reporting a result whose quality is genuinely too poor to be considered complete → **an even worse failure**.

Apply to every judge score:

- **`score < 3.0` → FAIL, unconditionally. No discretion.** Retry with judge feedback until it passes or max retries is reached.
- **`3.0 <= score < 4.0` → discretion band.** ONLY inside this band MAY you decide that a result below the `4.0` target is acceptable. The fixed `4.0` target puts the effective floor at `3.0`, so no separate bounded-drop guard is needed.
- Inside the band, when the outstanding issues are ONLY low/medium priority (any High or Critical finding removes discretion entirely) AND none of them breaks a target requirement of the task or causes a meaningful defect (i.e. they are nitpicks), you MUST reason FIRST — before dispatching a retry — about whether another attempt is worth the developer's time and your context.
- **At most ONE nitpick-driven retry**, and it counts against the retry budget. If it again surfaces only nitpicks, you MUST report PASS (☑️ ACCEPTED) with the outstanding issues listed in the final report. If it returns a score below `3.0`, the unconditional-FAIL rule applies instead.
- You MUST be critical, NOT lenient. Stopping short of target MUST be an intentional decision grounded in the absence of real, requirement-breaking issues. A genuine blocking issue that prevents completing the task within max retries MUST be escalated as a failure, never papered over.
- **If `STRICT_MODE` is true, this whole rule is DISABLED**: stop only when `score >= 4.0` or max retries is reached. `--strict` changes nothing else — the `4.0` target, the max-retry limit, the `< 3.0` unconditional FAIL and meta-judge/judge dispatch are unaffected.

### Phase 5: Retry with Feedback (If Needed)

#### Model Escalation on Retry

Before dispatching any retry you MUST decide the tier explicitly per the [Escalation Rule](#escalation-rule) — which governs in full — and state the decision in your output. Retry-specific anchors on top of it:

- **Trigger (1) is anchored at `score < 3.0`** here (or issues showing the model misunderstood the task rather than merely missing details).
- **Hold the tier** when the failure is a specific fixable defect rather than a capability gap — narrow, precisely specified issues are resolved faster by a same-tier retry with exact feedback.
- If `opus` still fails, escalate to the user per [Error Handling](#error-handling).

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
**Result:** ✅ PASS (or ☑️ ACCEPTED below target per the Iteration Discretion Rule)
**Strict Mode:** {STRICT_MODE}

### Verification
| Attempt | Score | Status |
|---------|-------|--------|
| 1 | {X.X}/5.0 | {PASS/ACCEPTED/FAIL} |
| {N} | {X.X}/5.0 | {PASS/ACCEPTED/FAIL} | (one row per retry that occurred, up to 3)

### Outstanding Issues (if accepted below target)
{Nitpicks left unresolved, with priority — omit this section when score >= 4.0}

### Files Modified
- {file1}: {what changed}
- {file2}: {what changed}

### Key Changes
- {change 1}
- {change 2}

### Suggested Improvements (Optional)
{IMPROVEMENTS from judge, if any}
```

**Re-entry after reporting:** a reported PASS does NOT close the task. If the user then says the result is wrong or the quality is too low, re-enter Phase 5 with their complaint as the feedback — that is [Escalation Rule](#escalation-rule) trigger (2), so bump BOTH producer and evaluator one tier (unless already `opus`) and retry. The retry budget **resets**: the complaint opens a fresh cycle of up to 3 retries even if the previous cycle exhausted its own.

## Error Handling

### If Max Retries Exceeded

When the task still fails verification after 3 retries:

1. **STOP** - Do not proceed
2. **Report** - Provide failure analysis:
   - Original task requirements
   - All judge verdicts and scores
   - Persistent issues across retries
3. **Escalate** - Present options to user:
   - Provide additional context/guidance for retry
   - Re-run at the next model tier up (unavailable if the run was already at `opus`)
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
2. **Escalate the tier** - Re-run implementation and judge one tier up (omit this option if already `opus`)
3. **Modify requirements** - Simplify or clarify task
4. **Abort** - Stop execution

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
  → Model: haiku (implementation + judge), sonnet (meta-judge)
    Reasoning: Single documentation file, no code written — no opus
    trigger fires. It is more than a one-line correction, so it straddles
    haiku/sonnet; the tie-breaker sends it DOWN to haiku, and escalation
    covers a thin first pass. The task states no checkable acceptance
    condition — the second non-obvious disjunct — so the sharpened-haiku
    pairing raises the meta-judge one tier to sonnet.
  → Agent type: general-purpose
    Reasoning: This is a documentation task — writing and restructuring
    prose, not implementing code. The sdd:developer agent is optimized
    for code implementation patterns, not technical writing. A
    general-purpose agent handles documentation tasks more effectively
    because it applies broader writing and reasoning skills without
    code-centric constraints.

Phase 2: Parallel Dispatch (single message, 2 tool calls)
  Tool call 1 — Meta-judge (Sonnet)...
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

  Tool call 2 — Implementation (general-purpose + Haiku)...
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

  Judge (sadd:judge + Haiku)...   ← same tier as implementation
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

### Example 2: Pass After Retry with Model Escalation

**Input:**

```
/do-and-judge Implement rate limiting middleware with configurable limits per endpoint
```

**Execution:**

```
Phase 1: Task Analysis
  - Complexity: Medium (new middleware, established pattern)
  - Risk: Medium (middleware sits in front of all endpoints)
  - Scope: Small (single middleware + config schema)
  → Model: sonnet (implementation + meta-judge + judge)
    Reasoning: Code writing on an established pattern, confined to one
    module. No opus trigger fires — not multi-file, not complex logic,
    and rate limiting is on none of the critical list; breadth of reach
    is not itself a trigger. Same tier for all three roles.

Phase 2: Parallel Dispatch (Attempt 1)
  Tool call 1 — Meta-judge (Sonnet)...
    → Generated evaluation specification YAML
    → 4 rubric dimensions, 8 checklist items
  Tool call 2 — Implementation (sdd:developer + Sonnet)...
    → Created RateLimiter middleware
    → Added configuration schema

Phase 3: Dispatch Judge (with meta-judge specification)
  Judge (sadd:judge + Sonnet)...
    → VERDICT: FAIL, SCORE: 2.9/5.0
    → ISSUES:
      - Missing per-endpoint configuration (a stated requirement)
      - Limiter is not concurrency-safe under parallel requests
    → IMPROVEMENTS: Add monitoring hooks

Phase 5: Retry with Feedback
  Model Escalation on Retry:
    → Score 2.9 < 3.0 and the concurrency issue shows the task was
      misunderstood, not merely under-delivered → ESCALATE
    → Bump BOTH implementation and judge: sonnet → opus
    → Meta-judge NOT re-run, NOT re-tiered — same specification reused
  Implementation (sdd:developer + Opus)...
    → Added endpoint-specific limits
    → Replaced the counter with an atomic, concurrency-safe token bucket

Phase 3: Dispatch Judge (Attempt 2, same meta-judge specification)
  Judge (sadd:judge + Opus)...   ← escalated with the implementation
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
  - Complexity: High (multi-tenancy affects every query path)
  - Risk: High (database schema change)
  - Scope: Large (schema, migrations, query layer)
  → Model: opus (implementation + meta-judge + judge)
    Reasoning: opus is EARNED here — two triggers fire: multi-file
    refactoring and critical (data integrity, irreversible migration).

Phase 2: Parallel Dispatch
  Meta-judge → evaluation specification YAML
  Implementation → initial migration scaffolding

Attempt 1: FAIL (2.8/5.0) - Missing tenant isolation in queries
Attempt 2: FAIL (3.2/5.0) - Incomplete migration script
Attempt 3: FAIL (3.3/5.0) - Edge cases in existing data migration

ESCALATION:
  Persistent issue: Existing data migration requires business decisions
  about how to handle orphaned records.

  Options presented to user (tier escalation omitted — already at the
  opus ceiling, no bump available):
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
  - Scope: Medium (new module, several files)
  → Model: opus (implementation + meta-judge + judge)
    Reasoning: opus is EARNED — the critical trigger fires on auth.
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
  Model Escalation on Retry:
    → Already at opus — the ceiling, no bump available. Retry at the
      same tier with the judge's specific feedback; if this fails
      repeatedly, escalate to the user rather than looping.
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
  - Scope: Large (5 files across the module and its wiring)
  → Model: opus (implementation + meta-judge + judge)
    Reasoning: opus is EARNED — multi-file refactoring, and the module
    being rewired is the security-critical auth path.
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
  → Model: sonnet (implementation + meta-judge + judge)
    Reasoning: Code writing on a contained bug plus a regression test.
    No opus trigger — not a multi-file refactor, nothing on the critical
    list (in-memory cart state, not billing), no intricate logic. Too
    much reasoning is needed for haiku, so sonnet for all three roles.
  - Pre-existing Changes: User modified several files before this task

Phase 2: Parallel Dispatch
  Tool call 1 — Meta-judge (Sonnet)...
    → Generated evaluation specification YAML
    → 3 rubric dimensions, 5 checklist items
  Tool call 2 — Implementation (sdd:developer + Sonnet)...
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

  Judge (sadd:judge + Sonnet)...   ← same tier as implementation
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

The rules govern in the [Model Selection Policy](#model-selection-policy); these are the habits that make them stick:

- **Justify out loud** - state scope, complexity and risk plus the resulting tier before dispatching; this is the highest-leverage decision in the run
- **`opus` is earned, never a hedge** - resolve every overlap and tie by the [Selection Rules](#selection-rules) precedence and tie-breaker, never by instinct
- **One tier across roles** - raise only the criteria-setter (meta-judge), and only for a non-obvious task ([Role Pairing](#role-pairing))
- **Escalate on evidence** - a clearly-too-low iteration or a user quality complaint ([Escalation Rule](#escalation-rule))

### Meta-Judge + Judge Verification

- **Never skip meta-judge** - Tailored evaluation criteria produce better judgments than generic ones
- **Reuse meta-judge spec on retries** - The evaluation specification stays constant across retry attempts; only the implementation changes
- **Parse only headers from judge** - Don't read full reports to avoid context pollution
- **Trust the threshold** - 4/5.0 is the quality gate; below it, the [Iteration Discretion Rule](#iteration-discretion-rule) decides (unless `--strict`)
- **Include CLAUDE_PLUGIN_ROOT** - Both meta-judge and judge need the resolved plugin root path

### Iteration

- **Focus fixes** - Don't rewrite everything, fix specific issues
- **Pass feedback verbatim** - Let the implementation agent see exact issues
- **Same meta-judge spec** - Do NOT re-run meta-judge on retries; the evaluation criteria don't change
- **Escalate appropriately** - Don't loop forever on fundamental problems
- **Stay proportionate** - Match iteration effort to task size per the [Iteration Discretion Rule](#iteration-discretion-rule); at most ONE nitpick-driven retry

### Context Management

- **Keep it clean** - You orchestrate, sub-agents implement
- **Summarize, don't copy** - Pass summaries, not full file contents
- **Trust sub-agents** - They can read files themselves
- **Meta-judge YAML** - Pass only the meta-judge YAML to the judge, do not add any additional text or comments to it!
- **Track pre-existing changes** - Pass context about prior modifications to the judge to prevent attribution confusion between pre-existing and current changes
