# /git:load-issues - Load Open Issues

Load all open issues from GitHub and save them as markdown files.

- Purpose - Bulk import issues for planning and analysis
- Output - Markdown files for each open issue

```bash
/git:load-issues
```

## Arguments

None required - loads all open issues automatically.

## How It Works

1. **Issue Retrieval**: Fetches all open issues from repository
2. **Content Extraction**: Parses issue title, body, labels, and metadata
3. **File Generation**: Creates markdown file for each issue
4. **Organization**: Structures files in designated directory

## Usage Examples

```bash
# Load all issues for sprint planning
> /load-issues

# Then analyze specific issues
> /analyze-issue 123
```

## Best Practices

- Use for sprint planning - Get overview of all open work
- Combine with analysis - Analyze high-priority issues in detail
- Regular updates - Reload periodically to stay current
