# Domain-Driven Development Plugin

Code quality framework that embeds Clean Architecture, SOLID principles, and Domain-Driven Design patterns into your development workflow through persistent rules and contextual commands.

Focused on:

- **Clean Architecture** - Separation of concerns with layered architecture boundaries
- **Domain-Driven Design** - Ubiquitous language and bounded contexts for complex domains
- **SOLID Principles** - Single responsibility, open-closed, and dependency inversion patterns
- **Code Quality Standards** - Consistent formatting, naming conventions, and anti-pattern avoidance

## Overview

The DDD plugin implements battle-tested software architecture principles that have proven essential for building maintainable, scalable systems. It provides commands to configure AI-assisted development with established best practices, and rules that guide code generation toward high-quality patterns.

The plugin is based on foundational works including Eric Evans' "Domain-Driven Design" (2003), Robert C. Martin's "Clean Architecture" (2017), and the SOLID principles that have become industry standards for object-oriented design.

These principles address the core challenge of software development: **managing complexity**. By establishing clear boundaries between business logic and infrastructure, using domain-specific naming, and following proven design patterns, teams can build systems that remain understandable and modifiable as they grow.

## Quick Start

```bash
# Install the plugin
/plugin install ddd@NeoLabHQ/context-engineering-kit

# Set up code formatting standards in CLAUDE.md
/ddd:setup-code-formating

# Rules activate automatically when writing or reviewing code
# Alternatively, you can ask Claude to use DDD directly
> claude "Use DDD rules to implement user authentication"
```

[Usage Examples](./usage-examples.md)

## setup-code-formating command

Establishes consistent code formatting rules and style guidelines by updating your project's CLAUDE.md file with enforced standards.

See [setup-code-formating.md](./setup-code-formating.md) for detailed command documentation.

## Rules

The DDD plugin includes 14 rules organized into four categories that activate automatically when writing or reviewing code. Each rule targets specific file patterns and has an assigned impact level.

| Category | Rules |
|----------|-------|
| **Architecture** | Clean Architecture & DDD, Separation of Concerns, Functional Core / Imperative Shell |
| **Function Design** | Command-Query Separation, Principle of Least Astonishment, Call-Site Honesty |
| **Explicitness** | Explicit Control Flow, Explicit Data Flow, Explicit Side Effects |
| **Code Quality** | Error Handling, Domain-Specific Naming, Library-First Approach, Early Return Pattern, Function & File Size Limits |

See [rules.md](./rules.md) for detailed documentation of all rules.

## Foundation

The DDD plugin is based on foundational software engineering literature that has shaped modern development practices:

### Core Literature

- **[Domain-Driven Design](https://www.domainlanguage.com/ddd/)** (Eric Evans, 2003) - Introduced ubiquitous language, bounded contexts, and strategic design patterns for managing complex domains
- **[Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)** (Robert C. Martin, 2012/2017) - Defines dependency rules and layer boundaries for maintainable systems
- **[SOLID Principles](https://en.wikipedia.org/wiki/SOLID)** (Robert C. Martin, 2000s) - Five principles of object-oriented design that promote maintainability

### Key Concepts Applied

| Concept | Source | Application in Plugin |
|---------|--------|----------------------|
| Ubiquitous Language | Evans (DDD) | Domain-specific naming conventions |
| Bounded Contexts | Evans (DDD) | Module and file organization |
| Dependency Inversion | Martin (SOLID) | Layer separation rules |
| Single Responsibility | Martin (SOLID) | Function and file size limits |
| Separation of Concerns | General | Business logic isolation |
| Command-Query Separation | Meyer (OOSC) | Function design rules |
| Functional Core, Imperative Shell | Bernhardt | Pure logic with side effects at edges |
| Principle of Least Astonishment | General | Function behavior predictability |
