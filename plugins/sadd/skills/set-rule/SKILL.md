---
name: sadd:set-rule
description: Use when found gap or repetative issue, that produced by you or implemenataion agent. Esentially use it each time when you say "You absolutly right, I should have done it differently." -> need create rule for this issue so it not appears again.
argument-hint: Rule intent or domain (e.g., "enforce error handling patterns" or "evaluation priorities for API code")
---

# set-rule

## Task

Add or modify `.claude/rules` files by dispatching the judge agent to analyze the user's domain/intent and produce well-formed contrastive rules. Rules follow the LLMBar explicit high-level rule pattern with Description/Incorrect/Correct examples.

## Context

Rules are always-loaded behavioral guardrails (unlike skills which load on-demand). Effective rules use contrastive examples that show both the anti-pattern and the fix, following research from:

- **LLMBar** (Zeng et al. 2023): Explicit rules like "prioritize correctness over style; do not reward hallucinated detail" improve evaluator accuracy ~10% across natural and adversarial test sets. Rules + Metrics + Reference is the strongest combination.
- **OpenRubrics CRG** (Contrastive Rubric Generation): Two rubric types -- "hard rules" (explicit constraints) and "principles" (implicit quality indicators visible by comparing good/bad responses). Conditioning on contrastive pairs produces more discriminative criteria.
- **Vercel Labs pattern**: Description, Incorrect, Correct template for agent rules.

**CRITICAL:** You are the orchestrator. Do NOT write rules directly. Dispatch the meta judge agent (Stage 4: Contrastive Rule Generation) to produce the rules, then validate and write them.

## Process

### Phase 1: Analyze Rule Intent

Determine what rules the user needs:

1. **Parse the user request** -- What domain, behavior, or convention should the rule enforce?
2. **Check existing rules** -- Read `.claude/rules/` directory to avoid duplication
3. **Classify rule type**:

| Type | When | Example |
|------|------|---------|
| **Global** | Applies to all work | Error handling, evaluation priorities |
| **Path-scoped** | Applies to specific files | API validation for `src/api/**/*.ts` |
| **Priority** | Guides evaluator/judge behavior | "Correctness over style" |

4. **Gather codebase context** -- If the rule relates to code patterns, identify relevant files for the meta judge to analyze

### Phase 2: Dispatch Meta Judge for Rule Generation

Launch the meta judge agent with a prompt focused on Stage 4 (Contrastive Rule Generation). The meta judge has the full methodology for producing quality contrastive rules.

**Meta judge dispatch prompt:**

```markdown
## Task

Generate contrastive rules for `.claude/rules/` based on the following intent:

**Rule Intent:** {user's request}
**Rule Type:** {global | path-scoped | priority}
**Existing Rules:** {list of existing .claude/rules/ files, or "None"}
**Codebase Context:** {relevant file paths and patterns, or "N/A"}

## Instructions

Execute your Stage 4: Contrastive Rule Generation process. For each rule:

1. Identify the behavioral gap or convention to enforce
2. Generate contrastive examples (Incorrect/Correct) grounded in the codebase or domain
3. Apply the quality check: Plausibility, Minimality, Clarity, Specificity, Groundedness
4. Output each rule in the format below

## Output Format

For each rule, produce:

---
title: "Short Rule Name"
impact: CRITICAL | HIGH | MEDIUM | LOW
tags: comma, separated, categories
paths:                          # Optional: omit for global rules
  - "glob/pattern/**/*.ext"
---

# Rule Name

[1-2 sentences: WHAT it enforces and WHY]

## Incorrect

[What the wrong pattern looks like]

\`\`\`language
// Anti-pattern example
\`\`\`

## Correct

[What the right pattern looks like -- minimal change from Incorrect]

\`\`\`language
// Fixed example
\`\`\`

## Quality Check Results

| Check | Pass? | Evidence |
|-------|-------|----------|
| Plausibility | YES/NO | Would an agent actually produce the Incorrect pattern? |
| Minimality | YES/NO | Does the Correct pattern change only what is necessary? |
| Clarity | YES/NO | Can a reader identify the difference in under 5 seconds? |
| Specificity | YES/NO | Does each example demonstrate exactly one concept? |
| Groundedness | YES/NO | Are the examples drawn from real patterns? |
```

**Dispatch:**

```
Use Task tool:
  - description: "Meta Judge: Generate contrastive rules for {brief intent}"
  - prompt: {constructed meta judge prompt above}
  - model: opus
  - agent: sadd:meta-judge
```

### Phase 3: Validate and Write Rules

After meta judge returns:

1. **Validate each rule** against the `customaize-agent:create-rule` checklist:
   - Frontmatter has `title` and `impact`
   - Both Incorrect and Correct sections present with code blocks
   - Description is 50-200 words (excluding code)
   - All 5 quality checks pass (Plausibility, Minimality, Clarity, Specificity, Groundedness)
   - No overlap with existing rules or CLAUDE.md

2. **Write validated rules** to `.claude/rules/` with descriptive hyphenated filenames

3. **Report results** to user:

```
## Rules Created/Modified

| File | Title | Impact | Type |
|------|-------|--------|------|
| .claude/rules/{name}.md | {title} | {impact} | {global/path-scoped} |

### Summary
- Rules created: {count}
- Rules modified: {count}
- Quality checks: All passed
```

### Phase 4: Optional Judge-Driven Rule Discovery

When the user asks to "discover rules from evaluation" or "create rules from issues found":

1. Dispatch the judge agent to evaluate recent work
2. The judge's Stage 8 (Rule Generation) triggers when it finds recurring quality gaps
3. Collect the judge's rule recommendations
4. Feed them through Phase 2-3 for meta judge refinement and validation

## Rule Writing Principles (from LLMBar)

These principles MUST be embedded in every rule's design:

| Principle | Application |
|-----------|-------------|
| **Prioritize correctness over style** | Rules about behavior trump rules about formatting |
| **Do not reward hallucinated detail** | Penalize ungrounded additions, not reward them |
| **Explicit over implicit** | State the boundary clearly with contrastive examples |
| **One concept per rule** | Split compound rules into focused, atomic files |
| **Minimal diff between Incorrect/Correct** | The fix should be obvious, not a rewrite |

## Cross-References

- **Rule template and creation process**: `customaize-agent:create-rule` -- full 7-step process, quality checks, anti-patterns, directory structure
- **Meta judge Stage 4**: `sadd:meta-judge` agent -- contrastive rule generation methodology
- **Judge Stage 8**: `sadd:judge` agent -- conditional rule generation from evaluation findings
