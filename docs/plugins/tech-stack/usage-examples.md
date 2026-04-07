# Tech Stack Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the Tech Stack plugin for establishing coding standards.

## Examples

### New TypeScript Project Setup

**Scenario**: You're starting a new TypeScript API project and want to establish coding standards from the beginning.

```bash
# Initialize Claude configuration
claude /init

# Create project constitution
/sdd:00-setup TypeScript REST API with Express and PostgreSQL

# Add TypeScript best practices
/add-typescript-best-practices

# Verify the configuration
cat CLAUDE.md
```

**Expected Flow**:

1. Claude creates initial CLAUDE.md with project basics
2. SDD establishes architectural principles in specs/constitution.md
3. Tech Stack adds TypeScript-specific coding standards to CLAUDE.md
4. Your project now has comprehensive development guidelines

**Result in CLAUDE.md**:
```markdown
## Code Style Rules

### General Principles

- **TypeScript**: All code must be strictly typed, leverage TypeScript's type safety features

### Code style rules

- Interfaces over types - use interfaces for object types
- Use enum for constant values, prefer them over string literals
- Export all types by default
- Use type guards instead of type assertions
```

### Onboarding Existing Project

**Scenario**: You have an existing TypeScript codebase that needs standardized coding guidelines for the team.

```bash
# Add TypeScript best practices to existing project
/add-typescript-best-practices

# Review what was added
cat CLAUDE.md

# Optionally, customize for your project's specific needs
> claude "add a section about our REST API naming conventions to CLAUDE.md"
```

**Expected Flow**:

1. Tech Stack adds standardized TypeScript guidelines
2. Existing CLAUDE.md content is preserved
3. You can customize the added guidelines to match your project

**When to Customize**:

Your team may have different preferences. After running the command, consider:

- Removing library recommendations that don't match your stack
- Adding project-specific type naming conventions
- Including framework-specific patterns (NestJS, Next.js, etc.)

### Team Standardization

**Scenario**: Your team wants consistent AI-generated code across all developers.

```bash
# Lead developer sets up standards
/add-typescript-best-practices

# Commit CLAUDE.md to version control
git add CLAUDE.md
git commit -m "Add TypeScript coding standards for AI assistance"

# All team members get the same guidelines when they pull
git pull
```

**Benefits**:

- All team members' Claude instances follow the same rules
- Code reviews have consistent standards to reference
- New team members immediately work with established patterns
- AI-generated code matches team conventions

### Combined with Code Formatting

**Scenario**: You want both language best practices and code formatting standards.

```bash
# Add TypeScript best practices
/add-typescript-best-practices

# Add code formatting and architecture rules
/setup-code-formating

# Your CLAUDE.md now has comprehensive standards
cat CLAUDE.md
```

**Result**:

Your CLAUDE.md will contain:

1. **TypeScript Best Practices** (from Tech Stack)
   - Type system guidelines
   - Library recommendations
   - Code quality patterns

2. **Code Formatting Rules** (from DDD)
   - Clean Architecture principles
   - SOLID patterns
   - Formatting standards

### Feature Development with Standards

**Scenario**: Implementing a new feature while ensuring it follows established TypeScript practices.

```bash
# Ensure standards are in place
/add-typescript-best-practices

# Implement a feature
> claude "create a user authentication service with JWT tokens"
```

**Claude's Implementation Will Follow**:

- Use interfaces for user and token types
- Use enums for authentication states
- Apply type guards for token validation
- Use established libraries (e.g., jsonwebtoken)
- Apply destructuring patterns

**Example Generated Code**:

```typescript
// Interfaces over types (from guidelines)
interface User {
  id: string;
  email: string;
  role: UserRole;
}

// Enum for constants (from guidelines)
enum UserRole {
  Admin = 'ADMIN',
  User = 'USER',
  Guest = 'GUEST'
}

// Type guards instead of assertions (from guidelines)
function isValidUser(data: unknown): data is User {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'email' in data
  );
}

// Destructuring (from guidelines)
async function authenticateUser(credentials: Credentials): Promise<AuthResult> {
  const { email, password } = credentials;
  const { data: user } = await userRepository.findByEmail(email);
  // ...
}
```

### Quality Assurance Workflow

**Scenario**: After implementing a feature, verify it follows the established standards.

```bash
# Setup standards first
/add-typescript-best-practices

# Implement feature
> claude "create a payment processing module"

# Reflect on the implementation
/reflect "verify TypeScript best practices are followed"
```

**Reflection Output Example**:
```
Reflection Analysis:
- All interfaces properly defined for PaymentRequest, PaymentResponse
- Enum used for PaymentStatus (PENDING, COMPLETED, FAILED)
- Type guards implemented for external API responses
- Destructuring applied consistently

Improvements Suggested:
- Consider using date-fns for date formatting (library-first principle)
- Add explicit return types to all functions
```

```bash
# Apply improvements
> claude "apply the suggested improvements from reflection"

# Save insights for future reference
/memorize
```

### Gradual Standards Adoption

**Scenario**: Introducing TypeScript best practices incrementally to a large codebase.

```bash
# Start with basic standards
/add-typescript-best-practices

# Review a specific module against new standards
/critique src/users/*.ts

# Address findings in that module
> claude "refactor the users module to follow TypeScript best practices"

# Move to next module
/critique src/payments/*.ts
```

**Benefits of Gradual Adoption**:

1. Avoid massive refactoring PRs
2. Learn patterns as you apply them
3. Team can adapt to new standards progressively
4. Easier to track and review changes

## Integration with Other Plugins

### With SDD (Full Project Setup)

```bash
# Complete project initialization
/sdd:00-setup TypeScript microservice with NestJS

# Add language standards
/add-typescript-best-practices

# Add formatting standards
/setup-code-formating

# Start feature development
/sdd:01-research "user authentication feature"
```

### With Reflexion (Quality Loop)

```bash
# Establish standards
/add-typescript-best-practices

# Implement feature
> claude "create REST API for product catalog"

# Review against standards
/critique

# Memorize project-specific patterns
/memorize --section="TypeScript Patterns"
```

### With Code Review

```bash
# Standards in place
/add-typescript-best-practices

# Make changes
> claude "add pagination to product listing endpoint"

# Review against CLAUDE.md standards
/review-local-changes

# Standards violations will be flagged in review
```

### With MCP Tools

```bash
# Setup TypeScript standards
/add-typescript-best-practices

# Add documentation retrieval
/mcp:setup-context7-mcp

# Now when implementing features, Claude can:
# - Follow your TypeScript standards (from CLAUDE.md)
# - Look up library documentation (from Context7)
> claude "implement form validation using zod"
```

## Common Patterns

### Before Starting Any TypeScript Project

```bash
claude /init
/sdd:00-setup [your tech stack description]
/add-typescript-best-practices
/setup-code-formating
```

### Before Major Feature Implementation

```bash
# Ensure standards are current
cat CLAUDE.md | grep "Code Style"

# If missing, add them
/add-typescript-best-practices
```

### During Code Review Preparation

```bash
# Self-review against standards
/reflect "check TypeScript best practices compliance"

# Fix any issues before submitting PR
> claude "address the TypeScript issues identified"
```

### When Onboarding New Team Member

Share with new team members:

1. Pull the repository (includes CLAUDE.md)
2. Review CLAUDE.md for coding standards
3. Standards automatically apply to their Claude sessions

## Troubleshooting

### Standards Not Being Followed

If Claude isn't following the established standards:

1. Verify CLAUDE.md exists and contains the standards
2. Check if CLAUDE.md is in the project root
3. Re-run `/add-typescript-best-practices` if needed
4. Explicitly reference standards: "follow the TypeScript guidelines in CLAUDE.md"

### Conflicting Guidelines

If your project has specific requirements that conflict with default guidelines:

1. Run the command to get the base guidelines
2. Modify CLAUDE.md to reflect your project's actual standards
3. Commit the customized CLAUDE.md

### Need More Language Support

Currently, the plugin supports TypeScript. For other languages:

1. Use the TypeScript command as a template
2. Manually add similar sections for your language to CLAUDE.md
3. Watch for future plugin updates with additional language support
