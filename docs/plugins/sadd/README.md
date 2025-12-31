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

### do-competitively - Competitive Multi-Agent Synthesis

Execute tasks through competitive generation, multi-judge evaluation, and evidence-based synthesis to produce superior results.

- Purpose - Generate multiple solutions competitively, evaluate with independent judges, synthesize best elements
- Pattern - Generate-Critique-Synthesize (GCS) with self-critique, verification loops, and adaptive strategy selection
- Output - Superior solution combining best elements from all candidates
- Cost - Variable (6-7 agents depending on strategy: 3 generators + 3 judges + 0-1 synthesizer/polish agent)
- Quality - Enhanced with Constitutional AI self-critique, Chain of Verification, and intelligent strategy selection
- Efficiency - 15-20% average cost savings through adaptive strategy (polish clear winners, redesign failures)

## Pattern: Generate-Critique-Synthesize (GCS)

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

#### Usage

```bash
# Basic usage
/do-competitively <task-description>

# With explicit output specification
/do-competitively "Create authentication middleware" --output "src/middleware/auth.ts"

# With specific evaluation criteria
/do-competitively "Design user schema" --criteria "scalability,security,developer-experience"
```

#### Quality Enhancement Techniques

Techniques that were used to enhance the quality of the competitive execution pattern.

| Phase | Technique | Benefit |
|-------|-----------|---------|
| **Phase 1** | Constitutional AI Self-Critique | Generators review and fix their own solutions before submission, catching 40-60% of issues |
| **Phase 2** | Chain of Verification | Judges verify their evaluations with structured questions, improving calibration and reducing bias |
| **Phase 2.5** | Adaptive Strategy Selection | Orchestrator parses structured judge outputs (VOTE+SCORES) to select optimal strategy, saving 15-20% cost on average |
| **Phase 3** | Evidence-Based Synthesis | Combines proven best elements rather than creating new solutions (only when needed) |


#### Theoretical Foundation

The competitive execution pattern combines insights from:

**Academic Research:**
- Multi-Agent Debate (Du et al., 2023) - Diverse perspectives improve reasoning
- Self-Consistency with CoT (Wang et al., 2022) - Multiple reasoning paths improve reliability
- Tree of Thoughts (Yao et al., 2023) - Exploration of solution branches before commitment
- Constitutional AI (Bai et al., 2022) - Self-critique loops catch 40-60% of issues before review
- Chain-of-Verification (Dhuliawala et al., 2023) - Structured verification reduces bias
- LLM-as-a-Judge (Zheng et al., 2023) - Structured evaluation rubrics

**Engineering Practices:**
- Design Studio Method - Parallel design, critique, synthesis
- Spike Solutions (XP/Agile) - Explore approaches, combine best
- A/B Testing - Compare alternatives with clear metrics
- Ensemble Methods - Combining multiple models improves performance



### judge - Single-Agent Work Evaluation

Evaluate completed work using LLM-as-Judge with structured rubrics and evidence-based scoring.

- Purpose - Assess quality of work produced earlier in conversation
- Output - Evaluation report with scores, evidence, improvements
- Pattern - Single judge with multi-dimensional rubric

#### Usage

```bash
> Write new controller for the user model

# Evaluate completed work
/judge
```

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

| Checkpoint | Gate Type | Action on Failure |
|------------|-----------|-------------------|
| After each task (sequential) | Code review | Fix issues before next task |
| After batch (parallel) | Human review | Apply feedback, continue |
| Final review | Comprehensive review | Address all findings |
| Before merge | Full test suite | All tests must pass |

**Issue Severity Handling:**

- **Critical**: Fix immediately, do not proceed until resolved
- **Important**: Fix before next task or batch
- **Minor**: Note for later, do not block progress

### multi-agent-patterns

Use when single-agent context limits are exceeded, when tasks decompose naturally into subtasks, or when specializing agents improves quality.

**Why Multi-Agent Architectures:**

| Problem | Solution |
|---------|----------|
| **Context Bottleneck** | Partition work across multiple context windows |
| **Sequential Bottleneck** | Parallelize independent subtasks across agents |
| **Generalist Overhead** | Specialize agents with lean, focused context |

**Architecture Patterns:**

| Pattern | When to Use | Trade-offs |
|---------|-------------|------------|
| **Supervisor/Orchestrator** | Clear task decomposition, need human oversight | Central bottleneck, "telephone game" risk |
| **Peer-to-Peer/Swarm** | Flexible exploration, emergent requirements | Coordination complexity, divergence risk |
| **Hierarchical** | Large projects with layered abstraction | Overhead between layers, alignment challenges |

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
- Du, Y., et al. (2023). "Improving Factuality and Reasoning in Language Models through Multiagent Debate"
- Wang, X., et al. (2022). "Self-Consistency Improves Chain of Thought Reasoning in Language Models"
- Yao, S., et al. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"

**Evaluation and Critique:**
- Bai, Y., et al. (2022). "Constitutional AI: Harmlessness from AI Feedback" - Self-critique loops
- Zheng, L., et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" - Structured evaluation
- Dhuliawala, S., et al. (2023). "Chain-of-Verification Reduces Hallucination in Large Language Models" - Verification loops

### Engineering Methodologies

- **Design Studio Method** - Parallel design exploration with critique and synthesis
- **Spike Solutions** (Extreme Programming) - Time-boxed exploration of multiple approaches
- **Ensemble Methods** (Machine Learning) - Combining multiple models for improved performance

