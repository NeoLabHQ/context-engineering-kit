---
description: Execute tasks through competitive multi-agent generation, multi-judge evaluation, and evidence-based synthesis
argument-hint: Task description and optional output path/criteria
---

# do-competitively

<task>
Execute tasks through competitive multi-agent generation, multi-judge evaluation, and evidence-based synthesis to produce superior results by combining the best elements from parallel implementations.
</task>

<context>
This command implements the Generate-Critique-Synthesize (GCS) pattern with adaptive strategy selection for high-stakes tasks where quality matters more than speed. It combines competitive generation with multi-perspective evaluation and intelligently selects the optimal synthesis strategy based on results.

**Key features:**

- Self-critique loops in generation (Constitutional AI)
- Verification loops in evaluation (Chain-of-Verification)
- Adaptive strategy: polish clear winners, synthesize split decisions, redesign failures
- Average 15-20% cost savings through intelligent strategy selection
</context>

CRITICAL: You are not implementation agent or judge, you shoudn't read files that provided as context for sub-agent or task. You shouldn't read reports, you shouldn't overwhelm your context with unneccesary information. You MUST follow process step by step. Any diviations will be considered as failure and you will be killed!

## Pattern: Generate-Critique-Synthesize (GCS)

This command implements a four-phase adaptive competitive orchestration pattern:

```
Phase 1: Competitive Generation with Self-Critique
         ┌─ Agent 1 → Draft → Critique → Revise → Solution A ─┐
Task ───┼─ Agent 2 → Draft → Critique → Revise → Solution B ─┼─┐
         └─ Agent 3 → Draft → Critique → Revise → Solution C ─┘ │
                                                                  │
Phase 2: Multi-Judge Evaluation with Verification                │
         ┌─ Judge 1 → Evaluate → Verify → Revise → Report A ─┐  │
         ├─ Judge 2 → Evaluate → Verify → Revise → Report B ─┼──┤
         └─ Judge 3 → Evaluate → Verify → Revise → Report C ─┘  │
                                                                  │
Phase 2.5: Adaptive Strategy Selection                           │
         Analyze Consensus ──────────────────────────────────────┤
                ├─ Clear Winner? → SELECT_AND_POLISH             │
                ├─ All Flawed (<3.0)? → REDESIGN (return Phase 1)│
                └─ Split Decision? → FULL_SYNTHESIS              │
                                          │                       │
Phase 3: Evidence-Based Synthesis        │                       │
         (Only if FULL_SYNTHESIS)         │                       │
         Synthesizer ─────────────────────┴───────────────────────┴─→ Final Solution
```

## Process

### Setup: Create Reports Directory

Before starting, ensure the reports directory exists:

```bash
mkdir -p .specs/reports
```

**Report naming convention:** `.specs/reports/{solution-name}-{YYYY-MM-DD}.[1|2|3].md`

Where:

- `{solution-name}` - Derived from output path (e.g., `users-api` from output `specs/api/users.md`)
- `{YYYY-MM-DD}` - Current date
- `[1|2|3]` - Judge number

**Note:** Solutions remain in their specified output locations; only evaluation reports go to `.specs/reports/`

### Phase 1: Competitive Generation

Launch **3 independent agents in parallel** (recommended: Opus for quality):

1. Each agent receives **identical task description and context**
2. Agents work **independently without seeing each other's work**
3. Each produces a **complete solution** to the same problem
4. Solutions are saved to distinct files (e.g., `{solution-file}.[a|b|c].[ext]`)

**Solution naming convention:** `{solution-file}.[a|b|c].[ext]`
Where:

- `{solution-file}` - Derived from task (e.g., `create users.ts` result in `users` as solution file)
- `[a|b|c]` - Unique identifier per sub-agent
- `[ext]` - File extension (e.g., `md`, `ts` and etc.)

**Key principle:** Diversity through independence - agents explore different approaches.

CRITICAL: You MUST provide filename with [a|b|c] identifier to agents and judges!!! Missing it, will result in your TERMINATION imidiatly!

**Prompt template for generators:**

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
{define expected output following such pattern: {solution-file}.[a|b|c].[ext] based on the task description and context. Each [a|b|c] is a unique identifier per sub-agent. You MUST provide filename with it!!!}
</output>

Instructions:
Let's approach this systematically to produce the best possible solution.

1. First, analyze the task carefully - what is being asked and what are the key requirements?
2. Consider multiple approaches - what are the different ways to solve this?
3. Think through the tradeoffs step by step and choose the approach you believe is best
4. Implement it completely
5. Generate 5 verification questions about critical aspects
6. Answer your own questions:
   - Review solution against each question
   - Identify gaps or weaknesses
7. Revise solution:
   - Fix identified issues
8. Explain what was changed and why
```

### Phase 2: Multi-Judge Evaluation

Launch **3 independent judges in parallel** (recommended: Opus for rigor):

1. Each judge receives path to **ALL candidate solutions** (A, B, C)
2. Judges evaluate against **clear criteria** (correctness, design quality, maintainability, etc.)
3. Each judge produces:
   - **Comparative analysis** (which solution excels where)
   - **Evidence-based ratings** (with specific quotes/examples)
   - **Final vote** (which solution they prefer and why)
4. Reports saved to distinct files (e.g., `.specs/reports/{solution-name}-{date}.[1|2|3].md`)

**Key principle:** Multiple independent evaluations reduce bias and catch different issues.

**Prompt template for judges:**

```markdown
You are evaluating {number} solutions to this task:

<task>
{task_description}
</task>

<solutions>
{list of paths to all candidate solutions}
</solutions>

<output>
Write full report to: {.specs/reports/{solution-name}-{date}.[1|2|3].md - each judge gets unique number identifier}

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
...

Read ${CLAUDE_PLUGIN_ROOT}/tasks/judge.md for evaluation methodology and execute using following criteria.

Instructions:
1. For each criterion, analyze ALL solutions
2. Write a combined report:
   1. Provide specific evidence (quote exact text) for your assessments
   2. Compare strengths and weaknesses
   3. Score each solution on each criterion
   4. Calculate weighted total scores
3. Generate verification 5 questions about your evaluation.
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

### Phase 2.5: Adaptive Strategy Selection (Early Return)

**The orchestrator** (not a subagent) analyzes judge outputs to determine the optimal strategy.

#### Decision Logic

**Step 1: Parse structured headers from judge reply**

Parse the judges reply.
CRITICAL: Do not read reports files itself, it can overflow your context.

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

**Step 5: Default to full synthesis**

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
Let's work through this step by step to polish the winning solution effectively.

1. Take the winning solution as your base (do NOT rewrite it)
2. First, carefully review all judge feedback to understand what needs improvement
3. Apply improvements based on judge feedback:
   - Fix identified weaknesses
   - Add missing elements judges noted
4. Next, examine the runner-up solutions for standout elements
5. Cherry-pick 1-2 specific elements from runners-up if judges praised them
6. Document changes made:
   - What was changed and why
   - What was added from other solutions

CRITICAL: Preserve the winning solution's core approach. Make targeted improvements only.
```

#### Strategy 2: REDESIGN

**When:** All solutions scored <3.0/5.0 (fundamental issues across the board)

**Process:**

1. Launch new agent to analyze the failure modes and lessons learned. Ask the agent to:
   - Think through step by step: what went wrong with each solution?
   - Analyze common failure modes across all solutions
   - Extract lessons learned (what NOT to do)
   - Identify the root causes of why all approaches failed
   - Generate new task decomposition or constraints based on these insights
2. **Return to Phase 1**, provide to new implementation agents the lessons learned and new constraints.

**Prompt template for new implementation:**

```markdown
You are analyzing why all solutions failed to meet quality standards. And implement new solution based on it.

<task>
{task_description}
</task>

<constraints>
{constraints_if_any}
</constraints>

<context>
{relevant_context}
</context>

<failed_solutions>
{list of paths to all candidate solutions}
</failed_solutions>

<evaluation_reports>
{list of paths to all evaluation reports with low scores}
</evaluation_reports>

Instructions:
Let's break this down systematically to understand what went wrong and how to design new solution based on it.

1. First, analyze the task carefully - what is being asked and what are the key requirements?
2. Read through each solution and its evaluation report
3. For each solution, think step by step about:
   - What was the core approach?
   - What specific issues did judges identify?
   - Why did this approach fail to meet the quality threshold?
4. Identify common failure patterns across all solutions:
   - Are there shared misconceptions?
   - Are there missing requirements that all solutions overlooked?
   - Are there fundamental constraints that weren't considered?
5. Extract lessons learned:
   - What approaches should be avoided?
   - What constraints must be addressed?
6. Generate improved guidance for the next iteration:
   - New constraints to add
   - Specific approaches to try - what are the different ways to solve this?
   - Key requirements to emphasize
7. Think through the tradeoffs step by step and choose the approach you believe is best
8. Implement it completely
9. Generate 5 verification questions about critical aspects
10. Answer your own questions:
   - Review solution against each question
   - Identify gaps or weaknesses
11. Revise solution:
   - Fix identified issues
12. Explain what was changed and why

```

#### Strategy 3: FULL_SYNTHESIS (Default)

**When:** No clear winner AND solutions have merit (scores ≥3.0)

**Process:** Proceed to Phase 3 (Evidence-Based Synthesis)

### Phase 3: Evidence-Based Synthesis

**Only executed when Strategy 3 (FULL_SYNTHESIS) selected in Phase 2.5**

Launch **1 synthesis agent** (recommended: Opus for quality):

1. Agent receives:
   - **All candidate solutions** (A, B, C)
   - **All evaluation reports** (1, 2, 3)
2. Agent analyzes:
   - Which elements each judge praised (consensus on strengths)
   - Which issues each judge identified (consensus on weaknesses)
   - Where solutions differed in approach
3. Agent produces **final solution** by:
   - **Copying superior sections** when one solution clearly wins
   - **Combining approaches** when hybrid is better
   - **Fixing identified issues** that all judges caught
   - **Documenting decisions** (what was taken from where and why)

**Key principle:** Evidence-based synthesis leverages collective intelligence.

**Prompt template for synthesizer:**

```markdown
You are synthesizing the best solution from competitive implementations and evaluations.

<task>
{task_description}
</task>

<solutions>
{list of paths to all candidate solutions}
</solutions>

<evaluation_reports>
{list of paths to all evaluation reports}
</evaluation_reports>

<output>
{define expected output following such pattern: solution.md based on the task description and context. Result should be a complete solution to the task.}
</output>

Instructions:
Let's think through this synthesis step by step to create the best possible combined solution.

1. First, read all solutions and evaluation reports carefully
2. Map out the consensus:
   - What strengths did multiple judges praise in each solution?
   - What weaknesses did multiple judges criticize in each solution?
3. For each major component or section, think through:
   - Which solution handles this best and why?
   - Could a hybrid approach work better?
4. Create the best possible solution by:
   - Copying text directly when one solution is clearly superior
   - Combining approaches when a hybrid would be better
   - Fixing all identified issues
   - Preserving the best elements from each
5. Explain your synthesis decisions:
   - What you took from each solution
   - Why you made those choices
   - How you addressed identified weaknesses

CRITICAL: Do not create something entirely new. Synthesize the best from what exists.
```

<output>
The command produces different outputs depending on the adaptive strategy selected:

### Outputs (All Strategies)

1. **Candidate solutions:** `{solution-file}.[a|b|c].[ext]` (in specified output location)
2. **Evaluation reports:** `.specs/reports/{solution-name}-{date}.[1|2|3].md`
3. **Resulting solution:** `{output_path}`

### Strategy-Specific Outputs

- SELECT_AND_POLISH: Polished solution based on winning solution
- REDESIGN: Do not stop, return to phase 1 and eventiualy should result in finish at SELECT_AND_POLISH or FULL_SYNTHESIS strategies
- FULL_SYNTHESIS: Synthesized solution combined best from all

### Orcestrator Reply

Once command execution is complete, reply to user with following structure:

```markdown
## Execution Summary

Original Task: {task_description}

Strategy Used: {strategy} ({reason})

### Results

| Phase                   | Agents | Models   | Status      |
|-------------------------|--------|----------|-------------|
| Phase [N]: [phase name] | [N]    | [model] × 3 | [✅ Complete / ❌ Failed] |

Files Created

Final Solution:
- {output_path} - Synthesized production-ready command

Candidate Solutions:
- {solution-file}.[a|b|c].[ext] (Score: [X.X]/5.0)

Evaluation Reports:
- .specs/reports/{solution-file}-{date}.[1|2|3].md (Vote: [Solution A/B/C])

Synthesis Decisions

| Element              | Source           | Rationale   |
|----------------------|------------------|-------------|
| [element]            | Solution [B/A/C] | [rationale] |

```

</output>

## Best Practices

### Evaluation Criteria

Choose 3-5 weighted criteria relevant to the task:

**Code tasks:**

- Correctness (30%)
- Design quality (25%)
- Maintainability (20%)
- Performance (15%)
- Clarity (10%)

**Design tasks:**

- Completeness (30%)
- Feasibility (25%)
- Scalability (20%)
- Simplicity (15%)
- Clarity (10%)

**Documentation tasks:**

- Completeness (35%)
- Accuracy (30%)
- Clarity (20%)
- Usability (15%)

### Common Pitfalls

❌ **Using for trivial tasks** - Overhead not justified
❌ **Vague task descriptions** - Leads to incomparable solutions
❌ **Insufficient context** - Agents can't produce quality work
❌ **Weak evaluation criteria** - Judges can't differentiate quality
❌ **Forcing synthesis when clear winner exists** - Wastes cost and risks degrading quality
❌ **Synthesizing fundamentally flawed solutions** - Better to redesign than polish garbage

✅ **Well-defined task with clear constraints**
✅ **Rich context for informed decisions**
✅ **Specific, measurable evaluation criteria**
✅ **Trust adaptive strategy selection**
✅ **Polish clear winners, synthesize split decisions, redesign failures**

## Examples

### Example 1: API Design (Clear Winner - SELECT_AND_POLISH)

```bash
/do-competitively "Design REST API for user management (CRUD + auth)" \
  --output "specs/api/users.md" \
  --criteria "RESTfulness,security,scalability,developer-experience"
```

**Phase 1 outputs:**

- `specs/api/users.a.md` - Resource-based design with nested routes
- `specs/api/users.b.md` - Action-based design with RPC-style endpoints
- `specs/api/users.c.md` - Minimal design, missing auth consideration

**Phase 2 outputs** (assuming date 2025-01-15):

- `.specs/reports/users-api-2025-01-15.1.md`:

  ```
  VOTE: Solution A
  SCORES: A=4.5/5.0, B=3.2/5.0, C=2.8/5.0
  ```

  "Most RESTful, good security"

- `.specs/reports/users-api-2025-01-15.2.md`:

  ```
  VOTE: Solution A
  SCORES: A=4.3/5.0, B=3.5/5.0, C=2.6/5.0
  ```

  "Clean resource design, scalable"

- `.specs/reports/users-api-2025-01-15.3.md`:

  ```
  VOTE: Solution A
  SCORES: A=4.6/5.0, B=3.0/5.0, C=2.9/5.0
  ```

  "Best practices, clear structure"

**Phase 2.5 decision (orchestrator parses headers):**

- Unanimous vote: A, A, A
- Average scores: A=4.5, B=3.2, C=2.8
- Strategy: SELECT_AND_POLISH
- Reason: Unanimous winner with >1.0 point gap

**Phase 3 output:**

- `specs/api/users.md` - Solution A polished with:
  - Added rate limiting documentation (from B)
  - Simplified nested routes (judge feedback)
  - Total cost: 6 agents (saved 1 from full synthesis)

### Example 2: Algorithm Selection (Split Decision - FULL_SYNTHESIS)

```bash
/do-competitively "Design caching strategy for high-traffic API" \
  --output "specs/caching.md" \
  --criteria "performance,memory-efficiency,simplicity,reliability"
```

**Phase 1 outputs:**

- `specs/caching.a.md` - Redis with LRU eviction
- `specs/caching.b.md` - Multi-tier cache (memory + Redis)
- `specs/caching.c.md` - CDN + application cache

**Phase 2 outputs** (assuming date 2025-01-15):

- `.specs/reports/caching-2025-01-15.1.md`:

  ```
  VOTE: Solution B
  SCORES: A=3.8/5.0, B=4.2/5.0, C=3.9/5.0
  ```

  "Best performance, complex"

- `.specs/reports/caching-2025-01-15.2.md`:

  ```
  VOTE: Solution A
  SCORES: A=4.0/5.0, B=3.9/5.0, C=3.7/5.0
  ```

  "Simple, reliable, proven"

- `.specs/reports/caching-2025-01-15.3.md`:

  ```
  VOTE: Solution C
  SCORES: A=3.6/5.0, B=4.0/5.0, C=4.1/5.0
  ```

  "Global reach, cost-effective"

**Phase 2.5 decision (orchestrator parses headers):**

- Split votes: B, A, C (no consensus)
- Average scores: A=3.8, B=4.0, C=3.9
- Score gap: 4.0 - 3.9 = 0.1 (<1.0 threshold)
- Strategy: FULL_SYNTHESIS
- Reason: Split decision, all solutions ≥3.0, no clear winner

**Phase 3 output:**

- `specs/caching.md` - Hybrid approach:
  - Multi-tier architecture (from B)
  - Simple LRU policy (from A)
  - CDN for static content (from C)
  - Total cost: 7 agents (full synthesis needed)

### Example 3: Authentication Design (All Flawed - REDESIGN)

```bash
/do-competitively "Design authentication system with social login" \
  --output "specs/auth.md" \
  --criteria "security,user-experience,maintainability"
```

**Phase 1 outputs:**

- `specs/auth.a.md` - Custom OAuth2 implementation
- `specs/auth.b.md` - Session-based with social providers
- `specs/auth.c.md` - JWT with password-only auth

**Phase 2 outputs** (assuming date 2025-01-15):

- `.specs/reports/auth-2025-01-15.1.md`:

  ```
  VOTE: Solution A
  SCORES: A=2.5/5.0, B=2.2/5.0, C=2.3/5.0
  ```

  "Security risks, reinventing wheel"

- `.specs/reports/auth-2025-01-15.2.md`:

  ```
  VOTE: Solution B
  SCORES: A=2.4/5.0, B=2.8/5.0, C=2.1/5.0
  ```

  "Sessions don't scale, missing requirements"

- `.specs/reports/auth-2025-01-15.3.md`:

  ```
  VOTE: Solution C
  SCORES: A=2.6/5.0, B=2.5/5.0, C=2.3/5.0
  ```

  "No social login, security concerns"

**Phase 2.5 decision (orchestrator parses headers):**

- Split votes: A, B, C (no consensus)
- Average scores: A=2.5, B=2.5, C=2.2 (ALL <3.0)
- Strategy: REDESIGN
- Reason: All solutions below 3.0 threshold, fundamental issues

- Do not stop, return to phase 1 and eventiualy should result in finish at SELECT_AND_POLISH or FULL_SYNTHESIS strategies
