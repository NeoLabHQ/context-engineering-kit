# Plugin Catalog

Browse hand-crafted plugins for improving Claude Code agent quality.

## Code Quality

### Code Review Checklist
**Location:** `plugins/code-quality/code-review-checklist/`
**Tokens:** ~400
**Command:** `/review-checklist`

Systematic code review using a comprehensive quality checklist. Covers correctness, security, performance, maintainability, and testing.

**Best for:** Pre-PR reviews, catching common issues, ensuring nothing is missed

---

## Testing

*Coming soon - contribute your testing plugins!*

---

## Documentation

*Coming soon - contribute your documentation plugins!*

---

## Installation

### Quick Install (Single Plugin)

```bash
# Navigate to your Claude Code plugins directory
cd ~/.claude-code/plugins/

# Clone the marketplace
git clone https://github.com/neolab/quality-agent.git

# Link specific plugin
ln -s quality-agent/plugins/code-quality/code-review-checklist ./
```

### Install All Plugins

```bash
# Clone the marketplace
git clone https://github.com/neolab/quality-agent.git ~/.claude-code/quality-agent

# Add to your Claude Code config to load all plugins
```

## Contributing

Have a plugin idea? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**We're looking for:**
- Test generation assistants
- Documentation improvers
- Code refactoring guides
- Architecture validators
- Performance analyzers

## Quality Standards

All plugins in this marketplace are:
- ✓ Hand-crafted for quality
- ✓ Token-efficient
- ✓ Well-documented
- ✓ Tested with real use cases
- ✓ Focused on specific improvements

## Support

- **Issues:** Report bugs or request features via GitHub Issues
- **Discussions:** Share ideas and ask questions in Discussions
- **Pull Requests:** Contribute new plugins or improvements
