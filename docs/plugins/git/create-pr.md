# /git:create-pr - Pull Request Creation

Create pull requests using GitHub CLI with proper templates and formatting.

- Purpose - Streamline PR creation with consistent formatting
- Output - GitHub pull request with template

```bash
/create-pr
```

## Arguments

None required - interactive guide for PR creation.

## How It Works

1. **Branch Detection**: Identifies current branch and target base branch
2. **Template Search**: Looks for PR templates in `.github/` directory
3. **Change Summary**: Analyzes commits to generate description
4. **PR Creation**: Uses `gh pr create` with formatted content
5. **Issue Linking**: Automatically links related issues

## Usage Examples

```bash
# Create PR for current branch
> /create-pr

# After completing feature
> /commit
> /create-pr

# Full workflow
> /analyze-issue 123
> claude "implement feature"
> /commit
> /create-pr
```

## Best Practices

- Push branch first - Ensure branch is pushed to remote
- Use descriptive titles - Clear summary of changes
- Link issues - Reference related issues in description
- Request reviewers - Add appropriate team members
