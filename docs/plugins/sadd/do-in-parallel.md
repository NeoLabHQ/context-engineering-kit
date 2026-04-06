# /do-in-parallel

Execute tasks in parallel across multiple targets with intelligent model selection, independence validation, requirement grouping analysis, meta-judge evaluation specification, LLM-as-a-judge verification, and quality-focused prompting.

- Purpose - Execute tasks across multiple independent targets in parallel
- Pattern - Supervisor/Orchestrator with parallel dispatch, requirement grouping, context isolation, and meta-judge + judge verification
- Output - Multiple solutions, one per target, with aggregated summary
- Efficiency - Dramatic time savings through concurrent execution of independent work

## Quality Assurance

Enhanced verification with Zero-shot CoT, Constitutional AI self-critique, requirement grouping analysis, meta-judge evaluation specification, LLM-as-a-judge verification, and intelligent model selection

## Pattern: Parallel Orchestration with Judge Verification

This command implements a seven-phase parallel orchestration pattern:

```
Phase 1: Parse Input and Identify Targets
                     │
Phase 2: Task Analysis with Zero-shot CoT
         ┌─ Task Type Identification ─────────────────┐
         │ (transformation, analysis, documentation)  │
         ├─ Per-Target Complexity Assessment ─────────┤
         │ (high/medium/low)                          │
         ├─ Independence Validation ──────────────────┤
         │ CRITICAL: Must pass before proceeding      │
         ├─ Requirement Grouping Analysis ────────────┤
         │ (repeatable / shared / independent)        │
         └────────────────────────────────────────────┘
                     │
Phase 3: Model and Agent Selection
         Is task COMPLEX? → Opus
         Is task SIMPLE/MECHANICAL? → Haiku
         Is output LARGE but task not complex? → Sonnet
         Otherwise → Opus (default for balanced work)
                     │
Phase 3.5: Dispatch Meta-Judges (Grouped, All in Parallel)
         One per repeatable group (reusable spec)
         One per shared group (combined spec)
         One per independent task (task-specific spec)
         (Specs reused for ALL retries — never re-run)
                     │
Phase 4: Construct Per-Target Prompts
         [CoT Prefix] + [Task Body] + [Self-Critique Suffix]
         (Same structure for ALL agents, customized per target)
                     │
Phase 5: Parallel Dispatch and Judge Verification
         ┌─ Agent 1 (target A) ─→ Judge 1 (+meta-spec) ─┐
         ├─ Agent 2 (target B) ─→ Judge 2 (+meta-spec) ─┼─→ Concurrent
         └─ Agent 3 (target C) ─→ Judge 3 (+meta-spec) ─┘
                     │
         Each target: Implement → Judge (with meta-spec) → Retry (max 3)
         Shared groups: ONE judge reviews ALL related changes together
                     │
Phase 6: Collect and Summarize Results
         Aggregate outcomes, report failures, suggest remediation
```

## Execution Flow

### Independent / Repeatable Flow (one judge per task)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   Phase 3.5: Meta-Judge Dispatch (ALL in parallel)                      │
│                                                                         │
│   Independent:            Repeatable Group:                             │
│   ┌──────────────┐        ┌─────────────────────┐                       │
│   │ Meta-Judge A  │        │ Meta-Judge (shared)  │                       │
│   │ (Opus)        │        │ (Opus)               │                       │
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
│   Parse Verdict (per target)                                            │
│   ├─ PASS (≥4)? → Complete                                              │
│   ├─ Soft PASS (≥3 + low priority issues)? → Done                       │
│   └─ FAIL (<4)? → Retry (max 3 per target)                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Shared Flow (one judge for the group)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   Phase 3.5: Meta-Judge for Shared Group                                │
│   ┌──────────────────────┐                                              │
│   │ Meta-Judge (combined) │                                              │
│   │ (Opus)                │                                              │
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
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Usage

```bash
# Inferred targets from task description
/do-in-parallel "Apply consistent logging format to src/handlers/user.ts, src/handlers/order.ts, and src/handlers/product.ts"
```

## Advanced Options

```bash
# Basic usage with file targets
/do-in-parallel "Simplify error handling to use early returns" \
  --files "src/services/user.ts,src/services/order.ts,src/services/payment.ts"

# With named targets
/do-in-parallel "Generate unit tests achieving 80% coverage" \
  --targets "UserService,OrderService,PaymentService"

# With model override
/do-in-parallel "Security audit for injection vulnerabilities" \
  --files "src/db/queries.ts,src/api/search.ts" \
  --model opus
```

## When to Use

**Good use cases:**

- Same operation across multiple files (refactoring, formatting)
- Independent transformations (each file stands alone)
- Batch documentation generation (API docs per module)
- Parallel analysis tasks (security audit per component)
- Multi-file code generation (tests per service)

**Do NOT use when:**

- Only one target → use `/do-and-judge` instead
- Targets have dependencies → use `/do-in-steps` instead
- Tasks require sequential ordering → use `/do-in-steps` instead
- Shared state needed between executions → use `/do-in-steps` instead
- Quality-critical tasks needing comparison → use `/do-competitively` instead

## Meta-Judge and Judge Verification

Meta-judges are dispatched based on a requirement grouping analysis performed before any implementation begins. The number and type of meta-judges depends on how tasks are grouped:

| Grouping Type | When to Apply | Meta-Judges | Judges |
|---------------|---------------|-------------|--------|
| **Repeatable** | Same task applied across multiple targets (e.g., "add tests to all 3 modules") | ONE shared meta-judge producing a reusable spec | One per task, each receiving the SAME shared spec |
| **Shared** | Interdependent tasks reviewed together (e.g., "implement S3 adapter AND integrate it") | ONE combined meta-judge for the group | ONE judge for the entire group, reviewing all changes together |
| **Independent** | Fully independent tasks with no grouping benefit | One per task | One per task |

Each meta-judge generates a tailored evaluation specification (rubrics, checklists, scoring criteria). Specifications are reused for all retries of their associated tasks -- they are never re-run per target or on retries. All meta-judges are launched in parallel regardless of grouping type.

Each implementation agent is then verified by an independent `sadd:judge` agent that applies the appropriate meta-judge specification mechanically.

| Aspect | Details |
|--------|---------|
| **Meta-Judge** | `sadd:meta-judge` (Opus) dispatched per group or independent task, all in parallel |
| **Judge** | `sadd:judge` (Opus) per target (independent/repeatable) or per group (shared) |
| **Threshold** | Score >=4/5.0 for PASS; soft PASS at >=3 if all issues are low priority |
| **Max Retries** | 3 retries per target (same meta-judge spec reused on retries) |
| **Isolation** | Each target's failure doesn't affect others |
| **Feedback Loop** | Judge ISSUES passed to retry implementation |
| **Shared Retries** | Only failing implementation agent(s) are retried, not the entire group |

### Scoring Scale

| Score | Meaning | Frequency |
|-------|---------|-----------|
| 5 | Excellent - Exceeds requirements | <5% of evaluations |
| 4 | Good - Meets ALL requirements | Genuinely solid work |
| 3 | Adequate - Meets basic requirements | Refined work |
| 2 | Below Average - Multiple issues | Common for first attempts |
| 1 | Unacceptable - Clear failures | Fundamental failures |

## Quality Enhancement Techniques

| Technique | Phase | Purpose |
|-----------|-------|---------|
| Zero-shot Chain-of-Thought | Phase 4 (prompt prefix) | Structured reasoning before implementation |
| Constitutional AI Self-Critique | Phase 4 (prompt suffix) | Internal verification before submission |
| Requirement Grouping | Phase 2 (analysis) | Reduces meta-judges and judges by identifying repeatable and shared task patterns |
| Meta-Judge Specification | Phase 3.5 (grouped dispatch) | Tailored rubrics and checklists generated per group/task, reused for all retries |
| LLM-as-a-Judge | Phase 5 (per-target or per-group) | External verification applying meta-judge spec mechanically |
| Retry with Feedback | Phase 5 (on failure) | Iterative improvement using judge-identified issues |

## Context Isolation Best Practices

- **Minimal context**: Each sub-agent receives only what it needs for its target
- **No cross-references**: Don't tell Agent A about Agent B's target
- **Let them discover**: Sub-agents read files to understand local patterns
- **File system as truth**: Changes are coordinated through the filesystem
- **Track pre-existing changes**: Pass context about prior modifications to each agent's judge to prevent attribution confusion between pre-existing and current changes

## Error Handling

| Failure Type | Description | Recovery Action |
|--------------|-------------|-----------------|
| **Recoverable** | Judge found issues, retry available | Retry with judge feedback (max 3 per target) |
| **Approach Failure** | The approach for this target is wrong | Escalate to user with options |
| **Foundation Issue** | Requirements unclear or impossible | Escalate to user for clarification |
| **Max Retries Exceeded** | Target failed after 3 retries | Mark failed, continue other targets, report at end |

**Critical Rules:**
- Each target is isolated - failures don't affect other targets
- NEVER continue past max retries without user input
- NEVER try to "fix forward" without addressing judge issues
- NEVER skip judge verification
- STOP and report if context is missing (don't guess)
- Continue with successful targets even if some fail
- Report all failures clearly in final summary
- For shared groups, only retry the specific failing implementation agent(s), not the entire group

## Token Optimisation via Requirement Grouping

Requirement grouping analysis reduces the total number of agents dispatched by sharing meta-judges and judges across related tasks. The key insight is that tasks sharing the same pattern (repeatable) or requiring joint review (shared) do not each need their own meta-judge.

### How It Works

1. A **single meta-judge** is dispatched per group (not per target) before implementation begins
2. Its evaluation specification YAML is **reused across ALL targets** in that group
3. The meta-judge spec is also **reused on retries** -- it is never re-generated

### Agent Count Formula

| Grouping | Meta-Judges | Implementers | Judges | Total |
|----------|-------------|--------------|--------|-------|
| **Without grouping** (all independent) | N | N | N | 3N |
| **With grouping** (repeatable/shared) | G (groups) | N | N (repeatable) or G (shared) | G + 2N or 2G + N |

For repeatable groups (the most common case): G meta-judges + N implementers + N judges = **G + 2N** agents.

### Concrete Savings Examples

| Scenario | Targets | Without Grouping | With Grouping | Savings |
|----------|---------|-----------------|---------------|---------|
| Same refactoring across 5 files (1 repeatable group) | 5 | 15 agents (5+5+5) | 11 agents (1+5+5) | 4 agents (27%) |
| Same task across 3 files + 1 independent task | 4 | 12 agents (4+4+4) | 10 agents (2+4+4) | 2 agents (17%) |
| 2 shared tasks + 3 repeatable tasks | 5 | 15 agents (5+5+5) | 11 agents (2+5+4) | 4 agents (27%) |
| 3 fully independent tasks | 3 | 9 agents (3+3+3) | 9 agents (3+3+3) | 0 (no reduction possible) |

### Key Principles

- Implementation agents are **always isolated** -- one per task, never shared. Only meta-judges and judges can be grouped
- When in doubt, default to **independent** grouping. Over-grouping risks incorrect evaluation specs; independent tasks always receive correct, task-specific evaluation
- All meta-judges are launched **in parallel** regardless of grouping type
- Implementers launch immediately after their meta-judge completes, without waiting for all meta-judges

## Theoretical Foundation

**Zero-shot Chain-of-Thought** (Kojima et al., 2022)

- "Let's think step by step" improves reasoning by 20-60%
- Applied to each parallel agent independently
- Reference: [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916)

**Constitutional AI / Self-Critique** (Bai et al., 2022)

- Each agent self-verifies before completing
- Catches issues without coordinator overhead
- Reference: [Constitutional AI](https://arxiv.org/abs/2212.08073)

**Multi-Agent Context Isolation** (Multi-agent architecture patterns)

- Fresh context prevents accumulated confusion
- Focused tasks produce better results than context-polluted sessions
- Reference: [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) (Du et al., 2023)

**LLM-as-a-Judge** (Zheng et al., 2023)

- Independent judge catches blind spots self-critique misses
- Structured evaluation criteria ensure consistency
- Reference: [Judging LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)
