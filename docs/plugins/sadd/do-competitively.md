# /do-competitively - Competitive Multi-Agent Synthesis

Execute tasks through competitive multi-agent generation, meta-judge evaluation specification, multi-judge evaluation, and evidence-based synthesis to produce superior results.

- Purpose - Generates multiple solutions competitively, evaluates with independent judges using meta-judge criteria, synthesizes best elements
- Pattern - Generate-Critique-Synthesize (GCS) with meta-judge evaluation specification, self-critique, verification loops, and adaptive strategy selection
- Output - Superior solution combining best elements from all candidates
- Efficiency - 15-20% average cost savings through adaptive strategy (polish clear winners, redesign failures)

## Quality Assurance

Enhanced verification with meta-judge tailored rubrics, Constitutional AI self-critique, Chain of Verification, and intelligent strategy selection

## Pattern: Generate-Critique-Synthesize (GCS)

This command implements a four-phase adaptive competitive orchestration pattern with meta-judge evaluation specification and quality enhancement loops:

```
Phase 1: Competitive Generation with Self-Critique + Meta-Judge (IN PARALLEL)
         ┌─ Meta-Judge → Evaluation Specification YAML ───────────┐
Task ────┼─ Agent 2 → Draft → Critique → Revise → Solution B ───┐ │
         ├─ Agent 3 → Draft → Critique → Revise → Solution C ───┼─┤
         └─ Agent 1 → Draft → Critique → Revise → Solution A ───┘ │
                                                                  │
Phase 2: Multi-Judge Evaluation with Verification                 │
         ┌─ Judge 1 → Evaluate → Verify → Revise → Report A ─┐    │
         ├─ Judge 2 → Evaluate → Verify → Revise → Report B ─┼────┤
         └─ Judge 3 → Evaluate → Verify → Revise → Report C ─┘    │
                                                                  │
Phase 2.5: Adaptive Strategy Selection                            │
         Analyze Consensus ───────────────────────────────────────┤
                ├─ Clear Winner? → SELECT_AND_POLISH              │
                ├─ All Flawed (<3.0)? → REDESIGN (return Phase 1) │
                └─ Split Decision? → FULL_SYNTHESIS               │
                                          │                       │
Phase 3: Evidence-Based Synthesis         │                       │
         (Only if FULL_SYNTHESIS)         │                       │
         Synthesizer ─────────────────────┴───────────────────────┴─→ Final Solution
```

## Usage

```bash
# Basic usage
/do-competitively <task-description>

# With explicit output specification
/do-competitively "Create authentication middleware" --output "src/middleware/auth.ts"

# With specific evaluation criteria
/do-competitively "Design user schema" --criteria "scalability,security,developer-experience"
```

## Agent Types

| Agent | Type | Phase | Role |
|-------|------|-------|------|
| Meta-Judge | `sadd:meta-judge` | Phase 1 (parallel) | Generates evaluation specification YAML (rubrics, checklists, scoring criteria) tailored to the task |
| Generator (x3) | default | Phase 1 (parallel) | Produces independent competitive solutions with self-critique |
| Judge (x3) | `sadd:judge` | Phase 2 | Evaluates all solutions against meta-judge criteria |
| Synthesizer/Polisher (x1) | default | Phase 3 | Combines or polishes based on adaptive strategy |

## When to Use

Use this command when:

- **Quality is critical** - Multiple perspectives catch flaws single agents miss
- **Novel/ambiguous tasks** - No clear "right answer", exploration needed
- **High-stakes decisions** - Architecture choices, API design, critical algorithms
- **Learning/evaluation** - Compare approaches to understand trade-offs
- **Avoiding local optima** - Competitive generation explores solution space better

Do NOT use when:

- Simple, well-defined tasks with obvious solutions
- Time-sensitive changes
- Trivial bug fixes or typos
- Tasks with only one viable approach

## Quality Enhancement Techniques

Techniques that were used to enhance the quality of the competitive execution pattern.

| Phase         | Technique                       | Benefit                                                                                                              |
| --------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Phase 1**   | Constitutional AI Self-Critique | Generators review and fix their own solutions before submission, catching 40-60% of issues                           |
| **Phase 1/2** | Meta-Judge Evaluation Specification | Meta-judge generates tailored rubrics, checklists, and scoring criteria in parallel with generators; judges use these instead of hardcoded criteria |
| **Phase 2**   | Chain of Verification           | Judges verify their evaluations with structured questions, improving calibration and reducing bias                   |
| **Phase 2.5** | Adaptive Strategy Selection     | Orchestrator parses structured judge outputs (VOTE+SCORES) to select optimal strategy, saving 15-20% cost on average |
| **Phase 3**   | Evidence-Based Synthesis        | Combines proven best elements rather than creating new solutions (only when needed)                                  |

## Theoretical Foundation

The competitive execution pattern combines insights from:

**Academic Research:**

- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) (Du et al., 2023) - Diverse perspectives improve reasoning
- [Self-Consistency](https://arxiv.org/abs/2203.11171) (Wang et al., 2022) - Multiple reasoning paths improve reliability
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) (Yao et al., 2023) - Exploration of solution branches before commitment
- [Constitutional AI](https://arxiv.org/abs/2212.08073) (Bai et al., 2022) - Self-critique loops catch 40-60% of issues before review
- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) (Dhuliawala et al., 2023) - Structured verification reduces bias
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) (Zheng et al., 2023) - Structured evaluation rubrics

**Engineering Practices:**

- Design Studio Method - Parallel design, critique, synthesis
- Spike Solutions (XP/Agile) - Explore approaches, combine best
- A/B Testing - Compare alternatives with clear metrics
- Ensemble Methods - Combining multiple models improves performance
