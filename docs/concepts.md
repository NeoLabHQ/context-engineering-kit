# Concepts

Reference of terms and concepts used throughout Context Engineering Kit documentation.

## What is Context Engineering?

Context engineering is the discipline of managing the language model's context window. Unlike prompt engineering, which focuses on crafting effective instructions, context engineering addresses the holistic curation of all information that enters the model's limited attention budget: system prompts, tool definitions, retrieved documents, message history, and tool outputs.

The fundamental challenge is that context windows are constrained not by raw token capacity but by attention mechanics. As context length increases, models exhibit predictable degradation patterns: the "lost-in-the-middle" phenomenon, U-shaped attention curves, and attention scarcity. Effective context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of desired outcomes.


## Commands

Commands are explicit actions you invoke manually to perform specific tasks. They follow the pattern `/plugin-name:command-name`. They include a prompt that will be loaded to the LLM and trigger it to perform a specific task.

Commands are:

- **User-invoked** - You explicitly call them when needed
- **Task-specific** - Designed for particular operations
- **Token-efficient** - Don't consume context when not in use

### Discovering Commands

After installing a plugin, its commands become available. View all commands:

```bash
/help
```

Commands are namespaced by plugin, making their origin clear:

- `/reflexion:reflect` - From the reflexion plugin
- `/git:commit` - From the git plugin
- `/sdd:01-specify` - From the sdd plugin

### Command Syntax

```bash
/plugin-name:command-name [optional-argument]
```

**Examples:**

```bash
# No argument required
/reflexion:reflect
/git:commit

# With argument
/sdd:01-specify Add user authentication with OAuth
/analyse Target the checkout flow for optimization
```

---

## Using Skills

Skills are automatically applied knowledge that influences Claude's behavior without explicit invocation. When a skill is loaded, Claude considers it continuously during your session.

### How Skills Work

Skills are markdown documents loaded into Claude's context that provide:

- **Best practices** - Industry-standard approaches and patterns
- **Methodologies** - Systematic processes (e.g., TDD, DDD)
- **Anti-patterns** - Common mistakes to avoid
- **Gate functions** - Checks before taking certain actions

**Key difference from commands:**

- **Commands** - You invoke manually with `/command-name`
- **Skills** - Claude applies automatically when relevant, but you can explicitly ask Claude to load a specific skill, for example: "load TDD skill, before implementing feature"

### Skills vs Commands Trade-off

**Why prefer commands over skills:**

The Context Engineering Kit architecture prefers commands over skills to minimize token usage:

- **Skills description** always populate context (every session)
- **Commands** only load when invoked (zero tokens until used)

---

## Agents

Agents are specialized sub-agents designed for focused tasks. Unlike Claude's general-purpose capabilities, agents have specific expertise and domain knowledge.

### What Are Agents?

Agents are fresh Claude instances launched with specialized prompts for specific tasks. They:

- **Focus on one domain** - e.g., code review, architecture design, business analysis
- **Have specialized knowledge** - Expertise in their specific area
- **Work independently** - Operate as sub-agents with their own context
- **Return specific outputs** - Structured results aligned with their purpose

### Agent Architecture

```
Main Claude Session (You)
├── Launches specialized agent for task
│   ├── Agent has specific prompt and knowledge
│   ├── Agent performs focused work
│   └── Agent returns structured result
└── Integrates agent results into workflow
```

**Key benefits:**

- **Fresh context** - Each agent starts with clean context specific to its task
- **Specialized expertise** - Domain-specific knowledge and techniques
- **Parallel execution** - Multiple agents can work simultaneously
- **Quality gates** - Agents perform validation and review

### How Agents Are Invoked

**Automatic invocation** - Commands launch agents as part of their workflow:

```bash
# Launches multiple code review agents
/review-local-changes

# Launches business-analyst agent
/sdd:01-specify Add user authentication

# Launches researcher, code-explorer, and software-architect agents
/sdd:02-plan
```

**Manual invocation** - Request specific agents directly:

```text
Launch business analyst agent to analyze payment feature requirements
Launch code explorer agent to trace authentication flow
Launch software architect Opus agent to design caching strategy
```

---

## Workflow Commands

Workflow commands orchestrate multi-step processes using sub-agents, automating complex reasoning cycles that would otherwise require manual invocation of multiple commands.

### What Are Workflow Commands?

Workflow commands combine multiple sub-tasks into a single invocation:

- **Orchestrate sub-agents** - Launch specialized agents for each step
- **Handle transitions** - Manage state between phases automatically
- **Preserve audit trails** - Document intermediate results
- **Support iteration** - Allow user intervention at key decision points

### Example: FPF Propose-Hypotheses Workflow

The FPF plugin's `/propose-hypotheses` command demonstrates this pattern:

```
/propose-hypotheses How should we implement caching?
       │
       ├── Step 1: Initialize Context (FPF Agent)
       │   └── Creates .fpf/context.md
       │
       ├── Step 2: Generate Hypotheses (FPF Agent)
       │   └── Creates L0 hypothesis files
       │
       ├── Step 3: Present Summary (Main Agent)
       │   └── User can add own hypotheses
       │
       ├── Step 4: Verify Logic (Parallel FPF Agents)
       │   └── Promotes valid hypotheses L0 -> L1
       │
       ├── Step 5: Validate Evidence (Parallel FPF Agents)
       │   └── Promotes corroborated hypotheses L1 -> L2
       │
       ├── Step 6: Audit Trust (Parallel FPF Agents)
       │   └── Computes R_eff scores
       │
       └── Step 7: Make Decision (FPF Agent)
           └── Creates Design Rationale Record
```

### Benefits of Workflow Commands

| Benefit | Description |
|---------|-------------|
| **Reduced cognitive load** | User doesn't need to remember command sequence |
| **Consistent execution** | Same process every time, reducing errors |
| **Parallel processing** | Multiple agents work simultaneously where possible |
| **Auditable results** | Intermediate artifacts preserved for review |
| **User control** | Decision points allow course correction |

### When to Use Workflow vs Individual Commands

| Use Case | Approach |
|----------|----------|
| Complete end-to-end process | Workflow command |
| Check current state | Utility command (`/status`) |
| Manage specific aspect | Utility command (`/decay`) |
| Iterate on single phase | Individual task prompts |

---

## First-Principles Reasoning (FPF)

The First Principles Framework (FPF) provides structured reasoning for complex decisions. Rather than jumping to solutions, FPF enforces systematic hypothesis generation, logical verification, and evidence-based validation.

### ADI Cycle

FPF follows the Abduction-Deduction-Induction reasoning cycle:

| Phase | Action | Output |
|-------|--------|--------|
| **Abduction** | Generate candidate explanations | L0 hypotheses (conjectures) |
| **Deduction** | Verify logical consistency | L1 hypotheses (substantiated) |
| **Induction** | Validate against evidence | L2 hypotheses (corroborated) |

This cycle ensures that hypotheses progress through increasing levels of confidence before informing decisions.

### Knowledge Layers (L0/L1/L2)

FPF tracks epistemic status through knowledge layers:

| Layer | Status | Meaning |
|-------|--------|---------|
| **L0** | Conjecture | Hypothesis generated but unverified |
| **L1** | Substantiated | Passed logical consistency checks |
| **L2** | Corroborated | Validated by empirical evidence |
| **Invalid** | Falsified | Failed verification or validation |

Hypotheses progress through layers as they accumulate verification:
- L0 -> L1: Logical deduction passes
- L1 -> L2: Evidence gathering confirms
- Any layer -> Invalid: Verification or validation fails

### Trust Calculus and R_eff

FPF computes effective reliability (R_eff) using the **Weakest Link principle**:

```
R_eff = min(evidence_scores)
```

This means a hypothesis is only as reliable as its weakest supporting evidence. Key factors:

| Factor | Description |
|--------|-------------|
| **Evidence Score** | Reliability rating of each evidence source |
| **Congruence Level** | How closely evidence context matches current context (CL3=same, CL1=different) |
| **Evidence Freshness** | Age of evidence affects reliability (decay over time) |

The trust calculus ensures decisions are based on computed reliability, not estimated confidence.

### Transformer Mandate

A core FPF principle: **A system cannot transform itself.**

- AI generates options with computed evidence scores
- Human makes the final decision
- Autonomous architectural choices are a protocol violation

This separation ensures accountability and prevents unsupervised AI decisions on consequential matters.

---

## Working with CLAUDE.md

The `CLAUDE.md` file is your project's living memory - a central repository of project-specific knowledge, patterns, and insights that persists across sessions.

### What is CLAUDE.md?

`CLAUDE.md` is a markdown file in your project root that contains:

- **Project constitution** - Core principles and standards
- **Architecture decisions** - Key design choices and rationale
- **Best practices** - Project-specific patterns and conventions
- **Lessons learned** - Insights from reflections and critiques
- **Common pitfalls** - Known issues and how to avoid them
- **Tech stack guidance** - Framework and library usage patterns

**Why it matters:**

- **Persistent memory** - Knowledge survives between sessions
- **Consistency** - Ensures Claude follows project patterns
- **Quality improvement** - Accumulates insights over time
- **Team alignment** - Documents shared understanding

### How Plugins Update CLAUDE.md

Several plugins read from and write to `CLAUDE.md`:

**Reflexion plugin** - Memorizes insights:

```bash
# After reflecting, save insights to CLAUDE.md
/reflexion:memorize
```

**What it adds:**

- Key insights from reflection sessions
- Patterns discovered during implementation
- Lessons learned from critiques
- Common mistakes to avoid
- Successful approaches to replicate

**Tech Stack plugin** - Adds language/framework practices:

```bash
/add-typescript-best-practices
```

**What it adds:**

- Language-specific best practices
- Framework usage patterns
- Code style guidelines
- Common anti-patterns for the tech stack

**DDD plugin** - Sets up code quality standards:

```bash
/setup-code-formating
```

**What it adds:**

- Code formatting rules
- Architecture principles
- SOLID principle applications
- Clean Architecture patterns

**MCP plugin** - Documents MCP server requirements:

```bash
/mcp:setup-context7-mcp
```

**What it adds:**

- MCP server integration requirements
- When and how to use specific MCP servers
- Configuration and usage patterns

**SDD plugin** - Establishes project constitution:

```bash
/sdd:00-setup Use NestJS, follow SOLID and Clean Architecture
```

**What it adds:**

- Project constitution and governance
- Core architectural principles
- Technology stack decisions
- Development standards
