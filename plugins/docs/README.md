# Docs Plugin

Technical documentation management plugin that maintains living documentation throughout the development lifecycle, ensuring docs stay accurate, useful, and aligned with code changes.

## Plugin Target

- Reduce documentation debt - Identify and remove outdated or duplicate documentation
- Improve discoverability - Ensure documentation is findable when users need it
- Maintain accuracy - Keep docs synchronized with implementation changes
- Focus effort - Document only what provides real value to users

Focused on:

- **Living documentation** - Documentation that evolves with your codebase
- **Smart prioritization** - Focus on high-impact documentation that helps users accomplish real tasks
- **Automation integration** - Leverage generated docs (OpenAPI, JSDoc, GraphQL) where appropriate
- **Documentation hygiene** - Prevent documentation debt and bloat

## Overview

The Docs plugin provides a structured approach to documentation management based on the principle that documentation must justify its existence. It implements a documentation philosophy that prioritizes user tasks over comprehensive coverage, preferring automation where possible and manual documentation where it adds unique value.

The plugin guides you through:

- **Documentation audit** - Assess existing docs for freshness, accuracy, and value
- **Gap analysis** - Identify high-impact documentation needs
- **Smart updates** - Create or update documentation with clear purpose
- **Quality validation** - Verify that examples work and links are valid

## Quick Start

```bash
# Install the plugin
/plugin install docs@NeoLabHQ/context-engineering-kit

# Update project documentation after implementing features
> claude "implement user profile settings page"
> /update-docs

# Focus on specific documentation type
> /update-docs api

# Target specific directory
> /update-docs src/payments/
```

[Usage Examples](./usage-examples.md)

## Commands

### update-docs

Comprehensive documentation update command that analyzes your project, identifies documentation needs, and creates or updates documentation following best practices.

See [update-docs.md](./update-docs.md) for detailed command documentation.

### write-concisely

Apply William Strunk Jr.'s *The Elements of Style* principles to documentation. Makes writing clearer, stronger, and more professional by cutting ruthlessly and eliminating weak constructions.

See [write-concisely.md](./write-concisely.md) for detailed command documentation.

## Theoretical Foundation

The Docs plugin is grounded in classic writing principles that have stood the test of time:

### Core Reference

- **[The Elements of Style](https://en.wikisource.org/wiki/The_Elements_of_Style)** - William Strunk Jr.'s 1918 manual, later revised by E.B. White, remains the definitive guide for clear, concise English prose

### Key Principles Applied

| Principle | Description |
|-----------|-------------|
| **Active voice** | Subject performs action - more direct and vigorous |
| **Positive form** | State what is, not what isn't - stronger assertions |
| **Concrete language** | Specific over abstract - engages the reader |
| **Omit needless words** | Every word must earn its place - tighter prose |
| **Related words together** | Proximity signals relationship - clearer meaning |
| **Emphatic endings** | Important words at sentence end - memorable impact |

These principles inform both the `write-concisely` command and the quality standards applied by `update-docs`.
