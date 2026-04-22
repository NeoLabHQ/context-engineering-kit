# /git:attach-review-to-pr - PR Review Comments

Add line-specific review comments to pull requests using GitHub CLI API.

- Purpose - Attach detailed code review feedback to PRs
- Output - Review comments on specific lines

```bash
/git:attach-review-to-pr [pr-number]
```

## Arguments

PR number or URL (optional - can work with current branch).

## Usage Examples

```bash
# Add review comments to PR
> /git:attach-review-to-pr 456

# After code review
> /review-pr 456
> /git:attach-review-to-pr 456
```
