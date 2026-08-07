---
name: do-in-steps
description: Execute one complex task as ordered, dependent steps run sequentially, passing context from each step to the next, with per-step LLM-as-a-judge verification. Use when later steps depend on the results of earlier ones.
argument-hint: Task description [--model haiku|sonnet|opus] [--strict] (e.g., "Refactor UserService class and update all consumers")
---

# do-in-steps

<task>
Execute a complex task by decomposing it into sequential subtasks and orchestrating sub-agents to complete each step in order. Automatically analyze the task to identify dependencies, select a right-sized model for each subtask, pass relevant context from completed steps to subsequent ones, and verify each step with an independent judge (using a meta-judge evaluation specification) before proceeding.
</task>

<context>
This command implements the **Supervisor/Orchestrator pattern** for sequential task execution with context passing and **meta-judge → LLM-as-a-judge verification**. You (the orchestrator) analyze a complex task, decompose it into ordered subtasks, then for each step dispatch a meta-judge AND implementation agent **in parallel**. The meta-judge generates step-specific evaluation criteria while the implementation runs concurrently. Each sub-agent receives:
- **Isolated context** - Clean context window for its specific subtask
- **Right-sized model** - Chosen per step by the [Model Selection Policy](#model-selection-policy): `sonnet`/`haiku` by default, `opus` only when earned
- **Previous step context** - Summary of relevant outputs from preceding steps
- **Structured reasoning** - Zero-shot CoT prefix for systematic thinking
- **Self-critique** - Internal verification before submission
- **Structured evaluation** - Meta-judge produces tailored rubrics and checklists per step before judging occurs
- **External judge** - LLM-as-a-judge verification using meta-judge specification with iteration loop
- **Parallel speed** - Meta-judge and implementation agent run in parallel per step; meta-judge specification reused across retries within that step

</context>

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task` | Free-form text | **Required** | Task description to decompose and execute |
| `--strict` | `--strict` | `false` | Disable the [Iteration Discretion Rule](#36-iteration-discretion-rule) - a step passes ONLY when `score >= 4.0`, otherwise retry until max retries is reached. |
| `--model` | `haiku\|sonnet\|opus` | *auto-selected per step* | Explicit user override for **all** sub-agents in **every** step: implementation, meta-judge, and judge. When omitted, you MUST select a tier per step per the [Model Selection Policy](#model-selection-policy) — there is no fixed fallback tier. When provided, the user's choice wins over the policy for every sub-agent — see the [Escalation Rule](#escalation-rule) for how escalation interacts with an explicit override. |

Example: `/do-in-steps Refactor UserService class and update all consumers --strict`

**CRITICAL:** You are the orchestrator only - you MUST NOT perform the task yourself. IF you read, write or run bash tools you failed task imidiatly. It is single most critical criteria for you. If you used anyting except sub-agents you will be killed immediatly!!!! Your role is to:

1. Analyze and decompose the task
2. Select the model tier and agent for **each** subtask per the [Model Selection Policy](#model-selection-policy) — `sonnet`/`haiku` by default, `opus` only when earned
3. **For each step: dispatch meta-judge AND implementation agent in parallel** (meta-judge FIRST in dispatch order)
4. **Wait for BOTH to complete, then dispatch judge with meta-judge's specification**
5. **Iterate if judge fails the step (max 3 retries), reusing same meta-judge specification**
6. Collect outputs and pass context forward
7. Report final results

## RED FLAGS - Never Do These

**NEVER:**

- Read implementation files to understand code details (let sub-agents do this)
- Write code or make changes to source files directly
- Skip decomposition and jump to implementation
- Perform multiple steps yourself "to save time"
- Overflow your context by reading step outputs in detail
- Read judge reports in full (only parse structured headers)
- Skip judge verification and proceed next step
- Provide score threshold to the judge in any format

**ALWAYS:**

- Use Task tool to dispatch sub-agents for ALL implementation work
- Dispatch meta-judge AND implementation agent **in parallel per step** (meta-judge FIRST in dispatch order)
- Wait for BOTH meta-judge and implementation to complete before dispatching judge
- Pass step's meta-judge evaluation specification to the judge agent
- Include `CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}` in prompts to meta-judge and judge agents
- Reuse same meta-judge specification across retries within a step (never re-run meta-judge for retries)
- Dispatch a NEW meta-judge for each new step (each step gets its own tailored specification)
- Use Task tool to dispatch **independent judges** for step verification
- Pass only necessary context summaries, not full file contents
- Get pass from judge verification before proceeding to next step
- Iterate with judge feedback if verification fails (max 3 retries)
- Apply the [Iteration Discretion Rule](#36-iteration-discretion-rule) to every step verdict, unless `--strict` was provided

Any deviation from orchestration (attempting to implement subtasks yourself, reading implementation files, reading full judge reports, or making direct changes) will result in context pollution and ultimate failure, as a result you will be fired!

## Model Selection Policy

Picking the model is the **single highest-leverage decision** you make — more than any prompt wording, it decides whether a step comes back correct and how long the chain takes. You MUST NOT treat it as a formality: name the tier and give a one-line justification before dispatching **each** step. Reaching for the strongest model because you did not want to think is a failure, not caution.

**Tier default:** `sonnet` and `haiku` are the default. `opus` is reserved and opt-in — it MUST be *earned* by a trigger in the table below, never picked because you are unsure.

**Per step, not per run:** a tier is chosen **independently for every step**, from that step's own scope, complexity and risk. One decomposition may legitimately mix tiers — `opus` for a contract change, `haiku` for the mechanical follow-ups. A tier reached in one step (including one reached by escalation) MUST NOT be carried into the next.

### Selection Rules

| Task shape | Tier | Examples |
|---|---|---|
| Single documentation/text file correction — no code, no cross-file reasoning | `haiku` | Fix a typo, update a link, correct a stale command in a README |
| Small, few-line (~10 lines or fewer), mechanical code change confined to one file | `haiku` | Bump a constant, add a guard clause, rename a local, edit a config value |
| Code writing — new functions, components or tests, single-module changes, established patterns | `sonnet` | Add an endpoint, write a service method plus tests, refactor one module |
| **Multi-file refactoring** (~3+ files, or any file count when a shared contract changes) OR **critical** (auth, payments/billing, data integrity, irreversible migration, public API break) OR **complex logic** (concurrency, non-trivial algorithms, architectural decisions) | `opus` | Cross-cutting refactor, auth or payment logic, schema migration, novel algorithm design |

**Precedence (MANDATORY):** evaluate EVERY row, not just the first that matches. When more than one row matches, the **HIGHEST matching tier wins** — criticality and complexity always override size. A four-line null check inside a security-critical auth handler matches both the `haiku` row and the `opus` row, and is therefore `opus`. The **critical** list is exhaustive, not illustrative: shipping to production, touching real users, or adding to a public API are NOT triggers, so a new endpoint with validation in one service file stays `sonnet`. **Mechanical-breadth carve-out:** breadth alone is not complexity. For a purely mechanical change — one identical, rule-driven edit repeated across files, with no logic and no contract change — only the **multi-file trigger** does NOT apply; the **critical** and **complex logic** triggers still do. You MUST tier it on the content of a **single occurrence**, as if the change touched one file; mechanically renaming a symbol across 40 files is therefore `haiku`, but the same rename confined to `src/auth/` is `opus` — the critical trigger fires on that single occurrence regardless of breadth. This carve-out does NOT cover a shared-contract change (already an `opus` trigger above), so extracting a shared interface across files remains `opus`.

**Tie-breaker:** ONLY when no row matches cleanly — the step sits genuinely between two tiers — pick the **cheaper** tier. You MUST NOT bias up to `opus` to hedge; the [Escalation Rule](#escalation-rule) makes a cheap first guess recoverable, and one recovered step costs far less than over-provisioning every step.

### Role Pairing

Any model-assigned pipeline has up to three roles — **producer** (does the work), **criteria-setter** (defines what "correct" means), **evaluator** (checks the work against those criteria); in this skill they instantiate **per step** as implementation / meta-judge / judge. **Default: the SAME tier for all three roles of that step.**

**Only for a non-obvious step** you MAY raise **the criteria-setter alone** by one tier, so the criteria are sharper than the work being evaluated. *Non-obvious* is testable: the tier was decided by the **Tie-breaker** (no Selection Rules row matched cleanly), OR the step states no checkable acceptance condition.

| Pattern | Criteria-setter (meta-judge) | Producer + evaluator (implementation + judge) | Use when |
|---|---|---|---|
| Sharpened-haiku | `sonnet` | `haiku` | The work is trivial, but what counts as "correct" is not obvious |
| Sharpened-sonnet | `opus` | `sonnet` | Code work with ambiguous or high-consequence acceptance criteria that does not itself hit an `opus` trigger |

Producer and evaluator MAY be a differnt tier. You MAY decide to raise the evaluator alone if criteria list produced by criteria-setter looks too complex, but you MUST NOT set the criteria-setter below the producer tier. **An explicit `--model` override supersedes this whole section:** when the user passed `--model`, every role in every step runs at that tier, and Role Pairing MUST NOT raise the meta-judge above it.

### Escalation Rule

Bump **BOTH producer and evaluator** (the failing step's implementation and judge) one tier for the next attempt when either trigger fires:

1. **Low first-attempt quality** — a low score, or issues showing the model misunderstood the step rather than merely missing details.
2. **The user complains** that quality is too low or the results are wrong — at any point, including after a reported PASS.

Ladder: `haiku` → `sonnet` → `opus`. `opus` is the **ceiling** — there is no further tier. If `opus`-tier work still fails, escalate to the **user**, never loop.

- **Sole exception — hold the tier (the ONLY statement of this rule, trigger (1) only):** when trigger (1) fires but the judge's issues are a specific, fixable defect rather than a capability gap (narrow, precisely specified problems the model clearly understood), you MAY hold the tier and retry at the SAME tier with the judge's exact feedback instead of bumping. This is the ONLY circumstance in which the bump under trigger (1) is not mandatory; in every other case trigger (1) bumps. Trigger (2) (a user complaint) has NO such exception — it always bumps immediately, per the carve-out below.
- **Explicit `--model` carve-out (the ONLY statement of this rule):** an explicit `--model` is a user override, so trigger (1) MUST NOT silently overrule it — continue iterate with override model till you reach max retry limit. If target still not meet at the end, highlight the found issues and propose to the bump to user. Trigger (2) IS that approval, so it bumps immediately.
- **Scoped to the failing step.** Escalation re-tiers the retries of THAT step only. It does NOT re-tier the chain: every later step is assessed on its own merits per the [Selection Rules](#selection-rules), starting again from the `sonnet`/`haiku` default.
- Escalation moves implementation and judge only. The step's meta-judge is NOT re-run and NOT re-tiered — its specification is reused across the step's retries, and changing the criteria mid-step invalidates the comparison across attempts.
- Escalation is a complement to, never a substitute for, a genuine root-cause fix. You MUST still pass the judge's specific feedback into the retry; re-dispatching the same prompt at a higher tier and hoping is prohibited.
- Escalation is orthogonal to the score thresholds, the [Iteration Discretion Rule](#36-iteration-discretion-rule) and the per-step max-3-retries budget — it changes *which model* runs the next attempt, never *whether* an attempt is warranted.
- **Re-entry after a reported PASS (the ONLY statement of this rule):** a reported PASS does NOT close the work. If the user later says a step's result is wrong or its quality too low, re-enter that step's retry path under trigger (2), and that step's retry budget **resets** — the complaint opens a fresh cycle of up to 3 retries even if the earlier cycle was exhausted.

### Cross-Provider Equivalence

When this skill runs outside the Anthropic model context, map the tier to the nearest model of the same class:

| Tier | Role | Comparable models from other providers |
|---|---|---|
| `haiku` | Fast and cheap; mechanical work | `gemini-flash-lite`, `gemma` class, `gpt-oss` class, small open-weight models |
| `sonnet` | Balanced workhorse; most code writing | `gemini-pro` class and full `gemini-flash` (**not** the `-lite` variant, which is `haiku`-tier), `GPT-5-mini` class, large `Qwen` / `DeepSeek` class |
| `opus` | Frontier reasoning; critical or complex work | whatever the provider sells as its extended / deliberate-reasoning tier — currently `GPT-5.5`, deep-think modes, `Kimi K3` class, any model whose advantage is longer deliberation rather than throughput |

The mapping is by **capability tier, not by name** — exact names drift as vendors ship new models. Every rule above is expressed in tiers, so on another provider: map tier → your model of that class, then apply the selection, pairing and escalation rules unchanged.

## Process

### Setup: Create Reports Directory

Before starting, ensure the reports directory exists:

```bash
mkdir -p .specs/reports
```

**Report naming convention:** `.specs/reports/{task-name}-step-{N}-{YYYY-MM-DD}.md`

Where:

- `{task-name}` - Derived from task description (e.g., `user-dto-refactor`)
- `{N}` - Step number
- `{YYYY-MM-DD}` - Current date

**Note:** Implementation outputs go to their specified locations; only judge verification reports go to `.specs/reports/`

### Phase 1: Task Analysis and Decomposition

Resolve configuration first: `STRICT_MODE = --strict present || false`. Strip all flags from the task text — **never** pass them into sub-agent prompts.

Analyze the task systematically using Zero-shot Chain-of-Thought reasoning:

```
Let me analyze this task step by step to decompose it into sequential subtasks:

1. **Task Understanding**
   "What is the overall objective?"
   - What is being asked?
   - What is the expected final outcome?
   - What constraints exist?

2. **Identify Natural Boundaries**
   "Where does the work naturally divide?"
   - Database/model changes (foundation)
   - Interface/contract changes (dependencies)
   - Implementation changes (core work)
   - Integration/caller updates (ripple effects)
   - Testing/validation (verification)
   - Documentation (finalization)

3. **Dependency Identification**
   "What must happen before what?"
   - "If I do B before A, will B break or use stale information?"
   - "Does B need any output from A as input?"
   - "Would doing B first require redoing work after A?"
   - What is the minimal viable ordering?

4. **Define Clear Boundaries**
   "What exactly does each subtask encompass?"
   - Input: What does this step receive?
   - Action: What transformation/change does it make?
   - Output: What does this step produce?
   - Verification: How do we know it succeeded?
```

**Decomposition Guidelines:**

| Pattern | Decomposition Strategy | Example |
|---------|------------------------|---------|
| Interface change | 1. Update interface, 2. Update implementations, 3. Update consumers | "Change return type of getUser" |
| Feature addition | 1. Add core logic, 2. Add integration points, 3. Add API layer | "Add caching to UserService" |
| Refactoring | 1. Extract/modify core, 2. Update internal references, 3. Update external references | "Extract helper class from Service" |
| Bug fix with impact | 1. Fix root cause, 2. Fix dependent issues, 3. Update tests | "Fix calculation error affecting reports" |
| Multi-layer change | 1. Data layer, 2. Business layer, 3. API layer, 4. Client layer | "Add new field to User entity" |

**Decomposition Output Format:**

```markdown
## Task Decomposition

### Original Task
{task_description}

### Subtasks (Sequential Order)

| Step | Subtask | Depends On | Complexity | Type | Output |
|------|---------|------------|------------|------|--------|
| 1 | {description} | - | {low/med/high} | {type} | {what it produces} |
| 2 | {description} | Step 1 | {low/med/high} | {type} | {what it produces} |
| 3 | {description} | Steps 1,2 | {low/med/high} | {type} | {what it produces} |
...

### Dependency Graph
Step 1 ─→ Step 2 ─→ Step 3 ─→ ...
```

### Phase 2: Model Selection for Each Subtask

Assess **every** subtask on the three axes below, then read its tier straight off the [Selection Rules](#selection-rules) table — tiers are chosen per step, never once for the whole run.

- **Scope** — one file, one component, or multiple files?
- **Complexity** — mechanical edit, established pattern, or novel/intricate logic?
- **Risk** — isolated and reversible, internal, or **critical** per the exhaustive list in the [Selection Rules](#selection-rules) `opus` row?

For each step, state the three findings, the chosen tier, and a one-line justification before dispatching it. Then apply [Role Pairing](#role-pairing) — which governs in full, including its `--model` override — to decide that step's meta-judge tier.

**Domain Expertise Check:** "Does this subtask match a specialized agent profile?"

- Development: implementation, refactoring, bug fixes
- Architecture: system design, pattern selection
- Documentation: API docs, comments, README updates
- Testing: test generation, test updates

**Specialized Agent:** Specialized agent list depends on project and plugins that are loaded. Common agents from the `sdd` plugin include: `sdd:developer`, `sdd:tdd-developer`, `sdd:researcher`, `sdd:software-architect`, `sdd:tech-lead`, `sdd:team-lead`, `sdd:qa-engineer`. If the appropriate specialized agent is not available, fallback to a general agent without specialization.

**Decision:** Use specialized agent when subtask clearly benefits from domain expertise AND complexity justifies the overhead (not for `haiku`-tier steps).

**Selection Output Format:**

```markdown
## Model/Agent Selection

| Step | Subtask | Model | Agent | Rationale |
|------|---------|-------|-------|-----------|
| 1 | Update interface | opus | sdd:developer | opus is EARNED — shared contract changes across consumers |
| 2 | Update implementations | sonnet | sdd:developer | Code writing on an established pattern, one module |
| 3 | Update callers | haiku | - | Mechanical rename, no logic or contract change |
| 4 | Update tests | sonnet | sdd:tdd-developer | Test writing, established patterns |
```

### Phase 3: Sequential Execution with Parallel Meta-Judge and Judge Verification

Execute subtasks one by one. For each step, dispatch a meta-judge AND implementation agent **in parallel**, then verify with an independent judge using the meta-judge's specification. Iterate if needed, then pass context forward.

**Execution Flow per Step:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Step N                                                                       │
│                                                                              │
│   ┌──────────────┐                                                           │
│   │ Meta-Judge   │──┐ (parallel)                                             │
│   │ (Sub-agent)  │  │                                                        │
│   └──────────────┘  │   ┌──────────────┐     ┌──────────────────────┐       │
│                      ├──▶│    Judge     │────▶│ Parse Verdict        │       │
│   ┌──────────────┐  │   │ (Sub-agent)  │     │ (Orchestrator)       │       │
│   │ Implementer  │──┘   └──────────────┘     └──────────────────────┘       │
│   │ (Sub-agent)  │                                      │                    │
│   └──────────────┘                                      ▼                    │
│          ▲                              ┌──────────────────────────────┐     │
│          │                              │ PASS (≥4.0)?                 │     │
│          │                              │ ├─ YES → Next Step           │     │
│          │                              │ ├─ ≥3.0 → Rule 3.6           │     │
│          │                              │ └─ NO  → Retry?              │     │
│          │                              │     ├─ <3 retries → Retry    │     │
│          │                              │     └─ ≥3 retries → Escalate │     │
│          │                              └──────────────────────────────┘     │
│          │                                            │                      │
│          └────────────── feedback ────────────────────┘                      │
│          (retries reuse same meta-judge spec, no new meta-judge)             │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 3.1 Context Passing Protocol

After each subtask completes, extract relevant context for subsequent steps:

**Context to pass forward:**

- Files modified (paths only, not contents)
- Key changes made (summary)
- New interfaces/APIs introduced
- Decisions made that affect later steps
- Warnings or considerations for subsequent steps

**Context filtering:**

- Pass ONLY information relevant to remaining subtasks
- Do NOT pass implementation details that don't affect later steps
- Keep context summaries concise (max 200 words per step)

**Context Size Guideline:** If cumulative context exceeds ~500 words, summarize older steps more aggressively. Sub-agents can read files directly if they need details.

**Example of Context Accumulation (Concrete):**

```markdown
## Completed Steps Summary

### Step 1: Define UserRepository Interface
- **What was done:** Created `src/repositories/UserRepository.ts` with interface definition
- **Key outputs:**
  - Interface: `IUserRepository` with methods: `findById`, `findByEmail`, `create`, `update`, `delete`
  - Types: `UserCreateInput`, `UserUpdateInput` in `src/types/user.ts`
- **Relevant for next steps:**
  - Implementation must fulfill `IUserRepository` interface
  - Use the defined input types for method signatures

### Step 2: Implement UserRepository
- **What was done:** Created `src/repositories/UserRepositoryImpl.ts` implementing `IUserRepository`
- **Key outputs:**
  - Class: `UserRepositoryImpl` with all interface methods implemented
  - Uses existing database connection from `src/db/connection.ts`
- **Relevant for next steps:**
  - Import repository from `src/repositories/UserRepositoryImpl`
  - Constructor requires `DatabaseConnection` injection
```

#### 3.2 Sub-Agent Prompt Construction

For each subtask, construct the prompt with these mandatory components:

##### 3.2.1 Zero-shot Chain-of-Thought Prefix (REQUIRED - MUST BE FIRST)

```markdown
## Reasoning Approach

Before taking any action, think through this subtask systematically.

Let's approach this step by step:

1. "Let me understand what was done in previous steps..."
   - What context am I building on?
   - What interfaces/patterns were established?
   - What constraints did previous steps introduce?

2. "Let me understand what this step requires..."
   - What is the specific objective?
   - What are the boundaries of this step?
   - What must I NOT change (preserve from previous steps)?

3. "Let me plan my approach..."
   - What specific modifications are needed?
   - What order should I make them?
   - What could go wrong?

4. "Let me verify my approach before implementing..."
   - Does my plan achieve the objective?
   - Am I consistent with previous steps' changes?
   - Is there a simpler way?

Work through each step explicitly before implementing.
```

##### 3.2.2 Task Body

```markdown
<task>
{Subtask description}
</task>

<subtask_context>
Step {N} of {total_steps}: {subtask_name}
</subtask_context>

<previous_steps_context>
{Summary of relevant outputs from previous steps - ONLY if this is not the first step}
- Step 1: {what was done, key files modified, relevant decisions}
- Step 2: {what was done, key files modified, relevant decisions}
...
</previous_steps_context>

<constraints>
- Focus ONLY on this specific subtask
- Build upon (do not undo) changes from previous steps
- Follow existing code patterns and conventions
- Produce output that subsequent steps can build upon
- Critical: you not allowed to use any mutation git commands, including, but not limited: commit, stash, push, checkout, reset, revert, etc. Except cases when task EXPLICITLY allows or requires it. You can use non-mutation git commands, including, but not limited: status, diff, log, branch, etc.

</constraints>

<input>
{What this subtask receives - files, context, dependencies}
</input>

<output>
{Expected deliverable - modified files, new files, summary of changes}

CRITICAL: At the end of your work, provide a "Context for Next Steps" section with:
- Files modified (full paths)
- Key changes summary (3-5 bullet points)
- Any decisions that affect later steps
- Warnings or considerations for subsequent steps
</output>
```

##### 3.2.3 Self-Critique Suffix (REQUIRED - MUST BE LAST)

```markdown
## Self-Critique Verification (MANDATORY)

Before completing, verify your work integrates properly with previous steps. Do not submit unverified changes.

### Verification Questions

Generate verification questions based on the subtask description and the previous steps context. Examples:

| # | Question | Evidence Required |
|---|----------|-------------------|
| 1 | Does my work build correctly on previous step outputs? | [Specific evidence] |
| 2 | Did I maintain consistency with established patterns/interfaces? | [Specific evidence] |
| 3 | Does my solution address ALL requirements for this step? | [Specific evidence] |
| 4 | Did I stay within my scope (not modifying unrelated code)? | [List any out-of-scope changes] |
| 5 | Is my output ready for the next step to build upon? | [Check against dependency graph] |

### Answer Each Question with Evidence

Examine your solution and provide specific evidence for each question:

[Q1] Previous Step Integration:
- Previous step output: [relevant context received]
- How I built upon it: [specific integration]
- Any conflicts: [resolved or flagged]

[Q2] Pattern Consistency:
- Patterns established: [list]
- How I followed them: [evidence]
- Any deviations: [justified or fixed]

[Q3] Requirement Completeness:
- Required: [what was asked]
- Delivered: [what you did]
- Gap analysis: [any gaps]

[Q4] Scope Adherence:
- In-scope changes: [list]
- Out-of-scope changes: [none, or justified]

[Q5] Output Readiness:
- What later steps need: [based on decomposition]
- What I provided: [specific outputs]
- Completeness: [HIGH/MEDIUM/LOW]

### Revise If Needed

If ANY verification question reveals a gap:
1. **FIX** - Address the specific gap identified
2. **RE-VERIFY** - Confirm the fix resolves the issue
3. **UPDATE** - Update the "Context for Next Steps" section

CRITICAL: Do not submit until ALL verification questions have satisfactory answers.
```

#### 3.3 Parallel Meta-Judge Dispatch

**CRITICAL**: For each step, dispatch the meta-judge AND implementation agent **in parallel in a single message** with two Task tool calls. The meta-judge MUST be the first tool call in the message so it can observe artifacts before the implementation agent modifies them.

Both agents run as **foreground** agents. Wait for BOTH to complete before proceeding to judge dispatch.

**Meta-Judge Prompt (per step):**

```markdown
## Task

Generate an evaluation specification yaml for the following step. You will produce rubrics, checklists, and scoring criteria that a judge agent will use to evaluate the implementation artifact.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt
{Original task description from user}

## Step Being Evaluated
Step {N}/{total}: {subtask_name}
{subtask_description}
- Input: {what this step receives}
- Expected output: {what this step should produce}

## Previous Steps Context
{Summary of what previous steps accomplished}

## Artifact Type
{code | documentation | configuration | etc.}

## Instructions
Return only the final evaluation specification YAML in your response.
```

**Dispatch Example**

Send BOTH Task tool calls in a single message. Meta-judge first, implementation second:

```
Message with 2 tool calls:
  Tool call 1 (meta-judge):
    - description: "Meta-judge Step {N}/{total}: {subtask_name}"
    - model: {meta-judge model — the user's `--model` if one was passed; otherwise the same tier as this step's implementation, or one tier up per Role Pairing}
    - subagent_type: "sadd:meta-judge"

  Tool call 2 (implementation):
    - description: "Step {N}/{total}: {subtask_name}"
    - model: {implementation model — the user's `--model` if one was passed; otherwise the model selected for this step}
    - subagent_type: "{selected agent type}"
```

Wait for BOTH to return before proceeding to judge dispatch.

#### 3.4 Judge Verification Protocol

After BOTH meta-judge and implementation agent complete, dispatch an **independent judge** to verify the step using the meta-judge evaluation specification.

CRITICAL: Provide to the judge EXACT meta-judge's evaluation specification YAML, do not skip or add anything, do not modify it in any way, do not shorten or summarize any text in it!

##### 3.4.1 Analyze the Pre-existing Changes Section

Before dispatching the judge for each step, assess whether there are pre-existing changes in the codebase that the judge needs to be aware of. The "Pre-existing Changes" section prevents the judge from confusing prior modifications with the current step's implementation agent's work.

**When to include:**

- Previous steps' changes from the SAME do-in-steps run (steps 1..N-1 when judging step N) — this is the most common case in sequential execution. When running step N, the judge MUST know about changes from steps 1..N-1 as pre-existing. Each completed step's output (files created/modified, key changes) becomes pre-existing context for subsequent step judges. 
- Previous do-in-steps or do-and-judge task runs completed earlier in the same session
- User's manual modifications made before invoking the skill (visible from conversation context or in git)
- Changes from other tools or agents that ran before this task

**When to omit:**

- This is step 1 with no known prior changes (no earlier session tasks, no user modifications) — omit the section entirely
- On retries within the SAME step, do NOT include the implementation agent's own previous attempt as "pre-existing changes" — those are part of the current step's iteration cycle

**Content guidelines:**

- Use a high-level summary: task description, list of affected files/modules, general nature of changes (created, modified, deleted)
- Do NOT include code blocks, diffs, or line-level details — keep it concise
- Label each source clearly: "Step 1: {description}", "Step 2: {description}", "User modifications (before current task)", etc.
- If multiple sources of pre-existing changes exist, use separate subsections for each (one per completed step, plus any external sources)
- Leverage the Context Passing Protocol output (section 3.1) — the "Completed Steps Summary" already tracks what each step produced

CRITICAL: avoid reading full codebase or git history, just use high-level git diff/status to determine which files were changed, or use conversation context and completed step summaries to determine pre-existing changes.

**Prompt template for step judge:**

```markdown
You are evaluating Step {N}/{total}: {subtask_name} against an evaluation specification produced by the meta judge.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## Original Task
{overall_task_description}

## Step Requirements
{subtask_description}
- Input: {what this step receives}
- Expected output: {what this step should produce}

## Previous Steps Context
{Summary of what previous steps accomplished}

{IF pre-existing changes are known (previous steps, prior tasks, or user modifications), include the following section — otherwise omit entirely}

## Pre-existing Changes (Context Only)

The following changes were made BEFORE the current step's implementation agent started working. They are NOT part of the current step's output. Focus your evaluation on the current step's changes. Only verify pre-existing changed files/logic if they directly relate to the current step's requirements.

### {Source of changes: e.g., "Step 1: {step description}" or "Previous Task: {task description}" or "User modifications (before current task)"}
{High-level summary: what was done, which files/modules were created or modified}

### {Additional source if applicable}
{High-level summary}

{END conditional section}

## Evaluation Specification

```yaml
{meta-judge's evaluation specification YAML}
```

## Implementation Output
{Path to files modified by implementation agent}
{Context for Next Steps section from implementation agent}

## Instructions

Follow your full judge process as defined in your agent instructions!

## Output

CRITICAL: You must reply with this exact structured evaluation report format in YAML at the START of your response!
```

CRITICAL: NEVER provide score threshold, in any format, including `threshold_pass` or anything different. Judge MUST not know what threshold for score is, in order to not be biased!!!

**Dispatch:**

```
Use Task tool:
  - description: "Judge Step {N}/{total}: {subtask_name}"
  - prompt: {judge verification prompt with exact meta-judge specification YAML, and Pre-existing Changes section if applicable}
  - model: {judge model — the user's `--model` if one was passed; otherwise MUST equal this step's current implementation model, including after escalation}
  - subagent_type: "sadd:judge"
```

#### 3.5 Dispatch, Verify, and Iterate

For each subtask in sequence:

```
1. Dispatch meta-judge AND implementation agent IN PARALLEL (single message, 2 tool calls):
   Tool call 1 (meta-judge — MUST be first):
     Use Task tool:
       - description: "Meta-judge Step {N}/{total}: {subtask_name}"
       - prompt: {meta-judge prompt with step requirements and context}
       - model: {meta-judge model — the user's `--model` if one was passed; otherwise the same tier as this step's implementation, or one tier up per Role Pairing}
       - subagent_type: "sadd:meta-judge"

   Tool call 2 (implementation):
     Use Task tool:
       - description: "Step {N}/{total}: {subtask_name}"
       - prompt: {constructed prompt with CoT + task + previous context + self-critique}
       - model: {implementation model — the user's `--model` if one was passed; otherwise the model selected for this step}
       - subagent_type: "{selected agent type}"

2. Wait for BOTH to complete. Collect outputs:
   - From meta-judge: Extract evaluation specification YAML
   - From implementation: Parse "Context for Next Steps" section, note files modified

3. Dispatch judge sub-agent (with this step's meta-judge specification):
   Use Task tool:
     - description: "Judge Step {N}/{total}: {subtask_name}"
     - prompt: {judge verification prompt with step requirements, implementation output, and meta-judge specification YAML}
     - model: {judge model — the user's `--model` if one was passed; otherwise MUST equal this step's current implementation model, including after escalation}
     - subagent_type: "sadd:judge"

4. Parse judge verdict (DO NOT read full report):
   Extract from judge reply:
   - VERDICT: PASS or FAIL
   - SCORE: X.X/5.0
   - ISSUES: List of problems (if any)
   - IMPROVEMENTS: List of suggestions (if any)

5. Decision based on verdict:

   If score ≥4.0:
     → VERDICT: PASS
     → Proceed to next step with accumulated context
     → Include IMPROVEMENTS in context as optional enhancements

   If 3.0 ≤ score <4.0 and NOT STRICT_MODE:
     → Apply the Iteration Discretion Rule (3.6)
       → accepted → VERDICT: PASS (report outstanding issues and proceed)
       → declined → VERDICT: FAIL → go to "Check retry count" below

   Otherwise (score <3.0, or score <4.0 with STRICT_MODE):
     → VERDICT: FAIL
     → Check retry count for this step

     If retries < 3:
       → Decide this step's retry tier per "3.5.1 Model Escalation on Retry" below
         (per the Escalation Rule — bump BOTH, unless its sole hold exception applies)
       → Dispatch retry implementation agent at that tier with:
         - Original step requirements
         - Judge's ISSUES list as feedback
         - Path to judge report for details
         - Instruction to fix specific issues
       → Return to judge verification with SAME meta-judge specification from this step,
         dispatching the judge at the retry tier (judge always matches implementation)
       → Do NOT re-run meta-judge for retries, and do NOT re-tier it

     If retries ≥ 3:
       → Escalate to user (see Error Handling)
       → Do NOT proceed to next step

6. Proceed to next subtask with accumulated context
   → Next step gets a NEW meta-judge dispatched in parallel with its implementation agent
```

##### 3.5.1 Model Escalation on Retry

Before dispatching any retry you MUST decide this step's tier explicitly per the [Escalation Rule](#escalation-rule) — which governs in full, including its sole hold exception — and state the decision in your step report. Retry-specific anchors on top of it:

- **Trigger (1) is anchored at `score < 3.0`** here (or issues showing the model misunderstood the step rather than merely missing details).
- The retry's judge MUST be dispatched at the same tier as the retry implementation; the step's meta-judge is neither re-run nor re-tiered.
- The escalated tier applies to **this step's remaining attempts only** — the next step is re-assessed from scratch per [Phase 2](#phase-2-model-selection-for-each-subtask).
- If `opus` still fails, escalate to the user per [Error Handling](#if-step-fails-after-max-retries).

**Retry prompt template for implementation agent:**

```markdown
## Retry Required: Step {N}/{total}

Your previous implementation did not pass judge verification.

<original_requirements>
{subtask_description}
</original_requirements>

<judge_feedback>
VERDICT: FAIL
SCORE: {score}/5.0
ISSUES:
{list of issues from judge}

Full report available at: {path_to_judge_report}
</judge_feedback>

<your_previous_output>
{files modified in previous attempt}
</your_previous_output>

Instructions:
Let's fix the identified issues step by step.

1. First, review each issue the judge identified
2. For each issue, determine the root cause
3. Plan the fix for each issue
4. Implement ALL fixes
5. Verify your fixes address each issue
6. Provide updated "Context for Next Steps" section

CRITICAL: Focus on fixing the specific issues identified. Do not rewrite everything.
```

#### 3.6 Iteration Discretion Rule

Your main task is to COMPLETE the task within target quality, and iteration effort MUST stay proportionate to each step's size. Two failure modes are equally real:

- Burning retries and context on nitpicks so the overall task never completes → **the task is failed**.
- Accepting a step whose quality is genuinely too poor to be considered complete → **an even worse failure**.

Apply to every judge score:

- **`score < 3.0` → FAIL, unconditionally. No discretion.** Retry with judge feedback until the step passes or max retries is reached.
- **`3.0 <= score < 4.0` → discretion band.** ONLY inside this band MAY you decide that a step below the `4.0` target is acceptable. The fixed `4.0` target puts the effective floor at `3.0`, so no separate bounded-drop guard is needed.
- Inside the band, when the outstanding issues are ONLY low/medium priority (any High or Critical finding removes discretion entirely) AND none of them breaks a target requirement of the step or causes a meaningful defect (i.e. they are nitpicks), you MUST reason FIRST — before dispatching a retry — about whether another attempt is worth the time and context cost.
- **At most ONE nitpick-driven retry**, and it counts against the retry budget. If it again surfaces only nitpicks, you MUST mark the step PASS (`ACCEPTED`), carry the outstanding issues forward in the accumulated context, report them in the final summary, and continue with the next step. If it returns a score below `3.0`, the unconditional-FAIL rule applies instead.
- You MUST be critical, NOT lenient. Stopping short of target MUST be an intentional decision grounded in the absence of real, requirement-breaking issues — later steps build on this one. A genuine blocking issue that prevents completing the step within max retries MUST be escalated as a failure, never papered over.
- **If `STRICT_MODE` is true, this whole rule is DISABLED**: stop only when `score >= 4.0` or max retries is reached. `--strict` changes nothing else — the `4.0` target, the max-retry limit, the `< 3.0` unconditional FAIL and meta-judge/judge dispatch are unaffected.

### Phase 4: Final Summary and Report

After all subtasks complete and pass verification, reply with a comprehensive report:

```markdown
## Sequential Execution Summary

**Overall Task:** {original task description}
**Total Steps:** {count}
**Total Agents:** {meta_judges(one per step) + implementation_agents + judge_agents + retry_agents}
**Strict Mode:** {STRICT_MODE}

### Step-by-Step Results

| Step | Subtask | Model | Judge Score | Retries | Status |
|------|---------|-------|-------------|---------|--------|
| 1 | {name} | {model} | {X.X}/5.0 | {0-3} | PASS |
| 2 | {name} | {model} | {X.X}/5.0 | {0-3} | PASS |
| ... | ... | ... | ... | ... | ... |

Status is `PASS` (score >= 4.0), `ACCEPTED` (below target per the [Iteration Discretion Rule](#36-iteration-discretion-rule) — list the outstanding nitpicks under Follow-up Recommendations), or `FAILED`.

**Model** is the tier the step finished at; when [escalation](#351-model-escalation-on-retry) fired, record it as `{starting tier} → {final tier}`.

### Files Modified (All Steps)
- {file1}: {what changed, which step}
- {file2}: {what changed, which step}
...

### Key Decisions Made
- Step 1: {decision and rationale}
- Step 2: {decision and rationale}
...

### Integration Points
{How the steps connected and built upon each other}

### Judge Verification Summary
| Step | Initial Score | Final Score | Issues Fixed |
|------|---------------|-------------|--------------|
| 1 | {X.X} | {X.X} | {count or "None"} |
| 2 | {X.X} | {X.X} | {count or "None"} |

### Meta-Judge Specifications
One evaluation specification generated per step (in parallel with implementation), reused across retries within each step.


### Follow-up Recommendations
{Any improvements suggested by judges, tests to run, or manual verification needed}
```

## Error Handling

### If Judge Verification Fails (Score <4.0)

The judge-verified iteration loop handles most failures automatically (a score in `3.0..4.0` is FAIL only after the [Iteration Discretion Rule](#36-iteration-discretion-rule) declines to accept it):

```
Judge FAIL (Retry Available):
  1. Parse ISSUES from judge verdict
  2. Dispatch retry implementation agent with feedback
  3. Re-verify with judge (using same step's meta-judge specification — do NOT re-run meta-judge)
  4. Repeat until PASS or max retries (3)
```

### If Step Fails After Max Retries

When a step fails judge verification three times:

1. **STOP** - Do not proceed with broken foundation
2. **Report** - Provide failure analysis:
   - Original step requirements
   - All judge verdicts and scores
   - Persistent issues across retries
3. **Escalate** - Present options to user:
   - Provide additional context/guidance for retry
   - Re-run this step at the next model tier up (omit this option if the step already reached `opus`)
   - Modify step requirements
   - Skip step (if optional)
   - Abort and report partial progress
4. **Wait** - Do NOT proceed without user decision

**Escalation Report Format:**

```markdown
## Step {N} Failed Verification (Max Retries Exceeded)

### Step Requirements
{subtask_description}

### Verification History
| Attempt | Score | Key Issues |
|---------|-------|------------|
| 1 | {X.X}/5.0 | {issues} |
| 2 | {X.X}/5.0 | {issues} |
| 3 | {X.X}/5.0 | {issues} |
| 4 | {X.X}/5.0 | {issues} |

### Persistent Issues
{Issues that appeared in multiple attempts}

### Judge Reports
- .specs/reports/{task-name}-step-{N}-attempt-1.md
- .specs/reports/{task-name}-step-{N}-attempt-2.md
- .specs/reports/{task-name}-step-{N}-attempt-3.md
- .specs/reports/{task-name}-step-{N}-attempt-4.md

### Options
1. **Provide guidance** - Give additional context for another retry
2. **Escalate the tier** - Re-run this step's implementation and judge one tier up (omit this option if the step already reached `opus`)
3. **Modify requirements** - Simplify or clarify step requirements
4. **Skip step** - Mark as skipped and continue (if non-critical)
5. **Abort** - Stop execution and preserve partial progress

Awaiting your decision...
```

**Never:**

- Continue past a failed step after max retries
- Skip judge verification to "save time"
- Ignore persistent issues across retries
- Make assumptions about what might have worked

### If Context is Missing

1. **Do NOT guess** what previous steps produced
2. **Re-examine** previous step output for missing information
3. **Check judge reports** - they may have noted missing elements
4. **Dispatch clarification sub-agent** if needed to extract missing context
5. **Update context passing** for future similar tasks

### If Steps Conflict

1. **Stop execution** at conflict point
2. **Analyze:** Was decomposition incorrect? Are steps actually dependent?
3. **Check judge feedback** - judges may have flagged integration issues
4. **Options:**
   - Re-order steps if dependency was missed
   - Combine conflicting steps into one
   - Add reconciliation step between conflicting steps

## Examples

### Example 1: Sequential Steps Building on Each Other (Pre-existing Changes from Previous Steps)

**Input:**

```
/do-in-steps implement user management feature
```

**Phase 1 - Decomposition:**

| Step | Subtask | Depends On | Complexity | Type | Output |
|------|---------|------------|------------|------|--------|
| 1 | Create User model and database schema | - | Medium | Implementation | User model, migration files |
| 2 | Add CRUD endpoints for users | Step 1 | Medium | Implementation | REST API routes, controller |
| 3 | Add authentication integration | Steps 1,2 | High | Implementation | Auth middleware, JWT handling |

**Phase 2 - Model Selection:**

| Step | Subtask | Model | Rationale |
|------|---------|-------|-----------|
| 1 | Create User model and schema | sonnet | Code writing on an established pattern; the greenfield `users` table is reversible, so the irreversible-migration trigger does not fire |
| 2 | Add CRUD endpoints | sonnet | Code writing in one module; "adding to a public API" is NOT on the exhaustive critical list |
| 3 | Add authentication integration | opus | opus is EARNED — the critical trigger fires on auth (JWT issuance and route protection) |

**Phase 3 - Execution with Pre-existing Changes Accumulation:**

```
Step 1: Create User model and database schema
  Parallel dispatch: Meta-judge + Implementation
  Judge Verification (with step 1 meta-judge spec):
    NOTE: No pre-existing changes — this is step 1 with no prior session tasks.
    The "Pre-existing Changes" section is OMITTED from the judge prompt.

    Judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ You are evaluating Step 1/3: Create User model and
    │ database schema against an evaluation specification
    │ produced by the meta judge.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## Original Task
    │ Implement user management feature
    │
    │ ## Step Requirements
    │ Create User model and database schema with proper
    │ fields and relationships.
    │
    │ ## Previous Steps Context
    │ None (first step)
    │
    │ ## Evaluation Specification
    │ ```yaml
    │ {meta-judge's evaluation specification YAML}
    │ ```
    │
    │ ## Implementation Output
    │ Files: src/models/User.ts (new), migrations/001_create_users.ts (new)
    │ Key changes: Created User model with id, email, name, passwordHash...
    │
    │ ## Instructions
    │ Follow your full judge process...
    └─────────────────────────────────────────────────────────

  → Judge (Sonnet — same tier as implementation): PASS, SCORE: 4.2/5.0
  → Context passed forward: User model fields, migration file paths

Step 2: Add CRUD endpoints for users
  Parallel dispatch: Meta-judge + Implementation (both Sonnet)
  Judge Verification (with step 2 meta-judge spec):
    NOTE: Pre-existing changes detected — Step 1 created the User model.
    Include "Pre-existing Changes" section so the judge does not confuse
    Step 1's files with Step 2's implementation work.

    Judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ You are evaluating Step 2/3: Add CRUD endpoints for
    │ users against an evaluation specification produced by
    │ the meta judge.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## Original Task
    │ Implement user management feature
    │
    │ ## Step Requirements
    │ Add CRUD endpoints (create, read, update, delete) for
    │ user management with proper validation and error handling.
    │
    │ ## Previous Steps Context
    │ Step 1 created User model with fields: id, email, name,
    │ passwordHash, createdAt, updatedAt.
    │
    │ ## Pre-existing Changes (Context Only)
    │
    │ The following changes were made BEFORE the current
    │ step's implementation agent started working. They are
    │ NOT part of the current step's output. Focus your
    │ evaluation on the current step's changes. Only verify
    │ pre-existing changed files/logic if they directly
    │ relate to the current step's requirements.
    │
    │ ### Step 1: "Create User model and database schema"
    │ The following files were created as part of Step 1:
    │ - src/models/User.ts (new) - User model with fields:
    │   id, email, name, passwordHash, createdAt, updatedAt
    │ - migrations/001_create_users.ts (new) - Database
    │   migration for users table
    │
    │ These files exist in the codebase and may be referenced
    │ by the current step, but evaluate only the changes made
    │ by Step 2's implementation agent.
    │
    │ ## Evaluation Specification
    │ ```yaml
    │ {meta-judge's evaluation specification YAML}
    │ ```
    │
    │ ## Implementation Output
    │ Files: src/controllers/UserController.ts (new),
    │        src/routes/users.ts (new), src/app.ts (modified)
    │ Key changes: Added REST endpoints for user CRUD...
    │
    │ ## Instructions
    │ Follow your full judge process...
    └─────────────────────────────────────────────────────────

  → Judge (Sonnet — same tier as implementation): PASS, SCORE: 4.4/5.0
  → Context passed forward: API routes, controller patterns

Step 3: Add authentication integration
  Parallel dispatch: Meta-judge + Implementation (both Opus — critical trigger)
  Judge Verification (with step 3 meta-judge spec):
    NOTE: Pre-existing changes include BOTH Step 1 AND Step 2.
    The judge needs to know about all prior steps' output.

    Judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ You are evaluating Step 3/3: Add authentication
    │ integration against an evaluation specification
    │ produced by the meta judge.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## Original Task
    │ Implement user management feature
    │
    │ ## Step Requirements
    │ Add JWT-based authentication with login/register
    │ endpoints and middleware for protecting user routes.
    │
    │ ## Previous Steps Context
    │ Step 1 created User model. Step 2 added CRUD endpoints
    │ at /api/users with UserController.
    │
    │ ## Pre-existing Changes (Context Only)
    │
    │ The following changes were made BEFORE the current
    │ step's implementation agent started working. They are
    │ NOT part of the current step's output. Focus your
    │ evaluation on the current step's changes. Only verify
    │ pre-existing changed files/logic if they directly
    │ relate to the current step's requirements.
    │
    │ ### Step 1: "Create User model and database schema"
    │ - src/models/User.ts (new) - User model with fields:
    │   id, email, name, passwordHash, createdAt, updatedAt
    │ - migrations/001_create_users.ts (new) - Database
    │   migration for users table
    │
    │ ### Step 2: "Add CRUD endpoints for users"
    │ - src/controllers/UserController.ts (new) - REST
    │   controller with create, read, update, delete handlers
    │ - src/routes/users.ts (new) - Express router for
    │   /api/users endpoints
    │ - src/app.ts (modified) - Registered user routes
    │
    │ These files exist in the codebase and may be modified
    │ by the current step, but evaluate only the changes made
    │ by Step 3's implementation agent.
    │
    │ ## Evaluation Specification
    │ ```yaml
    │ {meta-judge's evaluation specification YAML}
    │ ```
    │
    │ ## Implementation Output
    │ Files: src/auth/AuthMiddleware.ts (new),
    │        src/routes/auth.ts (new), src/app.ts (modified),
    │        src/routes/users.ts (modified)
    │ Key changes: Added JWT auth with login/register...
    │
    │ ## Instructions
    │ Follow your full judge process...
    └─────────────────────────────────────────────────────────

  → Judge (Opus — same tier as implementation): PASS, SCORE: 4.1/5.0
```

**Final Summary:**

- Total Agents: 10 (3 meta-judges + 3 implementations + 0 retries + 3 judges)
- Pre-existing Changes Progression:
  - Step 1 judge: None
  - Step 2 judge: Step 1 output (2 files)
  - Step 3 judge: Steps 1+2 output (5 files)
- All Judge Scores: 4.2, 4.4, 4.1

---

### Example 2: User-Modified Codebase + Sequential Steps (Mixed Pre-existing Changes Sources)

**Scenario:**

The user has been working on a payment processing module during the conversation. They modified several files (added a new PaymentGateway interface, updated configuration) before invoking do-in-steps.

**Input:**

```
/do-in-steps fix and improve payment processing
```

**Phase 1 - Decomposition:**

| Step | Subtask | Depends On | Complexity | Type | Output |
|------|---------|------------|------------|------|--------|
| 1 | Fix payment validation bugs | - | Medium | Bug fix | Corrected validation logic |
| 2 | Add retry logic for failed payments | Step 1 | High | Implementation | Retry mechanism with backoff |

**Phase 2 - Model Selection:**

| Step | Subtask | Model | Rationale |
|------|---------|-------|-----------|
| 1 | Fix payment validation bugs | opus | opus is EARNED — small in scope, but precedence makes criticality override size: payments are on the critical list |
| 2 | Add retry logic for failed payments | opus | opus is EARNED — payments (critical) plus retry/backoff sequencing around money movement (complex logic) |

Both steps land on `opus` because the *domain* earns it, not because the run does — see Example 3 for a chain that mixes tiers.

**Phase 3 - Execution with Mixed Pre-existing Changes:**

```
Step 1: Fix payment validation bugs
  Parallel dispatch: Meta-judge + Implementation (both Opus — critical trigger)
  Judge Verification (Opus, with step 1 meta-judge spec):
    NOTE: Pre-existing changes detected from USER modifications.
    The user modified payment files before this task — include those
    so the judge focuses only on the bug fix, not the user's prior work.

    Judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ You are evaluating Step 1/2: Fix payment validation
    │ bugs against an evaluation specification produced by
    │ the meta judge.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## Original Task
    │ Fix and improve payment processing
    │
    │ ## Step Requirements
    │ Fix validation bugs in payment amount and currency
    │ checks that allow invalid transactions to proceed.
    │
    │ ## Previous Steps Context
    │ None (first step)
    │
    │ ## Pre-existing Changes (Context Only)
    │
    │ The following changes were made BEFORE the current
    │ step's implementation agent started working. They are
    │ NOT part of the current step's output. Focus your
    │ evaluation on the current step's changes. Only verify
    │ pre-existing changed files/logic if they directly
    │ relate to the current step's requirements.
    │
    │ ### User modifications (before current task)
    │ The user made changes to the following files/modules
    │ before this task was started:
    │ - src/payments/PaymentGateway.ts (new) - Payment
    │   gateway interface definition
    │ - src/payments/StripeAdapter.ts (modified) - Updated
    │   to implement new PaymentGateway interface
    │ - src/config/payment.config.ts (modified) - Added
    │   gateway configuration settings
    │
    │ The current task focuses on fixing validation bugs.
    │ Pre-existing changes to payment files may overlap with
    │ the current step's scope — evaluate whether the
    │ implementation agent's changes correctly fix the bugs
    │ without breaking the pre-existing modifications.
    │
    │ ## Evaluation Specification
    │ ```yaml
    │ {meta-judge's evaluation specification YAML}
    │ ```
    │
    │ ## Implementation Output
    │ Files: src/payments/PaymentValidator.ts (modified),
    │        tests/payments/PaymentValidator.test.ts (modified)
    │ Key changes: Fixed amount validation to reject negative
    │ values, added currency code format check...
    │
    │ ## Instructions
    │ Follow your full judge process...
    └─────────────────────────────────────────────────────────

  → VERDICT: PASS, SCORE: 4.3/5.0
  → Context passed forward: Validation fixes, affected files

Step 2: Add retry logic for failed payments
  Parallel dispatch: Meta-judge + Implementation (both Opus — critical trigger)
  Judge Verification (Opus, with step 2 meta-judge spec):
    NOTE: Pre-existing changes now include BOTH the user's modifications
    AND Step 1's output. The judge needs both sources to correctly
    attribute changes.

    Judge prompt sent:
    ┌─────────────────────────────────────────────────────────
    │ You are evaluating Step 2/2: Add retry logic for failed
    │ payments against an evaluation specification produced by
    │ the meta judge.
    │
    │ CLAUDE_PLUGIN_ROOT=...
    │
    │ ## Original Task
    │ Fix and improve payment processing
    │
    │ ## Step Requirements
    │ Add retry mechanism with exponential backoff for failed
    │ payment transactions, with configurable max retries.
    │
    │ ## Previous Steps Context
    │ Step 1 fixed payment validation bugs in
    │ PaymentValidator.ts (amount and currency checks).
    │
    │ ## Pre-existing Changes (Context Only)
    │
    │ The following changes were made BEFORE the current
    │ step's implementation agent started working. They are
    │ NOT part of the current step's output. Focus your
    │ evaluation on the current step's changes. Only verify
    │ pre-existing changed files/logic if they directly
    │ relate to the current step's requirements.
    │
    │ ### User modifications (before current task)
    │ - src/payments/PaymentGateway.ts (new) - Payment
    │   gateway interface definition
    │ - src/payments/StripeAdapter.ts (modified) - Updated
    │   to implement new PaymentGateway interface
    │ - src/config/payment.config.ts (modified) - Added
    │   gateway configuration settings
    │
    │ ### Step 1: "Fix payment validation bugs"
    │ - src/payments/PaymentValidator.ts (modified) - Fixed
    │   amount validation and currency code format checks
    │ - tests/payments/PaymentValidator.test.ts (modified) -
    │   Added regression tests for validation fixes
    │
    │ These files exist in the codebase and may be modified
    │ by the current step, but evaluate only the changes made
    │ by Step 2's implementation agent.
    │
    │ ## Evaluation Specification
    │ ```yaml
    │ {meta-judge's evaluation specification YAML}
    │ ```
    │
    │ ## Implementation Output
    │ Files: src/payments/PaymentRetryService.ts (new),
    │        src/payments/StripeAdapter.ts (modified),
    │        src/config/payment.config.ts (modified),
    │        tests/payments/PaymentRetryService.test.ts (new)
    │ Key changes: Added PaymentRetryService with exponential
    │ backoff, integrated into StripeAdapter...
    │
    │ ## Instructions
    │ Follow your full judge process...
    └─────────────────────────────────────────────────────────

  → VERDICT: PASS, SCORE: 4.5/5.0
```

**Final Summary:**

- Total Agents: 7 (2 meta-judges + 2 implementations + 0 retries + 2 judges)
- Pre-existing Changes Progression:
  - Step 1 judge: User modifications (3 files)
  - Step 2 judge: User modifications (3 files) + Step 1 output (2 files)
- All Judge Scores: 4.3, 4.5

---

### Example 3: Multi-file Refactoring with Escalation

**Input:**

```
/do-in-steps Rename 'userId' to 'accountId' across the codebase - this affects interfaces, implementations, and callers
```

**Phase 1 - Decomposition:**

| Step | Subtask | Depends On | Complexity | Type | Output |
|------|---------|------------|------------|------|--------|
| 1 | Update interface definitions | - | High | Refactoring | Updated interfaces |
| 2 | Update implementations of those interfaces | Step 1 | Low | Refactoring | Updated implementations |
| 3 | Update callers and consumers | Step 2 | Low | Refactoring | Updated caller files |
| 4 | Update tests | Step 3 | Low | Testing | Updated test files |
| 5 | Update documentation | Step 4 | Low | Documentation | Updated docs |

**Phase 2 - Model Selection:**

| Step | Subtask | Model | Rationale |
|------|---------|-------|-----------|
| 1 | Update interfaces | opus | opus is EARNED — a shared contract changes, which is an `opus` trigger at any file count |
| 2 | Update implementations | haiku | Mechanical-breadth carve-out: one rule-driven rename repeated per file, tiered on a single occurrence |
| 3 | Update callers | haiku | Same carve-out — mechanical rename, no logic or contract change |
| 4 | Update tests | haiku | Mechanical test fixes mirroring the rename |
| 5 | Update documentation | haiku | Single-purpose text correction, no code |

**Phase 3 - Execution with Escalation (each step has parallel meta-judge + implementation):**

```
Step 1: Update interfaces
  Parallel dispatch: Meta-judge + Implementation (both Opus — shared contract change)
  → Judge (Opus, sadd:judge, with step 1 meta-judge spec): PASS, 4.3/5.0

Step 2: Update implementations
  Parallel dispatch: Meta-judge + Implementation (both Haiku)
    NOTE: Step 1's opus tier does NOT carry forward — Step 2 is tiered on
    its own merits (mechanical rename).
  → Judge (Haiku, sadd:judge, with step 2 meta-judge spec): PASS, 4.0/5.0

Step 3: Update callers (Problem Detected — model escalation within the step)
  Parallel dispatch: Meta-judge (Haiku) + Implementation (Haiku)
  Attempt 1 (Haiku impl + Haiku judge): Judge FAIL, 2.5/5.0
    → ISSUES: Missed 12 occurrences in legacy module
    → score < 3.0 → trigger (1) fires. Missed occurrences read as a capability
      gap, not a narrow fixable defect, so the sole hold exception does not
      apply → mandatory bump: haiku → sonnet.
      Meta-judge NOT re-run, NOT re-tiered — same spec reused.
  Attempt 2 (Sonnet impl + Sonnet judge, same step 3 meta-judge spec): FAIL, 2.8/5.0
    → ISSUES: Still missing 4 occurrences, found new deprecated API usage
    → still < 3.0 → still a capability gap, not a narrow fixable defect →
      mandatory bump again: sonnet → opus
  Attempt 3 (Opus impl + Opus judge, same spec): FAIL, 3.2/5.0
    → ISSUES: 2 occurrences in dynamically generated code
    → at the `opus` ceiling — no bump available regardless of the hold
      exception; retry at `opus` with exact feedback.
  Attempt 4 (Opus impl + Opus judge, same spec): FAIL, 3.3/5.0
    → ISSUES: Dynamic code generation still not fully addressed

  ESCALATION TO USER:
  "Step 3 failed after 4 attempts (haiku → sonnet → opus). Persistent issue:
   Dynamic code generation in LegacyAdapter.ts generates 'userId' at runtime.
   Options: 1) Provide guidance, 2) Modify requirements, 3) Skip, 4) Abort"
  (Tier escalation is NOT offered as an option — already at the opus ceiling.)

  User response: "Update LegacyAdapter to use string template with accountId"

  Attempt 5 (with user guidance, Opus, same step 3 meta-judge spec): Judge PASS, 4.1/5.0

Step 4-5: Each with parallel meta-judge + implementation, complete without issues
  NOTE: Step 3's escalation to opus is scoped to Step 3. Steps 4 and 5 are
  re-assessed from scratch and both run at Haiku.
```

Total Agents: 20 (5 meta-judges + 5 implementations + 5 retries + 5 judges)

---

## Best Practices

### Task Decomposition

- **Be explicit:** Each subtask should have a clear, verifiable outcome
- **Define verification points:** What should the judge check for each step?
- **Minimize steps:** Combine related work; don't over-decompose
- **Validate dependencies:** Ensure each step has what it needs from previous steps
- **Plan context:** Identify what context needs to pass between steps

### Model Selection

The rules govern in the [Model Selection Policy](#model-selection-policy); these are the habits that make them stick:

- **Justify out loud, per step** - state scope, complexity and risk plus the resulting tier before dispatching each step; this is the highest-leverage decision in the run
- **`opus` is earned, never a hedge** - resolve every overlap and tie by the [Selection Rules](#selection-rules) precedence and tie-breaker, never by instinct
- **Tier each step on its own merits** - a chain mixes tiers; a neighbouring step's tier (or an escalated one) is not evidence about this step
- **One tier across roles** - raise only the criteria-setter (meta-judge), and only for a non-obvious step ([Role Pairing](#role-pairing))
- **Escalate on evidence** - a clearly-too-low attempt or a user quality complaint ([Escalation Rule](#escalation-rule)), scoped to the failing step

### Context Passing Guidelines

| Scenario | What to Pass | What to Omit |
|----------|--------------|--------------|
| Interface defined in step 1 | Full interface definition | Implementation details |
| Implementation in step 2 | Key patterns, file locations | Internal logic |
| Integration in step 3 | Usage patterns, entry points | Step 2 internal details |
| Judge feedback for retry | ISSUES list, report path | Full report contents |

**Keep context focused:**

- Pass what the next step NEEDS to build on
- Omit internal details that don't affect subsequent steps
- Highlight patterns/conventions to maintain consistency
- Include judge IMPROVEMENTS as optional enhancements
- **Track pre-existing changes** - Pass context about prior modifications (including previous steps) to the judge to prevent attribution confusion

### Meta-Judge + Judge Verification

- **Never skip meta-judge** - Tailored evaluation criteria produce better judgments than generic ones
- **One meta-judge per step** - Each step gets its own meta-judge dispatched in parallel with implementation
- **Reuse meta-judge spec across retries within a step** - On retry, reuse the same step's meta-judge specification; do NOT re-run meta-judge
- **New meta-judge for each new step** - Different steps have different requirements, so each gets a fresh meta-judge
- **Meta-judge FIRST in parallel dispatch** - Always the first tool call in the message
- **Parse only headers from judge** - Don't read full reports to avoid context pollution
- **Include CLAUDE_PLUGIN_ROOT** - Both meta-judge and judge need the resolved plugin root path
- **Meta-judge YAML** - Pass only the meta-judge YAML to the judge, do not add any additional text or comments to it!
- **After self-critique:** Judge reviews work that already passed internal verification
- **Independent verification:** Judge is different agent than implementer
- **Structured output:** Always parse VERDICT/SCORE from reply, not full report
- **Max retries:** 3 attempts before escalating to user
- **Feedback loop:** Pass judge ISSUES to retry implementation agent
- **Return to judge verification with same step's meta-judge specification** on retry

### Quality Assurance

- **Two-layer verification:** Self-critique (internal) + Judge (external)
- **Self-critique first:** Implementation agents verify own work before submission
- **External judge second:** Independent judge catches blind spots self-critique misses
- **Iteration loop:** Retry with feedback until passing or max retries
- **Proportionate iteration:** Apply the [Iteration Discretion Rule](#36-iteration-discretion-rule) — at most ONE nitpick-driven retry, never below `3.0`, disabled by `--strict`
- **Chain validation:** Judges check integration with previous steps
- **Escalation:** Don't proceed past failed steps - get user input
- **Final integration test:** After all steps, verify the complete change works together

## Context Format Reference

### Implementation Agent Output Format

```markdown
## Context for Next Steps

### Files Modified
- `src/dto/UserDTO.ts` (new file)
- `src/services/UserService.ts` (modified)

### Key Changes Summary
- Created UserDTO with fields: id (string), name (string), email (string), createdAt (Date)
- UserDTO includes static `fromUser(user: User): UserDTO` factory method
- Added `toDTO()` method to User class for convenience

### Decisions That Affect Later Steps
- Used class-based DTO (not interface) to enable transformation methods
- Opted for explicit mapping over automatic serialization for better control

### Warnings for Subsequent Steps
- UserDTO does NOT include password field - ensure no downstream code expects it
- The `createdAt` field is formatted as ISO string in JSON serialization

### Verification Points
- TypeScript compiles without errors
- UserDTO.fromUser() correctly maps all User properties
- Existing service tests still pass
```

### Judge Verdict Format (Structured Header)

```markdown
---
VERDICT: PASS
SCORE: 4.2/5.0
ISSUES:
  - None
IMPROVEMENTS:
  - Consider adding input validation to fromUser() method
  - Add JSDoc comments for better IDE support
---

## Detailed Evaluation
[Evidence and analysis following meta-judge specification rubrics...]
```

### Judge Verdict Format (FAIL Example)

```markdown
---
VERDICT: FAIL
SCORE: 2.8/5.0
ISSUES:
  - Missing User->UserDTO mapping logic in getUser() method
  - Return type annotation changed but actual return value still returns User object
  - No null handling for optional User fields
IMPROVEMENTS:
  - Add static fromUser() factory method to UserDTO
  - Implement toDTO() as instance method on User class
---
```

**Key Insight:** Complex tasks with dependencies benefit from sequential execution where each step operates in a fresh context while receiving only the relevant outputs from previous steps. **Per-step meta-judge evaluation specifications** ensure tailored evaluation criteria specific to each step's requirements, while running in parallel with implementation for speed. **External judge verification** catches blind spots that self-critique misses, while the **iteration loop** (reusing the same step's meta-judge spec) ensures quality before proceeding. This prevents both context pollution and error propagation.
