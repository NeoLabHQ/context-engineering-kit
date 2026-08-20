# /create-workflow-command - Workflow Command Builder

Create commands that orchestrate multi-step workflows by dispatching sub-agents with task-specific instructions stored in separate files. Solves the **context bloat problem** by keeping orchestrator commands lean.

- Purpose - Build workflow commands that dispatch sub-agents with file-based task prompts
- Output - Complete workflow structure: orchestrator command, task files, and optional custom agents

```bash
/create-workflow-command [workflow-name] [description]
```

## Arguments

Optional workflow name (kebab-case) and description of what the workflow accomplishes.

## Usage Examples

```bash
# Create a feature implementation workflow
> /create-workflow-command feature-implementation "Research, plan, and implement features"

# Create a code review workflow
> /create-workflow-command code-review "Multi-phase code analysis and feedback"

# Start interactive workflow creation
> /create-workflow-command
```

## How It Works

1. **Gather Requirements**: Collects workflow details
   - Workflow name and description
   - List of discrete steps with goals and tools
   - Execution mode (sequential or parallel)
   - Agent type preferences

2. **Create Directory Structure**: Sets up the workflow layout

```
plugins/<plugin-name>/
├── commands/
│   └── <workflow>.md          # Lean orchestrator (~50-100 tokens per step)
├── agents/                     # Optional: reusable executor agents
│   └── step-executor.md       # Custom agent with specific tools/behavior
└── tasks/                      # All task instructions directly here
    ├── step-1-<name>.md       # Full instructions (~500+ tokens each)
    ├── step-2-<name>.md
    ├── step-3-<name>.md
    └── common-context.md      # Shared context across workflows
```

1. **Create Task Files**: Generates self-contained task instructions
   - Context and goal for each step
   - Input/output specifications
   - Constraints and success criteria

2. **Create Orchestrator Command**: Builds lean dispatch logic
   - Uses `${CLAUDE_PLUGIN_ROOT}/tasks/` paths for portability
   - Passes minimal context between steps (summaries, not full data)
   - Supports sequential, parallel, and stateful (resume) patterns

## Execution Patterns

| Pattern | Use Case | Description |
|---------|----------|-------------|
| **Sequential** | Dependent steps | Each step uses previous step's output |
| **Parallel** | Independent analysis | Multiple agents run simultaneously |
| **Stateful (Resume)** | Shared context | Continue same agent across steps |
