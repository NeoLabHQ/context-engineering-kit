# Contributing to Context Engineering Kit

Thank you for your interest in contributing to the Context Engineering Kit marketplace!

## Philosophy

Context Engineering Kit is focused on:

- **Quality over quantity** - Each plugin should meaningfully improve agent output, just generating as much commands as possible, do not acceptable.
- **Minimal token footprint** - Use efficient and predictable approaches for loading information into context. Specifically:
  - **Commands over skills** - Commands load on-demand, skills descrition are by default loaded into context and maybe not loaded by agent when needed. So use skills only when it clearly more suitable for the use case.
  - **Specialized agents** - Use specialized agents with broad context, when they can be used instead of skill or command. It allow to orcestrator agent more predictable and stable, and decrease chances of context pollution and hallucinations for specialized agents.
  - **Setup-commands** - Use setup commands to update CLAUDE.md file when some short context should be loadeed each time per project for agent. This insure that model really see important information, instead of chance, when using skills.

## Creating a Plugin

### 1. Choose the Right Category

Place your prompt files in the appropriate `plugins/<plugin>` directory or create new one if needed.

### 2. Plugin Structure

Create a directory with these files:

```
your-plugin/
├── plugin.json       # Required: Plugin metadata
├── README.md        # Required: Usage instructions
├── commands/        # Optional: Slash commands
│   └── command.md
└── skills/          # Optional: Skill definitions
    └── skill.md
```

### 3. Plugin Manifest

Create `plugin.json` with:

```json
{
  "name": "your-plugin-name",
  "version": "1.0.0",
  "description": "Clear, concise description (one sentence)",
  "author": "Your Name or GitHub handle",
  "license": "MIT",
  "tokens": {
    "estimated": 500,
    "description": "Explain token usage and what affects it"
  },
  "commands": [
    {
      "name": "command-name",
      "description": "What this command does",
      "path": "commands/command.md"
    }
  ],
  "skills": [
    {
      "name": "skill-name",
      "description": "What this skill provides",
      "path": "skills/skill.md"
    }
  ]
}
```

### 4. Documentation Requirements

Your `README.md` should include:

1. **Clear purpose** - What problem does it solve?
2. **Installation** - Copy-paste ready instructions, for example `setup` commands if it exists.
3. **Usage examples** - Show real use cases
4. **How it works** - High level overview of how the plugin works, and how it can be used in real projects.

### 5. Quality Guidelines

- **Prompts should be concise** - Every token counts
- **Test thoroughly** - Verify it works as documented - you can use `customaize-agent` plugin to test your plugin.
- **Be specific** - Avoid vague or overly general instructions
- **Focus on quality** - Better to do one thing well than many things poorly.
- **Use MUST and SHOULD tags** - Use MUST and SHOULD tags to describe the requirements for the plugin to agent.
- **Use examples** - Use examples to show agent how to behave in different scenarios.

## Submission Process

1. Fork the repository
2. Create a new branch: `git checkout -b plugin/your-plugin-name`
3. Add your plugin with all required files
4. Test your plugin thoroughly
5. Update the main catalog in `.claude-plugin/marketplace.json`
6. Submit a pull request

## Pull Request Template

Your PR should include:

- [ ] Plugin follows directory structure
- [ ] `plugin.json` is valid and complete
- [ ] `README.md` includes all required sections
- [ ] Tested with Claude Code
- [ ] Added to `.claude-plugin/marketplace.json` catalog

## Questions?

Open an issue with the `question` label or start a discussion.

## Tips

- Use the `--plugin-dir` flag to test plugins during development. This loads your plugin directly without requiring installation. Example `claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two`
