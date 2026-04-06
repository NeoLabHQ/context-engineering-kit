---
name: customaize-agent:create-rule
description: Use when found gap or repetative issue, that produced by you or implemenataion agent. Esentially use it each time when you say "You absolutly right, I should have done it differently." -> need create rule for this issue so it not appears again.
---

# Create Rule

Guide for creating effective `.claude/rules` files with contrastive examples that improve agent accuracy.

## Overview

**Core principle:** Effective rules use contrastive examples (Incorrect vs Correct) to eliminate ambiguity. 

**REQUIRED BACKGROUND:** Rules are behavioral guardrails, that load into every session and shapes how agents behave across all tasks. Skills load on-demand. If guidance is task-specific, create a skill instead.

## About Rules

Rules are modular, always-loaded instructions placed in `.claude/rules/` that enforce consistent behavior. They act as "standing orders" — every agent session inherits them automatically.

### What Rules Provide

1. **Behavioral constraints** — What to do and what NOT to do
2. **Code standards** — Formatting, patterns, architecture decisions
3. **Quality gates** — Conditions that must be met before proceeding
4. **Domain conventions** — Project-specific terminology and practices

### Rules vs Skills vs CLAUDE.md

| Aspect | Rules (`.claude/rules/`) | Skills (`skills/`) | CLAUDE.md |
|--------|--------------------------|---------------------|-----------|
| **Loading** | Every session (or path-scoped) | On-demand when triggered | Every session |
| **Purpose** | Behavioral constraints | Procedural knowledge | Project overview |
| **Scope** | Narrow, focused topics | Complete workflows | Broad project context |
| **Size** | Small (50-200 words each) | Medium (200-2000 words) | Medium (project summary) |
| **Format** | Contrastive examples | Step-by-step guides | Key-value / bullet points |

## When to Create a Rule

**Create when:**

- A behavior must apply to ALL agent sessions, not just specific tasks
- Agents repeatedly make the same mistake despite corrections
- A convention has clear right/wrong patterns (contrastive examples possible)
- Path-specific guidance is needed for certain file types

**Do NOT create for:**

- Task-specific workflows (use a skill instead)
- One-time instructions (put in the prompt)
- Broad project context (put in CLAUDE.md)
- Guidance that requires multi-step procedures (use a skill)

## Rule Types

### Global Rules (no `paths` frontmatter)

Load every session. Use for universal constraints.

```markdown
# Error Handling

All error handlers must log the error before rethrowing.
Never silently swallow exceptions.
```

### Path-Scoped Rules (`paths` frontmatter)

Load only when agent works with matching files. Use for file-type-specific guidance.

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

All API endpoints must include input validation.
Use the standard error response format.
```

### Priority Rules (evaluator/judge guidance)

Explicit high-level rules that set evaluation priorities.

```markdown
# Evaluation Priorities

Prioritize correctness over style.
Do not reward hallucinated detail.
Penalize confident wrong answers more than uncertain correct ones.
```

## Rule Structure: The Contrastive Pattern

Every rule MUST follow the Description-Incorrect-Correct template. This structure eliminates ambiguity by showing both what NOT to do and what TO do.

### Required Sections

```markdown
---
title: Short Rule Name
paths:                          # Optional but preferable: when it is possible to define, use it!
  - "src/**/*.ts"
---

# Rule Name

[1-2 sentence description of what the rule enforces and WHY it matters.]

## Incorrect

[Description of what is wrong with this pattern.]

\`\`\`language
// Anti-pattern code or behavior example
\`\`\`

## Correct

[Description of why this pattern is better.]

\`\`\`language
// Recommended code or behavior example
\`\`\`

## Reference

[Optional: links to documentation, papers, or related rules.]
```

### Why Contrastive Examples Work

Researches shows that rules with both positive and negative examples are significantly more discriminative than rules with only positive guidance. The Incorrect/Correct pairing:

1. **Eliminates ambiguity** — the agent sees the exact boundary between acceptable and unacceptable
2. **Prevents rationalization** — harder to argue "this is close enough" when the wrong pattern is explicitly shown
3. **Enables self-correction** — agents can compare their output against both patterns

## Writing Effective Rules

### Rule Description Principles

Explicit, high-level guidance:

| Principle | Example |
|-----------|---------|
| **Prioritize correctness over style** | "A functionally correct but ugly solution is better than an elegant but broken one" |
| **Do not reward hallucinated detail** | "Extra information not grounded in the codebase should be penalized, not rewarded" |
| **Penalize confident errors** | "A confidently stated wrong answer is worse than an uncertain correct one" |
| **Be specific, not vague** | "Functions must not exceed 50 lines" not "Keep functions short" |
| **State the WHY** | "Use early returns to reduce nesting — deeply nested code increases cognitive load" |

### Incorrect Examples: What to Show

The Incorrect section must show a pattern the agent would **plausibly produce**. Abstract or contrived bad examples provide no value.

**Effective Incorrect examples:**

- Show the most common mistake agents make for this scenario
- Include the rationalization an agent might use ("this is simpler")
- Mirror real code patterns found in the codebase

**Ineffective Incorrect examples:**

- Obviously broken code no agent would produce
- Syntax errors (agents already avoid these)
- Patterns unrelated to the rule's concern

### Correct Examples: What to Show

The Correct section must show the minimal change needed to fix the Incorrect pattern. Large rewrites obscure the actual lesson.

**Effective Correct examples:**

- Show the same scenario as Incorrect, fixed
- Highlight the specific change that matters
- Include a brief comment explaining WHY this is better

**Ineffective Correct examples:**

- Completely different code from the Incorrect example
- Over-engineered solutions that add unnecessary complexity
- Patterns that require additional context not shown

### Token Efficiency

Rules load every session. Every token counts.

- **Target:** 50-200 words per rule file (excluding code examples)
- **One rule per file** — do not bundle unrelated constraints
- **Use path scoping** to avoid loading irrelevant rules
- **Code examples:** Keep under 20 lines each (Incorrect and Correct)

## Directory Structure

```
.claude/
├── CLAUDE.md                    # Project overview (broad)
└── rules/
    ├── code-style.md            # Global: code formatting rules
    ├── error-handling.md        # Global: error handling patterns
    ├── testing.md               # Global: testing conventions
    ├── security.md              # Global: security requirements
    ├── evaluation-priorities.md # Global: judge/evaluator priorities
    ├── frontend/
    │   ├── components.md        # Path-scoped: React component rules
    │   └── state-management.md  # Path-scoped: state management rules
    └── backend/
        ├── api-design.md        # Path-scoped: API patterns
        └── database.md          # Path-scoped: database conventions
```

**Naming conventions:**

- Use lowercase with hyphens: `error-handling.md`, not `ErrorHandling.md`
- Name by the concern, not the solution: `error-handling.md`, not `try-catch-patterns.md`
- One topic per file for modularity
- Use subdirectories to group related rules by domain

## Rule Creation Process

Follow these steps in order, skipping only when a step is clearly not applicable.

### Step 1: Identify the Behavioral Gap

Before writing any rule, identify the specific agent behavior that needs correction. This understanding can come from:

- **Observed failures** — the agent repeatedly makes a specific mistake
- **Codebase analysis** — the project has conventions not obvious from code alone
- **Evaluation findings** — a judge/meta-judge identified a quality gap
- **User feedback** — explicit correction of agent behavior

Document the gap as a concrete statement: "The agent does X, but should do Y."

Conclude this step when there is a clear, specific behavior to correct.

### Step 2: Determine Rule Scope

Decide whether this rule should be:

1. **Global** (no `paths` frontmatter) — applies to all work in the project
2. **Path-scoped** (`paths` frontmatter with glob patterns) — applies only when working with matching files
3. **User-level** (`~/.claude/rules/`) — applies across all projects for personal preferences

**Decision guide:**

```
Is this project-specific?
  No  → User-level rule (~/.claude/rules/)
  Yes → Is it relevant to ALL files?
    Yes → Global rule (.claude/rules/rule-name.md)
    No  → Path-scoped rule (.claude/rules/rule-name.md with paths: frontmatter)
```

### Step 3: Write Contrastive Examples

This is the most critical step. Write the Incorrect and Correct examples BEFORE writing the description.

1. **Start with the Incorrect pattern** — write the exact code or behavior the agent produces that needs correction
2. **Write the Correct pattern** — show the minimal fix that addresses the issue
3. **Verify contrast is clear** — the difference between Incorrect and Correct must be obvious and focused on exactly one concept

**Quality check for contrastive examples:**

| Check | Pass Criteria |
|-------|---------------|
| Plausibility | Would an agent actually produce the Incorrect pattern? |
| Minimality | Does the Correct pattern change only what is necessary? |
| Clarity | Can a reader identify the difference in under 5 seconds? |
| Specificity | Does each example demonstrate exactly one concept? |
| Groundedness | Are the examples drawn from real codebase patterns? |

### Step 4: Write the Rule Description

Now write the 1-2 sentence description that connects the contrastive examples. The description must:

- State WHAT the rule enforces
- State WHY it matters (the impact or consequence)
- Use imperative form ("Use early returns" not "You should use early returns")

### Step 5: Assemble the Rule File

Create the rule file following the structure template:

1. Add YAML frontmatter with `title`, `impact`, `tags`, and optionally `paths`
2. Write the heading and description
3. Add the Incorrect section with description and code
4. Add the Correct section with description and code
5. Optionally add a Reference section with links

Place the file in `.claude/rules/` with a descriptive filename.

### Step 6: Validate the Rule

Before finishing, verify:

1. **File location** — rule exists at `.claude/rules/<rule-name>.md`
2. **Frontmatter** — contains at minimum `title` and `impact`
3. **Contrastive examples** — both Incorrect and Correct sections present with code blocks
4. **Token budget** — description is 50-200 words (excluding code)
5. **Path scoping** — if `paths` is set, glob patterns match intended files
6. **No overlap** — rule does not duplicate guidance in CLAUDE.md or other rules

### Step 7: Iterate Based on Feedback or Observations

After a rule is written, apply a Decompose → Filter → Reweight refinement cycle before finalizing:

#### 7.1 Decompose Check

Consider splitting complex rules into multiple focused rules.

For rules that your written, ask yourself: "Is this rule trying to cover more than one concept?"
- If YES, split it into multiple focused rules, each addressing exactly one concept
- If the Incorrect example shows multiple distinct anti-patterns, create separate rules for each

#### 7.2 Misalignment Filter
For rules that your written, ask yourself: "Could this rule penalize acceptable variations or reward behaviors the prompt does not ask for?"
- If YES, narrow the scope or rewrite the contrastive examples
- Verify: would an agent actually produce the Incorrect pattern? (If not, the rule is contrived)

#### 7.3 Redundancy Filter
Check all existing `.claude/rules/` files for overlap:
- If already exists a rule that covers the same concept, **update the existing rule** instead and remove the duplicate rule that you just created
- If two rules substantially overlap (enforcing the same behavioral boundary), merge them
- Use: `ls -R .claude/rules/` and `grep -r "relevant-keyword"` to find potential overlaps

#### 7.4 Impact Reweight
Assign or reassign the `impact` frontmatter field based on:
- **CRITICAL**: Anti-pattern causes data loss, security vulnerabilities, or system failures
- **HIGH**: Anti-pattern causes broken functionality, incorrect behavior, or hard-to-debug issues
- **MEDIUM**: Anti-pattern degrades quality, readability, or maintainability
- **LOW**: Anti-pattern is a minor style or convention issue

#### 7.5 Iterate Based on Feedback

After the refinement cycle, ask the user for feedback on the rule. 
- If the user says that the rule is good, you can stop the refinement cycle. 
- If the user says that the rule is bad, you should update the rule to close gaps. 
 
You should continue to iterate until the rule is good.

## Complete Rule Example

```markdown
---
title: Use Early Returns to Reduce Nesting
paths:
  - "**/*.ts"
---

# Use Early Returns to Reduce Nesting

Handle error conditions and edge cases at the top of functions using early returns. Deeply nested code increases cognitive load and makes logic harder to follow.

## Incorrect

Guard clauses are buried inside nested conditionals, making the happy path hard to find.

\`\`\`typescript
function processOrder(order: Order) {
  if (order) {
    if (order.items.length > 0) {
      if (order.status === 'pending') {
        // actual logic buried 3 levels deep
        const total = calculateTotal(order.items)
        return submitOrder(order, total)
      } else {
        throw new Error('Order not pending')
      }
    } else {
      throw new Error('No items')
    }
  } else {
    throw new Error('No order')
  }
}
\`\`\`

## Correct

Error conditions are handled first with early returns, keeping the happy path at the top level.

\`\`\`typescript
function processOrder(order: Order) {
  if (!order) 
    throw new Error('No order')
  if (order.items.length === 0) 
    throw new Error('No items')
  if (order.status !== 'pending') 
    throw new Error('Order not pending')

  const total = calculateTotal(order.items)
  return submitOrder(order, total)
}
\`\`\`

## Reference

- [Flattening Arrow Code](https://blog.codinghorror.com/flattening-arrow-code/)
```

## Complete Path-Scoped Rule Example

```markdown
---
title: API Endpoints Must Validate Input
paths:
  - "src/api/**/*.ts"
  - "src/routes/**/*.ts"
---

# API Endpoints Must Validate Input

Every API endpoint must validate request input before processing. Unvalidated input leads to runtime errors, security vulnerabilities, and data corruption.

## Incorrect

The handler trusts the request body without validation, allowing malformed data through.

\`\`\`typescript
export async function POST(req: Request) {
  const body = await req.json()
  const user = await db.users.create({
    email: body.email,
    name: body.name,
  })
  return Response.json(user)
}
\`\`\`

## Correct

Input is validated with a schema before use. Invalid requests receive a 400 response.

\`\`\`typescript
import { z } from 'zod'

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
})

export async function POST(req: Request) {
  const parsed = CreateUserSchema.safeParse(await req.json())
  if (!parsed.success) {
    return Response.json({ error: parsed.error.flatten() }, { status: 400 })
  }
  const user = await db.users.create(parsed.data)
  return Response.json(user)
}
\`\`\`
```

## Anti-Patterns

### Vague Rules Without Examples

```markdown
# Bad: No contrastive examples, too vague
Keep functions short and readable.
Use meaningful variable names.
```

**Why bad:** No concrete boundary. "Short" means different things to different agents. No Incorrect/Correct to calibrate behavior.

### Rules That Should Be Skills

```markdown
# Bad: Multi-step procedure in a rule
When deploying to production:
1. Run all tests
2. Check coverage thresholds
3. Build the project
4. Run integration tests
5. Deploy to staging first
...
```

**Why bad:** Rules should be constraints, not workflows. This belongs in a skill.

### Duplicate Rules

```markdown
# Bad: Same guidance in two places
# .claude/rules/formatting.md says "use 2-space indent"
# CLAUDE.md also says "use 2-space indent"
```

**Why bad:** When guidance conflicts, the agent cannot determine which takes precedence. Keep each piece of guidance in exactly one location.

### Overly Broad Path Scoping

```markdown
---
paths:
  - "**/*"
---
```

**Why bad:** Equivalent to a global rule but with the overhead of path matching. Remove the `paths` field entirely for global rules.

## Rule Creation Checklist

- [ ] Behavioral gap identified with concrete "does X, should do Y" statement
- [ ] Rule type determined: global, path-scoped, or user-level
- [ ] Contrastive examples written: Incorrect shows plausible agent mistake
- [ ] Contrastive examples written: Correct shows minimal fix
- [ ] Description states WHAT the rule enforces and WHY
- [ ] Frontmatter includes `title` and `impact`
- [ ] Token budget: 50-200 words (excluding code examples)
- [ ] One topic per rule file
- [ ] No overlap with CLAUDE.md or other rule files
- [ ] Path scoping uses correct glob patterns (if applicable)
- [ ] File placed in `.claude/rules/` with descriptive hyphenated name

## The Bottom Line

**Effective rules show, they do not just tell.** The Incorrect/Correct contrastive pattern eliminates ambiguity that prose descriptions leave open. When an agent can see both what to avoid and what to produce, compliance improves dramatically.

Every rule should answer three questions:
1. **What** behavior does this enforce?
2. **Why** does it matter?
3. **How** does right differ from wrong? (shown through contrastive examples)


## Claude Code Official Rules Guidlines

For larger projects, you can organize instructions into multiple files using the `.claude/rules/` directory. This keeps instructions modular and easier for teams to maintain. Rules can also be [scoped to specific file paths](#path-specific-rules), so they only load into context when Claude works with matching files, reducing noise and saving context space.

<Note>
  Rules load into context every session or when matching files are opened. For task-specific instructions that don't need to be in context all the time, use [skills](/en/skills) instead, which only load when you invoke them or when Claude determines they're relevant to your prompt.
</Note>

### Set up rules

Place markdown files in your project's `.claude/rules/` directory. Each file should cover one topic, with a descriptive filename like `testing.md` or `api-design.md`. All `.md` files are discovered recursively, so you can organize rules into subdirectories like `frontend/` or `backend/`:

```text  theme={null}
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md   # Code style guidelines
│       ├── testing.md      # Testing conventions
│       └── security.md     # Security requirements
```

Rules without [`paths` frontmatter](#path-specific-rules) are loaded at launch with the same priority as `.claude/CLAUDE.md`.

### Path-specific rules

Rules can be scoped to specific files using YAML frontmatter with the `paths` field. These conditional rules only apply when Claude is working with files matching the specified patterns.

```markdown  theme={null}
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
```

Rules without a `paths` field are loaded unconditionally and apply to all files. Path-scoped rules trigger when Claude reads files matching the pattern, not on every tool use.

Use glob patterns in the `paths` field to match files by extension, directory, or any combination:

| Pattern                | Matches                                  |
| ---------------------- | ---------------------------------------- |
| `**/*.ts`              | All TypeScript files in any directory    |
| `src/**/*`             | All files under `src/` directory         |
| `*.md`                 | Markdown files in the project root       |
| `src/components/*.tsx` | React components in a specific directory |

You can specify multiple patterns and use brace expansion to match multiple extensions in one pattern:

```markdown  theme={null}
---
paths:
  - "src/**/*.{ts,tsx}"
  - "lib/**/*.ts"
  - "tests/**/*.test.ts"
---
```

### Share rules across projects with symlinks

The `.claude/rules/` directory supports symlinks, so you can maintain a shared set of rules and link them into multiple projects. Symlinks are resolved and loaded normally, and circular symlinks are detected and handled gracefully.

This example links both a shared directory and an individual file:

```bash  theme={null}
ln -s ~/shared-claude-rules .claude/rules/shared
ln -s ~/company-standards/security.md .claude/rules/security.md
```

### User-level rules

Personal rules in `~/.claude/rules/` apply to every project on your machine. Use them for preferences that aren't project-specific:

```text  theme={null}
~/.claude/rules/
├── preferences.md    # Your personal coding preferences
└── workflows.md      # Your preferred workflows
```

User-level rules are loaded before project rules, giving project rules higher priority.
