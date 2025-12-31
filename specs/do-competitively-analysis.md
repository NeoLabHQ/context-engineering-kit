# Analysis: Improving /do-competitively Command

This document analyzes the current GCS (Generate-Critique-Synthesize) pattern implementation and proposes specific improvements from academic research and engineering practices.

## Current Architecture Analysis

### Strengths

| Aspect | Strength |
|--------|----------|
| **Parallel exploration** | 3 independent agents explore solution space without bias |
| **Multi-judge evaluation** | Independent evaluations reduce individual judge bias |
| **Evidence-based synthesis** | Combines best elements rather than simple voting |
| **Cost-aware** | Explicit cost considerations for practical use |

### Limitations

| Limitation | Impact |
|------------|--------|
| **No intermediate feedback** | Generators can't course-correct during work |
| **No judge interaction** | Judges don't challenge each other's reasoning |
| **Single synthesis pass** | No iteration if synthesis is flawed |
| **No structured exploration** | Generators don't systematically explore design space |
| **No learning** | Past evaluations don't inform future generations |
| **Binary decision points** | Either synthesize or pick one, no graduated approach |

## Improvement Opportunities

### 1. Tree of Thoughts Integration

**Current approach:**
```
Task → [Agent A, Agent B, Agent C] → [Solution A, B, C]
```

**ToT-enhanced approach:**
```
Task → [Agent A, B, C] → Proposals [A1, B1, C1]
                      ↓
              Preliminary Evaluation
                      ↓
              Select Top 2 Proposals
                      ↓
         [Agent A expands A1, Agent B expands B1]
                      ↓
              [Full Solution A, B]
```

**Implementation:**

```markdown
### Phase 1a: Proposal Generation (NEW)

Each agent generates 2-3 high-level approaches (not full implementations):
- Architecture sketch
- Key design decisions
- Trade-offs
- Estimated complexity

Time limit: 5 minutes per agent

### Phase 1b: Proposal Evaluation (NEW)

Quick evaluation (single judge):
- Feasibility (1-5)
- Alignment with requirements (1-5)
- Potential for quality (1-5)

Select top 2-3 proposals for full development.

### Phase 1c: Full Implementation

Only develop selected proposals → saves 1-2 agent costs
```

**Benefits:**
- Prune obviously flawed approaches early
- Focus compute on promising directions
- Reduce cost (5 agents instead of 7 if only 2 proposals selected)
- More systematic exploration of design space

**Cost:**
- +1 agent for proposal evaluation
- +5-10 minutes for proposal phase
- Net savings if fewer full implementations needed

### 2. Constitutional AI / Self-Critique

**Current approach:**
```
Agent generates solution → (no self-review) → Submit to judges
```

**Critique-enhanced approach:**
```
Agent generates solution → Self-critique → Revise → Submit to judges
```

**Implementation:**

```markdown
### Phase 1 Enhancement: Self-Critique Loop

After generating initial solution, each agent:

1. **Generate critique questions** (3-5 questions):
   - "Does this handle edge case X?"
   - "Is this approach scalable to N users?"
   - "Have I considered security implications?"

2. **Answer own questions**:
   - Review solution against each question
   - Identify gaps or weaknesses

3. **Revise solution**:
   - Fix identified issues
   - Document what was changed and why

4. **Submit revised solution**

**Prompt addition:**

"Before submitting your solution, critique it:
1. Generate 3-5 verification questions about critical aspects
2. Answer each question by examining your solution
3. Revise your solution to address any gaps
4. Document your revisions in a 'Self-Critique' section"
```

**Benefits:**
- Catches obvious errors before expensive judge evaluation
- Improves solution quality without adding agents
- Demonstrates reasoning transparency
- Reduces judge workload (fewer obvious issues)

**Cost:**
- +20% token usage per generator (minimal cost increase)
- +5 minutes per generator

### 3. Multi-Agent Debate Enhancement

**Current approach:**
```
[Judge 1, Judge 2, Judge 3] → [Report 1, Report 2, Report 3] → Synthesizer
                (no interaction)
```

**Debate-enhanced approach:**
```
[Judge 1, Judge 2, Judge 3] → Initial Assessments
                ↓
        Debate Round (judges see each other's views)
                ↓
        Revised Assessments → Synthesizer
```

**Implementation:**

```markdown
### Phase 2 Enhancement: Judge Debate

**Phase 2a: Independent Evaluation** (existing)

Each judge evaluates all solutions independently.

**Phase 2b: Debate Round (NEW)**

1. **Share evaluations**: All judges receive all other judges' reports

2. **Identify disagreements**:
   - Where judges rated same criterion differently (>1 point gap)
   - Where judges preferred different solutions

3. **Argue positions**:
   - Each judge defends their high ratings with specific evidence
   - Each judge challenges others' ratings they disagree with
   - Focus on the 2-3 biggest disagreements

4. **Revise if convinced**:
   - Judges may revise their assessments based on debate
   - Must explain what changed their mind
   - Original assessment preserved for transparency

**Prompt for debate:**

"You previously evaluated solutions [A, B, C]. Other judges disagree with you on:

Judge 2 rated Solution B's 'Design Quality' as 4/5, you rated it 2/5.
Judge 2's evidence: [quote]
Judge 2's reasoning: [summary]

Respond:
1. Do you maintain your rating? Why?
2. Did you miss evidence that Judge 2 cited?
3. Is there counter-evidence Judge 2 missed?
4. What is your revised rating (if changed)?"
```

**Benefits:**
- Resolves subjective disagreements through argumentation
- Catches evidence one judge missed but others saw
- More robust consensus than independent voting
- Reduces synthesis complexity (clearer signal)

**Cost:**
- +3 agents (one per judge for debate round)
- +10-15 minutes
- Higher quality but 2x judge cost

**When to use:**
- High-stakes decisions with subjective criteria
- When initial judge votes are split
- When quality > cost is priority

### 4. Reflexion / Learning from History

**Current approach:**
```
Each task starts fresh (no memory of past evaluations)
```

**Reflexion-enhanced approach:**
```
Task → Check memory for similar past tasks → Learn patterns → Apply learnings
```

**Implementation:**

```markdown
### Phase 0: Learn from History (NEW)

Before starting competitive generation:

1. **Check memory**: Look for past `/do-competitively` executions
   - Same task type (API design, algorithm, architecture)
   - Similar domain (auth, data processing, UI)

2. **Extract lessons**:
   - What made past winning solutions good?
   - What mistakes did past solutions make?
   - What criteria mattered most in past evaluations?

3. **Inform generators**:
   - "In past API design tasks, judges valued: [lessons]"
   - "Common mistakes to avoid: [anti-patterns]"
   - "Key considerations for this domain: [insights]"

**Memory structure:**

Store after each `/do-competitively` execution:

```yaml
task_type: "API_DESIGN"
domain: "authentication"
date: "2025-12-31"
winning_approach: "Resource-based REST with JWT"
key_success_factors:
  - "Stateless design valued for scalability"
  - "Clear error responses critical for DX"
  - "Security considerations explicitly documented"
common_mistakes:
  - "Nested routes too deep (>3 levels)"
  - "Missing rate limiting considerations"
judge_priorities:
  - security: 0.30
  - developer_experience: 0.25
  - scalability: 0.20
```

**Prompt addition for generators:**

"Based on {N} past similar tasks, successful solutions typically:
- {pattern_1}
- {pattern_2}

Common pitfalls to avoid:
- {anti_pattern_1}
- {anti_pattern_2}

Use these insights, but don't be constrained by them."
```

**Benefits:**
- Learn organizational preferences over time
- Avoid repeating past mistakes
- Faster convergence to good solutions
- Compound improvement with each use

**Cost:**
- Storage for past evaluations (~1KB per task)
- +1 minute for memory lookup and summarization
- Minimal cost, high long-term value

### 5. Chain of Verification for Judges

**Current approach:**
```
Judge evaluates → Provides scores (self-verification exists but not enforced)
```

**CoVe-enhanced approach:**
```
Judge evaluates → Generates verification questions → Answers them → Revises if needed
```

**Implementation:**

```markdown
### Phase 2 Enhancement: Structured Verification

After initial evaluation, each judge:

1. **Generate verification questions** (4-6 questions):
   - "Did I check for [edge case]?"
   - "Is my evidence for criterion X actually supporting my score?"
   - "Could this high rating be due to [known bias]?"
   - "Did I compare apples-to-apples across all solutions?"

2. **Answer verification questions**:
   - Re-examine solutions for each question
   - Find counter-evidence if it exists
   - Check for systematic bias (length, confidence, etc.)

3. **Revise scores if needed**:
   - Document what changed
   - Explain why original score was incorrect

4. **Verification attestation**:
   - [ ] Generated and answered all verification questions
   - [ ] Found and corrected at least one potential issue
   - [ ] Checked for known biases (length, verbosity, confidence)
   - [ ] Confident in revised scores

**Critical: Require at least one adjustment**

Force judges to find something to improve → reduces rubber-stamping.
```

**Benefits:**
- Catches systematic bias (length, confidence, etc.)
- Improves calibration between judges
- Transparent reasoning chain
- Already partially in judge.md, enforce here

**Cost:**
- +15% token usage per judge
- +3 minutes per judge
- Minimal cost for quality improvement

### 6. Mixture of Agents (Hierarchical Synthesis)

**Current approach:**
```
[Solution A, B, C] + [Report 1, 2, 3] → Single Synthesizer → Final Solution
```

**MoA-enhanced approach:**
```
[Solution A, B, C] + Reports → Layer 1: Pairwise Synthesis
                            ↓
                    [Hybrid A+B, Hybrid B+C]
                            ↓
                Layer 2: Final Synthesis → Best Solution
```

**Implementation:**

```markdown
### Phase 3 Enhancement: Hierarchical Synthesis

**For complex tasks only** (>500 lines, multiple subsystems):

**Phase 3a: Pairwise Synthesis**

Launch 2-3 agents in parallel:
- Agent 1: Synthesize best of A + B
- Agent 2: Synthesize best of B + C
- Agent 3: Synthesize best of A + C

Each focuses on combining two approaches deeply.

**Phase 3b: Final Synthesis**

Single agent receives:
- All 3 pairwise hybrids
- Original solutions
- Judge reports

Selects or combines the best hybrid.

**Rationale:**

Pairwise synthesis allows deeper analysis:
- More focused attention (2 solutions vs 3)
- Can thoroughly explore hybrid combinations
- Different pairings may reveal non-obvious combinations

Final synthesis picks from higher-quality candidates.
```

**Benefits:**
- Better for complex multi-aspect solutions
- More thorough exploration of combinations
- Higher quality hybrids

**Cost:**
- +2-3 agents (pairwise synthesizers)
- +15-20 minutes
- Only justified for complex tasks

**When to use:**
- Solutions >500 lines
- Multiple independent subsystems
- High complexity/stakes

### 7. Best-of-N with Verification

**Current approach:**
```
Always synthesize (even when one solution is clearly best)
```

**Adaptive approach:**
```
IF clear winner (judges agree) → Select + Polish
ELSE → Synthesize
```

**Implementation:**

```markdown
### Phase 3: Adaptive Synthesis

**Decision Logic:**

Check judge consensus:

```python
# Pseudo-code for decision
def synthesis_strategy(judge_votes, score_gaps):
    if unanimous_winner(judge_votes):
        return "SELECT_AND_POLISH"

    if large_score_gap(score_gaps):  # >1.0 point gap to second place
        return "SELECT_AND_POLISH"

    if all_solutions_flawed():
        return "REDESIGN"  # Start over with lessons learned

    return "FULL_SYNTHESIS"  # Default
```

**SELECT_AND_POLISH strategy:**

1. Take winning solution
2. Apply improvements from judge feedback
3. Cherry-pick 1-2 specific elements from runners-up
4. Much faster than full synthesis

**REDESIGN strategy:**

If all solutions scored <3.0/5.0:
1. Analyze common failure modes
2. Generate new task decomposition
3. Re-run with adjusted constraints
4. Fail fast rather than synthesize garbage

**FULL_SYNTHESIS strategy:**

Current approach (combine best elements from all).
```

**Benefits:**
- Saves synthesis cost when unnecessary
- Clearer signal (don't force synthesis when winner obvious)
- Fail-fast on universally flawed solutions
- Adaptive to task difficulty

**Cost:**
- Negligible (logic is simple)
- Can save 1 agent if selection used

### 8. Self-Consistency Expansion

**Current approach:**
```
Generate 3 solutions
```

**Self-consistency approach:**
```
Generate 5-7 solutions (more sampling)
Use voting for objective criteria
Use synthesis for subjective aspects
```

**Implementation:**

```markdown
### Phase 1 Enhancement: Expanded Sampling

For critical tasks, increase from 3 to 5-7 generators.

**Voting mechanism:**

For objective criteria (correctness, completeness):
- Use majority vote
- Example: 4/7 solutions handle edge case X → probably correct approach

For subjective criteria (design quality, readability):
- Use synthesis
- Combine preferred patterns from multiple solutions

**Prompt enhancement:**

"You are generator {N} of {total}. Other solutions exist but you cannot see them.
Diversity is valued - try a different approach than you would typically use."

**Budget option:**

Use cheaper model (Sonnet) for 5-7 generators, Opus for judges.
Cost roughly equal to 3 Opus generators.
```

**Benefits:**
- Better coverage of solution space
- Voting reduces need for complex synthesis on objective aspects
- More robust to individual agent failures
- Self-consistency improvement: +10-20% accuracy (Wang et al.)

**Cost:**
- +2-4 agents (generators)
- Can use cheaper model to offset
- +10-15 minutes

**When to use:**
- Critical correctness requirements
- Well-defined objective criteria
- When diversity of approaches is valuable

## Recommended Implementation Strategy

### Tier 1: Low-hanging fruit (immediate implementation)

These improve quality with minimal cost:

1. **Self-Critique (§2)** - +20% tokens per generator
2. **Chain of Verification enforcement (§5)** - +15% tokens per judge
3. **Adaptive Synthesis (§7)** - negligible cost
4. **Reflexion/Memory (§4)** - ~1KB storage + 1 min

**Total cost increase:** ~5-10%, significant quality improvement

### Tier 2: High-value options (implement as flags)

Add command flags to enable optionally:

```bash
/do-competitively "task" --with-debate        # §3: Judge debate
/do-competitively "task" --with-proposals     # §1: ToT proposal phase
/do-competitively "task" --expanded-sampling  # §8: 5-7 generators
```

Allow users to choose cost/quality trade-off.

### Tier 3: Complex enhancements (future work)

For specialized use cases:

- Hierarchical synthesis (§6) - only for >500 line solutions
- Full ToT with backtracking - research project complexity

## Comparison Matrix

| Enhancement | Quality Gain | Cost Increase | Complexity | Priority |
|-------------|--------------|---------------|------------|----------|
| Self-Critique | +15% | +20% tokens | Low | **HIGH** |
| Chain of Verification | +10% | +15% tokens | Low | **HIGH** |
| Adaptive Synthesis | +5% | 0% (saves cost) | Low | **HIGH** |
| Reflexion/Memory | +10% (compounds) | ~0% | Medium | **HIGH** |
| Judge Debate | +20% | +100% judges | Medium | MEDIUM |
| ToT Proposals | +15% | +20% | Medium | MEDIUM |
| Expanded Sampling | +15% | +60-130% | Low | MEDIUM |
| Hierarchical Synthesis | +10% | +40-60% | High | LOW |

## Proposed Command Evolution

### Version 1.0 (Current)

```
Phase 1: Generate (3 agents)
Phase 2: Evaluate (3 judges)
Phase 3: Synthesize (1 agent)

Total: 7 agents, ~$2-5
```

### Version 2.0 (Tier 1 improvements)

```
Phase 0: Learn from history (+1 min)
Phase 1: Generate with self-critique (3 agents, +20% tokens)
Phase 2: Evaluate with enforced verification (3 judges, +15% tokens)
Phase 3: Adaptive synthesis (1 agent, 0-100% cost depending on path)

Total: 7 agents, ~$2.50-6, +15-20% quality
```

### Version 3.0 (Tier 2 options)

```
Phase 0: Learn from history
Phase 1a: Proposal generation (3 agents, quick)
Phase 1b: Proposal evaluation (1 agent)
Phase 1c: Full implementation (2 agents, selected proposals)
Phase 2a: Independent evaluation (3 judges with verification)
Phase 2b: Judge debate [optional] (3 agents)
Phase 3: Adaptive synthesis (1 agent)

Total: 10-13 agents, ~$4-8, +30-40% quality
Configurable via flags
```

## Open Research Questions

1. **Optimal number of generators?**
   - Current: 3 (arbitrary)
   - Research: Does 5 or 7 meaningfully improve coverage?
   - Need empirical evaluation

2. **Judge debate convergence?**
   - Does debate improve consensus or create groupthink?
   - How many rounds before diminishing returns?
   - Need A/B testing

3. **Synthesis vs Selection threshold?**
   - When is synthesis better than picking best + polish?
   - What score gap indicates clear winner?
   - Need analysis of past executions

4. **Memory decay?**
   - How long are past lessons relevant?
   - Should old memories be weighted less?
   - Need longitudinal study

5. **Cost-quality frontier?**
   - What is optimal budget allocation across phases?
   - Is 3-3-1 split optimal or should we reallocate?
   - Need systematic cost/quality experiments

## Conclusion

The current GCS pattern is solid but can be significantly improved:

**Immediate wins** (Tier 1):
- Self-critique, verification enforcement, adaptive synthesis, memory
- ~+15-20% quality for ~+5-10% cost

**Optional enhancements** (Tier 2):
- Debate, proposals, expanded sampling
- User-configurable cost/quality trade-offs
- ~+30-40% quality for ~2-3x cost

**Future research** (Tier 3):
- Hierarchical synthesis, full ToT, optimal configurations
- Diminishing returns, high complexity

**Recommended path:**
1. Implement Tier 1 (low cost, high value)
2. Add Tier 2 as optional flags
3. Evaluate empirically before Tier 3

The command should evolve from "competitive generation" to "adaptive multi-agent synthesis" with intelligent strategy selection based on task characteristics and user requirements.
