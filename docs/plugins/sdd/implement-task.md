# /implement-task - Task Implementation with Verification

Execute task implementation steps using automated LLM-as-Judge quality verification at the end of every implementation phase, sequential and parallel execution, and Definition of Done (DoD) validation.

- **Purpose**: Implement all steps from a planned task specification and verify the results.
- **Output**: Working code with passing tests; task moved to `.specs/tasks/done/`.

```bash
/implement-task [task-file] [options]
```

## Two Things Are Called "Phase"

| Term | Meaning |
|------|---------|
| **Workflow phase** | A stage of this command itself — select task, load, execute, verify the Definition of Done, move the task, report. Numbered `Workflow Phase 0`-`Workflow Phase 5` throughout this page. |
| **Implementation phase** / `Phase N` | A milestone in the task file's `### Phase Overview`. It groups steps, names a `Reviewer model`, and lists the acceptance criteria due at that milestone. **This is the unit of code review.** |
| **Step** | One sub-task file at `.specs/sub-tasks/<task-name>/<NN>-<step-slug>.md`. **This is the unit of implementation dispatch.** |

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task-file` | Path or filename | Auto-detect | Task file name or path (e.g., `add-validation.feature.md`). Auto-selects from `in-progress/` or `todo/` if only one task exists. |
| `--model` | `opus\|sonnet\|haiku` | Unset | Model for all sub-agents — implementation agents and `sdd:code-reviewer`. Overrides every model in the task specification file. When omitted, step models come from the Parallelization Overview and reviewer models from the Phase Overview. |
| `--target-quality` | `--target-quality X.X` | `4.0` | The single quality threshold applied to every implementation phase review. There is no separate standard/critical value and no comma-separated form. |
| `--max-iterations` | `--max-iterations N` | `3` | Maximum fix→re-review cycles per implementation phase. Set to `unlimited` for no limit. |
| `--human-in-the-loop` | `--human-in-the-loop [Phase 1,Phase 3,...]` | None | Implementation **phases** after whose review to pause. If no phases are specified, the process pauses after every implementation phase. |
| `--skip-reviews` | flag | `false` | Skip all phase reviews — fast but provides no quality gates |
| `--continue` | flag | None | Resume from the last completed step, within the implementation phase in progress |
| `--refine` | flag | `false` | Detect changed project files and re-verify from the implementation phase that owns the earliest affected step |
| `--strict` | flag | `false` | Disable iteration discretion — a phase passes ONLY when its score reaches the threshold, otherwise iterate until `--max-iterations` |

**The task file carries no threshold at all.** Quality thresholds are orchestrator configuration only; the planning agents are forbidden from writing one.


## Context Management

If you ran `/plan-task` in the same session, run `/clear` (or re-open Claude Code) before `/implement-task`. The planning phase fills the context window with analysis artifacts; starting fresh gives the implementation agents a clean context for better results.


## Workflow Diagram

```
+--------------------------------------+
| Workflow Phase 0: Select Task        |
|  Task from todo/ or in-progress/     |
|              |                       |
|              v                       |
|  Move to in-progress/                |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| Workflow Phase 1: Load Task          |
|  Parse ### Parallelization Overview  |
|   (steps, models, agents, sub-task   |
|    file paths)                       |
|  Parse ### Phase Overview            |
|   (phases, steps, reviewer models,   |
|    criteria due)                     |
+------------------+-------------------+
                   |
                   v
+------------------------------------------------------+
| Workflow Phase 2: Execute Implementation Phases      |
|                                                      |
|  For Each Implementation Phase, in order:            |
|                                                      |
|   +----------------------------------------------+   |
|   | For each step of the phase, in dependency    |   |
|   | order (Parallel with: groups together):      |   |
|   |   Launch its Agent at its Model with         |   |
|   |   task file path + sub-task file path        |   |
|   +---------------------+------------------------+   |
|                         | all steps reported done    |
|                         v                            |
|   +----------------------------------------------+   |
|   | Launch ONE sdd:code-reviewer for the PHASE   |   |
|   | at the phase's Reviewer model                |   |
|   +---------------------+------------------------+   |
|                         |                            |
|                         v                            |
|   +----------------------------------------------+   |
|   | Apply THRESHOLD to combined_score:           |   |
|   |  PASS -> mark phase [REVIEWED], next phase   |   |
|   |  FAIL -> reason about BLAST RADIUS, pick     |   |
|   |          fix model + scope + re-review model,|   |
|   |          re-review (up to max-iterations)    |   |
|   +----------------------------------------------+   |
+----------------------+-------------------------------+
                       |
                       v
+--------------------------------------+
| Workflow Phase 3: Final Verification |
|                                      |
|  Verify Definition of Done  <--+     |
|              |                 |     |
|              v                 |     |
|      All DoD PASS?             |     |
|         /       \              |     |
|       Yes       No             |     |
|        |         \             |     |
|        |    Fix Failing Items--+     |
+--------+-----------------------------+
         |
         v
+--------------------------------------+
| Workflow Phase 4: Move Task to Done  |
|  Move to done/                       |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| Workflow Phase 5: Aggregation and    |
| Reporting                            |
|  Final Report                        |
+--------------------------------------+
```

## How It Works

### Workflow Phase 0: Select Task & Move to In-Progress

1. Resolves the task file by checking `in-progress/` first, then `todo/`
2. Moves the task from `todo/` to `in-progress/`
3. Parses flags and displays resolved configuration

### Workflow Phase 1: Load and Analyze Task

Reads the task file **once** and parses the `## Implementation Process` section:

- `### Parallelization Overview` — every step with its implementation phase, model, agent, dependencies, `Parallel with:` group and `Sub-Task File` path
- `### Phase Overview` — every implementation phase with its `Steps:`, its `Reviewer model:`, and the checklist items and rubrics due at that milestone

### Workflow Phase 2: Execute Implementation Phases

Implementation phases run **in order**. There is exactly one dispatch pattern, and it applies to every phase without exception:

1. **Dispatch one implementation agent per step**, in dependency order, with steps in the same `Parallel with:` group launched simultaneously. Each agent receives the task file path **and** its own sub-task file path, and runs at the model named in that step's `Model` column of the Parallelization Overview. The step's content is never pasted into the prompt — passing the path is the contract, and the orchestrator does not read the sub-task file itself when dispatching.
2. **When every step of the phase has reported completion, launch exactly ONE `sdd:code-reviewer`** for the phase, at that phase's `Reviewer model`. It receives four inputs and nothing else: the task file path, the phase identifier, the artifact paths the step agents reported, and `CLAUDE_PLUGIN_ROOT`. The reviewer resolves the phase's sub-task file paths itself; it is never given a threshold or a pass/fail expectation.
3. **The orchestrator applies the threshold** to the reviewer's `combined_score`. On PASS the phase is marked `[REVIEWED]` and the next phase begins.
4. **On FAIL, the orchestrator reasons about blast radius** before dispatching anything — see below.

Because the phase is the review unit, individual steps are never reviewed on their own, and no phase review is skipped for being "simple" unless `--skip-reviews` is set.

#### Partial Fulfilment Is Expected

A phase is a checkpoint, not the finish line. The reviewer scores **only** the checklist items and rubric criteria that phase's `#### Phase N` block lists as due. Acceptance criteria that belong to a later phase are not yet due and are never counted as missing or incomplete.

#### Failure Handling: Blast-Radius Reasoning

When a phase review fails, the orchestrator matches the capability of the fixing agent — and of the agent that re-reviews the fix — to the **blast radius of the findings**, not to the models that originally built the phase. It walks scope → depth → coupling → severity → ceiling, then chooses the fix model, the fix scope (which sub-task files to re-dispatch) and the re-review model, and records that reasoning in the final report. Two illustrations of the same failing verdict:

- **The whole phase failed** — High findings across all steps, the phase's shared abstraction is wrong. The whole phase is re-dispatched at a higher tier, and the re-review is escalated too, because the review that let the broken shape through is not a check.
- **One step failed** — a single High finding on one step, the others clean, no rework required. Only that step is re-dispatched, at its original model, and the phase is re-reviewed at its usual `Reviewer model`. Steps whose work is sound are never re-dispatched.

### Workflow Phase 3: Final Verification

After all steps complete:

1. Launch `sdd:developer` agent to verify all **Definition of Done** items
2. Each item is checked for evidence (e.g., passing tests, successful builds, existing files, matching patterns)
3. Failing items are fixed by dedicated developer agents
4. Re-verify until all items pass

### Workflow Phase 4: Move Task to Done

1. Confirm every Definition of Done item is marked complete in the task file
2. Move the task from `in-progress/` to `done/` with `git mv` (plain `mv` if git is unavailable)

`.specs/sub-tasks/<task-name>/` is deliberately **not** moved, so the `Sub-Task File` paths recorded in the task file keep resolving.

### Workflow Phase 5: Aggregation and Reporting

Generates the final implementation report: the configuration used, the steps completed, the phase reviews, the blast-radius fix decisions, the Definition of Done verification results and follow-up recommendations. Its `### Task File Updated` section records that all step rows are marked `[DONE]` in the Parallelization Overview, every phase heading `[REVIEWED]` (or `[REVIEWED-SKIPPED]` where `--skip-reviews` suppressed the review), all Definition of Done items `[X]`, and the sub-task files' subtasks `[X]`.

## Phase Reviews

There is exactly one review configuration, and it is the same for every implementation phase:

| Property | Value |
|----------|-------|
| Reviewer | ONE `sdd:code-reviewer`, dispatched once per implementation phase |
| When | After every step of the phase has reported completion |
| Model | The phase's `Reviewer model` from the Phase Overview, unless `--model` overrides it |
| Threshold | The single `--target-quality` value (default `4.0`), applied by the orchestrator, never passed to the reviewer |
| Scored against | Only the checklist items and rubric criteria the phase lists as due, plus built-in code quality, Muda waste and test coverage analysis |
| Skipped when | `--skip-reviews` is set — the phase is marked `[REVIEWED-SKIPPED]` |

The reviewer returns a `combined_score`, a list of issues each attributed to a step, and a blast-radius report. The orchestrator alone decides PASS/FAIL from it.

## Continue Mode (`--continue`)

Resumes by **implementation phase, then step**:

1. Parses the step table for `[DONE]` markers and the phase headings for `[REVIEWED]` / `[REVIEWED-SKIPPED]`
2. Resumes at the first phase carrying neither marker, and dispatches that phase's steps that are not yet `[DONE]`
3. If that phase's steps are all done but its review never ran, launches the phase review — unless `--skip-reviews` is set, which marks it `[REVIEWED-SKIPPED]` and moves on
4. On a failing review, enters blast-radius failure handling for that phase

## Refine Mode (`--refine`)

Detects changes to **project files** (not the task file) and re-verifies from the implementation phase that owns the earliest affected step:

1. Picks its comparison base from the git state: when **both** staged and unstaged changes exist it compares the working directory against the staging area (unstaged changes only); when there are **only** staged or **only** unstaged changes it compares against the last commit. With neither, it exits with a message.
2. Maps changed files to steps using each sub-task file's `#### Expected Output`, then maps each step to its implementation phase
3. Determines the earliest affected implementation phase
4. Launches one `sdd:code-reviewer` per affected phase — if it passes, the user's fix is accepted; if it fails, the orchestrator reasons about blast radius and dispatches fixes for the affected steps only, without overwriting the user's changes
5. All subsequent phases are also re-verified, because they build on the changed one

## Human-in-the-Loop (`--human-in-the-loop`)

Checkpoints are keyed on **implementation phases**, never on individual steps. After the review of each specified phase passes:

1. Displays the phase's step results, artifacts, reviewer model, `combined_score` and consolidated issues
2. Asks: `Continue? [Y/n/feedback]`
3. User feedback is incorporated into subsequent iterations
4. User can pause the workflow at any point

## Usage Examples

```bash
# Implement a specific task
/implement-task add-validation.feature.md

# Auto-select task from todo/ or in-progress/ (if only 1 task)
/implement-task

# Continue from last completed step
/implement-task add-validation.feature.md --continue

# Refine after manually fixing project files
/implement-task add-validation.feature.md --refine

# Human review after every implementation phase
/implement-task add-validation.feature.md --human-in-the-loop

# Human review after specific implementation phases only
/implement-task add-validation.feature.md --human-in-the-loop "Phase 1,Phase 3"

# Stricter quality threshold for every phase review
/implement-task critical-api.feature.md --target-quality 4.5

# Lower threshold for faster convergence
/implement-task add-validation.feature.md --target-quality 3.5

# Unlimited iterations until quality threshold met
/implement-task add-validation.feature.md --max-iterations unlimited

# Skip all phase reviews for fast execution (no quality gates)
/implement-task add-validation.feature.md --skip-reviews

# Never accept a phase below target quality
/implement-task add-validation.feature.md --strict

# Force every sub-agent onto one model, overriding the task file
/implement-task add-validation.feature.md --model sonnet

# Combined: continue with human review
/implement-task add-validation.feature.md --continue --human-in-the-loop
```

## Task Lifecycle

| When | Action |
|------|--------|
| Start implementation | Move task from `todo/` → `in-progress/` |
| Final verification PASS | Move task from `in-progress/` → `done/` |
| Implementation aborted | Keep in `in-progress/` |

The task's sub-task folder `.specs/sub-tasks/<task-name>/` **never moves** while the task file travels between these folders, so the `Sub-Task File` paths recorded in the task file stay valid.

## Best Practices

- Let the orchestrator work autonomously — it launches sub-agents for both implementation and review
- Use `--continue` if the process is interrupted — it picks up at the phase in progress
- Use `--refine` after making manual fixes — it re-verifies affected phases without re-implementing everything
- For critical features, use `--target-quality 4.5` to enforce stricter quality
- Use `--human-in-the-loop` for high-risk implementations where you want to review each milestone
- Use `--skip-reviews` only for well-understood tasks where speed matters more than verification
- Use `--strict` when the target quality is non-negotiable and you accept the extra iterations it costs
- Use `--model` to force one model everywhere (e.g. `haiku` for a cheap dry run); leave it off to keep the per-step and per-phase models chosen during planning
