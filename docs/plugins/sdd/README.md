# Spec-Driven Development (SDD) Plugin

Comprehensive specification-driven development workflow that transforms vague ideas into production-ready implementations through structured planning, architecture design, and quality-gated execution.

Focused on:

- **Specification-first development** - Define what to build before how to build it
- **Multi-agent architecture** - Specialized agents for analysis, design, and implementation
- **Iterative refinement** - Continuous validation and quality gates at each stage
- **Documentation-driven** - Generate living documentation alongside implementation

## Plugin Target

- Reduce implementation rework - detailed specs catch issues before code is written
- Improve architecture decisions - structured exploration of alternatives with trade-offs
- Maintain project consistency - constitution and templates ensure uniform standards
- Enable complex feature development - break down large features into manageable, testable tasks

## Overview

The SDD plugin implements a structured software development methodology based on GitHub Spec Kit, OpenSpec, and the BMad Method. It uses specialized AI agents to guide you through the complete development lifecycle: from initial brainstorming through specification, architecture design, task breakdown, implementation, and documentation.

The workflow ensures that every feature is thoroughly specified, properly architected, and systematically implemented with quality gates at each stage. Each phase produces concrete artifacts (specification files, architecture documents, task lists) that serve as the source of truth for subsequent phases.


## Quick Start

```bash
# Install the plugin
/plugin install sdd@NeoLabHQ/context-engineering-kit

# Set up project standards (one-time)
/sdd:00-setup Use TypeScript, follow SOLID principles and Clean Architecture

# Start a new feature
/sdd:01-specify Add user authentication with OAuth2 providers

# Plan the architecture
/sdd:02-plan Use Passport.js for OAuth, prioritize security

# Create implementation tasks
/sdd:03-tasks Use TDD approach, prioritize MVP features

# Execute the implementation
/sdd:04-implement Focus on test coverage and error handling

# Document the feature
/sdd:05-document Include API examples and integration guide
```

[Usage Examples](./usage-examples.md)


## Workflow Diagram

```
┌─────────────────────────────────────────────┐
│ 1. Setup Project Standards                  │
│    /sdd:00-setup                            │
│    (create specs/constitution.md)           │
└────────────────────┬────────────────────────┘
                     │
                     │ project principles established
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Create Specification                     │ ◀─── clarify requirements ───┐
│    /sdd:01-specify                          │                              │
│    (create specs/<feature>/spec.md)         │                              │
└────────────────────┬────────────────────────┘                              │
                     │                                                       │
                     │ validated specification                               │
                     ▼                                                       │
┌─────────────────────────────────────────────┐                              │
│ 3. Plan Architecture                        │──────────────────────────────┘
│    /sdd:02-plan                             │◀─── refine architecture ─────┐
│    (create plan.md, design.md, research.md) │                              │
└────────────────────┬────────────────────────┘                              │
                     │                                                       │
                     │ approved architecture                                 │
                     ▼                                                       │
┌─────────────────────────────────────────────┐                              │
│ 4. Break Down into Tasks                    │──────────────────────────────┘
│    /sdd:03-tasks                            │
│    (create tasks.md)                        │
└────────────────────┬────────────────────────┘
                     │
                     │ executable task list
                     ▼
┌─────────────────────────────────────────────┐
│ 5. Implement Tasks                          │ ◀─── fix issues ─────────────┐
│    /sdd:04-implement                        │                              │
│    (write code, run tests)                  │                              │
└────────────────────┬────────────────────────┘                              │
                     │                                                       │
                     │ working implementation                                │
                     ▼                                                       │
┌─────────────────────────────────────────────┐                              │
│ 6. Quality Review                           │──────────────────────────────┘
│    (automatic in /sdd:04-implement)         │
└────────────────────┬────────────────────────┘
                     │
                     │ approved changes
                     ▼
┌─────────────────────────────────────────────┐
│ 7. Document Changes                         │
│    /sdd:05-document                         │
│    (update docs/ directory)                 │
└─────────────────────────────────────────────┘
```


## Commands Overview

### /sdd:00-setup - Project Constitution Setup

Create or update the project constitution that establishes development principles, coding standards, and governance rules for all subsequent development.

- Purpose - Establish project-wide development standards and principles
- Output - `specs/constitution.md` and template files for specs, plans, and tasks

```bash
/sdd:00-setup ["principle inputs or constitution parameters"]
```

#### Arguments

Optional principle inputs such as technology stack, architectural patterns, or development guidelines. Examples: "Use NestJS, follow SOLID and Clean Architecture" or "Python with FastAPI, prioritize type safety".

#### How It Works

1. **Template Initialization**: Downloads and creates the constitution template at `specs/constitution.md` along with spec, plan, and tasks templates in `specs/templates/`

2. **Value Collection**: Gathers concrete values for template placeholders from:
   - User input (conversation)
   - Existing repo context (README, docs, CLAUDE.md)
   - Prior constitution versions if present

3. **Constitution Drafting**: Fills the template with:
   - Project name and description
   - Development principles (each with name, rules, and rationale)
   - Governance section with amendment procedures and versioning policy
   - Compliance review expectations

4. **Consistency Propagation**: Ensures all dependent templates align with updated principles:
   - `specs/templates/plan-template.md` - Architecture planning template
   - `specs/templates/spec-template.md` - Feature specification template
   - `specs/templates/tasks-template.md` - Task breakdown template
   - `specs/templates/spec-checklist.md` - Specification quality checklist

5. **Sync Impact Report**: Documents version changes, modified principles, and any follow-up TODOs

#### Usage Examples

```bash
# Initialize with core principles
/sdd:00-setup Use React with TypeScript, follow atomic design patterns

# Set up for backend project
/sdd:00-setup NestJS, PostgreSQL, follow hexagonal architecture

# Minimal setup (will prompt for details)
/sdd:00-setup

# Update existing constitution with new principle
/sdd:00-setup Add principle: All APIs must be versioned
```

#### Best practices

- Be specific about tech stack - Clear technology choices improve downstream decisions
- Include architectural patterns - Patterns like Clean Architecture guide agent decisions
- Review generated templates - Ensure templates align with your team's workflow
- Version your constitution - Use semantic versioning for governance changes

---

### /sdd:01-specify - Feature Specification

Transform a natural language feature description into a detailed, validated specification with business requirements, user scenarios, and success criteria.

- Purpose - Create comprehensive feature specification from business requirements
- Output - `specs/<feature-name>/spec.md` with validated requirements

```bash
/sdd:01-specify ["feature description"]
```

#### Arguments

Natural language description of the feature to build. Examples: "Add OAuth authentication with Google and GitHub providers" or "Create a dashboard for analytics with real-time data".

#### How It Works

1. **Feature Naming**: Generates a concise short name (2-4 words) for the feature branch and spec directory

2. **Branch/Directory Management**:
   - Checks for existing branches to determine the next available feature number
   - Creates `specs/<number>-<short-name>/` directory (FEATURE_DIR)
   - Copies spec template to `FEATURE_DIR/spec.md`

3. **Business Analysis**: Launches `business-analyst` agent to:
   - Perform requirements discovery and stakeholder analysis
   - Extract key concepts: actors, actions, data, constraints
   - Write specification following the template structure
   - Mark unclear aspects with [NEEDS CLARIFICATION] (max 3)

4. **Specification Validation**: Launches second `business-analyst` agent to:
   - Fill in `spec-checklist.md` with quality criteria
   - Review spec against each checklist item
   - Document specific issues with quoted spec sections
   - Iterate until all items pass (max 3 iterations)

5. **Clarification Resolution**: If [NEEDS CLARIFICATION] markers remain:
   - Presents max 3 questions with suggested answers in table format
   - Options include A, B, C choices plus Custom input
   - Updates spec with user's chosen answers
   - Re-validates after clarifications

#### Usage Examples

```bash
# Define a new feature
/sdd:01-specify Add user authentication with social login support

# Feature with specific scope
/sdd:01-specify Create invoice generation with PDF export and email delivery

# Complex feature
/sdd:01-specify Build real-time collaborative document editing with conflict resolution

# Bug fix specification
/sdd:01-specify Fix payment timeout issues when processing large transactions
```

#### Best practices

- Focus on WHAT and WHY - Describe the problem and user needs, not implementation
- Be specific about scope - Clear boundaries prevent scope creep
- Include success criteria - Measurable outcomes help validation
- Answer clarification questions - User input improves spec quality
- Review generated spec - Verify it captures your intent before proceeding

---

### /sdd:02-plan - Architecture Planning

Design the technical architecture with multiple approaches, research unknowns, and create a comprehensive implementation plan with data models and API contracts.

- Purpose - Create detailed architecture design with trade-off analysis
- Output - `FEATURE_DIR/plan.md`, `design.md`, `research.md`, `data-model.md`, `contracts.md`

```bash
/sdd:02-plan ["plan specifics or preferences"]
```

#### Arguments

Optional architecture preferences or constraints. Examples: "Use libraries instead of direct integration" or "Prioritize simplicity over performance".

#### How It Works

1. **Context Loading**: Reads feature specification and project constitution

2. **Research & Exploration** (Stage 2):
   - Launches `researcher` agent to investigate unknown technologies and dependencies
   - Launches 2-3 `code-explorer` agents in parallel to:
     - Find similar features in the codebase
     - Map architecture and abstractions
     - Identify UI patterns and testing approaches
   - Consolidates findings in `FEATURE_DIR/research.md`

3. **Clarifying Questions** (Stage 3):
   - Reviews codebase findings and original requirements
   - Identifies underspecified aspects: edge cases, error handling, integration points
   - Presents questions and waits for user answers

4. **Architecture Design** (Stage 4):
   - Launches 2-3 `software-architect` agents with different focuses:
     - **Minimal changes**: Smallest change, maximum reuse
     - **Clean architecture**: Maintainability, elegant abstractions
     - **Pragmatic balance**: Speed + quality trade-off
   - Each produces a design document with trade-offs

5. **Final Plan** (Stage 5):
   - User selects preferred approach
   - Launches `software-architect` agent to create final design
   - Generates:
     - `FEATURE_DIR/design.md` - Final architecture document
     - `FEATURE_DIR/plan.md` - Implementation plan
     - `FEATURE_DIR/data-model.md` - Entity definitions, relationships, validation rules
     - `FEATURE_DIR/contracts.md` - API endpoints in OpenAPI/GraphQL format

6. **Plan Review** (Stage 6):
   - Reviews implementation plan for unclear areas
   - Resolves high-confidence issues automatically
   - Presents remaining uncertainties to user for clarification

#### Usage Examples

```bash
# Start architecture planning
/sdd:02-plan

# With technology preference
/sdd:02-plan Use Redis for caching, prefer PostgreSQL transactions

# With architectural constraint
/sdd:02-plan Must integrate with existing auth system, minimize changes

# Performance focus
/sdd:02-plan Optimize for high throughput, consider async processing
```

#### Best practices

- Review research findings - Understand what exists before designing
- Answer architecture questions - Your input shapes the design direction
- Compare all approaches - Each has trade-offs worth considering
- Validate data models early - Entity definitions drive implementation
- Review API contracts - Contracts become the integration specification

---

### /sdd:03-tasks - Task Generation

Generate an actionable, dependency-ordered task list organized by user stories with complexity analysis and parallel execution opportunities.

- Purpose - Break down feature into executable tasks with clear dependencies
- Output - `FEATURE_DIR/tasks.md` with phased task list

```bash
/sdd:03-tasks ["task creation guidance"]
```

#### Arguments

Optional guidance for task creation. Examples: "Use TDD approach and prioritize MVP features" or "Focus on backend first, then frontend".

#### How It Works

1. **Context Loading**: Reads from FEATURE_DIR:
   - **Required**: plan.md (tech stack, architecture), spec.md (user stories with priorities)
   - **Optional**: data-model.md, contracts.md, research.md

2. **Task Generation**: Launches `tech-lead` agent to create tasks following:

   **Implementation Strategy Selection**:
   - **Top-to-Bottom**: Workflow-first when process is clear
   - **Bottom-to-Top**: Building-blocks-first when algorithms are complex
   - **Mixed**: Combine approaches for different parts

   **Phase Structure**:
   - Phase 1: Setup (project initialization)
   - Phase 2: Foundational (blocking prerequisites)
   - Phase 3+: User Stories in priority order (P1, P2, P3...)
   - Final Phase: Polish & cross-cutting concerns

3. **Complexity Analysis**: Each task includes:
   - Clear goal and acceptance criteria
   - Technical approach and patterns to use
   - Dependencies and blocking relationships
   - **Complexity Rating**: Low/Medium/High
   - **Uncertainty Rating**: Low/Medium/High

4. **Risk Review**: After generation:
   - Lists all high-complexity or high-uncertainty tasks
   - Explains what makes each task risky
   - Asks if user wants further decomposition

#### Usage Examples

```bash
# Generate tasks with TDD focus
/sdd:03-tasks Use TDD approach, write tests before implementation

# MVP prioritization
/sdd:03-tasks Focus on P1 user stories only for initial release

# Parallel-friendly breakdown
/sdd:03-tasks Maximize parallel execution opportunities

# Sequential approach
/sdd:03-tasks Prefer sequential tasks for easier debugging
```

#### Best practices

- Review high-risk tasks - Consider decomposing complex tasks further
- Validate task dependencies - Ensure parallel tasks are truly independent
- Check user story coverage - Each story should have complete task set
- Estimate before starting - Use complexity ratings for planning
- Keep tasks small - 1-2 day tasks are ideal

---

### /sdd:04-implement - Feature Implementation

Execute the implementation plan by processing all tasks with TDD approach, quality review, and continuous progress tracking.

- Purpose - Implement all tasks following the execution plan
- Output - Working code with tests passing, updated tasks.md with completion status

```bash
/sdd:04-implement ["implementation preferences"]
```

#### Arguments

Optional implementation preferences. Examples: "Focus on test coverage and error handling" or "Prioritize performance optimization".

#### How It Works

1. **Context Loading**: Reads implementation context from FEATURE_DIR:
   - **Required**: tasks.md, plan.md
   - **Optional**: data-model.md, contracts.md, research.md

2. **Phase Execution** (Stage 8): For each phase in tasks.md:
   - Launches `developer` agent to implement the phase
   - Follows execution rules:
     - Phase-by-phase: Complete each phase before next
     - Respect dependencies: Sequential tasks in order, parallel [P] tasks together
     - TDD approach: Tests before implementation
     - File coordination: Tasks affecting same files run sequentially

3. **Progress Tracking**:
   - Reports progress after each completed phase
   - Marks completed tasks as [X] in tasks.md
   - Halts on non-parallel task failures
   - Continues parallel tasks, reports failed ones

4. **Completion Validation**: Launches `developer` agent to verify:
   - All required tasks completed
   - Implementation matches specification
   - Tests pass and coverage meets requirements
   - Implementation follows technical plan

5. **Quality Review** (Stage 9):
   - Performs `/code-review:review-local-changes` if available
   - Otherwise launches 3 `developer` agents focusing on:
     - Simplicity/DRY/elegance
     - Bugs/functional correctness
     - Project conventions/abstractions
   - Consolidates findings and recommends fixes

6. **User Decision**: Presents findings and asks:
   - Fix now
   - Fix later
   - Proceed as-is

#### Usage Examples

```bash
# Start implementation
/sdd:04-implement

# With error handling focus
/sdd:04-implement Prioritize error handling and edge cases

# Performance-focused
/sdd:04-implement Optimize for performance, use caching where appropriate

# Test coverage priority
/sdd:04-implement Achieve 90%+ test coverage
```

#### Best practices

- Address review findings - Quality issues compound over time
- Monitor test failures - Fix tests before proceeding
- Review progress regularly - Check tasks.md for completion status
- Commit frequently - Save progress after each phase

---

### /sdd:05-document - Feature Documentation

Document the completed feature implementation with API guides, architecture updates, usage examples, and lessons learned.

- Purpose - Create comprehensive documentation for implemented feature
- Output - Updated documentation in `docs/` folder

```bash
/sdd:05-document ["documentation focus areas"]
```

#### Arguments

Optional focus areas for documentation. Examples: "Include API examples and integration guide" or "Focus on troubleshooting common issues".

#### How It Works

1. **Context Loading**: Reads from FEATURE_DIR:
   - **Required**: tasks.md (verify completion)
   - **Optional**: plan.md, spec.md, contracts.md, data-model.md

2. **Implementation Verification** (Stage 10):
   - Reviews tasks.md to confirm all tasks marked [X]
   - Identifies incomplete or partially implemented tasks
   - Reviews codebase for missing functionality
   - **Presents issues to user**: Fix now or later?

3. **Documentation Update**: Launches `tech-writer` agent following workflow:
   - Reads all FEATURE_DIR artifacts
   - Reviews files modified during implementation
   - Identifies documentation gaps in `docs/`

4. **Documentation Generation**:
   - API guides and usage examples
   - Architecture updates reflecting implementation
   - README.md updates in affected folders
   - Development specifics for LLM navigation
   - Troubleshooting guidance for common issues

5. **Output Summary**:
   - Files updated
   - Major documentation changes
   - New best practices documented
   - Project status after this phase

#### Usage Examples

```bash
# Generate documentation
/sdd:05-document

# API-focused documentation
/sdd:05-document Focus on API documentation with curl examples

# Integration guide
/sdd:05-document Include step-by-step integration guide

# Troubleshooting emphasis
/sdd:05-document Document common errors and solutions
```

#### Best practices

- Complete implementation first - Document working code, not plans
- Include working examples - Test all code samples
- Update architecture docs - Reflect actual implementation
- Document gotchas - Share lessons learned during implementation
- Cross-reference specs - Link to original requirements

---

### /sdd:create-ideas - Idea Generation

Generate ideas in one shot using creative sampling. Based on [Verbalized Sampling](https://arxiv.org/abs/2510.01171) - a training-free prompting strategy to mitigate mode collapse in LLMs by requesting responses with probabilities. Achieves 2-3x diversity improvement while maintaining quality.

Different from `/sdd:brainstorm`, by much simpler and faster approach, but focused on generating ideas in one shot, don't include refinement, focuses on creativity. Can be used for any other purpose that include creative thinking.

- Purpose - Generate responses which require high diversity and creativity, like brainstorming or creative writing
- Output - List of ideas with text and probability scores

```bash
/sdd:create-ideas [topic or problem] [optional: number of ideas]
```

#### Arguments

Topic or problem to generate ideas for. Optionally specify the number of ideas to generate (defaults to 5).

#### How It Works

1. **Creative Sampling**: Uses verbalized probability sampling to generate diverse responses
   - Requests responses from the full distribution or distribution tails
   - Each response includes a probability score (< 0.10 for tail sampling)
   - Reduces mode collapse common in standard LLM generation

2. **Output Format**: Returns a list where each item contains:
   - Text: The generated idea or response
   - Probability: Numeric score indicating sampling position

#### Usage Examples

```bash
# Generate creative ideas for a feature
/sdd:create-ideas ways to improve user onboarding

# Brainstorm solutions to a problem
/sdd:create-ideas reduce API response times

# Creative writing prompts
/sdd:create-ideas write jokes about cats

# Generate more ideas
/sdd:create-ideas 10 marketing slogans for a fitness app

# Technical alternatives
/sdd:create-ideas caching strategies for real-time data
```

#### When to Use

- **Use `/sdd:create-ideas`** when you need quick, diverse ideas without refinement
- **Use `/sdd:brainstorm`** when you need thorough exploration with validation and documentation

#### Best practices

- Be specific about the domain - "API error handling patterns" vs just "error handling"
- Use for divergent thinking - Generate many options before converging on solutions
- Review probability scores - Lower probabilities indicate more creative/unusual ideas
- Combine with brainstorm - Use create-ideas for initial ideation, then brainstorm to refine

---

### /sdd:brainstorm - Idea Refinement

Transform rough ideas into fully-formed designs through collaborative dialogue, incremental validation, and design documentation.

- Purpose - Refine vague ideas into actionable designs
- Output - Design document in `docs/plans/YYYY-MM-DD-<topic>-design.md`

```bash
/sdd:brainstorm initial feature concept
```

#### Arguments

Optional initial concept to explore. Can be vague: "something to help with user onboarding" or more specific: "real-time notification system".

#### How It Works

1. **Context Understanding**:
   - Reviews current project state (files, docs, recent commits)
   - Asks questions one at a time to refine the idea
   - Prefers multiple choice questions when possible
   - Focuses on: purpose, constraints, success criteria

2. **Approach Exploration**:
   - Proposes 2-3 different approaches with trade-offs
   - Leads with recommended option and reasoning
   - Presents options conversationally

3. **Design Presentation**:
   - Breaks design into 200-300 word sections
   - Asks after each section if it looks right
   - Covers: architecture, components, data flow, error handling, testing
   - Ready to clarify if something doesn't make sense

4. **Documentation**:
   - Writes validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
   - Commits the design document to git

5. **Implementation Handoff** (optional):
   - Asks if ready to set up for implementation
   - Can create isolated workspace with git worktrees
   - Can create detailed implementation plan

#### Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each

#### Usage Examples

```bash
# Start with vague idea
/sdd:brainstorm Something to improve user onboarding

# More specific concept
/sdd:brainstorm Real-time collaboration features for document editing

# Technical exploration
/sdd:brainstorm Caching strategy for our product catalog API

# Process improvement
/sdd:brainstorm Automated deployment pipeline for our microservices
```

#### Best practices

- Start with the problem - Describe what you're trying to solve
- Be open to alternatives - The first idea isn't always best
- Engage with questions - Your answers shape the design
- Validate incrementally - Catch issues early in design sections
- Save the design - Use as input for `/sdd:01-specify`

---

## Available Agents

The SDD plugin uses specialized agents for different phases of development:

| Agent | Description | Used By |
|-------|-------------|---------|
| `business-analyst` | Requirements discovery, stakeholder analysis, specification writing | `/sdd:01-specify` |
| `researcher` | Technology research, dependency analysis, best practices | `/sdd:02-plan` |
| `code-explorer` | Codebase analysis, pattern identification, architecture mapping | `/sdd:02-plan` |
| `software-architect` | Architecture design, component design, implementation planning | `/sdd:02-plan` |
| `tech-lead` | Task decomposition, dependency mapping, sprint planning | `/sdd:03-tasks` |
| `developer` | Code implementation, TDD execution, quality review | `/sdd:04-implement` |
| `tech-writer` | Documentation creation, API guides, architecture docs | `/sdd:05-document` |

## Foundation

The SDD plugin is based on established software engineering methodologies and research:

### Core Methodologies

- **[GitHub Spec Kit](https://github.com/github/spec-kit)** - Specification-driven development templates and workflows
- **OpenSpec** - Open specification format for software requirements
- **BMad Method** - Structured approach to breaking down complex features

### Supporting Research

- **[Specification-Driven Development](https://en.wikipedia.org/wiki/Design_by_contract)** - Design by contract and formal specification approaches
- **[Agile Requirements Engineering](https://www.agilealliance.org/agile101/)** - User stories, acceptance criteria, and iterative refinement
- **[Test-Driven Development](https://www.agilealliance.org/glossary/tdd/)** - Writing tests before implementation
- **[Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)** - Separation of concerns and dependency inversion
- **[Vertical Slice Architecture](https://jimmybogard.com/vertical-slice-architecture/)** - Feature-based organization for incremental delivery
- **[Verbalized Sampling](https://arxiv.org/abs/2510.01171)** - Training-free prompting strategy for diverse idea generation. Achieves **2-3x diversity improvement** while maintaining quality. Used for `create-ideas`, `brainstorm` and `plan` commands

