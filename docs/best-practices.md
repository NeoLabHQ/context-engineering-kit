# Tips and Best Practices

## Token Efficiency

**Install only what you need:**

```bash
# ❌ Don't install all plugins
/plugin install reflexion@NeoLabHQ/context-engineering-kit
/plugin install code-review@NeoLabHQ/context-engineering-kit
/plugin install sdd@NeoLabHQ/context-engineering-kit
# ... (if you won't use them all)

# ✅ Install only plugins that you expect to use
/plugin install reflexion@NeoLabHQ/context-engineering-kit  # For today's feature work
```

## Maximizing Quality

**Use quality gates:**

- Review after implementation
- Reflect before finalizing
- Critique for critical code

**Leverage specialized agents:**

- Code review agents catch domain-specific issues
- SDD agents provide specialized expertise
- Multiple agents offer diverse perspectives

**Maintain CLAUDE.md:**

- Update after major work
- Review and refine regularly
- Reference it actively

**Follow methodologies:**

- TDD prevents untested code
- SDD ensures comprehensive specifications
- DDD maintains clean architecture


### Project-Specific Adaptation

**Small projects:**

- Focus on reflexion and code-review plugins
- Skip full SDD workflow for simple features
- Use git plugin for clean commits

**Large projects:**

- Full SDD workflow for complex features
- Multiple specialized agents in parallel
- Comprehensive CLAUDE.md maintenance

**Team projects:**

- Document everything in CLAUDE.md
- Use SDD for shared understanding
- Review all PRs with code-review agents

**Solo projects:**

- Balance quality and velocity
- Use commands judiciously
- Focus on learning and improvement

### Getting Help

Each command has a description of how it should be used and what it does.

**Command help:**

```bash
/help
```

Shows all available commands with descriptions.

### Best Practices for CLAUDE.md

**Keep it curated:**

- Remove outdated information
- Consolidate duplicate insights
- Organize by topic for easy reference

**Use it actively:**

- Reference it when starting new features
- Update it after completing major work
- Review it during code reviews

**Make it actionable:**

- Write specific guidance, not generic advice
- Include examples and anti-patterns
- Link to relevant documentation

**Version control:**

- Commit `CLAUDE.md` with code changes
- Track evolution of project knowledge
- Review changes during pull requests

**Balance detail and brevity:**

- Detailed enough to be useful
- Concise enough to remain readable
- Focus on project-specific insights

### Using CLAUDE.md Effectively

**Start of session:**

```text
Read CLAUDE.md and follow its guidelines
```

**After major feature:**

```bash
# Reflect on implementation
/reflexion:reflect

# Memorize key insights to CLAUDE.md
/reflexion:memorize
```

**When setting up new project:**

```bash
# Establish constitution
/sdd:00-setup Use FastAPI, PostgreSQL, follow Clean Architecture

# Add language best practices
/add-typescript-best-practices

# Setup code quality standards
/setup-code-formating
```

**Regular maintenance:**

- Review and consolidate monthly
- Remove obsolete guidance
- Update based on team retrospectives
- Refine based on recurring issues

---

### Hook

A script or command that executes automatically at specific points in a workflow, typically Git hooks (pre-commit, pre-push, etc.).

**CEK usage**: The customaize-agent plugin includes `/customaize-agent:create-hook` for setting up automated testing and quality checks.

**Related**: [Customaize Agent Plugin](../plugins/customaize-agent/)
