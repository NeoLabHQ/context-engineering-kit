# Decision Making with FPF

Structured decision-making workflow using the First Principles Framework (FPF) for hypothesis-driven architectural choices.

For quick decisions with obvious solutions, skip FPF and decide directly. For decisions needing auditable reasoning trails, use this workflow.

## When to Use

- Architectural decisions with long-term consequences
- Multiple viable approaches requiring systematic evaluation
- Decisions needing auditable reasoning trails
- Building project knowledge over time

## Skip FPF For

- Quick fixes with obvious solutions
- Easily reversible decisions
- Time-critical situations

## Plugins needed for this workflow

- [FPF](../plugins/fpf/README.md)

## Workflow

### How It Works

```md
┌─────────────────────────────────────────────┐
│ 1. Generate Hypotheses                      │
│    (3-5 competing approaches)               │
└────────────────────┬────────────────────────┘
                     │
                     │ FPF agent generates L0 hypotheses
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Add User Hypotheses (optional)           │ ◀─── add more ────────────────┐
│    (present summary and ask for additions)  │                               │
└────────────────────┬────────────────────────┘                               │
                     │                                                        │
                     │ no more to add                                         │
                     ▼                                                        │
┌─────────────────────────────────────────────┐                               │
│ 3. Verify Logic (parallel)                  │───────────────────────────────┘
│    (L0 → L1 or invalid)                     │
└────────────────────┬────────────────────────┘
                     │
                     │ substantiated hypotheses
                     ▼
┌─────────────────────────────────────────────┐
│ 4. Validate Evidence (parallel)             │
│    (L1 → L2 with confidence scores)         │
└────────────────────┬────────────────────────┘
                     │
                     │ corroborated hypotheses
                     ▼
┌─────────────────────────────────────────────┐
│ 5. Audit Trust (parallel)                   │
│    (compute R_eff using WLNK)               │
└────────────────────┬────────────────────────┘
                     │
                     │ ranked hypotheses with trust scores
                     ▼
┌─────────────────────────────────────────────┐
│ 6. Make Decision                            │
│    (create DRR with user approval)          │
└────────────────────┬────────────────────────┘
                     │
                     │ decision documented in .fpf/
                     ▼
┌─────────────────────────────────────────────┐
│ 7. Present Results                          │
│    (final summary with next steps)          │
└─────────────────────────────────────────────┘
```

### 1. Generate hypotheses

Use the `/propose-hypotheses` command to start the FPF cycle. The FPF agent will generate 3-5 competing hypotheses for your problem.

```bash
/propose-hypotheses What caching strategy should we use?
```

After starting, the FPF agent will:

- Initialize `.fpf/` directory structure if needed
- Frame your problem in the bounded context
- Generate diverse L0 hypotheses (conservative + radical approaches)
- Save hypotheses to `.fpf/knowledge/L0/`

### 2. Add user hypotheses

The workflow presents a summary table of generated hypotheses and asks: "Would you like to add any hypotheses of your own?"

```md
Generated hypotheses:

| ID | Title | Kind | Scope |
|----|-------|------|-------|
| H1 | Redis cache | Pattern | Infrastructure |
| H2 | In-memory cache | Pattern | Application |
| H3 | Memcached | Pattern | Infrastructure |

Would you like to add any hypotheses of your own?
```

If you have additional approaches to consider, describe them. The FPF agent will formalize them into proper hypothesis files. This loop continues until you're satisfied with the hypothesis set.

### 3. Verify logic

The workflow launches parallel FPF agents to verify each L0 hypothesis against logical constraints.

For each hypothesis:

- Check internal consistency
- Apply first-principles reasoning
- Verify against project constraints
- Move to L1 (substantiated) or invalid

Hypotheses that pass verification are promoted to `.fpf/knowledge/L1/`. Failed hypotheses move to `.fpf/knowledge/invalid/` with failure reasons documented.

### 4. Validate evidence

The workflow launches parallel FPF agents to gather empirical evidence for each L1 hypothesis.

For each substantiated hypothesis:

- Search codebase for similar patterns
- Review documentation and external sources
- Run tests or benchmarks if applicable
- Compute confidence scores based on evidence

Validated hypotheses are promoted to `.fpf/knowledge/L2/` with confidence scores and evidence references.

### 5. Audit trust

The workflow launches parallel FPF agents to compute effective reliability (R_eff) for each L2 hypothesis using the Weakest Link (WLNK) principle.

For each corroborated hypothesis:

- Apply evidence decay factors for freshness
- Consider congruence levels (CL1/CL2/CL3)
- Compute R_eff = min(evidence_scores)
- Calculate confidence intervals

The trust audit produces ranked hypotheses with their R_eff scores.

### 6. Make decision

The FPF agent creates a Decision Readiness Report (DRR) with:

- Ranked hypotheses by R_eff and confidence
- Comparison table showing trade-offs
- Recommended action with rationale
- Evidence supporting each hypothesis

You review the DRR and select the winning hypothesis. The decision is documented in `.fpf/decisions/` with full audit trail.

### 7. Present results

The workflow presents the final summary:

- Selected hypothesis with rationale
- R_eff score and confidence interval
- Supporting evidence
- Next steps for implementation

All decision artifacts are preserved in `.fpf/` for future reference and audit.

## Key Concepts

### ADI Cycle

The FPF workflow follows the Abduction-Deduction-Induction reasoning loop:

| Phase | Description | Output |
|-------|-------------|--------|
| **Abduction** | Generate hypotheses to explain anomaly | L0 (Conjecture) |
| **Deduction** | Verify logical consistency | L1 (Substantiated) or Invalid |
| **Induction** | Validate with empirical evidence | L2 (Corroborated) |

### Knowledge Layers

Hypotheses progress through epistemic layers as they gain assurance:

| Layer | Name | Meaning | How to reach |
|-------|------|---------|--------------|
| **L0** | Conjecture | Unverified hypothesis | Generate hypotheses |
| **L1** | Substantiated | Passed logical check | Verify logic |
| **L2** | Corroborated | Empirically validated | Validate evidence |
| **Invalid** | Falsified | Failed verification | FAIL verdict |

### Trust Calculus

FPF computes reliability scores rather than estimates:

| Concept | Description |
|---------|-------------|
| **R_eff** | Effective reliability = min(evidence_scores) using WLNK |
| **WLNK** | Weakest Link principle: system reliability limited by weakest evidence |
| **Congruence** | Context match penalty (CL3=same, CL2=similar, CL1=different) |
| **Decay** | Evidence freshness reduces reliability over time |

### Transformer Mandate

A core FPF principle: **A system cannot transform itself.**

- FPF agent generates options with evidence
- Human decides which hypothesis to implement
- Making architectural choices autonomously is a PROTOCOL VIOLATION

This ensures accountability and prevents AI from making unsupervised decisions.

## Example: Choosing a Caching Strategy

### Starting the workflow

```bash
/propose-hypotheses What caching strategy should we use for the product catalog?
```

### Generated hypotheses (L0)

```md
The FPF agent generates:

H1: Redis cache with TTL-based expiration
    - Kind: Pattern
    - Scope: Infrastructure
    - Rationale: Proven solution, good for distributed systems

H2: In-memory LRU cache in application
    - Kind: Pattern
    - Scope: Application
    - Rationale: No external dependencies, simple deployment

H3: Two-tier cache (in-memory + Redis)
    - Kind: Pattern
    - Scope: Hybrid
    - Rationale: Best performance, more complexity
```

### User adds hypothesis

```md
Would you like to add any hypotheses?

User: Yes, we should consider Memcached as an option

FPF agent formalizes:

H4: Memcached distributed cache
    - Kind: Pattern
    - Scope: Infrastructure
    - Rationale: Lighter than Redis, simpler protocol
```

### Verification results (L0 → L1)

```md
Parallel verification:

H1 (Redis): PASS
    - Consistent with deployment constraints
    - Compatible with existing infrastructure

H2 (In-memory): PASS
    - Meets performance requirements
    - Acceptable memory constraints

H3 (Two-tier): PASS
    - Logical consistency verified
    - Complexity manageable

H4 (Memcached): FAIL → Invalid
    - Reason: Lacks persistence needed for catalog
    - Moved to .fpf/knowledge/invalid/
```

### Validation results (L1 → L2)

```md
Parallel validation:

H1 (Redis): R=0.85
    - Evidence: Internal benchmark (CL3)
    - Evidence: Production use in similar service (CL2)
    - Weakest link: 0.85

H2 (In-memory): R=0.70
    - Evidence: External docs (CL1)
    - Evidence: Local testing (CL3)
    - Weakest link: 0.70

H3 (Two-tier): R=0.75
    - Evidence: External case study (CL1)
    - Evidence: Internal prototype (CL2)
    - Weakest link: 0.75
```

### Trust audit

```md
Final ranking by R_eff:

| Hypothesis | R_eff | Weakest Link | Decision |
|------------|-------|--------------|----------|
| H1 (Redis) | 0.85 | Internal benchmark | Recommended |
| H3 (Two-tier) | 0.75 | External case study | Alternative |
| H2 (In-memory) | 0.70 | External docs | Fallback |
```

### Decision

```md
User selects: H1 (Redis cache with TTL-based expiration)

DRR created:
    - Selected: Redis cache
    - R_eff: 0.85
    - Rationale: Highest reliability, proven in production
    - Next steps: Configure Redis instance, implement cache layer
    - Fallback: H3 (two-tier) if performance issues arise

Decision saved to .fpf/decisions/2025-01-15-caching-strategy.md
```

## Managing Evidence Freshness

Evidence expires. A benchmark from 6 months ago may not reflect current performance.

### Check stale evidence

```bash
/decay
```

The decay command shows evidence that needs attention:

```md
Stale evidence found:

Evidence: ev-redis-benchmark-2024-06-15
Age: 7 months
Hypothesis: H1 (Redis cache)
Impact: R_eff drops from 0.85 to 0.75

Three options:
1. Refresh: Re-run benchmark for fresh evidence
2. Deprecate: Downgrade hypothesis if decision needs rethinking
3. Waive: Accept risk temporarily with documented rationale
```

### Waive stale evidence

```bash
User: Waive the benchmark until February, we'll re-run after migration

FPF records waiver:
    - Evidence: ev-redis-benchmark-2024-06-15
    - Waived until: 2025-02-01
    - Rationale: Will re-run after migration
    - Risk accepted: R_eff may not reflect current performance
```

## Directory Structure

The FPF plugin creates and manages this structure:

```
.fpf/
├── context.md              # Problem context and constraints
├── knowledge/
│   ├── L0/                 # Candidate hypotheses
│   ├── L1/                 # Substantiated hypotheses
│   ├── L2/                 # Validated hypotheses
│   └── invalid/            # Rejected hypotheses
├── evidence/               # Evidence files and audit reports
├── decisions/              # DRR files
└── sessions/               # Archived sessions
```

All decision artifacts are preserved for audit and knowledge building.

## Integration with Other Workflows

FPF integrates with other workflows at decision points:

### Before specification (SDD)

Use FPF to decide on architecture approach before creating the spec:

```bash
/propose-hypotheses What architecture pattern should we use for this feature?
# Review DRR and select approach
/sdd:add-task "Implement feature using [selected approach]"
/plan-task
```

### During brainstorming

Use FPF to evaluate alternative designs:

```bash
/sdd:brainstorm Users want better search but requirements are unclear
# After exploring approaches, use FPF to decide
/propose-hypotheses Which search implementation should we choose?
# Continue with selected approach
/sdd:add-task "Implement search with [selected approach]"
/plan-task
```

### For technical decisions

Use FPF for any architectural choice needing audit trail:

```bash
/propose-hypotheses How should we deploy our application?
/propose-hypotheses What testing strategy should we use?
/propose-hypotheses Which database should we choose?
```

## Utility Commands

FPF provides utility commands for managing the knowledge base:

| Command | Description |
|---------|-------------|
| `/status` | Show current FPF phase and hypothesis counts |
| `/query` | Search knowledge base with assurance info |
| `/decay` | Manage evidence freshness (refresh/deprecate/waive) |
| `/actualize` | Reconcile knowledge with codebase changes |
| `/reset` | Archive session and return to IDLE |

## Related Resources

- [FPF Plugin Documentation](../plugins/fpf/README.md) - Complete plugin reference
- [Brainstorming to Implementation](./brainstorming-to-implementation.md) - Combine brainstorming with FPF decisions
- [Spec-Driven Development](./spec-driven-development.md) - Use FPF decisions in SDD workflow
