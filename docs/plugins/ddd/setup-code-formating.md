# /setup-code-formating - Code Style Configuration

Establishes consistent code formatting rules and style guidelines by updating your project's CLAUDE.md file with enforced standards.

- Purpose - Configure AI-assisted development with consistent code style
- Output - Updated CLAUDE.md with formatting rules

```bash
/setup-code-formating
```

## Arguments

None required - creates standard formatting configuration.

## How It Works

1. **Configuration Detection**: Checks for existing CLAUDE.md in the project root
2. **Standards Application**: Adds or updates the Code Style Rules section with:
   - Semicolon usage rules
   - Quote style enforcement
   - Curly brace conventions
   - Indentation standards
   - Import ordering guidelines

3. **Persistent Memory**: Rules are written to CLAUDE.md, ensuring all future AI interactions follow the same standards

**Formatting Rules Applied**

The command configures the following standards:

| Rule | Setting | Purpose |
|------|---------|---------|
| Semicolons | No semicolons | Cleaner, modern JavaScript/TypeScript |
| Quotes | Single quotes | Consistency across codebase |
| Curly braces | Minimal (no unnecessary) | Reduced visual noise |
| Indentation | 2 spaces | Readable, compact code |
| Import order | External, Internal, Types | Logical organization |

## Usage Examples

```bash
# Basic setup - adds formatting rules to CLAUDE.md
/setup-code-formating

# Typically used during project initialization
/sdd:00-setup Use React, TypeScript, Node.js
/add-typescript-best-practices
/setup-code-formating
```

## Best Practices

- Run early in project setup - Establish standards before significant code is written
- Combine with linting tools - Use ESLint/Prettier to enforce rules automatically
- Team alignment - Ensure all team members use the same CLAUDE.md configuration
- Review generated rules - Adjust the CLAUDE.md output if your project has different conventions
