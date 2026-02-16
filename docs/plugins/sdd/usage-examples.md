# SDD Plugin - Usage Examples

Real-world scenarios demonstrating the effective use of the Spec-Driven Development plugin across various project types and complexity levels.

## Examples

### Simple Feature Implementation

**Scenario**: Adding a basic user profile feature to an existing application.

```bash
# Step 1: Create draft task
/sdd:add-task "Add user profile view and edit functionality with name, email, and avatar"

# Step 2: Plan — research, analyze, decompose, parallelize, verify
/sdd:plan @.specs/tasks/draft/add-user-profile.feature.md

# Step 3: Review specification (optional but recommended)
# Edit .specs/tasks/todo/add-user-profile.feature.md if needed
# Re-run planning for only affected sections:
/sdd:plan @.specs/tasks/todo/add-user-profile.feature.md --refine

# Step 4: Implement
/sdd:implement @.specs/tasks/todo/add-user-profile.feature.md

# Step 5: Commit and create PR
/git:commit
/git:create-pr
```

**What happens during `/sdd:plan`**:

1. `researcher` agent gathers relevant resources and creates a skill file
2. `code-explorer` agent identifies affected files and integration points
3. `business-analyst` agent refines description and creates acceptance criteria
4. `software-architect` agent synthesizes architecture overview
5. `tech-lead` agent decomposes into implementation steps with risks
6. `team-lead` agent parallelizes steps for efficient execution
7. `qa-engineer` agent defines verification rubrics for each step
8. Task file moved from `draft/` to `todo/`

**What happens during `/sdd:implement`**:

1. Task moved from `todo/` to `in-progress/`
2. Each step executed by `sdd:developer` agent
3. Critical steps verified by judge agents (panel of 2 for critical artifacts)
4. Definition of Done items verified
5. Task moved from `in-progress/` to `done/`

---

### Quick Fix with Minimal Planning

**Scenario**: A simple bug fix where full analysis is overkill.

```bash
# Create the task
/sdd:add-task "Fix null pointer in user service when email is empty"

# Fast planning — only business analysis + decomposition, lower quality bar
/sdd:plan @.specs/tasks/draft/fix-null-pointer-user-service.bug.md --fast

# Implement without judge verification for speed
/sdd:implement @.specs/tasks/todo/fix-null-pointer-user-service.bug.md --skip-judges
```

The `--fast` flag sets `--target-quality 3.0 --max-iterations 1 --included-stages "business analysis,decomposition,verifications"`, skipping research, codebase analysis, architecture synthesis, and parallelization.

---

### Complex Feature with High Quality Gates

**Scenario**: Implementing a multi-tenant billing system with Stripe integration.

```bash
# Brainstorm the approach first
/sdd:brainstorm We need to add billing capabilities for our B2B SaaS. Organizations should have subscription plans, usage tracking, and invoice generation.

# Create the task with clear scope
/sdd:add-task "Implement multi-tenant billing with hybrid pricing and Stripe integration"

# High-quality planning with human review at each phase
/sdd:plan @.specs/tasks/draft/implement-billing-stripe.feature.md --target-quality 4.5 --human-in-the-loop 2,3,4,5,6
```

**Expected planning flow with human-in-the-loop**:

```
Phase 2a: Research complete → Judge 2a: 4.6/5.0 ✅ PASS
Phase 2b: Codebase analysis → Judge 2b: 4.3/5.0 ✅ PASS
Phase 2c: Business analysis → Judge 2c: 4.5/5.0 ✅ PASS

🔍 Human Review Checkpoint - Phase 2
Review acceptance criteria and scope...
> Continue? [Y/n/feedback]: Y

Phase 3: Architecture synthesis → Judge 3: 4.7/5.0 ✅ PASS

🔍 Human Review Checkpoint - Phase 3
Review architecture decisions...
> Continue? [Y/n/feedback]: Use Stripe as source of truth, option A from research

Phase 4: Decomposition → Judge 4: 4.5/5.0 ✅ PASS
...continues...
```

After reviewing and refining the specification:

```bash
# Implement with stricter thresholds and human review on critical steps
/sdd:implement @.specs/tasks/todo/implement-billing-stripe.feature.md --target-quality 4.5 --human-in-the-loop 2,4,6
```

---

### Iterative Specification Refinement

**Scenario**: The generated specification needs corrections after review.

```bash
# Initial planning
/sdd:plan @.specs/tasks/draft/add-notification-system.feature.md

# Review the generated specification
# Edit .specs/tasks/todo/add-notification-system.feature.md:
#   - Fix architecture section to use WebSockets instead of polling
#   - Add // comment: "should support both email and push notifications"

# Re-run only affected stages (architecture and below)
/sdd:plan @.specs/tasks/todo/add-notification-system.feature.md --refine

# Detects: Architecture Overview section changed
# Skips: research, codebase analysis, business analysis
# Runs: architecture synthesis, decomposition, parallelize, verifications
```

The `--refine` flag uses git diff to detect which sections were modified and only re-runs stages from the earliest changed section onward (top-to-bottom propagation).

---

### Resuming Interrupted Implementation

**Scenario**: Implementation was interrupted mid-way and needs to continue.

```bash
# Initial implementation starts
/sdd:implement @.specs/tasks/todo/add-validation.feature.md

# ... interrupted after Step 3 ...

# Resume from where it left off
/sdd:implement add-validation.feature.md --continue

# Output:
# Found: Step 1 [DONE], Step 2 [DONE], Step 3 [DONE]
# Verifying Step 3 artifacts... Judge: 4.3/5.0 PASS ✅
# Resuming from Step 4...
```

---

### Manual Fix with Re-verification

**Scenario**: After implementation, you manually fix a file and want to re-verify.

```bash
# Initial implementation complete but you want to improve something
# Manually edit src/validation/validation.service.ts

# Re-verify from the affected step onward
/sdd:implement add-validation.feature.md --refine

# Output:
# Detecting changed project files...
# Changed: src/validation/validation.service.ts (modified)
# Maps to: Step 2 (Create ValidationService)
# Step 2: Judge PASS ✅ — The user's fix is good
# Step 3: Judge PASS ✅ — no cascading issues
# Step 4: Judge FAIL — Launching the implementation agent to align...
# Step 4: Judge PASS ✅ (after fix)
```

---

### Task Dependencies

**Scenario**: Multiple related tasks that should be implemented in order.

```bash
# Create tasks with dependencies
/sdd:add-task "Implement user authentication service"
# Created: .specs/tasks/draft/implement-user-auth-service.feature.md

/sdd:add-task "Add role-based access control" @.specs/tasks/draft/implement-user-auth-service.feature.md
# Created: .specs/tasks/draft/add-role-based-access-control.feature.md
# Depends on: implement-user-auth-service.feature.md

# Plan and implement in order
/sdd:plan @.specs/tasks/draft/implement-user-auth-service.feature.md
/sdd:implement
/git:commit

/sdd:plan @.specs/tasks/draft/add-role-based-access-control.feature.md
/sdd:implement
/git:commit

/git:create-pr
```

---

### Idea Generation Before Task Creation

**Scenario**: Exploring approaches before committing to a task.

```bash
# Quick diverse idea generation
/sdd:create-ideas "caching strategies for a real-time product catalog"

# Output: 5 diverse ideas with probability scores
# Pick the most promising approach

# Deeper exploration with collaborative dialogue
/sdd:brainstorm "We need real-time features but are not sure about WebSockets vs. Server-Sent Events"

# After brainstorm produces a design document:
/sdd:add-task "Implement real-time stock updates using WebSocket connections"
/sdd:plan @.specs/tasks/draft/implement-realtime-stock-updates.feature.md
/sdd:implement
```

---

### Skipping Specific Planning Stages

**Scenario**: You already know the technology and don't need research.

```bash
# Skip research phase — you're familiar with the stack
/sdd:plan @.specs/tasks/draft/add-pagination.feature.md --skip research

# Skip research and codebase analysis — A small, isolated change
/sdd:plan @.specs/tasks/draft/fix-date-format.bug.md --skip research,"codebase analysis"

# Only run business analysis and decomposition
/sdd:plan @.specs/tasks/draft/update-config.chore.md --included-stages "business analysis,decomposition"
```

---

### Different Quality Thresholds

**Scenario**: Balancing speed vs quality for different types of work.

```bash
# Critical production API — highest quality
/sdd:plan @.specs/tasks/draft/payment-api.feature.md --target-quality 4.5 --max-iterations 5
/sdd:implement --target-quality 4.5 --max-iterations unlimited

# Internal tool — standard quality
/sdd:plan @.specs/tasks/draft/admin-dashboard.feature.md
/sdd:implement

# Quick prototype — minimum viable quality
/sdd:plan @.specs/tasks/draft/poc-feature.feature.md --fast
/sdd:implement --target-quality 3.5 --max-iterations 1

# Different thresholds for standard vs critical components
/sdd:implement --target-quality 3.5,4.5
# Standard components verified at 3.5, critical at 4.5
```

---

## Integration with Other Plugins

### Full Feature Cycle with Git

```bash
# 1. Create and plan the task
/sdd:add-task "Add user notification preferences with email digest settings"
/sdd:plan @.specs/tasks/draft/add-notification-preferences.feature.md

# 2. Review specification, make edits if needed
# 3. Re-plan if you made edits
/sdd:plan @.specs/tasks/todo/add-notification-preferences.feature.md --refine

# 4. Implement
/sdd:implement

# 5. Commit and create PR
/git:commit
/git:create-pr
```

### Research-Heavy Features

```bash
# For unfamiliar technology — brainstorm first
/sdd:brainstorm "We need real-time features, but I'm not sure about WebSockets vs. Server-Sent Events"

# The research phase in /sdd:plan will:
# - Launch researcher agent to compare libraries
# - Analyze browser support and scalability
# - Check existing codebase patterns
# - Create a reusable skill document

/sdd:add-task "Add real-time collaboration with WebSocket support"
/sdd:plan @.specs/tasks/draft/add-realtime-collaboration.feature.md
```

---

## Best Practices Summary

### When to Use Full SDD Workflow

- New features with unclear requirements
- Complex integrations with multiple systems
- Features affecting multiple parts of the codebase
- Public APIs or features with external consumers
- Refactoring projects with high regression risk

### When to Use Abbreviated Workflow

- Simple bug fixes: use `--fast` for planning, `--skip-judges` for implementation
- Well-understood features: use `--skip research` if tech stack is familiar
- Quick prototypes: use `--one-shot` for minimal planning

### Common Patterns

1. **Brainstorm before task creation** — Use `/sdd:brainstorm` for vague requirements, `/sdd:create-ideas` for quick diverse options
2. **Review specifications** — Edit the task file and use `--refine` to propagate changes
3. **Decompose large tasks** — Create multiple tasks with dependencies using `/sdd:add-task`
4. **Use human-in-the-loop for critical decisions** — Architecture and decomposition phases benefit most from human review
5. **Continue interrupted work** — Use `--continue` to resume implementation, `--refine` after manual fixes

### Anti-Patterns to Avoid

1. Skipping specification reviews for complex features
2. Ignoring high-risk task warnings in decomposition
3. Using `--skip-judges` for production-critical code
4. Creating tasks that are too large — decompose into smaller dependent tasks
5. Not using `--refine` after editing specifications (re-running a full plan is wasteful)
