# /apply-anthropic-skill-best-practices - Skill Optimization

Comprehensive guide for skill development based on Anthropic's official best practices. Use for complex skills requiring detailed structure and optimization.

- Purpose - Apply official guidelines to skill authoring
- Output - Optimized skill with improved discoverability

```bash
/apply-anthropic-skill-best-practices ["skill path"]
```

## Arguments

Optional skill name or path to skill being reviewed.

## Usage Examples

```bash
# Optimize an existing skill
> /apply-anthropic-skill-best-practices pdf-processing

# Review a skill by path
> /apply-anthropic-skill-best-practices ~/.claude/skills/bigquery/

# Start optimization workflow
> /apply-anthropic-skill-best-practices
```

## How It Works

1. **Structure Review**: Checks skill organization
   - YAML frontmatter (name: 64 chars max, description: 1024 chars max)
   - SKILL.md body under 500 lines
   - Progressive disclosure with separate files
   - One-level-deep references

2. **Description Optimization**: Improves discoverability
   - Third-person writing (injected into system prompt)
   - "Use when..." trigger conditions
   - Specific keywords and terms
   - Both what it does AND when to use it

3. **Content Guidelines**: Applies best practices
   - Avoid time-sensitive information
   - Consistent terminology throughout
   - Concrete examples over abstract descriptions
   - Template patterns and examples patterns

4. **Workflow Enhancement**: Adds feedback loops
   - Clear sequential steps with checklists
   - Validation steps for critical operations
   - Conditional workflow patterns

5. **Token Efficiency**: Optimizes for context window
   - Remove redundant explanations
   - Challenge each paragraph's token cost
   - Use progressive disclosure appropriately

## Key Principles

| Principle | Description |
|-----------|-------------|
| **Progressive Disclosure** | Metadata always loaded, SKILL.md on trigger, resources as needed |
| **CSO (Claude Search Optimization)** | Rich descriptions with triggers, keywords, and symptoms |
| **Degrees of Freedom** | Match specificity to task fragility |
| **Conciseness** | Only add context Claude doesn't already have |

## Best Practices

- Test with all models - What works for Opus may need more detail for Haiku
- Iterate with Claude - Use Claude A to design, Claude B to test
- Observe navigation - Watch how Claude actually uses the skill
- Build evaluations first - Create test scenarios BEFORE extensive documentation
- Gather team feedback - Address blind spots from different usage patterns
