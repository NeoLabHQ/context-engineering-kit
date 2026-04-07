# Related Projects

Context Engineering Kit builds upon and integrates the best ideas from multiple open-source projects and community initiatives. This page documents the projects that inspired CEK and provides context for where specific techniques and patterns originated.
Rather than starting from scratch, CEK curates and enhances proven plugins, patterns, and techniques from across the Claude Code ecosystem.

## Source Projects

CEK builds upon and integrates ideas from these open-source projects:

- **[anthropics/claude-code](https://github.com/anthropics/claude-code/tree/main/plugins)** - Official plugin examples and templates from Anthropic, providing baseline plugin architecture and patterns
- **[eyaltoledano/claude-task-master](https://github.com/eyaltoledano/claude-task-master)** - Task management system with structured workflows and progress tracking
- **[wshobson/agents](https://github.com/wshobson/agents)** - Multi-agent orchestration framework for coordinating specialized agents
- **[anthropics/skills](https://github.com/anthropics/skills)** - Official collection of example skills demonstrating Claude's capabilities
- **[ruvnet/claude-flow](https://github.com/ruvnet/claude-flow)** - Workflow orchestration system with visual design and state management
- **[obra/superpowers](https://github.com/obra/superpowers)** - Collection of productivity-enhancing plugins and commands
- **[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)** - Curated list of community Claude skills and resources
- **[steveyegge/beads](https://github.com/steveyegge/beads)** - Modular system for composing AI capabilities into workflows
- **[obra/the-elements-of-style](https://github.com/obra/the-elements-of-style)** - William Strunk Jr.'s *The Elements of Style* (1918) in markdown format for AI agents.

---

## Context Engineering & Agent Evaluation

CEK's context engineering and agent evaluation skills integrate research from:

- **[muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)** - Comprehensive skills for context engineering fundamentals, multi-agent architectures, and agent evaluation frameworks. Source for `context-engineering`, `agent-evaluation`, and `multi-agent-patterns` skills.

---

## First Principles Framework

CEK's FPF plugin implements structured reasoning methodology from:

- **[m0n0x41d/quint-code](https://github.com/m0n0x41d/quint-code)** - CLI tool implementing the First Principles Framework (FPF) for AI-assisted development with structured reasoning, hypothesis generation, and auditable decisions. Source for the `fpf` plugin's ADI cycle workflow and utility commands.
- **[ailev/FPF](https://github.com/ailev/FPF)** - Original First Principles Framework methodology by Anatoly Levenchuk, providing the theoretical foundation for structured reasoning and trust calculus.

The FPF plugin adapts the quint-code approach into a workflow-based architecture:

- **Workflow command** (`/propose-hypotheses`) - Orchestrates the complete ADI cycle using sub-agents
- **Utility commands** (`/status`, `/query`, `/decay`, `/actualize`, `/reset`) - Manage knowledge base state and maintenance

---

## Spec-Driven Development Projects

CEK's Spec-Driven Development (SDD) plugin integrates best practices from these established frameworks:

- **[github/spec-kit](https://github.com/github/spec-kit)** - GitHub's internal Spec-Driven Development methodology and tools
- **[Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)** - Open-source specification framework for AI-assisted development with detailed templates
- **[bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)** - Behavioral Model-Assisted Development methodology focusing on behavior-driven specifications

---

## How CEK Integrates These Projects

Context Engineering Kit collects these techniques and splits them into separate plugins, with additional features and improvements.

### Token Optimization

Every prompt is optimized to:

- Minimize context pollution
- Load only when needed
- Use commands over always-on skills
- Share common patterns efficiently

### Quality Gates

Enhanced with systematic review:

- Multi-agent code review
- Reflexion loops
- Verification steps
- Continuous improvement

### Modular Architecture

Organized for maximum flexibility:

- Install only needed plugins
- No overlap or redundancy
- Clear dependencies
- Independent operation

## Using These Projects with CEK

### Complementary Use

These projects can work alongside CEK:

- **Use official plugins** for features not in CEK
- **Use Task Master** if you need more detailed task tracking
- **Use Claude Flow** for visual workflow design
- **Use OpenSpec** for more detailed specification templates
