---
name: do-in-parallel
description: Run independent tasks concurrently across multiple files or targets using parallel sub-agents, with per-task model selection and LLM-as-a-judge verification. Use when tasks do not depend on each other and can run side by side.
argument-hint: Task description [--files "file1.ts,file2.ts,..."] [--targets "target1,target2,..."] [--model haiku|sonnet|opus] [--output <path>] [--strict]
---

# do-in-parallel

<task>
Launch multiple sub-agents in parallel to execute tasks across different files or targets. Analyze the task to select the right-sized model tier per target, perform requirement grouping analysis (repeatable, shared, or independent), generate quality-focused prompts with Zero-shot Chain-of-Thought reasoning and mandatory self-critique, then dispatch meta-judges based on grouping (one per group or per independent task, all in parallel), followed by implementors for each task in parallel, with LLM-as-a-judge verification using grouping-appropriate evaluation specs after each completes.
</task>

<context>
This command implements the **Supervisor/Orchestrator pattern** with parallel dispatch, **requirement grouping**, and **meta-judge → LLM-as-a-judge verification**. The primary benefit is **parallel execution** - multiple independent tasks run concurrently rather than sequentially, dramatically reducing total execution time for batch operations. Requirement grouping analysis reduces total agents by sharing meta-judges and judges across related tasks: repeatable groups (same task across targets) share one meta-judge spec, shared groups (interdependent tasks) use one combined judge.


Key benefits:
- **Parallel execution** - Multiple tasks run simultaneously
- **Requirement grouping** - Reduces meta-judges and judges by identifying repeatable and shared task patterns
- **Right-sized model** - Chosen per target by the [Model Selection Policy](#model-selection-policy): `sonnet`/`haiku` by default, `opus` only when earned
- **Fresh context** - Each sub-agent works with clean context window
- **Task-specific evaluation** - Each meta-judge produces tailored rubrics and checklists for its specific task or group
- **External verification** - Judge applies target-specific meta-judge specification mechanically — catches blind spots self-critique misses
- **Feedback loop** - Retry with specific issues identified by judge
- **Quality gate** - Work doesn't ship until it meets threshold

**Common use cases:**
- Apply the same refactoring across multiple files
- Run code analysis on several modules simultaneously
- Generate documentation for multiple components
- Execute independent transformations in parallel
</context>

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task` | Free-form text | **Required** | Task description to execute across targets |
| `--files` | `"file1,file2,..."` | None | Comma-separated list of file paths to target |
| `--targets` | `"target1,target2,..."` | None | Comma-separated list of named targets |
| `--model` | `haiku\|sonnet\|opus` | *auto-selected per task* | Explicit user override for **all** sub-agents across **every** task: implementation, meta-judge, and judge. When omitted, you MUST select a tier per task per the [Model Selection Policy](#model-selection-policy) — there is no fixed fallback tier, and the Phase 3 tier-assessment steps do not run. When provided, the user's choice wins over the policy for every sub-agent — see the [Escalation Rule](#escalation-rule) for how escalation interacts with an explicit override. |
| `--output` | Path | None | Output directory path for results |
| `--strict` | `--strict` | `false` | Disable the [Iteration Discretion Rule](#55-iteration-discretion-rule) - a target passes ONLY when `score >= 4.0`, otherwise retry until max retries is reached. |

Example: `/do-in-parallel Refactor error handling --files "src/a.ts,src/b.ts" --strict`

**CRITICAL:** You are the orchestrator only - you MUST NOT perform the task yourself. IF you read, write or run bash tools you failed task imidiatly. It is single most critical criteria for you. If you used anyting except sub-agents you will be killed immediatly!!!! Your role is to:

1. Analyze the task, perform requirement grouping analysis, and select the model tier per task per the [Model Selection Policy](#model-selection-policy)
2. Dispatch meta-judges in parallel based on grouping 
3. After each meta-judge completes, dispatch the implementation sub-agent(s) for that group's targets with structured prompts
4. After implementors complete, dispatch judges based on grouping 
5. Parse verdict and iterate if needed (max 3 retries per target; for shared groups, retry only failing tasks)
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
- Launch separate meta-judges for tasks that belong to the same repeatable or shared group
- Re-launch ALL implementation agents in a shared group when only some failed

**ALWAYS:**

- Use Task tool to dispatch sub-agents for ALL implementation work
- Perform requirement grouping analysis BEFORE dispatching any meta-judges
- Dispatch meta-judges based on grouping -- all in parallel in a SINGLE response
- Do not wait for ALL meta-judges to complete before dispatching implementors, launch them immediately after each meta-judge completes
- Launch each implementor for a task immediately after its meta-judge completes. If all meta-judges are completed, launch all implementation agents in SINGLE response
- Pass each target's specific meta-judge evaluation specification to its judge agent 
- For shared groups, dispatch ONE judge that reviews ALL related changes together
- Include `CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}` in prompts to meta-judge and judge agents
- Use Task tool to dispatch independent judges for verification
- Wait for each implementation to complete before dispatching its judge
- Parse only VERDICT/SCORE/ISSUES from judge output
- Iterate with feedback if verification fails (max 3 retries per target)
- Apply the [Iteration Discretion Rule](#55-iteration-discretion-rule) to every target verdict, unless `--strict` was provided
- For shared group retries, only re-launch the specific failing implementation agent(s), not the entire group
- Reuse same meta-judge specification for all retries (never re-run meta-judge)

## Model Selection Policy

Picking the model is the **single highest-leverage decision** you make — more than any prompt wording, it decides whether a target comes back correct and how long the batch takes. You MUST NOT treat it as a formality: name the tier and give a one-line justification before dispatching **each** target. Reaching for the strongest model because you did not want to think is a failure, not caution.

**Tier default:** `sonnet` and `haiku` are the default. `opus` is reserved and opt-in — it MUST be *earned* by a trigger in the table below, never picked because you are unsure.

**Per task, not per run:** a tier is chosen **independently for every task**, from that task's own scope, complexity and risk — the batch is no longer forced into one "same configuration for all parallel agents." Independent tasks are each tiered on their own merits. A repeatable group's shared meta-judge produces one reusable spec, but that does NOT force one tier: each task in the group keeps its own implementation and judge tier from the Selection Rules below, so a critical-domain target inside an otherwise-mechanical group can still land on `opus` while its siblings stay cheaper. A shared group's single judge reviews every task in the group together, so it runs at the HIGHEST current implementation tier among them (see [Role Pairing](#role-pairing)). A tier reached by one task (including one reached by escalation) MUST NOT be carried into sibling tasks or the next batch.

### Selection Rules

| Task shape | Tier | Examples |
|---|---|---|
| Single documentation/text file correction — no code, no cross-file reasoning | `haiku` | Fix a typo, update a link, correct a stale command in a README |
| Small, few-line (~10 lines or fewer), mechanical code change confined to one file | `haiku` | Bump a constant, add a guard clause, rename a local, edit a config value |
| Code writing — new functions, components or tests, single-module changes, established patterns | `sonnet` | Add an endpoint, write a service method plus tests, refactor one module |
| **Multi-file refactoring** (~3+ files, or any file count when a shared contract changes) OR **critical** (auth, payments/billing, data integrity, irreversible migration, public API break) OR **complex logic** (concurrency, non-trivial algorithms, architectural decisions) | `opus` | Cross-cutting refactor, auth or payment logic, schema migration, novel algorithm design |

**Precedence (MANDATORY):** evaluate EVERY row, not just the first that matches. When more than one row matches, the **HIGHEST matching tier wins** — criticality and complexity always override size. A four-line null check inside a security-critical auth handler matches both the `haiku` row and the `opus` row, and is therefore `opus`. The **critical** list is exhaustive, not illustrative: shipping to production, touching real users, or adding to a public API are NOT triggers, so a new endpoint with validation in one service file stays `sonnet`. **Mechanical-breadth carve-out:** breadth alone is not complexity. For a purely mechanical change — one identical, rule-driven edit repeated across targets, with no logic and no contract change — only the **multi-file trigger** does NOT apply; the **critical** and **complex logic** triggers still do. You MUST tier it on the content of a **single occurrence**, as if the task touched one file; mechanically renaming a symbol across 40 files is therefore `haiku`, but the same rename confined to `src/auth/` is `opus` — the critical trigger fires on that single occurrence regardless of breadth. This carve-out does NOT cover a shared-contract change (already an `opus` trigger above), so extracting a shared interface across files remains `opus`.

**Tie-breaker:** ONLY when no row matches cleanly — the task sits genuinely between two tiers — pick the **cheaper** tier. You MUST NOT bias up to `opus` to hedge; the [Escalation Rule](#escalation-rule) makes a cheap first guess recoverable, and one recovered task costs far less than over-provisioning every task.

### Role Pairing

Any model-assigned pipeline has up to three roles — **producer** (does the work), **criteria-setter** (defines what "correct" means), **evaluator** (checks the work against those criteria); in this skill they instantiate **per parallel task** as implementation / meta-judge / judge — a repeatable group shares one meta-judge across its tasks, and a shared group additionally shares one judge across its tasks. **Default: the SAME tier for all three roles of that task.**

**Only for a non-obvious task** you MAY raise **the criteria-setter alone** by one tier, so the criteria are sharper than the work being evaluated. *Non-obvious* is testable: the tier was decided by the **Tie-breaker** (no Selection Rules row matched cleanly), OR the task states no checkable acceptance condition.

| Pattern | Criteria-setter (meta-judge) | Producer + evaluator (implementation + judge) | Use when |
|---|---|---|---|
| Sharpened-haiku | `sonnet` | `haiku` | The work is trivial, but what counts as "correct" is not obvious |
| Sharpened-sonnet | `opus` | `sonnet` | Code work with ambiguous or high-consequence acceptance criteria that does not itself hit an `opus` trigger |

Producer and evaluator MUST always share a tier — for a repeatable or shared group's judge that serves more than one task, "share a tier" means the HIGHEST current implementation tier among the tasks it serves, so it is never asked to judge work above its own tier (see [Model Escalation on Retry](#531-model-escalation-on-retry)). You MUST NOT raise the evaluator alone, and MUST NOT set the criteria-setter below the producer tier. **An explicit `--model` override supersedes this whole section:** when the user passed `--model`, every role for every task runs at that tier, and Role Pairing MUST NOT raise the meta-judge above it.

### Escalation Rule

Bump **BOTH producer and evaluator** (the failing task's implementation and judge) one tier for the next attempt when either trigger fires:

1. **Low first-attempt quality** — a low score, or issues showing the model misunderstood the task rather than merely missing details.
2. **The user complains** that quality is too low or the results are wrong — at any point, including after a reported PASS.

Ladder: `haiku` → `sonnet` → `opus`. `opus` is the **ceiling** — there is no further tier. If `opus`-tier work still fails, escalate to the **user**, never loop.

- **Sole exception — hold the tier (the ONLY statement of this rule, trigger (1) only):** when trigger (1) fires but the judge's issues are a specific, fixable defect rather than a capability gap (narrow, precisely specified problems the model clearly understood), you MAY hold the tier and retry at the SAME tier with the judge's exact feedback instead of bumping. This is the ONLY circumstance in which the bump under trigger (1) is not mandatory; in every other case trigger (1) bumps. Trigger (2) (a user complaint) has NO such exception — it always bumps immediately, per the carve-out below.
- **Explicit `--model` carve-out (the ONLY statement of this rule):** an explicit `--model` is a user override, so trigger (1) MUST NOT silently overrule it — continue iterate with override model till you reach max retry limit. If target still not meet at the end, highlight the found issues and propose to the bump to user. Trigger (2) IS that approval, so it bumps immediately.
- **Scoped to the failing task only.** Escalation re-tiers the retries of THAT task's implementation and judge. It does NOT re-tier the batch: sibling tasks running concurrently, and every task in a later batch, are assessed on their own merits per the [Selection Rules](#selection-rules), starting again from the `sonnet`/`haiku` default.
- Escalation moves implementation and judge only. The task's meta-judge (or the group's, for repeatable/shared groups) is NOT re-run and NOT re-tiered — its specification is reused across the task's retries, and changing the criteria mid-task invalidates the comparison across attempts.
- Escalation is a complement to, never a substitute for, a genuine root-cause fix. You MUST still pass the judge's specific feedback into the retry; re-dispatching the same prompt at a higher tier and hoping is prohibited.
- Escalation is orthogonal to the score thresholds, the [Iteration Discretion Rule](#55-iteration-discretion-rule) and the per-target max-3-retries budget — it changes *which model* runs the next attempt, never *whether* an attempt is warranted.
- **Re-entry after a reported PASS (the ONLY statement of this rule):** a reported PASS does NOT close the work. If the user later says a target's result is wrong or its quality too low, re-enter that target's retry path under trigger (2), and that target's retry budget **resets** — the complaint opens a fresh cycle of up to 3 retries even if the earlier cycle was exhausted.

### Cross-Provider Equivalence

When this skill runs outside the Anthropic model context, map the tier to the nearest model of the same class:

| Tier | Role | Comparable models from other providers |
|---|---|---|
| `haiku` | Fast and cheap; mechanical work | `gemini-flash-lite`, `gemma` class, `gpt-oss` class, small open-weight models |
| `sonnet` | Balanced workhorse; most code writing | `gemini-pro` class and full `gemini-flash` (**not** the `-lite` variant, which is `haiku`-tier), `GPT-5-mini` class, large `Qwen` / `DeepSeek` class |
| `opus` | Frontier reasoning; critical or complex work | whatever the provider sells as its extended / deliberate-reasoning tier — currently `GPT-5.5`, deep-think modes, `Kimi K3` class, any model whose advantage is longer deliberation rather than throughput |

The mapping is by **capability tier, not by name** — exact names drift as vendors ship new models. Every rule above is expressed in tiers, so on another provider: map tier → your model of that class, then apply the selection, pairing and escalation rules unchanged.

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
- `STRICT_MODE = --strict present || false` - disables the [Iteration Discretion Rule](#55-iteration-discretion-rule); a target then passes ONLY when `score >= 4.0`, otherwise it is retried until max retries
- Strip ALL flags from the task text before building sub-agent prompts — **never** pass them into a sub-agent prompt

Example: `/do-in-parallel Simplify error handling --files "src/a.ts,src/b.ts" --strict`

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

#### Requirement Grouping Analysis (REQUIRED before Meta-Judge dispatch)

After identifying individual tasks and validating independence, analyze whether tasks can share meta-judges and/or judges. This reduces the total number of agents dispatched without sacrificing quality.

**Three grouping types** (can be combined within a single user prompt):

| Grouping Type | When to Apply | Meta-Judges | Implementation Agents | Judges |
|---------------|---------------|-------------|----------------------|--------|
| **Repeatable** | Same task pattern applied across multiple files/modules (e.g., "add tests to all 3 modules") | ONE shared meta-judge for the group | One per task (always isolated) | One per task, each receiving the SAME shared spec |
| **Shared** | Tasks that should be reviewed/verified together because they are interdependent (e.g., "implement S3 adapter AND integrate it into analytics") | ONE combined meta-judge for the group | One per task (always isolated) | ONE judge for the entire group, reviewing all changes together |
| **Independent** | Tasks that are fully independent with no grouping benefit | One per task | One per task (always isolated) | One per task |

**Decision process:**

```
For each pair of tasks, ask:

1. "Is this the SAME task applied to different targets?"
   +-- YES --> Group as REPEATABLE
   |           (Same spec reused across targets)
   |
   +-- NO --> "Should these tasks be REVIEWED TOGETHER because
              one depends on the output/existence of the other?"
              |
              +-- YES --> Group as SHARED
              |           (Combined spec, single judge reviews all)
              |
              +-- NO --> Mark as INDEPENDENT
                         (Separate meta-judge and judge per task)
```

CRITICAL:
- When in doubt, default to INDEPENDENT.** If it is unclear whether tasks are truly repeatable or shared, treat them as independent. Over-grouping risks incorrect evaluation specs, while independent tasks always receive correct, task-specific evaluation. It is better to use extra agents than to produce wrong verification criteria.
- Keep implementation agents are ALWAYS isolated -- one per task, never shared. Only meta-judges and judges can be shared/grouped. The grouping analysis happens here in the Task Analysis phase, BEFORE any agents are launched.

**Meta-judge instructions:**
- Repeatable group: When dispatching a meta-judge for a repeatable group, include explicit instructions to produce a reusable verification spec.
- Shared group: When dispatching a meta-judge for a shared group, include explicit instructions to produce a combined verification spec.


**Shared group retry logic:**

If the shared judge finds issues, analyze which specific implementation agent(s) produced the failing changes. Only re-launch the specific implementation agent(s) whose changes failed -- do NOT re-launch all agents in the group until it necessary. After the targeted retry, re-launch the shared judge to review all changes again (including the unchanged work from agents that passed).



### Phase 3: Model and Agent Selection

Select the model tier and specialized agent per task, based on the analysis in Phase 2, per the [Model Selection Policy](#model-selection-policy) — `sonnet`/`haiku` by default, `opus` only when earned. If `--model` was passed, skip straight to [3.2](#32-specialized-agent-selection-optional): every sub-agent for every task runs at the user's tier, per the [Role Pairing](#role-pairing) override clause.

#### 3.1 Model Tier Selection Per Task

Assess **every** task on the three axes below, then read its tier straight off the [Selection Rules](#selection-rules) table — tiers are chosen per task, never once for the whole batch:

- **Scope** — one file, one component, or multiple files?
- **Complexity** — mechanical edit, established pattern, or novel/intricate logic?
- **Risk** — isolated and reversible, internal, or **critical** per the exhaustive list in the [Selection Rules](#selection-rules) `opus` row?

**Per grouping type:**

- **Independent** tasks — tier each task on its own merits; it gets its own meta-judge and its own judge at that tier.
- **Repeatable** groups — the shared meta-judge produces ONE reusable spec, but each task's implementation and judge are still tiered individually: assess each target against the Selection Rules exactly as if it were independent. A critical-domain target inside the group (e.g. one file happens to be auth code) can land on `opus` while its siblings stay at `sonnet` or `haiku`, even though they share one spec.
- **Shared** groups — tier each task on its own content first, then set the group's ONE shared judge to the HIGHEST of those tiers (per [Role Pairing](#role-pairing)), so it is never asked to judge work above its own tier.

For each task, state the three findings, the chosen tier, and a one-line justification before dispatching it. Then apply [Role Pairing](#role-pairing) — which governs in full, including its `--model` override — to decide that task's (or group's) meta-judge tier.

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

### Phase 3.5: Dispatch Meta-Judges (Grouped by Requirement Type, All in Parallel)

Before dispatching implementation agents, dispatch meta-judges based on the requirement grouping analysis from Phase 2. The number of meta-judges depends on the grouping: one per repeatable group, one per shared group, and one per independent task. All meta-judges are launched in parallel regardless of grouping type. Each meta-judge produces rubrics, checklists, and scoring criteria. Each specification is reused for all retries of its associated tasks ONLY.

Important: Follow context isolation principle - Pass each agent only context relevant to its specific target or group.

#### 3.5.1 Meta-Judge Prompt Templates by Grouping Type

**Independent meta-judge prompt:**

```markdown
## Task

Generate an evaluation specification yaml for the following task applied to a specific target. You will produce rubrics, checklists, and scoring criteria that a judge agent will use to evaluate the implementation artifact for this specific target.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt as Context
{Original user prompt}

## Target
{Specific target for this meta-judge: task description, file path, component name, etc. extracted from User Prompt}

## Context
{Any relevant codebase context, file paths, constraints}

## Artifact Type
{code | documentation | configuration | etc.}

## Instructions
User prompt is provided as context, you should use it only as reference of changes that can occur in the project by other agents. Generate evaluation specification ONLY on the for the your specific target, generated from User Prompt. Your report will be used to verify only this particular task, not the all tasks in the user prompt.
Return only the final evaluation specification YAML in your response.
```

**Repeatable group meta-judge prompt (ONE per group):**

```markdown
## Task

Generate a REUSABLE evaluation specification yaml that can be applied to ANY of the following targets performing the same task. You will produce rubrics, checklists, and scoring criteria that individual judge agents will each use independently to evaluate one target's implementation artifact.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt as Context
{Original user prompt}

## Task Being Repeated
{The common task description shared by all targets in this group}

## Targets in This Group
{List of all targets: file paths, component names, etc.}

## Context
{Any relevant codebase context, file paths, constraints}

## Artifact Type
{code | documentation | configuration | etc.}

## Instructions
CRITICAL: You are generating a REUSABLE spec that will be applied to EACH target independently by separate judges.
- Use generic language: "target file should align with criteria" instead of "all files should align"
- Do NOT include file-specific requirements (e.g., NOT "file should have only authentication logic") if the same spec will be applied to another target which logically cannot fulfill this criteria (e.g. "cart.ts" or "payments.ts" cannot have authentication logic)
- The spec must be applicable to ANY target in this group without modification
- Each judge will receive this same spec and evaluate only its own target against it
User prompt is provided as context, you should use it only as reference of changes that can occur in the project by other agents.
Return only the final evaluation specification YAML in your response.
```

**Shared group meta-judge prompt (ONE per group):**

```markdown
## Task

Generate a COMBINED evaluation specification yaml that covers ALL of the following related tasks. These tasks are interdependent and will be reviewed TOGETHER by a single judge. You will produce rubrics, checklists, and scoring criteria that account for cross-task dependencies and integration points.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt as Context
{Original user prompt}

## Tasks in This Shared Group
{List of all tasks with their targets:
- Task 1: {description} -> {target}
- Task 2: {description} -> {target}
}

## Context
{Any relevant codebase context, file paths, constraints, integration points between tasks}

## Artifact Type
{code | documentation | configuration | etc.}

## Instructions
CRITICAL: You are generating a COMBINED spec for tasks that will be reviewed TOGETHER by ONE judge.
- Include evaluation criteria for EACH individual task
- Include cross-task verification criteria (e.g., "adapter implementation matches the interface consumed by the integration module")
- Organize the spec so the judge can identify which criteria apply to which task's changes
- The judge will review ALL changes from ALL tasks in this group in a single evaluation
User prompt is provided as context, you should use it only as reference of changes that can occur in the project by other agents.
Return only the final evaluation specification YAML in your response.
```

#### 3.5.2 Dispatch Pattern

**Dispatch ALL meta-judges in a SINGLE response (regardless of grouping type):**

```
Use Task tool (one per group/independent task, all in same message):

[Meta-judge for Repeatable Group: "add tests"]
  - description: "Meta-judge (repeatable): reusable spec for adding tests across 3 modules"
  - prompt: {repeatable group meta-judge prompt}
  - model: {meta-judge model — the user's `--model` if one was passed; otherwise the HIGHEST current implementation tier among the group's tasks, or one tier up per Role Pairing}
  - subagent_type: "sadd:meta-judge"

[Meta-judge for Shared Group: "S3 adapter + integration"]
  - description: "Meta-judge (shared): combined spec for S3 adapter implementation and integration"
  - prompt: {shared group meta-judge prompt}
  - model: {meta-judge model — the user's `--model` if one was passed; otherwise the HIGHEST current implementation tier among the group's tasks, or one tier up per Role Pairing}
  - subagent_type: "sadd:meta-judge"

[Meta-judge for Independent Task: "update CI pipeline"]
  - description: "Meta-judge: update CI pipeline"
  - prompt: {independent meta-judge prompt}
  - model: {meta-judge model — the user's `--model` if one was passed; otherwise this task's implementation tier, or one tier up per Role Pairing}
  - subagent_type: "sadd:meta-judge"

[All meta-judges launched simultaneously]
```

**CRITICAL:** Do not wait for ALL meta-judges to complete before proceeding to Phase 4. Launch implementors immediately after each meta-judge completes. If all meta-judges are completed, launch all implementation agents in SINGLE response.

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
- Critical: you not allowed to use any mutation git commands, including, but not limited: commit, stash, push, checkout, reset, revert, etc. Except cases when task EXPLICITLY allows or requires it. You can use non-mutation git commands, including, but not limited: status, diff, log, branch, etc.
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

After meta-judges complete, launch all implementation sub-agents simultaneously, then verify with judges based on grouping type.

#### 5.1 Execution Flow

**Independent / Repeatable flow** (one judge per task):

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   Phase 3.5: Meta-Judge Dispatch (ALL in parallel)                      │
│                                                                         │
│   Independent:            Repeatable Group:                             │
│   ┌──────────────┐        ┌─────────────────────┐                       │
│   │ Meta-Judge A  │        │ Meta-Judge (shared)  │                       │
│   │ (tier)        │        │ (tier)               │                       │
│   │ → Spec YAML A │        │ → Reusable Spec YAML │                       │
│   └──────┬───────┘        └──────────┬──────────┘                       │
│          │                     ┌─────┴─────┐                            │
│          ▼                     ▼           ▼                            │
│   Phase 5: Implementation (ALL in parallel, one per task)               │
│                                                                         │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐               │
│   │ Implementer A │   │ Implementer B │   │ Implementer C │              │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘               │
│          │                  │                  │                        │
│          ▼                  ▼                  ▼                        │
│   Phase 5.2: Judge per task (after ALL implementors complete)           │
│                                                                         │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐               │
│   │  Judge A      │   │  Judge B      │   │  Judge C      │              │
│   │ +Spec YAML A  │   │ +Reusable Spec│   │ +Reusable Spec│              │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘               │
│          ▼                  ▼                  ▼                        │
│   Parse Verdict (per target) → PASS/FAIL → Retry if needed             │
└─────────────────────────────────────────────────────────────────────────┘
```

**Shared flow** (one judge for the group):

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   Phase 3.5: Meta-Judge for Shared Group                                │
│   ┌──────────────────────┐                                              │
│   │ Meta-Judge (combined) │                                              │
│   │ (tier)                │                                              │
│   │ → Combined Spec YAML  │                                              │
│   └──────────┬───────────┘                                              │
│         ┌────┴────┐                                                     │
│         ▼         ▼                                                     │
│   Phase 5: Implementation (one per task, in parallel)                   │
│   ┌──────────────┐   ┌──────────────┐                                   │
│   │ Implementer X │   │ Implementer Y │                                  │
│   └──────┬───────┘   └──────┬───────┘                                   │
│          │                  │                                           │
│          └────────┬─────────┘                                           │
│                   ▼                                                     │
│   Phase 5.2: ONE Judge for entire group                                 │
│   ┌────────────────────────────────┐                                    │
│   │  Judge (shared)                 │                                    │
│   │ +Combined Spec YAML             │                                    │
│   │ +ALL implementation outputs     │                                    │
│   └──────────────┬─────────────────┘                                    │
│                  ▼                                                      │
│   Parse per-task verdicts → Retry ONLY failing task(s) if needed        │
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

After ALL implementation agents complete, dispatch judges based on the requirement grouping determined in Phase 2. The dispatch pattern varies by grouping type:

| Grouping Type | Judge Dispatch | Spec Used |
|---------------|---------------|-----------|
| **Independent** | One judge per task | Task-specific meta-judge spec |
| **Repeatable** | One judge per task | SAME shared reusable spec from the group's meta-judge |
| **Shared** | ONE judge for the entire group | Combined spec from the group's meta-judge |

CRITICAL: Provide to the judge the EXACT meta-judge evaluation specification YAML, do not skip or add anything, do not modify it in any way, do not shorten or summarize any text in it! For repeatable groups, each target's judge receives the SAME reusable spec. For shared groups, the single judge receives the combined spec covering all tasks.

##### 5.2.1 Analyze the Pre-existing or expected parallel Changes Section

Before dispatching each target's judge, assess whether there are pre-existing or expected parallel changes in the codebase that the judge needs to be aware of. The "Pre-existing or Expected Parallel Changes" section prevents the judge from confusing prior modifications with the current implementation agent's work.

**When to include:**

- Previous do-in-parallel runs completed earlier in the same session (all targets from a prior batch)
- User's manual modifications made before invoking the skill (visible from conversation context or in git)
- Changes from other tools or agents that ran before this parallel dispatch
- Expected changes from other parallel agents in the same batch (e.g. if other agents are expected to modify other files in repository during the parallel development)

**When to omit:**

- This is the first run with no known prior changes — omit the section entirely
- On retries within the SAME target, do NOT include the implementation agent's own previous attempt as "pre-existing changes" — those are part of the current target's iteration cycle

**Content guidelines:**

- Use a high-level summary: task description, list of affected files/modules, general nature of changes (created, modified, deleted)
- Do NOT include code blocks, diffs, or line-level details — keep it concise
- Label the source clearly: "Previous do-in-parallel: {description}", "User modifications (before current task)", etc.
- If multiple sources of changes exist, use separate subsections for each

CRITICAL: avoid reading full codebase or git history, just use high-level git diff/status to determine which files were changed, or use conversation context to determine if there are any pre-existing changes.

##### 5.2.2 Launch Judge with prompt and target-specific specification YAML

**Judge prompt template:**

```markdown
You are evaluating an implementation artifact for target {target_name} against an evaluation specification produced by the meta judge.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt
{Original task description from user}

## Target
{Specific target: file path or component name}

{IF pre-existing changes are known, include the following section — otherwise omit entirely}

## Pre-existing or Expected Parallel Changes (Context Only)

The following changes were made before or expected to be done by other parallel agents in the same batch now. They are NOT part of the current implementation agent's output. Focus your evaluation on the current agent's changes to its specific target. Only verify other changed files/logic if they directly relate to the current target's task requirements.

### {Source of changes: e.g., "Previous do-in-parallel: {task description}" or "User modifications (before current task)"}
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
User prompt is provided as context, you should use it only as reference of changes that can occur in the project by other agents. Evaluate ONLY on the task from User Prompt. Your job to verify only this particular of the target, not the all tasks in the user prompt.
Follow your full judge process as defined in your agent instructions!

## Output

CRITICAL: You must reply with this exact structured evaluation report format in YAML at the START of your response!
```

CRITICAL: NEVER provide score threshold, in any format, including `threshold_pass` or anything different. Judge MUST not know what threshold for score is, in order to not be biased!!!

##### 5.2.3 Shared Group Judge Prompt Template

For shared groups where ONE judge reviews ALL related changes together:

```markdown
You are evaluating implementation artifacts for a group of related tasks against a combined evaluation specification produced by the meta judge. These tasks are interdependent and must be reviewed together.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt
{Original task description from user}

## Tasks in This Shared Group
{List of all tasks with their targets:
- Task 1: {description} -> {target}
- Task 2: {description} -> {target}
}

{IF pre-existing changes are known, include the "Pre-existing or Expected Parallel Changes (Context Only)" section — otherwise omit entirely}

## Evaluation Specification

```yaml
{meta-judge's COMBINED evaluation specification YAML}
```

## Implementation Outputs
{For each task in the group:}
### Task: {task description} -> {target}
{Summary section from that task's implementation agent}
{Paths to files modified}

## Instructions
User prompt is provided as context, you should use it only as reference of changes that can occur in the project by other agents. Evaluate ALL tasks in this shared group together. Verify cross-task integration points (e.g., does the adapter match the interface the integration module consumes?).
CRITICAL: For each task, indicate separately whether it PASSED or FAILED so that only failing tasks can be retried.
Follow your full judge process as defined in your agent instructions!

## Output

CRITICAL: You must reply with this exact structured evaluation report format in YAML at the START of your response! Include per-task verdicts within the report.
```

##### 5.2.4 Dispatch Judges by Grouping Type

**Independent and Repeatable targets -- one judge per task:**

```
Use Task tool:
  - description: "Judge: {target name}"
  - prompt: {judge verification prompt with exact meta-judge specification YAML, and Pre-existing or Expected Parallel Changes section if applicable}
  - model: {judge model — the user's `--model` if one was passed; otherwise MUST equal this task's current implementation tier, including after escalation}
  - subagent_type: "sadd:judge"
```

For repeatable groups, each judge receives the SAME shared reusable spec from the group's single meta-judge, but its **model** is still that task's own current implementation tier — repeatable tasks can diverge in tier even though they share one spec. The judge prompt template from 5.2.2 is used as-is; only the target and implementation output differ between judges.

**Shared group -- ONE judge for the entire group:**

```
Use Task tool:
  - description: "Judge (shared): {group description}"
  - prompt: {shared group judge prompt from 5.2.3 with combined meta-judge specification YAML and ALL implementation outputs}
  - model: {judge model — the user's `--model` if one was passed; otherwise MUST equal the HIGHEST current implementation tier among this group's tasks, including after any of them escalates}
  - subagent_type: "sadd:judge"
```

**Launch ALL judges in parallel** (independent, repeatable, and shared judges all dispatched in same response).

CRITICAL: NEVER provide score threshold, in any format, including `threshold_pass` or anything different. Judge MUST not know what threshold for score is, in order to not be biased!!!

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

If 3.0 <= score < 4 and NOT STRICT_MODE:
  -> Apply the Iteration Discretion Rule (5.5)
     -> accepted -> VERDICT: PASS (mark target complete, report outstanding issues)
     -> declined -> VERDICT: FAIL -> go to "Check retry count" below

Otherwise (score < 3.0, or score < 4 with STRICT_MODE):
  -> VERDICT: FAIL
  -> Check retry count for this target

  If retries < 3:
    -> Decide this target's retry tier per "5.3.1 Model Escalation on Retry" below
       (per the Escalation Rule — bump BOTH implementation and judge, unless its sole hold exception applies)
    -> Dispatch retry implementation agent at that tier with judge feedback
    -> Return to judge verification with same target-specific meta-judge specification,
       dispatching the judge at the retry tier (judge always matches implementation)

  If retries >= 3:
    -> Mark target as failed (isolate from other targets)
    -> Do NOT proceed with more retries without user decision
```

**IMPORTANT: Failures are isolated**
- One target failing does NOT affect other targets
- Other parallel tasks continue independently
- Only the failed target is retried

**Shared group verdict parsing:**

For shared groups, the judge produces per-task verdicts within a single report. Parse each task's verdict individually:

```
Extract from shared judge reply:
- Per-task verdicts:
  - Task 1 ({target}): VERDICT: PASS/FAIL, SCORE: X.X/5.0, ISSUES: [...]
  - Task 2 ({target}): VERDICT: PASS/FAIL, SCORE: X.X/5.0, ISSUES: [...]
- OVERALL SCORE: X.X/5.0
- CROSS-TASK ISSUES: List of integration problems (if any)
```

**Shared group retry logic:**

```
If shared judge finds failures:
  1. Identify which specific task(s) failed from per-task verdicts
  2. Re-launch ONLY the implementation agent(s) for the failed task(s)
     -- Do NOT re-launch agents whose tasks passed
  3. After retry implementation completes, re-launch the shared judge
     to review ALL changes again (passed + retried)
     -- The shared judge still uses the same combined meta-judge spec
  4. Repeat until all tasks pass or max retries reached for any task

CRITICAL: Only the specific failing implementation agent(s) are retried.
Passing tasks are NOT re-implemented. The shared judge always reviews
the complete group together on each evaluation round.
```

##### 5.3.1 Model Escalation on Retry

Before dispatching any retry you MUST decide the failing task's tier explicitly per the [Escalation Rule](#escalation-rule) — which governs in full, including its sole hold exception — and record the decision in the target's row of the Results table. Retry-specific anchors on top of it:

- **Trigger (1) is anchored at `score < 3.0`** here (or issues showing the model misunderstood the task rather than merely missing details).
- **Scope:** per the [Escalation Rule](#escalation-rule).
- **Independent and repeatable-group judges:** the retry's judge MUST be dispatched at the same tier as the retry implementation.
- **Shared-group judge:** because ONE judge reviews every task in the group together, its retry tier MUST equal the HIGHEST current implementation tier among the group's tasks — so an escalated task's judge coverage never falls below its own tier, even while unescalated siblings stay at their original tier.
- The task's meta-judge (or the group's, for repeatable/shared groups) is neither re-run nor re-tiered; its specification is reused across every retry.
- The escalated tier applies to **this task's remaining attempts only** — every other target keeps the tier it was assigned in [Phase 3](#phase-3-model-and-agent-selection).
- If `opus` still fails, escalate to the user per [Error Handling](#error-handling).

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

#### 5.5 Iteration Discretion Rule

Your main task is to COMPLETE the task within target quality, and iteration effort MUST stay proportionate to each target's size. Two failure modes are equally real:

- Burning retries and context on nitpicks so the overall batch never completes → **the task is failed**.
- Accepting a target whose quality is genuinely too poor to be considered complete → **an even worse failure**.

Apply to every judge score (for shared groups, apply this per task verdict inside the group):

- **`score < 3.0` → FAIL, unconditionally. No discretion.** Retry with judge feedback until the target passes or max retries is reached.
- **`3.0 <= score < 4.0` → discretion band.** ONLY inside this band MAY you decide that a target below the `4.0` target score is acceptable. The fixed `4.0` target puts the effective floor at `3.0`, so no separate bounded-drop guard is needed.
- Inside the band, when the outstanding issues are ONLY low/medium priority (any High or Critical finding removes discretion entirely) AND none of them breaks a target requirement or causes a meaningful defect (i.e. they are nitpicks), you MUST reason FIRST — before dispatching a retry — about whether another attempt is worth the time and context cost.
- **At most ONE nitpick-driven retry**, and it counts against the retry budget. If it again surfaces only nitpicks, you MUST mark the target complete (`ACCEPTED`), report the outstanding issues in the final summary, and move on. If it returns a score below `3.0`, the unconditional-FAIL rule applies instead.
- You MUST be critical, NOT lenient. Stopping short of target MUST be an intentional decision grounded in the absence of real, requirement-breaking issues. A genuine blocking issue that prevents completing the target within max retries MUST be reported as a failed target, never papered over.
- **If `STRICT_MODE` is true, this whole rule is DISABLED**: stop only when `score >= 4.0` or max retries is reached. `--strict` changes nothing else — the `4.0` target score, the max-retry limit, the `< 3.0` unconditional FAIL and meta-judge/judge dispatch are unaffected.

### Phase 6: Collect and Summarize Results

After all agents complete (with retries as needed), aggregate results:

```markdown
## Parallel Execution Summary

### Configuration
- **Task:** {task description}
- **Models Used:** {tiers seen across all targets, e.g. "sonnet (3), opus (1), haiku (1)" — or `--model` override if the user passed one; see Results table for per-target detail}
- **Targets:** {count} items
- **Strict Mode:** {STRICT_MODE}

### Results

| Target | Grouping | Model | Judge Score | Retries | Status | Summary |
|--------|----------|-------|-------------|---------|--------|---------|
| {target_1} | {Repeatable/Shared/Independent} | {model} | {X.X}/5.0 | {0-3} | SUCCESS | {brief outcome} |
| {target_2} | {Repeatable/Shared/Independent} | {model} | {X.X}/5.0 | {0-3} | SUCCESS | {brief outcome} |
| {target_3} | {Repeatable/Shared/Independent} | {model} | {X.X}/5.0 | {3} | FAILED | {failure reason} |
| ... | ... | ... | ... | ... | ... | ... |

Status is `SUCCESS` (score >= 4.0), `ACCEPTED` (below target per the [Iteration Discretion Rule](#55-iteration-discretion-rule) — list the outstanding nitpicks in the Verification Summary), or `FAILED`.

**Model** is the tier the target finished at; when [escalation](#531-model-escalation-on-retry) fired, record it as `{starting tier} → {final tier}`.

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

### Example 1: Requirement Grouping -- Mixed Repeatable + Independent (with Pre-existing Changes from Prior Batch)

**Scenario:**

A team runs two sequential do-in-parallel batches. The first batch updates API documentation across 3 endpoint files (`src/api/users.ts`, `src/api/orders.ts`, `src/api/products.ts`). The second batch adds tests to all 3 modules in src folder and adds a tests step to GitHub Actions. Each agent's judge in the second batch needs to know about the documentation changes from the first batch AND the expected changes from other parallel agents in the same second batch.

**Input (second batch -- first batch already completed earlier in session):**

```
/do-in-parallel add tests to all 3 modules in src folder and add tests step to github actions
```

**Orchestrator Analysis:**

```
Phase 2: Task Analysis + Requirement Grouping

1. Task Identification:
   - Task A: "Add tests to src/modules/auth.ts"
   - Task B: "Add tests to src/modules/cart.ts"
   - Task C: "Add tests to src/modules/payments.ts"
   - Task D: "Add tests step to GitHub Actions CI pipeline"

2. Requirement Grouping:
   - Tasks A, B, C: REPEATABLE — same task ("add tests") applied to 3 different modules
     → ONE shared meta-judge producing a reusable spec
   - Task D: INDEPENDENT — different task type (CI configuration)
     → Separate meta-judge

3. Pre-existing and Expected Parallel Changes Assessment:
   - Pre-existing (from prior batch): API documentation updated across
     src/api/users.ts, src/api/orders.ts, src/api/products.ts
   - Expected parallel: Each agent should be aware that other agents in this
     batch are adding tests to other modules and updating GH Actions simultaneously

4. Agent Count:
   - Meta-judges: 2 (1 repeatable for tests + 1 independent for GH Actions)
   - Implementation agents: 4 (one per task, always isolated)
   - Judges: 4 (3 using shared test spec + 1 for GH Actions)
   - Total: 10 agents (vs. 12 without grouping)
```

**Phase 3: Model Selection**

| Target | Grouping | Tier | Rationale |
|--------|----------|------|-----------|
| src/modules/auth.ts | Repeatable | opus | opus is EARNED — the critical trigger fires on the auth domain even though the task itself is "just" adding tests; a wrong test could mask a real auth defect |
| src/modules/cart.ts | Repeatable | sonnet | Code writing (test generation) on an established pattern; cart.ts has no critical-domain trigger |
| src/modules/payments.ts | Repeatable | opus | opus is EARNED — the critical trigger fires on the payments domain |
| .github/workflows/ci.yml | Independent | haiku | Small, mechanical addition of one CI step following existing pipeline conventions |

The repeatable group's tasks do NOT share one tier even though they share one meta-judge spec: auth.ts and payments.ts each independently hit the critical trigger, cart.ts does not. The shared meta-judge itself runs at `opus`, the HIGHEST tier among the three tasks it serves.

**Phase 3.5: Meta-Judge Dispatch (2 meta-judges in parallel):**

```
[Meta-judge 1: Repeatable group — test generation]
Use Task tool:
  - description: "Meta-judge (repeatable): reusable spec for adding tests across 3 modules"
  - prompt:
    ## Task

    Generate a REUSABLE evaluation specification yaml that can be applied to
    ANY of the following targets performing the same task. You will produce
    rubrics, checklists, and scoring criteria that individual judge agents
    will each use independently to evaluate one target's implementation artifact.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt as Context
    add tests to all 3 modules in src folder and add tests step to github actions

    ## Task Being Repeated
    Add comprehensive unit tests to a source module

    ## Targets in This Group
    - src/modules/auth.ts
    - src/modules/cart.ts
    - src/modules/payments.ts

    ## Context
    Project uses Jest for testing. Test files should be co-located as
    *.test.ts files. Existing test patterns available in src/modules/__tests__/.

    ## Artifact Type
    code

    ## Instructions
    CRITICAL: You are generating a REUSABLE spec that will be applied to
    EACH target independently by separate judges.
    - Use generic language: "target file should align with criteria" instead
      of "all files should align"
    - Do NOT include file-specific requirements (e.g., NOT "auth.ts should
      test only authentication logic") since this same spec will be applied
      to different files
    - The spec must be applicable to ANY target in this group without modification
    - Each judge will receive this same spec and evaluate only its own target
      against it
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents.
    Return only the final evaluation specification YAML in your response.
  - model: opus
  - subagent_type: "sadd:meta-judge"

[Meta-judge 2: Independent — GitHub Actions]
Use Task tool:
  - description: "Meta-judge: add tests step to GitHub Actions"
  - prompt:
    ## Task

    Generate an evaluation specification yaml for the following task applied
    to a specific target. You will produce rubrics, checklists, and scoring
    criteria that a judge agent will use to evaluate the implementation
    artifact for this specific target.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt as Context
    add tests to all 3 modules in src folder and add tests step to github actions

    ## Target
    Add a test execution step to the GitHub Actions CI pipeline
    (.github/workflows/ci.yml or similar)

    ## Context
    Project uses Jest for testing. The CI pipeline should run tests after
    build step. Existing workflow file may need a new job or step.

    ## Artifact Type
    configuration

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Generate
    evaluation specification ONLY for adding the tests step to GitHub Actions.
    Your report will be used to verify only this particular task, not the
    all tasks in the user prompt.
    Return only the final evaluation specification YAML in your response.
  - model: haiku
  - subagent_type: "sadd:meta-judge"

[Both meta-judges launched simultaneously]
```

**Phase 5: Implementation Dispatch (4 agents in parallel, after meta-judges complete):**

```
[Implementation 1: auth module tests]
Use Task tool:
  - description: "Parallel: add tests to src/modules/auth.ts"
  - prompt:
    ## Reasoning Approach
    Let's think step by step.
    Before taking any action, think through the problem systematically:
    1. "Let me first understand what is being asked for this specific target..."
    2. "Let me analyze this specific target..."
    3. "Let me plan my approach..."
    Work through each step explicitly before implementing.

    <task>Add comprehensive unit tests</task>
    <target>src/modules/auth.ts</target>
    <constraints>
    - Work ONLY on the specified target
    - Do NOT modify other files unless explicitly required
    - Follow existing test patterns in the project
    </constraints>
    <output>
    Create test file for the auth module.
    CRITICAL: At the end of your work, provide a "Summary" section containing:
    - Files modified (full paths)
    - Key changes (3-5 bullet points)
    - Any decisions made and rationale
    </output>

    ## Self-Critique Verification (MANDATORY)
    [standard self-critique suffix]
  - model: opus  # opus is EARNED — critical trigger: auth.ts implements authentication logic

[Implementation 2: cart module tests]
Use Task tool:
  - description: "Parallel: add tests to src/modules/cart.ts"
  - prompt:
    ## Reasoning Approach
    Let's think step by step.
    Before taking any action, think through the problem systematically:
    1. "Let me first understand what is being asked for this specific target..."
    2. "Let me analyze this specific target..."
    3. "Let me plan my approach..."
    Work through each step explicitly before implementing.

    <task>Add comprehensive unit tests</task>
    <target>src/modules/cart.ts</target>
    <constraints>
    - Work ONLY on the specified target
    - Do NOT modify other files unless explicitly required
    - Follow existing test patterns in the project
    </constraints>
    <output>
    Create test file for the cart module.
    CRITICAL: At the end of your work, provide a "Summary" section containing:
    - Files modified (full paths)
    - Key changes (3-5 bullet points)
    - Any decisions made and rationale
    </output>

    ## Self-Critique Verification (MANDATORY)
    Before submitting, verify your work:
    1. Re-read the original task and confirm every requirement is addressed
    2. Check that all tests follow existing patterns in the project
    3. Verify no unrelated files were modified
    4. Confirm the Summary section is complete and accurate
  - model: sonnet

[Implementation 3: payments module tests]
Use Task tool:
  - description: "Parallel: add tests to src/modules/payments.ts"
  - prompt: [Same CoT prefix + task body for payments.ts + critique suffix]
  - model: opus  # opus is EARNED — critical trigger: payments.ts is the payments/billing domain

[Implementation 4: GitHub Actions test step]
Use Task tool:
  - description: "Parallel: add tests step to GitHub Actions CI"
  - prompt:
    ## Reasoning Approach
    Let's think step by step.
    Before taking any action, think through the problem systematically:
    1. "Let me first understand what is being asked for this specific target..."
    2. "Let me analyze this specific target..."
    3. "Let me plan my approach..."
    Work through each step explicitly before implementing.

    <task>Add a test execution step to the GitHub Actions CI pipeline</task>
    <target>.github/workflows/ci.yml</target>
    <constraints>
    - Work ONLY on the CI workflow file
    - Add a step that runs the test suite after the build step
    - Do NOT modify other workflow files or steps beyond what is necessary
    - Follow existing workflow patterns and conventions
    </constraints>
    <output>
    Update the CI workflow with a test execution step.
    CRITICAL: At the end of your work, provide a "Summary" section containing:
    - Files modified (full paths)
    - Key changes (3-5 bullet points)
    - Any decisions made and rationale
    </output>

    ## Self-Critique Verification (MANDATORY)
    Before submitting, verify your work:
    1. Re-read the original task and confirm every requirement is addressed
    2. Check that the workflow YAML is valid and well-structured
    3. Verify no unrelated workflow steps were modified
    4. Confirm the Summary section is complete and accurate
  - model: haiku

[All 4 launched simultaneously]
```

**Phase 5.2: Judge Dispatch (4 judges in parallel, after ALL implementors complete):**

```
[Judge 1: auth module — uses SHARED reusable spec from repeatable meta-judge]
Use Task tool:
  - description: "Judge: src/modules/auth.ts"
  - prompt:
    You are evaluating an implementation artifact for target
    src/modules/auth.ts against an evaluation specification produced
    by the meta judge.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt
    add tests to all 3 modules in src folder and add tests step to github actions

    ## Target
    src/modules/auth.ts

    ## Pre-existing and expected parallel changes (Context Only)

    The following changes were made before or expected to be done by
    other parallel agents in the same batch now. They are NOT part of
    the current implementation agent's output. Focus your evaluation
    on the current agent's changes to its specific target. Only verify
    other changed files/logic if they directly relate to the current
    target's task requirements.

    ### Previous do-in-parallel: "Update API documentation for all endpoints"
    The following files were modified as part of a previous parallel batch:
    - src/api/users.ts (modified) - Added JSDoc to public methods,
      updated module header
    - src/api/orders.ts (modified) - Added JSDoc to public methods,
      added @example tags
    - src/api/products.ts (modified) - Added JSDoc to public methods,
      updated type annotations

    ### Expected parallel changes (current batch)
    Other agents in this batch are simultaneously:
    - Adding tests to src/modules/cart.ts and src/modules/payments.ts
      (repeatable group — same task on other modules)
    - Adding a tests step to .github/workflows/ci.yml (independent task)

    ## Evaluation Specification
    ```yaml
    {EXACT reusable spec YAML from repeatable meta-judge — same for all 3 module judges}
    ```

    ## Implementation Output
    {Summary from auth implementation agent}

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Evaluate ONLY
    the test generation for auth.ts.
    Follow your full judge process as defined in your agent instructions!

    ## Output
    CRITICAL: You must reply with this exact structured evaluation report
    format in YAML at the START of your response!
  - model: opus  # matches auth.ts's own implementation tier, not the group's shared meta-judge tier
  - subagent_type: "sadd:judge"

[Judge 2: cart module — uses SAME shared reusable spec]
Use Task tool:
  - description: "Judge: src/modules/cart.ts"
  - prompt: [Same judge template, same reusable spec YAML, cart implementation output.
    Pre-existing and expected parallel changes section: same prior batch info,
    expected parallel changes list auth.ts, payments.ts, and GH Actions instead]
  - model: sonnet  # matches cart.ts's own implementation tier
  - subagent_type: "sadd:judge"

[Judge 3: payments module — uses SAME shared reusable spec]
Use Task tool:
  - description: "Judge: src/modules/payments.ts"
  - prompt: [Same judge template, same reusable spec YAML, payments implementation output.
    Pre-existing and expected parallel changes section: same prior batch info,
    expected parallel changes list auth.ts, cart.ts, and GH Actions instead]
  - model: opus  # matches payments.ts's own implementation tier
  - subagent_type: "sadd:judge"

[Judge 4: GitHub Actions — uses INDEPENDENT spec from GH Actions meta-judge]
Use Task tool:
  - description: "Judge: GitHub Actions CI"
  - prompt:
    You are evaluating an implementation artifact for target
    .github/workflows/ci.yml against an evaluation specification produced
    by the meta judge.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt
    add tests to all 3 modules in src folder and add tests step to github actions

    ## Target
    .github/workflows/ci.yml

    ## Pre-existing and expected parallel changes (Context Only)

    The following changes were made before or expected to be done by
    other parallel agents in the same batch now. They are NOT part of
    the current implementation agent's output. Focus your evaluation
    on the current agent's changes to its specific target. Only verify
    other changed files/logic if they directly relate to the current
    target's task requirements.

    ### Previous do-in-parallel: "Update API documentation for all endpoints"
    The following files were modified as part of a previous parallel batch:
    - src/api/users.ts (modified) - Added JSDoc to public methods,
      updated module header
    - src/api/orders.ts (modified) - Added JSDoc to public methods,
      added @example tags
    - src/api/products.ts (modified) - Added JSDoc to public methods,
      updated type annotations

    ### Expected parallel changes (current batch)
    Other agents in this batch are simultaneously:
    - Adding tests to src/modules/auth.ts, src/modules/cart.ts,
      and src/modules/payments.ts (repeatable group — test generation)

    ## Evaluation Specification
    ```yaml
    {EXACT spec YAML from independent GH Actions meta-judge}
    ```

    ## Implementation Output
    {Summary from GH Actions implementation agent}

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Evaluate ONLY
    the GitHub Actions test step.
    Follow your full judge process as defined in your agent instructions!

    ## Output
    CRITICAL: You must reply with this exact structured evaluation report
    format in YAML at the START of your response!
  - model: haiku  # matches ci.yml's own implementation tier
  - subagent_type: "sadd:judge"

[All 4 judges launched simultaneously]
```

**Result:**

| Target | Grouping | Model | Judge Score | Retries | Status |
|--------|----------|-------|-------------|---------|--------|
| src/modules/auth.ts | Repeatable | opus | 4.2/5.0 | 0 | SUCCESS |
| src/modules/cart.ts | Repeatable | sonnet | 4.0/5.0 | 0 | SUCCESS |
| src/modules/payments.ts | Repeatable | opus | 4.1/5.0 | 0 | SUCCESS |
| .github/workflows/ci.yml | Independent | haiku | 4.3/5.0 | 0 | SUCCESS |

**Overall:** 4/4 completed. Total Agents: 10 (2 meta-judges + 4 implementations + 4 judges)

---

### Example 2: Requirement Grouping -- Shared + Repeatable Combined (with Pre-existing User Changes)

**Scenario:**

A developer has been working on a Node.js backend during the conversation. They refactored the database connection layer and updated several service modules manually, including adding S3 class interface. Then they invoked do-in-parallel to implement and integrate the S3 interface, and also refactor the cart module. Each agent's judge needs to know about the user's prior modifications AND the expected changes from other parallel agents in the same batch.

**Input:**

```
/do-in-parallel I wrote class interface for S3 service in s3.adapter.ts, please do 2 tasks: implement s3 adapter with tests and integrate s3 adapter to analytics module. Also refactor and simplify all files in cart module
```

**Orchestrator Analysis:**

```
Phase 2: Task Analysis + Requirement Grouping

1. Task Identification:
   - Task A: "Implement S3 adapter with tests in src/adapters/s3.adapter.ts"
   - Task B: "Integrate S3 adapter into src/modules/analytics.module.ts"
   - Task C: "Refactor and simplify src/modules/cart/cart.service.ts"
   - Task D: "Refactor and simplify src/modules/cart/cart.repository.ts"
   - Task E: "Refactor and simplify src/modules/cart/cart.controller.ts"

2. Requirement Grouping:
   - Tasks A, B: SHARED — interdependent (adapter must match interface consumed
     by analytics integration; should be reviewed together)
     → ONE combined meta-judge, ONE shared judge
   - Tasks C, D, E: REPEATABLE — same task ("refactor and simplify") applied
     to 3 different files in cart module
     → ONE reusable meta-judge

3. Pre-existing and Expected Parallel Changes Assessment:
   - Pre-existing (user modifications): Refactored database connection layer
     (src/db/connection.ts, src/db/queries.ts), updated service modules,
     and added S3 class interface in src/adapters/s3.adapter.ts
   - Expected parallel: S3 adapter implementation and analytics integration
     run in parallel (shared group); cart refactoring agents run in parallel
     (repeatable group); both groups run simultaneously

4. Agent Count:
   - Meta-judges: 2 (1 shared for S3 work + 1 repeatable for cart refactoring)
   - Implementation agents: 5 (one per task, always isolated)
   - Judges: 4 (1 shared for S3 group + 3 individual for cart)
   - Total: 11 agents (vs. 15 without grouping)
```

**Phase 3: Model Selection**

| Target | Grouping | Tier | Rationale |
|--------|----------|------|-----------|
| src/adapters/s3.adapter.ts | Shared | opus | Shared-contract trigger — its public interface is the contract Task B integrates against |
| src/modules/analytics.module.ts | Shared | opus | Shared-contract trigger — integrates against the adapter's public interface defined in the paired task |
| src/modules/cart/cart.service.ts | Repeatable | sonnet | Refactor confined to one file, no contract change |
| src/modules/cart/cart.repository.ts | Repeatable | sonnet | Refactor confined to one file, no contract change |
| src/modules/cart/cart.controller.ts | Repeatable | sonnet | Refactor confined to one file, no contract change |

The shared group lands on `opus` because Tasks A and B share a contract — the S3 adapter's public interface that the analytics integration consumes — which the [Selection Rules](#selection-rules) name as an `opus` trigger "at any file count when a shared contract changes." The repeatable group lands on `sonnet` because each cart file is refactored in isolation with no contract change. The shared group's meta-judge and its single judge also run at `opus` — Role Pairing's default is the SAME tier for all three roles of a task, and the shared judge's tier is the HIGHEST current implementation tier among the tasks it serves (both `opus`, since they agree).

**Phase 3.5: Meta-Judge Dispatch (2 meta-judges in parallel):**

```
[Meta-judge 1: Shared group — S3 adapter + integration]
Use Task tool:
  - description: "Meta-judge (shared): combined spec for S3 adapter and analytics integration"
  - prompt:
    ## Task

    Generate a COMBINED evaluation specification yaml that covers ALL of the
    following related tasks. These tasks are interdependent and will be
    reviewed TOGETHER by a single judge. You will produce rubrics, checklists,
    and scoring criteria that account for cross-task dependencies and
    integration points.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt as Context
    I wrote class interface for S3 service in s3.adapter.ts, please do 2 tasks:
    implement s3 adapter with tests and integrate s3 adapter to analytics module.
    Also refactor and simplify all files in cart module

    ## Tasks in This Shared Group
    - Task A: Implement S3 adapter with tests -> src/adapters/s3.adapter.ts
    - Task B: Integrate S3 adapter into analytics module -> src/modules/analytics.module.ts

    ## Context
    The user has already written the class interface in s3.adapter.ts. Task A
    implements the interface methods and adds unit tests. Task B integrates the
    adapter into the analytics module. The adapter's public API from Task A must
    match what Task B consumes.

    ## Artifact Type
    code

    ## Instructions
    CRITICAL: You are generating a COMBINED spec for tasks that will be
    reviewed TOGETHER by ONE judge.
    - Include evaluation criteria for EACH individual task
    - Include cross-task verification criteria (e.g., "S3 adapter's public
      methods match the calls made by the analytics integration")
    - Organize the spec so the judge can identify which criteria apply to
      which task's changes
    - The judge will review ALL changes from ALL tasks in this group in a
      single evaluation
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents.
    Return only the final evaluation specification YAML in your response.
  - model: opus
  - subagent_type: "sadd:meta-judge"

[Meta-judge 2: Repeatable group — cart refactoring]
Use Task tool:
  - description: "Meta-judge (repeatable): reusable spec for refactoring cart module files"
  - prompt:
    ## Task

    Generate a REUSABLE evaluation specification yaml that can be applied to
    ANY of the following targets performing the same task. You will produce
    rubrics, checklists, and scoring criteria that individual judge agents
    will each use independently to evaluate one target's implementation artifact.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt as Context
    I wrote class interface for S3 service in s3.adapter.ts, please do 2 tasks:
    implement s3 adapter with tests and integrate s3 adapter to analytics module.
    Also refactor and simplify all files in cart module

    ## Task Being Repeated
    Refactor and simplify a source file in the cart module

    ## Targets in This Group
    - src/modules/cart/cart.service.ts
    - src/modules/cart/cart.repository.ts
    - src/modules/cart/cart.controller.ts

    ## Context
    All three files are in the cart module. Refactoring should simplify logic,
    reduce complexity, improve readability while preserving existing behavior.

    ## Artifact Type
    code

    ## Instructions
    CRITICAL: You are generating a REUSABLE spec that will be applied to
    EACH target independently by separate judges.
    - Use generic language: "target file should align with criteria" instead
      of "all files should align"
    - Do NOT include file-specific requirements since this same spec will be
      applied to different files
    - The spec must be applicable to ANY target in this group without modification
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents.
    Return only the final evaluation specification YAML in your response.
  - model: sonnet
  - subagent_type: "sadd:meta-judge"

[Both meta-judges launched simultaneously]
```

**Phase 5: Implementation Dispatch (5 agents in parallel, after meta-judges complete):**

```
[Implementation 1: S3 adapter]
Use Task tool:
  - description: "Parallel: implement S3 adapter with tests"
  - prompt:
    ## Reasoning Approach
    Let's think step by step.
    Before taking any action, think through the problem systematically:
    1. "Let me first understand what is being asked for this specific target..."
    2. "Let me analyze this specific target..."
    3. "Let me plan my approach..."
    Work through each step explicitly before implementing.

    <task>Implement S3 adapter with tests based on the existing class interface</task>
    <target>src/adapters/s3.adapter.ts</target>
    <constraints>
    - Work ONLY on the specified target
    - Implement all methods defined in the existing class interface
    - Add comprehensive unit tests
    - Do NOT modify the analytics module
    </constraints>
    <output>
    Implement the S3 adapter and create tests.
    CRITICAL: At the end of your work, provide a "Summary" section containing:
    - Files modified (full paths)
    - Key changes (3-5 bullet points)
    - Any decisions made and rationale
    </output>

    ## Self-Critique Verification (MANDATORY)
    Before submitting, verify your work:
    1. Re-read the original task and confirm every requirement is addressed
    2. Check that the adapter implements all interface methods correctly
    3. Verify no unrelated files were modified
    4. Confirm the Summary section is complete and accurate
  - model: opus

[Implementation 2: Analytics integration]
Use Task tool:
  - description: "Parallel: integrate S3 adapter into analytics module"
  - prompt:
    ## Reasoning Approach
    [standard CoT prefix]

    <task>Integrate S3 adapter into the analytics module</task>
    <target>src/modules/analytics.module.ts</target>
    <constraints>
    - Work ONLY on the specified target
    - Import and use the S3 adapter from src/adapters/s3.adapter.ts
    - Follow existing dependency injection patterns
    - Do NOT modify the S3 adapter itself
    </constraints>
    <output>
    Integrate S3 adapter into analytics module.
    CRITICAL: At the end of your work, provide a "Summary" section.
    </output>

    ## Self-Critique Verification (MANDATORY)
    [standard self-critique suffix]
  - model: opus

[Implementation 3: cart.service.ts refactoring]
Use Task tool:
  - description: "Parallel: refactor src/modules/cart/cart.service.ts"
  - prompt:
    ## Reasoning Approach
    Let's think step by step.
    Before taking any action, think through the problem systematically:
    1. "Let me first understand what is being asked for this specific target..."
    2. "Let me analyze this specific target..."
    3. "Let me plan my approach..."
    Work through each step explicitly before implementing.

    <task>Refactor and simplify the cart service</task>
    <target>src/modules/cart/cart.service.ts</target>
    <constraints>
    - Work ONLY on the specified target
    - Simplify logic, reduce complexity, improve readability
    - Preserve existing behavior — no functional changes
    - Do NOT modify other cart module files
    </constraints>
    <output>
    Refactor the cart service file.
    CRITICAL: At the end of your work, provide a "Summary" section containing:
    - Files modified (full paths)
    - Key changes (3-5 bullet points)
    - Any decisions made and rationale
    </output>

    ## Self-Critique Verification (MANDATORY)
    Before submitting, verify your work:
    1. Re-read the original task and confirm every requirement is addressed
    2. Check that existing behavior is preserved after refactoring
    3. Verify no unrelated files were modified
    4. Confirm the Summary section is complete and accurate
  - model: sonnet

[Implementation 4: cart.repository.ts refactoring]
Use Task tool:
  - description: "Parallel: refactor src/modules/cart/cart.repository.ts"
  - prompt: [Same CoT prefix + refactoring task body for cart.repository.ts + critique suffix]
  - model: sonnet

[Implementation 5: cart.controller.ts refactoring]
Use Task tool:
  - description: "Parallel: refactor src/modules/cart/cart.controller.ts"
  - prompt: [Same CoT prefix + refactoring task body for cart.controller.ts + critique suffix]
  - model: sonnet

[All 5 launched simultaneously]
```

**Phase 5.2: Judge Dispatch (4 judges in parallel, after ALL implementors complete):**

```
[Judge 1: SHARED judge for S3 group — reviews both S3 adapter + analytics integration]
Use Task tool:
  - description: "Judge (shared): S3 adapter implementation and analytics integration"
  - prompt:
    You are evaluating implementation artifacts for a group of related tasks
    against a combined evaluation specification produced by the meta judge.
    These tasks are interdependent and must be reviewed together.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt
    I wrote class interface for S3 service in s3.adapter.ts, please do 2 tasks:
    implement s3 adapter with tests and integrate s3 adapter to analytics module.
    Also refactor and simplify all files in cart module

    ## Tasks in This Shared Group
    - Task A: Implement S3 adapter with tests -> src/adapters/s3.adapter.ts
    - Task B: Integrate S3 adapter into analytics module -> src/modules/analytics.module.ts

    ## Pre-existing and expected parallel changes (Context Only)

    The following changes were made before or expected to be done by
    other parallel agents in the same batch now. They are NOT part of
    the current implementation agents' output for this shared group.
    Focus your evaluation on the S3 group's changes. Only verify other
    changed files/logic if they directly relate to these tasks.

    ### User modifications (before current task)
    The user made changes to the following files/modules before this
    task was started:
    - src/db/connection.ts (modified) - Refactored database connection
      pooling
    - src/db/queries.ts (modified) - Updated query builder patterns
    - src/adapters/s3.adapter.ts (created) - Added S3 class interface
      (the interface that Task A implements)
    - Several service modules updated to use new DB connection API

    ### Expected parallel changes (current batch)
    Other agents in this batch are simultaneously:
    - Refactoring src/modules/cart/cart.service.ts (repeatable group)
    - Refactoring src/modules/cart/cart.repository.ts (repeatable group)
    - Refactoring src/modules/cart/cart.controller.ts (repeatable group)

    ## Evaluation Specification
    ```yaml
    {EXACT combined spec YAML from shared S3 meta-judge}
    ```

    ## Implementation Outputs
    ### Task: Implement S3 adapter with tests -> src/adapters/s3.adapter.ts
    {Summary from S3 adapter implementation agent}
    Files: src/adapters/s3.adapter.ts (modified), src/adapters/s3.adapter.test.ts (created)

    ### Task: Integrate S3 adapter into analytics -> src/modules/analytics.module.ts
    {Summary from analytics integration agent}
    Files: src/modules/analytics.module.ts (modified)

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Evaluate ALL
    tasks in this shared group together. Verify cross-task integration points
    (e.g., does the adapter's public API match what the analytics module consumes?).
    CRITICAL: For each task, indicate separately whether it PASSED or FAILED
    so that only failing tasks can be retried.
    Follow your full judge process as defined in your agent instructions!

    ## Output
    CRITICAL: You must reply with this exact structured evaluation report
    format in YAML at the START of your response! Include per-task verdicts.
  - model: opus  # HIGHEST current implementation tier among Task A and Task B (both opus)
  - subagent_type: "sadd:judge"

[Judge 2: cart.service.ts — uses SHARED reusable spec from repeatable meta-judge]
Use Task tool:
  - description: "Judge: src/modules/cart/cart.service.ts"
  - prompt:
    You are evaluating an implementation artifact for target
    src/modules/cart/cart.service.ts against an evaluation specification
    produced by the meta judge.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt
    [original user prompt]

    ## Target
    src/modules/cart/cart.service.ts

    ## Pre-existing and expected parallel changes (Context Only)

    The following changes were made before or expected to be done by
    other parallel agents in the same batch now. They are NOT part of
    the current implementation agent's output. Focus your evaluation
    on the current agent's changes to its specific target. Only verify
    other changed files/logic if they directly relate to the current
    target's task requirements.

    ### User modifications (before current task)
    The user made changes to the following files/modules before this
    task was started:
    - src/db/connection.ts (modified) - Refactored database connection
      pooling
    - src/db/queries.ts (modified) - Updated query builder patterns
    - src/adapters/s3.adapter.ts (created) - Added S3 class interface
    - Several service modules updated to use new DB connection API

    ### Expected parallel changes (current batch)
    Other agents in this batch are simultaneously:
    - Implementing S3 adapter in src/adapters/s3.adapter.ts (shared group)
    - Integrating S3 adapter into src/modules/analytics.module.ts (shared group)
    - Refactoring src/modules/cart/cart.repository.ts (repeatable group)
    - Refactoring src/modules/cart/cart.controller.ts (repeatable group)

    ## Evaluation Specification
    ```yaml
    {EXACT reusable spec YAML from repeatable cart meta-judge — same for all 3 cart judges}
    ```

    ## Implementation Output
    {Summary from cart.service.ts implementation agent}

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Evaluate ONLY
    the refactoring of cart.service.ts.
    Follow your full judge process as defined in your agent instructions!

    ## Output
    CRITICAL: You must reply with this exact structured evaluation report
    format in YAML at the START of your response!
  - model: sonnet  # matches cart.service.ts's own implementation tier
  - subagent_type: "sadd:judge"

[Judge 3: cart.repository.ts — uses SAME shared reusable spec]
Use Task tool:
  - description: "Judge: src/modules/cart/cart.repository.ts"
  - prompt: [Same judge template, same reusable spec YAML, cart.repository implementation output.
    Pre-existing and expected parallel changes section: same user modifications,
    expected parallel changes list S3 group, cart.service.ts, and cart.controller.ts instead]
  - model: sonnet  # matches cart.repository.ts's own implementation tier
  - subagent_type: "sadd:judge"

[Judge 4: cart.controller.ts — uses SAME shared reusable spec]
Use Task tool:
  - description: "Judge: src/modules/cart/cart.controller.ts"
  - prompt: [Same judge template, same reusable spec YAML, cart.controller implementation output.
    Pre-existing and expected parallel changes section: same user modifications,
    expected parallel changes list S3 group, cart.service.ts, and cart.repository.ts instead]
  - model: sonnet  # matches cart.controller.ts's own implementation tier
  - subagent_type: "sadd:judge"

[All 4 judges launched simultaneously]
```

**Repeatable-group retry scenario** (if the cart.controller.ts judge finds issues) — demonstrates [Model Escalation on Retry](#531-model-escalation-on-retry):

```
Judge 4 Verdict (cart.controller.ts):
  FAIL, SCORE: 2.6/5.0
  ISSUES: The refactor introduced a circular import between
  cart.controller.ts and cart.service.ts — the implementation agent
  misunderstood the module's dependency direction, not a narrow,
  fixable nitpick (Escalation trigger 1: low first-attempt quality)

Retry Decision (per Model Escalation on Retry):
  → cart.controller.ts FAILED on a misunderstanding, not a fixable nitpick — bump ONE tier: sonnet -> opus
  → Re-launch ONLY the cart.controller.ts implementation agent, now at opus, with the judge's feedback
  → Re-launch ONLY the cart.controller.ts judge, now at opus, to re-evaluate
  → cart.service.ts and cart.repository.ts are untouched — their sonnet tier, their judges, and their PASS verdicts stand; escalation is scoped to cart.controller.ts alone, never the whole repeatable group
```

**Result:**

| Target | Grouping | Model | Judge Score | Retries | Status |
|--------|----------|-------|-------------|---------|--------|
| src/adapters/s3.adapter.ts | Shared | opus | 4.2/5.0 | 0 | SUCCESS |
| src/modules/analytics.module.ts | Shared | opus | 4.4/5.0 | 0 | SUCCESS |
| src/modules/cart/cart.service.ts | Repeatable | sonnet | 4.0/5.0 | 0 | SUCCESS |
| src/modules/cart/cart.repository.ts | Repeatable | sonnet | 4.3/5.0 | 0 | SUCCESS |
| src/modules/cart/cart.controller.ts | Repeatable | sonnet → opus | 4.1/5.0 | 1 | SUCCESS |

**Overall:** 5/5 completed. Total Agents: 13 (2 meta-judges + 5 implementations + 4 judges + 1 retry implementation + 1 retry judge)

---

### Example 3: Requirement Grouping -- All Independent

**Input:**

```
/do-in-parallel write tests for loan.service.ts, add password recovery feature to auth module and enable caching during dependency loading in github actions.
```

**Orchestrator Analysis:**

```
Phase 2: Task Analysis + Requirement Grouping

1. Task Identification:
   - Task A: "Write tests for src/services/loan.service.ts"
   - Task B: "Add password recovery feature to src/modules/auth/"
   - Task C: "Enable caching during dependency loading in .github/workflows/ci.yml"

2. Requirement Grouping:
   - Task A: INDEPENDENT — test generation for a specific service
   - Task B: INDEPENDENT — new feature in auth module (unrelated to tasks A and C)
   - Task C: INDEPENDENT — CI configuration change (unrelated to tasks A and B)
   - No grouping possible: all 3 tasks are different task types on different targets

3. Agent Count:
   - Meta-judges: 3 (one per task — standard flow)
   - Implementation agents: 3 (one per task)
   - Judges: 3 (one per task)
   - Total: 9 agents (no reduction possible)
```

**Phase 3: Model Selection**

| Target | Tier | Rationale |
|--------|------|-----------|
| src/services/loan.service.ts | sonnet | Test writing on an established pattern; generating tests alone does not fire the critical trigger |
| src/modules/auth/ | opus | opus is EARNED — the critical trigger fires on the auth domain (password-reset token issuance and validation) |
| .github/workflows/ci.yml | haiku | Small, mechanical caching config change using a standard GitHub Action; no logic to write |

**Phase 3.5: Meta-Judge Dispatch (3 meta-judges in parallel):**

```
[Meta-judge 1: Independent — loan service tests]
Use Task tool:
  - description: "Meta-judge: write tests for loan.service.ts"
  - prompt:
    ## Task

    Generate an evaluation specification yaml for the following task applied
    to a specific target. You will produce rubrics, checklists, and scoring
    criteria that a judge agent will use to evaluate the implementation
    artifact for this specific target.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt as Context
    write tests for loan.service.ts, add password recovery feature to auth
    module and enable caching during dependency loading in github actions.

    ## Target
    Write comprehensive unit tests for src/services/loan.service.ts

    ## Context
    Project uses Jest. Tests should cover all public methods, edge cases,
    and error scenarios for the loan service.

    ## Artifact Type
    code

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Generate
    evaluation specification ONLY for the loan service test generation.
    Your report will be used to verify only this particular task, not the
    all tasks in the user prompt.
    Return only the final evaluation specification YAML in your response.
  - model: sonnet
  - subagent_type: "sadd:meta-judge"

[Meta-judge 2: Independent — password recovery feature]
Use Task tool:
  - description: "Meta-judge: add password recovery to auth module"
  - prompt:
    ## Task

    Generate an evaluation specification yaml for the following task applied
    to a specific target. You will produce rubrics, checklists, and scoring
    criteria that a judge agent will use to evaluate the implementation
    artifact for this specific target.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt as Context
    write tests for loan.service.ts, add password recovery feature to auth
    module and enable caching during dependency loading in github actions.

    ## Target
    Add password recovery feature to src/modules/auth/ (password reset flow:
    request, token generation, validation, password update)

    ## Context
    Auth module handles authentication. Password recovery requires new
    endpoints, email integration, token management.

    ## Artifact Type
    code

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Generate
    evaluation specification ONLY for the password recovery feature.
    Your report will be used to verify only this particular task, not the
    all tasks in the user prompt.
    Return only the final evaluation specification YAML in your response.
  - model: opus
  - subagent_type: "sadd:meta-judge"

[Meta-judge 3: Independent — GH Actions caching]
Use Task tool:
  - description: "Meta-judge: enable dependency caching in GitHub Actions"
  - prompt:
    ## Task

    Generate an evaluation specification yaml for the following task applied
    to a specific target. You will produce rubrics, checklists, and scoring
    criteria that a judge agent will use to evaluate the implementation
    artifact for this specific target.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt as Context
    write tests for loan.service.ts, add password recovery feature to auth
    module and enable caching during dependency loading in github actions.

    ## Target
    Enable caching during dependency loading in .github/workflows/ci.yml
    (e.g., npm/yarn cache, actions/cache)

    ## Context
    GitHub Actions CI pipeline. Dependency installation step should use
    caching to speed up builds.

    ## Artifact Type
    configuration

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Generate
    evaluation specification ONLY for enabling dependency caching in GH Actions.
    Your report will be used to verify only this particular task, not the
    all tasks in the user prompt.
    Return only the final evaluation specification YAML in your response.
  - model: haiku
  - subagent_type: "sadd:meta-judge"

[All 3 meta-judges launched simultaneously]
```

**Phase 5: Implementation Dispatch (3 agents in parallel, after meta-judges complete):**

```
[Implementation 1: loan service tests]
Use Task tool:
  - description: "Parallel: write tests for loan.service.ts"
  - prompt:
    ## Reasoning Approach
    Let's think step by step.
    Before taking any action, think through the problem systematically:
    1. "Let me first understand what is being asked for this specific target..."
    2. "Let me analyze this specific target..."
    3. "Let me plan my approach..."
    Work through each step explicitly before implementing.

    <task>Write comprehensive unit tests for the loan service</task>
    <target>src/services/loan.service.ts</target>
    <constraints>
    - Work ONLY on the specified target
    - Create test file co-located with the service
    - Cover all public methods, edge cases, and error scenarios
    - Follow existing test patterns in the project
    </constraints>
    <output>
    Create test file for the loan service.
    CRITICAL: At the end of your work, provide a "Summary" section containing:
    - Files modified (full paths)
    - Key changes (3-5 bullet points)
    - Any decisions made and rationale
    </output>

    ## Self-Critique Verification (MANDATORY)
    Before submitting, verify your work:
    1. Re-read the original task and confirm every requirement is addressed
    2. Check that all tests follow existing patterns in the project
    3. Verify no unrelated files were modified
    4. Confirm the Summary section is complete and accurate
  - model: sonnet

[Implementation 2: password recovery]
Use Task tool:
  - description: "Parallel: add password recovery feature to auth module"
  - prompt:
    ## Reasoning Approach
    [standard CoT prefix]

    <task>Add password recovery feature to the auth module</task>
    <target>src/modules/auth/</target>
    <constraints>
    - Work ONLY on the auth module
    - Implement password reset request, token generation, validation,
      and password update
    - Follow existing auth module patterns
    - Do NOT modify unrelated modules
    </constraints>
    <output>
    Implement password recovery feature.
    CRITICAL: At the end of your work, provide a "Summary" section.
    </output>

    ## Self-Critique Verification (MANDATORY)
    [standard self-critique suffix]
  - model: opus

[Implementation 3: GH Actions caching]
Use Task tool:
  - description: "Parallel: enable dependency caching in GitHub Actions"
  - prompt:
    ## Reasoning Approach
    [standard CoT prefix]

    <task>Enable caching during dependency loading in CI pipeline</task>
    <target>.github/workflows/ci.yml</target>
    <constraints>
    - Work ONLY on the CI workflow file
    - Add dependency caching (npm/yarn cache or actions/cache)
    - Do NOT modify other workflow steps beyond what is necessary
    </constraints>
    <output>
    Update CI workflow with dependency caching.
    CRITICAL: At the end of your work, provide a "Summary" section.
    </output>

    ## Self-Critique Verification (MANDATORY)
    [standard self-critique suffix]
  - model: haiku

[All 3 launched simultaneously]
```

**Phase 5.2: Judge Dispatch (3 judges in parallel, after ALL implementors complete):**

```
[Judge 1: loan service tests — independent spec]
Use Task tool:
  - description: "Judge: loan.service.ts tests"
  - prompt:
    You are evaluating an implementation artifact for target
    src/services/loan.service.ts against an evaluation specification
    produced by the meta judge.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt
    write tests for loan.service.ts, add password recovery feature to auth
    module and enable caching during dependency loading in github actions.

    ## Target
    src/services/loan.service.ts

    ## Evaluation Specification
    ```yaml
    {EXACT spec YAML from loan service meta-judge}
    ```

    ## Implementation Output
    {Summary from loan service test implementation agent}

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Evaluate ONLY
    the test generation for loan.service.ts.
    Follow your full judge process as defined in your agent instructions!

    ## Output
    CRITICAL: You must reply with this exact structured evaluation report
    format in YAML at the START of your response!
  - model: sonnet
  - subagent_type: "sadd:judge"

[Judge 2: password recovery — independent spec]
Use Task tool:
  - description: "Judge: auth password recovery"
  - prompt:
    You are evaluating an implementation artifact for target
    src/modules/auth/ against an evaluation specification produced
    by the meta judge.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt
    [original user prompt]

    ## Target
    src/modules/auth/ (password recovery feature)

    ## Evaluation Specification
    ```yaml
    {EXACT spec YAML from password recovery meta-judge}
    ```

    ## Implementation Output
    {Summary from password recovery implementation agent}

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Evaluate ONLY
    the password recovery feature.
    Follow your full judge process as defined in your agent instructions!

    ## Output
    CRITICAL: You must reply with this exact structured evaluation report
    format in YAML at the START of your response!
  - model: opus
  - subagent_type: "sadd:judge"

[Judge 3: GH Actions caching — independent spec]
Use Task tool:
  - description: "Judge: GitHub Actions dependency caching"
  - prompt:
    You are evaluating an implementation artifact for target
    .github/workflows/ci.yml against an evaluation specification produced
    by the meta judge.

    CLAUDE_PLUGIN_ROOT={CLAUDE_PLUGIN_ROOT}

    ## User Prompt
    [original user prompt]

    ## Target
    .github/workflows/ci.yml (dependency caching)

    ## Evaluation Specification
    ```yaml
    {EXACT spec YAML from GH Actions caching meta-judge}
    ```

    ## Implementation Output
    {Summary from GH Actions caching implementation agent}

    ## Instructions
    User prompt is provided as context, you should use it only as reference
    of changes that can occur in the project by other agents. Evaluate ONLY
    the dependency caching in GitHub Actions.
    Follow your full judge process as defined in your agent instructions!

    ## Output
    CRITICAL: You must reply with this exact structured evaluation report
    format in YAML at the START of your response!
  - model: haiku
  - subagent_type: "sadd:judge"

[All 3 judges launched simultaneously]
```

**Result:**

| Target | Grouping | Model | Judge Score | Retries | Status |
|--------|----------|-------|-------------|---------|--------|
| src/services/loan.service.ts | Independent | sonnet | 4.1/5.0 | 0 | SUCCESS |
| src/modules/auth/ | Independent | opus | 4.3/5.0 | 0 | SUCCESS |
| .github/workflows/ci.yml | Independent | haiku | 4.0/5.0 | 0 | SUCCESS |

**Overall:** 3/3 completed. Total Agents: 9 (3 meta-judges + 3 implementations + 3 judges). No grouping reduction possible for fully independent tasks.

## Best Practices

### Target Selection

- **Be specific:** List exact files when possible
- **Use globs carefully:** Review expanded list before confirming
- **Limit scope:** 10-15 targets max per batch for manageability
- **Group by similarity:** Similar targets benefit from consistent patterns

### Model Selection Guidelines

Quick-reference examples only — the [Model Selection Policy](#model-selection-policy) is authoritative; when a scenario doesn't fit neatly below, follow the [Selection Rules](#selection-rules) table, not this list.

| Scenario | Tier | Reason |
|----------|------|--------|
| Security-critical logic (auth, payments, data integrity) | `opus` | Critical trigger — earned regardless of task size |
| Multi-file refactor or shared-contract change | `opus` | Complex trigger — breadth or contract change across files |
| Refactoring confined to one file, no contract change | `sonnet` | Single-module change on an established pattern |
| Documentation generation | `haiku` | Mechanical task, no code or cross-file reasoning |
| Code review or test generation per file | `sonnet` | Balanced capability, established patterns |

### Meta-Judge + Judge Verification

- **Requirement grouping first** - Before dispatching any meta-judges, analyze tasks for repeatable, shared, or independent grouping to minimize total agents
- **One meta-judge per group or independent task** - Repeatable groups share one reusable spec, shared groups share one combined spec, independent tasks get their own spec
- **Batch meta-judges first** - Launch all meta-judges in parallel (regardless of grouping type), then launch implementors
- **Reuse spec on retries** - Each group/target's evaluation specification stays constant across retries; only the implementation changes
- **Parse only headers from judge** - Don't read full reports to avoid context pollution
- **Include CLAUDE_PLUGIN_ROOT** - Both meta-judge and judge need the resolved plugin root path
- **Target-specific YAML** - Pass only the relevant meta-judge YAML to its judge, do not add any additional text or comments to it!
- **Shared group retries** - Only re-launch the specific failing implementation agent(s), not the entire group

### Judge Selection

Per [Role Pairing](#role-pairing), the judge tier is NOT independent of the implementation tier — the default is the SAME tier for both. There is no scenario where a `haiku`-tier task is judged by `opus`; sharpening (see the Role Pairing table) can only raise the shared **criteria-setter** (meta-judge), never the judge alone.

| Implementation Tier | Judge Tier | Rationale |
|---------------------|------------|-----------|
| `opus` | `opus` | Producer and evaluator CAN share a tier |
| `sonnet` | `sonnet` | Producer and evaluator CAN share a tier |
| `haiku` | `haiku` | Producer and evaluator CAN share a tier |

**Guideline:** see [Role Pairing](#role-pairing).

### Context Isolation

- **Minimal context:** Each sub-agent gets only what it needs
- **No cross-references:** Don't tell Agent A about Agent B's target
- **Let them discover:** Sub-agents read files to understand patterns
- **File system as truth:** Changes are coordinated through the filesystem
- **Track pre-existing changes** - Pass context about prior modifications to each agent's judge to prevent attribution confusion between pre-existing and current changes

### Quality Assurance

- **Three-layer verification:** Self-critique (internal) + Target-specific meta-judge specification (structured) + Judge (external)
- **Self-critique first:** Implementation agents verify own work before submission
- **Target-specific meta-judge specification:** Each target gets tailored rubrics that account for its unique characteristics, producing more precise evaluation criteria
- **External judge second:** Independent judge applies target-specific meta-judge specification mechanically — catches blind spots self-critique misses
- **Iteration loop:** Retry with feedback until passing or max retries
- **Proportionate iteration:** Apply the [Iteration Discretion Rule](#55-iteration-discretion-rule) — at most ONE nitpick-driven retry, never below `3.0`, disabled by `--strict`
- **Isolated failures:** One target failing doesn't affect others
- **Review the summary:** Check for failed or partial completions
- **Run tests after:** Parallel changes may have subtle interactions
- **Commit atomically:** All changes from one batch = one commit

#### Error Handling

| Failure Type | Description | Recovery Action |
|--------------|-------------|-----------------|
| **Recoverable** | Judge found issues, retry available | Retry with judge feedback (max 3 per target), subject to the [Iteration Discretion Rule](#55-iteration-discretion-rule) |
| **Approach Failure** | The approach for this target is wrong | Escalate to user with options |
| **Foundation Issue** | Requirements unclear or impossible | Escalate to user for clarification |
| **Max Retries Exceeded** | Target failed after 3 retries | Mark failed, continue other targets, report at end |

**Critical Rules:**
- NEVER continue past max retries without user input
- NEVER try to "fix forward" without addressing judge issues
- NEVER skip judge verification
- STOP and report if context is missing (don't guess)
- ISOLATE failures - one target failing doesn't stop others
