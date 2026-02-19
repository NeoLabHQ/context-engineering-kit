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
/plan 
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
| | (sonnet)       |  | code-explorer    |  | business-   ||
| |      |         |  | (sonnet)         |  | analyst     ||
| |      v         |  |       |          |  | (opus)      ||
| |  Judge 2a      |  |   Judge 2b       |  |      |      ||
| +------+---------+  +--------+---------+  +------+------+|
|        |                     |                    |       |
+----------------------------------------------------------+
         |                     |                    |
         +----------+----------+--------------------+
                    |
                    v
         +-----------------------------+
         | Phase 3: Architecture       |
         | software-architect (opus)   |
         |            |                |
         |            v                |
         |        Judge 3              |
         +--------------+--------------+
                        |
                        v
         +-----------------------------+
         | Phase 4: Decomposition      |
         | tech-lead (opus)            |
         |            |                |
         |            v                |
         |        Judge 4              |
         +--------------+--------------+
                        |
                        v
         +-----------------------------+
         | Phase 5: Parallelize        |
         | team-lead (opus)            |
         |            |                |
         |            v                |
         |        Judge 5              |
         +--------------+--------------+
                        |
                        v
         +-----------------------------+
         | Phase 6: Verifications      |
         | qa-engineer (opus)          |
         |            |                |
         |            v                |
         |        Judge 6              |
         +--------------+--------------+
                        |
      +-----------------+-----------------+
      |                 |                 |
      v                 v                 v
+--------------+ +--------------+ +---------------+
| Refined Task | | Skill File   | | Analysis File |
| todo/*.md    | | SKILL.md     | | analysis-*.md |
+--------------+ +--------------+ +---------------+
```

It will output the updated task file to `.specs/tasks/todo/design-implement-authentication-middleware-with-jwt-support.feature.md` and create new skills if needed. It also produces scratchpads and verification reports along the way to properly evaluate each step of the process. You can safely ignore all of them.

At this point you can verify and adjust the specification, then run the `/plan --refine` command again for agents to update the rest of the specification where it doesn't align with your changes. It uses a top-to-bottom approach, meaning all sections below your changes will be rethought and updated accordingly. See the [Refining Specifications and Code](../plugins/sdd/refine.md) guide for details.

### Code Generation

Once you are happy with the specification, run `/clear` (or re-open Claude Code) to clear context. Then you can start the implementation process:

```bash
/implement
```

It will perform the following actions:

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

It will automatically write tests, verify them, build the solution, and confirm it works as expected.

Once implementation is complete, you can review and adjust it, then run `/implement --refine` again for the agent to update the rest of the implementation if it doesn't align with your changes or feedback.

### Commit and Push

Once complete, you can use the [git](../plugins/git) plugin to commit changes and create a pull request.

```bash
/git:commit
/git:create-pr
```
