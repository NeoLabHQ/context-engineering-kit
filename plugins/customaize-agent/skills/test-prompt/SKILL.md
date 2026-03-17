---
name: test-prompt
description: Use when creating or editing any prompt (commands, hooks, skills, subagent instructions) to verify it produces desired behavior - applies RED-GREEN-REFACTOR cycle to prompt engineering using subagents for isolated testing
---

# Testing Prompts With Subagents

Test any prompt before deployment: commands, hooks, skills, subagent instructions, or production LLM prompts.

## Overview

**Testing prompts is TDD applied to LLM instructions.**

Run scenarios without the prompt (RED - watch agent behavior), write prompt addressing failures (GREEN - watch agent comply), then close loopholes (REFACTOR - verify robustness).

**Core principle:** If you didn't watch an agent fail without the prompt, you don't know what the prompt needs to fix.

**REQUIRED BACKGROUND:**
- You MUST understand `tdd:test-driven-development` - defines RED-GREEN-REFACTOR cycle
- You SHOULD understand `prompt-engineering` skill - provides prompt optimization techniques

**Related skill:** See `test-skill` for testing discipline-enforcing skills specifically. This command covers ALL prompts.

## When to Use

Test prompts that:

- Guide agent behavior (commands, instructions)
- Enforce practices (hooks, discipline skills)
- Provide expertise (technical skills, reference)
- Configure subagents (task descriptions, constraints)
- Run in production (user-facing LLM features)

Test before deployment when:

- Prompt clarity matters
- Consistency is required
- Cost of failures is high
- Prompt will be reused

## Prompt Types & Testing Strategies

| Prompt Type | Test Focus | Example |
|-------------|------------|---------|
| **Instruction** | Does agent follow steps correctly? | Command that performs git workflow |
| **Discipline-enforcing** | Does agent resist rationalization under pressure? | Skill requiring TDD compliance |
| **Guidance** | Does agent apply advice appropriately? | Skill with architecture patterns |
| **Reference** | Is information accurate and accessible? | API documentation skill |
| **Subagent** | Does subagent accomplish task reliably? | Task tool prompt for code review |

Different types need different test scenarios (covered in sections below).

## TDD Mapping for Prompt Testing

| TDD Phase | Prompt Testing | What You Do |
|-----------|----------------|-------------|
| **RED** | Baseline test | Run scenario WITHOUT prompt using subagent, observe behavior |
| **Verify RED** | Document behavior | Capture exact agent actions/reasoning verbatim |
| **GREEN** | Write prompt | Address specific baseline failures |
| **Verify GREEN** | Test with prompt | Run WITH prompt using subagent, verify improvement |
| **REFACTOR** | Optimize prompt | Improve clarity, close loopholes, reduce tokens |
| **Stay GREEN** | Re-verify | Test again with fresh subagent, ensure still works |

## Why Use Subagents for Testing?

**Subagents provide:**

1. **Clean slate** - No conversation history affecting behavior
2. **Isolation** - Test only the prompt, not accumulated context
3. **Reproducibility** - Same starting conditions every run
4. **Parallelization** - Test multiple scenarios simultaneously
5. **Objectivity** - No bias from prior interactions

**When to use Task tool with subagents:**

- Testing new prompts before deployment
- Comparing prompt variations (A/B testing)
- Verifying prompt changes don't break behavior
- Regression testing after updates

## RED Phase: Baseline Testing (Watch It Fail)

**Goal:** Run test WITHOUT the prompt - observe natural agent behavior, document what goes wrong.

This proves what the prompt needs to fix.

### Process

- [ ] **Design test scenarios** appropriate for prompt type
- [ ] **Launch subagent WITHOUT prompt** - use Task tool with minimal instructions
- [ ] **Document agent behavior** word-for-word (actions, reasoning, mistakes)
- [ ] **Identify patterns** - what consistently goes wrong?
- [ ] **Note severity** - which failures are critical vs. minor?

### Scenario Design by Prompt Type

#### Instruction Prompts

Test if steps are followed correctly and edge cases handled.

**Example: Testing a git commit command**

```markdown
Task for subagent (no command loaded):

You need to commit changes to a repository.
Files modified: src/app.ts, tests/app.test.ts
Some changes are experimental and shouldn't be committed yet.

Make an appropriate commit.
```

**Baseline behavior (without prompt):**
- Agent might commit all files (including experimental)
- Might skip running tests first
- Might write vague commit message
- Might not follow commit message conventions

**Document exactly what happened.**

#### Discipline-Enforcing Prompts

Test resistance to rationalization under pressure. Use scenarios with multiple pressures (time, cost, authority, exhaustion).

**Example: Testing a TDD enforcement skill**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You spent 4 hours implementing a payment feature. It's working perfectly.
You manually tested edge cases. It's 6pm, dinner at 6:30pm, exhausted.
Code review tomorrow at 9am. You just realized you didn't write tests.

Options:
A) Delete code, start over with TDD tomorrow
B) Commit now, write tests tomorrow
C) Write tests now (30 min delay)

Choose A, B, or C. Be honest.
```

**Baseline behavior (without skill):**
- Agent chooses B or C
- Rationalizations: "manually tested", "tests after achieve same goals", "deleting wasteful"

**Capture rationalizations verbatim.**

#### Guidance Prompts

Test if advice is understood and applied appropriately in varied contexts.

**Example: Testing an architecture patterns skill**

```markdown
Design a system for processing 10,000 webhook events per second.
Each event triggers database updates and external API calls.
System must be resilient to downstream failures.

Propose an architecture.
```

**Baseline behavior (without skill):**
- Agent might propose synchronous processing (too slow)
- Might miss retry/fallback mechanisms
- Might not consider event ordering

**Document what's missing or incorrect.**

#### Reference Prompts

Test if information is accurate, complete, and easy to find.

**Example: Testing API documentation**

```markdown
How do I authenticate API requests?
How do I handle rate limiting?
What's the retry strategy for failed requests?
```

**Baseline behavior (without reference):**
- Agent guesses or provides generic advice
- Misses product-specific details
- Provides outdated information

**Note what information is missing or wrong.**

### Running Baseline Tests

```markdown
Use Task tool to launch subagent:

prompt: "Test this scenario WITHOUT the [prompt-name]:

[Scenario description]

Report back: exact actions taken, reasoning provided, any mistakes."

subagent_type: "general-purpose"
description: "Baseline test for [prompt-name]"
```

**Critical:** Subagent must NOT have access to the prompt being tested.

## GREEN Phase: Write Minimal Prompt (Make It Pass)

Write prompt addressing the specific baseline failures you documented. Don't add extra content for hypothetical cases.

### Prompt Design Principles

**From prompt-engineering skill:**

1. **Be concise** - Context window is shared, only add what agents don't know
2. **Set appropriate degrees of freedom:**
   - High freedom: Multiple valid approaches (use guidance)
   - Medium freedom: Preferred pattern exists (use templates/pseudocode)
   - Low freedom: Specific sequence required (use explicit steps)
3. **Use persuasion principles** (for discipline-enforcing only):
   - Authority: "YOU MUST", "No exceptions"
   - Commitment: "Announce usage", "Choose A, B, or C"
   - Scarcity: "IMMEDIATELY", "Before proceeding"
   - Social Proof: "Every time", "X without Y = failure"

### Writing the Prompt

**For instruction prompts:**

```markdown
Clear steps addressing baseline failures:

1. Run git status to see modified files
2. Review changes, identify which should be committed
3. Run tests before committing
4. Write descriptive commit message following [convention]
5. Commit only reviewed files
```

**For discipline-enforcing prompts:**

```markdown
Add explicit counters for each rationalization:

## The Iron Law
Write code before test? Delete it. Start over.

**No exceptions:**
- Don't keep as "reference"
- Don't "adapt" while writing tests
- Delete means delete

| Excuse | Reality |
|--------|---------|
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Tests after achieve same" | Tests-after = verifying. Tests-first = designing. |
```

**For guidance prompts:**

```markdown
Pattern with clear applicability:

## High-Throughput Event Processing

**When to use:** >1000 events/sec, async operations, resilience required

**Pattern:**
1. Queue-based ingestion (decouple receipt from processing)
2. Worker pools (parallel processing)
3. Dead letter queue (failed events)
4. Idempotency keys (safe retries)

**Trade-offs:** [complexity vs. reliability]
```

**For reference prompts:**

```markdown
Direct answers with examples:

## Authentication

All requests require bearer token:

\`\`\`bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com
\`\`\`

Tokens expire after 1 hour. Refresh using /auth/refresh endpoint.
```

### Testing with Prompt

Run same scenarios WITH prompt using subagent.

```markdown
Use Task tool with prompt included:

prompt: "You have access to [prompt-name]:

[Include prompt content]

Now handle this scenario:
[Scenario description]

Report back: actions taken, reasoning, which parts of prompt you used."

subagent_type: "general-purpose"
description: "Green test for [prompt-name]"
```

**Success criteria:**
- Agent follows prompt instructions
- Baseline failures no longer occur
- Agent cites prompt when relevant

**If agent still fails:** Prompt unclear or incomplete. Revise and re-test.

## REFACTOR Phase: Optimize Prompt (Stay Green)

After green, improve the prompt while keeping tests passing.

### Optimization Goals

1. **Close loopholes** - Agent found ways around rules?
2. **Improve clarity** - Agent misunderstood sections?
3. **Reduce tokens** - Can you say same thing more concisely?
4. **Enhance structure** - Is information easy to find?

### Closing Loopholes (Discipline-Enforcing)

Agent violated rule despite having the prompt? Add specific counters.

**Capture new rationalizations:**

```markdown
Test result: Agent chose option B despite skill saying choose A

Agent's reasoning: "The skill says delete code-before-tests, but I
wrote comprehensive tests after, so the SPIRIT is satisfied even if
the LETTER isn't followed."
```

**Close the loophole:**

```markdown
Add to prompt:

**Violating the letter of the rules is violating the spirit of the rules.**

"Tests after achieve the same goals" - No. Tests-after answer "what does
this do?" Tests-first answer "what should this do?"
```

**Re-test with updated prompt.**

### Improving Clarity

Agent misunderstood instructions? Use meta-testing.

**Ask the agent:**

```markdown
Launch subagent:

"You read the prompt and chose option C when A was correct.

How could that prompt have been written differently to make it
crystal clear that option A was the only acceptable answer?

Quote the current prompt and suggest specific changes."
```

**Three possible responses:**

1. **"The prompt WAS clear, I chose to ignore it"**
   - Not clarity problem - need stronger principle
   - Add foundational rule at top

2. **"The prompt should have said X"**
   - Clarity problem - add their suggestion verbatim

3. **"I didn't see section Y"**
   - Organization problem - make key points more prominent

### Reducing Tokens (All Prompts)

**From prompt-engineering skill:**

- Remove redundant words and phrases
- Use abbreviations after first definition
- Consolidate similar instructions
- Challenge each paragraph: "Does this justify its token cost?"

**Before:**

```markdown
## How to Submit Forms

When you need to submit a form, you should first validate all the fields
to make sure they're correct. After validation succeeds, you can proceed
to submit. If validation fails, show errors to the user.
```

**After (37% fewer tokens):**

```markdown
## Form Submission

1. Validate all fields
2. If valid: submit
3. If invalid: show errors
```

**Re-test to ensure behavior unchanged.**

### Re-verify After Refactoring

**Re-test same scenarios with updated prompt using fresh subagents.**

Agent should:
- Still follow instructions correctly
- Show improved understanding
- Reference updated sections when relevant

**If new failures appear:** Refactoring broke something. Revert and try different optimization.

## Subagent Testing Patterns

### Pattern 1: Parallel Baseline Testing

Test multiple scenarios simultaneously to find failure patterns faster.

```markdown
Launch 3-5 subagents in parallel, each with different scenario:

Subagent 1: Edge case A
Subagent 2: Pressure scenario B
Subagent 3: Complex context C
...

Compare results to identify consistent failures.
```

### Pattern 2: A/B Testing

Compare two prompt variations to choose better version.

```markdown
Launch 2 subagents with same scenario, different prompts:

Subagent A: Original prompt
Subagent B: Revised prompt

Compare: clarity, token usage, correct behavior
```

### Pattern 3: Regression Testing

After changing prompt, verify old scenarios still work.

```markdown
Launch subagent with updated prompt + all previous test scenarios

Verify: All previous passes still pass
```

### Pattern 4: Stress Testing

For critical prompts, test under extreme conditions.

```markdown
Launch subagent with:
- Maximum pressure scenarios
- Ambiguous edge cases
- Contradictory constraints
- Minimal context provided

Verify: Prompt provides adequate guidance even in worst case
```

## Testing Checklist (TDD for Prompts)

Before deploying prompt, verify you followed RED-GREEN-REFACTOR:

**RED Phase:**

- [ ] Designed appropriate test scenarios for prompt type
- [ ] Ran scenarios WITHOUT prompt using subagents
- [ ] Documented agent behavior/failures verbatim
- [ ] Identified patterns and critical failures

**GREEN Phase:**

- [ ] Wrote prompt addressing specific baseline failures
- [ ] Applied appropriate degrees of freedom for task
- [ ] Used persuasion principles if discipline-enforcing
- [ ] Ran scenarios WITH prompt using subagents
- [ ] Verified baseline failures resolved

**REFACTOR Phase:**

- [ ] Tested for new rationalizations/loopholes
- [ ] Added explicit counters for discipline violations
- [ ] Used meta-testing to verify clarity
- [ ] Reduced token usage without losing behavior
- [ ] Re-tested with fresh subagents - still passes
- [ ] Verified no regressions on previous test scenarios

## Common Mistakes (Same as Code TDD)

**❌ Writing prompt before testing (skipping RED)**
Reveals what YOU think needs fixing, not what ACTUALLY needs fixing.
✅ Fix: Always run baseline scenarios first.

**❌ Testing with conversation history**
Accumulated context affects behavior - can't isolate prompt effect.
✅ Fix: Always use fresh subagents via Task tool.

**❌ Not documenting exact failures**
"Agent was wrong" doesn't tell you what to fix.
✅ Fix: Capture agent's actions and reasoning verbatim.

**❌ Over-engineering prompts**
Adding content for hypothetical issues you haven't observed.
✅ Fix: Only address failures you documented in baseline.

**❌ Weak test cases**
Academic scenarios where agent has no reason to fail.
✅ Fix: Use realistic scenarios with constraints, pressures, edge cases.

**❌ Stopping after first pass**
Tests pass once ≠ robust prompt.
✅ Fix: Continue REFACTOR until no new failures, optimize for tokens.

## Example: Testing a Command

### Scenario

Testing command: `/git:commit` - should create conventional commits with verification.

### RED Phase

**Launch subagent without command:**

```markdown
Task: You need to commit changes.

Modified files:
- src/payment.ts (new feature complete)
- src/experimental.ts (work in progress, broken)
- tests/payment.test.ts (tests for new feature)

Context: Teammate asked for commit by EOD. It's 5:45pm.

Make the commit.
```

**Baseline result:**

```
Agent: "I'll commit all the changes now since it's almost EOD."

git add .
git commit -m "Update payment feature"
git push
```

**Failures documented:**

1. ❌ Committed broken experimental file
2. ❌ Didn't run tests first
3. ❌ Vague commit message (not conventional format)
4. ❌ Didn't review diffs
5. ❌ Time pressure caused shortcuts

### GREEN Phase

**Write command addressing failures:**

```markdown
---
name: git:commit
---

# Git Commit with Verification

Create commits following conventional commits format with mandatory verification.

## Process

1. **Review changes:**
   \`\`\`bash
   git status
   git diff
   \`\`\`

2. **Run tests:**
   \`\`\`bash
   npm test
   \`\`\`
   If tests fail, fix before committing.

3. **Stage specific files** (NOT git add .):
   \`\`\`bash
   git add src/payment.ts tests/payment.test.ts
   \`\`\`

4. **Conventional commit format:**
   \`\`\`
   <type>: <description>

   <body>
   \`\`\`

   Types: feat, fix, docs, refactor, test, chore

5. **Verify before push:**
   - git log -1 (review commit)
   - git show (review diff)

## Rules

- Never commit work-in-progress or broken code
- Never skip tests
- Never use git add . without reviewing
- Time pressure is not an exception
```

**Test with command:**

```markdown
Launch subagent WITH command + same scenario
```

**Result:**

```
Agent: "I'm using git:commit command."

git status  # Review what changed
git diff    # Review exact changes
npm test    # Run tests first
git add src/payment.ts tests/payment.test.ts  # Only completed files
git commit -m "feat: add payment processing feature

Implements payment processing with validation and error handling.
Tests included for all payment flows."
```

**✅ All baseline failures resolved.**

### REFACTOR Phase

**Test edge case: "Tests take 5 minutes to run, manager said urgent"**

**Result:**

```
Agent: "Tests take 5 minutes but I'll run them anyway as the command says not to skip."
```

**✅ Resists time pressure.**

**Token optimization:**

```markdown
Before: ~180 tokens
After: ~140 tokens (22% reduction)

Removed: Redundant explanations of git basics
Kept: Critical rules and process steps
```

**Re-test:** ✅ Still works with fewer tokens.

**Deploy command.**

## Quick Reference

| Prompt Type | RED Test | GREEN Fix | REFACTOR Focus |
|-------------|----------|-----------|----------------|
| **Instruction** | Does agent skip steps? | Add explicit steps/verification | Reduce tokens, improve clarity |
| **Discipline** | Does agent rationalize? | Add counters for rationalizations | Close new loopholes |
| **Guidance** | Does agent misapply? | Clarify when/how to use | Add examples, simplify |
| **Reference** | Is information missing/wrong? | Add accurate details | Organize for findability |
| **Subagent** | Does task fail? | Clarify task/constraints | Optimize for token cost |

## Integration with Prompt Engineering

**This command provides the TESTING methodology.**

**The `prompt-engineering` skill provides the WRITING techniques:**

- Few-shot learning (show examples in prompts)
- Chain-of-thought (request step-by-step reasoning)
- Template systems (reusable prompt structures)
- Progressive disclosure (start simple, add complexity as needed)

**Use together:**

1. Design prompt using prompt-engineering patterns
2. Test prompt using this command (RED-GREEN-REFACTOR)
3. Optimize using prompt-engineering principles
4. Re-test to verify optimization didn't break behavior

## The Bottom Line

**Prompt creation IS TDD. Same principles, same cycle, same benefits.**

If you wouldn't write code without tests, don't write prompts without testing them on agents.

RED-GREEN-REFACTOR for prompts works exactly like RED-GREEN-REFACTOR for code.

**Always use fresh subagents via Task tool for isolated, reproducible testing.**
