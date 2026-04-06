# multi-agent-patterns - Multi-Agent Analysis Orchestration

Design multi-agent architectures for complex tasks. Use when single-agent context limits are exceeded, when tasks decompose naturally into subtasks, or when specializing agents improves quality.

The critical insight is that sub-agents exist primarily to isolate context, not to anthropomorphize role division.

**Sequential Analysis:**

```
Command → Agent 1 → Agent 2 → Agent 3 → Synthesized Result
```

**Parallel Analysis:**

```
         ┌─ Agent 1 ─┐
Command ─┼─ Agent 2 ─┼─ Synthesized Result
         └─ Agent 3 ─┘
```

**Debate Pattern:**

```
Command → Agent 1 ─┐
       → Agent 2 ─┼─ Debate → Consensus → Result
       → Agent 3 ─┘
```

## Why Multi-Agent Architectures

| Problem | Solution |
|---|---|
| **Context Bottleneck** | Partition work across multiple context windows; each agent operates in clean, focused context |
| **Sequential Bottleneck** | Parallelize independent subtasks across agents; total time approaches longest subtask |
| **Generalist Overhead** | Specialize agents with lean, focused context optimized for their domain |

## Architecture Patterns

### Pattern 1: Supervisor/Orchestrator

Central agent delegates to specialists and synthesizes results.

```
User Request → Supervisor → [Specialist A, B, C] → Aggregation → Output
```

| Aspect | Details |
|---|---|
| **When to use** | Clear task decomposition, need human oversight, coordination across domains |
| **Advantages** | Strict workflow control, easier human-in-the-loop, adherence to plans |
| **Disadvantages** | Supervisor context becomes bottleneck, failures cascade, "telephone game" risk |

**Telephone Game Problem:** Supervisors can paraphrase sub-agent responses incorrectly, losing fidelity. Fix: allow sub-agents to write directly to shared files or return output verbatim rather than having the supervisor rewrite everything.

### Pattern 2: Peer-to-Peer/Swarm

No central control; agents communicate directly based on predefined protocols.

| Aspect | Details |
|---|---|
| **When to use** | Flexible exploration, emergent requirements, rigid planning is counterproductive |
| **Advantages** | No single point of failure, scales for breadth-first exploration |
| **Disadvantages** | Coordination complexity, divergence risk without central state keeper |

### Pattern 3: Hierarchical

Agents organized into layers: strategy (goal definition), planning (task decomposition), execution (atomic tasks).

```
Strategy Layer → Planning Layer → Execution Layer
```

| Aspect | Details |
|---|---|
| **When to use** | Large projects with layered abstraction, enterprise workflows |
| **Advantages** | Clear separation of concerns, different context structures at different levels |
| **Disadvantages** | Coordination overhead between layers, potential misalignment |

## Context Isolation as Design Principle

The primary purpose of multi-agent architectures is context isolation. Each sub-agent operates in a clean context window focused on its subtask.

### Isolation Mechanisms

| Mechanism | Description | When to Use |
|---|---|---|
| **Instruction passing** | Coordinator creates focused instructions; sub-agent receives only what it needs | Simple, well-defined subtasks |
| **File system memory** | Agents read/write to persistent storage; file system as coordination mechanism | Complex tasks requiring shared state |
| **Full context delegation** | Coordinator shares entire context with sub-agent | Use sparingly; defeats isolation purpose |

## Consensus and Coordination

### The Voting Problem

Simple majority voting treats hallucinations as equal to sound reasoning. Without intervention, multi-agent discussions can devolve into consensus on false premises.

### Approaches

| Approach | Description |
|---|---|
| **Weighted contributions** | Weight by confidence or expertise; higher domain expertise carries more weight |
| **Debate protocols** | Agents critique each other over multiple rounds; adversarial critique yields higher accuracy than collaborative consensus |
| **Trigger-based intervention** | Monitor for stall triggers (no progress), sycophancy triggers (agents mimic without unique reasoning), divergence triggers (drifting from objective) |

## Failure Modes and Mitigations

| Failure | Cause | Mitigation |
|---|---|---|
| **Supervisor Bottleneck** | Supervisor accumulates context from all workers | Output constraints so workers return distilled summaries; file-based checkpointing |
| **Coordination Overhead** | Communication consumes tokens and introduces latency | Minimize communication with clear handoff protocols; batch results |
| **Divergence** | Agents pursuing different goals without central coordination | Clear objective boundaries; convergence checks; iteration limits |
| **Error Propagation** | Errors in one agent's output propagate downstream | Validate outputs before passing; retry logic; graceful degradation |

## Processes

### Sequential Execution Process

1. **Load Plan**: Read plan file and create TodoWrite with all tasks
2. **Execute Task with Subagent**: For each task, dispatch a fresh subagent:
   - Subagent reads the specific task from the plan
   - Implements exactly what the task specifies
   - Writes tests following project conventions
   - Verifies implementation works
   - Commits the work
   - Reports back with summary
3. **Review Subagent's Work**: Dispatch a code-reviewer subagent:
   - Reviews what was implemented against the plan
   - Returns: Strengths, Issues (Critical/Important/Minor), Assessment
   - Quality gate: Must pass before proceeding
4. **Apply Review Feedback**:
   - Fix Critical issues immediately (dispatch fix subagent)
   - Fix Important issues before next task
   - Note Minor issues for later
5. **Mark Complete, Next Task**: Update TodoWrite and proceed to next task
6. **Final Review**: After all tasks, dispatch final reviewer for overall assessment
7. **Complete Development**: Use finishing-a-development-branch skill to verify and close

### Parallel Execution Process

1. **Load and Review Plan**: Read plan, identify concerns, create TodoWrite
2. **Execute Batch**: Execute first 3 tasks (default batch size):
   - Mark each as in_progress
   - Follow each step exactly
   - Run verifications as specified
   - Mark as completed
3. **Report**: Show what was implemented and verification output
4. **Continue**: Apply feedback if needed, execute next batch
5. **Complete Development**: Final verification and close

### Parallel Investigation Process

For multiple unrelated failures (different files, subsystems, bugs):

1. **Identify Independent Domains**: Group failures by what is broken
2. **Create Focused Agent Tasks**: Each agent gets specific scope, clear goal, constraints
3. **Dispatch in Parallel**: All agents run concurrently
4. **Review and Integrate**: Verify fixes do not conflict, run full suite

#### Quality Gates

| Checkpoint | Gate Type | Action on Failure |
|---|---|---|
| After each task (sequential) | Code review | Fix issues before next task |
| After batch (parallel) | Human review | Apply feedback, continue |
| Final review | Comprehensive review | Address all findings |
| Before merge | Full test suite | All tests must pass |

**Issue Severity Handling:**

- **Critical**: Fix immediately, do not proceed until resolved
- **Important**: Fix before next task or batch
- **Minor**: Note for later, do not block progress

## Applying Patterns in Claude Code

### Command as Supervisor

Create a main command that analyzes the task, dispatches subagents via Task tool for specialized work, collects results (via return values or shared files), and synthesizes final output.

### Subagents as Specialists

Each subagent focuses on one area of expertise, receives focused context relevant to their specialty, and returns structured outputs that coordinators can aggregate.

### Files as Shared Memory

Use the file system for inter-agent coordination: state files track progress, output files collect results from parallel work, task lists coordinate remaining work.

### Example: Code Review Multi-Agent

```
Supervisor Command: review-code
├── Subagent: security-review (security specialist)
├── Subagent: performance-review (performance specialist)
├── Subagent: style-review (style/conventions specialist)
└── Aggregation: combine findings, deduplicate, prioritize
```

## Memory and State Management

For tasks spanning multiple sessions or requiring persistent state, use file-based memory.

### Memory Layers

| Layer | Scope | Persistence | Use Case |
|---|---|---|---|
| **Working Memory** | Context window | Volatile (session end) | Active information, scratchpad calculations |
| **Session Memory** | Current session | Session-scoped files | Task lists, intermediate results, decision logs |
| **Long-Term Memory** | Cross-session | Persistent files | CLAUDE.md, memory files, knowledge bases |
| **Entity Memory** | Cross-session | Persistent graph | Track entity identity, properties, relationships |
| **Temporal Knowledge Graph** | Cross-session | Persistent with validity periods | Time-travel queries, temporal reasoning |

### Memory Patterns for Multi-Agent

- **Handoff files**: Agent A writes state, Agent B reads and continues
- **Result aggregation**: Multiple agents write to separate files, supervisor reads all
- **Progress tracking**: Shared task list updated by all agents
- **Knowledge accumulation**: Agents append findings to shared knowledge files

### Memory Architecture Performance

| Memory System | DMR Accuracy | Notes |
|---|---|---|
| Temporal KG (e.g., Zep) | 94.8% | Best accuracy, fast retrieval |
| MemGPT | 93.4% | Good general performance |
| GraphRAG | ~75-85% | 20-35% gains over baseline RAG |
| Vector RAG | ~60-70% | Loses relationship structure |
| Recursive Summarization | 35.3% | Severe information loss |

### Memory Implementation Patterns

| Pattern | Description | Trade-offs |
|---|---|---|
| **File-System-as-Memory** | Use file system hierarchy, naming conventions, structured formats | Simple, transparent, no semantic search |
| **Vector RAG with Metadata** | Semantic search with entity tags, temporal validity, confidence | Good retrieval, lacks relationship tracking |
| **Knowledge Graph** | Explicitly model entities and relationships | Relationship queries, infrastructure complexity |
| **Temporal Knowledge Graph** | Validity periods on facts; time-travel queries | Best accuracy, highest implementation cost |

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
10. Start simple -- add multi-agent complexity only when single-agent approaches fail
