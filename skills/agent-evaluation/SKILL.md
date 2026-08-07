---
name: agent-evaluation
description: Evaluate and improve Claude Code commands, skills, and agents. Use when testing prompt effectiveness, validating context engineering choices, or measuring improvement quality.
---

# Evaluation Methods for Claude Code Agents

Evaluation of agent systems requires different approaches than traditional software or even standard language model applications. Agents make dynamic decisions, are non-deterministic between runs, and often lack single correct answers. Effective evaluation must account for these characteristics while providing actionable feedback. A robust evaluation framework enables continuous improvement, catches regressions, and validates that context engineering choices achieve intended effects.

## Core Concepts

Agent evaluation requires outcome-focused approaches that account for non-determinism and multiple valid paths. Multi-dimensional rubrics capture various quality aspects: factual accuracy, completeness, citation accuracy, source quality, and tool efficiency. LLM-as-judge provides scalable evaluation while human evaluation catches edge cases.

The key insight is that agents may find alternative paths to goals—the evaluation should judge whether they achieve right outcomes while following reasonable processes.

**Performance Drivers: The 95% Finding**
Research on the BrowseComp evaluation (which tests browsing agents' ability to locate hard-to-find information) found that three factors explain 95% of performance variance:

| Factor | Variance Explained | Implication |
|--------|-------------------|-------------|
| Token usage | 80% | More tokens = better performance |
| Number of tool calls | ~10% | More exploration helps |
| Model choice | ~5% | Better models multiply efficiency |

Implications for Claude Code development:

- **Token budgets matter**: Evaluate with realistic token constraints
- **Model upgrades beat token increases**: Upgrading models provides larger gains than increasing token budgets
- **Multi-agent validation**: Validates architectures that distribute work across subagents with separate context windows

## Evaluation Challenges

### Non-Determinism and Multiple Valid Paths

Agents may take completely different valid paths to reach goals. One agent might search three sources while another searches ten. They might use different tools to find the same answer. Traditional evaluations that check for specific steps fail in this context.

**Solution**: The solution is outcomes, not exact execution paths. Judge whether the agent achieves the right result through a reasonable process.

### Context-Dependent Failures

Agent failures often depend on context in subtle ways. An agent might succeed on complex queries but fail on simple ones. It might work well with one tool set but fail with another. Failures may emerge only after extended interaction when context accumulates.

**Solution**: Evaluation must cover a range of complexity levels and test extended interactions, not just isolated queries.

### Composite Quality Dimensions

Agent quality is not a single dimension. It includes factual accuracy, completeness, coherence, tool efficiency, and process quality. An agent might score high on accuracy but low in efficiency, or vice versa.

An agent might score high on accuracy but low in efficiency.

**Solution**: Evaluation rubrics must capture multiple dimensions with appropriate weighting for the use case.

## Evaluation Rubric Design

### Multi-Dimensional Rubric

Effective rubrics cover key dimensions with descriptive levels:

**Instruction Following** (weight: 0.30)

- Excellent (1.0): All instructions followed precisely
- Good (0.8): Minor deviations that don't affect outcome
- Acceptable (0.6): Major instructions followed, minor ones missed
- Poor (0.3): Significant instructions ignored
- Failed (0.0): Fundamentally misunderstood the task

**Output Completeness** (weight: 0.25)

- Excellent: All requested aspects thoroughly covered
- Good: Most aspects covered with minor gaps
- Acceptable: Key aspects covered, some gaps
- Poor: Major aspects missing
- Failed: Fundamental aspects not addressed

**Tool Efficiency** (weight: 0.20)

- Excellent: Optimal tool selection and minimal calls
- Good: Good tool selection with minor inefficiencies
- Acceptable: Appropriate tools with some redundancy
- Poor: Wrong tools or excessive calls
- Failed: Severe tool misuse or extremely excessive calls

**Reasoning Quality** (weight: 0.15)

- Excellent: Clear, logical reasoning throughout
- Good: Generally sound reasoning with minor gaps
- Acceptable: Basic reasoning present
- Poor: Reasoning unclear or flawed
- Failed: No apparent reasoning

**Response Coherence** (weight: 0.10)

- Excellent: Well-structured, easy to follow
- Good: Generally coherent with minor issues
- Acceptable: Understandable but could be clearer
- Poor: Difficult to follow
- Failed: Incoherent

### Scoring Approach

Convert dimension assessments to numeric scores (0.0 to 1.0) with appropriate weighting. Calculate weighted overall scores. Set passing thresholds based on use case requirements (typically 0.7 for general use, 0.85 for critical operations).

## Evaluation Methodologies

### LLM-as-Judge

Using an LLM to evaluate agent outputs scales well and provides consistent judgments. Design evaluation prompts that capture the dimensions of interest. LLM-based evaluation scales to large test sets and provides consistent judgments. The key is designing effective evaluation prompts that capture the dimensions of interest.

Provide clear task description, agent output, ground truth (if available), evaluation scale with level descriptions, and request structured judgment.

**Evaluation Prompt Template**:

```markdown
You are evaluating the output of a Claude Code agent.

## Original Task
{task_description}

## Agent Output
{agent_output}

## Ground Truth (if available)
{expected_output}

## Evaluation Criteria
For each criterion, assess the output and provide:
1. Score (1-5)
2. Specific evidence supporting your score
3. One improvement suggestion

### Criteria
1. Instruction Following: Did the agent follow all instructions?
2. Completeness: Are all requested aspects covered?
3. Tool Efficiency: Were appropriate tools used efficiently?
4. Reasoning Quality: Is the reasoning clear and sound?
5. Response Coherence: Is the output well-structured?

Provide your evaluation as a structured assessment with scores and justifications.
```

**Chain-of-Thought Requirement**: Always require justification before the score. Research shows this improves reliability by 15-25% compared to score-first approaches.

### Human Evaluation

Human evaluation catches what automation misses:

- Hallucinated answers on unusual queries
- Subtle context misunderstandings
- Edge cases that automated evaluation overlooks
- Qualitative issues with tone or approach

For Claude Code development, ask users this:

- Review agent outputs manually for edge cases
- Sample systematically across complexity levels
- Track patterns in failures to inform prompt improvements

### End-State Evaluation

For commands that produce artifacts (files, configurations, code), evaluate the final output rather than the process:

- Does the generated code work?
- Is the configuration valid?
- Does the output meet requirements?

## Test Set Design

**Sample Selection**
Start with small samples during development. Early in agent development, changes have dramatic impacts because there is abundant low-hanging fruit. Small test sets reveal large effects.

Sample from real usage patterns. Add known edge cases. Ensure coverage across complexity levels.

**Complexity Stratification**
Test sets should span complexity levels: simple (single tool call), medium (multiple tool calls), complex (many tool calls, significant ambiguity), and very complex (extended interaction, deep reasoning).

## Context Engineering Evaluation

### Testing Prompt Variations

When iterating on Claude Code prompts, evaluate systematically:

1. **Baseline**: Run current prompt on test cases
2. **Variation**: Run modified prompt on same cases
3. **Compare**: Measure quality scores, token usage, efficiency
4. **Analyze**: Identify which changes improved which dimensions

### Testing Context Strategies

Context engineering choices should be validated through systematic evaluation. Run agents with different context strategies on the same test set. Compare quality scores, token usage, and efficiency metrics.

### Degradation Testing

Test how context degradation affects performance by running agents at different context sizes. Identify performance cliffs where context becomes problematic. Establish safe operating limits.

## Advanced Evaluation: LLM-as-Judge

**Key insight**: LLM-as-a-Judge is not a single technique but a family of approaches, each suited to different evaluation contexts. Choosing the right approach and mitigating known biases is the core competency this skill develops.

### The Evaluation Taxonomy

Evaluation approaches fall into two primary categories with distinct reliability profiles:

**Direct Scoring**: A single LLM rates one response on a defined scale.

- Best for: Objective criteria (factual accuracy, instruction following, toxicity)
- Reliability: Moderate to high for well-defined criteria
- Failure mode: Score calibration drift, inconsistent scale interpretation

**Pairwise Comparison**: An LLM compares two responses and selects the better one.

- Best for: Subjective preferences (tone, style, persuasiveness)
- Reliability: Higher than direct scoring for preferences
- Failure mode: Position bias, length bias

Research from the MT-Bench paper (Zheng et al., 2023) establishes that pairwise comparison achieves higher agreement with human judges than direct scoring for preference-based evaluation, while direct scoring remains appropriate for objective criteria with clear ground truth.

### The Bias Landscape

LLM judges exhibit systematic biases that must be actively mitigated:

**Position Bias**: First-position responses receive preferential treatment in pairwise comparison. Mitigation: Evaluate twice with swapped positions, use majority vote or consistency check.

**Length Bias**: Longer responses are rated higher regardless of quality. Mitigation: Explicit prompting to ignore length, length-normalized scoring.

**Self-Enhancement Bias**: Models rate their own outputs higher. Mitigation: Use different models for generation and evaluation, or acknowledge limitation.

**Verbosity Bias**: Detailed explanations receive higher scores even when unnecessary. Mitigation: Criteria-specific rubrics that penalize irrelevant detail.

**Authority Bias**: Confident, authoritative tone rated higher regardless of accuracy. Mitigation: Require evidence citation, fact-checking layer.

### Metric Selection Framework

Choose metrics based on the evaluation task structure:

| Task Type | Primary Metrics | Secondary Metrics |
|-----------|-----------------|-------------------|
| Binary classification (pass/fail) | Recall, Precision, F1 | Cohen's κ |
| Ordinal scale (1-5 rating) | Spearman's ρ, Kendall's τ | Cohen's κ (weighted) |
| Pairwise preference | Agreement rate, Position consistency | Confidence calibration |
| Multi-label | Macro-F1, Micro-F1 | Per-label precision/recall |

The critical insight: High absolute agreement matters less than systematic disagreement patterns. A judge that consistently disagrees with humans on specific criteria is more problematic than one with random noise.


## Evaluation Metrics Reference

### Classification Metrics (Pass/Fail Tasks)

**Precision**: Of all responses marked as passing, what fraction truly passed?

- Use when false positives are costly

**Recall**: Of all actually passing responses, what fraction did we identify?

- Use when false negatives are costly

**F1 Score**: Harmonic mean of precision and recall

- Use for balanced single-number summary

### Agreement Metrics (Comparing to Human Judgment)

**Cohen's Kappa**: Agreement adjusted for chance
>
- > 0.8: Almost perfect agreement
- 0.6-0.8: Substantial agreement
- 0.4-0.6: Moderate agreement
- < 0.4: Fair to poor agreement

### Correlation Metrics (Ordinal Scores)

**Spearman's Rank Correlation**: Correlation between rankings
>
- > 0.9: Very strong correlation
- 0.7-0.9: Strong correlation
- 0.5-0.7: Moderate correlation
- < 0.5: Weak correlation

### Good Evaluation System Indicators

| Metric | Good | Acceptable | Concerning |
|--------|------|------------|------------|
| Spearman's rho | > 0.8 | 0.6-0.8 | < 0.6 |
| Cohen's Kappa | > 0.7 | 0.5-0.7 | < 0.5 |
| Position consistency | > 0.9 | 0.8-0.9 | < 0.8 |
| Length-score correlation | < 0.2 | 0.2-0.4 | > 0.4 |

## Evaluation Approaches

### Direct Scoring Implementation

Direct scoring requires three components: clear criteria, a calibrated scale, and structured output format.

**Criteria Definition Pattern**:

```
Criterion: [Name]
Description: [What this criterion measures]
Weight: [Relative importance, 0-1]
```

**Scale Calibration**:

- 1-3 scales: Binary with neutral option, lowest cognitive load
- 1-5 scales: Standard Likert, good balance of granularity and reliability
- 1-10 scales: High granularity but harder to calibrate, use only with detailed rubrics

**Prompt Structure for Direct Scoring**:

```
You are an expert evaluator assessing response quality.

## Task
Evaluate the following response against each criterion.

## Original Prompt
{prompt}

## Response to Evaluate
{response}

## Criteria
{for each criterion: name, description, weight}

## Instructions
For each criterion:
1. Find specific evidence in the response
2. Score according to the rubric (1-{max} scale)
3. Justify your score with evidence
4. Suggest one specific improvement

## Output Format
Respond with structured JSON containing scores, justifications, and summary.
```

**Chain-of-Thought Requirement**: All scoring prompts must require justification before the score. Research shows this improves reliability by 15-25% compared to score-first approaches.

### Pairwise Comparison Implementation

Pairwise comparison is inherently more reliable for preference-based evaluation but requires bias mitigation.

**Position Bias Mitigation Protocol**:

1. First pass: Response A in first position, Response B in second
2. Second pass: Response B in first position, Response A in second
3. Consistency check: If passes disagree, return TIE with reduced confidence
4. Final verdict: Consistent winner with averaged confidence

**Prompt Structure for Pairwise Comparison**:

```
You are an expert evaluator comparing two AI responses.

## Critical Instructions
- Do NOT prefer responses because they are longer
- Do NOT prefer responses based on position (first vs second)
- Focus ONLY on quality according to the specified criteria
- Ties are acceptable when responses are genuinely equivalent

## Original Prompt
{prompt}

## Response A
{response_a}

## Response B
{response_b}

## Comparison Criteria
{criteria list}

## Instructions
1. Analyze each response independently first
2. Compare them on each criterion
3. Determine overall winner with confidence level

## Output Format
JSON with per-criterion comparison, overall winner, confidence (0-1), and reasoning.
```

**Confidence Calibration**: Confidence scores should reflect position consistency:

- Both passes agree: confidence = average of individual confidences
- Passes disagree: confidence = 0.5, verdict = TIE

## Rubric Generation

Well-defined rubrics reduce evaluation variance by 40-60% compared to open-ended scoring.

### Rubric Components

1. **Level descriptions**: Clear boundaries for each score level
2. **Characteristics**: Observable features that define each level
3. **Examples**: Representative outputs for each level (when possible)
4. **Edge cases**: Guidance for ambiguous situations
5. **Scoring guidelines**: General principles for consistent application

### Strictness Calibration

- **Lenient**: Lower bar for passing scores, appropriate for encouraging iteration
- **Balanced**: Fair, typical expectations for production use
- **Strict**: High standards, appropriate for safety-critical or high-stakes evaluation

### Domain Adaptation

Rubrics should use domain-specific terminology:

- A "code readability" rubric mentions variables, functions, and comments.
- Documentation rubrics reference clarity, accuracy, completeness
- Analysis rubrics focus on depth, accuracy, actionability

## Practical Guidance

### Evaluation Pipeline Design

Production evaluation systems require multiple layers:

```
┌─────────────────────────────────────────────────┐
│                 Evaluation Pipeline              │
├─────────────────────────────────────────────────┤
│                                                   │
│  Input: Response + Prompt + Context               │
│           │                                       │
│           ▼                                       │
│  ┌─────────────────────┐                         │
│  │   Criteria Loader   │ ◄── Rubrics, weights    │
│  └──────────┬──────────┘                         │
│             │                                     │
│             ▼                                     │
│  ┌─────────────────────┐                         │
│  │   Primary Scorer    │ ◄── Direct or Pairwise  │
│  └──────────┬──────────┘                         │
│             │                                     │
│             ▼                                     │
│  ┌─────────────────────┐                         │
│  │   Bias Mitigation   │ ◄── Position swap, etc. │
│  └──────────┬──────────┘                         │
│             │                                     │
│             ▼                                     │
│  ┌─────────────────────┐                         │
│  │ Confidence Scoring  │ ◄── Calibration         │
│  └──────────┬──────────┘                         │
│             │                                     │
│             ▼                                     │
│  Output: Scores + Justifications + Confidence     │
│                                                   │
└─────────────────────────────────────────────────┘
```

### Avoiding Evaluation Pitfalls

**Anti-pattern: Scoring without justification**

- Problem: Scores lack grounding, difficult to debug or improve
- Solution: Always require evidence-based justification before score

**Anti-pattern: Single-pass pairwise comparison**

- Problem: Position bias corrupts results
- Solution: Always swap positions and check consistency

**Anti-pattern: Overloaded criteria**

- Problem: Criteria measuring multiple things are unreliable
- Solution: One criterion = one measurable aspect

**Anti-pattern: Missing edge case guidance**

- Problem: Evaluators handle ambiguous cases inconsistently
- Solution: Include edge cases in rubrics with explicit guidance

**Anti-pattern: Ignoring confidence calibration**

- Problem: High-confidence wrong judgments are worse than low-confidence
- Solution: Calibrate confidence to position consistency and evidence strength

### Decision Framework: Direct vs. Pairwise

Use this decision tree:

```
Is there an objective ground truth?
├── Yes → Direct Scoring
│   └── Examples: factual accuracy, instruction following, format compliance
│
└── No → Is it a preference or quality judgment?
    ├── Yes → Pairwise Comparison
    │   └── Examples: tone, style, persuasiveness, creativity
    │
    └── No → Consider reference-based evaluation
        └── Examples: summarization (compare to source), translation (compare to reference)
```

### Scaling Evaluation

For high-volume evaluation:

1. **Panel of LLMs (PoLL)**: Use multiple models as judges, aggregate votes
   - Reduces individual model bias
   - More expensive but more reliable for high-stakes decisions

2. **Hierarchical evaluation**: Fast cheap model for screening, expensive model for edge cases
   - Cost-effective for large volumes
   - Requires calibration of screening threshold

3. **Human-in-the-loop**: Automated evaluation for clear cases, human review for low-confidence
   - Best reliability for critical applications
   - Design feedback loop to improve automated evaluation


## Examples

### Example 1: Direct Scoring for Accuracy

**Input**:
```
Prompt: "What causes seasons on Earth?"
Response: "Seasons are caused by Earth's tilted axis. As Earth orbits the Sun, 
different hemispheres receive more direct sunlight at different times of year."
Criterion: Factual Accuracy (weight: 1.0)
Scale: 1-5
```

**Output**:
```json
{
  "criterion": "Factual Accuracy",
  "score": 5,
  "evidence": [
    "Correctly identifies axial tilt as primary cause",
    "Correctly explains differential sunlight by hemisphere",
    "No factual errors present"
  ],
  "justification": "Response accurately explains the cause of seasons with correct 
scientific reasoning. Both the axial tilt and its effect on sunlight distribution 
are correctly described.",
  "improvement": "Could add the specific tilt angle (23.5°) for completeness."
}
```

### Example 2: Pairwise Comparison with Position Swap

**Input**:
```
Prompt: "Explain machine learning to a beginner"
Response A: [Technical explanation with jargon]
Response B: [Simple analogy-based explanation]
Criteria: ["clarity", "accessibility"]
```

**First Pass (A first)**:
```json
{ "winner": "B", "confidence": 0.8 }
```

**Second Pass (B first)**:
```json
{ "winner": "A", "confidence": 0.6 }
```
(Note: Winner is A because B was in first position)

**Mapped Second Pass**:
```json
{ "winner": "B", "confidence": 0.6 }
```

**Final Result**:
```json
{
  "winner": "B",
  "confidence": 0.7,
  "positionConsistency": {
    "consistent": true,
    "firstPassWinner": "B",
    "secondPassWinner": "B"
  }
}
```

### Example 3: Rubric Generation

**Input**:
```
criterionName: "Code Readability"
criterionDescription: "How easy the code is to understand and maintain"
domain: "software engineering"
scale: "1-5"
strictness: "balanced"
```

**Output** (abbreviated):
```json
{
  "levels": [
    {
      "score": 1,
      "label": "Poor",
      "description": "Code is difficult to understand without significant effort",
      "characteristics": [
        "No meaningful variable or function names",
        "No comments or documentation",
        "Deeply nested or convoluted logic"
      ]
    },
    {
      "score": 3,
      "label": "Adequate",
      "description": "Code is understandable with some effort",
      "characteristics": [
        "Most variables have meaningful names",
        "Basic comments present for complex sections",
        "Logic is followable but could be cleaner"
      ]
    },
    {
      "score": 5,
      "label": "Excellent",
      "description": "Code is immediately clear and maintainable",
      "characteristics": [
        "All names are descriptive and consistent",
        "Comprehensive documentation",
        "Clean, modular structure"
      ]
    }
  ],
  "edgeCases": [
    {
      "situation": "Code is well-structured but uses domain-specific abbreviations",
      "guidance": "Score based on readability for domain experts, not general audience"
    }
  ]
}
```

### Iterative Improvement Workflow

1. **Identify weakness**: Use evaluation to find where agent struggles
2. **Hypothesize cause**: Is it the prompt? The context? The examples?
3. **Modify prompt**: Make targeted changes based on hypothesis
4. **Re-evaluate**: Run same test cases with modified prompt
5. **Compare**: Did the change improve the target dimension?
6. **Check regression**: Did other dimensions suffer?
7. **Iterate**: Repeat until quality meets threshold


## Guidelines

1. **Always require justification before scores** - Chain-of-thought prompting improves reliability by 15-25%

2. **Always swap positions in pairwise comparison** - Single-pass comparison is corrupted by position bias

3. **Match scale granularity to rubric specificity** - Don't use 1-10 without detailed level descriptions

4. **Separate objective and subjective criteria** - Use direct scoring for objective, pairwise for subjective

5. **Include confidence scores** - Calibrate to position consistency and evidence strength

6. **Define edge cases explicitly** - Ambiguous situations cause the most evaluation variance

7. **Use domain-specific rubrics** - Generic rubrics produce generic (less useful) evaluations

8. **Validate against human judgments** - Automated evaluation is only valuable if it correlates with human assessment

9. **Monitor for systematic bias** - Track disagreement patterns by criterion and response type

10. **Design for iteration** - Evaluation systems improve with feedback loops

## Example: Evaluating a Claude Code Command

Suppose you've created a `/refactor` command and want to evaluate its quality:

**Test Cases**:

1. Simple: Rename a variable across a single file
2. Medium: Extract a function from existing code
3. Complex: Refactor a class to use a new design pattern
4. Very Complex: Restructure module dependencies

**Evaluation Rubric**:

- Correctness: Does the refactored code work?
- Completeness: Were all instances updated?
- Style: Does it follow project conventions?
- Efficiency: Were unnecessary changes avoided?

**Evaluation Prompt**:

```markdown
Evaluate this refactoring output:

Original Code:
{original}

Refactored Code:
{refactored}

Request:
{user_request}

Score 1-5 on each dimension with evidence:
1. Correctness: Does the code still work correctly?
2. Completeness: Were all relevant instances updated?
3. Style: Does it follow the project's coding patterns?
4. Efficiency: Were only necessary changes made?

Provide scores with specific evidence from the code.
```

**Iteration**:
If evaluation reveals the command often misses instances:

1. Add explicit instruction: "Search the entire codebase for all occurrences"
2. Re-evaluate with same test cases
3. Compare completeness scores
4. Check that correctness didn't regress



# Bias Mitigation Techniques for LLM Evaluation

This reference details specific techniques for mitigating known biases in LLM-as-a-Judge systems.

## Position Bias

### The Problem

In pairwise comparison, LLMs systematically prefer responses in certain positions. Research shows:
- GPT has mild first-position bias (~55% preference for first position in ties)
- Claude shows similar patterns
- Smaller models often show stronger bias

### Mitigation: Position Swapping Protocol

```python
async def position_swap_comparison(response_a, response_b, prompt, criteria):
    # Pass 1: Original order
    result_ab = await compare(response_a, response_b, prompt, criteria)
    
    # Pass 2: Swapped order
    result_ba = await compare(response_b, response_a, prompt, criteria)
    
    # Map second result (A in second position → B in first)
    result_ba_mapped = {
        'winner': {'A': 'B', 'B': 'A', 'TIE': 'TIE'}[result_ba['winner']],
        'confidence': result_ba['confidence']
    }
    
    # Consistency check
    if result_ab['winner'] == result_ba_mapped['winner']:
        return {
            'winner': result_ab['winner'],
            'confidence': (result_ab['confidence'] + result_ba_mapped['confidence']) / 2,
            'position_consistent': True
        }
    else:
        # Disagreement indicates position bias was a factor
        return {
            'winner': 'TIE',
            'confidence': 0.5,
            'position_consistent': False,
            'bias_detected': True
        }
```

### Alternative: Multiple Shuffles

For higher reliability, use multiple position orderings:

```python
async def multi_shuffle_comparison(response_a, response_b, prompt, criteria, n_shuffles=3):
    results = []
    for i in range(n_shuffles):
        if i % 2 == 0:
            r = await compare(response_a, response_b, prompt, criteria)
        else:
            r = await compare(response_b, response_a, prompt, criteria)
            r['winner'] = {'A': 'B', 'B': 'A', 'TIE': 'TIE'}[r['winner']]
        results.append(r)
    
    # Majority vote
    winners = [r['winner'] for r in results]
    final_winner = max(set(winners), key=winners.count)
    agreement = winners.count(final_winner) / len(winners)
    
    return {
        'winner': final_winner,
        'confidence': agreement,
        'n_shuffles': n_shuffles
    }
```

## Length Bias

### The Problem

LLMs tend to rate longer responses higher, regardless of quality. This manifests as:
- Verbose responses receiving inflated scores
- Concise but complete responses penalized
- Padding and repetition being rewarded

### Mitigation: Explicit Prompting

Include anti-length-bias instructions in the prompt:

```
CRITICAL EVALUATION GUIDELINES:
- Do NOT prefer responses because they are longer
- Concise, complete answers are as valuable as detailed ones
- Penalize unnecessary verbosity or repetition
- Focus on information density, not word count
```

### Mitigation: Length-Normalized Scoring

```python
def length_normalized_score(score, response_length, target_length=500):
    """Adjust score based on response length."""
    length_ratio = response_length / target_length
    
    if length_ratio > 2.0:
        # Penalize excessively long responses
        penalty = (length_ratio - 2.0) * 0.1
        return max(score - penalty, 1)
    elif length_ratio < 0.3:
        # Penalize excessively short responses
        penalty = (0.3 - length_ratio) * 0.5
        return max(score - penalty, 1)
    else:
        return score
```

### Mitigation: Separate Length Criterion

Make length a separate, explicit criterion so it's not implicitly rewarded:

```python
criteria = [
    {"name": "Accuracy", "description": "Factual correctness", "weight": 0.4},
    {"name": "Completeness", "description": "Covers key points", "weight": 0.3},
    {"name": "Conciseness", "description": "No unnecessary content", "weight": 0.3}  # Explicit
]
```

## Self-Enhancement Bias

### The Problem

Models rate outputs generated by themselves (or similar models) higher than outputs from different models.

### Mitigation: Cross-Model Evaluation

Use a different model family for evaluation than generation:

```python
def get_evaluator_model(generator_model):
    """Select evaluator to avoid self-enhancement bias."""
    if 'gpt' in generator_model.lower():
        return 'claude-4-5-sonnet'
    elif 'claude' in generator_model.lower():
        return 'gpt-5.2'
    else:
        return 'gpt-5.2'  # Default
```

### Mitigation: Blind Evaluation

Remove model attribution from responses before evaluation:

```python
def anonymize_response(response, model_name):
    """Remove model-identifying patterns."""
    patterns = [
        f"As {model_name}",
        "I am an AI",
        "I don't have personal opinions",
        # Model-specific patterns
    ]
    anonymized = response
    for pattern in patterns:
        anonymized = anonymized.replace(pattern, "[REDACTED]")
    return anonymized
```

## Verbosity Bias

### The Problem

Detailed explanations receive higher scores even when the extra detail is irrelevant or incorrect.

### Mitigation: Relevance-Weighted Scoring

```python
async def relevance_weighted_evaluation(response, prompt, criteria):
    # First, assess relevance of each segment
    relevance_scores = await assess_relevance(response, prompt)
    
    # Weight evaluation by relevance
    segments = split_into_segments(response)
    weighted_scores = []
    for segment, relevance in zip(segments, relevance_scores):
        if relevance > 0.5:  # Only count relevant segments
            score = await evaluate_segment(segment, prompt, criteria)
            weighted_scores.append(score * relevance)
    
    return sum(weighted_scores) / len(weighted_scores)
```

### Mitigation: Rubric with Verbosity Penalty

Include explicit verbosity penalties in rubrics:

```python
rubric_levels = [
    {
        "score": 5,
        "description": "Complete and concise. All necessary information, nothing extraneous.",
        "characteristics": ["Every sentence adds value", "No repetition", "Appropriately scoped"]
    },
    {
        "score": 3,
        "description": "Complete but verbose. Contains unnecessary detail or repetition.",
        "characteristics": ["Main points covered", "Some tangents", "Could be more concise"]
    },
    # ... etc
]
```

## Authority Bias

### The Problem

Confident, authoritative tone is rated higher regardless of accuracy.

### Mitigation: Evidence Requirement

Require explicit evidence for claims:

```
For each claim in the response:
1. Identify whether it's a factual claim
2. Note if evidence or sources are provided
3. Score based on verifiability, not confidence

IMPORTANT: Confident claims without evidence should NOT receive higher scores than 
hedged claims with evidence.
```

### Mitigation: Fact-Checking Layer

Add a fact-checking step before scoring:

```python
async def fact_checked_evaluation(response, prompt, criteria):
    # Extract claims
    claims = await extract_claims(response)
    
    # Fact-check each claim
    fact_check_results = await asyncio.gather(*[
        verify_claim(claim) for claim in claims
    ])
    
    # Adjust score based on fact-check results
    accuracy_factor = sum(r['verified'] for r in fact_check_results) / len(fact_check_results)
    
    base_score = await evaluate(response, prompt, criteria)
    return base_score * (0.7 + 0.3 * accuracy_factor)  # At least 70% of score
```

## Aggregate Bias Detection

Monitor for systematic biases in production:

```python
class BiasMonitor:
    def __init__(self):
        self.evaluations = []
    
    def record(self, evaluation):
        self.evaluations.append(evaluation)
    
    def detect_position_bias(self):
        """Detect if first position wins more often than expected."""
        first_wins = sum(1 for e in self.evaluations if e['first_position_winner'])
        expected = len(self.evaluations) * 0.5
        z_score = (first_wins - expected) / (expected * 0.5) ** 0.5
        return {'bias_detected': abs(z_score) > 2, 'z_score': z_score}
    
    def detect_length_bias(self):
        """Detect if longer responses score higher."""
        from scipy.stats import spearmanr
        lengths = [e['response_length'] for e in self.evaluations]
        scores = [e['score'] for e in self.evaluations]
        corr, p_value = spearmanr(lengths, scores)
        return {'bias_detected': corr > 0.3 and p_value < 0.05, 'correlation': corr}
```

## Summary Table

| Bias | Primary Mitigation | Secondary Mitigation | Detection Method |
|------|-------------------|---------------------|------------------|
| Position | Position swapping | Multiple shuffles | Consistency check |
| Length | Explicit prompting | Length normalization | Length-score correlation |
| Self-enhancement | Cross-model evaluation | Anonymization | Model comparison study |
| Verbosity | Relevance weighting | Rubric penalties | Relevance scoring |
| Authority | Evidence requirement | Fact-checking layer | Confidence-accuracy correlation |

# LLM-as-Judge Implementation Patterns for Claude Code

This reference provides practical prompt patterns and workflows for evaluating Claude Code commands, skills, and agents during development.

## Pattern 1: Structured Evaluation Workflow

The most reliable evaluation follows a structured workflow that separates concerns:

```
Define Criteria → Gather Test Cases → Run Evaluation → Mitigate Bias → Interpret Results
```

### Step 1: Define Evaluation Criteria

Before evaluating, establish clear criteria. Document them in a reusable format:

```markdown
## Evaluation Criteria for [Command/Skill Name]

### Criterion 1: Instruction Following (weight: 0.30)
- **Description**: Does the output follow all explicit instructions?
- **1 (Poor)**: Ignores or misunderstands core instructions
- **3 (Adequate)**: Follows main instructions, misses some details
- **5 (Excellent)**: Follows all instructions precisely

### Criterion 2: Output Completeness (weight: 0.25)
- **Description**: Are all requested aspects covered?
- **1 (Poor)**: Major aspects missing
- **3 (Adequate)**: Core aspects covered with gaps
- **5 (Excellent)**: All aspects thoroughly addressed

### Criterion 3: Tool Efficiency (weight: 0.20)
- **Description**: Were appropriate tools used efficiently?
- **1 (Poor)**: Wrong tools or excessive redundant calls
- **3 (Adequate)**: Appropriate tools with some redundancy
- **5 (Excellent)**: Optimal tool selection, minimal calls

### Criterion 4: Reasoning Quality (weight: 0.15)
- **Description**: Is the reasoning clear and sound?
- **1 (Poor)**: No apparent reasoning or flawed logic
- **3 (Adequate)**: Basic reasoning present
- **5 (Excellent)**: Clear, logical reasoning throughout

### Criterion 5: Response Coherence (weight: 0.10)
- **Description**: Is the output well-structured and clear?
- **1 (Poor)**: Difficult to follow or incoherent
- **3 (Adequate)**: Understandable but could be clearer
- **5 (Excellent)**: Well-structured, easy to follow
```

### Step 2: Create Test Cases

Structure test cases by complexity level:

```markdown
## Test Cases for /refactor Command

### Simple (Single Operation)
- **Input**: Rename variable `x` to `count` in a single file
- **Expected**: All instances renamed, code still runs
- **Complexity**: Low

### Medium (Multiple Operations)
- **Input**: Extract function from 20-line code block
- **Expected**: New function created, original call site updated, behavior preserved
- **Complexity**: Medium

### Complex (Cross-File Changes)
- **Input**: Refactor class to use Strategy pattern
- **Expected**: Interface created, implementations separated, all usages updated
- **Complexity**: High

### Edge Case
- **Input**: Refactor code with conflicting variable names in nested scopes
- **Expected**: Correct scoping preserved, no accidental shadowing
- **Complexity**: Edge case
```

### Step 3: Run Direct Scoring Evaluation

Use this prompt template to evaluate a single output:

```markdown
You are evaluating the output of a Claude Code command.

## Original Task
{paste the user's original request}

## Command Output
{paste the full command output including tool calls}

## Evaluation Criteria
{paste your criteria definitions from Step 1}

## Instructions
For each criterion:
1. Find specific evidence in the output that supports your assessment
2. Assign a score (1-5) based on the rubric levels
3. Write a 1-2 sentence justification citing the evidence
4. Suggest one specific improvement

IMPORTANT: Provide your justification BEFORE stating the score. This improves evaluation reliability.

## Output Format
For each criterion, respond with:

### [Criterion Name]
**Evidence**: [Quote or describe specific parts of the output]
**Justification**: [Explain how the evidence maps to the rubric level]
**Score**: [1-5]
**Improvement**: [One actionable suggestion]

### Overall Assessment
**Weighted Score**: [Calculate: sum of (score × weight)]
**Pass/Fail**: [Pass if weighted score ≥ 3.5]
**Summary**: [2-3 sentences summarizing strengths and weaknesses]
```

### Step 4: Mitigate Position Bias in Comparisons

When comparing two prompt variants (A vs B), use this two-pass workflow:

**Pass 1 (A First):**
```markdown
You are comparing two outputs from different prompt variants.

## Original Task
{task description}

## Output A (First Variant)
{output from prompt variant A}

## Output B (Second Variant)
{output from prompt variant B}

## Comparison Criteria
- Instruction Following
- Output Completeness
- Reasoning Quality

## Critical Instructions
- Do NOT prefer outputs because they are longer
- Do NOT prefer outputs based on their position (first vs second)
- Focus ONLY on quality differences
- TIE is acceptable when outputs are equivalent

## Analysis Process
1. Analyze Output A independently: [strengths, weaknesses]
2. Analyze Output B independently: [strengths, weaknesses]
3. Compare on each criterion
4. Determine winner with confidence (0-1)

## Output
Reasoning: [Explain why]
Winner: [A/B/TIE]
Confidence: [0.0-1.0]
```

**Pass 2 (B First):**
Repeat the same prompt but swap the order—put Output B first and Output A second.

**Interpret Results:**
- If both passes agree → Winner confirmed, average the confidences
- If passes disagree → Result is TIE with confidence 0.5 (position bias detected)

## Pattern 2: Hierarchical Evaluation Workflow

For complex evaluations, use a hierarchical approach:

```
Quick Screen (cheap model) → Detailed Evaluation (expensive model) → Human Review (edge cases)
```

### Tier 1: Quick Screen (Use Haiku)

```markdown
Rate this command output 0-10 for basic adequacy.

Task: {brief task description}
Output: {command output}

Quick assessment: Does this output reasonably address the task?
Score (0-10):
One-line reasoning:
```

**Decision rule**: Score < 5 → Fail, Score ≥ 7 → Pass, Score 5-7 → Escalate to detailed evaluation

### Tier 2: Detailed Evaluation (Use Opus)

Use the full direct scoring prompt from Pattern 1 for borderline cases.

### Tier 3: Human Review

For low-confidence automated evaluations (confidence < 0.6), queue for manual review:

```markdown
## Human Review Request

**Automated Score**: 3.2/5 (Confidence: 0.45)
**Reason for Escalation**: Low confidence, evaluator disagreed across passes

### What to Review
1. Does the output actually complete the task?
2. Are the automated criterion scores reasonable?
3. What did the automation miss?

### Original Task
{task}

### Output
{output}

### Automated Assessment
{paste automated evaluation}

### Human Override
[ ] Agree with automation
[ ] Override to PASS - Reason: ___
[ ] Override to FAIL - Reason: ___
```

## Pattern 3: Panel of LLM Judges (PoLL)

For high-stakes evaluation, use multiple models::

### Workflow

1. **Run 3 independent evaluations** with different prompt framings:
   - Evaluation 1: Standard criteria prompt
   - Evaluation 2: Adversarial framing ("Find problems with this output")
   - Evaluation 3: User perspective ("Would a developer be satisfied?")

2. **Aggregate results**:
   - Take median score per criterion (robust to outliers)
   - Flag criteria with high variance (std > 1.0) for review
   - Overall pass requires majority agreement

### Multi-Judge Prompt Variants

**Standard Framing:**
```markdown
Evaluate this output against the specified criteria. Be fair and balanced.
```

**Adversarial Framing:**
```markdown
Your role is to find problems with this output. Be critical and thorough.
Look for: factual errors, missing requirements, inefficiencies, unclear explanations.
```

**User Perspective:**
```markdown
Imagine you're a developer who requested this task.
Would you be satisfied with this result? Would you need to redo any work?
```

### Agreement Analysis

After running all judges, check consistency:

| Criterion | Judge 1 | Judge 2 | Judge 3 | Median | Std Dev |
|-----------|---------|---------|---------|--------|---------|
| Instruction Following | 4 | 4 | 5 | 4 | 0.58 |
| Completeness | 3 | 4 | 3 | 3 | 0.58 |
| Tool Efficiency | 2 | 3 | 4 | 3 | 1.00 ⚠️ |

**⚠️ High variance** on Tool Efficiency suggests the criterion needs clearer definition or the output has ambiguous efficiency characteristics.

## Pattern 4: Confidence Calibration

Confidence scores should be calibrated to actual reliability:

### Confidence Factors

| Factor | High Confidence | Low Confidence |
|--------|-----------------|----------------|
| Position consistency | Both passes agree | Passes disagree |
| Evidence count | 3+ specific citations | Vague or no citations |
| Criterion agreement | All criteria align | Criteria scores vary widely |
| Edge case match | Similar to known cases | Novel situation |

### Calibration Prompt Addition

Add this to evaluation prompts:

```markdown
## Confidence Assessment

After scoring, assess your confidence:

1. **Evidence Strength**: How specific was the evidence you cited?
   - Strong: Quoted exact passages, precise observations
   - Moderate: General observations, reasonable inferences
   - Weak: Vague impressions, assumptions

2. **Criterion Clarity**: How clear were the criterion boundaries?
   - Clear: Easy to map output to rubric levels
   - Ambiguous: Output fell between levels
   - Unclear: Rubric didn't fit this case

3. **Overall Confidence**: [0.0-1.0]
   - 0.9+: Very confident, clear evidence, obvious rubric fit
   - 0.7-0.9: Confident, good evidence, minor ambiguity
   - 0.5-0.7: Moderate confidence, some ambiguity
   - <0.5: Low confidence, significant uncertainty

Confidence: [score]
Confidence Reasoning: [explain what factors affected confidence]
```

## Pattern 5: Structured Output Format

Request consistent output structure for easier analysis:

### Evaluation Output Template

```markdown
## Evaluation Results

### Metadata
- **Evaluated**: [command/skill name]
- **Test Case**: [test case ID or description]
- **Evaluator**: [model used]
- **Timestamp**: [when evaluated]

### Criterion Scores

| Criterion | Score | Weight | Weighted | Confidence |
|-----------|-------|--------|----------|------------|
| Instruction Following | 4/5 | 0.30 | 1.20 | 0.85 |
| Output Completeness | 3/5 | 0.25 | 0.75 | 0.70 |
| Tool Efficiency | 5/5 | 0.20 | 1.00 | 0.90 |
| Reasoning Quality | 4/5 | 0.15 | 0.60 | 0.75 |
| Response Coherence | 4/5 | 0.10 | 0.40 | 0.80 |

### Summary
- **Overall Score**: 3.95/5.0
- **Pass Threshold**: 3.5/5.0
- **Result**: ✅ PASS

### Evidence Summary
- **Strengths**: [bullet points]
- **Weaknesses**: [bullet points]
- **Improvements**: [prioritized suggestions]

### Confidence Assessment
- **Overall Confidence**: 0.78
- **Flags**: [any concerns or caveats]
```

## Evaluation Workflows for Claude Code Development

### Workflow: Testing a New Command

1. **Write 5-10 test cases** spanning complexity levels
2. **Run command** on each test case, capture full output
3. **Quick screen** all outputs with Tier 1 evaluation
4. **Detailed evaluate** failures and borderline cases
5. **Identify patterns** in failures to guide prompt improvements
6. **Iterate prompt** based on specific weaknesses found
7. **Re-evaluate** same test cases to measure improvement

### Workflow: Comparing Prompt Variants

1. **Create variant prompts** (e.g., different instruction phrasings)
2. **Run both variants** on identical test cases
3. **Pairwise compare** with position swapping
4. **Calculate win rate** for each variant
5. **Analyze** which cases each variant handles better
6. **Decide**: Pick winner or create hybrid

### Workflow: Regression Testing

1. **Maintain test suite** of representative cases
2. **Before changes**: Run evaluation, record baseline scores
3. **After changes**: Re-run evaluation
4. **Compare**: Flag regressions (score drops > 0.5)
5. **Investigate**: Why did specific cases regress?
6. **Accept or revert**: Based on overall impact

### Workflow: Continuous Quality Monitoring

1. **Sample production usage** (if available)
2. **Run lightweight evaluation** on samples
3. **Track metrics over time**:
   - Average scores by criterion
   - Failure rate
   - Low-confidence rate
4. **Alert on degradation**: Score drop > 10% from baseline
5. **Periodic deep dive**: Monthly detailed evaluation on random sample

## Anti-Patterns to Avoid

### ❌ Scoring Without Justification
**Problem**: Scores lack grounding, difficult to debug
**Solution**: Always require evidence before score

### ❌ Single-Pass Pairwise Comparison
**Problem**: Position bias corrupts results
**Solution**: Always swap positions and check consistency

### ❌ Overloaded Criteria
**Problem**: Criteria measuring multiple things are unreliable
**Solution**: One criterion = one measurable aspect

### ❌ Missing Edge Case Guidance
**Problem**: Evaluators handle ambiguous cases inconsistently
**Solution**: Include edge cases in rubrics with explicit guidance

### ❌ Ignoring Low Confidence
**Problem**: Acting on uncertain evaluations leads to wrong conclusions
**Solution**: Escalate low-confidence cases for human review

### ❌ Generic Rubrics
**Problem**: Generic criteria produce vague, unhelpful evaluations
**Solution**: Create domain-specific rubrics (code commands vs documentation commands vs analysis commands)

## Handling Evaluation Failures

When evaluations fail or produce unreliable results, use these recovery strategies:

### Malformed Output Disregard

When the evaluator produces unparseable or incomplete output:

1. **Mark as invalid and ingore for analysis** - incorrect output, usally means halicunations during thinking process

2. **Retry initial prompt without chagnes** - multiple retries usally more consistent rahter one shot prompt

3. **if still produce incorrect output, flag for human review**: Mark as "evaluation failed, needs manual check" and queue for later

### Validation Checklist

Before trusting evaluation results, verify:

- [ ] All criteria have scores in valid range (1-5)
- [ ] Each score has a justification referencing specific evidence
- [ ] Confidence score is provided and reasonable
- [ ] No contradictions between justification and assigned score
- [ ] Weighted total calculation is correct

## Validating Evaluation Prompts (Meta-Evaluation)

Before using an evaluation prompt in production, test it against known cases:

### Calibration Test Cases

Create a small set of outputs with known quality levels:

| Test Type | Description | Expected Score |
|-----------|-------------|----------------|
| Known-good | Clearly excellent output | 4.5+ / 5.0 |
| Known-bad | Clearly poor output | < 2.5 / 5.0 |
| Boundary | Borderline case | 3.0-3.5 with nuanced explanation |

### Validation Workflow

1. **Known-good test**: Evaluate a clearly excellent output
   - If score < 4.0 → Rubric is too strict or evidence requirements unclear

2. **Known-bad test**: Evaluate a clearly poor output
   - If score > 3.0 → Rubric is too lenient or criteria not specific enough

3. **Boundary test**: Evaluate a borderline case
   - Should produce moderate score (3.0-3.5) with detailed explanation
   - If confident high/low score → Criteria lack nuance

4. **Consistency test**: Run same evaluation 3 times
   - Score variance should be < 0.5
   - If higher variance → Criteria need tighter definitions

### Position Bias Validation

Test for position bias before using pairwise comparisons:

```markdown
## Position Bias Test

Run this test with IDENTICAL outputs in both positions:

Test Case: [Same output text]
Position A: [Paste output]
Position B: [Paste identical output]

Expected Result: TIE with high confidence (>0.9)

If Result Shows Winner:
- Position bias detected
- Add stronger anti-bias instructions to prompt
- Re-test until TIE achieved consistently
```

### Evaluation Prompt Iteration

When calibration tests fail:

1. **Identify failure mode**: Too strict? Too lenient? Inconsistent?
2. **Adjust specific rubric levels**: Add examples, clarify boundaries
3. **Re-run calibration tests**: All 4 tests must pass
4. **Document changes**: Track what adjustments improved reliability

# Metric Selection Guide for LLM Evaluation

This reference provides guidance on selecting appropriate metrics for different evaluation scenarios.

## Metric Categories

### Classification Metrics

Use for binary or multi-class evaluation tasks (pass/fail, correct/incorrect).

#### Precision

```
Precision = True Positives / (True Positives + False Positives)
```

**Interpretation**: Of all responses the judge said were good, what fraction were actually good?

**Use when**: False positives are costly (e.g., approving unsafe content)

#### Recall

```
Recall = True Positives / (True Positives + False Negatives)
```

**Interpretation**: Of all actually good responses, what fraction did the judge identify?

**Use when**: False negatives are costly (e.g., missing good content in filtering)

#### F1 Score

```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Interpretation**: Harmonic mean of precision and recall

**Use when**: You need a single number balancing both concerns

### Agreement Metrics

Use for comparing automated evaluation with human judgment.

#### Cohen's Kappa (κ)

```
κ = (Observed Agreement - Expected Agreement) / (1 - Expected Agreement)
```

**Interpretation**: Agreement adjusted for chance
- κ > 0.8: Almost perfect agreement
- κ 0.6-0.8: Substantial agreement
- κ 0.4-0.6: Moderate agreement
- κ < 0.4: Fair to poor agreement

**Use for**: Binary or categorical judgments

#### Weighted Kappa

For ordinal scales where disagreement severity matters:

**Interpretation**: Penalizes large disagreements more than small ones

### Correlation Metrics

Use for ordinal/continuous scores.

#### Spearman's Rank Correlation (ρ)

**Interpretation**: Correlation between rankings, not absolute values
- ρ > 0.9: Very strong correlation
- ρ 0.7-0.9: Strong correlation
- ρ 0.5-0.7: Moderate correlation
- ρ < 0.5: Weak correlation

**Use when**: Order matters more than exact values

#### Kendall's Tau (τ)

**Interpretation**: Similar to Spearman but based on pairwise concordance

**Use when**: You have many tied values

#### Pearson Correlation (r)

**Interpretation**: Linear correlation between scores

**Use when**: Exact score values matter, not just order

### Pairwise Comparison Metrics

#### Agreement Rate

```
Agreement = (Matching Decisions) / (Total Comparisons)
```

**Interpretation**: Simple percentage of agreement

#### Position Consistency

```
Consistency = (Consistent across position swaps) / (Total comparisons)
```

**Interpretation**: How often does swapping position change the decision?

## Selection Decision Tree

```
What type of evaluation task?
│
├── Binary classification (pass/fail)
│   └── Use: Precision, Recall, F1, Cohen's κ
│
├── Ordinal scale (1-5 rating)
│   ├── Comparing to human judgments?
│   │   └── Use: Spearman's ρ, Weighted κ
│   └── Comparing two automated judges?
│       └── Use: Kendall's τ, Spearman's ρ
│
├── Pairwise preference
│   └── Use: Agreement rate, Position consistency
│
└── Multi-label classification
    └── Use: Macro-F1, Micro-F1, Per-label metrics
```

## Metric Selection by Use Case

### Use Case 1: Validating Automated Evaluation

**Goal**: Ensure automated evaluation correlates with human judgment

**Recommended Metrics**:
1. Primary: Spearman's ρ (for ordinal scales) or Cohen's κ (for categorical)
2. Secondary: Per-criterion agreement
3. Diagnostic: Confusion matrix for systematic errors

### Use Case 2: Comparing Two Models

**Goal**: Determine which model produces better outputs

**Recommended Metrics**:
1. Primary: Win rate (from pairwise comparison)
2. Secondary: Position consistency (bias check)
3. Diagnostic: Per-criterion breakdown

### Use Case 3: Quality Monitoring

**Goal**: Track evaluation quality over time

**Recommended Metrics**:
1. Primary: Rolling agreement with human spot-checks
2. Secondary: Score distribution stability
3. Diagnostic: Bias indicators (position, length)

## Interpreting Metric Results

### Good Evaluation System Indicators

| Metric | Good | Acceptable | Concerning |
|--------|------|------------|------------|
| Spearman's ρ | > 0.8 | 0.6-0.8 | < 0.6 |
| Cohen's κ | > 0.7 | 0.5-0.7 | < 0.5 |
| Position consistency | > 0.9 | 0.8-0.9 | < 0.8 |
| Length correlation | < 0.2 | 0.2-0.4 | > 0.4 |

### Warning Signs

1. **High agreement but low correlation**: May indicate calibration issues
2. **Low position consistency**: Position bias affecting results
3. **High length correlation**: Length bias inflating scores
4. **Per-criterion variance**: Some criteria may be poorly defined

## Reporting Template

```markdown
## Evaluation System Metrics Report

### Human Agreement
- Spearman's ρ: 0.82 (p < 0.001)
- Cohen's κ: 0.74
- Sample size: 500 evaluations

### Bias Indicators
- Position consistency: 91%
- Length-score correlation: 0.12

### Per-Criterion Performance
| Criterion | Spearman's ρ | κ |
|-----------|--------------|---|
| Accuracy | 0.88 | 0.79 |
| Clarity | 0.76 | 0.68 |
| Completeness | 0.81 | 0.72 |

### Recommendations
- All metrics within acceptable ranges
- Monitor "Clarity" criterion - lower agreement may indicate need for rubric refinement
```
