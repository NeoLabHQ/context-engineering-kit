# Brainstorming to Implementation

Collaborative workflow for transforming vague ideas into well-defined features through structured dialogue before specification.

For well-defined requirements, skip brainstorming and use [Spec-Driven Development](./spec-driven-development.md) directly.

## When to Use

- Unclear or incomplete requirements that need refinement
- Exploring multiple approaches before committing to a direction
- New features where you know the goal but not the implementation
- Stakeholder alignment needed before detailed planning

## Plugins needed for this workflow

- [SDD](../plugins/sdd/README.md)
- [Review](../plugins/review/README.md)
- [Git](../plugins/git/README.md)

## Workflow

### How It Works

```md
┌─────────────────────────────────────────────┐
│ 1. Brainstorm the Idea                      │
│    (collaborative Q&A refinement)           │
└────────────────────┬────────────────────────┘
                     │
                     │ LLM asks questions one at a time
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Explore Approaches                       │ ◀─── refine understanding ────┐
│    (evaluate 2-3 options with trade-offs)   │                               │
└────────────────────┬────────────────────────┘                               │
                     │                                                        │
                     │ select preferred approach                              │
                     ▼                                                        │
┌─────────────────────────────────────────────┐                               │
│ 3. Present Design                           │───────────────────────────────┘
│    (incremental validation in sections)     │
└────────────────────┬────────────────────────┘
                     │
                     │ validated design saved to docs/plans/
                     ▼
┌─────────────────────────────────────────────┐
│ 4. Create Task & Plan Specification         │
│    (formal spec from design)                │
└────────────────────┬────────────────────────┘
                     │
                     │ continue with SDD workflow
                     ▼
┌─────────────────────────────────────────────┐
│ 5-6. Implement, Review                      │
│    (standard SDD phases)                    │
└─────────────────────────────────────────────┘
```

### 1. Brainstorm the idea

Use the `/brainstorm` command to start a collaborative dialogue. The LLM will explore your project context and ask clarifying questions one at a time.

```bash
/brainstorm Users want better search but requirements are unclear
```

After starting, the LLM will:

- Review your project structure, docs, and recent commits
- Ask focused questions (preferring multiple choice when possible)
- Help you define purpose, constraints, and success criteria

Answer each question to progressively refine the idea. The conversation continues until requirements are clear.

### 2. Explore approaches

Once the LLM understands your needs, it will propose 2-3 different approaches with trade-offs.

```md
The LLM will present options like:

**Option A: Elasticsearch Integration** (Recommended)
- Full-text search with faceting
- Trade-off: Additional infrastructure

**Option B: PostgreSQL Full-Text Search**
- No new dependencies
- Trade-off: Limited faceting capabilities

**Option C: Algolia Service**
- Fastest implementation
- Trade-off: External dependency and cost
```

After reviewing options, select your preferred approach or ask for more exploration. The LLM leads with its recommendation and explains the reasoning.

### 3. Present design

The LLM presents the validated approach as a design document in 200-300 word sections, checking after each section whether it looks right.

```md
The LLM will cover:
- Architecture overview
- Component breakdown
- Data flow
- Error handling
- Testing approach
```

After each section, confirm it matches your expectations or request changes. Once complete, the design is saved to `docs/plans/YYYY-MM-DD-<topic>-design.md`.

### 4. Create task and plan specification

Use the `/add-task` command to create a task file from the refined design, then `/plan-task` to generate a detailed specification with architecture, implementation steps, and verification criteria.

```bash
/add-task "Implement faceted search with Elasticsearch, filters, and autocomplete"
```

After LLM completes, review the task file in `.specs/tasks/draft/`. You can adjust the task file to incorporate additional details from the brainstorming session.

Then run planning to generate the full specification:

```bash
/plan-task
```

After LLM completes, review the refined specification in `.specs/tasks/todo/`. The plan includes architecture design, implementation steps with parallelization, and verification rubrics. You can adjust and run `/plan-task --refine` to iterate.

### 5. Implement features

Use the `/implement-task` command to execute the implementation. This produces working code with tests and verification.

```bash
/implement-task
```

During implementation, the LLM executes each step with quality gates, writes tests, and verifies the solution works as expected. More info in [Spec-Driven Development](./spec-driven-development.md) workflow.

### 6. Review and ship

Complete the workflow with code review and pull request creation.

```bash
/review-local-changes
/commit
/create-pr
```

After completion, your feature is ready for merge.

## Key Principles

The brainstorming phase follows these principles to ensure productive refinement:

- **One question at a time** - Focused dialogue prevents overwhelm
- **Multiple choice preferred** - Easier to answer than open-ended questions
- **YAGNI ruthlessly** - Remove unnecessary features from designs
- **Explore alternatives** - Always consider 2-3 approaches before committing
- **Incremental validation** - Present design in sections, validate each one
