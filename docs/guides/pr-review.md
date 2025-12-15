# PR Review and Merge

Comprehensive pull request review using specialized agents to catch issues before merging code.

Other types of reviews:

- Local changes only - For pre-commit local review, use `/code-review:review-local-changes` command directly.
- CI Integration - You can automate PR reviews using GitHub Actions. See the [CI/CD Integration guide](./ci-integration.md) for setup instructions.


## When to Use

- Reviewing pull requests before merging
- Getting multi-perspective code analysis on PR changes
- Ensuring code quality standards are met before merge
- Catching security vulnerabilities and bugs in proposed changes

## Plugins needed for this workflow

- [Code Review](../plugins/code-review/README.md)
- [Reflexion](../plugins/reflexion/README.md)
- [Git](../plugins/git/README.md)

## Workflow

### How It Works

```md
+---------------------------------------------+
| 1. Review PR with Specialized Agents        |
|    (run multi-agent code review)            |
+--------------------+------------------------+
                     |
                     | six agents analyze from different perspectives
                     v
+---------------------------------------------+
| 2. Analyze Findings                         |
|    Review prioritized issues by severity    |
+--------------------+------------------------+
                     |
                     | critical/high issues require attention
                     v
+---------------------------------------------+
| 3. Address Findings                         | <--- iterate until clean ---+
|    Fix issues locally                       |                             |
+--------------------+------------------------+                             |
                     |                                                      |
                     | changes made locally                                 |
                     v                                                      |
+---------------------------------------------+                             |
| 4. Re-review Local Changes                  |                             |
|    Verify fixes resolve issues              +-----------------------------+
+--------------------+------------------------+
                     |
                     | all critical/high issues resolved
                     v
+---------------------------------------------+
| 5. Get Final Critique                       |
|    Multi-perspective quality check          |
+--------------------+------------------------+
                     |
                     | final validation passed
                     v
+---------------------------------------------+
| 6. Push Updates                             |
|    Push fixed changes to PR branch          |
+--------------------+------------------------+
                     |
                     | changes pushed
                     v
+---------------------------------------------+
| 7. Preserve Learnings                       |
|    Save patterns to project memory          |
+---------------------------------------------+
```

### 1. Review PR with specialized agents

Use the `/code-review:review-pr` command to analyze a pull request with six specialized agents: Bug Hunter, Security Auditor, Test Coverage Reviewer, Code Quality Reviewer, Contracts Reviewer, and Historical Context Reviewer.

```bash
/code-review:review-pr #123
```

After LLM completes, you receive a structured report with findings categorized by severity (Critical, High, Medium, Low). Each agent provides specific findings with file locations and line references.

### 2. Analyze findings

Review the generated report and identify issues that must be addressed before merging. Focus on Critical and High priority items first.

```md
# Typical Report Structure

## Critical Issues (Must Fix)
- Security vulnerability in authentication middleware
- Missing input validation on user endpoints

## High Priority (Should Fix)
- Potential null pointer in data processing
- Missing error handling in API calls

## Medium Priority (Consider Fixing)
- Code duplication in utility functions
- Missing unit tests for edge cases

## Low Priority (Nice to Have)
- Naming convention inconsistencies
- Documentation gaps
```

After reviewing, create a mental checklist of issues to address. Critical and High priority issues should be fixed before merging.

### 3. Address findings

Fix the identified issues in your local environment. You can ask Claude to help address specific concerns from the review.

```bash
claude "Fix security concerns in authentication middleware"
```

After LLM completes, the issues should be resolved in your local working directory. You may need to address multiple findings iteratively.

### 4. Re-review local changes

Use the `/code-review:review-local-changes` command to verify your fixes resolve the identified issues and do not introduce new problems.

```bash
/code-review:review-local-changes
```

After LLM completes, compare the new findings with the original PR review. If Critical or High priority issues remain, return to step 3 and continue fixing. Repeat until the review is clean.

### 5. Get final critique

Use the `/reflexion:critique` command to get an additional multi-perspective review before pushing. This provides a final quality check from multiple specialized judges.

```bash
/reflexion:critique
```

After LLM completes, review the critique feedback. Address any significant concerns raised. The critique offers perspectives that complement the code review agents.

### 6. Push updates

Push your local fixes to the PR branch once all significant issues are resolved.

```bash
git push
```

After push completes, the PR will be updated with your fixes. Reviewers can now see the improved code.

### 7. Preserve learnings

Use the `/reflexion:memorize` command to save valuable patterns, decisions, and insights discovered during the review process to your project memory.

```bash
/reflexion:memorize
```

After LLM completes, your CLAUDE.md file is updated with learnings from this review cycle. These insights help improve future development and reviews.

## Tips for Effective PR Reviews

**Prioritize by severity**: Always address Critical issues first, then High, then Medium. Low priority items can be tracked as separate issues.

**Iterate efficiently**: Run review commands after each batch of fixes rather than after each individual fix to save time.

**Learn from patterns**: Use `/reflexion:memorize` to capture recurring issues as project guidelines to prevent them in future PRs.

**Combine perspectives**: The six review agents and reflexion critique provide complementary views - consider all perspectives before marking issues as resolved.

