# Tech Stack Plugin

Language and framework-specific best practices plugin that configures your CLAUDE.md with standardized coding standards, ensuring consistent code quality across all AI-assisted development.

Focused on:

- **Standardized Guidelines** - Pre-defined best practices for specific languages and frameworks
- **Initial context building** - Updates of CLAUDE.md, so it will be loaded during every claude code session

## Overview

The Tech Stack plugin provides commands for setting up language and framework-specific best practices in your CLAUDE.md file. Instead of manually defining coding standards, this plugin provides curated, production-tested guidelines that can be applied with a single command.

When Claude operates with explicit coding standards in CLAUDE.md, it produces more consistent and higher-quality code. The Tech Stack plugin bridges the gap between starting a new project and having well-defined development standards.

## Quick Start

```bash
# Install the plugin
/plugin install tech-stack@NeoLabHQ/context-engineering-kit

# Add TypeScript best practices to your project
/add-typescript-best-practices

# Review the updated CLAUDE.md
cat CLAUDE.md
```

[Usage Examples](./usage-examples.md)


### Why CLAUDE.md Matters

CLAUDE.md is read by Claude at the start of every conversation. By placing coding standards here:

1. **Persistent Context** - Guidelines are always available to Claude
2. **Project-Specific Rules** - Different projects can have different standards
3. **Team Synchronization** - All team members share the same AI configuration
4. **Version Control** - Guidelines are tracked alongside your code

## Commands

- [/add-typescript-best-practices](./add-typescript-best-practices.md) - Sets up TypeScript best practices and code style rules in your CLAUDE.md file, providing Claude with explicit guidelines for generating consistent, type-safe code.

