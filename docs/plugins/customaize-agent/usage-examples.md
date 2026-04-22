# Customaize Agent Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the Customaize Agent plugin for creating, testing, and optimizing Claude Code extensions.

## Examples

### Creating a Custom Command

**Scenario**: You need a command to validate API documentation against your OpenAPI specs.

```bash
# Start the command creation assistant
> /customaize-agent:create-command validate API documentation
```

**Expected Flow**:

1. Assistant examines existing commands in `.claude/commands/`
2. Identifies this as an Analysis command (similar to `review.md`)
3. Asks clarifying questions:
   - What format is the documentation in?
   - What aspects need validation?
   - Should it create tasks for issues found?
4. Generates command file with proper structure

**Generated Command** (simplified):

```markdown
---
description: Validates API documentation against OpenAPI standards for completeness and consistency
argument-hint: Path to OpenAPI spec file (optional, will search if not provided)
---

<task>
You are an API documentation validator reviewing OpenAPI specifications.
</task>

<validation_process>
1. Load OpenAPI spec files
2. Check required endpoints documented
3. Validate response schemas
4. Verify authentication documented
5. Check for missing examples
</validation_process>

<human_review_needed>
Flag for manual review:
- [ ] Breaking changes detected
- [ ] Security implications unclear
</human_review_needed>
```

**Next Steps**:

```bash
# Test the command before deployment
> /customaize-agent:test-prompt .claude/commands/validate-api.md

# Document the new command
> /update-docs
```

---

### Creating a Domain-Specific Skill

**Scenario**: Building a BigQuery analysis skill for your data team.

```bash
# Start skill creation with TDD approach
> /customaize-agent:create-skill bigquery-analysis
```

**Expected Flow**:

1. **Understanding Phase** - Assistant asks about use cases:
   - "What queries will users run most often?"
   - "What tables and schemas exist?"
   - "What are common filtering requirements?"

2. **Planning Phase** - Identifies reusable resources:
   - `references/finance.md` - Revenue metrics and billing schemas
   - `references/sales.md` - Pipeline and opportunity data
   - `references/product.md` - Usage analytics schemas

3. **Structure Created**:

```
bigquery-analysis/
├── SKILL.md              # Overview and navigation
└── references/
    ├── finance.md        # Revenue, ARR, billing
    ├── sales.md          # Opportunities, pipeline
    └── product.md        # API usage, features
```

**SKILL.md Content** (simplified):

```markdown
---
name: BigQuery-Analysis
description: Use when querying company data in BigQuery, analyzing revenue metrics, sales pipeline, or product usage - provides table schemas, common query patterns, and filtering rules
---

# BigQuery Data Analysis

## Quick Start

Always filter test accounts:
```sql
WHERE account_type != 'test'
```

## Available Datasets

**Finance**: Revenue, ARR, billing -> See [references/finance.md](references/finance.md)
**Sales**: Opportunities, pipeline -> See [references/sales.md](references/sales.md)
**Product**: API usage, features -> See [references/product.md](references/product.md)

## Common Mistakes

- Forgetting to filter test accounts (MUST always exclude)
- Not accounting for timezone in date comparisons
- Missing joins to get current account status
```

**Testing the Skill**:

```bash
# Verify skill works correctly
> /customaize-agent:test-skill bigquery-analysis
```

---

### Testing a TDD Enforcement Skill

**Scenario**: You've created a skill that enforces TDD practices. Now you need to verify it resists rationalization under pressure.

```bash
# Start pressure testing
> /customaize-agent:test-skill tdd-enforcement
```

**RED Phase - Baseline Testing**:

The assistant creates a pressure scenario WITHOUT the skill:

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You spent 4 hours implementing a payment feature. It's working perfectly.
You manually tested all edge cases. It's 6pm, dinner at 6:30pm.
Code review tomorrow at 9am. You just realized you didn't write tests.

Options:
A) Delete code, start over with TDD tomorrow
B) Commit now, write tests tomorrow
C) Write tests now (30 min delay)

Choose A, B, or C.
```

**Baseline Result** (agent without skill):

```
Agent chose: C (write tests after)

Rationalizations captured:
- "I already manually tested it"
- "Tests after achieve the same goals"
- "Deleting 4 hours of work is wasteful"
- "Being pragmatic not dogmatic"
```

**GREEN Phase - Skill Addresses Failures**:

Skill updated with explicit counters:

```markdown
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
| "Deleting is wasteful" | Keeping it = testing after = violation. |
```

**Re-test Result**:

```
Agent chose: A (delete and start fresh)
Cited: "The Iron Law" and "No exceptions" sections
```

**Bulletproof achieved.**

---

### Creating a Security Hook

**Scenario**: You want to prevent accidental commits containing API keys or secrets.

```bash
# Let the assistant analyze your project and suggest hooks
> /customaize-agent:create-hook
```

**Expected Flow**:

1. **Environment Analysis**:
   - Detects Git repository
   - Finds `.env` file patterns
   - Identifies Node.js project

2. **Suggestions Offered**:
   ```
   Based on your project, I suggest:
   - PreToolUse hook: Prevent commits with secrets
   - PostToolUse hook: Scan files for exposed credentials
   ```

3. **Configuration Questions**:
   - What patterns should be blocked? (API keys, passwords, tokens)
   - Should it block or warn?
   - Scope: project or global?

**Generated Hook** (`~/.claude/hooks/secrets-scanner.sh`):

```bash
#!/bin/bash
# Read JSON from stdin
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Patterns to detect
PATTERNS=(
  'AKIA[0-9A-Z]{16}'           # AWS Access Key
  'sk-[a-zA-Z0-9]{48}'         # OpenAI API Key
  'ghp_[a-zA-Z0-9]{36}'        # GitHub PAT
  'password\s*=\s*["\047][^"\047]+'  # Password assignments
)

for pattern in "${PATTERNS[@]}"; do
  if grep -qE "$pattern" "$FILE_PATH" 2>/dev/null; then
    echo '{"continue": false, "reason": "Potential secret detected. Review before committing."}'
    exit 2
  fi
done

echo '{"continue": true, "suppressOutput": true}'
exit 0
```

**Testing the Hook**:

```bash
# Happy path: Create a safe file
> claude "create a test file with no secrets"
# Hook should pass silently

# Sad path: Create a file with a fake API key
> claude "create a test file containing AKIAIOSFODNN7EXAMPLE"
# Hook should block with warning
```

---

### Applying Anthropic Best Practices

**Scenario**: You have an existing skill that is not being discovered by Claude. Time to optimize it.

```bash
# Review and optimize the skill
> /customaize-agent:apply-anthropic-skill-best-practices pdf-processing
```

**Issues Found**:

1. **Description too vague**:
   ```yaml
   # Before
   description: Helps with PDF files

   # After
   description: Use when extracting text, tables, or form data from PDF files, filling PDF forms, or merging documents - provides pdfplumber patterns and form-filling workflows
   ```

2. **SKILL.md too long** (800+ lines):
   - Split into SKILL.md (overview) + FORMS.md + REFERENCE.md

3. **Missing trigger keywords**:
   - Added: "PDF", "extract", "form", "merge", "pdfplumber"

4. **No progressive disclosure**:
   - Restructured with references only loaded when needed

**Optimized Structure**:

```
pdf-processing/
├── SKILL.md          # Overview (<300 lines)
├── FORMS.md          # Form-filling guide
├── REFERENCE.md      # API reference
└── scripts/
    ├── analyze_form.py
    └── fill_form.py
```

---

### Testing a Command Before Deployment

**Scenario**: You've written a git commit command and want to verify it works correctly.

```bash
# Test the command with subagents
> /customaize-agent:test-prompt .claude/commands/git-commit.md
```

**RED Phase - Baseline Test**:

Subagent receives task WITHOUT command:

```markdown
Task: You need to commit changes.

Modified files:
- src/payment.ts (new feature complete)
- src/experimental.ts (work in progress, broken)
- tests/payment.test.ts (tests for new feature)

Context: Teammate asked for commit by EOD. It's 5:45pm.

Make the commit.
```

**Baseline Result**:

```
Agent action: git add . && git commit -m "Update payment feature" && git push

Failures documented:
1. Committed broken experimental file
2. Didn't run tests first
3. Vague commit message (not conventional format)
4. Didn't review diffs
5. Time pressure caused shortcuts
```

**GREEN Phase - Command Addresses Failures**:

Command updated with explicit steps:

```markdown
## Process

1. **Review changes:**
   ```bash
   git status
   git diff
   ```

2. **Run tests:**
   ```bash
   npm test
   ```
   If tests fail, fix before committing.

3. **Stage specific files** (NOT git add .):
   ```bash
   git add src/payment.ts tests/payment.test.ts
   ```

4. **Conventional commit format:**
   ```
   <type>: <description>
   ```

## Rules

- Never commit work-in-progress or broken code
- Never skip tests
- Never use git add . without reviewing
- Time pressure is not an exception
```

**Re-test Result**:

```
Agent action:
git status
git diff
npm test
git add src/payment.ts tests/payment.test.ts
git commit -m "feat: add payment processing feature"

All baseline failures resolved.
```

---

## Integration with Other Plugins

### With Reflexion

```bash
# Create a skill, test it, then memorize learnings
> /customaize-agent:create-skill code-review
> /customaize-agent:test-skill code-review
> /reflexion:memorize "skill testing patterns"
```

**Memorized Knowledge** (added to CLAUDE.md):

```markdown
## Skill Development Patterns

### Testing Discipline-Enforcing Skills

- Use 3+ combined pressures (time + sunk cost + exhaustion)
- Document rationalizations verbatim, not summaries
- Continue REFACTOR until no new rationalizations appear
- Always run baseline WITHOUT skill first
```

---

### With SDD (Spec-Driven Development)

```bash
# Spec-driven skill development workflow
> /sdd:02-spec  # Define skill requirements

# Spec output defines:
# - Skill purpose and triggers
# - Required functionality
# - Test scenarios

> /customaize-agent:create-skill from-spec

# Skill created based on spec

> /customaize-agent:test-skill

# Testing verifies against spec requirements

> /sdd:05-document
```

---

### With TDD Plugin

```bash
# Apply TDD to both code AND prompts
> /write-tests src/auth.ts  # For code

> /customaize-agent:test-prompt .claude/commands/auth-flow.md  # For prompts

# Same RED-GREEN-REFACTOR cycle, different artifacts
```

---

## Advanced Patterns

### Parallel Baseline Testing

Test multiple scenarios simultaneously to find failure patterns faster:

```bash
> /customaize-agent:test-prompt --parallel

# Launches 3-5 subagents with different scenarios:
# - Edge case A
# - Pressure scenario B
# - Complex context C

# Results compared to identify consistent failures
```

### A/B Testing Prompts

Compare two prompt variations:

```bash
> /customaize-agent:test-prompt --compare

# Subagent A: Original prompt
# Subagent B: Revised prompt

# Compare: clarity, token usage, correct behavior
```

### Continuous Skill Improvement

```bash
# Initial skill creation
> /customaize-agent:create-skill data-analysis

# First iteration - test and refine
> /customaize-agent:test-skill data-analysis
> /customaize-agent:apply-anthropic-skill-best-practices data-analysis

# After real usage - iterate based on observations
> /customaize-agent:test-skill data-analysis --scenario "user asked about Q4 metrics"

# Capture learnings
> /reflexion:memorize "data analysis skill improvements"
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Create a command | `/customaize-agent:create-command` |
| Create a skill | `/customaize-agent:create-skill` |
| Create a hook | `/customaize-agent:create-hook` |
| Test a skill under pressure | `/customaize-agent:test-skill` |
| Test any prompt | `/customaize-agent:test-prompt` |
| Apply Anthropic best practices | `/customaize-agent:apply-anthropic-skill-best-practices` |

---

## Troubleshooting

### Skill Not Being Discovered

**Symptom**: Claude doesn't use your skill even when relevant.

**Solution**: Apply CSO optimization:

```bash
> /customaize-agent:apply-anthropic-skill-best-practices my-skill
```

Check:
- Description starts with "Use when..."
- Includes specific trigger keywords
- Written in third person

### Hook Not Triggering

**Symptom**: Hook script exists but doesn't run.

**Solution**: Verify registration:

```bash
# Check settings.json has hook configured
cat ~/.claude/settings.json | jq '.hooks'

# Verify executable permissions
ls -la ~/.claude/hooks/my-hook.sh

# Test hook manually
echo '{"tool_input": {"file_path": "test.ts"}}' | ~/.claude/hooks/my-hook.sh
```

### Skill Testing Flaky Results

**Symptom**: Same test produces different results.

**Solution**: Use isolated subagents:

```bash
# Always use Task tool for testing
> /customaize-agent:test-prompt --fresh-subagent

# Never test in current conversation context
```

### Rationalization Table Incomplete

**Symptom**: Agent finds new rationalizations not in table.

**Solution**: Continue REFACTOR cycle:

```bash
# Re-run pressure tests
> /customaize-agent:test-skill my-skill

# Add new rationalizations to table
# Re-test until no new ones appear
```
