# /judge-with-debate - Multi-Agent Debate Evaluation

Evaluate solutions through iterative multi-judge debate where independent judges analyze, challenge each other's assessments, and refine evaluations until reaching consensus or maximum rounds.

- Purpose - Rigorous evaluation through adversarial critique and evidence-based argumentation
- Pattern - Meta-Judge Specification → Independent Analysis → Iterative Debate → Consensus or Disagreement Report
- Output - Consensus evaluation report with averaged scores and debate summary, or disagreement report flagging unresolved issues
- Efficiency - Early termination when consensus reached or judges stop converging

## Quality Assurance

Enhanced verification with standardized evaluation criteria, multi-perspective analysis, evidence-based argumentation, and iterative refinement

## Pattern: Debate-Based Evaluation

This command implements iterative multi-judge debate with filesystem-based communication:

```
Phase 0.5: Meta-Judge
         Meta-Judge (Opus)
              ↓
         Evaluation Specification YAML
              ↓
Phase 1: Independent Analysis (3 judges in parallel)
         ┌─ Judge 1 → report.1.md ─┐
Solution ┼─ Judge 2 → report.2.md ─┼─┐
         └─ Judge 3 → report.3.md ─┘ │
                                     │
Phase 2: Debate Round (iterative)   │
    Each judge reads others' reports │
         ↓                           │
    Argue + Defend + Challenge       │
    (grounded in eval specification) │
         ↓                           │
    Revise if convinced ─────────────┤
         ↓                           │
    Check consensus (≤0.5 overall,   │
                     ≤1.0 per-criterion)
         ├─ Yes → Consensus Report   │
         └─ No → Next Round ─────────┘
                (max 3 rounds)
```

## Usage

```bash
# Basic usage
/judge-with-debate --solution "src/api/users.ts" --task "REST API implementation"

# With specific criteria
/judge-with-debate Implement REST API for user management \
  --solution "src/api/users.ts" \" \
  --criteria "correctness:30,design:25,security:20,performance:15,docs:10" \
  --output "evaluation/"

# Evaluating design documents
/judge-with-debate System architecture design \
  --solution "specs/architecture.md" \
  --criteria "completeness:30,feasibility:25,scalability:20,clarity:15,maintainability:10"
```

## When to Use

✅ **Use debate when:**

- High-stakes decisions requiring rigorous evaluation
- Subjective criteria where perspectives differ legitimately
- Complex solutions with many evaluation dimensions
- Quality is more important than speed/cost
- Initial judge assessments show significant disagreement
- You need defensible, evidence-based evaluation

❌ **Skip debate when:**

- Objective pass/fail criteria (use simple validation)
- Trivial solutions (single judge sufficient)
- Time/cost constraints prohibit multiple rounds
- Clear rubrics leave little room for interpretation
- Evaluation criteria are purely mechanical (linting, formatting)

## Quality Enhancement Techniques

| Phase           | Technique                | Benefit                                                                                            |
| --------------- | ------------------------ | -------------------------------------------------------------------------------------------------- |
| **Phase 0.5** | Meta-Judge Specification | `sadd:meta-judge` generates tailored rubrics, checklists, and scoring criteria before judging begins |
| **Phase 0.5** | Shared Specification     | Same evaluation YAML used by all judges across all rounds, ensuring consistent criteria            |
| **Phase 1**   | Chain of Verification    | Judges generate verification questions and self-critique before submitting initial assessment      |
| **Phase 1**   | Evidence Requirement     | All scores must be supported by specific quotes from solution                                      |
| **Phase 2**   | Filesystem Communication | Judges read each other's reports directly, orchestrator never mediates (prevents context overflow) |
| **Phase 2**   | Structured Argumentation | Judges must defend positions AND challenge others with counter-evidence grounded in eval specification |
| **Phase 2**   | Explicit Revision        | Judges must document what changed their mind or why they maintained their position                 |
| **Consensus** | Adaptive Termination     | Stops early if consensus reached, max rounds hit, or judges stop converging                        |

## Process Flow

**Step 0: Meta-Judge**

- Dispatches `sadd:meta-judge` agent (Opus) with task description 
- Meta-judge generates evaluation specification YAML (rubrics, checklists, scoring criteria)
- Runs once; output is shared verbatim with all judges across all rounds

**Step 1: Independent Analysis**

- 3 `sadd:judge` agents analyze solution in parallel, each receiving the meta-judge's evaluation specification YAML and `CLAUDE_PLUGIN_ROOT`
- Each writes comprehensive report to `report.[1|2|3].md`
- Includes per-criterion scores with evidence grounded in the evaluation specification

**Step 2: Check Consensus**

- Extract all scores from reports
- Consensus if: overall scores within 0.5 AND all criterion scores within 1.0
- If achieved → generate consensus report and complete

**Step 3: Debate Round** (if no consensus, max 3 rounds)

- Each judge reads their own report + others' reports from filesystem
- Receives the same evaluation specification YAML from the meta-judge
- Identifies disagreements (>1 point gap on any criterion)
- Defends their ratings with evidence from the solution and evaluation specification
- Challenges others' ratings with counter-evidence
- Revises scores if convinced by others' arguments
- Appends "Debate Round N" section to their own report

**Step 4: Repeat** until consensus, max rounds, or lack of convergence

**Step 5: Final Report**

- If consensus: averaged scores, strengths/weaknesses, debate summary
- If no consensus: disagreement report with flag for human review

## Theoretical Foundation

Based on:

- **[Multi-Agent Debate](https://arxiv.org/abs/2305.14325)** (Du et al., 2023) - Adversarial critique improves reasoning accuracy
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Pairwise comparison and structured evaluation
- **[Chain-of-Verification](https://arxiv.org/abs/2309.11495)** (Dhuliawala et al., 2023) - Self-verification reduces bias
- **Deliberative Democracy** - Argumentation and evidence-based consensus building

**Key Insight**: Debate forces judges to explicitly defend positions with evidence and consider counter-arguments, reducing individual bias and improving calibration.
