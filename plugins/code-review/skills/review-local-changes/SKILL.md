---
description: Comprehensive review of local uncommitted changes using specialized agents with code improvement suggestions
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
disable-model-invocation: false
argument-hint: "[review-aspects]"
---

# Local Changes Review Instructions

You are an expert code reviewer conducting a thorough evaluation of local uncommitted changes. Your review must be structured, systematic, and provide actionable feedback including improvement suggestions.

**Review Aspects (optional):** "$ARGUMENTS"
**IMPORTANT**: Skip reviewing changes in `spec/` and `reports/` folders unless specifically asked.

## Review Workflow

Run a comprehensive code review of local uncommitted changes using multiple specialized agents, each focusing on a different aspect of code quality. Follow these steps precisely:

### Phase 1: Preparation

1. **Determine Review Scope**
   - Check git status to identify changed files: `git status --short`
   - Get detailed diff: `git diff --name-only`
   - Parse arguments to see if user requested specific review aspects

2. Use Haiku agent to give you a list of file paths to (but not the contents of) any relevant agent instruction files, if they exist: CLAUDE.md, AGENTS.md, **/constitution.md, the root README.md file, as well as any README.md files in the directories whose files were modified

3. Use a Haiku agent to analyze the changes and provide summary:

   ```markdown
   **Identify Changed Files**
      - Run `git diff --name-only` to see modified files
      - Run `git diff --stat` to see change statistics
      - Identify file types and scope of changes

   Please return a detailed summary of the local changes, including:
   - Full list of changed files and their types
   - Number of additions/deletions per file
   - Overall scope of the change (feature, bugfix, refactoring, etc.)
   ```

4. If there are no changes, inform the user and exit

### Phase 2: Searching for Issues and Improvements

Determine Applicable Reviews, then launch up to 6 parallel Sonnet agents to independently code review all local changes. The agents should do the following, then return a list of issues and the reason each issue was flagged (eg. CLAUDE.md or constitution.md adherence, bug, historical git context, etc.).

**Note**: The code-quality-reviewer agent should also provide code improvement and simplification suggestions with specific examples and reasoning.

**Available Review Agents**:

- **security-auditor** - Analyze code for security vulnerabilities
- **bug-hunter** - Scan for bugs and issues, including silent failures
- **code-quality-reviewer** - General code review for project guidelines, maintainability and quality. Simplifying code for clarity and maintainability
- **contracts-reviewer** - Analyze code contracts, including: type design and invariants (if new types added), API changes, data modeling, etc.
- **test-coverage-reviewer** - Review test coverage quality and completeness
- **historical-context-reviewer** - Review historical context of the code, including git blame and history of the code modified, and previous commits that touched these files.

Note: Default option is to run **all** applicable review agents.

#### Determine Applicable Reviews

Based on changes summary from phase 1, determine which review agents are applicable:

- **Always applicable**: bug-hunter, code-quality-reviewer (general quality), security-auditor, historical-context-reviewer
- **If test files changed**: test-coverage-reviewer
- **If types, API, data modeling changed**: contracts-reviewer

#### Launch Review Agents

**Parallel approach**:

- Launch all agents simultaneously
- Provide to them full list of modified files and summary of changes as context, also provide list of files with project guidelines and standards, including README.md, CLAUDE.md and constitution.md if they exist.
- Results should come back together

### Phase 3: Confidence Scoring

1. For each issue found in Phase 2, launch a parallel Haiku agent that takes the changes, issue description, and list of CLAUDE.md files (from step 2), and returns a score to indicate the agent's level of confidence for whether the issue is real or false positive. To do that, the agent should score each issue on a scale from 0-100, indicating its level of confidence. For issues that were flagged due to CLAUDE.md instructions, the agent should double check that the CLAUDE.md actually calls out that issue specifically. The scale is (give this rubric to the agent verbatim):
   a. 0: Not confident at all. This is a false positive that doesn't stand up to light scrutiny, or is a pre-existing issue.
   b. 25: Somewhat confident. This might be a real issue, but may also be a false positive. The agent wasn't able to verify that it's a real issue. If the issue is stylistic, it is one that was not explicitly called out in the relevant CLAUDE.md.
   c. 50: Moderately confident. The agent was able to verify this is a real issue, but it might be a nitpick or not happen very often in practice. Relative to the rest of the changes, it's not very important.
   d. 75: Highly confident. The agent double checked the issue, and verified that it is very likely it is a real issue that will be hit in practice. The existing approach in the changes is insufficient. The issue is very important and will directly impact the code's functionality, or it is an issue that is directly mentioned in the relevant CLAUDE.md.
   e. 100: Absolutely certain. The agent double checked the issue, and confirmed that it is definitely a real issue, that will happen frequently in practice. The evidence directly confirms this.

2. Filter out any issues with a score less than 80.

3. Format and output the comprehensive review report including:
   - All confirmed issues from Phase 2
   - Code improvement suggestions from the code-quality-reviewer agent
   - Prioritize improvements based on impact and alignment with project guidelines

#### Examples of false positives, for Phase 3

- Pre-existing issues in unchanged code
- Something that looks like a bug but is not actually a bug
- Pedantic nitpicks that a senior engineer wouldn't call out
- Issues that a linter, typechecker, or compiler would catch (eg. missing or incorrect imports, type errors, broken tests, formatting issues, pedantic style issues like newlines). No need to run these build steps yourself -- it is safe to assume that they will be run separately as part of CI.
- General code quality issues (eg. lack of test coverage, general security issues, poor documentation), unless explicitly required in CLAUDE.md
- Issues that are called out in CLAUDE.md, but explicitly silenced in the code (eg. due to a lint ignore comment)
- Changes in functionality that are likely intentional or are directly related to the broader change

Notes:

- Use build, lint and tests commands if you have access to them. They can help you find potential issues that are not obvious from the code changes.
- Make a todo list first
- You must cite each bug/issue/suggestion with file path and line numbers

### Template for Review Report

#### If you found issues or improvements

Output the review report in the following format:

```markdown
# 📋 Local Changes Review Report

## 🎯 Quality Assessment

**Quality Gate**: ⬜ READY TO COMMIT / ⬜ NEEDS FIXES

**Blocking Issues Count**: X

### Code Quality Scores
- **Security**: X/Y *(Passed security checks / Total applicable checks)*
  - Vulnerabilities: Critical: X, High: X, Medium: X, Low: X
- **Test Coverage**: X/Y *(Covered scenarios / Total critical scenarios)*
- **Code Quality**: X/Y *(Count of checked (correct) items / Total applicable items)*
- **Maintainability**: ⬜ Excellent / ⬜ Good / ⬜ Needs Improvement

---

## 🔄 Required Actions

### 🚫 Must Fix Before Commit
*(Blocking issues that prevent commit)*

1. 

### ⚠️ Better to Fix Before Commit
*(Issues that can be addressed now or later)*

1. 

### 💡 Consider for Future
*(Suggestions for improvement, not blocking)*

1. 

---

## 🐛 Found Issues & Bugs

Detailed list of issues and bugs found in the local changes:

| File:Lines | Issue | Evidence | Impact | 
|-----------|-------|----------|--------|
| `<file>:<lines>` | <brief description> | <evidence> | <impact> |

**Impact types**:
- **Critical**: Will cause runtime errors, data loss, or system crash
- **High**: Will break core features or corrupt data under normal usage
- **Medium**: Will cause errors under edge cases or degrade performance
- **Low**: Code smells that don't affect functionality but hurt maintainability

---

## 🔒 Security Vulnerabilities Found

Detailed list of security vulnerabilities found:

| Severity | File:Lines | Vulnerability Type | Specific Risk | Required Fix |
|----------|-----------|-------------------|---------------|--------------|
| <severity> | `<file>:<lines>` | <description> | <risk> | <fix> |

**Severity Classification**:
- **Critical**: Can be misused by bad actors to gain unauthorized access or fully shutdown the system
- **High**: Can be misused to perform actions without proper authorization or access sensitive data
- **Medium**: May cause issues in edge cases or degrade performance
- **Low**: Not have real impact on the system, but violates security practices

---

## 📋 Failed Checklist Items

Detailed list of failed code quality and test coverage checklist items:

| File:Lines | Issue | Description | Fix Required |
|-----------|-------|-------------|--------------|
| `[file]:[lines]` | [brief description] | [detailed description] | [required fix] |

---

## ✨ Code Improvements & Simplifications

1. **[Improvement description]**
   - **Priority**: High
   - **Affects**: `[file]:[function/method/class/variable]`
   - **Reasoning**: [why this improvement matters and what benefits it brings]
   - **Effort**: Low/Medium/High

```markdown

Notes:

- `<file>:<lines>` format: e.g., `src/utils/api.ts:23-45`
- For improvements, provide clear descriptions of what should be changed and why
- Prioritize improvements based on impact and alignment with project guidelines
- Be specific about file locations and line numbers
- Focus on actionable suggestions that developers can implement immediately

#### If you found no issues

```markdown
# 📋 Local Changes Review Report

## ✅ All Clear!

No critical issues found. The code changes look good!

**Checked for**:
- Bugs and logical errors ✓
- Security vulnerabilities ✓
- Code quality and maintainability ✓
- Test coverage ✓
- Guidelines compliance ✓

**Quality Gate**: ✅ READY TO COMMIT

---

## ✨ Optional Improvements

<If there are any non-blocking suggestions, list them here>


```

## Evaluation Guidelines

- **Security First**: Any High or Critical security issue automatically makes code not ready to commit
- **Quantify Everything**: Use numbers, not words like "some", "many", "few"
- **Be Pragmatic**: Focus on real issues and high-impact improvements
- **Skip Trivial Issues** in large changes (>500 lines):
  - Focus on architectural and security issues
  - Ignore minor naming conventions unless CLAUDE.md explicitly requires them
  - Prioritize bugs over style
- **Improvements Should Be Actionable**: Each suggestion should include concrete code examples
- **Consider Effort vs Impact**: Prioritize improvements with high impact and reasonable effort
- **Align with Project Standards**: Reference CLAUDE.md and project guidelines when suggesting improvements

## Remember

The goal is to catch bugs and security issues, improve code quality while maintaining development velocity, not to enforce perfection. Be thorough but pragmatic, focus on what matters for code safety, maintainability, and continuous improvement.

This review happens **before commit**, so it's a great opportunity to catch issues early and improve code quality proactively. However, don't block reasonable changes for minor style issues - those can be addressed in future iterations.
