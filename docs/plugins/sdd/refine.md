# Refining Specifications and Code

Guide for handling requirement changes at different stages of the SDD workflow.

## During Planning

When the specification needs adjustment after `/plan` completes:

### Option A: Pass the change directly

```bash
/plan --refine <requirement change>
```

The agent incorporates your change and re-runs affected stages.

**Examples:**

```bash
# Change authentication strategy
/plan --refine Use session-based auth instead of JWT

# Add a constraint the agent missed
/plan --refine The API must support pagination with cursor-based navigation, not offset

# Narrow the scope
/plan --refine Remove the admin dashboard from this task, we will handle it separately
```

### Option B: Edit the spec, then refine

1. Edit the task file in `.specs/tasks/todo/`
2. Add `//` comments to lines that need clarification
3. Run `/plan --refine`

The agent detects your edits, identifies the earliest modified section, and re-runs all stages from that point onward. Earlier sections remain unchanged.

**Example:** The agent planned a REST API, but you need GraphQL. Open the task file and edit:

```markdown
## Architecture Overview

// Change this to use GraphQL with Apollo Server instead of REST
- REST API with Express routes for CRUD operations
- PostgreSQL with Prisma ORM
```

Then run `/plan --refine`. The agent re-runs from architecture synthesis onward, producing new implementation steps for GraphQL while preserving the research and business analysis stages.

### What `--refine` compares

By default, `--refine` diffs local (unstaged) changes against staged changes. Both `/plan` and `/implement` stage their output at the end, so any manual edits you make afterward appear as unstaged changes.

To compare against the last commit instead, specify it: `/plan --refine compare with last commit`.

## After Implementation

When requirements change after `/implement` completes, choose based on the scope of the change:

### Small code adjustments

Edit the code directly, then run:

```bash
/implement --refine
```

The agent detects your changes, maps them to implementation steps, and aligns the rest of the codebase. If the judge passes your fix, it is accepted as-is. If it fails, the agent adjusts surrounding code to match your intent.

**Examples:**

```bash
# You fixed a validation bug in the controller — agent updates related tests and error messages
vi src/controllers/users.ts
/implement --refine

# You replaced bcrypt with argon2 in the auth service — agent aligns password checks elsewhere
vi src/services/auth.ts
/implement --refine

# You changed the database column name from `userName` to `username` — agent propagates across migrations, models, and queries
vi src/models/user.ts
/implement --refine
```

### Minor tweaks and polish

If the implementation is done and you need small refinements — renaming, formatting, minor behavior changes — run `/clear` (or re-open Claude Code) and work with agent as usual. No need to re-enter the SDD workflow.

**Examples:**

- Adjusting log messages or error text
- Renaming a local variable for clarity
- Tweaking CSS spacing or colors
- Adding a missing `console.log` for debugging

### Major requirement changes

If requirements changed substantially, create a new task:

```bash
/sdd:add-task "Refactor authentication implementation"
/sdd:plan
# /clear (or re-open Claude Code)
/sdd:implement
```

Re-running `/implement --refine` on large changes is less reliable than a fresh planning cycle. A new task produces a clean specification, proper architecture analysis, and accurate implementation steps.

**Examples of changes that warrant a new task:**

- Switching from a monolith to microservices
- Replacing the database engine (e.g., PostgreSQL to MongoDB)
- Changing the authentication model from API keys to OAuth2 with SSO
- Adding a real-time collaboration feature that was never in scope

## Walkthrough: Iterating on an Authentication Feature

A realistic sequence showing how refinement fits into the workflow:

```bash
# 1. Create and plan the task
/sdd:add-task "Add JWT authentication middleware"
/sdd:plan

# 2. Review the spec — agent chose HS256, but you need RS256
/plan --refine Use RS256 with rotating key pairs instead of HS256

# 3. Clear context, then implement
/clear
/sdd:implement

# 4. Review the code — token expiry is 1 hour, you want 15 minutes
vi src/config/auth.ts   # change TOKEN_EXPIRY to 900
/implement --refine     # agent updates tests and documentation to match

# 5. Product feedback: "Add refresh tokens"
# This is a significant scope addition — create a new task
/sdd:add-task "Add refresh token rotation for JWT auth"
/sdd:plan
/clear
/sdd:implement
```
