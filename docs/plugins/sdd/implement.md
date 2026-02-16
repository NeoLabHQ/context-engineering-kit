# /sdd:implement - Task Implementation with Verification

Execute task implementation steps using automated LLM-as-Judge quality verification, sequential and parallel execution, and Definition of Done (DoD) validation.

- **Purpose**: Implement all steps from a planned task specification and verify the results.
- **Output**: Working code with passing tests; task moved to `.specs/tasks/done/`.

```bash
/sdd:implement [task-file] [options]
```

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task-file` | Path or filename | Auto-detect | Task file name or path (e.g., `add-validation.feature.md`). Auto-selects from `in-progress/` or `todo/` if only one task exists. |
| `--target-quality` | `--target-quality X.X` or `X.X,Y.Y` | `4.0` (standard) / `4.5` (critical) | Quality threshold. Single value sets both. Two comma-separated values set standard,critical. |
| `--max-iterations` | `--max-iterations N` | `3` | Maximum fix→verify cycles per step. Set to `unlimited` for no limit. |
| `--human-in-the-loop` | `--human-in-the-loop [s1,s2,...]` | None | Steps after which to pause for review. If no steps are specified, the process pauses after every step. |
| `--skip-judges` | flag | `false` | Skip all judge validation — fast but provides no quality gates |
| `--continue` | flag | None | Resume from the last completed step |
| `--refine` | flag | `false` | Detect changed project files and re-verify from the earliest affected step |

## Workflow Diagram

```
+--------------------------------------+
| Phase 0: Select Task                 |
|  Task from todo/ or in-progress/     |
|              |                       |
|              v                       |
|  Move to in-progress/                |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| Phase 1: Load Task                   |
|  Parse Implementation Steps          |
|  & Verification Requirements         |
+------------------+-------------------+
                   |
                   v
+------------------------------------------------------+
| Phase 2: Execute Steps                               |
|                                                      |
|  For Each Step:                                      |
|                                                      |
|    Developer Agent: Implement Step  <--+             |
|                |                       |             |
|                v                       |             |
|       Verification Level?              |             |
|        |       |       |       |       |             |
|      None   Single   Panel  Per-Item   |             |
|        |    (4.0)   (4.5)  (Parallel)  |             |
|        |       |       |       |       |             |
|        |       +---+---+-------+       |             |
|        |           |                   |             |
|        |           v                   |             |
|        |        PASS? --No--> Fix & Retry            |
|        |           |                                 |
|        |          Yes                                |
|        +-----+-----+                                |
|              |                                       |
|              v                                       |
|       Mark Step DONE                                 |
+----------------------+-------------------------------+
                       |
                       v
+--------------------------------------+
| Phase 3: Final Verification          |
|                                      |
|  Verify Definition of Done  <--+     |
|              |                  |     |
|              v                  |     |
|      All DoD PASS?              |     |
|         /       \               |     |
|       Yes       No              |     |
|        |         \              |     |
|        |     Fix Failing Items--+     |
+--------+-----------------------------+
         |
         v
+--------------------------------------+
| Phase 4: Complete                    |
|  Move to done/                       |
|  Final Report                        |
+--------------------------------------+
```

## How It Works

### Phase 0: Select Task & Move to In-Progress

1. Resolves the task file by checking `in-progress/` first, then `todo/`
2. Moves the task from `todo/` to `in-progress/`
3. Parses flags and displays resolved configuration

### Phase 1: Load and Analyze Task

Reads the task file once and parses the `## Implementation Process` section:

- Lists all steps with dependencies
- Identifies parallel execution opportunities (`Parallel with:` annotations)
- Classifies verification needs from `#### Verification` sections

### Phase 2: Execute Implementation Steps

For each step in dependency order, the orchestrator launches sub-agents and judges:

#### Pattern A: Simple Step (No Verification)

For simple operations (directory creation, file deletion):

1. Launch `sdd:developer` agent to implement the step
2. Mark the step as complete — no judge verification is needed

#### Pattern B: Critical Step (Panel of 2 Evaluations)

For critical artifacts requiring high confidence:

1. Launch the `sdd:developer` agent to implement the step
2. Launch 2 `sdd:developer` evaluation agents **in parallel** with the step's rubric
3. Calculate the median score; pass if median ≥ threshold
4. On failure: iterate through fix→verify cycles until they pass or the maximum number of iterations is reached

#### Pattern C: Multi-Item Step (Per-Item Evaluations)

For steps creating multiple similar items:

1. Launch `sdd:developer` agents **in parallel** (one per item)
2. Launch evaluation agents **in parallel** (one per item)
3. All items must pass; failing items are re-implemented
4. Iterate until all pass or the maximum number of iterations is reached

### Phase 3: Final Verification

After all steps complete:

1. Launch `sdd:developer` agent to verify all **Definition of Done** items
2. Each item is checked for evidence (e.g., passing tests, successful builds, existing files, matching patterns)
3. Failing items are fixed by dedicated developer agents
4. Re-verify until all items pass

### Phase 4: Complete

1. Move task from `in-progress/` to `done/`
2. All step titles are marked `[DONE]`, and subtasks are marked `[X]`
3. All DoD items are marked `[X]`
4. Generate a final implementation report

## Verification Levels

| Level | When Used | Configuration |
|-------|-----------|---------------|
| None | Simple operations (mkdir, delete) | Skip verification |
| Single Judge | Non-critical artifacts | 1 judge, threshold 4.0/5.0 |
| Panel of 2 Judges | Critical artifacts | 2 judges, median voting, threshold 4.5/5.0 |
| Per-Item Judges | Multiple similar items | 1 judge per item, parallel execution |

## Continue Mode (`--continue`)

Resumes implementation from the last completed step:

1. Parses task file for `[DONE]` markers
2. Launches judge to verify the last incomplete step's artifacts
3. If PASS: marks done, resumes from next step
4. If it fails: re-implement the step and iterate

## Refine Mode (`--refine`)

Detects changes to **project files** (not the task file) and re-verifies from the earliest affected step:

1. Detects changed files via `git diff`
2. Maps changed files to implementation steps using "Expected Output" and artifact paths
3. Determines the earliest affected step
4. Launches a judge for each affected step — if it passes, the user's fix is accepted; if it fails, the implementation agent aligns the rest of the code with the user's changes
5. All subsequent steps are also re-verified

## Human-in-the-Loop (`--human-in-the-loop`)

After each specified step passes:

1. Displays step results, artifacts, and judge feedback
2. Asks: `Continue? [Y/n/feedback]`
3. User feedback is incorporated into subsequent iterations
4. User can pause the workflow at any point

## Usage Examples

```bash
# Implement a specific task
/sdd:implement add-validation.feature.md

# Auto-select task from todo/ or in-progress/ (if only 1 task)
/sdd:implement

# Continue from last completed step
/sdd:implement add-validation.feature.md --continue

# Refine after manually fixing project files
/sdd:implement add-validation.feature.md --refine

# Human review after every step
/sdd:implement add-validation.feature.md --human-in-the-loop

# Human review after specific steps only
/sdd:implement add-validation.feature.md --human-in-the-loop 2,4,6

# Stricter quality threshold (both standard and critical set to 4.5)
/sdd:implement critical-api.feature.md --target-quality 4.5

# Different thresholds for standard (3.5) and critical (4.5)
/sdd:implement add-validation.feature.md --target-quality 3.5,4.5

# Unlimited iterations until quality threshold met
/sdd:implement add-validation.feature.md --max-iterations unlimited

# Skip judges for fast execution (no quality gates)
/sdd:implement add-validation.feature.md --skip-judges

# Combined: continue with human review
/sdd:implement add-validation.feature.md --continue --human-in-the-loop
```

## Task Lifecycle

| When | Action |
|------|--------|
| Start implementation | Move task from `todo/` → `in-progress/` |
| Final verification PASS | Move task from `in-progress/` → `done/` |
| Implementation aborted | Keep in `in-progress/` |

## Best Practices

- Let the orchestrator work autonomously — it launches sub-agents for both implementation and verification
- Use `--continue` if the process is interrupted — it picks up where it left off
- Use `--refine` after making manual fixes — it re-verifies affected steps without re-implementing everything
- For critical features, use `--target-quality 4.5` to enforce stricter quality
- Use `--human-in-the-loop` for high-risk implementations where you want to review each step
- Use `--skip-judges` only for well-understood tasks where speed matters more than verification
