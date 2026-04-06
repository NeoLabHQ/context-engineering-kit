# /judge - Meta-Judge + Single-Agent Work Evaluation

Evaluate completed work using a two-phase pipeline: meta-judge generates tailored evaluation criteria, then LLM-as-Judge applies them with context isolation and evidence-based scoring.

- Purpose - Assess quality of work produced earlier in conversation with isolated context
- Pattern - Context Extraction → Meta-Judge → Judge (with meta-judge spec) → Validation & Report
- Output - Evaluation report with weighted scores, evidence citations, and actionable improvements
- Efficiency - Single focused judge for fast evaluation

## Quality Assurance

Enhanced verification with meta-judge rubric generation, Chain-of-Thought scoring, self-verification, and bias mitigation

## Pattern: Meta-Judge → LLM-as-Judge with Context Isolation

This command implements a four-phase evaluation pipeline:

```
Phase 1: Context Extraction
         Review conversation history
         Identify work to evaluate
         Extract: Original task, output, files, constraints, artifact type
                     │
Phase 2: Meta-Judge (sadd:meta-judge)
         ┌─────────────────────────────────────────┐
         │ Receives extracted context + artifact    │
         │ type + evaluation focus                  │
         │                                         │
         │ Generates evaluation specification YAML: │
         │   - Tailored rubrics per artifact type   │
         │   - Checklists                           │
         │   - Scoring criteria and weights         │
         └─────────────────────────────────────────┘
                     │
Phase 3: Judge Sub-Agent (sadd:judge, Fresh Context)
         ┌─────────────────────────────────────────┐
         │ Receives ONLY extracted context          │
         │ + exact meta-judge specification YAML    │
         │ (prevents confirmation bias)             │
         │                                         │
         │ For each criterion from meta-judge spec: │
         │   1. Review evidence                    │
         │   2. Write justification                │
         │   3. Assign score (1-5)                 │
         │   4. Self-verify with questions         │
         │   5. Adjust if needed                   │
         └─────────────────────────────────────────┘
                     │
Phase 4: Validation & Report
         Verify scores in valid range (1-5)
         Check justification has evidence
         Confirm weighted total calculation
         Present verdict with recommendations
```

## Usage

```bash
> Write new controller for the user model

# Evaluate completed work
/judge

# Evaluate with specific focus
/judge code quality and test coverage

# Evaluate security considerations
/judge security implications

# Evaluate requirements alignment
/judge requirements fulfillment

# Evaluate documentation completeness
/judge documentation
```

## When to Use

**Use single judge when:**

- Quick quality check needed
- Work is straightforward with clear criteria
- Speed/cost matters more than multi-perspective analysis
- Evaluation is formative (guiding improvements), not summative
- Low-to-medium stakes decisions

**Use judge-with-debate instead when:**

- High-stakes decisions requiring rigorous evaluation
- Subjective criteria where perspectives differ legitimately
- Complex solutions with many evaluation dimensions
- You need defensible, consensus-based evaluation

## Scoring Interpretation

| Score Range | Verdict           | Recommendation              |
| ------------- | ------------------- | ----------------------------- |
| 4.50 - 5.00 | EXCELLENT         | Ready as-is                 |
| 4.00 - 4.49 | GOOD              | Minor improvements optional |
| 3.50 - 3.99 | ACCEPTABLE        | Improvements recommended    |
| 3.00 - 3.49 | NEEDS IMPROVEMENT | Address issues before use   |
| 1.00 - 2.99 | INSUFFICIENT      | Significant rework needed   |

## Quality Enhancement Techniques

| Technique                | Benefit                                                                                |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| Meta-Judge Rubric Generation | Tailored evaluation criteria per artifact type, replacing hardcoded defaults           |
| Context Isolation        | Judge receives only extracted context, preventing confirmation bias from session state |
| Chain-of-Thought Scoring | Justification BEFORE score improves reliability by 15-25%                              |
| Evidence Requirement     | Every score requires specific citations (file paths, line numbers, quotes)             |
| Self-Verification        | Judge generates verification questions and documents adjustments                       |
| Bias Mitigation          | Explicit warnings against length bias, verbosity bias, and authority bias              |

## Theoretical Foundation

Based on:

- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Structured evaluation rubrics with calibrated scoring
- **[Chain of Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Reasoning before conclusion improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique and verification loops
- **[Inference-Time Scaling of Verification](https://arxiv.org/abs/2601.15808)** (Wan et al., 2026) - Rubric-guided verification with test-time self-evolution and iterative feedback refinement
