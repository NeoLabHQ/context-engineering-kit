# Tech Stack Plugin

Language and framework-specific best practices plugin that provides rules automatically loaded into agent context when working with matching file types, ensuring consistent code quality across all AI-assisted development.

Focused on:

- **Automatic Rules** - Best practices loaded into context based on file types being worked on
- **Zero Configuration** - Rules activate automatically when agent reads or writes matching files

## Overview

The Tech Stack plugin provides rules for language and framework-specific best practices. Rules are automatically loaded into the agent's context when working with matching file types (e.g., `**/*.ts` for TypeScript). No manual invocation is needed -- once the plugin is installed, the agent receives relevant coding standards whenever it reads or writes files of that type.


## Quick Start

```bash
# Install the plugin
/plugin install tech-stack@NeoLabHQ/context-engineering-kit

# Rules activate automatically when working on TypeScript files
# No additional setup needed

Refactor @src/main.ts to use generics
-> TypeScript Best Practices automatically loaded and applied
```

## Rules

Rules are context files that are automatically loaded when the agent works on files matching specific glob patterns. Unlike skills (which require manual invocation), rules apply transparently based on the file types being edited.

| Rule | File Pattern | Description |
|------|-------------|-------------|
| [TypeScript Best Practices](typescript-best-practices.md) | `**/*.ts` | Type system guidelines, code style, async patterns, utility types, and code quality standards |

### What TypeScript Best Practices Covers

- **Code Style** - Strict typing, interfaces over types, enum usage, type guards
- **Type System** - Inference, generics, conditional types, mapped types, opaque types
- **Async Patterns** - async/await, Promise-based APIs, concurrent operations
- **Code Quality** - Destructuring, naming conventions, library-first approach
- **Utility Types** - Practical usage of Record, Partial, Omit, Pick, and more
