# SDD Plugin - Usage Examples

Real-world scenarios demonstrating the effective use of the Spec-Driven Development plugin across various project types and complexity levels.

## Examples

### Simple Feature Implementation

**Scenario**: Adding a basic user profile feature to an existing application.

```bash
# Step 1: Create draft task
/add-task "Add user profile view and edit functionality with name, email, and avatar"

# Step 2: Plan — research, analyze, define acceptance criteria, architect, decompose
/plan-task @.specs/tasks/draft/add-user-profile.feature.md

# Step 3: Review specification (optional but recommended)
# Edit .specs/tasks/todo/add-user-profile.feature.md if needed
# Re-run planning for only affected sections:
/plan-task @.specs/tasks/todo/add-user-profile.feature.md --refine

# Step 4: Implement
/implement-task @.specs/tasks/todo/add-user-profile.feature.md

# Step 5: Commit and create PR
/commit
/create-pr
```

**What happens during `/plan-task`**:

Phases 2a, 2b and 2c run in parallel; Phase 3 and Phase 4 follow in order. Each is gated by its own judge.

1. **Phase 2a** — `researcher` agent gathers relevant resources and creates a skill file
2. **Phase 2b** — `code-explorer` agent identifies affected files and integration points
3. **Phase 2c** — `business-analyst` agent refines the description and writes the single `## Acceptance Criteria` section: checklist, regular checks, rubric, score definitions, test strategy and definition of done
4. **Phase 3** — `software-architect` agent synthesizes the architecture overview
5. **Phase 4** — `tech-lead` agent decomposes the work into per-step sub-task files under `.specs/sub-tasks/add-user-profile.feature/`, and groups them into independently verifiable phases with dependencies, parallel groups and a reviewer model per phase
6. Task file moved from `draft/` to `todo/` — the sub-task folder stays where it was written

**What happens during `/implement-task`**:

1. Task moved from `todo/` to `in-progress/`
2. Each step executed by its assigned agent, given the task file path and its own sub-task file path
3. At the end of every implementation phase, ONE `sdd:code-reviewer` reviews the whole phase at that phase's reviewer model, scoring only the criteria that phase lists as due
4. Definition of Done items verified
5. Task moved from `in-progress/` to `done/`

---

### Quick Fix with Minimal Planning

**Scenario**: A simple bug fix where full analysis is overkill.

```bash
# Create the task
/add-task "Fix null pointer in user service when email is empty"

# Fast planning — only business analysis + decomposition, lower quality bar
/plan-task @.specs/tasks/draft/fix-null-pointer-user-service.bug.md --fast

# Implement without phase reviews for speed
/implement-task @.specs/tasks/todo/fix-null-pointer-user-service.bug.md --skip-reviews
```

The `--fast` flag sets `--target-quality 3.0 --max-iterations 1 --included-stages "business analysis,decomposition"`, skipping research, codebase analysis and architecture synthesis. Judges still run, at the lowered threshold with a single retry. Use `--one-shot` for the same stage list with no judges at all.

---

### Complex Feature with High Quality Gates

**Scenario**: Implementing a multi-tenant billing system with Stripe integration.

```bash
# Brainstorm the approach first
/brainstorm We need to add billing capabilities for our B2B SaaS. Organizations should have subscription plans, usage tracking, and invoice generation.

# Create the task with clear scope
/add-task "Implement multi-tenant billing with hybrid pricing and Stripe integration"

# High-quality planning with human review at each phase
/plan-task @.specs/tasks/draft/implement-billing-stripe.feature.md --target-quality 4.5 --human-in-the-loop 2,3,4
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

🔍 Human Review Checkpoint - Phase 4
Review the sub-task files and the phase boundaries...
> Continue? [Y/n/feedback]: Y

Promote: draft/ → todo/
```

After reviewing and refining the specification:

```bash
# Implement with a stricter threshold and human review on the critical milestones
/implement-task @.specs/tasks/todo/implement-billing-stripe.feature.md --target-quality 4.5 --human-in-the-loop "Phase 2,Phase 4"
```

Note that `--human-in-the-loop` takes **implementation phase identifiers** here, not step numbers — the phase is the review unit.

---

### Iterative Specification Refinement

**Scenario**: The generated specification needs corrections after review.

```bash
# Initial planning
/plan-task @.specs/tasks/draft/add-notification-system.feature.md

# Review the generated specification
# Edit .specs/tasks/todo/add-notification-system.feature.md:
#   - Fix architecture section to use WebSockets instead of polling
#   - Add // comment: "should support both email and push notifications"

# Re-run only affected stages (architecture and below)
/plan-task @.specs/tasks/todo/add-notification-system.feature.md --refine

# Detects: Architecture Overview section changed
# Skips: research, codebase analysis, business analysis
# Runs: architecture synthesis, decomposition
```

The `--refine` flag uses git diff to detect which sections were modified and only re-runs stages from the earliest changed section onward (top-to-bottom propagation).

---

### Resuming Interrupted Implementation

**Scenario**: Implementation was interrupted mid-way and needs to continue.

```bash
# Initial implementation starts
/implement-task @.specs/tasks/todo/add-validation.feature.md

# ... interrupted midway through Phase 2 ...

# Resume from where it left off
/implement-task add-validation.feature.md --continue

# Output:
# Phase 1 [REVIEWED] — skipping
# Phase 2: 03-validation-service [DONE], 04-controller not started
# Resuming Phase 2 at step 04-controller...
# All Phase 2 steps complete → launching sdd:code-reviewer for Phase 2 (sonnet)
# Phase 2 combined_score: 4.3/5.0 PASS ✅ → marked [REVIEWED]
# Continuing with Phase 3...
```

`--continue` resolves state by **implementation phase, then step**: it resumes at the first phase marked neither `[REVIEWED]` nor `[REVIEWED-SKIPPED]`, finishes that phase's outstanding steps, then reviews it.

---

### Manual Fix with Re-verification

**Scenario**: After implementation, you manually fix a file and want to re-verify.

```bash
# Initial implementation complete but you want to improve something
# Manually edit src/validation/validation.service.ts

# Re-verify from the affected step onward
/implement-task add-validation.feature.md --refine

# Output:
# Detecting changed project files...
# Changed: src/validation/validation.service.ts (modified)
# Maps to: step 02-validation-service → Phase 1
# Phase 1: reviewer 4.4/5.0 PASS ✅ — The user's fix is good
# Phase 2: reviewer 4.2/5.0 PASS ✅ — no cascading issues
# Phase 3: reviewer 3.1/5.0 FAIL — blast radius: 1 step, local defect,
#          re-dispatching only 05-error-messages at its own model...
# Phase 3: reviewer 4.3/5.0 PASS ✅ (after fix)
```

`--refine` re-verifies at **phase** granularity: it maps the changed files to steps, finds the earliest implementation phase that owns one, and re-reviews that phase and every phase after it.

---

### Task Dependencies

**Scenario**: Multiple related tasks that should be implemented in order.

```bash
# Create tasks with dependencies
/add-task "Implement user authentication service"
# Created: .specs/tasks/draft/implement-user-auth-service.feature.md

/add-task "Add role-based access control" @.specs/tasks/draft/implement-user-auth-service.feature.md
# Created: .specs/tasks/draft/add-role-based-access-control.feature.md
# Depends on: implement-user-auth-service.feature.md

# Plan and implement in order
/plan-task @.specs/tasks/draft/implement-user-auth-service.feature.md
/implement-task
/commit

/plan-task @.specs/tasks/draft/add-role-based-access-control.feature.md
/implement-task
/commit

/create-pr
```

---

### Idea Generation Before Task Creation

**Scenario**: Exploring approaches before committing to a task.

```bash
# Quick diverse idea generation
/create-ideas "caching strategies for a real-time product catalog"

# Output: 5 diverse ideas with probability scores
# Pick the most promising approach

# Deeper exploration with collaborative dialogue
/brainstorm "We need real-time features but are not sure about WebSockets vs. Server-Sent Events"

# After brainstorm produces a design document:
/add-task "Implement real-time stock updates using WebSocket connections"
# produces @.specs/tasks/draft/implement-realtime-stock-updates.feature.md

/clear
/plan-task @.specs/tasks/draft/implement-realtime-stock-updates.feature.md

/clear
/implement-task @.specs/tasks/todo/implement-realtime-stock-updates.feature.md
```

---

### Skipping Specific Planning Stages

**Scenario**: You already know the technology and don't need research.

```bash
# Skip research phase — you're familiar with the stack
/plan-task @.specs/tasks/draft/add-pagination.feature.md --skip research

# Skip research and codebase analysis — A small, isolated change
/plan-task @.specs/tasks/draft/fix-date-format.bug.md --skip research,"codebase analysis"

# Only run business analysis and decomposition
/plan-task @.specs/tasks/draft/update-config.chore.md --included-stages "business analysis,decomposition"
```

---

### Different Quality Thresholds

**Scenario**: Balancing speed vs quality for different types of work.

```bash
# Critical production API — highest quality
/plan-task @.specs/tasks/draft/payment-api.feature.md --target-quality 4.5 --max-iterations 5
/implement-task --target-quality 4.5 --max-iterations unlimited

# Internal tool — standard quality
/plan-task @.specs/tasks/draft/admin-dashboard.feature.md
/implement-task

# Quick prototype — minimum viable quality
/plan-task @.specs/tasks/draft/poc-feature.feature.md --fast
/implement-task --target-quality 3.5 --max-iterations 1
```

`/implement-task` has exactly **one** threshold. There is no separate standard/critical value and no comma-separated form — `--target-quality X.X` applies to every implementation phase review, and the task file never carries a threshold of its own.

---

## Integration with Other Plugins

### Full Feature Cycle with Git

```bash
# 1. Create and plan the task
/add-task "Add user notification preferences with email digest settings"
/plan-task @.specs/tasks/draft/add-notification-preferences.feature.md

# 2. Review specification, make edits if needed
# 3. Re-plan if you made edits
/clear
/plan-task @.specs/tasks/todo/add-notification-preferences.feature.md --refine

# 4. Implement
/clear
/implement-task @.specs/tasks/todo/add-notification-preferences.feature.md

# 5. Commit and create PR
/commit
/create-pr
```

### Research-Heavy Features

```bash
# For unfamiliar technology — brainstorm first
/brainstorm "We need real-time features, but I'm not sure about WebSockets vs. Server-Sent Events"

# The research phase in /plan-task will:
# - Launch researcher agent to compare libraries
# - Analyze browser support and scalability
# - Check existing codebase patterns
# - Create a reusable skill document

/add-task "Add real-time collaboration with WebSocket support"
# produces @.specs/tasks/draft/add-realtime-collaboration.feature.md

/clear
/plan-task @.specs/tasks/draft/add-realtime-collaboration.feature.md

/clear
/implement-task @.specs/tasks/todo/add-realtime-collaboration.feature.md
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

- Simple bug fixes: use `--fast` for planning, `--skip-reviews` for implementation
- Well-understood features: use `--skip research` if tech stack is familiar
- Quick prototypes: use `--one-shot` for minimal planning

### Common Patterns

1. **Brainstorm before task creation** — Use `/brainstorm` for vague requirements, `/create-ideas` for quick diverse options
2. **Review specifications** — Edit the task file and use `--refine` to propagate changes
3. **Decompose large tasks** — Create multiple tasks with dependencies using `/add-task`
4. **Use human-in-the-loop for critical decisions** — Architecture and decomposition phases benefit most from human review
5. **Continue interrupted work** — Use `--continue` to resume implementation, `--refine` after manual fixes

### Anti-Patterns to Avoid

1. Skipping specification reviews for complex features
2. Ignoring high-risk task warnings in decomposition
3. Using `--skip-judges` (planning) or `--skip-reviews` (implementation) for production-critical code
4. Creating tasks that are too large — decompose into smaller dependent tasks
5. Not using `--refine` after editing specifications (re-running a full plan is wasteful)
