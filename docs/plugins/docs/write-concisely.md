# /write-concisely - Clear and Concise Writing

Apply William Strunk Jr.'s *The Elements of Style* principles to documentation. Makes writing clearer, stronger, and more professional.

- Purpose - Cut ruthlessly, write directly, eliminate weak constructions
- Output - Documentation with improved clarity and reduced word count

```bash
/write-concisely ["text or file to improve"]
```

## Arguments

Optional target specification:

- **File path** (e.g., `docs/README.md`) - Apply writing rules to specific document
- **Inline text** - Direct text to improve
- **No argument** - Review recent documentation changes

## Core Principles

The skill enforces six essential writing rules:

| Rule | Principle | Bad → Good |
|------|-----------|------------|
| **Active voice** | Subject performs action | "was completed by team" → "team completed" |
| **Positive form** | State what is, not what isn't | "not many" → "few" |
| **Concrete language** | Specific over abstract | "period of unfavorable weather" → "it rained every day" |
| **Omit needless words** | Every word must earn its place | "the fact that" → delete |
| **Related words together** | Modifiers next to what they modify | "He only found two" → "He found only two" |
| **Emphatic endings** | Important words at sentence end | "...though it has advanced in many other ways" → "...but it has hardly advanced in fortitude" |

## Common Fixes Applied

**Wordy Expressions:**

| Original | Revision |
|----------|----------|
| the question as to whether | whether |
| owing to the fact that | because |
| in a hasty manner | hastily |
| he is a man who | he |
| this is a subject which | this subject |

**Weak Constructions:**

| Original | Revision |
|----------|----------|
| There were dead leaves on the ground | Dead leaves covered the ground |
| He was not very often on time | He usually came late |
| did not remember | forgot |
| not important | trifling |

**Passive to Active:**

| Original | Revision |
|----------|----------|
| A survey was made in 1900 | We surveyed in 1900 |
| The army was rapidly mobilized | Command mobilized the army rapidly |

## Usage Examples

```bash
# Improve a specific document
> /write-concisely docs/getting-started.md

# Apply to inline text
> /write-concisely "There is no doubt but that the system is working"
# Result: "The system works"

# Review recent documentation changes
> /write-concisely
```

## Quality Metrics

**Word Count Reduction:**

- Target 20-40% reduction without losing meaning
- Every sentence should justify its length

**Clarity Improvements:**

- Active voice percentage increases
- Abstract nouns decrease
- Sentence length becomes more varied

**Signs of Good Writing:**

- Reader understands on first pass
- No re-reading required for clarity
- Specific details replace vague generalities
