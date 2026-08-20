# /create-agent - Agent Creation Guide

Comprehensive guide for creating Claude Code agents with proper structure, triggering conditions, system prompts, and validation. Combines official Anthropic best practices with proven patterns.

- Purpose - Create autonomous agents that handle complex, multi-step tasks independently
- Output - Complete agent file with frontmatter, triggering examples, and system prompt

```bash
/create-agent [agent-name] [optional description]
```

## Arguments

Optional agent name (kebab-case) and description of the agent's purpose.

## Usage Examples

```bash
# Create a code review agent
> /create-agent code-reviewer "Review code for quality and security"

# Create a test generation agent
> /create-agent test-generator

# Start interactive agent creation
> /create-agent
```

## How It Works

1. **Gather Requirements**: Collects agent specifications
   - Agent name (kebab-case, 3-50 characters)
   - Purpose and core responsibilities
   - Triggering conditions (when Claude should use this agent)
   - Required tools (principle of least privilege)
   - Model requirements (inherit/sonnet/opus/haiku)

2. **Design Triggering**: Creates proper description field
   - Starts with "Use this agent when..."
   - Includes 2-4 `<example>` blocks with:
     - Context (situation description)
     - User request (exact message)
     - Assistant response (how Claude triggers)
     - Commentary (reasoning for triggering)

3. **Write System Prompt**: Generates comprehensive prompt
   - Role statement with specialization
   - Core responsibilities (numbered list)
   - Analysis/work process (step-by-step)
   - Quality standards (measurable criteria)
   - Output format (specific structure)
   - Edge cases handling

4. **Validate & Test**: Ensures agent quality
   - Structural validation (frontmatter, name, description)
   - Triggering tests with various scenarios
   - Verification of agent behavior

## Triggering Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Explicit Request** | User directly asks for function | "Review my code" |
| **Implicit Need** | Context suggests agent needed | "This code is confusing" |
| **Proactive Trigger** | After completing relevant work | Code written → review |
| **Tool Usage Pattern** | Based on prior tool usage | Multiple edits → test analyzer |

## Frontmatter Fields

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| `name` | Yes | lowercase, hyphens, 3-50 chars | `code-reviewer` |
| `description` | Yes | 10-5000 chars with examples | `Use this agent when...` |
| `model` | Yes | inherit/sonnet/opus/haiku | `inherit` |
| `color` | Yes | blue/cyan/green/yellow/magenta/red | `blue` |
| `tools` | No | Array of tool names | `["Read", "Grep"]` |

