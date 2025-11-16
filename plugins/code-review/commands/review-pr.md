---
description: Comprehensive pull request review using specialized agents
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task", "Bash(gh issue view:*)", "Bash(gh search:*)", "Bash(gh issue list:*)", "Bash(gh pr comment:*)", "Bash(gh pr diff:*)", "Bash(gh pr view:*)", "Bash(gh pr list:*)"]
disable-model-invocation: false
argument-hint: "[review-aspects]"
---

# Pull Request Review Instructions

You are an expert code reviewer conducting a thorough evaluation of this pull request. Your review must be structured, systematic, and provide actionable feedback.

**Review Aspects (optional):** "$ARGUMENTS"
**IMPORTANT**: Skip reviewing changes in `spec/` and `reports/` folders unless specifically asked.

## Review Workflow

Run a comprehensive pull request review using multiple specialized agents, each focusing on a different aspect of code quality. Follow these steps precisely:

### Phase 1: Preparation

1. Use a Haiku agent to check if the pull request (a) is closed, (b) is a draft, (c) does not need a code review (eg. because it is an automated pull request, or is very simple and obviously ok), or (d) already has a code review from you from earlier. If so, do not proceed.
2. **Determine Review Scope**
   - Check git status to identify changed files
   - Parse arguments to see if user requested specific review aspects
3. Use Haiku agent to give you a list of file paths to (but not the contents of) any relevant agent instruction files, if they exist: CLAUDE.md, AGENTS.md, **/consitution.md, the root README.md file, as well as any README.md files in the directories whose files the pull request modified
4. Use a Haiku agent to view the pull request, ask him following:

   ```markdown
   **Identify Changed Files**
      - Run `git diff --name-only` to see modified files
      - Check if PR already exists: `gh pr view`
      - Identify file types

   Please return a detailed summary of the change in the pull request, including full list of changed files and their types.
   ```

5. Ask Haiku agent to:

   ```markdown
   If PR missing description, add a description to the PR with summary of changes in short and concise format.
   ```

### Phase 2: Searching for Issues

Determine Applicable Reviews, then launch up to 6 parallel Sonnet agents to independently code review all changes in the pull request. The agents should do the following, then return a list of issues and the reason each issue was flagged (eg. CLAUDE.md or consitution.md adherence, bug, historical git context, etc.).

**Available Review Agents**:

- **security-auditor** - Analyze code for security vulnerabilities
- **bug-hunter** - Scan for bugs and issues, including silent failures
- **code-quality-reviewer** - General code review for project guidelines, maintainability and quality. Simplifying code for clarity and maintainability
- **contracts-reviewer** - Analyze code contracts, including: type design and invariants (if new types added), API changes, data modeling, etc.
- **test-coverage-reviewer** - Review test coverage quality and completeness
- **historical-context-reviewer** - Review historical context of the code, including git blame and history of the code modified, and previous pull requests that touched these files.

Note: Default option is to run **all** applicable review agents.

#### Determine Applicable Reviews

Based on changes summary from phase 1, determine which review agents are applicable:

- **Always applicable**: bug-hunter, code-quality-reviewer (general quality), security-auditor, historical-context-reviewer
- **If test files changed**: test-coverage-reviewer
- **If types, API, data modeling changed**: contracts-reviewer

#### Launch Review Agents

**Parallel approach**:

- Launch all agents simultaneously
- Provide to them full list of modified files and summary of the PR as a context, explicitly highlight which PR they are reviewing, also provide list of files with project guidelines and standards, including README.md, CLAUDE.md and consitution.md if they exist.
- Results should come back together

### Phase 3: Confidence & Impact Scoring

1. For each issue found in Phase 2, launch a parallel Haiku agent that takes the PR, issue description, and list of CLAUDE.md files (from step 2), and returns TWO scores:

   **Confidence Score (0-100)** - Level of confidence that the issue is real and not a false positive:

   a. 0: Not confident at all. This is a false positive that doesn't stand up to light scrutiny, or is a pre-existing issue.
   b. 25: Somewhat confident. This might be a real issue, but may also be a false positive. The agent wasn't able to verify that it's a real issue. If the issue is stylistic, it is one that was not explicitly called out in the relevant CLAUDE.md.
   c. 50: Moderately confident. The agent was able to verify this is a real issue, but it might be a nitpick or not happen very often in practice. Relative to the rest of the PR, it's not very important.
   d. 75: Highly confident. The agent double checked the issue, and verified that it is very likely it is a real issue that will be hit in practice. The existing approach in the PR is insufficient. The issue is very important and will directly impact the code's functionality, or it is an issue that is directly mentioned in the relevant CLAUDE.md.
   e. 100: Absolutely certain. The agent double checked the issue, and confirmed that it is definitely a real issue, that will happen frequently in practice. The evidence directly confirms this.

   **Impact Score (0-100)** - Severity and consequence of the issue if left unfixed:

   a. 0-20 (Low): Minor code smell or style inconsistency. Does not affect functionality or maintainability significantly.
   b. 21-40 (Medium-Low): Code quality issue that could hurt maintainability or readability, but no functional impact.
   c. 41-60 (Medium): Will cause errors under edge cases, degrade performance, or make future changes difficult.
   d. 61-80 (High): Will break core features, corrupt data under normal usage, or create significant technical debt.
   e. 81-100 (Critical): Will cause runtime errors, data loss, system crash, security breaches, or complete feature failure.

   For issues flagged due to CLAUDE.md instructions, the agent should double check that the CLAUDE.md actually calls out that issue specifically.

2. **Filter issues using the progressive threshold table below** - Higher impact issues require less confidence to pass:

   | Impact Score | Minimum Confidence Required | Rationale |
   |--------------|----------------------------|-----------|
   | 81-100 (Critical) | 50 | Critical issues warrant investigation even with moderate confidence |
   | 61-80 (High) | 65 | High impact issues need good confidence to avoid false alarms |
   | 41-60 (Medium) | 75 | Medium issues need high confidence to justify addressing |
   | 21-40 (Medium-Low) | 85 | Low-medium impact issues need very high confidence |
   | 0-20 (Low) | 95 | Minor issues only included if nearly certain |

   **Filter out any issues that don't meet the minimum confidence threshold for their impact level.** If there are no issues that meet this criteria, do not proceed.
3. Use a Haiku agent to repeat the eligibility check from Phase 1, to make sure that the pull request is still eligible for code review. (In case if there was updates since review started)
4. **Post Review Comments**:

   a. First, check if the `git:attach-review-to-pr` command is available by reading it.

   b. If the command is available and issues were found:
      - **Multiple Issues**: Use `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews` to create a review with line-specific comments for each issue. Include the Quality Gate summary, Blocking Issues Count, Security, Test Coverage, and Code Quality scores in the review body, and add each issue as a line-specific comment in the `comments` array.
      - **Single Issue**: Use `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments` to add just one line-specific comment for that issue.

   c. If the command is NOT available, fall back to posting a single comment using `gh pr comment` with the full review report.

   When writing comments, keep in mind to:
   - Keep your output brief
   - Use emojis
   - Link and cite relevant code, files, and URLs

#### Examples of false positives, for Phase 3

- Pre-existing issues
- Something that looks like a bug but is not actually a bug
- Pedantic nitpicks that a senior engineer wouldn't call out
- Issues that a linter, typechecker, or compiler would catch (eg. missing or incorrect imports, type errors, broken tests, formatting issues, pedantic style issues like newlines). No need to run these build steps yourself -- it is safe to assume that they will be run separately as part of CI.
- General code quality issues (eg. lack of test coverage, general security issues, poor documentation), unless explicitly required in CLAUDE.md
- Issues that are called out in CLAUDE.md, but explicitly silenced in the code (eg. due to a lint ignore comment)
- Changes in functionality that are likely intentional or are directly related to the broader change
- Real issues, but on lines that the user did not modify in their pull request

Notes:

- Use build, lint and tests commands if you have access to them. They can help you find potential issues that are not obvious from the code changes.
- Use `gh` to interact with Github (eg. to fetch a pull request, or to create inline comments), rather than web fetch
- Make a todo list first
- You must cite and link each bug (eg. if referring to a CLAUDE.md, you must link it)
- When using line-specific comments (via `git:attach-review-to-pr`):
  - Each issue should map to a specific file and line number
  - For multiple issues: Use `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews` with JSON input containing the review body (Quality Gate summary) and comments array (line-specific issues)
  - For single issue: Use `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments` to post just one line-specific comment

### Template for line-specific review comments

When using the `git:attach-review-to-pr` command to add line-specific comments, use this template for each issue:

```markdown
**[Issue Category]**: [Brief description]

**Evidence**: 
[Explain what code pattern/behavior was observed that indicates this issue]

**[Impact/Severity]**: [Critical/High/Medium/Low]
[Explain the consequence if left unfixed]

**Confidence**: [X/100]
[Brief justification for confidence score]

**Suggested Fix**:
[Provide actionable guidance on how to resolve this issue]
```

**Example for Bug Issue**:

```markdown
**Bug**: Potential null pointer dereference

**Evidence**: 
Variable `user` is accessed without null check after fetching from database.

**Impact**: High
Will cause runtime error if user is not found, breaking the user profile feature.

**Confidence**: 85/100
Verified by tracing data flow - `findUser()` can return null but no guard is present.

**Suggested Fix**:
Add null check before accessing user properties:
\`\`\`typescript
if (!user) {
  throw new Error('User not found');
}
\`\`\`
```

**Example for Security Issue**:

```markdown
**Security**: SQL Injection vulnerability

**Evidence**: 
User input is directly concatenated into SQL query without sanitization.

**Severity**: Critical
Attackers can execute arbitrary SQL commands, leading to data breach or deletion.

**Confidence**: 95/100
Direct string concatenation with user input is a well-known SQL injection vector.

**Suggested Fix**:
Use parameterized queries:
\`\`\`typescript
db.query('SELECT * FROM users WHERE id = ?', [userId])
\`\`\`
```

### Template for review using GitHub API

#### Multiple Issues (using `/reviews` endpoint)

When using `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews`, structure your review as:

**Review body format** (Quality Gate summary):

```markdown
# PR Review Report

**Quality Gate**: ⬜ PASS (Can merge) / ⬜ FAIL (Requires fixes)

**Blocking Issues Count**: X
- Security: X/Y *(Passed security checks / Total applicable checks)*
  - Vulnerabilities: Critical: X, High: X, Medium: X, Low: X
- Test Coverage: X/Y *(Covered scenarios / Total critical scenarios)*
- Code Quality: X/Y *(Count of checked (correct) items / Total applicable items)*
```

**Comments array**: Each comment uses the line-specific template above (Issue Category, Evidence, Impact/Severity, Confidence, Suggested Fix).

#### Single Issue (using `/comments` endpoint)

When using `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments`, post just one line-specific comment using the template above.

#### Fallback: Overall review comment (using `gh pr comment`)

This template is used when `git:attach-review-to-pr` command is NOT available.

When posting the overall review comment to the pull request, follow the following format precisely:

```markdown
# PR Review Report

**Quality Gate**: ⬜ PASS (Can merge) / ⬜ FAIL (Requires fixes)

**Blocking Issues Count**: X
- Security 
   - Score: X/Y** *(Passed security checks / Total applicable checks)*
   - Vulnerabilities: Critical: X, High: X, Medium: X, Low: X
- Test Coverage
   - Score: X/Y** *(Covered scenarios / Total critical scenarios)*
- Code Quality
   - Score: X/Y** *(Count of checked (correct) items / Total applicable items)*

## 🔄 Required Actions

### 🚫 Must Fix Before Merge
*(Blocking issues that prevent merge)*

1. 

### ⚠️ Better to Fix Before Merge
*(Issues that can be addressed in this or in next PRs)*

1. 

### 💡 Consider for Future
*(Suggestions for improvement, not blocking)*

1. 

---

## 🐛 Found Issues & Bugs & Checklist Items

Detailed list of issues and bugs found in the pull request:

| Link to file | Issue | Evidence | Impact | 
|--------------|-------|----------|--------|
| <link to file> | <brief description of bug or issue> | <evidence> | <impact> |

Impact types:
- Critical: Will cause runtime errors, data loss, or system crash
- High: Will break core features or corrupt data under normal usage
- Medium: Will cause errors under edge cases or degrade performance
- Low: Will cause code smells that don't affect functionality but hurt maintainability

### Security Vulnerabilities Found

Detailed list of security vulnerabilities found in the pull request:

| Severity | Link to file | Vulnerability Type | Specific Risk | Required Fix |
|----------|------|------|-------------------|---------------|--------------|
| <severity> | <link to file> | <brief description of vulnerability> | <specific risk> | <required fix> |


**Severity Classification**:
   - **Critical**: Can be misused by bad actors to gain unauthorized access to the system or fully shutdown the system
   - **High**: Can be misused to perform some actions without proper authorization or get access to some sensitive data
   - **Medium**: May cause issues in edge cases or degrade performance
   - **Low**: Not have real impact on the system, but violates security practices

```

Note:

- <link to file> - is a link to file and line with full sha1 + line range for context, note that you MUST provide the full sha and not use bash here, eg. https://github.com/anthropics/claude-code/blob/1d54823877c4de72b2316a64032a54afc404e619/README.md#L13-L17
- When linking to code, follow the following format precisely, otherwise the Markdown preview won't render correctly: <https://github.com/anthropics/claude-cli-internal/blob/c21d3c10bc8e898b7ac1a2d745bdc9bc4e423afe/package.json#L10-L15>
  - Requires full git sha
  - You must provide the full sha. Commands like `https://github.com/owner/repo/blob/$(git rev-parse HEAD)/foo/bar` will not work, since your comment will be directly rendered in Markdown.
  - Repo name must match the repo you're code reviewing

  - # sign after the file name

  - Line range format is L[start]-L[end]
  - Provide at least 1 line of context before and after, centered on the line you are commenting about (eg. if you are commenting about lines 5-6, you should link to `L4-7`)

Evaluation Instructions

- **Security First**: Any High or Critical security issue automatically becomes blocker for merge
- **Quantify Everything**: Use numbers, not words like "some", "many", "few"
- **Skip Trivial Issues** in large PRs (>500 lines):
  - Focus on architectural and security issues
  - Ignore minor naming conventions
  - Prioritize bugs over style

#### If you found no issues

When no issues are found after filtering, post a comment using `gh pr comment`:

```markdown
# PR Review Report

No issues found. Checked for bugs and CLAUDE.md compliance.
```

## Remember

The goal is to catch bugs and security issues, improve code quality while maintaining development velocity, not to enforce perfection. Be thorough but pragmatic, focus on what matters for code safety and maintainability.
