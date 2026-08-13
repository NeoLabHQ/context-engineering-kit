---
title: Pay a Token Budget Inside the Change's Scope, Never by Deleting Untouched Content
impact: HIGH
---

# Pay a Token Budget Inside the Change's Scope, Never by Deleting Untouched Content

When a change adds lines to a prompt or agent file and the project's token-minimalism rule presses
back, compress the text you were asked to change — never sections the task never mentioned. Trimming
untouched content silently destroys guidance nobody reviewed, and it hides inside a diff that looks
like a net-neutral refactor. If the budget still does not close, report the growth; do not fund it
from elsewhere.

## Incorrect

The task was to replace `score_definitions` with `anchors`. To offset +43 added lines, the agent
also gutted an unrelated Stage 4 example list — dropping four statements outright — even though the
file was nowhere near any size limit.

```markdown
<!-- Stage 4, NOT part of the task -->
- The response must incorporate a quote from a recent news article or study. [Hard Rule]
- The response must mention the publication date of the referenced source. [Hard Rule]
- The response must concisely summarize the quoted source. [Hard Rule]        <!-- deleted -->
- The response must discuss economic implications based on the source. [Hard Rule]  <!-- deleted -->
- The response employs sensory details to enhance the reader's mental image. [Principle]
- The response demonstrates originality to avoid clichés. [Principle]
```

## Correct

Touch only the sections the task names. Absorb the growth, and state it in the report so a reviewer
can decide whether a separate cleanup is warranted.

```markdown
<!-- Stage 4 left exactly as found; only the score_definitions sites changed -->
<!-- Report: file grew 766 -> 856 lines (+11.7%), all of it the new Step 5.1 stage and
     the anchors blocks. No unrelated sections were compressed. -->
```

## Reference

- `CLAUDE.md` — "Minimal tokens" is a design rule for what you write, not a licence to delete what
  you did not touch.
