---
description: Add line-specific review comments to pull requests using GitHub CLI API
argument-hint: PR number or URL (optional - can work with current branch)
allowed-tools: Bash(gh api:*), Bash(gh auth:*), Bash(gh pr:*), mcp__github_inline_comment__create_inline_comment
---

# How to Attach Line-Specific Review Comments to Pull Requests

This guide explains how to add line-specific review comments to pull requests using the GitHub CLI (`gh`) API or `mcp__github_inline_comment__create_inline_comment` if it not available, similar to how the GitHub UI allows commenting on specific lines of code.

## Preferred Approach: Using MCP GitHub Tools

**If available**, use the `mcp__github_inline_comment__create_inline_comment` MCP tool for posting line-specific inline comments on pull requests. This approach provides better integration with GitHub's UI and is the recommended method.

**Fallback**: If the MCP tool is not available, use the GitHub CLI (`gh`) API methods described below:

- For single comments: Use the `/comments` endpoint (see [Adding a Single Line-Specific Comment](#adding-a-single-line-specific-comment))
- For multiple comments: Use the `/reviews` endpoint (see [Adding Multiple Line-Specific Comments Together](#adding-multiple-line-specific-comments-together))

## Overview

While `gh pr review` provides basic review functionality (approve, request changes, general comments), it **does not support line-specific comments directly**. To add comments on specific lines of code, you must use the lower-level `gh api` command to call GitHub's REST API directly.

## Prerequisites

1. GitHub CLI installed and authenticated:

   ```bash
   gh auth status
   ```

2. Access to the repository and pull request you want to review

## Understanding GitHub's Review Comment System

GitHub has two types of PR comments:

1. **Issue Comments** - General comments on the PR conversation
2. **Review Comments** - Line-specific comments on code changes

Review comments can be added in two ways:

- **Single comment** - Using the `/pulls/{pr}/comments` endpoint
- **Review with multiple comments** - Using the `/pulls/{pr}/reviews` endpoint

## Adding a Single Line-Specific Comment

### Basic Syntax

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  -f body='Your comment text here' \
  -f commit_id='<commit-sha>' \
  -f path='path/to/file.js' \
  -F line=42 \
  -f side='RIGHT'
```

### Parameters Explained

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `body` | string | Yes | The text of the review comment (supports Markdown) |
| `commit_id` | string | Yes | The SHA of the commit to comment on |
| `path` | string | Yes | Relative path to the file being commented on |
| `line` | integer | Yes | The line number in the diff (use `-F` for integers) |
| `side` | string | Yes | `RIGHT` for new/modified lines, `LEFT` for deleted lines |
| `start_line` | integer | No | For multi-line comments, the starting line |
| `start_side` | string | No | For multi-line comments, the starting side |

### Parameter Flags

- `-f` (--field) - For string values
- `-F` (--field) - For integer values (note the capital F)

### Complete Example

```bash
# First, get the latest commit SHA for the PR
gh api repos/NeoLabHQ/learning-platform-app/pulls/4 --jq '.head.sha'

# Then add your comment
gh api repos/NeoLabHQ/learning-platform-app/pulls/4/comments \
  -f body='Consider adding error handling here. Should we confirm the lesson was successfully marked as completed before navigating away?' \
  -f commit_id='e152d0dd6cf498467eadbeb638bf05abe11c64d4' \
  -f path='src/components/LessonNavigationButtons.tsx' \
  -F line=26 \
  -f side='RIGHT'
```

### Understanding Line Numbers

The `line` parameter refers to the **position in the diff**, not the absolute line number in the file:

- For **new files**: Line numbers match the file's line numbers
- For **modified files**: Use the line number as it appears in the "Files changed" tab
- For **multi-line comments**: Use `start_line` and `line` to specify the range

### Response

On success, returns a JSON object with comment details:

```json
{
  "id": 2532291222,
  "pull_request_review_id": 3470545909,
  "path": "src/components/LessonNavigationButtons.tsx",
  "line": 26,
  "body": "Consider adding error handling here...",
  "html_url": "https://github.com/NeoLabHQ/learning-platform-app/pull/4#discussion_r2532291222",
  "created_at": "2025-11-16T22:40:46Z"
}
```

## Adding Multiple Line-Specific Comments Together

To add multiple comments across different files in a single review, use the `/reviews` endpoint with JSON input.

### Why Use Reviews for Multiple Comments?

- **Atomic operation** - All comments are added together
- **Single notification** - Doesn't spam with multiple notifications
- **Better UX** - Appears as one cohesive review
- **Same mechanism as GitHub UI** - "Start a review" → "Finish review"

### Basic Syntax

```bash
cat <<'EOF' | gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews --input -
{
  "event": "COMMENT",
  "body": "Overall review summary (optional)",
  "comments": [
    {
      "path": "file1.tsx",
      "body": "Comment on file 1",
      "side": "RIGHT",
      "line": 15
    },
    {
      "path": "file2.tsx",
      "body": "Comment on file 2",
      "side": "RIGHT",
      "line": 30
    }
  ]
}
EOF
```

### Review Event Types

| Event | Description | When to Use |
|-------|-------------|-------------|
| `COMMENT` | General review comment | Just leaving feedback without approval |
| `APPROVE` | Approve the PR | Changes look good, ready to merge |
| `REQUEST_CHANGES` | Request changes | Issues that must be fixed before merge |

### Complete Example

```bash
cat <<'EOF' | gh api repos/NeoLabHQ/learning-platform-app/pulls/4/reviews --input -
{
  "event": "COMMENT",
  "body": "Testing multiple line-specific comments via gh api",
  "comments": [
    {
      "path": "src/components/CourseCard.tsx",
      "body": "Test comment generated by Claude",
      "side": "RIGHT",
      "line": 15
    },
    {
      "path": "src/components/CourseProgressWidget.tsx",
      "body": "Test comment generated by Claude",
      "side": "RIGHT",
      "line": 30
    },
    {
      "path": "src/components/LessonProgressTracker.tsx",
      "body": "Test comment generated by Claude",
      "side": "RIGHT",
      "line": 20
    }
  ]
}
EOF
```

### Response

```json
{
  "id": 3470546747,
  "state": "COMMENTED",
  "html_url": "https://github.com/NeoLabHQ/learning-platform-app/pull/4#pullrequestreview-3470546747",
  "submitted_at": "2025-11-16T22:42:43Z",
  "commit_id": "e152d0dd6cf498467eadbeb638bf05abe11c64d4"
}
```

## Common Issues and Solutions

### Issue 1: "user_id can only have one pending review per pull request"

**Error Message:**

```
gh: Validation Failed (HTTP 422)
{"message":"Validation Failed","errors":[{"resource":"PullRequestReview","code":"custom","field":"user_id","message":"user_id can only have one pending review per pull request"}]}
```

**Cause:** GitHub only allows one pending (unsubmitted) review per user per PR. If you previously started a review through the UI or API and didn't submit it, it blocks new review creation.

**Solution 1: Submit the pending review**

```bash
# Check for pending reviews
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews | jq '.[] | select(.state=="PENDING")'

# Submit it through the UI or ask the user to submit it
```

**Solution 2: Use the single comment endpoint instead**

```bash
# Add individual comments without creating a review
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  -f body='Comment text' \
  -f commit_id='<sha>' \
  -f path='file.tsx' \
  -F line=26 \
  -f side='RIGHT'
```

### Issue 2: Array syntax not working with --raw-field

**Failed Attempt:**

```bash
# This does NOT work - GitHub API receives an object, not an array
gh api repos/{owner}/{repo}/pulls/{pr}/reviews \
  --raw-field 'comments[0][path]=file1.tsx' \
  --raw-field 'comments[0][line]=15' \
  --raw-field 'comments[1][path]=file2.tsx' \
  --raw-field 'comments[1][line]=30'
```

**Error:**

```
Invalid request. For 'properties/comments', {"0" => {...}, "1" => {...}} is not an array.
```

**Solution:** Use JSON input via heredoc:

```bash
cat <<'EOF' | gh api repos/{owner}/{repo}/pulls/{pr}/reviews --input -
{
  "comments": [...]
}
EOF
```

### Issue 3: Invalid line number

**Error Message:**

```
Pull request review thread line must be part of the diff
```

**Cause:** The line number doesn't exist in the diff for this file.

**Solutions:**

- Verify the file was actually changed in this PR
- Check the "Files changed" tab to see actual line numbers in the diff
- Ensure you're using the correct `commit_id` (the latest commit in the PR)

### Issue 4: Wrong commit_id

**Error Message:**

```
commit_sha is not part of the pull request
```

**Solution:** Get the latest commit SHA:

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number} --jq '.head.sha'
```

## Best Practices

### 1. Get PR Information First

Before adding comments, gather necessary information:

```bash
# Get PR details
gh pr view {pr_number} --json headRefOid,files

# Or use the API
gh api repos/{owner}/{repo}/pulls/{pr_number} --jq '{commit: .head.sha, files: [.changed_files]}'

# List files changed
gh api repos/{owner}/{repo}/pulls/{pr_number}/files --jq '.[] | {filename: .filename, additions: .additions, deletions: .deletions}'
```

### 2. Check for Pending Reviews

```bash
# Check if you have a pending review
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --jq '.[] | select(.state=="PENDING" and .user.login=="YOUR_USERNAME")'
```

### 3. Use Meaningful Comment Text

- Be specific and constructive
- Reference documentation or best practices
- Suggest alternatives when requesting changes
- Use code blocks for code suggestions:

```markdown
Consider using async/await:

\`\`\`typescript
async function getData() {
  const result = await fetch(url);
  return result.json();
}
\`\`\`
```

### 4. Batch Related Comments

Use the review endpoint to group related comments:

- All comments for a single file/area
- All comments for a specific concern (security, performance, etc.)
- Complete review session

### 5. Choose the Right Event Type

```bash
# For feedback during development
"event": "COMMENT"

# When approving
"event": "APPROVE"

# When blocking merge
"event": "REQUEST_CHANGES"
```

## Workflow Examples

### Example 1: Quick Single Comment

```bash
#!/bin/bash
OWNER="NeoLabHQ"
REPO="learning-platform-app"
PR=4

# Get latest commit
COMMIT=$(gh api repos/$OWNER/$REPO/pulls/$PR --jq '.head.sha')

# Add comment
gh api repos/$OWNER/$REPO/pulls/$PR/comments \
  -f body='Consider extracting this into a separate function for better testability' \
  -f commit_id="$COMMIT" \
  -f path='src/utils/validation.ts' \
  -F line=45 \
  -f side='RIGHT'
```

### Example 2: Comprehensive Review

```bash
#!/bin/bash
OWNER="NeoLabHQ"
REPO="learning-platform-app"
PR=4

# Create review with multiple comments
cat <<EOF | gh api repos/$OWNER/$REPO/pulls/$PR/reviews --input -
{
  "event": "COMMENT",
  "body": "Thanks for the PR! I've reviewed the changes and have a few suggestions.",
  "comments": [
    {
      "path": "src/components/CourseCard.tsx",
      "body": "Consider memoizing this component to prevent unnecessary re-renders",
      "side": "RIGHT",
      "line": 25
    },
    {
      "path": "src/utils/courseProgress.ts",
      "body": "This function could benefit from error handling for invalid course IDs",
      "side": "RIGHT",
      "line": 12
    },
    {
      "path": "src/state/CourseProgressState.ts",
      "body": "Consider adding JSDoc comments to document the expected behavior",
      "side": "RIGHT",
      "line": 8
    }
  ]
}
EOF
```

### Example 3: Multi-line Comment

```bash
# Comment on a range of lines (e.g., lines 10-15)
gh api repos/$OWNER/$REPO/pulls/$PR/comments \
  -f body='This entire block could be simplified using array destructuring' \
  -f commit_id="$COMMIT" \
  -f path='src/utils/parser.ts' \
  -F start_line=10 \
  -f start_side='RIGHT' \
  -F line=15 \
  -f side='RIGHT'
```

## Helpful Helper Scripts

### Get PR Files and Lines

```bash
#!/bin/bash
# pr-files.sh - List all files changed in a PR with line counts

OWNER="$1"
REPO="$2"
PR="$3"

gh api repos/$OWNER/$REPO/pulls/$PR/files --jq '.[] | "\(.filename): +\(.additions)/-\(.deletions)"'
```

### Check Review Status

```bash
#!/bin/bash
# check-reviews.sh - Check review status for a PR

OWNER="$1"
REPO="$2"
PR="$3"

echo "=== Reviews ==="
gh api repos/$OWNER/$REPO/pulls/$PR/reviews --jq '.[] | "\(.user.login): \(.state) at \(.submitted_at)"'

echo -e "\n=== Pending Reviews ==="
gh api repos/$OWNER/$REPO/pulls/$PR/reviews --jq '.[] | select(.state=="PENDING") | "\(.user.login): \(.state)"'
```

## Related Documentation

- [GitHub API: Pull Request Review Comments](https://docs.github.com/rest/pulls/comments)
- [GitHub API: Pull Request Reviews](https://docs.github.com/rest/pulls/reviews)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Create PR Command](./create-pr.md)
- [Commit Command](./commit.md)

## API Reference

### POST /repos/{owner}/{repo}/pulls/{pull_number}/comments

Creates a review comment on a specific line.

**Endpoint:** `https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments`

**Parameters:**

- `body` (string, required): Comment text
- `commit_id` (string, required): SHA of commit
- `path` (string, required): Relative file path
- `line` (integer, required): Line number in diff
- `side` (string, required): "LEFT" or "RIGHT"
- `start_line` (integer, optional): Start line for multi-line
- `start_side` (string, optional): Start side for multi-line

### POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews

Creates a review with optional line-specific comments.

**Endpoint:** `https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews`

**Parameters:**

- `event` (string, required): "APPROVE", "REQUEST_CHANGES", or "COMMENT"
- `body` (string, optional): Overall review comment
- `comments` (array, optional): Array of comment objects
- `commit_id` (string, optional): SHA of commit to review

**Comment Object:**

- `path` (string, required): Relative file path
- `body` (string, required): Comment text
- `line` (integer, required): Line number in diff
- `side` (string, required): "LEFT" or "RIGHT"
- `start_line` (integer, optional): Start line for multi-line
- `start_side` (string, optional): Start side for multi-line
