---
description: Analyze a GitHub issue and create a detailed technical specification
argument-hint: Issue number (e.g., 42)
allowed-tools: Bash(gh issue:*), Read, Write, Glob, Grep
---

Please analyze GitHub issue #$ARGUMENTS and create a technical specification.

Follow these steps:

1. Check if the issue is already loaded:
   - Look for the issue file in `./specs/issues/` folder
   - File naming pattern: `<number-padded-to-3-digits>-<kebab-case-title>.md`
   - If not found, fetch the issue details from GitHub (see step 2)

2. Fetch the issue details (if not already loaded):
   - Read `.claude/commands/load-issues.md` to understand how to fetch issue details
   - Save the issue file following the load-issues.md format

3. Understand the requirements thoroughly
4. Review related code and project structure
5. Create a technical specification with the format below

# Technical Specification for Issue #$ARGUMENTS

## Issue Summary
- Title: [Issue title from GitHub]
- Description: [Brief description from issue]
- Labels: [Labels from issue]
- Priority: [High/Medium/Low based on issue content]

## Problem Statement
[1-2 paragraphs explaining the problem]

## Technical Approach
[Detailed technical approach]

## Implementation Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Test Plan
1. Unit Tests:
   - [test scenario]
2. Component Tests:
   - [test scenario]
3. Integration Tests:
   - [test scenario]

## Files to Modify
- [file path]: [changes]

## Files to Create
- [file path]: [purpose]

## Existing Utilities to Leverage
- [utility name/path]: [purpose]

## Success Criteria
- [ ] [criterion 1]
- [ ] [criterion 2]

## Out of Scope
- [item 1]
- [item 2]

Remember to follow our strict TDD principles, KISS approach, and 300-line file limit.

IMPORTANT: After completing your analysis, SAVE the full technical specification to:
`./specs/issues/<number-padded-to-3-digits>-<kebab-case-title>.specs.md`

For example, for issue #7 with title "Make code review trigger on any *.SQL and .sh file changes", save to:
`./specs/issues/007-make-code-review-trigger-on-sql-sh-changes.specs.md`

After saving, provide a brief summary to the user confirming:
- Issue number and title analyzed
- File path where the specification was saved
- Key highlights from the specification (2-3 bullet points)
