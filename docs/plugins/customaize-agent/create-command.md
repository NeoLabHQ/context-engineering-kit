# /create-command - Command Creation Assistant

Interactive assistant for creating new Claude commands with proper structure, patterns, and MCP tool integration.

- Purpose - Guide through creating well-structured commands
- Output - Complete command file with frontmatter, sections, and patterns

```bash
/create-command ["command name or description"]
```

## Arguments

Optional command name or description of the command's purpose (e.g., "validate API documentation", "deploy to staging").

## Usage Examples

```bash
# Create an API validation command
> /create-command validate API documentation

# Create a deployment command
> /create-command deploy feature to staging

# Start without a specific idea
> /create-command
```

## How It Works

1. **Pattern Research**: Examines existing commands in the target category
   - Lists commands in project (`.claude/commands/`) or user (`~/.claude/commands/`) directories
   - Reads similar commands to identify patterns
   - Notes MCP tool usage, documentation references, and structure

2. **Interactive Interview**: Understands requirements through targeted questions
   - What problem does this command solve?
   - Who will use it and when?
   - Is it interactive or batch?
   - What's the expected output?

3. **Category Classification**: Determines the command type
   - Planning (feature ideation, proposals, PRDs)
   - Implementation (technical execution with modes)
   - Analysis (review, audit, reports)
   - Workflow (orchestrate multiple steps)
   - Utility (simple tools and helpers)

4. **Location Decision**: Chooses where the command should live
   - Project command (specific to codebase)
   - User command (available across all projects)

5. **Generation**: Creates the command following established patterns
   - Proper YAML frontmatter (description, argument-hint)
   - Task and context sections
   - MCP tool usage patterns
   - Human review sections
   - Documentation references

## Best Practices

- Research first - Let the assistant examine existing commands before creating new ones
- Be specific about purpose - Clearly describe what problem the command solves
- Choose location carefully - Project commands for codebase-specific workflows, user commands for general utilities
- Include MCP tools - Use MCP tool patterns instead of CLI commands where applicable
- Add human review sections - Flag decisions that need verification
