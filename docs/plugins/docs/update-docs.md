# /update-docs - Documentation Update

Comprehensive documentation update command that analyzes your project, identifies documentation needs, and creates or updates documentation following best practices.

- Purpose - Maintain accurate, useful project documentation
- Output - Updated README files, API docs, JSDoc comments, and guides

```bash
/update-docs ["target directory or documentation type"]
```

## Arguments

Optional target specification:

- **Directory path** (e.g., `src/auth/`) - Focus documentation updates on specific module
- **Documentation type** (e.g., `api`, `guides`, `readme`, `jsdoc`) - Target specific documentation category
- **No argument** - Full project documentation assessment and update

## How It Works

1. **Codebase Analysis**: Discovers project structure and existing documentation
   - Inventories all documentation files (README, docs/, API specs)
   - Checks for generated documentation (OpenAPI, GraphQL schemas)
   - Identifies JSDoc/TSDoc coverage
   - Maps project frameworks and tools in use

2. **User Journey Mapping**: Identifies critical documentation paths
   - Developer onboarding flow
   - API consumption journey
   - Feature usage patterns
   - Troubleshooting scenarios

3. **Gap Analysis**: Evaluates documentation health
   - High-impact gaps (missing setup instructions, undocumented APIs)
   - Quality assessment (freshness, accuracy, discoverability)
   - Duplication detection
   - Low-value content identification

4. **Strategic Updates**: Implements prioritized improvements
   - Fixes critical onboarding blockers first
   - Updates outdated examples and broken links
   - Adds missing API examples for common use cases
   - Creates module navigation READMEs

5. **Validation**: Ensures documentation quality
   - Tests code examples
   - Verifies links work
   - Confirms documentation serves real user needs

## Documentation Types Updated

**README Files:**

- **Project root README** - Quick start, overview, key links
- **Module READMEs** - Purpose statement, key exports, minimal usage example
- **Feature READMEs** - Navigation aid for complex feature directories

**API Documentation:**

- **OpenAPI/Swagger** - REST API specifications from code annotations
- **GraphQL schemas** - Type definitions and query documentation
- **Endpoint examples** - Request/response samples with realistic data

**Code Documentation:**

- **JSDoc/TSDoc** - Function contracts for complex business logic
- **Inline comments** - Non-obvious implementation decisions
- **Type definitions** - Complex interfaces and type aliases

**Guides and References:**

- **Getting started** - Fastest path to first success
- **How-to guides** - Task-oriented problem-solving docs
- **Troubleshooting** - Common problems with proven solutions
- **Architecture decisions** - When they affect user experience

## Usage Examples

```bash
# Full project documentation update
> /update-docs

# Update API documentation after adding new endpoints
> claude "add /api/v2/subscriptions endpoint"
> /update-docs api

# Document a specific module after changes
> /update-docs src/payments/

# Focus on README files only
> /update-docs readme

# Update JSDoc comments for complex business logic
> /update-docs jsdoc
```

## Quality Gates

The command enforces documentation quality through validation:

**Before Publishing:**

- All code examples tested and working
- Links verified (no 404s)
- Document purpose clearly stated
- Audience and prerequisites identified
- No duplication of generated docs
- Maintenance plan established

**Success Metrics:**

- Users complete common tasks without asking questions
- Issues contain more bug reports, fewer "how do I...?" questions
- Documentation is referenced in code reviews and discussions
- New contributors can get started independently
