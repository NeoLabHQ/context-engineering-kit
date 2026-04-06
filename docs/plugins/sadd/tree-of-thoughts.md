# /tree-of-thoughts - Tree of Thoughts with Adaptive Strategy

Execute complex reasoning tasks through systematic exploration of solution space, pruning unpromising branches, expanding viable approaches, and synthesizing the best solution.

- Purpose - Explore multiple solution paths before committing to full implementation
- Pattern - Tree of Thoughts (ToT) with adaptive strategy selection
- Output - Superior solution combining systematic exploration with evidence-based synthesis
- Efficiency - 15-20% average cost savings through adaptive strategy (polish clear winners, redesign failures)

## Quality Assurance

Enhanced verification with probability estimates, meta-judge evaluation specifications, multi-stage evaluation, and adaptive strategy

## Pattern: Tree of Thoughts (ToT)

This command implements an eight-phase systematic reasoning pattern with meta-judge evaluation and adaptive strategy selection:

```
Phase 1: Exploration (Propose Approaches)
         ┌─ Agent A → Proposals with probabilities ─┐
Task ───┼─ Agent B → Proposals with probabilities ─┼─┐
         └─ Agent C → Proposals with probabilities ─┘ │
                                                       │
Phase 1.5: Pruning Meta-Judge (parallel with Phase 1) │
         Meta-Judge → Pruning Evaluation Spec YAML ───┤
                                                       │
Phase 2: Pruning (Vote for Best 3)                    │
         ┌─ Judge 1 → Votes + Rationale ─┐            │
         ├─ Judge 2 → Votes + Rationale ─┼────────────┤
         └─ Judge 3 → Votes + Rationale ─┘            │
                 │                                     │
                 ├─→ Select Top 3 Proposals            │
                 │                                     │
Phase 3: Expansion (Develop Full Solutions)           │
         ┌─ Agent A → Solution A ─┐                   │
         ├─ Agent B → Solution B ─┼───────────────────┤
         └─ Agent C → Solution C ─┘                   │
                                                       │
Phase 3.5: Evaluation Meta-Judge (parallel w/ Phase 3)│
         Meta-Judge → Evaluation Spec YAML ───────────┤
                                                       │
Phase 4: Evaluation (Judge Full Solutions)            │
         ┌─ Judge 1 → Report 1 ─┐                     │
         ├─ Judge 2 → Report 2 ─┼─────────────────────┤
         └─ Judge 3 → Report 3 ─┘                     │
                                                       │
Phase 4.5: Adaptive Strategy Selection                │
         Analyze Consensus ───────────────────────────┤
                ├─ Clear Winner? → SELECT_AND_POLISH  │
                ├─ All Flawed (<3.0)? → REDESIGN      │
                └─ Split Decision? → FULL_SYNTHESIS   │
                                         │             │
Phase 5: Synthesis (Only if FULL_SYNTHESIS)           │
         Synthesizer ────────────────────┴─────────────┴─→ Final Solution
```

## Usage

```bash
# Basic usage
/tree-of-thoughts <task-description>

# With explicit output specification
/tree-of-thoughts "Design authentication middleware" --output "specs/auth.md"

# With specific evaluation criteria
/tree-of-thoughts "Design caching strategy" --criteria "performance,memory-efficiency,simplicity"
```

## When to Use

✅ **Use ToT when:**

- Solution space is large and poorly understood
- Wrong approach chosen early would waste significant effort
- Task has multiple valid approaches with different trade-offs
- Quality is more important than speed
- You need to explore before committing

❌ **Don't use ToT when:**

- Solution approach is obvious
- Task is simple or well-defined
- Speed matters more than exploration
- Only one reasonable approach exists

## Quality Enhancement Techniques

| Phase           | Technique                              | Benefit                                                                         |
| --------------- | -------------------------------------- | ------------------------------------------------------------------------------- |
| **Phase 1**     | Probabilistic Sampling                 | Explorers generate approaches with probability estimates, encouraging diversity |
| **Phase 1.5**   | Pruning Meta-Judge (`sadd:meta-judge`) | Generates tailored rubrics and scoring criteria before pruning judges evaluate  |
| **Phase 2**     | Multi-Judge Pruning                    | Independent judges apply meta-judge specs to vote on top 3, reducing groupthink |
| **Phase 3**     | Feedback-Aware Expansion               | Expanders address concerns raised during pruning                                |
| **Phase 3.5**   | Evaluation Meta-Judge (`sadd:meta-judge`) | Generates evaluation specification before full-solution judges evaluate      |
| **Phase 4**     | Structured Evaluation                  | Judges apply meta-judge-generated criteria with explicit evidence, reducing bias |
| **Phase 4.5**   | Adaptive Strategy Selection            | Orchestrator parses structured outputs to select optimal strategy               |
| **Phase 5**     | Evidence-Based Synthesis               | Combines proven best elements rather than creating new solutions                |

## Theoretical Foundation

Based on:

- **[Tree of Thoughts](https://arxiv.org/abs/2305.10601)** (Yao et al., 2023) - Systematic exploration and pruning
- **[Self-Consistency](https://arxiv.org/abs/2203.11171)** (Wang et al., 2023) - Multiple reasoning paths
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Critique and refinement
- **[LLM-as-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Multi-perspective evaluation
- **[Chain-of-Verification](https://arxiv.org/abs/2309.11495)** (Dhuliawala et al., 2023) - Structured verification reduces bias
