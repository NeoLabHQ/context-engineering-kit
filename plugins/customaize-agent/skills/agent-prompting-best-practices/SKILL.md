---
name: agent-prompting-best-practices
description: Use this skill when you writing commands, hooks, skills for Claude Code, or prompts for sub agents or any other LLM interaction. 
---

# Agent Prompting Best Practices

Based on Anthropic's official best practices for agent prompting.

## Core principles

### Context Window

The “context window” refers to the entirety of the amount of text a language model can look back on and reference when generating new text plus the new text it generates. This is different from the large corpus of data the language model was trained on, and instead represents a “working memory” for the model. A larger context window allows the model to understand and respond to more complex and lengthy prompts, while a smaller context window may limit the model’s ability to handle longer prompts or maintain coherence over extended conversations.

- Progressive token accumulation: As the conversation advances through turns, each user message and assistant response accumulates within the context window. Previous turns are preserved completely.
- Linear growth pattern: The context usage grows linearly with each turn, with previous turns preserved completely.
- 200K token capacity: The total available context window (200,000 tokens) represents the maximum capacity for storing conversation history and generating new output from Claude.
- Input-output flow: Each turn consists of:
  - Input phase: Contains all previous conversation history plus the current user message
  - Output phase: Generates a text response that becomes part of a future input

### Concise is key

The context window is a public good. Your prompt, command, skill shares the context window with everything else Claude needs to know, including:

- The system prompt
- Conversation history
- Other commands, skills, hooks, metadata
- Your actual request

**Default assumption**: Claude is already very smart

Only add context Claude doesn't already have. Challenge each piece of information:

- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

**Good example: Concise** (approximately 50 tokens):

````markdown  theme={null}
## Extract PDF text

Use pdfplumber for text extraction:

```python
import pdfplumber

with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
````

**Bad example: Too verbose** (approximately 150 tokens):

```markdown  theme={null}
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but we
recommend pdfplumber because it's easy to use and handles most cases well.
First, you'll need to install it using pip. Then you can use the code below...
```

The concise version assumes Claude knows what PDFs are and how libraries work.

### Set appropriate degrees of freedom

Match the level of specificity to the task's fragility and variability.

**High freedom** (text-based instructions):

Use when:

- Multiple approaches are valid
- Decisions depend on context
- Heuristics guide the approach

Example:

```markdown  theme={null}
## Code review process

1. Analyze the code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability and maintainability
4. Verify adherence to project conventions
```

**Medium freedom** (pseudocode or scripts with parameters):

Use when:

- A preferred pattern exists
- Some variation is acceptable
- Configuration affects behavior

Example:

````markdown  theme={null}
## Generate report

Use this template and customize as needed:

```python
def generate_report(data, format="markdown", include_charts=True):
    # Process data
    # Generate output in specified format
    # Optionally include visualizations
```
````

**Low freedom** (specific scripts, few or no parameters):

Use when:

- Operations are fragile and error-prone
- Consistency is critical
- A specific sequence must be followed

Example:

````markdown  theme={null}
## Database migration

Run exactly this script:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
````

**Analogy**: Think of Claude as a robot exploring a path:

- **Narrow bridge with cliffs on both sides**: There's only one safe way forward. Provide specific guardrails and exact instructions (low freedom). Example: database migrations that must run in exact sequence.
- **Open field with no hazards**: Many paths lead to success. Give general direction and trust Claude to find the best route (high freedom). Example: code reviews where context determines the best approach.

# Persuasion Principles for Agent Communication

Usefull for writing prompts, including but not limited to: commands, hooks, skills for Claude Code, or prompts for sub agents or any other LLM interaction.

## Overview

LLMs respond to the same persuasion principles as humans. Understanding this psychology helps you design more effective skills - not to manipulate, but to ensure critical practices are followed even under pressure.

**Research foundation:** Meincke et al. (2025) tested 7 persuasion principles with N=28,000 AI conversations. Persuasion techniques more than doubled compliance rates (33% → 72%, p < .001).

## The Seven Principles

### 1. Authority

**What it is:** Deference to expertise, credentials, or official sources.

**How it works in prompts:**

- Imperative language: "YOU MUST", "Never", "Always"
- Non-negotiable framing: "No exceptions"
- Eliminates decision fatigue and rationalization

**When to use:**

- Discipline-enforcing skills (TDD, verification requirements)
- Safety-critical practices
- Established best practices

**Example:**

```markdown
✅ Write code before test? Delete it. Start over. No exceptions.
❌ Consider writing tests first when feasible.
```

### 2. Commitment

**What it is:** Consistency with prior actions, statements, or public declarations.

**How it works in prompts:**

- Require announcements: "Announce skill usage"
- Force explicit choices: "Choose A, B, or C"
- Use tracking: TodoWrite for checklists

**When to use:**

- Ensuring skills are actually followed
- Multi-step processes
- Accountability mechanisms

**Example:**

```markdown
✅ When you find a skill, you MUST announce: "I'm using [Skill Name]"
❌ Consider letting your partner know which skill you're using.
```

### 3. Scarcity

**What it is:** Urgency from time limits or limited availability.

**How it works in prompts:**

- Time-bound requirements: "Before proceeding"
- Sequential dependencies: "Immediately after X"
- Prevents procrastination

**When to use:**

- Immediate verification requirements
- Time-sensitive workflows
- Preventing "I'll do it later"

**Example:**

```markdown
✅ After completing a task, IMMEDIATELY request code review before proceeding.
❌ You can review code when convenient.
```

### 4. Social Proof

**What it is:** Conformity to what others do or what's considered normal.

**How it works in prompts:**

- Universal patterns: "Every time", "Always"
- Failure modes: "X without Y = failure"
- Establishes norms

**When to use:**

- Documenting universal practices
- Warning about common failures
- Reinforcing standards

**Example:**

```markdown
✅ Checklists without TodoWrite tracking = steps get skipped. Every time.
❌ Some people find TodoWrite helpful for checklists.
```

### 5. Unity

**What it is:** Shared identity, "we-ness", in-group belonging.

**How it works in prompts:**

- Collaborative language: "our codebase", "we're colleagues"
- Shared goals: "we both want quality"

**When to use:**

- Collaborative workflows
- Establishing team culture
- Non-hierarchical practices

**Example:**

```markdown
✅ We're colleagues working together. I need your honest technical judgment.
❌ You should probably tell me if I'm wrong.
```

### 6. Reciprocity

**What it is:** Obligation to return benefits received.

**How it works:**

- Use sparingly - can feel manipulative
- Rarely needed in prompts

**When to avoid:**

- Almost always (other principles more effective)

### 7. Liking

**What it is:** Preference for cooperating with those we like.

**How it works:**

- **DON'T USE for compliance**
- Conflicts with honest feedback culture
- Creates sycophancy

**When to avoid:**

- Always for discipline enforcement

## Principle Combinations by Prompt Type

| Prompt Type | Use | Avoid |
|------------|-----|-------|
| Discipline-enforcing | Authority + Commitment + Social Proof | Liking, Reciprocity |
| Guidance/technique | Moderate Authority + Unity | Heavy authority |
| Collaborative | Unity + Commitment | Authority, Liking |
| Reference | Clarity only | All persuasion |

## Why This Works: The Psychology

**Bright-line rules reduce rationalization:**

- "YOU MUST" removes decision fatigue
- Absolute language eliminates "is this an exception?" questions
- Explicit anti-rationalization counters close specific loopholes

**Implementation intentions create automatic behavior:**

- Clear triggers + required actions = automatic execution
- "When X, do Y" more effective than "generally do Y"
- Reduces cognitive load on compliance

**LLMs are parahuman:**

- Trained on human text containing these patterns
- Authority language precedes compliance in training data
- Commitment sequences (statement → action) frequently modeled
- Social proof patterns (everyone does X) establish norms

## Ethical Use

**Legitimate:**

- Ensuring critical practices are followed
- Creating effective documentation
- Preventing predictable failures

**Illegitimate:**

- Manipulating for personal gain
- Creating false urgency
- Guilt-based compliance

**The test:** Would this technique serve the user's genuine interests if they fully understood it?

## Quick Reference

When designing a prompt, ask:

1. **What type is it?** (Discipline vs. guidance vs. reference)
2. **What behavior am I trying to change?**
3. **Which principle(s) apply?** (Usually authority + commitment for discipline)
4. **Am I combining too many?** (Don't use all seven)
5. **Is this ethical?** (Serves user's genuine interests?)
