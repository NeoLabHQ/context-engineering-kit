# /add-typescript-best-practices - TypeScript Configuration

Sets up TypeScript best practices and code style rules in your CLAUDE.md file, providing Claude with explicit guidelines for generating consistent, type-safe code.

- Purpose - Configure TypeScript coding standards
- Output - Updated CLAUDE.md with TypeScript guidelines

```bash
/add-typescript-best-practices
```

## Arguments

Optional argument which practices to add or avoid.

## How It Works

1. **File Detection**: Locates or creates CLAUDE.md in your project root

2. **Content Injection**: Adds the following standardized sections:
   - **Code Style Rules** - General principles for TypeScript development
   - **Type System Guidelines** - Interface vs type preferences, enum usage
   - **Library-First Approach** - Recommended libraries for common tasks
   - **Code Quality Patterns** - Destructuring, time handling, and more

3. **Non-Destructive Update**: Preserves existing CLAUDE.md content while adding new guidelines
