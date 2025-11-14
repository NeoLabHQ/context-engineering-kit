# Contributing to Quality Agent

Thank you for your interest in contributing to the Quality Agent marketplace!

## Philosophy

Quality Agent is focused on:
- **Quality over quantity** - Each plugin should meaningfully improve agent output
- **Minimal token footprint** - Efficient prompts that don't bloat context
- **Easy installation** - Simple, clear setup instructions
- **Hand-crafted excellence** - Carefully designed, not auto-generated

## Creating a Plugin

### 1. Choose the Right Category

Place your plugin in the appropriate directory:
- `plugins/code-quality/` - Code review, linting, style checks
- `plugins/testing/` - Test generation, coverage, validation
- `plugins/documentation/` - Docs generation, README updates

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
2. **Installation** - Copy-paste ready instructions
3. **Usage examples** - Show real use cases
4. **Token impact** - Honest about context usage
5. **Limitations** - What it doesn't do

### 5. Quality Guidelines

- **Prompts should be concise** - Every token counts
- **Test thoroughly** - Verify it works as documented
- **Provide examples** - Show real usage scenarios
- **Be specific** - Avoid vague or overly general instructions
- **Focus on quality** - Better to do one thing well than many things poorly

## Submission Process

1. Fork the repository
2. Create a new branch: `git checkout -b plugin/your-plugin-name`
3. Add your plugin with all required files
4. Test your plugin thoroughly
5. Update the main catalog in `PLUGINS.md`
6. Submit a pull request

## Pull Request Template

Your PR should include:

- [ ] Plugin follows directory structure
- [ ] `plugin.json` is valid and complete
- [ ] `README.md` includes all required sections
- [ ] Tested with Claude Code
- [ ] Token usage is documented
- [ ] Added to `PLUGINS.md` catalog

## Code of Conduct

- Be respectful and constructive
- Focus on quality over quantity
- Help others improve their plugins
- Share knowledge and best practices

## Questions?

Open an issue with the `question` label or start a discussion.
