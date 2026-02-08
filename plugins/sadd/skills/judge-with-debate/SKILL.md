---
description: Evaluate solutions through multi-round debate between independent judges until consensus
argument-hint: Solution path(s) and evaluation criteria
---

# judge-with-debate

<task>
Evaluate solutions through multi-agent debate where independent judges analyze, challenge each other's assessments, and iteratively refine their evaluations until reaching consensus or maximum rounds.
</task>

<context>
This command implements the Multi-Agent Debate pattern for high-quality evaluation where multiple perspectives and rigorous argumentation improve assessment accuracy. Unlike single-pass evaluation, debate forces judges to defend their positions with evidence and consider counter-arguments.
</context>

## Pattern: Debate-Based Evaluation

This command implements iterative multi-judge debate:

```
Phase 0: Setup
         mkdir -p .specs/reports
                  │
Phase 1: Independent Analysis
         ┌─ Judge 1 → {name}.1.md ─┐
Solution ┼─ Judge 2 → {name}.2.md ─┼─┐
         └─ Judge 3 → {name}.3.md ─┘ │
                                     │
Phase 2: Debate Round (iterative)   │
    Each judge reads others' reports │
         ↓                           │
    Argue + Defend + Challenge       │
         ↓                           │
    Revise if convinced ─────────────┤
         ↓                           │
    Check consensus                  │
         ├─ Yes → Final Report       │
         └─ No → Next Round ─────────┘
```

## Process

### Setup: Create Reports Directory

Before starting evaluation, ensure the reports directory exists:

```bash
mkdir -p .specs/reports
```

**Report naming convention:** `.specs/reports/{solution-name}-{YYYY-MM-DD}.[1|2|3].md`

Where:
- `{solution-name}` - Derived from solution filename (e.g., `users-api` from `src/api/users.ts`)
- `{YYYY-MM-DD}` - Current date
- `[1|2|3]` - Judge number

### Phase 1: Independent Analysis

Launch **3 independent judge agents in parallel** (recommended: Opus for rigor):

1. Each judge receives:
   - Path to solution(s) being evaluated
   - Evaluation criteria with weights
   - Clear rubric for scoring
2. Each produces **independent assessment** saved to `.specs/reports/{solution-name}-{date}.[1|2|3].md`
3. Reports must include:
   - Per-criterion scores with evidence
   - Specific quotes/examples supporting ratings
   - Overall weighted score
   - Key strengths and weaknesses

**Key principle:** Independence in initial analysis prevents groupthink.

**Prompt template for initial judges:**

```markdown
You are Judge {N} evaluating a solution independently.

<solution_path>
{path to solution file(s)}
</solution_path>

<task_description>
{what the solution was supposed to accomplish}
</task_description>

<evaluation_criteria>
{criteria with descriptions and weights}
</evaluation_criteria>

<output_file>
.specs/reports/{solution-name}-{date}.{N}.md
</output_file>

Read ${CLAUDE_PLUGIN_ROOT}/tasks/judge.md for evaluation methodology and execute using following criteria.

Instructions:
1. Read the solution thoroughly
2. For each criterion:
   - Find specific evidence (quote exact text)
   - Score on the defined scale
   - Justify with concrete examples
3. Calculate weighted overall score
4. Write comprehensive report to {output_file}
5. Generate verification 5 questions about your evaluation.
6. Answer verification questions:
   - Re-examine solutions for each question
   - Find counter-evidence if it exists
   - Check for systematic bias (length, confidence, etc.)
7. Revise your report file and update it accordingly.

Add to report begining `Done by Judge {N}`
```

### Phase 2: Debate Rounds (Iterative)

For each debate round (max 3 rounds):

Launch **3 debate agents in parallel**:

1. Each judge agent receives:
   - Path to their own previous report (`.specs/reports/{solution-name}-{date}.[1|2|3].md`)
   - Paths to other judges' reports (`.specs/reports/{solution-name}-{date}.[1|2|3].md`)
   - The original solution
2. Each judge:
   - Identifies disagreements with other judges (>1 point score gap on any criterion)
   - Defends their own ratings with evidence
   - Challenges other judges' ratings they disagree with
   - Considers counter-arguments
   - Revises their assessment if convinced
3. Updates their report file with new section: `## Debate Round {R}`
4. After they reply, if they reached agreement move to Phase 3: Consensus Report

**Key principle:** Judges communicate only through filesystem - orchestrator doesn't mediate and don't read reports files itself, it can overflow your context.

**Prompt template for debate judges:**

```markdown
You are Judge {N} in debate round {R}.

<your_previous_report>
{path to .specs/reports/{solution-name}-{date}.{N}.md}
</your_previous_report>

<other_judges_reports>
Judge 1: .specs/reports/{solution-name}-{date}.1.md
...
</other_judges_reports>

<task_description>
{what the solution was supposed to accomplish}
</task_description>

<solution_path>
{path to solution}
</solution_path>

<output_file>
.specs/reports/{solution-name}-{date}.{N}.md (append to existing file)
</output_file>

Read ${CLAUDE_PLUGIN_ROOT}/tasks/judge.md for evaluation methodology principles.

Instructions:
1. Read your previous assessment from {your_previous_report}
2. Read all other judges' reports
3. Identify disagreements (where your scores differ by >1 point)
4. For each major disagreement:
   - State the disagreement clearly
   - Defend your position with evidence
   - Challenge the other judge's position with counter-evidence
   - Consider whether their evidence changes your view
5. Update your report file by APPENDING:
6. Reply whether you are reached agreement, and with which judge. Include revisited scores and criteria scores.

---

## Debate Round {R}

### Disagreements Identified

**Disagreement with Judge {X} on Criterion "{Name}"**
- My score: {my_score}/5
- Their score: {their_score}/5
- My defense: [quote evidence supporting my score]
- My challenge: [what did they miss or misinterpret?]

[Repeat for each disagreement]

### Revised Assessment

After considering other judges' arguments:
- **Criterion "{Name}"**: [Maintained {X}/5 | Revised from {X} to {Y}/5]
  - Reason for change: [what convinced me] OR
  - Reason maintained: [why I stand by original score]

[Repeat for changed/maintained scores]

**New Weighted Score**: {updated_total}/5.0

## Evidences
[specific quotes]

--- 

CRITICAL:
- Only revise if you find their evidence compelling
- Defend your original scores if you still believe them
- Quote specific evidence from the solution
```

### Consensus Check

After each debate round, check for consensus:

**Consensus achieved if:**
- All judges' overall scores within 0.5 points of each other
- No criterion has >1 point disagreement across any two judges
- All judges explicitly state they accept the consensus

**If no consensus after 3 rounds:**
- Report persistent disagreements
- Provide all judge reports for human review
- Flag that automated evaluation couldn't reach consensus

**Orchestration Instructions:**

**Step 1: Run Independent Analysis (Round 1)**

1. Launch 3 judge agents in parallel (Judge 1, 2, 3)
2. Each writes their independent assessment to `.specs/reports/{solution-name}-{date}.[1|2|3].md`
3. Wait for all 3 agents to complete

**Step 2: Check for Consensus**

Let's work through this systematically to ensure accurate consensus detection.

Read all three reports and extract:
- Each judge's overall weighted score
- Each judge's score for every criterion

Check consensus step by step:
1. First, extract all overall scores from each report and list them explicitly
2. Calculate the difference between the highest and lowest overall scores
   - If difference ≤ 0.5 points → overall consensus achieved
   - If difference > 0.5 points → no consensus yet
3. Next, for each criterion, list all three judges' scores side by side
4. For each criterion, calculate the difference between highest and lowest scores
   - If any criterion has difference > 1.0 point → no consensus on that criterion
5. Finally, verify consensus is achieved only if BOTH conditions are met:
   - Overall scores within 0.5 points
   - All criterion scores within 1.0 point

**Step 3: Decision Point**

- **If consensus achieved**: Go to Step 5 (Generate Consensus Report)
- **If no consensus AND round < 3**: Go to Step 4 (Run Debate Round)
- **If no consensus AND round = 3**: Go to Step 6 (Report No Consensus)

**Step 4: Run Debate Round**

1. Increment round counter (round = round + 1)
2. Launch 3 judge agents in parallel
3. Each agent reads:
   - Their own previous report from filesystem
   - Other judges' reports from filesystem
   - Original solution
4. Each agent appends "Debate Round {R}" section to their own report file
5. Wait for all 3 agents to complete
6. Go back to Step 2 (Check for Consensus)

**Step 5: Reply with Report**

Let's synthesize the evaluation results step by step.

1. Read all final reports carefully
2. Before generating the report, analyze the following:
   - What is the consensus status (achieved or not)?
   - What were the key points of agreement across all judges?
   - What were the main areas of disagreement, if any?
   - How did the debate rounds change the evaluations?
3. Reply to user with a report that contains:
   - If there is consensus:
     - Consensus scores (average of all judges)
     - Consensus strengths/weaknesses
     - Number of rounds to reach consensus
     - Final recommendation with clear justification
   - If there is no consensus:
       - All judges' final scores showing disagreements
       - Specific criteria where consensus wasn't reached
       - Analysis of why consensus couldn't be reached
       - Flag for human review
4. Command complete

### Phase 3: Consensus Report

If consensus achieved, synthesize the final report by working through each section methodically:

```markdown
# Consensus Evaluation Report

Let's compile the final consensus by analyzing each component systematically.

## Consensus Scores

First, let's consolidate all judges' final scores:

| Criterion | Judge 1 | Judge 2 | Judge 3 | Final |
|-----------|---------|---------|---------|-------|
| {Name}    | {X}/5   | {X}/5   | {X}/5   | {X}/5 |
...

**Consensus Overall Score**: {avg}/5.0

## Consensus Strengths
[Review each judge's identified strengths and extract the common themes that all judges agreed upon]

## Consensus Weaknesses
[Review each judge's identified weaknesses and extract the common themes that all judges agreed upon]

## Debate Summary
Let's trace how consensus was reached:
- Rounds to consensus: {N}
- Initial disagreements: {list with specific criteria and score gaps}
- How resolved: {for each disagreement, explain what evidence or argument led to resolution}

## Final Recommendation
Based on the consensus scores and the key strengths/weaknesses identified:
{Pass/Fail/Needs Revision with clear justification tied to the evidence}
```

<output>
The command produces:

1. **Reports directory**: `.specs/reports/` (created if not exists)
2. **Initial reports**: `.specs/reports/{solution-name}-{date}.1.md`, `.specs/reports/{solution-name}-{date}.2.md`, `.specs/reports/{solution-name}-{date}.3.md`
3. **Debate updates**: Appended sections in each report file per round
4. **Final synthesis**: Replied to user (consensus or disagreement summary)
</output>

## Best Practices

### Evaluation Criteria

Choose 3-5 weighted criteria relevant to the solution type:

**Code evaluation:**
- Correctness (30%) - Does it work? Handles edge cases?
- Design Quality (25%) - Clean architecture? Maintainable?
- Efficiency (20%) - Performance considerations?
- Code Quality (15%) - Readable? Well-documented?
- Testing (10%) - Test coverage? Test quality?

**Design/Architecture evaluation:**
- Completeness (30%) - All requirements addressed?
- Feasibility (25%) - Can it actually be built?
- Scalability (20%) - Handles growth?
- Simplicity (15%) - Appropriately simple?
- Documentation (10%) - Clear and comprehensive?

**Documentation evaluation:**
- Accuracy (35%) - Technically correct?
- Completeness (30%) - Covers all necessary topics?
- Clarity (20%) - Easy to understand?
- Usability (15%) - Helpful examples? Good structure?

### Common Pitfalls

❌ **Judges create new reports instead of appending** - Loses debate history
❌ **Orchestrator passes reports between judges** - Violates filesystem communication principle
❌ **Weak initial assessments** - Garbage in, garbage out
❌ **Too many debate rounds** - Diminishing returns after 3 rounds
❌ **Sycophancy in debate** - Judges agree too easily without real evidence

✅ **Judges append to their own report file**
✅ **Judges read other reports from filesystem directly**
✅ **Strong evidence-based initial assessments**
✅ **Maximum 3 debate rounds**
✅ **Require evidence for changing positions**

## Example Usage

### Evaluating an API Implementation

```bash
/judge-with-debate \
  --solution "src/api/users.ts" \
  --task "Implement REST API for user management" \
  --criteria "correctness:30,design:25,security:20,performance:15,docs:10"
```

**Round 1 outputs** (assuming date 2025-01-15):
- `.specs/reports/users-api-2025-01-15.1.md` - Judge 1 scores correctness 4/5, security 3/5
- `.specs/reports/users-api-2025-01-15.2.md` - Judge 2 scores correctness 4/5, security 5/5
- `.specs/reports/users-api-2025-01-15.3.md` - Judge 3 scores correctness 5/5, security 4/5

**Disagreement detected:** Security scores range from 3-5

**Round 2 debate:**
- Judge 1 defends 3/5: "Missing rate limiting, input validation incomplete"
- Judge 2 challenges: "Rate limiting exists in middleware (line 45)"
- Judge 1 revises to 4/5: "Missed middleware, but input validation still weak"
- Judge 3 defends 4/5: "Input validation adequate for requirements"

**Round 2 outputs:**
- All judges now 4-5/5 on security (within 1 point)
- Disagreement on input validation remains

**Round 3 debate:**
- Judges examine specific validation code
- Judge 2 revises to 4/5: "Upon re-examination, email validation regex is weak"
- Consensus: Security = 4/5

**Final consensus:**
```
Correctness: 4.3/5
Design: 4.5/5
Security: 4.0/5 (3 rounds to consensus)
Performance: 4.7/5
Documentation: 4.0/5

Overall: 4.3/5 - PASS
```

