---
description: Execute tasks through systematic exploration, pruning, and expansion using Tree of Thoughts methodology with multi-agent evaluation
argument-hint: Task description and optional output path/criteria
---

# tree-of-thoughts

<task>
Execute complex reasoning tasks through systematic exploration of solution space, pruning unpromising branches, expanding viable approaches, and synthesizing the best solution.
</task>

<context>
This command implements the Tree of Thoughts (ToT) pattern for tasks requiring exploration of multiple solution paths before committing to full implementation. It combines creative sampling, multi-perspective evaluation, adaptive strategy selection, and evidence-based synthesis to produce superior outcomes.

**Related resources:**
- `/do-competitively` - Competitive generation without systematic exploration
- `multi-agent-patterns` skill - Architecture patterns for multi-agent systems
- `agent-evaluation` skill - Evaluation methodologies and LLM-as-Judge patterns
</context>

## Pattern: Tree of Thoughts (ToT)

This command implements a six-phase systematic reasoning pattern with adaptive strategy selection:

```
Phase 1: Exploration (Propose Approaches)
         ┌─ Agent A → Proposals A1, A2 (with probabilities) ─┐
Task ───┼─ Agent B → Proposals B1, B2 (with probabilities) ─┼─┐
         └─ Agent C → Proposals C1, C2 (with probabilities) ─┘ │
                                                                │
Phase 2: Pruning (Vote for Best 3)                             │
         ┌─ Judge 1 → Votes + Rationale ─┐                     │
         ├─ Judge 2 → Votes + Rationale ─┼─────────────────────┤
         └─ Judge 3 → Votes + Rationale ─┘                     │
                 │                                              │
                 ├─→ Select Top 3 Proposals                     │
                 │                                              │
Phase 3: Expansion (Develop Full Solutions)                    │
         ┌─ Agent A → Solution A (from proposal X) ─┐          │
         ├─ Agent B → Solution B (from proposal Y) ─┼──────────┤
         └─ Agent C → Solution C (from proposal Z) ─┘          │
                                                                │
Phase 4: Evaluation (Judge Full Solutions)                     │
         ┌─ Judge 1 → Report 1 ─┐                              │
         ├─ Judge 2 → Report 2 ─┼──────────────────────────────┤
         └─ Judge 3 → Report 3 ─┘                              │
                                                                │
Phase 4.5: Adaptive Strategy Selection                         │
         Analyze Consensus ────────────────────────────────────┤
                ├─ Clear Winner? → SELECT_AND_POLISH           │
                ├─ All Flawed (<3.0)? → REDESIGN (Phase 3)     │
                └─ Split Decision? → FULL_SYNTHESIS            │
                                         │                      │
Phase 5: Synthesis (Only if FULL_SYNTHESIS)                    │
         Synthesizer ────────────────────┴──────────────────────┴─→ Final Solution
```

## Process

### Phase 1: Exploration (Propose Approaches)

Launch **3 independent agents in parallel** (recommended: Sonnet for speed):

1. Each agent receives **identical task description and context**
2. Each agent **generates 6 high-level approaches** (not full implementations)
3. For each approach, agent provides:
   - **Approach description** (2-3 paragraphs)
   - **Key design decisions** and trade-offs
   - **Probability estimate** (0.0-1.0) 
   - **Estimated complexity** (low/medium/high)
   - **Potential risks** and failure modes
4. Proposals saved to `proposals.a.md`, `proposals.b.md`, `proposals.c.md`

**Key principle:** Systematic exploration through probabilistic sampling from the full distribution of possible approaches.

**Prompt template for explorers:**

```markdown
<task>
{task_description}
</task>

<constraints>
{constraints_if_any}
</constraints>

<context>
{relevant_context}
</context>

<output>
proposals.[*].md where [*] is your unique identifier (a, b, or c)
</output>

Instructions:
1. Generate 6 distinct high-level approaches to this task
2. For each approach, provide:
   - Name and one-sentence summary
   - Detailed description (2-3 paragraphs)
   - Key design decisions and rationale
   - Trade-offs (what you gain vs what you sacrifice)
   - Probability (0.0-1.0): 
   - Complexity estimate (low/medium/high)
   - Potential risks and failure modes

Please sample at random from the [full distribution / tails of the distribution]
- For first 3 approaches aim for high probability, over 0.80
- For last 3 approaches aim for diversity - explore different regions of the solution space, such that the probability of each response is less than 0.10

CRITICAL:
- Do NOT implement full solutions yet - only high-level approaches
- Ensure approaches are genuinely different, not minor variations
```

### Phase 2: Pruning (Vote for Top 3 Candidates)

Launch **3 independent judges in parallel** (recommended: Sonnet for efficiency):

1. Each judge receives **ALL proposal files** (proposals.a.md, proposals.b.md, proposals.c.md)
2. Judges evaluate each proposal against **pruning criteria**:
   - **Feasibility** (1-5): Can this be implemented with available resources?
   - **Alignment** (1-5): How well does it address the task requirements?
   - **Potential** (1-5): Likelihood of producing high-quality result?
   - **Risk** (1-5, inverse): How manageable are the identified risks?
3. Each judge produces:
   - **Scores for each proposal** (with evidence)
   - **Vote for top 3 proposals** to expand
   - **Rationale** for selections
4. Votes saved to `pruning.1.md`, `pruning.2.md`, `pruning.3.md`

**Key principle:** Independent evaluation with explicit criteria reduces groupthink and catches different strengths/weaknesses.

**Prompt template for pruning judges:**

```markdown
You are evaluating {N} proposed approaches to select the top 3 for full development.

<task>
{task_description}
</task>

<proposals>
{list of paths to all proposal files}
Read all proposals carefully before evaluating.
</proposals>

<output>
pruning.[*].md where [*] is your unique identifier (1, 2, or 3)
</output>

Evaluation criteria (with weights):
1. Feasibility (25%): Can this be implemented with available resources and constraints?
2. Alignment (30%): How well does it address the task requirements and constraints?
3. Potential (30%): Likelihood of producing a high-quality, robust solution?
4. Risk (15%): How manageable are the identified risks and failure modes?

Read ${CLAUDE_PLUGIN_ROOT}/tasks/judge.md for evaluation methodology and execute using following criteria.

Instructions:
1. For each proposal, score on each criterion (1-5)
2. Provide specific evidence from the proposal for each score
3. Calculate weighted total score for each proposal
4. Vote for your top 3 proposals with clear justification
5. Consider:
   - Does the probability estimate seem realistic?
   - Are the trade-offs clearly articulated?
   - Are risks identified and addressable?
6. Generate verification 4-6 questions about your evaluation.
7. Answer verification questions:
   - Re-examine solutions for each question
   - Find counter-evidence if it exists
   - Check for systematic bias (length, confidence, etc.)
8. Revise your evaluation and update it accordingly.

Output format:
- Evaluation table with scores for all proposals
- Top 3 selections with rationale
- Any concerns or questions about selected proposals

CRITICAL:
- Base your evaluation on evidence from proposals, not assumptions
- Your top 3 should be ranked: 1st choice, 2nd choice, 3rd choice
```

### Phase 2b: Select Top 3 Proposals

After judges complete voting:

1. **Aggregate votes** using ranked choice:
   - 1st choice = 3 points
   - 2nd choice = 2 points
   - 3rd choice = 1 point
2. **Select top 3** proposals by total points
3. **Handle ties** by comparing average scores across criteria
4. **Document selection** in `selection.md`:
   - Vote tallies
   - Selected proposals
   - Consensus rationale

### Phase 3: Expansion (Develop Full Solutions)

Launch **3 independent agents in parallel** (recommended: Opus for quality):

1. Each agent receives:
   - **One selected proposal** to expand
   - **Original task description** and context
   - **Judge feedback** from pruning phase (concerns, questions)
2. Agent produces **complete solution** implementing the proposal:
   - Full implementation details
   - Addresses concerns raised by judges
   - Documents key decisions made during expansion
3. Solutions saved to `solution.a.md`, `solution.b.md`, `solution.c.md`

**Key principle:** Focused development of validated approaches with awareness of evaluation feedback.

**Prompt template for expansion agents:**

```markdown
You are developing a full solution based on a selected proposal.

<task>
{task_description}
</task>

<selected_proposal>
{write selected proposal EXACTLY as it is. Including all details provided by the agent}
Read this carefully - it is your starting point.
</selected_proposal>

<judge_feedback>
{concerns and questions from judges about this proposal}
Address these in your implementation.
</judge_feedback>

<output>
solution.[*].md where [*] is your unique identifier (a, b, or c)
</output>

Instructions:
1. Read the selected proposal thoroughly
2. Develop a complete solution implementing the proposed approach
   - Address all concerns raised by judges during pruning
4. Generate 3-5 verification questions about critical aspects.
5. Answer own questions:
   - Review solution against each question
   - Identify gaps or weaknesses
6. Revise solution:
   - Fix identified issues
7. Explain what was changed and why

CRITICAL:
- Stay faithful to the selected proposal's core approach
- Do not switch to a different approach midway
- Address judge feedback explicitly
- Produce a complete, implementable solution
```

### Phase 4: Evaluation (Judge Full Solutions)

Launch **3 independent judges in parallel** (recommended: Opus for rigor):

1. Each judge receives **ALL solution files** (solution.a.md, solution.b.md, solution.c.md)
2. Judges evaluate against **final criteria** (task-specific):
   - **Correctness** (weight based on task)
   - **Completeness** (weight based on task)
   - **Quality** (design, maintainability, etc.)
   - **Feasibility** (can this be implemented?)
3. Each judge produces:
   - **Comparative analysis** (which solution excels where)
   - **Evidence-based ratings** (with specific quotes/examples)
   - **Final vote** (which solution they prefer and why)
4. Reports saved to `evaluation.1.md`, `evaluation.2.md`, `evaluation.3.md`

**Key principle:** Multiple independent evaluations with explicit evidence reduce bias and catch different quality aspects.

**Prompt template for evaluation judges:**

```markdown
You are evaluating {number} full solutions to this task:

<task>
{task_description}
</task>

<solutions>
{list of paths to all solution files}
Read all solutions carefully before evaluating.
</solutions>

<output>
Write full report to this file: evaluation.[*].md where [*] is your unique identifier (1, 2, or 3)

CRITICAL: You must reply with this exact structured header format:

---
VOTE: [Solution A/B/C]
SCORES:
  Solution A: [X.X]/5.0
  Solution B: [X.X]/5.0
  Solution C: [X.X]/5.0
CRITERIA:
 - {criterion_1}: [X.X]/5.0
 - {criterion_2}: [X.X]/5.0
 ...
---

[Summary of your evaluation]
</output>

Evaluation criteria (with weights):
1. {criterion_1} ({weight_1}%)
2. {criterion_2} ({weight_2}%)
3. {criterion_3} ({weight_3}%)
...

Read ${CLAUDE_PLUGIN_ROOT}/tasks/judge.md for evaluation methodology and execute using following criteria.

Instructions:
1. For each criterion, analyze ALL solutions
2. Write a combined report:
   - Provide specific evidence (quote exact text) for your assessments
   - Compare strengths and weaknesses
   - Score each solution on each criterion (1-5)
   - Calculate weighted total scores
3. Generate verification 4-6 questions about your evaluation.
4. Answer verification questions:
   - Re-examine solutions for each question
   - Find counter-evidence if it exists
   - Check for systematic bias (length, confidence, etc.)
5. Revise your evaluation and update it accordingly.
6. Reply structured output:
   - VOTE: Which solution you recommend
   - SCORES: Weighted total score for each solution (0.0-5.0)

CRITICAL: Base your evaluation on evidence, not impressions. Quote specific text.

Final checklist:
- [ ] Generated and answered all verification questions
- [ ] Found and corrected all potential issues
- [ ] Checked for known biases (length, verbosity, confidence)
- [ ] Confident in revised evaluation
- [ ] Structured header with VOTE and SCORES at top of report
```

### Phase 4.5: Adaptive Strategy Selection (Early Return)

**The orchestrator** (not a subagent) analyzes judge outputs to determine the optimal strategy.

#### Decision Logic

**Step 1: Parse structured headers from judge reply**

Parse the judges reply.
CRITICAL: Do not read report files themselves, as they can overflow your context.

**Step 2: Check for unanimous winner**

Compare all three VOTE values:
- If Judge 1 VOTE = Judge 2 VOTE = Judge 3 VOTE (same solution):
  - **Strategy: SELECT_AND_POLISH**
  - **Reason:** Clear consensus - all three judges prefer same solution

**Step 3: Check if all solutions are fundamentally flawed**

If no unanimous vote, calculate average scores:
1. Average Solution A scores: (Judge1_A + Judge2_A + Judge3_A) / 3
2. Average Solution B scores: (Judge1_B + Judge2_B + Judge3_B) / 3
3. Average Solution C scores: (Judge1_C + Judge2_C + Judge3_C) / 3

If (avg_A < 3.0) AND (avg_B < 3.0) AND (avg_C < 3.0):
- **Strategy: REDESIGN**
- **Reason:** All solutions below quality threshold, fundamental approach issues

**Step 4: Default to full synthesis**

If none of the above conditions met:
- **Strategy: FULL_SYNTHESIS**
- **Reason:** Split decision with merit, synthesis needed to combine best elements

#### Strategy 1: SELECT_AND_POLISH

**When:** Clear winner (unanimous votes)

**Process:**
1. Select the winning solution as the base
2. Launch subagent to apply specific improvements from judge feedback
3. Cherry-pick 1-2 best elements from runner-up solutions
4. Document what was added and why

**Benefits:**
- Saves synthesis cost (simpler than full synthesis)
- Preserves proven quality of winning solution
- Focused improvements rather than full reconstruction

**Prompt template:**

```markdown
You are polishing the winning solution based on judge feedback.

<task>
{task_description}
</task>

<winning_solution>
{path_to_winning_solution}
Score: {winning_score}/5.0
Judge consensus: {why_it_won}
</winning_solution>

<runner_up_solutions>
{list of paths to all runner-up solutions}
</runner_up_solutions>

<judge_feedback>
{list of paths to all evaluation reports}
</judge_feedback>

<output>
{final_solution_path}
</output>

Instructions:
1. Take the winning solution as your base (do NOT rewrite it)
2. Apply improvements based on judge feedback:
   - Fix identified weaknesses
   - Add missing elements judges noted
3. Cherry-pick 1-2 specific elements from runners-up if judges praised them
4. Document changes made:
   - What was changed and why
   - What was added from other solutions

CRITICAL: Preserve the winning solution's core approach. Make targeted improvements only.
```

#### Strategy 2: REDESIGN

**When:** All solutions scored <3.0/5.0 (fundamental issues across the board)

**Process:**
1. Launch new agent to analyze the failure modes and lessons learned. Ask it to:
   - Analyze common failure modes across all solutions
   - Extract lessons learned (what NOT to do)
   - Identify why all approaches failed
   - Generate new task decomposition or constraints
2. **Return to Phase 3** (Expansion), provide to new implementation agents the lessons learned and new constraints.

**Note:** If redesign fails twice, escalate to user for guidance.

#### Strategy 3: FULL_SYNTHESIS (Default)

**When:** No clear winner AND solutions have merit (scores ≥3.0)

**Process:** Proceed to Phase 5 (Evidence-Based Synthesis)

### Phase 5: Synthesis (Evidence-Based Combination)

**Only executed when Strategy 3 (FULL_SYNTHESIS) selected in Phase 4.5**

Launch **1 synthesis agent** (recommended: Opus for quality):

1. Agent receives:
   - **All solutions** (solution.a.md, solution.b.md, solution.c.md)
   - **All evaluation reports** (evaluation.1.md, evaluation.2.md, evaluation.3.md)
   - **Selection rationale** from pruning phase
2. Agent analyzes:
   - **Consensus strengths** (what multiple judges praised)
   - **Consensus weaknesses** (what multiple judges criticized)
   - **Complementary elements** where solutions took different approaches
3. Agent produces **final solution** by:
   - **Copying superior sections** when one solution clearly wins
   - **Combining approaches** when hybrid is better
   - **Fixing identified issues** that judges caught
   - **Documenting decisions** (what was taken from where and why)

**Key principle:** Evidence-based synthesis leverages collective intelligence from exploration and evaluation.

**Prompt template for synthesizer:**

```markdown
You are synthesizing the best solution from explored, pruned, and evaluated implementations.

<task>
{task_description}
</task>

<solutions>
{list of paths to all solution files}
</solutions>

<evaluation_reports>
{list of paths to all evaluation reports}
</evaluation_reports>

<selection_rationale>
{path to selection.md explaining why these proposals were chosen}
</selection_rationale>

<output>
{output_path} - The final synthesized solution
</output>

Instructions:
1. Read all solutions and evaluation reports carefully
2. Identify consensus strengths (what multiple judges praised)
3. Identify consensus weaknesses (what multiple judges criticized)
4. Note where solutions took complementary approaches
5. Create the best possible solution by:
   - Copying text directly when one solution is clearly superior
   - Combining approaches when a hybrid would be better
   - Fixing all identified issues
   - Preserving the best elements from each
6. Document your synthesis decisions:
   - What you took from each solution (with specific citations)
   - Why you made those choices (reference judge feedback)
   - How you addressed identified weaknesses
   - Any novel combinations or improvements

CRITICAL:
- Do not create something entirely new - synthesize the best from what exists
- Cite your sources (which solution, which section)
- Explain every major decision
- Address all consensus weaknesses identified by judges
```

<output>
The command produces different outputs depending on the adaptive strategy selected:

### Outputs (All Strategies)

1. **Exploration outputs:**
   - `proposals.a.md`, `proposals.b.md`, `proposals.c.md` - High-level approaches with probabilities

2. **Pruning outputs:**
   - `pruning.1.md`, `pruning.2.md`, `pruning.3.md` - Judge evaluations and votes
   - `selection.md` - Vote tallies and selected proposals

3. **Expansion outputs:**
   - `solution.a.md`, `solution.b.md`, `solution.c.md` - Full implementations

4. **Evaluation outputs:**
   - `evaluation.1.md`, `evaluation.2.md`, `evaluation.3.md` - Final judge reports

5. **Resulting solution:** `{output_path}`

### Strategy-Specific Outputs

- **SELECT_AND_POLISH**: Polished solution based on winning solution, with targeted improvements
- **REDESIGN**: Do not stop; return to Phase 3 with lessons learned; eventually finishes at SELECT_AND_POLISH or FULL_SYNTHESIS
- **FULL_SYNTHESIS**: Synthesized solution combining best elements from all solutions
</output>

## Best Practices

### Evaluation Criteria by Task Type

**Code implementation tasks:**
- Correctness (35%)
- Design quality (25%)
- Maintainability (20%)
- Performance (10%)
- Clarity (10%)

**Architecture/design tasks:**
- Completeness (30%)
- Feasibility (25%)
- Scalability (20%)
- Simplicity (15%)
- Clarity (10%)

**Research/analysis tasks:**
- Depth (35%)
- Accuracy (30%)
- Completeness (20%)
- Actionability (15%)

**Documentation tasks:**
- Completeness (35%)
- Accuracy (30%)
- Clarity (20%)
- Usability (15%)

### Common Pitfalls

❌ **Insufficient exploration** - Agents propose similar approaches
❌ **Weak pruning criteria** - Judges can't differentiate quality
❌ **Ignoring judge feedback** - Expansion ignores concerns from pruning
❌ **Vague proposals** - Can't properly evaluate without implementation details
❌ **Over-exploration** - Too many proposals, evaluation becomes expensive
❌ **Forcing synthesis when clear winner exists** - Wastes cost and risks degrading quality
❌ **Synthesizing fundamentally flawed solutions** - Better to redesign than polish garbage

✅ **Encourage diverse exploration** - Prompt for different regions of solution space
✅ **Clear pruning criteria** - Specific, measurable evaluation dimensions
✅ **Feed feedback forward** - Expansion agents address pruning concerns
✅ **Right level of detail** - Proposals have enough detail to evaluate
✅ **Prune aggressively** - Only expand most promising 3 approaches
✅ **Trust adaptive strategy selection** - Polish clear winners, synthesize split decisions, redesign failures

## Example: API Design

```bash
/tree-of-thoughts "Design REST API for user management (CRUD + auth)" \
  --output "specs/api/users.md" \
  --criteria "RESTfulness,security,scalability,developer-experience"
```

**Phase 1 outputs (proposals):**
- `proposals.a.md` - 3 approaches: Resource-based (0.35), Action-based (0.25), HATEOAS (0.15)
- `proposals.b.md` - 3 approaches: GraphQL-first (0.20), REST+GraphQL hybrid (0.30), Pure REST (0.40)
- `proposals.c.md` - 3 approaches: Microservices (0.25), Monolithic (0.45), Hybrid (0.20)

**Phase 2 outputs (pruning):**
- `pruning.1.md` - Top 3: Resource-based REST, Pure REST, Monolithic
- `pruning.2.md` - Top 3: Pure REST, Hybrid (services), Resource-based REST
- `pruning.3.md` - Top 3: Resource-based REST, REST+GraphQL hybrid, Pure REST
- `selection.md` - Selected: Resource-based REST (8 pts), Pure REST (7 pts), Monolithic (4 pts)

**Phase 3 outputs (expansion):**
- `solution.a.md` - Full resource-based design with nested routes
- `solution.b.md` - Flat REST design with simple endpoints
- `solution.c.md` - Monolithic API with service-oriented internals

**Phase 4 outputs (evaluation):**
- `evaluation.1.md`:
  ```
  VOTE: Solution A
  SCORES: A=4.2/5.0, B=3.8/5.0, C=3.4/5.0
  ```
  "Prefers A for RESTfulness, criticizes C complexity"

- `evaluation.2.md`:
  ```
  VOTE: Solution B
  SCORES: A=3.9/5.0, B=4.1/5.0, C=3.5/5.0
  ```
  "Prefers B for simplicity, criticizes A deep nesting"

- `evaluation.3.md`:
  ```
  VOTE: Solution A
  SCORES: A=4.3/5.0, B=3.6/5.0, C=3.2/5.0
  ```
  "Prefers A for discoverability, criticizes B lack of structure"

**Phase 4.5 decision (orchestrator parses headers):**
- Split votes: A, B, A (no unanimous winner)
- Average scores: A=4.1, B=3.8, C=3.4 (all ≥3.0)
- Strategy: FULL_SYNTHESIS
- Reason: Split decision with merit, synthesis needed

**Phase 5 output (synthesis):**
- `specs/api/users.md` - Resource-based structure (from A), max 2-level nesting (from B), internal services (from C)

