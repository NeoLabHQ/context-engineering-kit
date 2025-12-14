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
/tech-stack:add-typescript-best-practices

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

## Commands Overview

### /tech-stack:add-typescript-best-practices - TypeScript Configuration

Sets up TypeScript best practices and code style rules in your CLAUDE.md file, providing Claude with explicit guidelines for generating consistent, type-safe code.

- Purpose - Configure TypeScript coding standards
- Output - Updated CLAUDE.md with TypeScript guidelines

```bash
/tech-stack:add-typescript-best-practices
```

#### Arguments

Optional argument which practices to add or avoid.

#### How It Works

1. **File Detection**: Locates or creates CLAUDE.md in your project root

2. **Content Injection**: Adds the following standardized sections:
   - **Code Style Rules** - General principles for TypeScript development
   - **Type System Guidelines** - Interface vs type preferences, enum usage
   - **Library-First Approach** - Recommended libraries for common tasks
   - **Code Quality Patterns** - Destructuring, time handling, and more

3. **Non-Destructive Update**: Preserves existing CLAUDE.md content while adding new guidelines

