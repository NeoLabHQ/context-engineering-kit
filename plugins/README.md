# Quality Agent Plugins

This directory contains hand-crafted Claude Code plugins focused on improving agent result quality.

## Plugin Categories

- **code-quality/** - Plugins for code review, linting, and quality checks
- **testing/** - Plugins for test generation and validation
- **documentation/** - Plugins for documentation generation and maintenance

## Plugin Structure

Each plugin should follow this structure:

```
plugin-name/
├── plugin.json          # Plugin manifest
├── README.md           # Plugin documentation
├── commands/           # Slash commands (optional)
└── skills/            # Skills definitions (optional)
```

## Plugin Manifest (plugin.json)

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief description of what the plugin does",
  "author": "Your Name",
  "tokens": {
    "estimated": 500,
    "description": "Token usage explanation"
  },
  "commands": [],
  "skills": []
}
```

## Getting Started

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on creating plugins.
