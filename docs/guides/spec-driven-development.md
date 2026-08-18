# Reliable Engineering through Spec-Driven Development (SDD)

Structured workflow for features and bugs requiring planning, specifications, and architecture decisions before implementation. Mainly based on the [SDD](../plugins/sdd/README.md) plugin.

For simple features, use [Feature Development with Quality Gates](./feature-development.md) workflow.

## When to Use

- Features requiring complex development
- Significant architectural changes or integrations

## Required Plugins

- [SDD](../plugins/sdd/README.md)
- [Git](../plugins/git/README.md)

## Workflow

### Specification Creation

Optional, but highly recommended to switch the model to `sonnet[1m]` to keep it focused for a longer time.

Important: this does not mean that Sonnet will be used for the work itself. By default, `sonnet` is used as the orchestrator to launch `opus` agents that perform the actual work.

```bash
/model sonnet[1m]
```

Create a task file with the initial prompt:

```bash
/add-task "Design and implement authentication middleware with JWT support"
# Output:
# Created task file: .specs/tasks/draft/design-implement-authentication-middleware-with-jwt-support.feature.md
# Title: Design and implement authentication middleware with JWT support
# Type: feature
# Depends on: None
```

You can adjust the task file to incorporate additional details and criteria at this point, but it is not required.

Run the planning process:

```bash
/plan-task .specs/tasks/draft/design-implement-authentication-middleware-with-jwt-support.feature.md
```

It will perform the following refinement process to update the task file with a more detailed specification:

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

It will output the updated task file to `.specs/tasks/todo/design-implement-authentication-middleware-with-jwt-support.feature.md`, write one sub-task file per implementation step under `.specs/sub-tasks/design-implement-authentication-middleware-with-jwt-support.feature/`, and create new skills if needed. It also produces scratchpads and judge reports along the way to properly evaluate each phase of the process. You can safely ignore all of them.

The task file ends up with four sections: `# Description` and `## Acceptance Criteria` (Phase 2c), `## Architecture Overview` (Phase 3) and `## Implementation Process` (Phase 4). The last one groups the steps into **phases** — milestones that each leave a working, independently verifiable state — and names a reviewer model for each. The sub-task folder is created at planning time and never moves, so its recorded paths stay valid for the whole task lifecycle.

At this point you can verify and adjust the specification, then run the `/plan-task --refine` command again for agents to update the rest of the specification where it doesn't align with your changes. It uses a top-to-bottom approach, meaning all sections below your changes will be rethought and updated accordingly. See the [Refining Specifications and Code](../plugins/sdd/refine.md) guide for details.

### Code Generation

Once you are happy with the specification, run `/clear` (or re-open Claude Code) to clear context. Then you can start the implementation process:

```bash
/implement-task
```

It will perform the following actions:

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

Code review happens once per **implementation phase**, not once per step — a phase is a milestone that leaves a working, independently verifiable state, so the reviewer sees a coherent slice of work rather than an isolated edit. It scores only the acceptance criteria that phase lists as due; criteria belonging to later phases are not yet expected.

It will automatically write tests, verify them, build the solution, and confirm it works as expected.

Once implementation is complete, you can review and adjust it, then run `/implement-task --refine` again for the agent to update the rest of the implementation if it doesn't align with your changes or feedback.

### Commit and Push

Once complete, you can use the [git](../plugins/git) plugin to commit changes and create a pull request.

```bash
/git:commit
/git:create-pr
```
