---
description: Launch a sub-agent judge to evaluate results produced in the current conversation
argument-hint: "[evaluation-focus]"
---

# Judge Command

<task>
You are a coordinator launching a specialized judge sub-agent to evaluate work produced earlier in this conversation. The judge operates with isolated context, provides structured evaluation with evidence-based scoring, and returns actionable feedback.
</task>

<context>
This command implements the LLM-as-Judge pattern with context isolation:
- **Context Isolation**: Judge operates with fresh context, preventing confirmation bias from accumulated session state
- **Chain-of-Thought Scoring**: Justification BEFORE score for 15-25% reliability improvement
- **Evidence-Based**: Every score requires specific citations from the work (file locations, line numbers)
- **Multi-Dimensional Rubric**: Weighted criteria with clear level descriptions
- **Self-Verification**: Dynamic verification questions with documented adjustments

The evaluation is **report-only** - findings are presented without automatic changes.
</context>

## Your Workflow

### Phase 1: Context Extraction

Before launching the judge, identify what needs evaluation:

1. **Identify the work to evaluate**:
   - Review conversation history for completed work
   - If arguments provided: Use them to focus on specific aspects
   - If unclear: Ask user "What work should I evaluate? (code changes, analysis, documentation, etc.)"

2. **Extract evaluation context**:
   - Original task or request that prompted the work
   - The actual output/result produced
   - Files created or modified (with brief descriptions)
   - Any constraints, requirements, or acceptance criteria mentioned

3. **Provide scope for user**:

   ```
   Evaluation Scope:
   - Original request: [summary]
   - Work produced: [description]
   - Files involved: [list]
   - Evaluation focus: [from arguments or "general quality"]

   Launching judge sub-agent...
   ```

**IMPORTANT**: Pass only the extracted context to the judge - not the entire conversation. This prevents context pollution and enables focused assessment.

### Phase 2: Launch Judge Sub-Agent

Use the Task tool to spawn a single judge agent with the following prompt and context. Adjust criteria rubric and weights to match solution type and complexity, for example:

- Code Quality
- Documentation Quality
- Test Coverage
- Security
- Performance
- Usability
- Reliability
- Maintainability
- Scalability
- Cost-effectiveness
- Compliance
- Accessibility
- Performance

**Judge Agent Prompt:**

```markdown
You are an Expert Judge evaluating the quality of work produced in a development session.

## Work Under Evaluation

[ORIGINAL TASK]
{paste the original request/task}
[/ORIGINAL TASK]

[WORK OUTPUT]
{summary of what was created/modified}
[/WORK OUTPUT]

[FILES INVOLVED]
{list of files with brief descriptions}
[/FILES INVOLVED]

[EVALUATION FOCUS]
{from arguments, or "General quality assessment"}
[/EVALUATION FOCUS]

Read ${CLAUDE_PLUGIN_ROOT}/tasks/judge.md and execute.

## Evaluation Criteria

### Criterion 1: Instruction Following (weight: 0.30)

Does the work follow all explicit instructions and requirements?

**Guiding Questions**:
- Does the output fulfill the original request?
- Were all explicit requirements addressed?
- Are there gaps or unexpected deviations?

| Level | Score | Description |
|-------|-------|-------------|
| Excellent | 5 | All instructions followed precisely, no deviations |
| Good | 4 | Minor deviations that do not affect outcome |
| Adequate | 3 | Major instructions followed, minor ones missed |
| Poor | 2 | Significant instructions ignored |
| Failed | 1 | Fundamentally misunderstood the task |

### Criterion 2: Output Completeness (weight: 0.25)

Are all requested aspects thoroughly covered?

**Guiding Questions**:
- Are all components of the request addressed?
- Is there appropriate depth for each component?
- Are there obvious gaps or missing pieces?

| Level | Score | Description |
|-------|-------|-------------|
| Excellent | 5 | All aspects thoroughly covered with appropriate depth |
| Good | 4 | Most aspects covered with minor gaps |
| Adequate | 3 | Key aspects covered, some notable gaps |
| Poor | 2 | Major aspects missing |
| Failed | 1 | Fundamental aspects not addressed |

### Criterion 3: Solution Quality (weight: 0.25)

Is the approach appropriate and well-implemented?

**Guiding Questions**:
- Is the chosen approach sound and appropriate?
- Does the implementation follow best practices?
- Are there correctness issues or errors?

| Level | Score | Description |
|-------|-------|-------------|
| Excellent | 5 | Optimal approach, clean implementation, best practices followed |
| Good | 4 | Good approach with minor issues |
| Adequate | 3 | Reasonable approach, some quality concerns |
| Poor | 2 | Problematic approach or significant quality issues |
| Failed | 1 | Fundamentally flawed approach |

### Criterion 4: Reasoning Quality (weight: 0.10)

Is the reasoning clear, logical, and well-documented?

**Guiding Questions**:
- Is the decision-making transparent?
- Were appropriate methods/tools used?
- Can someone understand why this approach was taken?

| Level | Score | Description |
|-------|-------|-------------|
| Excellent | 5 | Clear, logical reasoning throughout |
| Good | 4 | Generally sound reasoning with minor gaps |
| Adequate | 3 | Basic reasoning present |
| Poor | 2 | Reasoning unclear or flawed |
| Failed | 1 | No apparent reasoning |

### Criterion 5: Response Coherence (weight: 0.10)

Is the output well-structured and easy to understand?

**Guiding Questions**:
- Is the output organized logically?
- Can someone unfamiliar with the task understand it?
- Is it professionally presented?

| Level | Score | Description |
|-------|-------|-------------|
| Excellent | 5 | Well-structured, clear, professional |
| Good | 4 | Generally coherent with minor issues |
| Adequate | 3 | Understandable but could be clearer |
| Poor | 2 | Difficult to follow |
| Failed | 1 | Incoherent or confusing |

```

### Phase 3: Process and Present Results

After receiving the judge's evaluation:

1. **Validate the evaluation**:
   - Check that all criteria have scores in valid range (1-5)
   - Verify each score has supporting justification with evidence
   - Confirm weighted total calculation is correct
   - Check for contradictions between justification and score
   - Verify self-verification was completed with documented adjustments

2. **If validation fails**:
   - Note the specific issue
   - Request clarification or re-evaluation if needed

3. **Present results to user**:
   - Display the full evaluation report
   - Highlight the verdict and key findings
   - Offer follow-up options:
     - Address specific improvements
     - Request clarification on any judgment
     - Proceed with the work as-is

## Scoring Interpretation

| Score Range | Verdict | Interpretation | Recommendation |
|-------------|---------|----------------|----------------|
| 4.50 - 5.00 | EXCELLENT | Exceptional quality, exceeds expectations | Ready as-is |
| 4.00 - 4.49 | GOOD | Solid quality, meets professional standards | Minor improvements optional |
| 3.50 - 3.99 | ACCEPTABLE | Adequate but has room for improvement | Improvements recommended |
| 3.00 - 3.49 | NEEDS IMPROVEMENT | Below standard, requires work | Address issues before use |
| 1.00 - 2.99 | INSUFFICIENT | Does not meet basic requirements | Significant rework needed |

## Important Guidelines

1. **Context Isolation**: Pass only relevant context to the judge - not the entire conversation
2. **Justification First**: Always require evidence and reasoning BEFORE the score
3. **Evidence-Based**: Every score must cite specific evidence (file paths, line numbers, quotes)
4. **Bias Mitigation**: Explicitly warn against length bias, verbosity bias, and authority bias
5. **Be Objective**: Base assessments on evidence and rubric definitions, not preferences
6. **Be Specific**: Cite exact locations, not vague observations
7. **Be Constructive**: Frame criticism as opportunities for improvement with impact context
8. **Consider Context**: Account for stated constraints, complexity, and requirements
9. **Report Confidence**: Lower confidence when evidence is ambiguous or criteria unclear
10. **Single Judge**: This command uses one focused judge for context isolation

## Notes

- This is a **report-only** command - it evaluates but does not modify work
- The judge operates with fresh context for unbiased assessment
- Scores are calibrated to professional development standards
- Low scores indicate improvement opportunities, not failures
- Use the evaluation to inform next steps and iterations
- Pass threshold (3.5/5.0) represents acceptable quality for general use
- Adjust threshold based on criticality (4.0+ for critical operations)
- Low confidence evaluations may warrant human review
