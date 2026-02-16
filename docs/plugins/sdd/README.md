# Spec-Driven Development (SDD) Plugin: Continuous Learning + LLM-as-Judge + Agent Swarm

Comprehensive specification-driven development workflow plugin that transforms prompts into production-ready implementations through structured planning, architecture design, and quality-gated execution.

This plugin is designed to consistently and reproducibly produce working code. It was tested on real-life production projects by our team, and in 100% of cases it generated working code aligned with the initial prompt. If you find a use case it cannot handle, please report it as an issue.

## Key Features

- **Development as compilation** — The plugin functions like a "compilation" or "nightly build" for your development process: `task specs → run /sdd:implement → working code`. After writing your prompt, you can launch the plugin and expect a functional result when you return. The completion time depends on task complexity — simple tasks may finish within 30 minutes, while complex ones can take several days.
- **Benchmark-level quality in real life** — Model benchmarks improve with each release, yet real-world results often stagnate. This is because benchmarks reflect the best possible output a model can achieve, whereas in practice LLMs tend to drift toward sub-optimal, non-functional solutions. This plugin uses a variety of patterns to keep the model operating at peak performance.
- **Customizable** — Balance result quality and process speed by adjusting command parameters. Learn more in the [Customization](customization.md) section.
- **Developer time-efficiency** — The overall process is designed to minimize developer time and reduce the number of interactions, while still producing results superior to what a model can generate from scratch. However, overall quality is proportional to the time invested in iterating on and refining the specification.
- **Industry-standard** — The plugin's specification template is based on the arc42 standard, adjusted for LLM capabilities. Arc42 is a widely adopted, high-quality standard for software development documentation used by many organizations.
- **Works best in complex or large codebases** — While most other frameworks work best for new projects and greenfield development, this plugin is designed to perform better as your codebase grows and your architecture becomes more structured. Each planning phase includes a **codebase impact analysis** step that evaluates which files may be affected and which patterns to follow to achieve the desired result.
- **Simple** — This plugin avoids unnecessary complexity by primarily using only three commands, offloading process complexity to the model via multi-agent orchestration. `/sdd:implement` is a single command that produces functional code from a task specification. To create that specification, you run `/sdd:add-task` and `/sdd:plan`, which analyze your prompt and iteratively refine the specification until it meets the required quality standards.

## Quick Start

```bash
/plugin marketplace add NeoLabHQ/context-engineering-kit
```

Enable the `sdd` plugin in the installed plugins list:

```bash
/plugin
# Installed -> sdd -> Space to enable
```

Then run the following commands:

```bash
# Create the .specs/tasks/draft/design-auth-middleware.feature.md file with the initial prompt
/sdd:add-task "Design and implement authentication middleware with JWT support"

# Write a detailed specification for the task
/sdd:plan
# Moves the task to the .specs/tasks/todo/ folder
```

Restart the Claude Code session to clear context and start fresh. Then run the following command:

```bash
# Implement the task
/sdd:implement @.specs/tasks/todo/design-auth-middleware.feature.md
# Produces a working implementation and moves the task to the .specs/tasks/done/ folder
```

- [Detailed guide](../../guides/spec-driven-development.md)
- [Usage Examples](usage-examples.md)

## Overall Flow

End-to-end task implementation process from initial prompt to pull request, including commands from the [git](../git/README.md) plugin:

- `/sdd:add-task` → Creates a `.specs/tasks/draft/<task-name>.<type>.md` file with the initial task description.
- `/sdd:plan` → Generates a `.claude/skills/<skill-name>/SKILL.md` file with the skills needed to implement the task (by analyzing the library and framework documentation used in the codebase), then updates the task file with a refined specification and moves it to `.specs/tasks/todo/`.
- `/sdd:implement` → Produces a working implementation, verifies it, then moves the task to `.specs/tasks/done/`.
- `/git:commit` → Commits changes.
- `/git:create-pr` → Creates a pull request.

```
  1. Create        2. Plan         3. Implement           4. Ship
+-------------+  +-----------+  +---------------+  +-----------------+
|/sdd:add-task|  | /sdd:plan |  |/sdd:implement |  |  /git:commit    |
+------+------+  +-----+-----+  +------+--------+  |       |         |
       |                |               |           |       v         |
       v                v               v           |/git:create-pr   |
                                                    +-------+---------+
                                                            |
                     Task Lifecycle                         |
 +----------+   +----------+   +--------------+   +---------+
 | draft/   +-->| todo/    +-->| in-progress/ +-->| done/   |
 |   *.md   |   |   *.md   |   |     *.md     |   |  *.md   |
 +----------+   +----------+   +--------------+   +---------+
```

## Commands

Core workflow commands:

- [/sdd:add-task](add-task.md) - Create task template file with initial prompt
- [/sdd:plan](plan.md) - Analyze prompt, generate required skills and refine task specification
- [/sdd:implement](implement.md) - Produce working implementation of the task and verify it

Additional commands useful before creating a task:

- [/sdd:create-ideas](create-ideas.md) - Generate diverse ideas on a given topic using creative sampling techniques
- [/sdd:brainstorm](brainstorm.md) - Refine vague ideas into fully-formed designs through collaborative dialogue

## Available Agents

The SDD plugin uses specialized agents for different phases of development:

| Agent | Description | Used By |
|-------|-------------|---------|
| `researcher` | Technology research, dependency analysis, best practices | `/sdd:plan` (Phase 2a) |
| `code-explorer` | Codebase analysis, pattern identification, architecture mapping | `/sdd:plan` (Phase 2b) |
| `business-analyst` | Requirements discovery, stakeholder analysis, specification writing | `/sdd:plan` (Phase 2c) |
| `software-architect` | Architecture design, component design, implementation planning | `/sdd:plan` (Phase 3) |
| `tech-lead` | Task decomposition, dependency mapping, risk analysis | `/sdd:plan` (Phase 4) |
| `team-lead` | Step parallelization, agent assignment, execution planning | `/sdd:plan` (Phase 5) |
| `qa-engineer` | Verification rubrics, quality gates, LLM-as-Judge definitions | `/sdd:plan` (Phase 6) |
| `developer` | Code implementation, TDD execution, quality review, verification | `/sdd:implement` |
| `tech-writer` | Technical documentation, API guides, architecture updates, and lessons learned | `/sdd:implement` |

## Patterns

Key patterns implemented in this plugin:

- **Structured reasoning templates** — Includes Zero-shot and Few-shot Chain of Thought, Tree of Thoughts, Problem Decomposition, and Self-Critique. Each is tailored to a specific agent and task, enabling sufficiently detailed decomposition so that isolated sub-agents can implement each step independently.
- **Multi-agent orchestration for context management** — Context isolation of independent agents prevents "context rot," maintaining optimal LLM performance at each step. The main agent acts as an orchestrator that launches sub-agents and manages their workflow.
- **Quality gates based on LLM-as-Judge** — Evaluates the quality of each planning and implementation step using evidence-based scoring and predefined verification rubrics. This eliminates cases where an agent produces non-functional or incorrect solutions.
- **Continuous learning** — Automatically builds specific skills the agent needs to implement a task, which it might otherwise be unable to perform from scratch.
- **Spec-driven development pattern** — Based on the arc42 specification standard adjusted for LLM capabilities, this pattern eliminates elements of the specification that do not add value to implementation quality.
- **MAKER** — An agent reliability pattern introduced in [Solving a Million-Step LLM Task with Zero Errors](https://arxiv.org/abs/2511.09030). It minimizes agent mistakes caused by context accumulation and hallucinations by utilizing clean-state agent launches, filesystem-based memory storage, and multi-agent voting during critical decisions.

## Vibe Coding vs. Specification-Driven Development

This plugin is not a "vibe coding" solution, though it can function like one out of the box. By default, it is designed to work from a single prompt through to task completion, making reasonable assumptions and evidence-based decisions instead of constantly asking for clarification. This is because developer time is more valuable than model time, allowing the developer to decide how much time is worth spending on a task. The plugin will always produce functional results, but quality may be sub-optimal without human feedback.

To improve quality, you can correct the generated specification or leave comments using `//`, then run the `/sdd:plan` command again with the `--refine` flag. You can also verify each planning and implementation phase by adding the `--human-in-the-loop` flag. Majority of researches show that human feedback is the most effective way to improve results.

Our tests showed that even when the initially generated specification was incorrect due to missing information or task complexity, the agent was still able to self-correct until it reached a working solution. However, this process often took longer, as the agent explored incorrect paths and stopped more frequently. To avoid this, we strongly recommend decomposing complex tasks into smaller, separate tasks with dependencies and reviewing the specification for each one. You can add dependencies between tasks as arguments to the `/sdd:add-task` command, and the model will link them by adding a `depends_on` section to the task file's frontmatter.

Even if you prefer a less hands-on approach, you can still use the plugin for complex tasks without decomposition or human verification — though you may need tools to keep the session active for longer periods, for example ralph-loop.

Learn more about available customization options in [Customization](customization.md).

## Theoretical Foundation

The SDD plugin is based on established software engineering methodologies and research:

### Core Methodologies

- [GitHub Spec Kit](https://github.com/github/spec-kit) - Specification-driven development templates and workflows
- [OpenSpec](https://github.com/Fission-AI/OpenSpec) - Open specification format for software requirements
- [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) - Structured approach to breaking down complex features

### Supporting Research

- [Specification-Driven Development](https://en.wikipedia.org/wiki/Design_by_contract) - Design by contract and formal specification approaches
- [Agile Requirements Engineering](https://www.agilealliance.org/agile101/) - User stories, acceptance criteria, and iterative refinement
- [Test-Driven Development](https://www.agilealliance.org/glossary/tdd/) - Writing tests before implementation
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Separation of concerns and dependency inversion
- [Vertical Slice Architecture](https://jimmybogard.com/vertical-slice-architecture/) - Feature-based organization for incremental delivery
- [Verbalized Sampling](https://arxiv.org/abs/2510.01171) - A training-free prompting strategy for diverse idea generation. It achieves a **2-3x diversity improvement** while maintaining quality. Used for the `create-ideas`, `brainstorm`, and `plan` commands.
- [Solving a Million-Step LLM Task with Zero Errors](https://arxiv.org/abs/2511.09030) - Reliability pattern for LLM-based agents that enables solving complex tasks with zero errors.
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - Evaluation patterns for grading LLM output.
- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Leveraging multiple perspectives for higher accuracy.
- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) - Reducing hallucinations through verification steps.
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) - Structured exploration of complex solution spaces.
- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Defining core principles for agent behavior.
- [Chain of Thought Prompting](https://arxiv.org/abs/2201.11903) - Enabling step-by-step reasoning.
