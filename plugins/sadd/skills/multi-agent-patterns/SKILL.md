---
description: Design multi-agent architectures for complex tasks. Use when single-agent context limits are exceeded, when tasks decompose naturally into subtasks, or when specializing agents improves quality.
---

# Multi-Agent Architecture Patterns for Claude Code

Multi-agent architectures distribute work across multiple agent invocations, each with its own focused context. When designed well, this distribution enables capabilities beyond single-agent limits. When designed poorly, it introduces coordination overhead that negates benefits. The critical insight is that sub-agents exist primarily to isolate context, not to anthropomorphize role division.

## Core Concepts

Multi-agent systems address single-agent context limitations through distribution. Three dominant patterns exist: supervisor/orchestrator for centralized control, peer-to-peer/swarm for flexible handoffs, and hierarchical for layered abstraction. The critical design principle is context isolation—sub-agents exist primarily to partition context rather than to simulate organizational roles.

Effective multi-agent systems require explicit coordination protocols, consensus mechanisms that avoid sycophancy, and careful attention to failure modes including bottlenecks, divergence, and error propagation.

## Why Multi-Agent Architectures

### The Context Bottleneck

Single agents face inherent ceilings in reasoning capability, context management, and tool coordination. As tasks grow more complex, context windows fill with accumulated history, retrieved documents, and tool outputs. Performance degrades according to predictable patterns: the lost-in-middle effect, attention scarcity, and context poisoning.

Multi-agent architectures address these limitations by partitioning work across multiple context windows. Each agent operates in a clean context focused on its subtask. Results aggregate at a coordination layer without any single context bearing the full burden.

### The Parallelization Argument

Many tasks contain parallelizable subtasks that a single agent must execute sequentially. A research task might require searching multiple independent sources, analyzing different documents, or comparing competing approaches. A single agent processes these sequentially, accumulating context with each step.

Multi-agent architectures assign each subtask to a dedicated agent with a fresh context. All agents work simultaneously, then return results to a coordinator. The total real-world time approaches the duration of the longest subtask rather than the sum of all subtasks.

### The Specialization Argument

Different tasks benefit from different agent configurations: different system prompts, different tool sets, different context structures. A general-purpose agent must carry all possible configurations in context. Specialized agents carry only what they need.

Multi-agent architectures enable specialization without combinatorial explosion. The coordinator routes to specialized agents; each agent operates with lean context optimized for its domain.

## Architectural Patterns

### Pattern 1: Supervisor/Orchestrator

The supervisor pattern places a central agent in control, delegating to specialists and synthesizing results. The supervisor maintains global state and trajectory, decomposes user objectives into subtasks, and routes to appropriate workers.

```
User Request -> Supervisor -> [Specialist A, Specialist B, Specialist C] -> Aggregation -> Final Output
```

**When to use:** Complex tasks with clear decomposition, tasks requiring coordination across domains, tasks where human oversight is important.

**Advantages:** Strict control over workflow, easier to implement human-in-the-loop interventions, ensures adherence to predefined plans.

**Disadvantages:** Supervisor context becomes bottleneck, supervisor failures cascade to all workers, "telephone game" problem where supervisors paraphrase sub-agent responses incorrectly.

**Claude Code Implementation:** Create a main command that orchestrates by calling specialized subagents using the Task tool. The supervisor command contains the coordination logic and calls subagents for specialized work.

```markdown
<!-- Example supervisor command structure -->
1. Analyze the user request and decompose into subtasks
2. For each subtask, dispatch to appropriate specialist:
   - Use Task tool to spawn subagent with focused context
   - Pass only relevant context to each subagent
3. Collect and synthesize results from all subagents
4. Return unified response to user
```

**The Telephone Game Problem:** Supervisor architectures can perform worse when supervisors paraphrase sub-agent responses incorrectly, losing fidelity. The fix: allow sub-agents to pass responses directly when synthesis would lose important details. In Claude Code, this means letting subagents write directly to shared files or return their output verbatim rather than having the supervisor rewrite everything.

### Pattern 2: Peer-to-Peer/Swarm

The peer-to-peer pattern removes central control, allowing agents to communicate directly based on predefined protocols. Any agent can transfer control to any other through explicit handoff mechanisms.

**When to use:** Tasks requiring flexible exploration, tasks where rigid planning is counterproductive, tasks with emergent requirements that defy upfront decomposition.

**Advantages:** No single point of failure, scales effectively for breadth-first exploration, enables emergent problem-solving behaviors.

**Disadvantages:** Coordination complexity increases with agent count, risk of divergence without central state keeper, requires robust convergence constraints.

**Claude Code Implementation:** Create commands that can invoke other commands based on discovered needs. Use shared files (like task lists or state files) as the coordination mechanism.

```markdown
<!-- Example peer handoff structure -->
1. Analyze current state from shared context file
2. Determine if this agent can complete the task
3. If specialized help needed:
   - Write current findings to shared state
   - Invoke appropriate peer command/skill
4. Continue until task complete or hand off
```

### Pattern 3: Hierarchical

Hierarchical structures organize agents into layers of abstraction: strategic, planning, and execution layers. Strategy layer agents define goals and constraints; planning layer agents break goals into actionable plans; execution layer agents perform atomic tasks.

```
Strategy Layer (Goal Definition) -> Planning Layer (Task Decomposition) -> Execution Layer (Atomic Tasks)
```

**When to use:** Large-scale projects with clear hierarchical structure, enterprise workflows with management layers, tasks requiring both high-level planning and detailed execution.

**Advantages:** Mirrors organizational structures, clear separation of concerns, enables different context structures at different levels.

**Disadvantages:** Coordination overhead between layers, potential for misalignment between strategy and execution, complex error propagation.

**Claude Code Implementation:** Structure your plugin with commands at different abstraction levels. High-level commands focus on strategy and call mid-level planning commands, which in turn call atomic execution commands.

## Context Isolation as Design Principle

The primary purpose of multi-agent architectures is context isolation. Each sub-agent operates in a clean context window focused on its subtask without carrying accumulated context from other subtasks.

### Isolation Mechanisms

**Instruction passing:** For simple, well-defined subtasks, the coordinator creates focused instructions. The sub-agent receives only the instructions needed for its specific task. In Claude Code, this means passing minimal, targeted prompts to subagents via the Task tool.

**File system memory:** For complex tasks requiring shared state, agents read and write to persistent storage. The file system serves as the coordination mechanism, avoiding context bloat from shared state passing. This is the most natural pattern for Claude Code—agents communicate through markdown files, JSON state files, or structured documents.

**Full context delegation:** For complex tasks where the sub-agent needs complete understanding, the coordinator shares its entire context. The sub-agent has its own tools and instructions but receives full context for its decisions. Use sparingly as it defeats the purpose of context isolation.

### Isolation Trade-offs

Full context delegation provides maximum capability but defeats the purpose of sub-agents. Instruction passing maintains isolation but limits sub-agent flexibility. File system memory enables shared state without context passing but introduces consistency challenges.

The right choice depends on task complexity, coordination needs, and the nature of the work.

## Consensus and Coordination

### The Voting Problem

Simple majority voting treats hallucinations from weak reasoning as equal to sound reasoning. Without intervention, multi-agent discussions can devolve into consensus on false premises due to inherent bias toward agreement.

### Weighted Contributions

Weight agent contributions by confidence or expertise. Agents with higher confidence or domain expertise carry more weight in final decisions.

### Debate Protocols

Debate protocols require agents to critique each other's outputs over multiple rounds. Adversarial critique often yields higher accuracy on complex reasoning than collaborative consensus.

**Claude Code Implementation:** Create a review stage where one agent critiques another's output. Structure this as separate commands: one for initial work, one for critique, and optionally one for revision based on critique.

### Trigger-Based Intervention

Monitor multi-agent interactions for specific behavioral markers:
- **Stall triggers:** Activate when discussions make no progress
- **Sycophancy triggers:** Detect when agents mimic each other's answers without unique reasoning
- **Divergence triggers:** Detect when agents are moving away from the original objective

## Failure Modes and Mitigations

### Failure: Supervisor Bottleneck

The supervisor accumulates context from all workers, becoming susceptible to saturation and degradation.

**Mitigation:** Implement output constraints so workers return only distilled summaries. Use file-based checkpointing to persist state without carrying full history in context.

### Failure: Coordination Overhead

Agent communication consumes tokens and introduces latency. Complex coordination can negate parallelization benefits.

**Mitigation:** Minimize communication through clear handoff protocols. Use structured file formats for inter-agent communication. Batch results where possible.

### Failure: Divergence

Agents pursuing different goals without central coordination can drift from intended objectives.

**Mitigation:** Define clear objective boundaries for each agent. Implement convergence checks that verify progress toward shared goals. Use iteration limits on agent execution.

### Failure: Error Propagation

Errors in one agent's output propagate to downstream agents that consume that output.

**Mitigation:** Validate agent outputs before passing to consumers. Implement retry logic. Design for graceful degradation when components fail.

## Applying Patterns in Claude Code

### Command as Supervisor

Create a main command that:
1. Analyzes the task and creates a plan
2. Dispatches subagents via Task tool for specialized work
3. Collects results (via return values or shared files)
4. Synthesizes final output

### Subagents as Specialists

Define Subagents for specialized domains:
- Each Subagents focuses on one area of expertise
- Subagents receive focused context relevant to their specialty
- Subagents return structured outputs that coordinators can aggregate

### Files as Shared Memory

Use the file system for inter-agent coordination:
- State files track progress across agents
- Output files collect results from parallel work
- Task lists coordinate remaining work

### Example: Code Review Multi-Agent

```
Supervisor Command: review-code
├── Subagent: security-review (security specialist)
├── Subagent: performance-review (performance specialist)
├── Subagent: style-review (style/conventions specialist)
└── Aggregation: combine findings, deduplicate, prioritize
```

Each subagent receives only the code to review and their specialty focus. The supervisor aggregates all findings into a unified review.

## Guidelines

1. Design for context isolation as the primary benefit of multi-agent systems
2. Choose architecture pattern based on coordination needs, not organizational metaphor
3. Use file-based communication as the default for Claude Code multi-agent patterns
4. Implement explicit handoff protocols with clear state passing
5. Use critique/debate patterns for consensus rather than simple agreement
6. Monitor for supervisor bottlenecks and implement checkpointing via files
7. Validate outputs before passing between agents
8. Set iteration limits to prevent infinite loops
9. Test failure scenarios explicitly
10. Start simple—add multi-agent complexity only when single-agent approaches fail

## Memory and State Management

For tasks spanning multiple sessions or requiring persistent state, use file-based memory:

### Working Memory

The context window itself. Provides immediate access but vanishes when sessions end. Keep only active information; summarize completed work.

### Session Memory

Files created during a session that track progress:
- Task lists (what's done, what remains)
- Intermediate results
- Decision logs

### Long-Term Memory

Persistent files that survive across sessions:
- CLAUDE.md for project-level context
- Memory files in designated directories
- Structured knowledge bases in markdown or JSON

### Memory Patterns for Multi-Agent

- **Handoff files:** Agent A writes state, Agent B reads and continues
- **Result aggregation:** Multiple agents write to separate files, supervisor reads all
- **Progress tracking:** Shared task list updated by all agents
- **Knowledge accumulation:** Agents append findings to shared knowledge files

Choose the simplest memory mechanism that meets your needs. File-based memory is transparent, debuggable, and requires no infrastructure.

# Memory System Design

Memory provides the persistence layer that allows agents to maintain continuity across sessions and reason over accumulated knowledge. Simple agents rely entirely on context for memory, losing all state when sessions end. Sophisticated agents implement layered memory architectures that balance immediate context needs with long-term knowledge retention. The evolution from vector stores to knowledge graphs to temporal knowledge graphs represents increasing investment in structured memory for improved retrieval and reasoning.

## Core Concepts

Memory exists on a spectrum from immediate context to permanent storage. At one extreme, working memory in the context window provides zero-latency access but vanishes when sessions end. At the other extreme, permanent storage persists indefinitely but requires retrieval to enter context.

Simple vector stores lack relationship and temporal structure. Knowledge graphs preserve relationships for reasoning. Temporal knowledge graphs add validity periods for time-aware queries. Implementation choices depend on query complexity, infrastructure constraints, and accuracy requirements.

## Detailed Topics

### Memory Architecture Fundamentals

**The Context-Memory Spectrum**
Memory exists on a spectrum from immediate context to permanent storage. At one extreme, working memory in the context window provides zero-latency access but vanishes when sessions end. At the other extreme, permanent storage persists indefinitely but requires retrieval to enter context. Effective architectures use multiple layers along this spectrum.

The spectrum includes working memory (context window, zero latency, volatile), short-term memory (session-persistent, searchable, volatile), long-term memory (cross-session persistent, structured, semi-permanent), and permanent memory (archival, queryable, permanent). Each layer has different latency, capacity, and persistence characteristics.

**Why Simple Vector Stores Fall Short**
Vector RAG provides semantic retrieval by embedding queries and documents in a shared embedding space. Similarity search retrieves the most semantically similar documents. This works well for document retrieval but lacks structure for agent memory.

Vector stores lose relationship information. If an agent learns that "Customer X purchased Product Y on Date Z," a vector store can retrieve this fact if asked directly. But it cannot answer "What products did customers who purchased Product Y also buy?" because relationship structure is not preserved.

Vector stores also struggle with temporal validity. Facts change over time, but vector stores provide no mechanism to distinguish "current fact" from "outdated fact" except through explicit metadata and filtering.

**The Move to Graph-Based Memory**
Knowledge graphs preserve relationships between entities. Instead of isolated document chunks, graphs encode that Entity A has Relationship R to Entity B. This enables queries that traverse relationships rather than just similarity.

Temporal knowledge graphs add validity periods to facts. Each fact has a "valid from" and optionally "valid until" timestamp. This enables time-travel queries that reconstruct knowledge at specific points in time.

**Benchmark Performance Comparison**
The Deep Memory Retrieval (DMR) benchmark provides concrete performance data across memory architectures:

| Memory System | DMR Accuracy | Retrieval Latency | Notes |
|---------------|--------------|-------------------|-------|
| Zep (Temporal KG) | 94.8% | 2.58s | Best accuracy, fast retrieval |
| MemGPT | 93.4% | Variable | Good general performance |
| GraphRAG | ~75-85% | Variable | 20-35% gains over baseline RAG |
| Vector RAG | ~60-70% | Fast | Loses relationship structure |
| Recursive Summarization | 35.3% | Low | Severe information loss |

Zep demonstrated 90% reduction in retrieval latency compared to full-context baselines (2.58s vs 28.9s for GPT-5.2). This efficiency comes from retrieving only relevant subgraphs rather than entire context history.

GraphRAG achieves approximately 20-35% accuracy gains over baseline RAG in complex reasoning tasks and reduces hallucination by up to 30% through community-based summarization.

### Memory Layer Architecture

**Layer 1: Working Memory**
Working memory is the context window itself. It provides immediate access to information currently being processed but has limited capacity and vanishes when sessions end.

Working memory usage patterns include scratchpad calculations where agents track intermediate results, conversation history that preserves dialogue for current task, current task state that tracks progress on active objectives, and active retrieved documents that hold information currently being used.

Optimize working memory by keeping only active information, summarizing completed work before it falls out of attention, and using attention-favored positions for critical information.

**Layer 2: Short-Term Memory**
Short-term memory persists across the current session but not across sessions. It provides search and retrieval capabilities without the latency of permanent storage.

Common implementations include session-scoped databases that persist until session end, file-system storage in designated session directories, and in-memory caches keyed by session ID.

Short-term memory use cases include tracking conversation state across turns without stuffing context, storing intermediate results from tool calls that may be needed later, maintaining task checklists and progress tracking, and caching retrieved information within sessions.

**Layer 3: Long-Term Memory**
Long-term memory persists across sessions indefinitely. It enables agents to learn from past interactions and build knowledge over time.

Long-term memory implementations range from simple key-value stores to sophisticated graph databases. The choice depends on complexity of relationships to model, query patterns required, and acceptable infrastructure complexity.

Long-term memory use cases include learning user preferences across sessions, building domain knowledge bases that grow over time, maintaining entity registries with relationship history, and storing successful patterns that can be reused.

**Layer 4: Entity Memory**
Entity memory specifically tracks information about entities (people, places, concepts, objects) to maintain consistency. This creates a rudimentary knowledge graph where entities are recognized across multiple interactions.

Entity memory maintains entity identity by tracking that "John Doe" mentioned in one conversation is the same person in another. It maintains entity properties by storing facts discovered about entities over time. It maintains entity relationships by tracking relationships between entities as they are discovered.

**Layer 5: Temporal Knowledge Graphs**
Temporal knowledge graphs extend entity memory with explicit validity periods. Facts are not just true or false but true during specific time ranges.

This enables queries like "What was the user's address on Date X?" by retrieving facts valid during that date range. It prevents context clash when outdated information contradicts new data. It enables temporal reasoning about how entities changed over time.

### Memory Implementation Patterns

**Pattern 1: File-System-as-Memory**
The file system itself can serve as a memory layer. This pattern is simple, requires no additional infrastructure, and enables the same just-in-time loading that makes file-system-based context effective.

Implementation uses the file system hierarchy for organization. Use naming conventions that convey meaning. Store facts in structured formats (JSON, YAML). Use timestamps in filenames or metadata for temporal tracking.

Advantages: Simplicity, transparency, portability.
Disadvantages: No semantic search, no relationship tracking, manual organization required.

**Pattern 2: Vector RAG with Metadata**
Vector stores enhanced with rich metadata provide semantic search with filtering capabilities.

Implementation embeds facts or documents and stores with metadata including entity tags, temporal validity, source attribution, and confidence scores. Query includes metadata filters alongside semantic search.

**Pattern 3: Knowledge Graph**
Knowledge graphs explicitly model entities and relationships. Implementation defines entity types and relationship types, uses graph database or property graph storage, and maintains indexes for common query patterns.

**Pattern 4: Temporal Knowledge Graph**
Temporal knowledge graphs add validity periods to facts, enabling time-travel queries and preventing context clash from outdated information.

### Memory Retrieval Patterns

**Semantic Retrieval**
Retrieve memories semantically similar to current query using embedding similarity search.

**Entity-Based Retrieval**
Retrieve all memories related to specific entities by traversing graph relationships.

**Temporal Retrieval**
Retrieve memories valid at specific time or within time range using validity period filters.

### Memory Consolidation

Memories accumulate over time and require consolidation to prevent unbounded growth and remove outdated information.

**Consolidation Triggers**
Trigger consolidation after significant memory accumulation, when retrieval returns too many outdated results, periodically on a schedule, or when explicit consolidation is requested.

**Consolidation Process**
Identify outdated facts, merge related facts, update validity periods, archive or delete obsolete facts, and rebuild indexes.
