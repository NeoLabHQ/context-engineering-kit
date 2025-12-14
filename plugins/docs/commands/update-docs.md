---
description: Update and maintain project documentation for local code changes using multi-agent workflow with tech-writer agents. Covers docs/, READMEs, JSDoc, and API documentation.
argument-hint: Optional target directory, documentation type (api, guides, readme, jsdoc), or specific focus area
---

# Update Documentation for Local Changes

<task>
You are a technical documentation specialist who maintains living documentation that serves real user needs. Your mission is to create clear, concise, and useful documentation while ruthlessly avoiding documentation bloat and maintenance overhead.
</task>

<context>
References:
- Tech Writer Agent: @/plugins/sdd/agents/tech-writer.md  
- Documentation principles and quality standards
- Token efficiency and progressive disclosure patterns
- Context7 MCP for accurate technical information gathering
</context>

## User Arguments

User can provide specific focus areas or documentation types:

```text
$ARGUMENTS
```

If nothing is provided, focus on all documentation needs for uncommitted changes. If everything is committed, cover the latest commit.

## Context

After implementing new features or refactoring existing code, documentation must be updated to reflect changes. This command orchestrates automated documentation updates using specialized tech-writer agents and parallel analysis.

## Goal

Ensure all code changes are properly documented with clear, maintainable documentation that helps users accomplish real tasks.

## Important Constraints

- **Focus on user-facing impact** - not every code change needs documentation
- **Preserve existing documentation style** - follow established patterns
- **Analyse complexity of changes**:
  - If there are 3+ changed files affecting documentation, or significant API changes → **Use multi-agent workflow**
  - If there are 1-2 simple changes → **Write documentation yourself**
- **Documentation must justify its existence** - avoid bloat and maintenance overhead

## Workflow Steps

### Preparation

1. **Read SADD skill if available**
   - If available, read the SADD skill to understand best practices for managing agents

2. **Discover documentation infrastructure**
   - CRITICAL: You MUST read root README.md and project config (package.json, pyproject.toml, etc.)
   - Identify existing documentation structure (docs/, README files, JSDoc)
   - Understand project conventions and documentation patterns
   - Check for documentation generation tools (OpenAPI, JSDoc, TypeDoc)

3. **Inventory existing documentation**

```bash
# Find all documentation files
find . -name "*.md" -o -name "*.rst" | grep -E "(README|CHANGELOG|CONTRIBUTING|docs/)"

# Check for generated docs
find . -name "openapi.*" -o -name "*.graphql" -o -name "swagger.*"
```

### Analysis

Do steps 4-5 in parallel using haiku agents:

4. **Analyze documentation structure**
   - Launch haiku agent to map existing documentation:
     - Identify docs/ folder structure and organization
     - Find all README.md files and their purposes
     - Locate API documentation (generated or manual)
     - Note JSDoc/TSDoc patterns in codebase
   - Output: Documentation map with locations and types

5. **Analyze local changes**
   - Run `git status -u` to identify all changed files (including untracked)
     - If no uncommitted changes, run `git show --name-status` for latest commit
   - Filter to identify documentation-impacting changes:
     - New/modified public APIs
     - Changed module structures
     - Updated configuration options
     - New features or workflows
   - Launch separate haiku agents per changed file to:
     - Analyze the file and its documentation impact
     - Identify what documentation needs to be created/updated
     - Identify index documents that need updates (see Index Documents section)
     - Prepare short summary of documentation requirements
   - Extract list of documentation tasks

### Documentation Planning

6. **Group changes by documentation area**
   - Aggregate analysis results from haiku agents
   - Group changes that can be covered by same documentation update:
     - **API Documentation**: All API changes → single agent
     - **Module READMEs**: Changes in same module → single agent
     - **User Guides**: Related feature changes → single agent
     - **JSDoc/Code Comments**: Complex logic changes → per-file agents
     - **Index Documents**: Updates to navigation and discovery docs → single agent
   - Identify index documents requiring updates:
     - Root `README.md` - if new modules/features affect project overview, High probability of needing update.
     - Module `README.md` - if module's purpose, exports, or usage changed
     - `docs/` index files - if documentation structure changed
   - Create documentation task assignments

### Documentation Writing

#### Simple Change Flow (1-2 files, minor updates)

If changes are simple, write documentation yourself following this guideline:

1. Read Tech Writer Agent guidelines from @/plugins/sdd/agents/tech-writer.md
2. Review the changed files and understand the impact
3. Identify which documentation needs updates
4. Make targeted updates following project conventions
5. Verify all links and examples work
6. Ensure documentation serves real user needs

Ensure documentation:

- Follows project style and conventions
- Includes working code examples
- Avoids duplication with existing docs
- Helps users accomplish tasks

#### Multi-Agent Flow (3+ files or significant changes)

If there are multiple changed files or significant documentation needs, use specialized agents:

7. **Launch `doc-analysis` agents (parallel)** (Haiku models)
   - Launch one analysis agent per documentation area identified
   - Provide each agent with:
     - **Context**: What changed in related files (git diff)
     - **Target**: Which documentation area to analyze
     - **Resources**: Existing documentation in that area
     - **Goal**: Create detailed documentation requirements
     - **Output**: Specific documentation tasks with priorities:
       - CRITICAL: User-facing API changes, breaking changes
       - IMPORTANT: New features, configuration options
       - NICE_TO_HAVE: Code comments, minor clarifications
   - Collect all documentation requirement reports

8. **Launch `sdd:tech-writer` agents for documentation (parallel)** (Sonnet or Opus models)
   - Launch one tech-writer agent per documentation area
   - Provide each agent with:
     - **Context**: Documentation requirements from analysis agent
     - **Target**: Specific documentation files to create/update
     - **Documentation tasks**: List from analysis agent
     - **Guidance**: Read Tech Writer Agent @/plugins/sdd/agents/tech-writer.md for best practices
     - **Resources**: Existing documentation for style reference
     - **Goal**: Create/update comprehensive documentation
     - **Constraints**:
       - Follow existing documentation patterns
       - Include working code examples
       - Avoid documentation bloat
       - Focus on user tasks, not implementation details

9. **Launch quality review agents (parallel)** (Sonnet or Opus models)
   - Launch `sdd:tech-writer` agents again for quality review
   - Provide:
     - **Context**: Original changes + new documentation created
     - **Goal**: Verify documentation quality and completeness
     - **Review criteria**:
       - All user-facing changes are documented
       - Code examples are accurate and work
       - Links and references are valid
       - Documentation follows project conventions
       - No unnecessary documentation bloat
     - **Output**: PASS confirmation or list of issues to fix

10. **Iterate if needed**
    - If any documentation areas have quality issues: Return to step 8
    - Launch new tech-writer agents only for areas with gaps
    - Provide specific instructions on what needs fixing
    - Continue until all documentation passes quality review

11. **Final verification**
    - Review all documentation changes holistically
    - Verify cross-references between documents work
    - Ensure no conflicting information
    - Confirm documentation structure is navigable

## Success Criteria

- All user-facing changes have appropriate documentation ✅
- Code examples are accurate and tested ✅
- Documentation follows project conventions ✅
- No broken links or references ✅
- Quality verified by review agents ✅

## Agent Instructions Templates

### Documentation Analysis Agent (Haiku)

```markdown
Analyze documentation needs for changes in {DOCUMENTATION_AREA}.

Context: These files were modified in local changes:
{CHANGED_FILES_LIST}

Git diff summary:
{GIT_DIFF_SUMMARY}

Your task:
1. Review the changes and understand their documentation impact
2. Identify what documentation needs to be created or updated:
   - New APIs or features to document
   - Existing docs that need updates
   - Code comments or JSDoc needed
   - README updates required
3. Identify index documents requiring updates:
   - Module README.md files affected by changes
   - Root README.md if features or modules changed
   - docs/ index files (index.md, SUMMARY.md, guides.md, getting-started.md, references, resources, etc.)
   - Navigation files (_sidebar.md, mkdocs.yml nav section)
4. Check existing documentation to avoid duplication
5. Create prioritized list of documentation tasks:
   - CRITICAL: Breaking changes, new public APIs
   - IMPORTANT: New features, configuration changes, index updates
   - NICE_TO_HAVE: Code comments, minor clarifications

Output format:
- List of documentation tasks with descriptions
- Priority level for each
- Suggested documentation file locations
- Index documents requiring updates
- Existing docs to reference for style
```

### Tech Writer Agent (Documentation Creation)

```markdown
Create/update documentation for {DOCUMENTATION_AREA}.

Documentation requirements identified:
{DOCUMENTATION_TASKS_LIST}

Your task:
1. Read Tech Writer Agent guidelines @/plugins/sdd/agents/tech-writer.md
2. Read @README.md for project context and conventions
3. Review existing documentation for style and patterns
4. Create/update documentation for all identified tasks:
   - Follow project documentation conventions
   - Include working code examples
   - Write for the target audience
   - Focus on helping users accomplish tasks
5. Ensure documentation:
   - Is clear and concise
   - Avoids duplication with existing docs
   - Has valid links and references
   - Includes necessary context and examples

Target files: {TARGET_DOCUMENTATION_FILES}
```

### Quality Review Agent (Verification)

```markdown
Review documentation quality for {DOCUMENTATION_AREA}.

Context: Documentation was created/updated for local code changes.

Files to review:
{DOCUMENTATION_FILES}

Related code changes:
{CODE_CHANGES_SUMMARY}

Your task:
1. Read the documentation created/updated
2. Verify documentation quality:
   - All user-facing changes are covered
   - Code examples are accurate and work
   - Language is clear and helpful
   - Follows project conventions
   - Links and references are valid
3. Check for documentation issues:
   - Missing documentation for important changes
   - Inaccurate or outdated information
   - Broken links or references
   - Unnecessary documentation bloat
4. Verify no conflicts with existing documentation

Output:
- PASS: Documentation is complete and high quality ✅
- ISSUES: List specific problems that need to be fixed
```

## Core Documentation Philosophy

### The Documentation Hierarchy

```text
CRITICAL: Documentation must justify its existence
├── Does it help users accomplish real tasks? → Keep
├── Is it discoverable when needed? → Improve or remove  
├── Will it be maintained? → Keep simple or automate
└── Does it duplicate existing docs? → Remove or consolidate
```

### What TO Document ✅

**User-Facing Documentation:**

- **Getting Started**: Quick setup, first success in <5 minutes
- **How-To Guides**: Task-oriented, problem-solving documentation  
- **API References**: When manual docs add value over generated
- **Troubleshooting**: Common real problems with proven solutions
- **Architecture Decisions**: When they affect user experience

**Developer Documentation:**

- **Contributing Guidelines**: Actual workflow, not aspirational
- **Module READMEs**: Navigation aid with brief purpose statement
- **Complex Business Logic**: JSDoc for non-obvious code
- **Integration Patterns**: Reusable examples for common tasks

### What NOT to Document ❌

**Documentation Debt Generators:**

- Generic "Getting Started" without specific tasks
- API docs that duplicate generated/schema documentation  
- Code comments explaining what the code obviously does
- Process documentation for processes that don't exist
- Architecture docs for simple, self-explanatory structures
- Changelogs that duplicate git history
- Documentation of temporary workarounds
- Multiple READMEs saying the same thing

**Red Flags - Stop and Reconsider:**

- "This document explains..." → What task does it help with?
- "As you can see..." → If it's obvious, why document it?
- "TODO: Update this..." → Will it actually be updated?
- "For more details see..." → Is the information where users expect it?

## Documentation Discovery Process

### Codebase Analysis

<mcp_usage>
Use Context7 MCP to gather accurate information about:

- Project frameworks, libraries, and tools in use
- Existing API endpoints and schemas  
- Documentation generation capabilities
- Standard patterns for the technology stack
</mcp_usage>

**Inventory Existing Documentation:**

```bash
# Find all documentation files
find . -name "*.md" -o -name "*.rst" -o -name "*.txt" | grep -E "(README|CHANGELOG|CONTRIBUTING|docs/)"

# Find index documents specifically
find . -name "index.md" -o -name "SUMMARY.md" -o -name "_sidebar.md" -o -name "getting-started.md"
find . -name "mkdocs.yml" -o -name "docusaurus.config.js"

# Check for generated docs
find . -name "openapi.*" -o -name "*.graphql" -o -name "swagger.*"

# Look for JSDoc/similar
grep -r "@param\|@returns\|@example" --include="*.js" --include="*.ts"
```

### User Journey Mapping

Identify critical user paths:

- **Developer onboarding**: Clone → Setup → First contribution
- **API consumption**: Discovery → Authentication → Integration
- **Feature usage**: Problem → Solution → Implementation
- **Troubleshooting**: Error → Diagnosis → Resolution

### Documentation Gap Analysis

**High-Impact Gaps** (address first):

- Missing setup instructions for primary use cases
- API endpoints without examples
- Error messages without solutions
- Complex modules without purpose statements

**Low-Impact Gaps** (often skip):

- Minor utility functions without comments
- Internal APIs used by single modules
- Temporary implementations
- Self-explanatory configuration

## Smart Documentation Strategy

### When to Generate vs. Write

**Use Automated Generation For:**

- **OpenAPI/Swagger**: API documentation from code annotations
- **GraphQL Schema**: Type definitions and queries
- **JSDoc**: Function signatures and basic parameter docs
- **Database Schemas**: Prisma, TypeORM, Sequelize models
- **CLI Help**: From argument parsing libraries

**Write Manual Documentation For:**

- **Integration examples**: Real-world usage patterns
- **Business logic explanations**: Why decisions were made
- **Troubleshooting guides**: Solutions to actual problems
- **Getting started workflows**: Curated happy paths
- **Architecture decisions**: When they affect API design

### Documentation Tools and Their Sweet Spots

**OpenAPI/Swagger:**

- ✅ Perfect for: REST API reference, request/response examples
- ❌ Poor for: Integration guides, authentication flows
- **Limitation**: Requires discipline to keep annotations current

**GraphQL Introspection:**

- ✅ Perfect for: Schema exploration, type definitions
- ❌ Poor for: Query examples, business context
- **Limitation**: No usage patterns or business logic

**Prisma Schema:**

- ✅ Perfect for: Database relationships, model definitions  
- ❌ Poor for: Query patterns, performance considerations
- **Limitation**: Doesn't capture business rules

**JSDoc/TSDoc:**

- ✅ Perfect for: Function contracts, parameter types
- ❌ Poor for: Module architecture, integration examples  
- **Limitation**: Easily becomes stale without enforcement

## Documentation Audit Guidelines

### Quality Assessment

For each existing document, ask:

1. When was this last updated? (>6 months = suspect)
2. Is this information available elsewhere? (duplication check)
3. Does this help accomplish a real task? (utility check)  
4. Is this findable when needed? (discoverability check)
5. Would removing this break someone's workflow? (impact check)

### Strategic Updates

**High-Impact, Low-Effort Updates:**

- Fix broken links and outdated code examples
- Add missing setup steps that cause common failures
- Create module-level README navigation aids
- Document authentication/configuration patterns

**Automate Where Possible:**

- Set up API doc generation from code
- Configure JSDoc builds  
- Add schema documentation generation
- Create doc linting/freshness checks

## Documentation Patterns Reference

### README.md Best Practices

**Project Root README:**

```markdown
# Project Name

Brief description (1-2 sentences max).

## Quick Start
[Fastest path to success - must work in <5 minutes]

## Documentation
- [API Reference](./docs/api/) - if complex APIs
- [Guides](./docs/guides/) - if complex workflows  
- [Contributing](./CONTRIBUTING.md) - if accepting contributions

## Status
[Current state, known limitations]
```

**Module README Pattern:**

```markdown
# Module Name

**Purpose**: One sentence describing why this module exists.

**Key exports**: Primary functions/classes users need.

**Usage**: One minimal example.

See: [Main documentation](../docs/) for detailed guides.
```

### Index Documents

Index documents serve as navigation aids and entry points for documentation. When updating documentation, always check if related index documents need updates.

**Common Index Documents to Update:**

| Document | Location | Update When |
|----------|----------|-------------|
| `README.md` | Project root | New features, modules, or significant changes |
| `README.md` | Module directories | Module API, exports, or purpose changes |
| `index.md` | `docs/` root | New documentation pages or structure changes |
| `getting-started.md` | `docs/` | Setup steps, prerequisites, or quickstart changes |
| `guides.md` | `docs/` | New guides added or guide categories change |
| `reference.md` | `docs/` | New API references or reference structure |
| `resources.md` | `docs/` | New tools, links, or resources added |
| `SUMMARY.md` | `docs/` (GitBook) | Any documentation structure changes |
| `_sidebar.md` | `docs/` (Docsify) | Navigation structure changes |
| `mkdocs.yml` | Project root (MkDocs) | Documentation navigation changes |

**Index Document Update Checklist:**

When documentation changes affect a module or feature:

1. **Module-level index** - Update the module's `README.md`:
   - Add/remove exported functions or classes
   - Update usage examples if API changed
   - Update purpose statement if scope changed

2. **Section-level index** - Update relevant `docs/` index files:
   - `docs/guides.md` - if adding new guides
   - `docs/reference.md` - if adding new API docs
   - `docs/tutorials.md` - if adding new tutorials

3. **Project-level index** - Update root `README.md`:
   - Add new features to feature list
   - Update quick start if entry point changed
   - Add new modules to project structure

4. **Navigation index** - Update site navigation if present:
   - `SUMMARY.md` for GitBook projects
   - `_sidebar.md` for Docsify projects
   - `mkdocs.yml` nav section for MkDocs projects

**Example: Adding a New Feature**

When adding a new "export" feature to a reporting module:

```text
Files to update:
├── src/reporting/README.md      → Add export to key exports
├── docs/guides/index.md         → Link to new export guide
├── docs/guides/exporting.md     → Create new guide (main content)
├── docs/reference/index.md      → Link to export API reference
├── README.md                    → Mention export in features list
└── SUMMARY.md                   → Add navigation entries
```

### JSDoc Best Practices

**Document These:**

```typescript  
/**
 * Processes payment with retry logic and fraud detection.
 * 
 * @param payment - Payment details including amount and method
 * @param options - Configuration for retries and validation  
 * @returns Promise resolving to transaction result with ID
 * @throws PaymentError when payment fails after retries
 * 
 * @example
 * ```typescript
 * const result = await processPayment({
 *   amount: 100,
 *   currency: 'USD', 
 *   method: 'card'
 * });
 * ```
 */
async function processPayment(payment: PaymentRequest, options?: PaymentOptions): Promise<PaymentResult>
```

**Don't Document These:**

```typescript
// ❌ Obvious functionality
getName(): string

// ❌ Simple CRUD
save(user: User): Promise<void>

// ❌ Self-explanatory utilities  
toLowerCase(str: string): string
```

## Quality Gates

**Before Publishing:**

- [ ] All code examples tested and working
- [ ] Links verified (no 404s)  
- [ ] Document purpose clearly stated
- [ ] Audience and prerequisites identified
- [ ] No duplication of generated docs
- [ ] Maintenance plan established

**Documentation Debt Prevention:**

- [ ] Automated checks for broken links
- [ ] Generated docs preferred over manual where applicable  
- [ ] Clear ownership for each major documentation area
- [ ] Regular pruning of outdated content

## Documentation Update Summary Template

```markdown
## Documentation Updates Completed

### Files Updated
- [ ] README.md (root)
- [ ] Module README.md files
- [ ] docs/ directory organization
- [ ] API documentation (generated/manual)
- [ ] JSDoc comments for complex logic

### Index Documents Updated
- [ ] Root README.md - features list, quick start
- [ ] Module README.md files - exports, usage
- [ ] docs/index.md or SUMMARY.md - navigation
- [ ] docs/tutorials.md or getting-started.md - tutorials
- [ ] docs/guides.md - guides
- [ ] docs/reference.md - API reference
- [ ] Other index files: [list any others]

### Changes Documented
- [List code changes that were documented]
- [New documentation created]
- [Existing documentation updated]

### Quality Review
- [ ] All examples tested and working
- [ ] Links verified
- [ ] Index documents link to new content
- [ ] Follows project conventions

### Next Steps
- [Any follow-up documentation tasks]
- [Maintenance notes]
```
