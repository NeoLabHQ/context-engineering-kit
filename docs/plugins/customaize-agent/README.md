# Customaize Agent Plugin

Framework for creating, testing, and optimizing Claude Code extensions including commands, skills, and hooks with built-in prompt engineering best practices.

Focused on:

- **Extension creation** - Interactive assistants for building commands, skills, and hooks with proper structure
- **TDD for prompts** - RED-GREEN-REFACTOR cycle applied to prompt engineering with subagent testing
- **Anthropic best practices** - Official guidelines for skill authoring, progressive disclosure, and discoverability
- **Prompt optimization** - Persuasion principles and token efficiency techniques

## Plugin Target

- Build reusable extensions - Create commands, skills, and hooks that follow established patterns
- Ensure prompt quality - Test prompts before deployment using isolated subagent scenarios
- Optimize for discoverability - Apply Claude Search Optimization (CSO) principles

## Overview

The Customaize Agent plugin provides a complete toolkit for extending Claude Code's capabilities. It applies Test-Driven Development principles to prompt engineering: you write test scenarios first, watch agents fail, create prompts that address those failures, and iterate until bulletproof.

The plugin is built on Anthropic's official skill authoring best practices and research-backed persuasion principles ([Prompting Science Report 3](https://arxiv.org/abs/2508.00614) - persuasion techniques more than doubled compliance rates from 33% to 72%).

## Quick Start

```bash
# Install the plugin
/plugin install customaize-agent@NeoLabHQ/context-engineering-kit

# Create a new agent
> /customaize-agent:create-agent code-reviewer "Review code for quality"

# Create a new command
> /customaize-agent:create-command validate API documentation

# Create a new skill
> /customaize-agent:create-skill image-editor

# Test a prompt before deployment
> /customaize-agent:test-prompt

# Apply Anthropic's best practices to a skill
> /customaize-agent:apply-anthropic-skill-best-practices
```

[Usage Examples](./usage-examples.md)

## Commands Overview

### /customaize-agent:create-command - Command Creation Assistant

Interactive assistant for creating new Claude commands with proper structure, patterns, and MCP tool integration.

- Purpose - Guide through creating well-structured commands
- Output - Complete command file with frontmatter, sections, and patterns

```bash
/customaize-agent:create-command ["command name or description"]
```

#### Arguments

Optional command name or description of the command's purpose (e.g., "validate API documentation", "deploy to staging").

#### Usage Examples

```bash
# Create an API validation command
> /customaize-agent:create-command validate API documentation

# Create a deployment command
> /customaize-agent:create-command deploy feature to staging

# Start without a specific idea
> /customaize-agent:create-command
```

#### How It Works

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

#### Best Practices

- Research first - Let the assistant examine existing commands before creating new ones
- Be specific about purpose - Clearly describe what problem the command solves
- Choose location carefully - Project commands for codebase-specific workflows, user commands for general utilities
- Include MCP tools - Use MCP tool patterns instead of CLI commands where applicable
- Add human review sections - Flag decisions that need verification

---

### /customaize-agent:create-workflow-command - Workflow Command Builder

Create commands that orchestrate multi-step workflows by dispatching sub-agents with task-specific instructions stored in separate files. Solves the **context bloat problem** by keeping orchestrator commands lean.

- Purpose - Build workflow commands that dispatch sub-agents with file-based task prompts
- Output - Complete workflow structure: orchestrator command, task files, and optional custom agents

```bash
/customaize-agent:create-workflow-command [workflow-name] [description]
```

#### Arguments

Optional workflow name (kebab-case) and description of what the workflow accomplishes.

#### Usage Examples

```bash
# Create a feature implementation workflow
> /customaize-agent:create-workflow-command feature-implementation "Research, plan, and implement features"

# Create a code review workflow
> /customaize-agent:create-workflow-command code-review "Multi-phase code analysis and feedback"

# Start interactive workflow creation
> /customaize-agent:create-workflow-command
```

#### How It Works

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

#### Execution Patterns

| Pattern | Use Case | Description |
|---------|----------|-------------|
| **Sequential** | Dependent steps | Each step uses previous step's output |
| **Parallel** | Independent analysis | Multiple agents run simultaneously |
| **Stateful (Resume)** | Shared context | Continue same agent across steps |

---

### /customaize-agent:create-agent - Agent Creation Guide

Comprehensive guide for creating Claude Code agents with proper structure, triggering conditions, system prompts, and validation. Combines official Anthropic best practices with proven patterns.

- Purpose - Create autonomous agents that handle complex, multi-step tasks independently
- Output - Complete agent file with frontmatter, triggering examples, and system prompt

```bash
/customaize-agent:create-agent [agent-name] [optional description]
```

#### Arguments

Optional agent name (kebab-case) and description of the agent's purpose.

#### Usage Examples

```bash
# Create a code review agent
> /customaize-agent:create-agent code-reviewer "Review code for quality and security"

# Create a test generation agent
> /customaize-agent:create-agent test-generator

# Start interactive agent creation
> /customaize-agent:create-agent
```

#### How It Works

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

#### Triggering Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Explicit Request** | User directly asks for function | "Review my code" |
| **Implicit Need** | Context suggests agent needed | "This code is confusing" |
| **Proactive Trigger** | After completing relevant work | Code written → review |
| **Tool Usage Pattern** | Based on prior tool usage | Multiple edits → test analyzer |

#### Frontmatter Fields

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| `name` | Yes | lowercase, hyphens, 3-50 chars | `code-reviewer` |
| `description` | Yes | 10-5000 chars with examples | `Use this agent when...` |
| `model` | Yes | inherit/sonnet/opus/haiku | `inherit` |
| `color` | Yes | blue/cyan/green/yellow/magenta/red | `blue` |
| `tools` | No | Array of tool names | `["Read", "Grep"]` |


---

### /customaize-agent:create-skill - Skill Development Guide

Guide for creating effective skills using a TDD-based approach. This command treats skill creation as Test-Driven Development applied to process documentation.

- Purpose - Create reusable skills that extend Claude's capabilities
- Output - Complete skill directory with SKILL.md and optional resources

```bash
/customaize-agent:create-skill ["skill name"]
```

#### Arguments

Optional skill name (e.g., "image-editor", "pdf-processing", "code-review").

#### Usage Examples

```bash
# Create an image editing skill
> /customaize-agent:create-skill image-editor

# Create a database query skill
> /customaize-agent:create-skill bigquery-analysis

# Start the skill creation workflow
> /customaize-agent:create-skill
```

#### How It Works

1. **Understanding with Concrete Examples**: Gathers usage scenarios
   - What functionality should the skill support?
   - How would users invoke this skill?
   - What triggers should activate it?

2. **Planning Reusable Contents**: Analyzes examples to identify resources
   - Scripts (`scripts/`) - Executable code for deterministic tasks
   - References (`references/`) - Documentation to load as needed
   - Assets (`assets/`) - Templates, images, files used in output

3. **Skill Initialization**: Creates proper structure
   - SKILL.md with YAML frontmatter (name, description)
   - Resource directories as needed
   - Proper naming conventions (gerund form: "Processing PDFs")

4. **Content Development**: Writes skill documentation
   - Overview with core principle
   - When to Use section with triggers and symptoms
   - Quick Reference for scanning
   - Implementation details
   - Common Mistakes section

5. **TDD Testing Cycle**: Applies RED-GREEN-REFACTOR
   - RED: Run scenarios WITHOUT skill, document failures
   - GREEN: Write skill addressing those failures
   - REFACTOR: Close loopholes, iterate until bulletproof

#### Best Practices

- Start with concrete examples - Understand real use cases before writing
- Apply TDD strictly - No skill without failing tests first
- Keep SKILL.md lean - Under 500 lines, use separate files for heavy reference
- Optimize for discovery - Start descriptions with "Use when..." and include specific triggers
- Name by action - Use gerunds like "Processing PDFs" not "PDF Processor"

---

### /customaize-agent:create-hook - Git Hook Configuration

Analyze the project, suggest practical hooks, and create them with proper testing. Intelligent project analysis detects tooling and suggests relevant hooks.

- Purpose - Create and configure git hooks with automated testing
- Output - Working hook script with proper registration

```bash
/customaize-agent:create-hook ["hook type or description"]
```

#### Arguments

Optional hook type or description of desired behavior (e.g., "type-check on save", "prevent secrets in commits").

#### Usage Examples

```bash
# Create a TypeScript type-checking hook
> /customaize-agent:create-hook type-check TypeScript files

# Create a security scanning hook
> /customaize-agent:create-hook prevent commits with secrets

# Let the assistant analyze and suggest hooks
> /customaize-agent:create-hook
```

#### How It Works

1. **Environment Analysis**: Detects project tooling automatically
   - TypeScript (`tsconfig.json`) - Suggests type-checking hooks
   - Prettier (`.prettierrc`) - Suggests formatting hooks
   - ESLint (`.eslintrc.*`) - Suggests linting hooks
   - Package scripts - Suggests test/build validation hooks
   - Git repository - Suggests security scanning hooks

2. **Hook Configuration**: Asks targeted questions
   - What should this hook do?
   - When should it run? (PreToolUse, PostToolUse, UserPromptSubmit)
   - Which tools trigger it? (Write, Edit, Bash, *)
   - Scope? (global, project, project-local)
   - Should Claude see and fix issues?
   - Should successful operations be silent?

3. **Hook Creation**: Generates complete hook setup
   - Script in `~/.claude/hooks/` or `.claude/hooks/`
   - Proper executable permissions
   - Configuration in appropriate `settings.json`
   - Project-specific commands using detected tooling

4. **Testing & Validation**: Tests both happy and sad paths
   - Happy path: Create conditions where hook should pass
   - Sad path: Create conditions where hook should fail/warn
   - Verification: Check blocking/warning/context behavior

#### Hook Types

| Type | Trigger | Use Case |
|------|---------|----------|
| **Code Quality** | PostToolUse | Formatting, linting, type-checking |
| **Security** | PreToolUse | Block dangerous operations, secrets detection |
| **Validation** | PreToolUse | Enforce requirements before operations |
| **Development** | PostToolUse | Automated improvements, documentation |

#### Best Practices

- Test both paths - Always verify both success and failure scenarios
- Use absolute paths - Avoid relative paths in scripts, use `$CLAUDE_PROJECT_DIR`
- Read JSON from stdin - Never use argv for hook input
- Provide specific feedback - Use `additionalContext` for error communication
- Keep success silent - Use `suppressOutput: true` to avoid context pollution

---

### /customaize-agent:test-skill - Skill Pressure Testing

Verify skills work under pressure and resist rationalization using the RED-GREEN-REFACTOR cycle. Critical for discipline-enforcing skills.

- Purpose - Test skill effectiveness with pressure scenarios
- Output - Verification report with rationalization table

```bash
/customaize-agent:test-skill ["skill path or name"]
```

#### Usage Examples

```bash
# Test a TDD enforcement skill
> /customaize-agent:test-skill tdd

# Test a custom skill by path
> /customaize-agent:test-skill ~/.claude/skills/code-review/

# Start testing workflow
> /customaize-agent:test-skill
```

#### Arguments

Optional path to skill being tested or skill name.

#### How It Works

1. **RED Phase - Baseline Testing**: Run scenarios WITHOUT the skill
   - Create pressure scenarios (3+ combined pressures)
   - Document agent behavior and rationalizations verbatim
   - Identify patterns in failures

2. **GREEN Phase - Write Minimal Skill**: Address baseline failures
   - Write skill addressing specific observed rationalizations
   - Run same scenarios WITH skill
   - Verify agent now complies

3. **REFACTOR Phase - Close Loopholes**: Iterate until bulletproof
   - Identify NEW rationalizations from testing
   - Add explicit counters for each loophole
   - Build rationalization table
   - Create red flags list
   - Re-test until bulletproof

#### Pressure Types

| Pressure | Example |
|----------|---------|
| **Time** | Emergency, deadline, deploy window closing |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior says skip it, manager overrides |
| **Economic** | Job, promotion, company survival at stake |
| **Exhaustion** | End of day, already tired, want to go home |
| **Social** | Looking dogmatic, seeming inflexible |
| **Pragmatic** | "Being pragmatic vs dogmatic" |

#### Best Practices

- Combine 3+ pressures - Single pressure tests are too weak
- Document verbatim - Capture exact rationalizations, not summaries
- Iterate completely - Continue REFACTOR until no new rationalizations
- Use meta-testing - Ask agents how skill could have been clearer
- Test all skill types - Discipline-enforcing, technique, pattern, and reference skills need different tests

---

### /customaize-agent:test-prompt - Prompt Testing with Subagents

Test any prompt (commands, hooks, skills, subagent instructions) using the RED-GREEN-REFACTOR cycle with subagents for isolated testing.

- Purpose - Verify prompts produce desired behavior before deployment
- Output - Test results with improvement recommendations

```bash
/customaize-agent:test-prompt ["prompt path or content"]
```

#### Usage Examples

```bash
# Test a command before deployment
> /customaize-agent:test-prompt .claude/commands/deploy.md

# Test inline prompt content
> /customaize-agent:test-prompt "Review this code for security issues"

# Start interactive testing workflow
> /customaize-agent:test-prompt
```

#### Arguments

Optional path to prompt file or inline prompt content to test.

#### How It Works

1. **RED Phase - Baseline Testing**: Run without prompt using subagent
   - Design test scenarios appropriate for prompt type
   - Launch subagent WITHOUT prompt
   - Document agent behavior, actions, and mistakes

2. **GREEN Phase - Write Minimal Prompt**: Make tests pass
   - Address specific baseline failures
   - Apply appropriate degrees of freedom
   - Use persuasion principles if discipline-enforcing
   - Test WITH prompt using subagent

3. **REFACTOR Phase - Optimize**: Improve while staying green
   - Close loopholes for discipline violations
   - Improve clarity using meta-testing
   - Reduce tokens without losing behavior
   - Re-test with fresh subagents

#### Why Subagents?

| Benefit | Description |
|---------|-------------|
| **Clean slate** | No conversation history affecting behavior |
| **Isolation** | Test only the prompt, not accumulated context |
| **Reproducibility** | Same starting conditions every run |
| **Parallelization** | Test multiple scenarios simultaneously |
| **Objectivity** | No bias from prior interactions |

#### Prompt Types & Testing Strategies

| Prompt Type | Test Focus | Example |
|-------------|------------|---------|
| **Instruction** | Steps followed correctly? | Git workflow command |
| **Discipline-enforcing** | Resists rationalization? | TDD compliance skill |
| **Guidance** | Applied appropriately? | Architecture patterns |
| **Reference** | Accurate and accessible? | API documentation |
| **Subagent** | Task accomplished reliably? | Code review prompt |

#### Best Practices

- Use fresh subagents - Always via Task tool for isolated testing
- Design realistic scenarios - Include constraints, pressures, edge cases
- Document exact failures - "Agent was wrong" doesn't tell you what to fix
- Avoid over-engineering - Only address failures you documented in baseline
- Iterate on token efficiency - Reduce tokens without losing behavior

---

### /customaize-agent:apply-anthropic-skill-best-practices - Skill Optimization

Comprehensive guide for skill development based on Anthropic's official best practices. Use for complex skills requiring detailed structure and optimization.

- Purpose - Apply official guidelines to skill authoring
- Output - Optimized skill with improved discoverability

```bash
/customaize-agent:apply-anthropic-skill-best-practices ["skill path"]
```

#### Arguments

Optional skill name or path to skill being reviewed.

#### Usage Examples

```bash
# Optimize an existing skill
> /customaize-agent:apply-anthropic-skill-best-practices pdf-processing

# Review a skill by path
> /customaize-agent:apply-anthropic-skill-best-practices ~/.claude/skills/bigquery/

# Start optimization workflow
> /customaize-agent:apply-anthropic-skill-best-practices
```

#### How It Works

1. **Structure Review**: Checks skill organization
   - YAML frontmatter (name: 64 chars max, description: 1024 chars max)
   - SKILL.md body under 500 lines
   - Progressive disclosure with separate files
   - One-level-deep references

2. **Description Optimization**: Improves discoverability
   - Third-person writing (injected into system prompt)
   - "Use when..." trigger conditions
   - Specific keywords and terms
   - Both what it does AND when to use it

3. **Content Guidelines**: Applies best practices
   - Avoid time-sensitive information
   - Consistent terminology throughout
   - Concrete examples over abstract descriptions
   - Template patterns and examples patterns

4. **Workflow Enhancement**: Adds feedback loops
   - Clear sequential steps with checklists
   - Validation steps for critical operations
   - Conditional workflow patterns

5. **Token Efficiency**: Optimizes for context window
   - Remove redundant explanations
   - Challenge each paragraph's token cost
   - Use progressive disclosure appropriately

#### Key Principles

| Principle | Description |
|-----------|-------------|
| **Progressive Disclosure** | Metadata always loaded, SKILL.md on trigger, resources as needed |
| **CSO (Claude Search Optimization)** | Rich descriptions with triggers, keywords, and symptoms |
| **Degrees of Freedom** | Match specificity to task fragility |
| **Conciseness** | Only add context Claude doesn't already have |

#### Best Practices

- Test with all models - What works for Opus may need more detail for Haiku
- Iterate with Claude - Use Claude A to design, Claude B to test
- Observe navigation - Watch how Claude actually uses the skill
- Build evaluations first - Create test scenarios BEFORE extensive documentation
- Gather team feedback - Address blind spots from different usage patterns

---

## Skills

### prompt-engineering

Advanced prompt engineering techniques including Anthropic's official best practices and research-backed persuasion principles.

**Includes:**

- **Few-Shot Learning** - Teach by showing examples
- **Chain-of-Thought** - Step-by-step reasoning
- **Prompt Optimization** - Systematic improvement through testing
- **Template Systems** - Reusable prompt structures
- **System Prompt Design** - Global behavior and constraints

**Persuasion Principles (from [Prompting Science Report 3](https://arxiv.org/abs/2508.00614)):**

| Principle | Use For | Example |
|-----------|---------|---------|
| **Authority** | Discipline enforcement | "YOU MUST", "No exceptions" |
| **Commitment** | Accountability | "Announce skill usage", "Choose A, B, or C" |
| **Scarcity** | Preventing procrastination | "IMMEDIATELY", "Before proceeding" |
| **Social Proof** | Establishing norms | "Every time", "X without Y = failure" |
| **Unity** | Collaboration | "our codebase", "we both want quality" |

**Key Concepts:**

- **Context Window Management** - The window is a shared resource; be concise
- **Degrees of Freedom** - Match specificity to task fragility
- **Progressive Disclosure** - Start simple, add complexity when needed

### context-engineering

Use when writing, editing, or optimizing commands, skills, or sub-agent prompts. Provides deep understanding of context mechanics in agent systems.

**The Anatomy of Context:**

| Component | Role | Key Insight |
|-----------|------|-------------|
| **System Prompts** | Core identity and constraints | Balance specificity vs flexibility ("right altitude") |
| **Tool Definitions** | Available actions | Poor descriptions force guessing; optimize with examples |
| **Retrieved Documents** | Domain knowledge | Use just-in-time loading, not pre-loading |
| **Message History** | Conversation state | Can dominate context in long tasks |
| **Tool Outputs** | Action results | Up to 83.9% of total context usage |

**Key Principles:**

- **Attention Budget** - Context is finite; every token depletes the budget
- **Progressive Disclosure** - Load information only when needed
- **Quality over Quantity** - Smallest high-signal token set wins
- **Lost-in-Middle Effect** - Critical info at start/end, not middle

**Practical Patterns:**

- File-system based access for progressive disclosure
- Hybrid strategies (pre-load some, load rest on-demand)
- Explicit context budgeting with compaction triggers

### agent-evaluation

Use when testing prompt effectiveness, validating context engineering choices, or measuring agent improvement quality.

**Evaluation Approaches:**

- **LLM-as-Judge** - Direct scoring, pairwise comparison, rubric-based
- **Outcome-Focused** - Judge results, not exact paths (agents may take valid alternative routes)
- **Multi-Level Testing** - Simple to complex queries, isolated to extended interactions
- **Bias Mitigation** - Position bias, verbosity bias, self-enhancement bias

**Multi-Dimensional Evaluation Rubric:**

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Instruction Following | 0.30 | Task adherence |
| Output Completeness | 0.25 | Coverage of requirements |
| Tool Efficiency | 0.20 | Optimal tool selection |
| Reasoning Quality | 0.15 | Logical soundness |
| Response Coherence | 0.10 | Structure and clarity |

## Theoretical Foundation

The Customaize Agent plugin is based on:

### Persuasion Research

- **[Prompting Science Report 3](https://arxiv.org/abs/2508.00614)** - Tested 7 persuasion principles with N=28,000 AI conversations. Persuasion techniques more than doubled compliance rates (33% to 72%, p < .001), based on related SSRN work on persuasion principles.

### Agent Skills for Context Engineering

- [Agent Skills for Context Engineering project](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) by Murat Can Koylan.
