# /create-skill - Skill Development Guide

Guide for creating effective skills using a TDD-based approach. This command treats skill creation as Test-Driven Development applied to process documentation.

- Purpose - Create reusable skills that extend Claude's capabilities
- Output - Complete skill directory with SKILL.md and optional resources

```bash
/create-skill ["skill name"]
```

## Arguments

Optional skill name (e.g., "image-editor", "pdf-processing", "code-review").

## Usage Examples

```bash
# Create an image editing skill
> /create-skill image-editor

# Create a database query skill
> /create-skill bigquery-analysis

# Start the skill creation workflow
> /create-skill
```

## How It Works

1. **Understanding with Concrete Examples**: Gathers usage scenarios
   - What functionality should the skill support?
   - How would users invoke this skill?
   - What triggers should activate it?

2. **Planning Reusable Contents**: Analyzes examples to identify resources
   - Scripts (`scripts/`) - Executable code for deterministic tasks
   - References (`references/`) - Documentation to load as needed
   - Assets (`assets/`) - Templates, images, files used in output

3. **Skill Initialization**: Creates proper structure
   - SKILL.md with YAML frontmatter (name, description)
   - Resource directories as needed
   - Proper naming conventions (gerund form: "Processing PDFs")

4. **Content Development**: Writes skill documentation
   - Overview with core principle
   - When to Use section with triggers and symptoms
   - Quick Reference for scanning
   - Implementation details
   - Common Mistakes section

5. **TDD Testing Cycle**: Applies RED-GREEN-REFACTOR
   - RED: Run scenarios WITHOUT skill, document failures
   - GREEN: Write skill addressing those failures
   - REFACTOR: Close loopholes, iterate until bulletproof

## Best Practices

- Start with concrete examples - Understand real use cases before writing
- Apply TDD strictly - No skill without failing tests first
- Keep SKILL.md lean - Under 500 lines, use separate files for heavy reference
- Optimize for discovery - Start descriptions with "Use when..." and include specific triggers
- Name by action - Use gerunds like "Processing PDFs" not "PDF Processor"
