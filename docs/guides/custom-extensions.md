# Creating Custom Extensions

Build project-specific commands and skills to automate team workflows and extend Claude Code capabilities.

For testing existing prompts or skills, use the `/customaize-agent:test-prompt` command directly.

## When to Use

- Automating repetitive team workflows
- Enforcing project-specific conventions
- Creating reusable knowledge for Claude across sessions
- Building domain-specific capabilities

## Plugins needed for this workflow

- [Customize Agent](../plugins/customaize-agent/README.md)
- [Docs](../plugins/docs/README.md)

## Workflow: Creating a Command

### How It Works

```md
+---------------------------------------------+
| 1. Create Command                           |
|    (interactive assistant)                  |
+----------------------+----------------------+
                       |
                       | generates command file with proper structure
                       v
+---------------------------------------------+
| 2. Test Command                             |
|    RED-GREEN-REFACTOR cycle                 |
+----------------------+----------------------+
                       |
                       | verify command works as expected
                       v
+---------------------------------------------+
| 3. Document Extension                       |
|    (update project docs)                    |
+---------------------------------------------+
```

### 1. Create command

Use the `/customaize-agent:create-command` command to interactively create a new Claude command. The assistant will guide you through understanding purpose, choosing patterns, and generating the command file.

```bash
/customaize-agent:create-command validate API documentation
```

After LLM completes, you will have a command file with proper frontmatter, structure, and patterns. Review and adjust the generated command as needed.

### 2. Test command

Use the `/customaize-agent:test-prompt` command to verify your command works correctly using the RED-GREEN-REFACTOR cycle with subagents.

```bash
/customaize-agent:test-prompt
```

After LLM completes, it will report whether the command handles scenarios correctly. If issues are found, iterate on the command and re-test.

### 3. Document the extension

Use the `/update-docs` command to add the new command to project documentation.

```bash
/update-docs
```

After LLM completes, your command will be documented and discoverable by the team.

## Workflow: Creating a Skill

### How It Works

```md
+---------------------------------------------+
| 1. Create Skill                             |
|    (TDD-based approach)                     |
+----------------------+----------------------+
                       |
                       | understand use cases, plan structure
                       v
+---------------------------------------------+
| 2. Test Skill                               | <--- iterate until bulletproof ---+
|    Pressure scenarios with subagents        |                                   |
+----------------------+----------------------+                                   |
                       |                                                          |
                       | verify skill resists rationalization                     |
                       v                                                          |
+---------------------------------------------+                                   |
| 3. Apply Best Practices                     |-----------------------------------+
|    Anthropic's official guidelines          |
+----------------------+----------------------+
                       |
                       | optimize structure and discoverability
                       v
+---------------------------------------------+
| 4. Document Extension                       |
|    (update project docs)                    |
+---------------------------------------------+
```

### 1. Create skill

Use the `/customaize-agent:create-skill` command to create a new skill. This follows a TDD approach where you first understand concrete use cases before writing the skill.

```bash
/customaize-agent:create-skill image-editor
```

After LLM completes, it will guide you through understanding use cases, planning reusable contents (scripts, references, assets), and generating the SKILL.md file with proper frontmatter and structure.

### 2. Test skill effectiveness

Use the `/customaize-agent:test-skill` command to verify skills work under pressure and resist rationalization. This is critical for discipline-enforcing skills.

```bash
/customaize-agent:test-skill
```

After LLM completes, it will run pressure scenarios with subagents, document failures, and help you close loopholes. Continue iterating until the skill is bulletproof.

### 3. Apply best practices

Use the `/customaize-agent:apply-anthropic-skill-best-practices` command to review and optimize your skill according to Anthropic's official guidelines.

```bash
/customaize-agent:apply-anthropic-skill-best-practices
```

After LLM completes, your skill will be optimized for discoverability, progressive disclosure, and Claude Search Optimization (CSO).

### 4. Document the extension

Use the `/update-docs` command to add the new skill to project documentation.

```bash
/update-docs
```

After LLM completes, your skill will be documented and the team can discover and use it.

## Workflow: Creating a Hook

### How It Works

```md
+---------------------------------------------+
| 1. Analyze Environment                      |
|    (detect tooling & suggest hooks)         |
+----------------------+----------------------+
                       |
                       | identify relevant hooks for project
                       v
+---------------------------------------------+
| 2. Configure Hook                           |
|    (ask targeted questions)                 |
+----------------------+----------------------+
                       |
                       | understand context and requirements
                       v
+---------------------------------------------+
| 3. Create Hook                              |
|    (generate script & register)             |
+----------------------+----------------------+
                       |
                       | hook is ready to use
                       v
+---------------------------------------------+
| 4. Test & Validate                          | <--- iterate until working ---+
|    (happy path + sad path testing)          |                               |
+----------------------+----------------------+                               |
                       |                                                      |
                       | verify both success and failure scenarios            |
                       v                                                      |
+---------------------------------------------+                               |
| 5. Fix Issues (if needed)                   |-------------------------------+
|    (permissions, registration, logic)       |
+---------------------------------------------+
```

### 1. Analyze environment

The `/customaize-agent:create-hook` command automatically detects your project tooling and suggests relevant hooks:

```bash
/customaize-agent:create-hook
```

The assistant will scan for:

- **TypeScript** (`tsconfig.json`) → Type-checking hooks
- **Prettier** (`.prettierrc`) → Formatting hooks  
- **ESLint** (`.eslintrc.*`) → Linting hooks
- **Package scripts** → Test/build validation hooks
- **Git repository** → Security scanning hooks

### 2. Configure hook

The assistant asks targeted questions based on your needs:

1. **What should this hook do?** (with suggestions from analysis)
2. **When should it run?** (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`)
3. **Which tools trigger it?** (`Write`, `Edit`, `Bash`, `*`)
4. **Scope?** (`global`, `project`, `project-local`)
5. **Should Claude see and fix issues?** (integration with additionalContext)
6. **Should successful operations be silent?** (avoid context pollution)

### 3. Create hook

After LLM completes, you will have:

- Hook script in `~/.claude/hooks/` or `.claude/hooks/`
- Proper executable permissions
- Configuration in appropriate `settings.json`
- Project-specific commands using detected tooling

### 4. Test and validate

**CRITICAL**: The assistant tests both happy and sad paths:

- **Happy path**: Create conditions where hook should pass
- **Sad path**: Create conditions where hook should fail/warn
- **Verification**: Check if it blocks/warns/provides context correctly

For example, a hook preventing file deletion will:

1. Create a test file
2. Attempt the protected action
3. Verify the hook prevents it

If issues occur, the assistant will:

- Check hook registration in settings
- Verify script permissions
- Test with simplified version
- Debug hook execution

## Extension Types

### Commands vs Skills vs Hooks

| Aspect | Commands | Skills | Hooks |
|--------|----------|--------|-------|
| **Purpose** | Execute specific workflows | Provide knowledge and patterns | Intercept and validate operations |
| **Location** | `.claude/commands/` | `.claude/skills/` or `~/.claude/skills/` | `.claude/hooks/` or `~/.claude/hooks/` |
| **Invocation** | `/plugin:command-name` | Auto-discovered by Claude | Triggered by events (PreToolUse, PostToolUse) |
| **Structure** | Markdown with frontmatter | SKILL.md with optional resources | Executable scripts (bash, node, python) |
| **Use when** | Automating multi-step tasks | Teaching Claude domain expertise | Quality gates, validation, automation |

### Command Categories

- **Planning**: Feature ideation, proposals, PRDs
- **Implementation**: Technical execution with mode-based variations
- **Analysis**: Review, audit, generate reports
- **Workflow**: Orchestrate multiple steps, coordinate areas
- **Utility**: Simple tools and helpers

### Skill Types

- **Technique**: Concrete methods with steps (condition-based-waiting)
- **Pattern**: Mental models for problems (flatten-with-flags)
- **Reference**: API docs, syntax guides, tool documentation

### Hook Types

- **Code Quality**: PostToolUse for feedback and automated fixes (formatting, linting, type-checking)
- **Security**: PreToolUse to block dangerous operations (secrets detection, unsafe commands)
- **Validation**: PreToolUse to enforce requirements before operations (tests, builds)
- **Development**: PostToolUse for automated improvements (documentation, optimization)

## Key Concepts

### TDD for Documentation

Creating skills follows the same RED-GREEN-REFACTOR cycle as code:

1. **RED**: Run scenarios WITHOUT the skill, document failures
2. **GREEN**: Write minimal skill addressing those failures
3. **REFACTOR**: Close loopholes, optimize structure

### Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) - Always in context
2. **SKILL.md body** - When skill triggers
3. **Bundled resources** - As needed by Claude

### Claude Search Optimization (CSO)

Make skills discoverable:

- Start descriptions with "Use when..." and specific triggers
- Include error messages and symptoms as keywords
- Name by what you DO, not what you ARE (creating-skills not skill-creation)

## Quick Reference

| Task | Command |
|------|---------|
| Create command | `/customaize-agent:create-command` |
| Create skill | `/customaize-agent:create-skill` |
| Test any prompt | `/customaize-agent:test-prompt` |
| Test skill under pressure | `/customaize-agent:test-skill` |
| Apply Anthropic best practices | `/customaize-agent:apply-anthropic-skill-best-practices` |
| Create git hook | `/customaize-agent:create-hook` |
| Document changes | `/update-docs` |
