---
title: Rename Identifiers in Link Targets, Not Just Link Text
impact: MEDIUM
paths:
  - "**/*.md"
---

# Rename Identifiers in Link Targets, Not Just Link Text

When renaming a command, page, section or anchor in documentation, update the identifier inside
every link **target** (`](...)`) as well as inside the visible link text. Markdown puts two copies of
the same identifier on one line, so a rename that edits only the rendered token leaves a link that
still points at the old, now non-existent, destination — and it reads as correct because the visible
label is right.

## Incorrect

`/plan` was renamed to `/plan-task`. The label was updated; the URL slug was not, and it now
disagrees with the same file's other links to that page.

```markdown
- [/plan-task](https://neolab.gitbook.io/cek/plugins/sdd/plan) - Refine the task specification
- [/implement-task](https://neolab.gitbook.io/cek/plugins/sdd/implement) - Implement and verify

<!-- ...elsewhere in the same file, already correct: -->
<a href="https://neolab.gitbook.io/cek/plugins/sdd/plan-task">/plan-task</a>
```

## Correct

Grep for the bare identifier including its path/anchor forms
(`grep -nE '\]\([^)]*/plan[^-a-z]|#plan[^-a-z]' README.md`) and fix both halves of every link.

```markdown
- [/plan-task](https://neolab.gitbook.io/cek/plugins/sdd/plan-task) - Refine the task specification
- [/implement-task](https://neolab.gitbook.io/cek/plugins/sdd/implement-task) - Implement and verify
```

## Reference

- `.claude/rules/refactor-cross-references.md` — the companion sweep for derived counts and ranges.
