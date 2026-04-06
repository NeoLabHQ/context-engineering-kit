# /do-in-steps

Execute complex tasks through sequential sub-agent orchestration with intelligent model selection, meta-judge → LLM-as-a-judge verification.

- Purpose - Execute dependent tasks sequentially where each step builds on previous outputs
- Pattern - Supervisor/Orchestrator with sequential dispatch, parallel meta-judge + implementation, judge verification, and iteration loop
- Output - Comprehensive report with all step results, judge scores, and integration summary
- Key Benefit - Prevents context pollution while ensuring quality through independent, specification-driven verification

## Quality Assurance

Three-layer verification: self-critique (internal) + meta-judge evaluation spec (per step) + LLM-as-a-judge (external) with iteration until passing

## Pattern: Sequential Orchestration with Meta-Judge and Judge Verification

```
Phase 1: Task Analysis and Decomposition
         Task → Identify Dependencies → Define Step Boundaries
                     │
Phase 2: Model Selection
         For each step: Assess Complexity + Scope + Risk → Select Model
                     │
Phase 3: Sequential Execution with Parallel Meta-Judge + Judge Verification
         ┌──────────────────────────────────────────────────────────────────────┐
         │ For each Step N:                                                     │
         │                                                                      │
         │   ┌─────────────┐                                                    │
         │   │ Meta-Judge  │──┐ (parallel)                                      │
         │   │ (sadd:meta- │  │                                                 │
         │   │  judge)     │  │   ┌──────────┐     ┌──────────────────┐        │
         │   └─────────────┘  ├──▶│  Judge   │────▶│ Parse Verdict    │        │
         │   ┌─────────────┐  │   │ (sadd:   │     │ (Orchestrator)   │        │
         │   │ Implementer │──┘   │  judge)  │     └──────────────────┘        │
         │   │ (Sub-agent) │      └──────────┘              │                   │
         │   └─────────────┘                                ▼                   │
         │          ▲                          ┌───────────────────────┐        │
         │          │                          │ PASS (≥4.0)?         │        │
         │          │                          │ ├─ YES → Next Step   │        │
         │          │                          │ ├─ ≥3.0 + low-pri   │        │
         │          │                          │ │   issues → PASS    │        │
         │          │                          │ └─ NO → Retry?       │        │
         │          │                          │   ├─ <3 retries →    │        │
         │          │                          │   │   Retry (reuse   │        │
         │          │                          │   │   meta-judge     │        │
         │          │                          │   │   spec)          │        │
         │          │                          │   └─ ≥3 → Escalate  │        │
         │          │                          └───────────────────────┘        │
         │          │                                       │                   │
         │          └──────────── feedback ─────────────────┘                   │
         └──────────────────────────────────────────────────────────────────────┘
         Step 1 → Judge ✓ → Step 2 → Judge ✓ → Step 3 → Judge ✓ → ...
                  (prev step summaries flow forward as context)
                     │
Phase 4: Final Summary and Report
         Aggregate results, judge scores, meta-judge specs, files modified, decisions made
```

## Usage

```bash
# Interface change with consumer updates
/do-in-steps "Change return type of UserService.getUser() from User to UserDTO and update all consumers"

# Feature addition across layers
/do-in-steps "Add email notification capability to the order processing system"

# Multi-file refactoring with breaking changes
/do-in-steps "Rename 'userId' to 'accountId' across the codebase - affects interfaces, implementations, and callers"
```

## When to Use

**Good use cases:**

- Changes that cascade through multiple files/layers
- Interface modifications with consumers to update
- Feature additions spanning multiple components
- Refactoring with dependency chains
- Any task where "Step N depends on Step N-1"

**Do NOT use when:**

- Independent tasks that could run in parallel → use `/do-in-parallel`
- Single-step tasks → use `/launch-sub-agent`
- Tasks needing exploration before commitment → use `/tree-of-thoughts`
- High-stakes tasks needing multiple approaches → use `/do-competitively`

## Quality Enhancement Techniques

| Phase | Technique | Benefit |
|-------|-----------|---------|
| **Phase 3** | Self-Critique | Implementation agents verify own work before submission, catching 40-60% of issues |
| **Phase 3** | Meta-Judge (`sadd:meta-judge`) | Generates step-specific evaluation rubrics, checklists, and scoring criteria in parallel with implementation |
| **Phase 3** | LLM-as-a-Judge (`sadd:judge`) | Independent judge evaluates each step against meta-judge specification; `CLAUDE_PLUGIN_ROOT` passed to both agents |
| **Phase 3** | Iteration Loop | Failed steps retry with judge feedback until passing (max 3 retries) or escalate; retries reuse same meta-judge spec |
| **Phase 3** | Context Passing | Previous step summaries (files modified, key changes, decisions) flow to next step's implementation agent; max ~200 words per step |

## Theoretical Foundation

- **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Step-by-step reasoning improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique loops before submission
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Independent evaluation with structured rubrics
- **[Multi-Agent Debate](https://arxiv.org/abs/2305.14325)** (Du et al., 2023) - Fresh context prevents accumulated confusion
