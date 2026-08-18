# Agents Reference

Complete alphabetical index of all specialized agents available across Context Engineering Kit plugins.

## Agents by Plugin

### Code Review

Specialized agents for comprehensive code quality analysis. [More info](../plugins/review/README.md).

- `bug-hunter` - Identifies potential bugs, edge cases, and error-prone patterns.
- `code-quality-reviewer` - Evaluates code structure, readability, and maintainability.
- `contracts-reviewer` - Reviews interfaces, API contracts, and data models.
- `historical-context-reviewer` - Analyzes changes in relation to codebase history and patterns.
- `security-auditor` - Identifies security vulnerabilities and potential attack vectors.
- `test-coverage-reviewer` - Evaluates test coverage and suggests missing test cases.
- `change-story-agent` - Builds the change "story" (intent, architecture, design decisions, risks, solutions) plus key facts for triage review.
- `change-impact-agent` - Rates changed files by blast radius, impact, exposure, and uncertainty.
- `change-failure-agent` - Rates changed files by failure severity and detectability.
- `change-expectation-agent` - Flags files sensitive to misunderstood requirements or side effects and lists declarative files.

### Spec-Driven Development (SDD)

Specialized agents for effective context management and quality review throughout the SDD workflow. [More info](../plugins/sdd/README.md).

- `business-analyst` - Requirements discovery, scope and user scenarios, and the task's whole `## Acceptance Criteria` section: checklist (Hard Rules + TICK), regular checks, rubric with score definitions, test strategy and definition of done, mixing business and technical criteria.
- `code-explorer` - Codebase analysis, pattern identification, architecture mapping.
- `code-reviewer` - Reviews a whole implementation **phase**: receives the task file path, the phase identifier and the artifact paths, resolves the phase's sub-task files itself, and scores only the checklist items and rubric criteria that phase lists as due, alongside code quality (duplication, naming, architecture, control flow, error handling, size limits, Muda waste, test coverage).
- `developer` - Implements exactly one step, receiving the task file path and that step's sub-task file path.
- `researcher` - Technology research, dependency analysis, best practices; creates a reusable skill file that all agents can leverage.
- `software-architect` - Architecture design, component design, solution strategy and expected changes.
- `tech-lead` - Decomposition into per-step sub-task files, dependency mapping, parallelization, risk analysis, and grouping steps into independently verifiable phases each with its own reviewer model.
- `tech-writer` - Technical documentation, API guides, usage examples, and architecture updates.

