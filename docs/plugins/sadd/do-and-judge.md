# /do-and-judge

Execute a single task with implementation sub-agent, meta-judge evaluation criteria, independent judge verification, and automatic retry loop until passing or max retries exceeded.

- Purpose - Executes a single task with quality verification and feedback-driven iteration
- Pattern - Meta-Judge + Implement (parallel) → Judge (with meta-judge spec) → Iterate (if needed) → Report
- Output - Verified implementation with judge scores and improvement suggestions

## Quality Assurance

Three-layer verification: 
- self-critique (internal) 
- meta-judge criteria (structured) 
- LLM-as-a-judge (external)

Iteration - Retry with judge feedback until passing (score >=4, or >=3.0 with all low-priority issues) or max retries (3)

## Pattern: Single-Task Execution with Meta-Judge and Judge Verification

```
Phase 1: Task Analysis and Model Selection
         Complexity + Risk + Scope → Model Selection
                     │
Phase 2: Parallel Dispatch (single message, 2 tool calls)
         ┌──────────────────────┬──────────────────────────────┐
         │ Meta-Judge (opus)    │ Implementation Agent         │
         │ sadd:meta-judge      │ [CoT + Task + Self-Critique] │
         │ → Evaluation spec    │ → Implementation artifact    │
         │   (YAML rubrics,     │                              │
         │    checklists,       │                              │
         │    scoring criteria) │                              │
         └──────────┬───────────┴────────────────────┬─────────┘
                    │  Waiting for both to complete  │
                    ▼                                ▼
Phase 3: Dispatch Judge Agent (sadd:judge)
         Judge applies meta-judge spec mechanically
                     │
Phase 4: Parse Verdict and Iterate
         ├─ PASS (>=4, or >=3.0 all low-priority) → Report Success
         └─ FAIL → Retry with Feedback (max 3)
                     └─ Return to Phase 3 (same meta-judge spec)
                     │
Phase 5: Final Report or Escalation
         Success summary OR escalate to user after max retries
```

## Usage

```bash
# Basic usage
/do-and-judge "Refactor the UserService class to use dependency injection"

# Complex implementation
/do-and-judge "Implement rate limiting middleware with configurable limits per endpoint"

# Architecture change
/do-and-judge "Extract validation logic from UserController into separate UserValidator class"
```

## When to Use

**Good use cases:**

- Single, well-defined tasks that benefit from quality verification
- Changes that should meet a quality threshold before shipping
- Tasks where feedback-driven iteration improves results
- Any implementation where you want an independent quality gate

**Do NOT use when:**

- Multi-step tasks with dependencies → use `/do-in-steps` instead
- Independent parallel tasks → use `/do-in-parallel` instead
- High-stakes tasks needing multiple approaches → use `/do-competitively` instead
- Simple tasks where verification overhead isn't justified → use `/launch-sub-agent` instead

## Key Architecture Details

- **Specialized agents**: Uses `sadd:meta-judge` and `sadd:judge` agent types for evaluation phases
- **CLAUDE_PLUGIN_ROOT**: Must be included in prompts to both meta-judge and judge agents
- **Evaluation specification**: Meta-judge produces a YAML spec (rubrics, checklists, scoring criteria) that the judge applies mechanically
- **Reuse on retries**: The same meta-judge evaluation spec is reused across all retry attempts; only the implementation changes
- **Pass threshold**: Score >=4/5.0, OR >=3.0 with all low-priority issues

## Quality Enhancement Techniques

| Phase | Technique | Benefit |
|-------|-----------|---------|
| **Phase 2** | Meta-Judge | Generates task-specific evaluation criteria (YAML rubrics, checklists, scoring) before judging |
| **Phase 2** | Zero-shot CoT | Systematic reasoning improves quality by 20-60% |
| **Phase 2** | Self-Critique | Implementation agents verify own work before submission |
| **Phase 3** | LLM-as-a-Judge | Judge applies meta-judge specification mechanically, catching blind spots self-critique misses |
| **Phase 4** | Feedback Loop | Retry with specific issues until passing or max retries (3) |

## Theoretical Foundation

- **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Step-by-step reasoning improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique loops before submission
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Independent evaluation with structured rubrics
