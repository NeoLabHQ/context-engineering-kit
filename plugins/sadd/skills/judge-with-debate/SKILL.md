---
name: judge-with-debate
description: Evaluate solutions through multi-round debate between independent judges until consensus
argument-hint: Solution path(s) and evaluation criteria
---

# judge-with-debate

<task>
Evaluate solutions through multi-agent debate where independent judges analyze, challenge each other's assessments, and iteratively refine their evaluations until reaching consensus or maximum rounds.
</task>

<context>
This command implements the Multi-Agent Debate pattern for high-quality evaluation where multiple perspectives and rigorous argumentation improve assessment accuracy. Unlike single-pass evaluation, debate forces judges to defend their positions with evidence and consider counter-arguments.

Key benefits:

- **Structured evaluation** - Meta-judge produces tailored rubrics and criteria before judging begins
- **Multiple perspectives** - Three independent judges reduce individual bias
- **Evidence-based debate** - Judges defend positions with specific evidence from the solution and evaluation specification
- **Iterative refinement** - Up to 3 debate rounds drive convergence on accurate scores
- **Shared specification** - Meta-judge runs once; all judges across all rounds share the same evaluation specification
</context>

## Pattern: Debate-Based Evaluation

This command implements iterative multi-judge debate:

```
Phase 0: Setup
         mkdir -p .specs/reports
                  |
Phase 0.5: Dispatch Meta-Judge
         Meta-Judge (Opus)
              |
         Evaluation Specification YAML
              |
Phase 1: Independent Analysis (3 judges in parallel)
         +- Judge 1 -> {name}.1.md -+
Solution +- Judge 2 -> {name}.2.md -+-+
         +- Judge 3 -> {name}.3.md -+ |
                                      |
Phase 2: Debate Round (iterative)     |
    Each judge reads others' reports  |
         |                            |
    Argue + Defend + Challenge        |
    (grounded in eval specification)  |
         |                            |
    Revise if convinced --------------+
         |                            |
    Check consensus                   |
         +- Yes -> Final Report       |
         +- No -> Next Round ---------+
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

### Phase 0.5: Dispatch Meta-Judge

Before independent analysis, dispatch a meta-judge agent to generate a tailored evaluation specification. The meta-judge runs ONCE and produces rubrics, checklists, and scoring criteria that ALL judges will use across ALL rounds.

**Meta-judge prompt template:**

```markdown
## Task

Generate an evaluation specification yaml for the following evaluation task. You will produce rubrics, checklists, and scoring criteria that multiple judge agents will use to evaluate the solution through independent analysis and multi-round debate.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## User Prompt
{task description - what the solution was supposed to accomplish}

## Context
{Any relevant context about the solution being evaluated}

## Artifact Type
{code | documentation | configuration | etc.}

## Evaluation Mode
Multi-judge debate with consensus-seeking across rounds

## Instructions
Return only the final evaluation specification YAML in your response.
The specification should support both independent analysis and debate-based refinement.
```

**Dispatch:**

```
Use Task tool:
  - description: "Meta-judge: generate evaluation specification for {solution-name}"
  - prompt: {meta-judge prompt}
  - model: opus
  - subagent_type: "sadd:meta-judge"
```

Wait for the meta-judge to complete and extract the evaluation specification YAML from its output before proceeding to Phase 1.

### Phase 1: Independent Analysis

Launch **3 independent judge agents in parallel** (Opus for rigor):

1. Each judge receives:
   - Path to solution(s) being evaluated
   - The meta-judge's evaluation specification YAML
   - Task description
2. Each produces **independent assessment** saved to `.specs/reports/{solution-name}-{date}.[1|2|3].md`
3. Reports must include:
   - Per-criterion scores with evidence
   - Specific quotes/examples supporting ratings
   - Overall weighted score
   - Key strengths and weaknesses

**Key principle:** Independence in initial analysis prevents groupthink.

**Prompt template for initial judges:**

```markdown
You are Judge {N} evaluating a solution independently against an evaluation specification produced by the meta judge.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## Solution
{path to solution file(s)}

## Task Description
{what the solution was supposed to accomplish}

## Evaluation Specification

```yaml
{meta-judge's evaluation specification YAML}
```

## Output File
.specs/reports/{solution-name}-{date}.{N}.md

## Instructions

Follow your full judge process as defined in your agent instructions!

Additional instructions:
1. Read the solution thoroughly
2. For each criterion from the evaluation specification:
   - Find specific evidence (quote exact text)
   - Score on the defined scale
   - Justify with concrete examples
3. Calculate weighted overall score
4. Write comprehensive report to {output_file}

Add to report beginning `Done by Judge {N}`
```

**Dispatch each judge:**

```
Use Task tool:
  - description: "Judge {N}: independent analysis of {solution-name}"
  - prompt: {judge prompt with evaluation specification YAML}
  - model: opus
  - subagent_type: "sadd:judge"
```

### Phase 2: Debate Rounds (Iterative)

For each debate round (max 3 rounds):

Launch **3 debate agents in parallel**:

1. Each judge agent receives:
   - Path to their own previous report (`.specs/reports/{solution-name}-{date}.[1|2|3].md`)
   - Paths to other judges' reports (`.specs/reports/{solution-name}-{date}.[1|2|3].md`)
   - The original solution
   - The meta-judge's evaluation specification YAML
2. Each judge:
   - Identifies disagreements with other judges (>1 point score gap on any criterion)
   - Defends their own ratings with evidence from the solution and evaluation specification
   - Challenges other judges' ratings they disagree with
   - Considers counter-arguments
   - Revises their assessment if convinced
3. Updates their report file with new section: `## Debate Round {R}`
4. After they reply, if they reached agreement move to Phase 3: Consensus Report

**Key principle:** Judges communicate only through filesystem - orchestrator doesn't mediate and don't read reports files itself, it can overflow your context.

**Prompt template for debate judges:**

```markdown
You are Judge {N} in debate round {R}.

CLAUDE_PLUGIN_ROOT=`${CLAUDE_PLUGIN_ROOT}`

## Your Previous Report
{path to .specs/reports/{solution-name}-{date}.{N}.md}

## Other Judges' Reports
Judge 1: .specs/reports/{solution-name}-{date}.1.md
...

## Task Description
{what the solution was supposed to accomplish}

## Solution
{path to solution}

## Evaluation Specification

```yaml
{meta-judge's evaluation specification YAML}
```

## Output File
.specs/reports/{solution-name}-{date}.{N}.md (append to existing file)

## Instructions

Follow your full judge process as defined in your agent instructions!

Additional debate instructions:
1. Read your previous assessment from {your_previous_report}
2. Read all other judges' reports
3. Identify disagreements (where your scores differ by >1 point)
4. For each major disagreement:
   - State the disagreement clearly
   - Defend your position with evidence from the solution and evaluation specification
   - Challenge the other judge's position with counter-evidence
   - Consider whether their evidence changes your view
5. Update your report file by APPENDING debate round section
6. Reply whether you reached agreement, and with which judge. Include revisited scores and criteria scores.

CRITICAL:
- Ground your arguments in the evaluation specification criteria
- Only revise if you find their evidence compelling
- Defend your original scores if you still believe them
- Quote specific evidence from the solution
```

**Dispatch each debate judge:**

```
Use Task tool:
  - description: "Judge {N}: debate round {R} for {solution-name}"
  - prompt: {debate judge prompt with evaluation specification YAML}
  - model: opus
  - subagent_type: "sadd:judge"
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

**Step 1: Dispatch Meta-Judge (Phase 0.5)**

1. Launch meta-judge agent
2. Wait for meta-judge to complete
3. Extract the evaluation specification YAML from meta-judge output

**Step 2: Run Independent Analysis (Phase 1)**

1. Launch 3 judge agents in parallel (Judge 1, 2, 3) with the evaluation specification YAML
2. Each writes their independent assessment to `.specs/reports/{solution-name}-{date}.[1|2|3].md`
3. Wait for all 3 agents to complete

**Step 3: Check for Consensus**

Let's work through this systematically to ensure accurate consensus detection.

Read all three reports and extract:
- Each judge's overall weighted score
- Each judge's score for every criterion

Check consensus step by step:
1. First, extract all overall scores from each report and list them explicitly
2. Calculate the difference between the highest and lowest overall scores
   - If difference <= 0.5 points -> overall consensus achieved
   - If difference > 0.5 points -> no consensus yet
3. Next, for each criterion, list all three judges' scores side by side
4. For each criterion, calculate the difference between highest and lowest scores
   - If any criterion has difference > 1.0 point -> no consensus on that criterion
5. Finally, verify consensus is achieved only if BOTH conditions are met:
   - Overall scores within 0.5 points
   - All criterion scores within 1.0 point

**Step 4: Decision Point**

- **If consensus achieved**: Go to Step 6 (Generate Consensus Report)
- **If no consensus AND round < 3**: Go to Step 5 (Run Debate Round)
- **If no consensus AND round = 3**: Go to Step 7 (Report No Consensus)

**Step 5: Run Debate Round**

1. Increment round counter (round = round + 1)
2. Launch 3 judge agents in parallel with the same evaluation specification YAML
3. Each agent reads:
   - Their own previous report from filesystem
   - Other judges' reports from filesystem
   - Original solution
4. Each agent appends "Debate Round {R}" section to their own report file
5. Wait for all 3 agents to complete
6. Go back to Step 3 (Check for Consensus)

**Step 6: Reply with Report**

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

**Step 7: Report No Consensus**

- Report persistent disagreements
- Provide all judge reports for human review
- Flag that automated evaluation couldn't reach consensus

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

### Meta-Judge + Judge Verification

- **Never skip meta-judge** - Tailored evaluation criteria produce better judgments and more grounded debates
- **Meta-judge runs once** - Same specification for all 3 judges across all debate rounds
- **Include CLAUDE_PLUGIN_ROOT** - Both meta-judge and judges need the resolved plugin root path
- **Meta-judge YAML** - Pass only the YAML to judges, do not modify it
- **Debate grounding** - Judges should reference evaluation specification criteria when defending positions

### Common Pitfalls

- **Judges create new reports instead of appending** - Loses debate history
- **Orchestrator passes reports between judges** - Violates filesystem communication principle
- **Weak initial assessments** - Garbage in, garbage out
- **Too many debate rounds** - Diminishing returns after 3 rounds
- **Sycophancy in debate** - Judges agree too easily without real evidence
- **Modifying meta-judge YAML** - Specification must be passed verbatim to all judges
- **Re-running meta-judge between rounds** - Specification is generated once and shared

### Do This

- **Judges append to their own report file**
- **Judges read other reports from filesystem directly**
- **Strong evidence-based initial assessments**
- **Maximum 3 debate rounds**
- **Require evidence for changing positions**
- **Ground debate arguments in the evaluation specification criteria**
- **Use same evaluation specification across all rounds**

## Example Usage

### Evaluating an API Implementation

```bash
/judge-with-debate Implement REST API for user management --solution "src/api/users.ts" 
```

**Phase 0.5 - Meta-Judge** (assuming date 2025-01-15):
- Meta-judge generates evaluation specification YAML with criteria:
  - Correctness (30%), Design (25%), Security (20%), Performance (15%), Documentation (10%)
  - Rubrics, checklists, and scoring definitions for each criterion

**Phase 1 - Independent Analysis** (3 judges receive specification):
- `.specs/reports/users-api-2025-01-15.1.md` - Judge 1 scores correctness 4/5, security 3/5
- `.specs/reports/users-api-2025-01-15.2.md` - Judge 2 scores correctness 4/5, security 5/5
- `.specs/reports/users-api-2025-01-15.3.md` - Judge 3 scores correctness 5/5, security 4/5

**Disagreement detected:** Security scores range from 3-5

**Phase 2 - Debate Round 1** (judges reference evaluation specification):
- Judge 1 defends 3/5: "Missing rate limiting, input validation incomplete per specification checklist item 4"
- Judge 2 challenges: "Rate limiting exists in middleware (line 45), satisfies specification rubric"
- Judge 1 revises to 4/5: "Missed middleware, but input validation still weak per specification"
- Judge 3 defends 4/5: "Input validation adequate for requirements as defined in specification"

**Debate Round 1 outputs:**
- All judges now 4-5/5 on security (within 1 point)
- Disagreement on input validation remains

**Debate Round 2** (same evaluation specification):
- Judges examine specific validation code against specification criteria
- Judge 2 revises to 4/5: "Upon re-examination, email validation regex is weak per specification checklist"
- Consensus: Security = 4/5

**Final consensus:**
```
Correctness: 4.3/5
Design: 4.5/5
Security: 4.0/5 (2 debate rounds to consensus)
Performance: 4.7/5
Documentation: 4.0/5

Overall: 4.3/5 - PASS
```

</output>
