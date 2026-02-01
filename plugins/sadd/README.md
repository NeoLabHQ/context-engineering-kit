# SADD Plugin (Subagent-Driven Development)

Execution framework that dispatches fresh subagents for each task with quality gates between iterations, enabling fast parallel development while maintaining code quality.

Focused on:

- **Fresh context per task** - Each subagent starts clean without context pollution from previous tasks
- **Quality gates** - Code review between tasks catches issues early before they compound
- **Parallel execution** - Independent tasks run concurrently for faster completion
- **Sequential execution** - Dependent tasks execute in order with review checkpoints

## Plugin Target

- Prevent context pollution - Fresh subagents avoid accumulated confusion from long sessions
- Catch issues early - Code review between tasks prevents bugs from compounding
- Faster iteration - Parallel execution of independent tasks saves time
- Maintain quality at scale - Quality gates ensure standards are met on every task

## Overview

The SADD plugin provides skills and commands for executing work through coordinated subagents. Instead of executing all tasks in a single long session where context accumulates and quality degrades, SADD dispatches fresh subagents with quality gates.

**Core capabilities:**

- **Sequential/Parallel Execution** - Execute implementation plans task-by-task with code review gates
- **Competitive Execution** - Generate multiple solutions, evaluate with judges, synthesize best elements
- **Work Evaluation** - Assess completed work using LLM-as-Judge with structured rubrics

This approach solves the "context pollution" problem - when an agent accumulates confusion, outdated assumptions, or implementation drift over long sessions. Each fresh subagent starts clean, implements its specific scope, and reports back for quality validation.

The plugin supports multiple execution strategies based on task characteristics, all with built-in quality gates.

## Quick Start

```bash
# Install the plugin
/plugin install sadd@NeoLabHQ/context-engineering-kit

# Use competitive execution for high-stakes tasks
/do-competitively "Design and implement authentication middleware with JWT support"

```

[Usage Examples](./usage-examples.md)

## Commands Overview

### launch-sub-agent

This command launches a focused sub-agent to execute the provided task. Analyze the task to intelligently select the optimal model and agent configuration, then dispatch a sub-agent with Zero-shot Chain-of-Thought reasoning at the beginning and mandatory self-critique verification at the end. It implements the **Supervisor/Orchestrator pattern** from multi-agent architectures where you (the orchestrator) dispatch focused sub-agents with isolated context. The primary benefit is **context isolation** - each sub-agent operates in a clean context window focused on its specific task without accumulated context pollution.

#### Usage

```bash
`/launch-sub-agent Design a caching strategy for our API that handles 10k requests/second`
```

Agent output:

```markdown
**Analysis:**
- Task type: Architecture / design
- Complexity: High (performance requirements, system design)
- Output size: Medium (design document)
- Domain match: software-architect

**Selection:** Opus + software-architect agent

**Dispatch:** Task tool with Opus model, software-architect prompt, CoT prefix, critique suffix
```

#### Advanced Options

**Explicit Model Override**

When you know the appropriate model tier, override automatic selection:

```bash
/launch-sub-agent "Task description" --model opus|sonnet|haiku
```

**Explicit Agent Selection**

Force use of a specific specialized agent:

```bash
/launch-sub-agent "Task description" --agent developer|researcher|software-architect|tech-writer|business-analyst|code-explorer|tech-lead|security-auditor
```

**Output Location**

Specify where results should be written:

```bash
/launch-sub-agent "Task description" --output path/to/output.md
```

**Combined Options**

```bash
/launch-sub-agent "Implement the payment flow" --agent developer --model opus --output src/services/payment.ts
```

#### Core design principles

- **Context isolation**: Sub-agents operate with fresh context, preventing confirmation bias and attention scarcity
- **Intelligent model selection**: Match model capability to task complexity for optimal quality/cost tradeoff
- **Specialized agent routing**: Domain experts handle domain-specific tasks
- **Zero-shot CoT**: Systematic reasoning at task start improves quality by 20-60%
- **Self-critique**: Verification loop catches 40-60% of issues before delivery

#### When to use this command

- Tasks that benefit from fresh, focused context
- Tasks where model selection matters (quality vs. cost tradeoffs)
- Delegating work while maintaining quality gates
- Single, well-defined tasks with clear deliverables

#### When NOT to use

- Simple tasks you can complete directly (overhead not justified)
- Tasks requiring conversation history or accumulated session context
- Exploratory work where scope is undefined

#### Theoretical Foundation

**Zero-shot Chain-of-Thought** (Kojima et al., 2022)

- Adding "Let's think step by step" improves reasoning by 20-60%
- Explicit reasoning steps reduce errors and catch edge cases
- Reference: [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916)

**Constitutional AI / Self-Critique** (Bai et al., 2022)

- Self-critique loops catch 40-60% of issues before delivery
- Verification questions force explicit quality checking
- Reference: [Constitutional AI](https://arxiv.org/abs/2212.08073)

**Multi-Agent Context Isolation** (Multi-agent architecture patterns)

- Fresh context prevents accumulated confusion and attention scarcity
- Focused tasks produce better results than context-polluted sessions
- Supervisor pattern enables quality gates between delegated work

### /do-and-judge

Execute a single task with implementation sub-agent, independent judge verification, and automatic retry loop until passing or max retries exceeded.

- Purpose - Execute a single task with quality verification and feedback-driven iteration
- Pattern - Implement → Judge → Iterate (if needed) → Report
- Output - Verified implementation with judge scores and improvement suggestions
- Quality - Two-layer verification: self-critique (internal) + LLM-as-a-judge (external)
- Iteration - Retry with judge feedback until passing (≥4/5.0) or max retries (2)

#### Pattern: Single-Task Execution with Judge Verification

```
Phase 1: Task Analysis and Model Selection
         Complexity + Risk + Scope → Model Selection
                     │
Phase 2: Dispatch Implementation Agent
         [CoT Prefix] + [Task Body] + [Self-Critique Suffix]
                     │
Phase 3: Dispatch Judge Agent
         Independent verification with structured criteria
                     │
Phase 4: Parse Verdict and Iterate
         ├─ PASS (≥4) → Report Success
         └─ FAIL (<4) → Retry with Feedback (max 2)
                            └─ Return to Phase 3
                     │
Phase 5: Final Report or Escalation
         Success summary OR escalate to user after max retries
```

#### Usage

```bash
# Basic usage
/do-and-judge "Refactor the UserService class to use dependency injection"

# Complex implementation
/do-and-judge "Implement rate limiting middleware with configurable limits per endpoint"

# Architecture change
/do-and-judge "Extract validation logic from UserController into separate UserValidator class"
```

#### When to Use

**Good use cases:**

- Single, well-defined tasks that benefit from quality verification
- Changes that should meet a quality threshold before shipping
- Tasks where feedback-driven iteration improves results
- Any implementation where you want an independent quality gate

**Do NOT use when:**

- Multi-step tasks with dependencies → use `/do-in-steps` instead
- Independent parallel tasks → use `/do-in-parallel` instead
- High-stakes tasks needing multiple approaches → use `/do-competitively` instead
- Simple tasks where verification overhead isn't justified → use `/launch-sub-agent` instead

#### Quality Enhancement Techniques

| Phase | Technique | Benefit |
|-------|-----------|---------|
| **Phase 2** | Zero-shot CoT | Systematic reasoning improves quality by 20-60% |
| **Phase 2** | Self-Critique | Implementation agents verify own work before submission |
| **Phase 3** | LLM-as-a-Judge | Independent judge catches blind spots self-critique misses |
| **Phase 4** | Feedback Loop | Retry with specific issues until passing or max retries |

#### Theoretical Foundation

- **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Step-by-step reasoning improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique loops before submission
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Independent evaluation with structured rubrics

### /do-in-parallel

Execute tasks in parallel across multiple targets with intelligent model selection, independence validation, and quality-focused prompting.

- Purpose - Execute the same task across multiple independent targets in parallel
- Pattern - Supervisor/Orchestrator with parallel dispatch and context isolation
- Output - Multiple solutions, one per target, with aggregated summary
- Quality - Enhanced with Zero-shot CoT, Constitutional AI self-critique, and intelligent model selection
- Efficiency - Dramatic time savings through concurrent execution of independent work

#### Pattern: Parallel Orchestration with Independence Validation

This command implements a six-phase parallel orchestration pattern:

```
Phase 1: Parse Input and Identify Targets
                     │
Phase 2: Task Analysis with Zero-shot CoT
         ┌─ Task Type Identification ─────────────────┐
         │ (transformation, analysis, documentation)  │
         ├─ Per-Target Complexity Assessment ─────────┤
         │ (high/medium/low)                          │
         ├─ Independence Validation ──────────────────┤
         │ ⚠️ CRITICAL: Must pass before proceeding   │
         └────────────────────────────────────────────┘
                     │
Phase 3: Model and Agent Selection
         Is task COMPLEX? → Opus
         Is task SIMPLE/MECHANICAL? → Haiku
         Otherwise → Opus (default for balanced work)
                     │
Phase 4: Construct Per-Target Prompts
         [CoT Prefix] + [Task Body] + [Self-Critique Suffix]
         (Same structure for ALL agents, customized per target)
                     │
Phase 5: Parallel Dispatch (ALL agents in SINGLE response)
         ┌─ Agent 1 (target A) ─┐
         ├─ Agent 2 (target B) ─┼─→ Concurrent Execution
         └─ Agent 3 (target C) ─┘
                     │
Phase 6: Collect and Summarize Results
         Aggregate outcomes, report failures, suggest remediation
```

#### Usage

```bash
# Inferred targets from task description
/do-in-parallel "Apply consistent logging format to src/handlers/user.ts, src/handlers/order.ts, and src/handlers/product.ts"
```

#### Advanced Options

```bash
# Basic usage with file targets
/do-in-parallel "Simplify error handling to use early returns" \
  --files "src/services/user.ts,src/services/order.ts,src/services/payment.ts"

# With named targets
/do-in-parallel "Generate unit tests achieving 80% coverage" \
  --targets "UserService,OrderService,PaymentService"

# With model override
/do-in-parallel "Security audit for injection vulnerabilities" \
  --files "src/db/queries.ts,src/api/search.ts" \
  --model opus
```

#### When to Use

**Good use cases:**

- Same operation across multiple files (refactoring, formatting)
- Independent transformations (each file stands alone)
- Batch documentation generation (API docs per module)
- Parallel analysis tasks (security audit per component)
- Multi-file code generation (tests per service)

**Do NOT use when:**

- Only one target → use `/launch-sub-agent` instead
- Targets have dependencies → use `/do-in-steps` instead
- Tasks require sequential ordering → use `/do-in-steps` instead
- Shared state needed between executions → use `/do-in-steps` instead
- Quality-critical tasks needing comparison → use `/do-competitively` instead

#### Context Isolation Best Practices

- **Minimal context**: Each sub-agent receives only what it needs for its target
- **No cross-references**: Don't tell Agent A about Agent B's target
- **Let them discover**: Sub-agents read files to understand local patterns
- **File system as truth**: Changes are coordinated through the filesystem

#### Theoretical Foundation

**Zero-shot Chain-of-Thought** (Kojima et al., 2022)

- "Let's think step by step" improves reasoning by 20-60%
- Applied to each parallel agent independently
- Reference: [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916)

**Constitutional AI / Self-Critique** (Bai et al., 2022)

- Each agent self-verifies before completing
- Catches issues without coordinator overhead
- Reference: [Constitutional AI](https://arxiv.org/abs/2212.08073)

**Multi-Agent Context Isolation** (Multi-agent architecture patterns)

- Fresh context prevents accumulated confusion
- Focused tasks produce better results than context-polluted sessions
- Reference: [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) (Du et al., 2023)

### /do-in-steps

Execute complex tasks through sequential sub-agent orchestration with intelligent model selection and LLM-as-a-judge verification.

- Purpose - Execute dependent tasks sequentially where each step builds on previous outputs
- Pattern - Supervisor/Orchestrator with sequential dispatch, judge verification, and iteration loop
- Output - Comprehensive report with all step results, judge scores, and integration summary
- Quality - Two-layer verification: self-critique (internal) + LLM-as-a-judge (external) with iteration until passing
- Key Benefit - Prevents context pollution while ensuring quality through independent verification

#### Pattern: Sequential Orchestration with Judge Verification

```
Phase 1: Task Analysis and Decomposition
         Task → Identify Dependencies → Define Step Boundaries
                     │
Phase 2: Model Selection
         For each step: Assess Complexity + Scope + Risk → Select Model
                     │
Phase 3: Sequential Execution with Judge Verification
         ┌─────────────────────────────────────────────────────────────┐
         │ For each Step N:                                           │
         │   Implementer → Self-Critique → Judge → Parse Verdict      │
         │        ▲                                    │               │
         │        │                                    ▼               │
         │        │                         PASS (≥3.5)? → Next Step  │
         │        │                         FAIL? → Retry (max 2)     │
         │        └──────── feedback ───────┘         or Escalate     │
         └─────────────────────────────────────────────────────────────┘
         Step 1 → Judge ✓ → Step 2 → Judge ✓ → Step 3 → Judge ✓ → ...
                     │
Phase 4: Final Summary and Report
         Aggregate results, judge scores, files modified, decisions made
```

#### Usage

```bash
# Interface change with consumer updates
/do-in-steps "Change return type of UserService.getUser() from User to UserDTO and update all consumers"

# Feature addition across layers
/do-in-steps "Add email notification capability to the order processing system"

# Multi-file refactoring with breaking changes
/do-in-steps "Rename 'userId' to 'accountId' across the codebase - affects interfaces, implementations, and callers"
```

#### When to Use

**Good use cases:**

- Changes that cascade through multiple files/layers
- Interface modifications with consumers to update
- Feature additions spanning multiple components
- Refactoring with dependency chains
- Any task where "Step N depends on Step N-1"

**Do NOT use when:**

- Independent tasks that could run in parallel → use `/do-in-parallel`
- Single-step tasks → use `/launch-sub-agent`
- Tasks needing exploration before commitment → use `/tree-of-thoughts`
- High-stakes tasks needing multiple approaches → use `/do-competitively`

#### Quality Enhancement Techniques

| Phase | Technique | Benefit |
|-------|-----------|---------|
| **Phase 3** | Self-Critique | Implementation agents verify own work before submission, catching 40-60% of issues |
| **Phase 3** | LLM-as-a-Judge | Independent judge verifies each step, catching blind spots self-critique misses |
| **Phase 3** | Iteration Loop | Failed steps retry with judge feedback until passing (max 2 retries) or escalate |
| **Phase 3** | Context Passing | Each step receives summary of previous outputs without full context pollution |

#### Theoretical Foundation

- **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Step-by-step reasoning improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique loops before submission
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Independent evaluation with structured rubrics
- **[Multi-Agent Debate](https://arxiv.org/abs/2305.14325)** (Du et al., 2023) - Fresh context prevents accumulated confusion

### /do-competitively - Competitive Multi-Agent Synthesis

Execute tasks through competitive generation, multi-judge evaluation, and evidence-based synthesis to produce superior results.

- Purpose - Generate multiple solutions competitively, evaluate with independent judges, synthesize best elements
- Pattern - Generate-Critique-Synthesize (GCS) with self-critique, verification loops, and adaptive strategy selection
- Output - Superior solution combining best elements from all candidates
- Quality - Enhanced with Constitutional AI self-critique, Chain of Verification, and intelligent strategy selection
- Efficiency - 15-20% average cost savings through adaptive strategy (polish clear winners, redesign failures)

#### Pattern: Generate-Critique-Synthesize (GCS)

This command implements a four-phase adaptive competitive orchestration pattern with quality enhancement loops:

```
Phase 1: Competitive Generation with Self-Critique
         ┌─ Agent 1 → Draft → Self-Critique → Revise → Solution A ─┐
Task ───┼─ Agent 2 → Draft → Self-Critique → Revise → Solution B ─┼─┐
         └─ Agent 3 → Draft → Self-Critique → Revise → Solution C ─┘ │
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

#### Usage

```bash
# Basic usage
/do-competitively <task-description>

# With explicit output specification
/do-competitively "Create authentication middleware" --output "src/middleware/auth.ts"

# With specific evaluation criteria
/do-competitively "Design user schema" --criteria "scalability,security,developer-experience"
```

#### When to Use

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

#### Quality Enhancement Techniques

Techniques that were used to enhance the quality of the competitive execution pattern.

| Phase         | Technique                       | Benefit                                                                                                              |
| --------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Phase 1**   | Constitutional AI Self-Critique | Generators review and fix their own solutions before submission, catching 40-60% of issues                           |
| **Phase 2**   | Chain of Verification           | Judges verify their evaluations with structured questions, improving calibration and reducing bias                   |
| **Phase 2.5** | Adaptive Strategy Selection     | Orchestrator parses structured judge outputs (VOTE+SCORES) to select optimal strategy, saving 15-20% cost on average |
| **Phase 3**   | Evidence-Based Synthesis        | Combines proven best elements rather than creating new solutions (only when needed)                                  |

#### Theoretical Foundation

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

### /tree-of-thoughts - Tree of Thoughts with Adaptive Strategy

Execute complex reasoning tasks through systematic exploration of solution space, pruning unpromising branches, expanding viable approaches, and synthesizing the best solution.

- Purpose - Explore multiple solution paths before committing to full implementation
- Pattern - Tree of Thoughts (ToT) with adaptive strategy selection
- Output - Superior solution combining systematic exploration with evidence-based synthesis
- Quality - Enhanced with probability estimates, multi-stage evaluation, and adaptive strategy
- Efficiency - 15-20% average cost savings through adaptive strategy (polish clear winners, redesign failures)

#### Pattern: Tree of Thoughts (ToT)

This command implements a six-phase systematic reasoning pattern with adaptive strategy selection:

```
Phase 1: Exploration (Propose Approaches)
         ┌─ Agent A → Proposals with probabilities ─┐
Task ───┼─ Agent B → Proposals with probabilities ─┼─┐
         └─ Agent C → Proposals with probabilities ─┘ │
                                                       │
Phase 2: Pruning (Vote for Best 3)                    │
         ┌─ Judge 1 → Votes + Rationale ─┐            │
         ├─ Judge 2 → Votes + Rationale ─┼────────────┤
         └─ Judge 3 → Votes + Rationale ─┘            │
                 │                                     │
                 ├─→ Select Top 3 Proposals            │
                 │                                     │
Phase 3: Expansion (Develop Full Solutions)           │
         ┌─ Agent A → Solution A ─┐                   │
         ├─ Agent B → Solution B ─┼───────────────────┤
         └─ Agent C → Solution C ─┘                   │
                                                       │
Phase 4: Evaluation (Judge Full Solutions)            │
         ┌─ Judge 1 → Report 1 ─┐                     │
         ├─ Judge 2 → Report 2 ─┼─────────────────────┤
         └─ Judge 3 → Report 3 ─┘                     │
                                                       │
Phase 4.5: Adaptive Strategy Selection                │
         Analyze Consensus ───────────────────────────┤
                ├─ Clear Winner? → SELECT_AND_POLISH  │
                ├─ All Flawed (<3.0)? → REDESIGN      │
                └─ Split Decision? → FULL_SYNTHESIS   │
                                         │             │
Phase 5: Synthesis (Only if FULL_SYNTHESIS)           │
         Synthesizer ────────────────────┴─────────────┴─→ Final Solution
```

#### Usage

```bash
# Basic usage
/tree-of-thoughts <task-description>

# With explicit output specification
/tree-of-thoughts "Design authentication middleware" --output "specs/auth.md"

# With specific evaluation criteria
/tree-of-thoughts "Design caching strategy" --criteria "performance,memory-efficiency,simplicity"
```

#### When to Use

✅ **Use ToT when:**

- Solution space is large and poorly understood
- Wrong approach chosen early would waste significant effort
- Task has multiple valid approaches with different trade-offs
- Quality is more important than speed
- You need to explore before committing

❌ **Don't use ToT when:**

- Solution approach is obvious
- Task is simple or well-defined
- Speed matters more than exploration
- Only one reasonable approach exists

#### Quality Enhancement Techniques

| Phase         | Technique                   | Benefit                                                                         |
| --------------- | ----------------------------- | --------------------------------------------------------------------------------- |
| **Phase 1**   | Probabilistic Sampling      | Explorers generate approaches with probability estimates, encouraging diversity |
| **Phase 2**   | Multi-Judge Pruning         | Independent judges vote on top 3 proposals, reducing groupthink                 |
| **Phase 3**   | Feedback-Aware Expansion    | Expanders address concerns raised during pruning                                |
| **Phase 4**   | Chain of Verification       | Judges verify evaluations with structured questions, reducing bias              |
| **Phase 4.5** | Adaptive Strategy Selection | Orchestrator parses structured outputs to select optimal strategy               |
| **Phase 5**   | Evidence-Based Synthesis    | Combines proven best elements rather than creating new solutions                |

#### Theoretical Foundation

Based on:

- **[Tree of Thoughts](https://arxiv.org/abs/2305.10601)** (Yao et al., 2023) - Systematic exploration and pruning
- **[Self-Consistency](https://arxiv.org/abs/2203.11171)** (Wang et al., 2023) - Multiple reasoning paths
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Critique and refinement
- **[LLM-as-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Multi-perspective evaluation
- **[Chain-of-Verification](https://arxiv.org/abs/2309.11495)** (Dhuliawala et al., 2023) - Structured verification reduces bias

### /judge-with-debate - Multi-Agent Debate Evaluation

Evaluate solutions through iterative multi-judge debate where independent judges analyze, challenge each other's assessments, and refine evaluations until reaching consensus or maximum rounds.

- Purpose - Rigorous evaluation through adversarial critique and evidence-based argumentation
- Pattern - Independent Analysis → Iterative Debate → Consensus or Disagreement Report
- Output - Consensus evaluation report with averaged scores and debate summary, or disagreement report flagging unresolved issues
- Quality - Enhanced through multi-perspective analysis, evidence-based argumentation, and iterative refinement
- Efficiency - Early termination when consensus reached or judges stop converging

#### Pattern: Debate-Based Evaluation

This command implements iterative multi-judge debate with filesystem-based communication:

```
Phase 1: Independent Analysis
         ┌─ Judge 1 → report.1.md ─┐
Solution ┼─ Judge 2 → report.2.md ─┼─┐
         └─ Judge 3 → report.3.md ─┘ │
                                     │
Phase 2: Debate Round (iterative)   │
    Each judge reads others' reports │
         ↓                           │
    Argue + Defend + Challenge       │
         ↓                           │
    Revise if convinced ─────────────┤
         ↓                           │
    Check consensus (≤0.5 overall,   │
                     ≤1.0 per-criterion)
         ├─ Yes → Consensus Report   │
         └─ No → Next Round ─────────┘
                (max 3 rounds)
```

#### Usage

```bash
# Basic usage
/judge-with-debate --solution "src/api/users.ts" --task "REST API implementation"

# With specific criteria
/judge-with-debate \
  --solution "src/api/users.ts" \
  --task "Implement REST API for user management" \
  --criteria "correctness:30,design:25,security:20,performance:15,docs:10" \
  --output "evaluation/"

# Evaluating design documents
/judge-with-debate \
  --solution "specs/architecture.md" \
  --task "System architecture design" \
  --criteria "completeness:30,feasibility:25,scalability:20,clarity:15,maintainability:10"
```

#### When to Use

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

#### Quality Enhancement Techniques

| Phase         | Technique                | Benefit                                                                                            |
| --------------- | -------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Phase 1**   | Chain of Verification    | Judges generate verification questions and self-critique before submitting initial assessment      |
| **Phase 1**   | Evidence Requirement     | All scores must be supported by specific quotes from solution                                      |
| **Phase 2**   | Filesystem Communication | Judges read each other's reports directly, orchestrator never mediates (prevents context overflow) |
| **Phase 2**   | Structured Argumentation | Judges must defend positions AND challenge others with counter-evidence                            |
| **Phase 2**   | Explicit Revision        | Judges must document what changed their mind or why they maintained their position                 |
| **Consensus** | Adaptive Termination     | Stops early if consensus reached, max rounds hit, or judges stop converging                        |

#### Process Flow

**Step 1: Independent Analysis**

- 3 judges analyze solution in parallel
- Each writes comprehensive report to `report.[1|2|3].md`
- Includes per-criterion scores, evidence, overall assessment

**Step 2: Check Consensus**

- Extract all scores from reports
- Consensus if: overall scores within 0.5 AND all criterion scores within 1.0
- If achieved → generate consensus report and complete

**Step 3: Debate Round** (if no consensus, max 3 rounds)

- Each judge reads their own report + others' reports from filesystem
- Identifies disagreements (>1 point gap on any criterion)
- Defends their ratings with evidence
- Challenges others' ratings with counter-evidence
- Revises scores if convinced by others' arguments
- Appends "Debate Round N" section to their own report

**Step 4: Repeat** until consensus, max rounds, or lack of convergence

**Step 5: Final Report**

- If consensus: averaged scores, strengths/weaknesses, debate summary
- If no consensus: disagreement report with flag for human review

#### Theoretical Foundation

Based on:

- **[Multi-Agent Debate](https://arxiv.org/abs/2305.14325)** (Du et al., 2023) - Adversarial critique improves reasoning accuracy
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Pairwise comparison and structured evaluation
- **[Chain-of-Verification](https://arxiv.org/abs/2309.11495)** (Dhuliawala et al., 2023) - Self-verification reduces bias
- **Deliberative Democracy** - Argumentation and evidence-based consensus building

**Key Insight**: Debate forces judges to explicitly defend positions with evidence and consider counter-arguments, reducing individual bias and improving calibration.

### /judge - Single-Agent Work Evaluation

Evaluate completed work using LLM-as-Judge with structured rubrics, context isolation, and evidence-based scoring.

- Purpose - Assess quality of work produced earlier in conversation with isolated context
- Pattern - Context Extraction → Judge Sub-Agent → Validation → Report
- Output - Evaluation report with weighted scores, evidence citations, and actionable improvements
- Quality - Enhanced with Chain-of-Thought scoring, self-verification, and bias mitigation
- Efficiency - Single focused judge for fast evaluation without multi-agent overhead

#### Pattern: LLM-as-Judge with Context Isolation

This command implements a three-phase evaluation pattern:

```
Phase 1: Context Extraction
         Review conversation history
         Identify work to evaluate
         Extract: Original task, output, files, constraints
                     │
Phase 2: Judge Sub-Agent (Fresh Context)
         ┌─────────────────────────────────────────┐
         │ Judge receives ONLY extracted context   │
         │ (prevents confirmation bias)            │
         │                                         │
         │ For each criterion:                     │
         │   1. Review evidence                    │
         │   2. Write justification                │
         │   3. Assign score (1-5)                 │
         │   4. Self-verify with questions         │
         │   5. Adjust if needed                   │
         └─────────────────────────────────────────┘
                     │
Phase 3: Validation & Report
         Verify scores in valid range (1-5)
         Check justification has evidence
         Confirm weighted total calculation
         Present verdict with recommendations
```

#### Usage

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

#### When to Use

✅ **Use single judge when:**

- Quick quality check needed
- Work is straightforward with clear criteria
- Speed/cost matters more than multi-perspective analysis
- Evaluation is formative (guiding improvements), not summative
- Low-to-medium stakes decisions

❌ **Use judge-with-debate instead when:**

- High-stakes decisions requiring rigorous evaluation
- Subjective criteria where perspectives differ legitimately
- Complex solutions with many evaluation dimensions
- You need defensible, consensus-based evaluation

#### Default Evaluation Criteria

| Criterion             | Weight | What It Measures                                                  |
| ----------------------- | -------- | ------------------------------------------------------------------- |
| Instruction Following | 0.30   | Does output fulfill original request? All requirements addressed? |
| Output Completeness   | 0.25   | All components covered? Appropriate depth? No gaps?               |
| Solution Quality      | 0.25   | Sound approach? Best practices? No correctness issues?            |
| Reasoning Quality     | 0.10   | Clear decision-making? Appropriate methods used?                  |
| Response Coherence    | 0.10   | Well-structured? Easy to understand? Professional?                |

#### Scoring Interpretation

| Score Range | Verdict           | Recommendation              |
| ------------- | ------------------- | ----------------------------- |
| 4.50 - 5.00 | EXCELLENT         | Ready as-is                 |
| 4.00 - 4.49 | GOOD              | Minor improvements optional |
| 3.50 - 3.99 | ACCEPTABLE        | Improvements recommended    |
| 3.00 - 3.49 | NEEDS IMPROVEMENT | Address issues before use   |
| 1.00 - 2.99 | INSUFFICIENT      | Significant rework needed   |

#### Quality Enhancement Techniques

| Technique                | Benefit                                                                                |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| Context Isolation        | Judge receives only extracted context, preventing confirmation bias from session state |
| Chain-of-Thought Scoring | Justification BEFORE score improves reliability by 15-25%                              |
| Evidence Requirement     | Every score requires specific citations (file paths, line numbers, quotes)             |
| Self-Verification        | Judge generates verification questions and documents adjustments                       |
| Bias Mitigation          | Explicit warnings against length bias, verbosity bias, and authority bias              |

#### Theoretical Foundation

Based on:

- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Structured evaluation rubrics with calibrated scoring
- **[Chain of Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Reasoning before conclusion improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique and verification loops
- **[Inference-Time Scaling of Verification](https://arxiv.org/abs/2601.15808)** (Wan et al., 2026) - Rubric-guided verification with test-time self-evolution and iterative feedback refinement

## Skills Overview

### subagent-driven-development - Task Execution with Quality Gates

Use when executing implementation plans with independent tasks or facing multiple independent issues that can be investigated without shared state - dispatches fresh subagent for each task with code review between tasks.

- Purpose - Execute plans through coordinated subagents with quality checkpoints
- Output - Completed implementation with all tasks verified and reviewed

#### When to Use SADD

**Use SADD when:**

- You have an implementation plan with 3+ distinct tasks
- Tasks can be executed independently (or in clear sequence)
- You need quality gates between implementation steps
- Context would accumulate over a long implementation session
- Multiple unrelated failures need parallel investigation
- Different subsystems need changes that do not conflict

**Use regular development when:**

- Single task or simple change
- Tasks are tightly coupled and need shared understanding
- Exploratory work where scope is undefined
- You need human-in-the-loop feedback between every step

#### Usage

```bash

# Use the skill when you have an implementation plan
> I have a plan in specs/feature/plan.md with 5 tasks. Please use subagent-driven development to implement it.

# Or when facing multiple independent issues
> We have 4 failing test files in different areas. Use subagent-driven development to fix them in parallel.
```

## How It Works

SADD supports four execution strategies based on task characteristics:

**Sequential Execution**

For dependent tasks that must be executed in order:

```
Plan Load → Task 1 → Review → Task 2 → Review → Task 3 → ... → Final Review → Complete
            ↓        ↓        ↓        ↓        ↓
         Subagent  Quality  Subagent  Quality  Subagent
                    Gate              Gate
```

**Parallel Execution**

For independent tasks that can run concurrently:

```
                  ┌─ Task 1 (Subagent) ─┐
Plan Load → Batch ┼─ Task 2 (Subagent) ─┼─ Batch Review → Next Batch → Final Review → Complete
                  └─ Task 3 (Subagent) ─┘
```

**Parallel Investigation**

Special case for fixing multiple unrelated failures:

```
                        ┌─ Domain 1 (Agent) ─┐
Identify Domains → Fix ─┼─ Domain 2 (Agent) ─┼─ Review & Integrate → Complete
                        └─ Domain 3 (Agent) ─┘
```

### Multi-Agent Analysis Orchestration

Commands often orchestrate multiple agents to provide comprehensive analysis:

**Sequential Analysis:**

```
Command → Agent 1 → Agent 2 → Agent 3 → Synthesized Result
```

**Parallel Analysis:**

```
         ┌─ Agent 1 ─┐
Command ─┼─ Agent 2 ─┼─ Synthesized Result
         └─ Agent 3 ─┘
```

**Debate Pattern:**

```
Command → Agent 1 ─┐
       → Agent 2 ─┼─ Debate → Consensus → Result
       → Agent 3 ─┘
```

## Processes

### Sequential Execution Process

1. **Load Plan**: Read plan file and create TodoWrite with all tasks
2. **Execute Task with Subagent**: For each task, dispatch a fresh subagent:

   - Subagent reads the specific task from the plan
   - Implements exactly what the task specifies
   - Writes tests following project conventions
   - Verifies implementation works
   - Commits the work
   - Reports back with summary
3. **Review Subagent's Work**: Dispatch a code-reviewer subagent:

   - Reviews what was implemented against the plan
   - Returns: Strengths, Issues (Critical/Important/Minor), Assessment
   - Quality gate: Must pass before proceeding
4. **Apply Review Feedback**:

   - Fix Critical issues immediately (dispatch fix subagent)
   - Fix Important issues before next task
   - Note Minor issues for later
5. **Mark Complete, Next Task**: Update TodoWrite and proceed to next task
6. **Final Review**: After all tasks, dispatch final reviewer for overall assessment
7. **Complete Development**: Use finishing-a-development-branch skill to verify and close

### Parallel Execution Process

1. **Load and Review Plan**: Read plan, identify concerns, create TodoWrite
2. **Execute Batch**: Execute first 3 tasks (default batch size):

   - Mark each as in_progress
   - Follow each step exactly
   - Run verifications as specified
   - Mark as completed
3. **Report**: Show what was implemented and verification output
4. **Continue**: Apply feedback if needed, execute next batch
5. **Complete Development**: Final verification and close

### Parallel Investigation Process

For multiple unrelated failures (different files, subsystems, bugs):

1. **Identify Independent Domains**: Group failures by what is broken
2. **Create Focused Agent Tasks**: Each agent gets specific scope, clear goal, constraints
3. **Dispatch in Parallel**: All agents run concurrently
4. **Review and Integrate**: Verify fixes do not conflict, run full suite

#### Quality Gates

Quality gates are enforced at key checkpoints:

| Checkpoint                   | Gate Type            | Action on Failure           |
| ------------------------------ | ---------------------- | ----------------------------- |
| After each task (sequential) | Code review          | Fix issues before next task |
| After batch (parallel)       | Human review         | Apply feedback, continue    |
| Final review                 | Comprehensive review | Address all findings        |
| Before merge                 | Full test suite      | All tests must pass         |

**Issue Severity Handling:**

- **Critical**: Fix immediately, do not proceed until resolved
- **Important**: Fix before next task or batch
- **Minor**: Note for later, do not block progress

### multi-agent-patterns

Use when single-agent context limits are exceeded, when tasks decompose naturally into subtasks, or when specializing agents improves quality.

**Why Multi-Agent Architectures:**

| Problem                   | Solution                                       |
| --------------------------- | ------------------------------------------------ |
| **Context Bottleneck**    | Partition work across multiple context windows |
| **Sequential Bottleneck** | Parallelize independent subtasks across agents |
| **Generalist Overhead**   | Specialize agents with lean, focused context   |

**Architecture Patterns:**

| Pattern                     | When to Use                                    | Trade-offs                                    |
| ----------------------------- | ------------------------------------------------ | ----------------------------------------------- |
| **Supervisor/Orchestrator** | Clear task decomposition, need human oversight | Central bottleneck, "telephone game" risk     |
| **Peer-to-Peer/Swarm**      | Flexible exploration, emergent requirements    | Coordination complexity, divergence risk      |
| **Hierarchical**            | Large projects with layered abstraction        | Overhead between layers, alignment challenges |

**Example of Implementation:**

```
Supervisor Pattern:
User Request → Supervisor → [Specialist A, B, C] → Aggregation → Output

Key Insight: Sub-agents exist to isolate context, not to anthropomorphize roles
```

## Foundation

The SADD plugin is based on the following foundations:

### Agent Skills for Context Engineering

- [Agent Skills for Context Engineering project](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) by Murat Can Koylan

### Research Papers

**Multi-Agent Patterns:**

- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Du, Y., et al. (2023)
- [Self-Consistency](https://arxiv.org/abs/2203.11171) - Wang, X., et al. (2022)
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) - Yao, S., et al. (2023)

**Evaluation and Critique:**

- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Bai, Y., et al. (2022). Self-critique loops
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - Zheng, L., et al. (2023). Structured evaluation
- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) - Dhuliawala, S., et al. (2023). Verification loops

### Engineering Methodologies

- **Design Studio Method** - Parallel design exploration with critique and synthesis
- **Spike Solutions** (Extreme Programming) - Time-boxed exploration of multiple approaches
- **Ensemble Methods** (Machine Learning) - Combining multiple models for improved performance
