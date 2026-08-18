---
title: Give an Output-Schema Field One Slot Per Case the Obligation Covers
impact: HIGH
paths:
  - "plugins/**/agents/*.md"
  - "plugins/**/skills/**/*.md"
  - ".claude/agents/*.md"
---

# Give an Output-Schema Field One Slot Per Case the Obligation Covers

When prose in a prompt mandates evidence for N cases (both directions of a comparison, every
listed item, each phase), the emitted-YAML template must provide N slots. A single slot for a
two-sided obligation does not make the second side optional — it makes it unrecordable, so the
agent silently satisfies half the rule while the output still looks well-formed. Count the cases
in the sentence, then count the keys in the template, and make the two numbers agree.

## Incorrect

The procedure demands the closer-to AND further-from anchors both be quoted, but the template
offers one `anchor_quoted` / `artifact_quoted` pair, so the further-from side degrades to a bare
label with no place for its evidence.

```yaml
# prose: "quote the anchor text and the artifact text, for the anchor it is closer to
#         and for the anchor it is further from"
anchor_comparison:
  closer_to: "score_2 | score_4"
  further_from: "score_4 | score_2"
  anchor_quoted: "[exact excerpt of the anchor text compared against]"
  artifact_quoted: "[exact excerpt of the artifact text compared, with file:line]"
```

## Correct

One quoted pair per side, so the template cannot be filled in without producing both.

```yaml
anchor_comparison:
  closer_to:
    anchor: "score_4 | [exact excerpt of the anchor text]"
    artifact: "[exact excerpt, with file:line]"
  further_from:
    anchor: "score_2 | [exact excerpt of the anchor text]"
    artifact: "[what the artifact does instead, or 'artifact lacks: ...']"
```

## Reference

- `.claude/rules/scope-criteria-per-item-not-per-block.md` — the companion check for admitting a
  block wholesale instead of item by item.
</content>
