# /do-in-parallel

Execute tasks in parallel across multiple targets with intelligent model selection, independence validation, LLM-as-a-judge verification, and quality-focused prompting.

- Purpose - Execute the same task across multiple independent targets in parallel
- Pattern - Supervisor/Orchestrator with parallel dispatch, context isolation, and judge verification
- Output - Multiple solutions, one per target, with aggregated summary
- Quality - Enhanced with Zero-shot CoT, Constitutional AI self-critique, LLM-as-a-judge verification, and intelligent model selection
- Efficiency - Dramatic time savings through concurrent execution of independent work

## Pattern: Parallel Orchestration with Judge Verification

This command implements a six-phase parallel orchestration pattern:

```
Phase 1: Parse Input and Identify Targets
                     │
Phase 2: Task Analysis with Zero-shot CoT
         ┌─ Task Type Identification ─────────────────┐
         │ (transformation, analysis, documentation)  │
         ├─ Per-Target Complexity Assessment ─────────┤
         │ (high/medium/low)                          │
         ├─ Independence Validation ──────────────────┤
         │ ⚠️ CRITICAL: Must pass before proceeding   │
         └────────────────────────────────────────────┘
                     │
Phase 3: Model and Agent Selection
         Is task COMPLEX? → Opus
         Is task SIMPLE/MECHANICAL? → Haiku
         Otherwise → Opus (default for balanced work)
                     │
Phase 4: Construct Per-Target Prompts
         [CoT Prefix] + [Task Body] + [Self-Critique Suffix]
         (Same structure for ALL agents, customized per target)
                     │
Phase 5: Parallel Dispatch and Judge Verification
         ┌─ Agent 1 (target A) ─→ Judge 1 ─┐
         ├─ Agent 2 (target B) ─→ Judge 2 ─┼─→ Concurrent Execution
         └─ Agent 3 (target C) ─→ Judge 3 ─┘
                     │
         Each target: Implement → Judge → Retry if needed (max 2)
                     │
Phase 6: Collect and Summarize Results
         Aggregate outcomes, report failures, suggest remediation
```

## Execution Flow per Target

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Target N (Parallel with others)                                         │
│                                                                         │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│   │ Implementer  │────▶│    Judge     │────▶│ Parse Verdict        │   │
│   │ (Sub-agent)  │     │ (Sub-agent)  │     │ (Orchestrator)       │   │
│   └──────────────┘     └──────────────┘     └──────────────────────┘   │
│          ▲                                            │                 │
│          │                                            ▼                 │
│          │                              ┌─────────────────────────┐     │
│          │                              │ PASS (≥4)?              │     │
│          │                              │ ├─ YES → Complete       │     │
│          │                              │ └─ NO  → Retry?         │     │
│          │                              │     ├─ <2 → Retry       │     │
│          │                              │     └─ ≥2 → Mark Failed │     │
│          │                              └─────────────────────────┘     │
│          │                                            │                 │
│          └────────────── feedback ────────────────────┘                 │
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

## Judge Verification

Each parallel agent is verified by an independent judge:

| Aspect | Details |
|--------|---------|
| **Threshold** | Score ≥4/5.0 for PASS |
| **Max Retries** | 2 retries per target |
| **Isolation** | Each target's failure doesn't affect others |
| **Feedback Loop** | Judge ISSUES passed to retry implementation |

### Scoring Scale

| Score | Meaning | Frequency |
|-------|---------|-----------|
| 5 | Excellent - Exceeds requirements | <5% of evaluations |
| 4 | Good - Meets ALL requirements | Genuinely solid work |
| 3 | Adequate - Meets basic requirements | Refined work |
| 2 | Below Average - Multiple issues | Common for first attempts |
| 1 | Unacceptable - Clear failures | Fundamental failures |

### Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 35% | Does the implementation meet requirements? |
| Quality | 25% | Is the code well-structured and maintainable? |
| Completeness | 25% | Are all required elements present? |
| Patterns | 15% | Does it follow existing codebase conventions? |

## Context Isolation Best Practices

- **Minimal context**: Each sub-agent receives only what it needs for its target
- **No cross-references**: Don't tell Agent A about Agent B's target
- **Let them discover**: Sub-agents read files to understand local patterns
- **File system as truth**: Changes are coordinated through the filesystem

## Error Handling

| Failure Type | Description | Recovery Action |
|--------------|-------------|-----------------|
| **Recoverable** | Sub-agent made a mistake but approach is sound | Retry with judge feedback (max 2 retries) |
| **Approach Failure** | The approach for this target is wrong | Mark as failed, continue with others |
| **Max Retries Exceeded** | Failed 3 times (initial + 2 retries) | Mark as failed, suggest `/do-and-judge` |

**Critical Rules:**
- Each target is isolated - failures don't affect other targets
- NEVER retry more than twice per target
- Continue with successful targets even if some fail
- Report all failures clearly in final summary

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
