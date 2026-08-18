---
title: Re-Ground Every Claim Copied Between Sibling Documentation Pages
impact: HIGH
paths:
  - "docs/**/*.md"
  - "**/README.md"
---

# Re-Ground Every Claim Copied Between Sibling Documentation Pages

When documenting a second command, agent, or module by mirroring the structure of its sibling's
page, re-verify each transplanted sentence against the NEW target's own source file before keeping
it. A claim that is true for the sibling reads as authoritative on the target's page and is
indistinguishable from a verified fact, so a false transplant is worse than an omission.

## Incorrect

The `/plan-task` page correctly says the command stages its output. The sentence is carried over to
the `/implement-task` page, whose skill only runs `git mv` on the task file — it never stages
changed files.

```markdown
<!-- docs/plugins/sdd/implement-task.md -->
### Workflow Phase 4: Complete
1. Move task from `in-progress/` to `done/`
4. Stage all changed files with Git

Staging at the end allows you to make manual edits on top and use `--refine`.
```

## Correct

Grep the target's own source for the behaviour (`grep -n 'git add\|stage' plugins/sdd/skills/implement-task/SKILL.md`
→ no staging step) and drop or correct the claim. Keep only what that file backs.

```markdown
<!-- docs/plugins/sdd/implement-task.md -->
### Workflow Phase 4: Complete
1. Move task from `in-progress/` to `done/` (via `git mv`)
2. Generate a final implementation report
```

## Reference

- `.claude/rules/grounded-instruction-references.md` — the companion check for references pointing
  at a source that produces nothing.
