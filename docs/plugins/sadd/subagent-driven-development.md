# subagent-driven-development - Task Execution with Quality Gates

Use when executing implementation plans with independent tasks or facing multiple independent issues that can be investigated without shared state - dispatches fresh subagent for each task with code review between tasks.

- Purpose - Execute plans through coordinated subagents with quality checkpoints
- Output - Completed implementation with all tasks verified and reviewed

## When to Use SADD

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

## Usage

```bash

# Use the skill when you have an implementation plan
> I have a plan in specs/feature/plan.md with 5 tasks. Please use subagent-driven development to implement it.

# Or when facing multiple independent issues
> We have 4 failing test files in different areas. Use subagent-driven development to fix them in parallel.
```

## How It Works

SADD supports three execution strategies based on task characteristics:

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

## Sequential Execution Process

1. **Load Plan**: Reads plan file, creates TodoWrite with all tasks
2. **Execute Task with Subagent**: For each task, dispatches a fresh subagent that reads the task, implements it, writes tests, verifies, commits, and reports back
3. **Review Subagent's Work**: Dispatches a code-reviewer subagent to review against the plan (returns Strengths, Issues by severity, Assessment)
4. **Apply Review Feedback**: Fix Critical issues immediately, Important issues before next task, note Minor issues
5. **Mark Complete, Next Task**: Updates TodoWrite and repeat steps 2-5
6. **Final Review**: After all tasks, dispatches final code-reviewer for overall assessment
7. **Complete Development**: Use finishing-a-development-branch skill to verify and close

## Parallel Execution Process

1. **Loads and Reviews Plan**: Reads plan, identifies concerns, creates TodoWrite
2. **Executes Batch**: Executes first 3 tasks (default batch size), marking each in_progress then completed
3. **Reports**: Shows what was implemented and verification output, says "Ready for feedback"
4. **Continues**: Applies feedback if needed, executes next batch, repeats until complete
5. **Complete Development**: Final verification using finishing-a-development-branch skill

## Parallel Investigation Process

Special case for multiple unrelated failures that can be investigated without shared state:

1. **Identifies Independent Domains**: Groups failures by what is broken (e.g., different test files, different subsystems)
2. **Creates Focused Agent Tasks**: Each agent gets specific scope, clear goal, constraints, and expected output format
3. **Dispatch in Parallel**: All agents run concurrently
4. **Reviews and Integrates**: Reads each summary, verifies fixes do not conflict, runs full test suite

