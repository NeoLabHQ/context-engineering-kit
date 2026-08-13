# /plan-task - Task Refinement & Planning

Refine a draft task specification into a fully planned, implementation-ready task with acceptance criteria, architecture, per-step sub-task files and verifiable phases.

- Purpose - Transforms a draft task into a complete specification with acceptance criteria, architecture, and a decomposition into per-step sub-task files grouped into independently verifiable phases
- Output - A refined task file moved to `.specs/tasks/todo/`, one sub-task file per step under `.specs/sub-tasks/<task-name>/`, plus skill files in `.claude/skills/` and analysis files in `.specs/analysis/`

```bash
/plan-task .specs/tasks/draft/add-validation.feature.md [options]
```

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `task-file` | Path | **Required** | Path to draft task file (e.g., `.specs/tasks/draft/add-validation.feature.md`) |
| `--target-quality` | `--target-quality X.X` | `3.5` | Target threshold (out of 5.0) for judge pass/fail decisions |
| `--max-iterations` | `--max-iterations N` | `3` | Maximum retry cycles per phase before moving on |
| `--included-stages` | `--included-stages s1,s2,...` | All stages | Comma-separated list of stages to include |
| `--skip` | `--skip s1,s2,...` | None | Comma-separated list of stages to exclude |
| `--fast` | flag | N/A | Alias for `--target-quality 3.0 --max-iterations 1 --included-stages business analysis,decomposition` — same stages as `--one-shot`, but judges still run, at a lowered threshold with a single retry |
| `--one-shot` | flag | N/A | Alias for `--included-stages business analysis,decomposition --skip-judges` — same stages as `--fast`, but no judge runs at all |
| `--human-in-the-loop` | `--human-in-the-loop p1,p2,...` | None | Phases after which to pause for human review |
| `--skip-judges` | flag | `false` | Skip all judge validation checks |
| `--refine` | flag | `false` | Detect changes via git diff and re-run only affected stages |
| `--continue` | `--continue [stage]` | None | Resume from a specific stage (auto-detects if stage not provided) |
| `--model` | `opus\|sonnet\|haiku` | *auto-selected* | Explicit override for every planning agent and judge. When omitted, the orchestrator picks a baseline tier from the task's shape (`sonnet` is the working default; `opus` must be earned by a breadth, critical-domain or open-design trigger) and runs architecture synthesis one tier above it, capped at `opus`. |
| `--strict` | flag | `false` | Disable iteration discretion — a phase passes ONLY when its score reaches the threshold, otherwise retry until `--max-iterations` |

## Stage Names

| Stage Name | Phase | Description |
|------------|-------|-------------|
| `research` | 2a | Gathers relevant resources, documentation, and libraries |
| `codebase analysis` | 2b | Identifies affected files, interfaces, and integration points |
| `business analysis` | 2c | Refines the description and creates the acceptance criteria (checklist, regular checks, rubric, test strategy, definition of done) |
| `architecture synthesis` | 3 | Synthesizes research and analysis into an architecture |
| `decomposition` | 4 | Breaks the architecture into per-step sub-task files grouped into verifiable phases, with dependencies, parallel groups and agent/model assignments |

## Workflow Diagram

```
                +----------------------------+
                |      Draft Task File       |
                | .specs/tasks/draft/*.md    |
                +-------------+--------------+
                              |
                              v
+----------------------------------------------------------+
| Phase 2: Parallel Analysis                               |
|                                                          |
| +----------------+  +------------------+  +-------------+|
| | Research       |  | Codebase         |  | Business    ||
| | researcher     |  | Analysis         |  | Analysis    ||
| |                |  | code-explorer    |  | business-   ||
| |      |         |  |                  |  | analyst     ||
| |      v         |  |       |          |  |      |      ||
| |  Judge 2a      |  |   Judge 2b       |  |   Judge 2c  ||
| +------+---------+  +--------+---------+  +------+------+|
|        |    all three at the baseline tier   |           |
+----------------------------------------------------------+
         |                     |                    |
         +----------+----------+--------------------+
                    |
                    v
         +-----------------------------+
         | Phase 3: Architecture       |
         | software-architect          |
         | (baseline + 1, cap opus)    |
         |            |                |
         |            v                |
         |        Judge 3              |
         +--------------+--------------+
                        |
                        v
         +-----------------------------+
         | Phase 4: Decomposition      |
         | tech-lead (baseline)        |
         |                             |
         | -> task file:               |
         |    ## Implementation Process|
         | -> .specs/sub-tasks/        |
         |    <task-name>/             |
         |      <NN>-<step-slug>.md    |
         |            |                |
         |            v                |
         |        Judge 4              |
         +--------------+--------------+
                        |
                        v
         +-----------------------------+
         | Promote: draft/ -> todo/    |
         | (file move, no agent)       |
         +--------------+--------------+
                        |
      +-----------------+-----------------+-----------------+
      |                 |                 |                 |
      v                 v                 v                 v
+--------------+ +--------------+ +---------------+ +----------------+
| Refined Task | | Skill File   | | Analysis File | | Sub-Task Files |
| todo/*.md    | | SKILL.md     | | analysis-*.md | | sub-tasks/**   |
+--------------+ +--------------+ +---------------+ +----------------+
```

## How It Works

### Phase 2: Parallel Analysis

Three analysis agents run **in parallel**, each at the run's baseline model tier and each with its own judge validation:

- **Phase 2a: Research** (`researcher` agent) — Gathers relevant resources, documentation, and libraries. Creates or updates a reusable skill file in `.claude/skills/`.
- **Phase 2b: Codebase Impact Analysis** (`code-explorer` agent) — Identifies affected files, interfaces, and integration points. Produces an analysis file in `.specs/analysis/`.
- **Phase 2c: Business Analysis** (`business-analyst` agent) — Refines the task description (scope, user scenarios) and writes the single `## Acceptance Criteria` section.

Each sub-phase is validated by a judge agent. All three must pass before proceeding.

`## Acceptance Criteria` holds exactly six sub-blocks, in this order, with business and technical criteria mixed inside each:

| Sub-block | Contents |
|-----------|----------|
| `**Checklist:**` | Table `\| ID \| Question \| Category \| Importance \|` with stable `CK-n` / `HR-n` IDs; every row a boolean YES/NO question |
| `**Regular Checks:**` | Checkbox list using the project's actual build / lint / test commands |
| `**Rubric:**` | Table `\| Criterion \| Weight \|`, weights summing to 1.0 |
| `**Rubric Score Definitions:**` | One `###` section per rubric criterion with a contrastive `Anchors` list (`score_2` / `score_4` / `contrast`); no 1-5 bins |
| `**Test Strategy:**` | Criticality, a Test Matrix table, and `Test Cases to Cover` grouped under `#### CK-N:` headings |
| `**Definition of Done:**` | Derived from the criteria above; consumed by `/implement-task`'s final verification |

The task file carries **no scoring configuration** — no thresholds, no judge counts, no evaluation modes. Those are orchestrator settings only.

### Phase 3: Architecture Synthesis

`software-architect` agent — the only **heavy** phase, run one tier above the baseline (capped at `opus`) — synthesizes findings from research, codebase analysis, and business analysis into an architectural overview featuring key decisions, a solution strategy, and expected file changes.

### Phase 4: Decomposition

`tech-lead` agent (baseline tier) breaks the architecture into implementation steps, writes each step as its own sub-task file under `.specs/sub-tasks/<task-name>/`, and groups the steps into independently verifiable phases.

It writes **only** the task file's `## Implementation Process` section:

- a sub-agent execution directive,
- `### Parallelization Overview` — an ASCII dependency diagram with phase boundaries, plus a step table with columns `Step | Phase | Model | Agent | Depends on | Parallel with | Sub-Task File`,
- `### Phase Overview` — per phase a `#### Phase N` block with `Steps:`, `Reviewer model:`, a `Checklist items:` list citing `CK-n`/`HR-n` IDs and a `Rubrics:` list citing rubric criterion names. There is no threshold anywhere.

Each phase must leave an independently verifiable milestone: a working application or service that could be committed and run, **plus** the tests or other verification artifacts that let a reviewer judge it. The step model and the phase's reviewer model are chosen per-step and per-phase from the same tier policy, with the reviewer normally one tier above the implementation models it checks.

Every step body lives in its sub-task file at `.specs/sub-tasks/<task-name>/<NN>-<step-slug>.md`, carrying `**Task File:**`, `**Phase:**`, `**Model:**`, `**Agent:**`, `**Depends on:**`, `**Parallel with:**`, `**Note:**`, `**Goal:**`, a step description, `#### Expected Output`, `#### Success Criteria`, `#### Subtasks` and `#### Blockers & Risks`.

### Promote Task

Moves the refined task file from `draft/` to `todo/` and stages all generated artifacts with Git. This is a plain file move — no agent, no model tier, no judge.

**The sub-task folder does not move.** `.specs/sub-tasks/<task-name>/` is created at planning time and stays put while the task file travels `draft/` → `todo/` → `in-progress/` → `done/`, so the paths recorded in the Parallelization Overview never go stale.

Staging at the end records the generated artifacts, so any manual edits you make afterwards are the only unstaged changes in the task file. `--refine` still diffs the task file with `git diff HEAD` — against the last commit — which sees staged and unstaged edits alike.

## Quality Gates

Each of the five phases is followed by one LLM-as-Judge validation, run by the same agent type as the phase and at the same model tier:

| Judge | Validates | Rubric dimensions |
|-------|-----------|-------------------|
| Judge 2a | The skill file's coverage, relevance and reusability | 5 |
| Judge 2b | File identification, interfaces, integration points, risk | 4 |
| Judge 2c | Description, criteria quality, scenarios, scope, rubric quality, coverage completeness, test strategy coverage | 7 |
| Judge 3 | Solution strategy, reference integration, section relevance, expected changes | 4 |
| Judge 4 | Step quality, success-criteria testability, risk coverage, completeness, dependency accuracy, parallelization, agent/model selection, phase design | 8 |

Verdicts:

- **PASS** (score >= threshold) — Phase complete; proceed to the next stage.
- **ACCEPTED** (score below threshold but at or above the floor) — Accepted because of only low/medium priority issues, all target requirements are met.
- **FAIL** (score < threshold) — Re-run the phase with judge feedback.
- **MAX_ITERATIONS reached** — Proceed to the next stage automatically (with a warning logged).


## Refine Mode (`--refine`)

After reviewing the generated specification, you can edit it directly and re-run the planning process with `--refine`:

1. Runs `git status --porcelain` on the task file, then `git diff HEAD` against it — capturing both staged and unstaged edits versus the last commit. An untracked task file cannot be diffed and is reported as an error.
2. Identifies the earliest modified section
3. Re-runs only stages from that point onward (top-to-bottom propagation)
4. Preserves earlier stages that are unaffected
5. Supports `//` comment markers for inline feedback

| Modified Section | Re-run From Stage |
|------------------|-------------------|
| Description / Acceptance Criteria (checklist, regular checks, rubric, test strategy, definition of done) | `business analysis` (Phase 2c) |
| Architecture Overview | `architecture synthesis` (Phase 3) |
| Implementation Process (Parallelization Overview / Phase Overview), or any sub-task file under `.specs/sub-tasks/<task-name>/` | `decomposition` (Phase 4) |

The Implementation Process section and the sub-task files are produced by the same phase, so a change to either re-runs Phase 4 as a whole.

## Usage Examples

```bash
# Refine a draft task with all stages (default)
/plan-task .specs/tasks/draft/add-validation.feature.md

# Fast refinement — minimal stages, lower quality bar
/plan-task .specs/tasks/draft/quick-fix.bug.md --fast

# One-shot — business analysis + decomposition only, no judges
/plan-task .specs/tasks/draft/simple-task.feature.md --one-shot

# Continue from a specific stage
/plan-task .specs/tasks/draft/complex-feature.feature.md --continue decomposition

# High-quality refinement with human review checkpoints
/plan-task .specs/tasks/draft/critical-api.feature.md --target-quality 4.5 --human-in-the-loop 2,3,4

# Skip research phase (you already know the tech stack)
/plan-task .specs/tasks/draft/my-task.feature.md --skip research

# Incremental refinement after editing the spec
/plan-task .specs/tasks/todo/my-task.feature.md --refine

# Never accept a phase below target quality
/plan-task .specs/tasks/draft/critical-api.feature.md --strict
```

## Artifacts Generated

```text
.claude/
└── skills/
    └── <skill-name>/
        └── SKILL.md               # Reusable skill document (if research stage ran)

.specs/
├── tasks/
│   ├── draft/                     # Source (now empty for this task)
│   └── todo/
│       └── <name>.<type>.md       # Complete task specification (ready for implementation)
├── sub-tasks/
│   └── <task-name>/               # One folder per task — NEVER moves with the task file
│       ├── 01-<step-slug>.md      # One sub-task file per implementation step
│       └── 02a-<step-slug>.md
├── analysis/
│   └── analysis-<name>.md         # Codebase impact analysis (if codebase analysis stage ran)
└── scratchpad/
    └── <hex-id>.md                # Working scratchpads (gitignored)
```

Sub-task files are **tracked in git** — they are specification artifacts, like task files.

## Best Practices

- Review the generated specification before implementing — human feedback is the most effective quality lever.
- Use `--refine` after making edits instead of re-running the full workflow.
- Add `//` comment markers to lines that need clarification — agents will incorporate your feedback.
- For complex tasks, use `--human-in-the-loop` to verify architecture decisions before decomposition.
- Use `--fast` for simple, well-defined tasks where full analysis is unnecessary.
- Use `--skip research` when working with familiar technologies.
