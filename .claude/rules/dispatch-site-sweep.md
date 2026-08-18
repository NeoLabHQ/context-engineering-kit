---
title: Update Every Dispatch Site When a Dispatched Procedure's Output Contract Changes
impact: HIGH
paths:
  - "plugins/**/*.md"
  - ".claude/agents/**/*.md"
  - ".claude/skills/**/*.md"
---

# Update Every Dispatch Site When a Dispatched Procedure's Output Contract Changes

Deleting a stage at its source is only half the refactor. Grep the repository for the procedure's
filename and update every prompt that dispatches it, because a dispatch that still says "execute it
exactly as is" plus "update the task file" against a procedure that now writes only a scratchpad
leaves two contradicting orders and the agent silently produces nothing.

## Incorrect

The stage was correctly deleted at the source, but the dispatching prompt still commands the removed
behaviour.

```markdown
<!-- analyse-business-requirements.md — STAGE 6 "Update Task File" deleted -->
**Write NOTHING to the task file here.** The dispatching agent owns the task file.
```

```markdown
<!-- plan-task/SKILL.md — NOT swept -->
Read ${CLAUDE_PLUGIN_ROOT}/skills/plan-task/analyse-business-requirements.md
and execute it exactly as is!

CRITICAL: ONLY CREATE THE SCRATCHPAD AND UPDATE THE TASK FILE.
```

## Correct

After the deletion, run `grep -rn "analyse-business-requirements" .` and re-anchor every hit to the
new contract.

```markdown
<!-- plan-task/SKILL.md — swept -->
Execute your own Core Process (STAGES 1-10). It dispatches
${CLAUDE_PLUGIN_ROOT}/skills/plan-task/analyse-business-requirements.md
STAGES 2-5, which write only to the scratchpad.

CRITICAL: DO NOT OUTPUT YOUR ANALYSIS. Write the scratchpad, then the task file's
`# Description` and `## Acceptance Criteria`.
```

## Reference

- `.claude/rules/supersede-at-the-source.md` — delete the stage in the source file; this rule is the
  caller-side follow-up.
