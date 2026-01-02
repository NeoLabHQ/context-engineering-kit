# First Principles Framework (FPF) Plugin

Structured reasoning plugin that makes AI decision-making transparent and auditable through hypothesis generation, logical verification, and evidence-based validation.

Focused on:

- **Transparent reasoning** - All decisions documented with full audit trails
- **Hypothesis-driven analysis** - Generate competing alternatives before evaluating
- **Evidence-based validation** - Computed reliability scores, not estimates
- **Human-in-the-loop** - AI generates options; humans decide (Transformer Mandate)

## Plugin Target

- Make AI reasoning auditable - full trail from hypothesis to decision
- Prevent premature conclusions - enforce systematic evaluation of alternatives
- Build project knowledge over time - decisions become reusable knowledge
- Enable informed decision-making - trust scores based on evidence quality

## Overview

The FPF plugin implements structured reasoning using [the First Principles Framework](https://github.com/ailev/FPF) methodology developed by Anatoly Levenchuk a methodology for rigorous, auditable reasoning. The killer feature is turning the black box of AI reasoning into a transparent, evidence-backed audit trail. 

The core cycle follows three modes of inference:

- Abduction — Generate competing hypotheses (don't anchor on the first idea).
- Deduction — Verify logic and constraints (does the idea make sense?).
- Induction — Gather evidence through tests or research (does the idea work in reality?).

Then, audit for bias, decide, and document the rationale in a durable record.

The framework addresses a fundamental challenge in AI-assisted development: making decision-making processes transparent and auditable. Rather than having AI jump to solutions, FPF enforces generating competing hypotheses, checking them logically, testing against evidence, then letting developers choose the path forward.

> **Warning:** This plugin loads the core FPF specification into context, which is large (~600k tokens). As a result it loaded into a subagent with Sonnet[1m] model. But it can consume your token limit quickly.

Implementation based on [quint-code](https://github.com/m0n0x41d/quint-code) by m0n0x41d.

## Quick Start

```bash
# Install the plugin
/plugin install fpf@NeoLabHQ/context-engineering-kit

# Start a decision process
/fpf:propose-hypotheses What caching strategy should we use?

# Commad will perform majority of orcestration and launch subagents to perform the work.
# Additionaly you will be asked to add your own hypotheses and review the results.
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Initialize Context                                           │
│    /fpf:propose-hypotheses <problem>                            │
│    (create .fpf/ directory structure)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ problem context captured
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Abduction: Generate Hypotheses                               │ ◀── add your own ───┐
│    (create L0 hypothesis files)                                 │                     │
└────────────────────────┬────────────────────────────────────────┘                     │
                         │                                                              │
                         │ 3-5 competing hypotheses                                     │
                         ▼                                                              │
┌─────────────────────────────────────────────────────────────────┐                     │
│ 3. User Input                                                   │                     │
│    (present summary, allow additions)                           │─────────────────────┘
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ all hypotheses collected
                         ▼ 
┌─────────────────────────────────────────────────────────────────┐
│ 4. Deduction: Verify Logic (Parallel)                           │
│    (check constraints, promote to L1 or invalidate)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ logically valid hypotheses (L1)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Induction: Validate Evidence (Parallel)                      │
│    (gather empirical evidence, promote L1 to L2)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ evidence-backed hypotheses (L2)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Audit Trust (Parallel)                                       │
│    (compute R_eff using Weakest Link principle)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ trust scores computed
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Decision                                                     │
│    (present comparison, user selects winner, create DRR)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ decision recorded
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Summary                                                      │
│    (DRR, winner rationale, next steps)                          │
└─────────────────────────────────────────────────────────────────┘
```

## Commands Overview

### /fpf:propose-hypotheses - Decision Cycle

Execute the complete FPF cycle from hypothesis generation through evidence validation to decision.

- Purpose - Make architectural decisions with full audit trail
- Output - `.fpf/decisions/DRR-<date>-<topic>.md` with winner and rationale

```bash
/fpf:propose-hypotheses [problem or decision to make]
```

#### Arguments

Natural language description of the decision or problem. Examples: "What caching strategy should we use?" or "How should we deploy our application?"

#### How It Works - ADI Cycle

The workflow follows three inference modes:

1. **Initialize Context** - Creates `.fpf/` directory structure and captures problem constraints

2. **Abduction: Generate Hypotheses** - FPF agent generates 3-5 generate plausible, diverse, and competing hypotheses in L0 folder.
   **How it works:**
   - You pose a problem or question
   - The AI (as *Abductor* persona) generates 3-5 candidate explanations or solutions
   - Each hypothesis is stored in `L0/` (unverified observations)
   - No hypothesis is privileged — anchoring bias is the enemy

   **Output:** Multiple L0 claims, each with:
   - Clear statement of the hypothesis
   - Initial reasoning for plausibility
   - Identified assumptions and constraints

3. **User Input** - Presents hypothesis table, allows user to add alternatives

4. **Deduction: Verify Logic (Parallel)** - Checks each hypothesis against constraints and typing, promotes to L1 or invalidates
   **How it works:**
   - The AI (as *Verifier* persona) checks each L0 hypothesis for:
   - Internal logical consistency
   - Compatibility with known constraints
   - Type correctness (does the solution fit the problem shape?)
   - Hypotheses that pass are promoted to `L1/`
   - Hypotheses that fail are moved to `invalid/` with explanation

   **Output:** L1 claims (logically sound) or invalidation records.

5. **Induction: Validate Evidence (Parallel)** - Gather empirical evidence through tests or research, promotes L1 hypotheses to L2
   **How it works:**
   - For **internal** claims: run tests, measure performance, verify behavior
   - For **external** claims: research documentation, benchmarks, case studies
   - Evidence is attached with:
   - Source and date (for decay tracking)
   - Congruence rating (how well does external evidence match our context?)
   - Claims that pass validation are promoted to `L2/`

   **Output:** L2 claims (empirically verified) with evidence chain.

6. **Audit(Parallel)** - Compute trust score R_eff using 
   - **WLNK (Weakest Link):** Assurance = min(evidence levels)
   - **Congruence Check:** Is external evidence applicable to our context?
   - **Bias Detection:** Are we anchoring on early hypotheses?

7. **Make Decision**: Presents comparison table, selects winner, creates Design Rationale Record (DRR) which captures:
   - decision
   - alternatives considered
   - evidence
   - expiry conditions

8. **Present Summary**: Shows DRR, winner rationale, and next steps

#### Usage Examples

```bash
# Caching strategy decision
/fpf:propose-hypotheses What caching strategy should we use?

# Deployment approach
/fpf:propose-hypotheses How should we deploy our application?

# Architecture decision
/fpf:propose-hypotheses Should we use microservices or monolith?

# Technology selection
/fpf:propose-hypotheses Which database should we use for high-write workloads?
```

#### When to Use

**Use it for:**

- Architectural decisions with long-term consequences
- Multiple viable approaches requiring systematic evaluation
- Decisions that need an auditable reasoning trail
- Building up project knowledge over time
Skip it for:

Quick fixes with obvious solutions
Easily reversible decisions
Time-critical situations where the overhead isn't justified

#### Best practices

- Frame as decisions - "What X should we use?" or "How should we Y?"
- Be specific about constraints - Include performance, cost, or time requirements
- Add your own hypotheses - Don't rely only on AI-generated options
- Review verification failures - Failed hypotheses reveal hidden constraints
- Document for future reference - DRRs become project knowledge

---

### /fpf:status - Check Progress

Show current FPF phase, hypothesis counts, and any warnings about stale evidence.

- Purpose - Understand current state of reasoning process
- Output - Status table with phase, counts, and warnings

```bash
/fpf:status
```

#### Arguments

None required.

#### How It Works

1. **Phase Detection**: Identifies current ADI cycle phase (IDLE, ABDUCTION, DEDUCTION, INDUCTION, DECISION)

2. **Hypothesis Count**: Reports counts per knowledge layer (L0, L1, L2, Invalid)

3. **Evidence Status**: Lists evidence files and their freshness

4. **Warning Detection**: Identifies stale evidence, orphaned hypotheses, or incomplete cycles

#### Usage Examples

```bash
# Check current status
/fpf:status
```

**Example Output:**

```markdown
## FPF Status

### Current Phase: DEDUCTION

You have 3 hypotheses in L0 awaiting verification.
Next step: Continue the FPF workflow to process L0 hypotheses.

### Hypothesis Counts

| Layer | Count |
|-------|-------|
| L0 | 3 |
| L1 | 0 |
| L2 | 0 |
| Invalid | 0 |

### Evidence Status

No evidence files yet (hypotheses not validated).

### No Warnings

All systems nominal.
```

#### Best practices

- Check before continuing - Know your current phase before proceeding
- Address warnings - Stale evidence affects trust scores
- Review invalid hypotheses - Understand why they failed

---

### /fpf:query - Search Knowledge Base

Search the FPF knowledge base for hypotheses, evidence, or decisions with assurance information.

- Purpose - Find and review stored knowledge with trust scores
- Output - Search results with layer, R_eff, and evidence counts

```bash
/fpf:query [keyword or hypothesis name]
```

#### Arguments

Keyword to search for, specific hypothesis name, or "DRR" to list decisions.

#### How It Works

1. **Keyword Search**: Searches hypothesis titles, descriptions, and evidence

2. **Hypothesis Details**: Returns full hypothesis info including layer, kind, scope, and R_eff

3. **DRR Listing**: Shows all Design Rationale Records with winner and rejected alternatives

#### Usage Examples

```bash
# Search by keyword
/fpf:query caching

# Query specific hypothesis
/fpf:query redis-caching

# List all decisions
/fpf:query DRR
```

**Example Output (keyword search):**

```markdown
Results:
| Hypothesis | Layer | R_eff |
|------------|-------|-------|
| redis-caching | L2 | 0.85 |
| cdn-edge-cache | L2 | 0.72 |
| lru-cache | invalid | N/A |
```

**Example Output (specific hypothesis):**

```markdown
# redis-caching (L2)

Title: Use Redis for Caching
Kind: system
Scope: High-load systems
R_eff: 0.85
Evidence: 2 files
```

**Example Output (DRR listing):**

```markdown
# Design Rationale Records

| DRR | Date | Winner | Rejected |
|-----|------|--------|----------|
| DRR-2025-01-15-caching | 2025-01-15 | redis-caching | cdn-edge |
```

#### Best practices

- Search before starting new decisions - Reuse existing knowledge
- Check R_eff scores - Higher scores indicate more reliable hypotheses
- Review DRRs - Past decisions inform future choices

---

### /fpf:decay - Manage Evidence Freshness

Check for stale evidence and choose how to handle it: refresh, deprecate, or waive.

- Purpose - Maintain evidence validity over time
- Output - Updated evidence status and trust scores

Evidence expires. A benchmark from six months ago might not reflect current performance. `/fpf:decay` shows you what's stale and gives you three options:

- Refresh — Re-run tests to get fresh evidence
- Deprecate — Downgrade the hypothesis if the decision needs rethinking
- Waive — Accept the risk temporarily with documented rationale

```bash
/fpf:decay waive the benchmark until February, we'll re-test after launch
```

#### Arguments

None required. Command is interactive.

#### How It Works

1. **Staleness Check**: Identifies evidence files past their freshness threshold

2. **Options Presented**: For each stale evidence:
   - **Refresh**: Re-run tests for fresh evidence
   - **Deprecate**: Downgrade hypothesis, flag decision for review
   - **Waive**: Accept risk temporarily with documented rationale

3. **Trust Recalculation**: Updates R_eff scores based on evidence changes

#### Usage Examples

```bash
# Check for stale evidence
/fpf:decay

# Natural language waiver
# User: Waive the benchmark until February, we'll re-run after migration.

# Agent response:
# Waiver recorded:
# - Evidence: ev-benchmark-2024-06-15
# - Until: 2025-02-01
# - Rationale: Will re-run after migration
```

#### Best practices

- Run periodically - Evidence expires; benchmarks from 6 months ago may not reflect current performance
- Document waivers - Always include rationale and expiration date
- Refresh critical evidence - High-impact decisions deserve fresh data

---

### /fpf:actualize - Reconcile with Codebase

Update the knowledge base to reflect codebase changes that may affect existing hypotheses.

- Purpose - Keep knowledge synchronized with implementation
- Output - Updated hypothesis validity and evidence relevance

This command serves as the Observe phase of the FPF's Canonical Evolution Loop (B.4). It reconciles your documented knowledge with the current state of the codebase by:

- Detecting Context Drift: Checks if project files (like package.json) have changed, potentially making your context.md stale.
- Finding Stale Evidence: Finds evidence whose carrier_ref (the file it points to) has been modified in git.
- Flagging Outdated Decisions: Identifies decisions whose underlying evidence chain has been impacted by recent code changes.

```bash
/fpf:actualize
```

#### How It Works

1. **Change Detection**: Identifies code changes since last actualization
2. **Impact Analysis**: Determines which hypotheses and evidence are affected
3. **Validity Update**: Marks affected hypotheses for re-verification if needed
4. **Report Generation**: Summarizes changes and recommended actions

#### Usage Examples

```bash
# After major refactoring
/fpf:actualize

# After dependency updates
/fpf:actualize
```

#### Best practices

- Run after major changes - Refactoring may invalidate previous assumptions
- Review impact report - Some hypotheses may need re-evaluation
- Update evidence - Changed code may need new benchmarks

---

### /fpf:reset - Start Fresh

Archive the current session and return to IDLE state for a new reasoning cycle.

- Purpose - Clear current state while preserving history
- Output - Archived session in `.fpf/sessions/`

```bash
/fpf:reset
```

#### Arguments

None required. Command is interactive.

#### How It Works

1. **Reset Type Selection**:
   - **Soft Reset**: Archive current session, start fresh (recommended)
   - **Hard Reset**: Delete all FPF data (cannot be undone)
   - **Decision Reset**: Keep hypotheses, re-evaluate from earlier phase

2. **Session Archive**: Creates timestamped archive in `.fpf/sessions/`

3. **State Clear**: Clears knowledge directories based on reset type

#### Usage Examples

```bash
/fpf:reset

# Agent: What type of reset would you like?
# 1. Soft Reset - Archive current session, start fresh
# 2. Hard Reset - Delete all FPF data (cannot be undone)
# 3. Decision Reset - Keep hypotheses, re-evaluate from earlier phase

# User: Soft reset please

# Agent: Creating session archive...
#        [Creates .fpf/sessions/session-2025-01-15-reset.md]
#        Session archived. Knowledge directories cleared.
#        Ready for new reasoning cycle.
```

#### When to Reset

| Scenario | Recommended Action |
|----------|-------------------|
| Starting a new problem | Soft reset (archive) |
| Wrong direction, start over | Soft reset |
| Testing/learning FPF | Hard reset |
| Re-evaluate with new info | Decision reset |
| Context changed significantly | Soft reset + update context |

#### Best practices

- Prefer soft reset - Always preserve history for reference
- Hard reset only for testing - Production knowledge is valuable
- Decision reset for pivots - When new information changes the equation

---

## Available Agents

| Agent | Description | Used By |
|-------|-------------|---------|
| `fpf-agent` | FPF reasoning specialist for hypothesis generation, verification, validation, and trust calculus using the ADI cycle | All commands |

### fpf-agent

**Purpose**: Executes FPF reasoning tasks with file operations for persisting knowledge state.

**Tools**: Read, Write, Glob, Grep, Bash (mkdir, mv, touch)

**Responsibilities**:
- Create hypothesis files in knowledge layers
- Move files between L0/L1/L2/invalid directories
- Create evidence files and audit reports
- Generate Design Rationale Records (DRRs)

## Key Concepts

| Concept | Description |
|---------|-------------|
| **ADI Cycle** | Abduction-Deduction-Induction reasoning loop |
| **Knowledge Layers** | L0 (Conjecture) -> L1 (Substantiated) -> L2 (Corroborated) |
| **WLNK** | Weakest Link principle: R_eff = min(evidence_scores) |
| **Holon** | Knowledge unit with identity, layer, kind, and assurance scores |
| **DRR** | Design Rationale Record documenting decisions |
| **Transformer Mandate** | AI generates options; humans decide |

### Knowledge Layers (Epistemic Status)

| Layer | Name | Meaning | How to reach |
|-------|------|---------|--------------|
| **L0** | Conjecture | Unverified hypothesis | Generate hypotheses |
| **L1** | Substantiated | Passed logical check | Verify logic |
| **L2** | Corroborated | Empirically validated | Validate evidence |
| **Invalid** | Falsified | Failed verification | FAIL verdict |

### Congruence Levels

| Level | Context Match | Penalty |
|-------|--------------|---------|
| CL3 | Same (internal test) | None |
| CL2 | Similar (related project) | Minor |
| CL1 | Different (external docs) | Significant |

### The Transformer Mandate

A core FPF principle: **A system cannot transform itself.**

- AI generates options with evidence
- Human decides
- Making architectural choices autonomously is a PROTOCOL VIOLATION

This ensures accountability and prevents AI from making unsupervised decisions.

## Directory Structure

The FPF plugin creates and manages this directory structure:

```
.fpf/
├── context.md              # Problem context and constraints
├── knowledge/
│   ├── L0/                 # Candidate hypotheses (Conjecture)
│   ├── L1/                 # Substantiated hypotheses (Passed logic)
│   ├── L2/                 # Validated hypotheses (Evidence-backed)
│   └── invalid/            # Rejected hypotheses (Failed verification)
├── evidence/               # Evidence files and audit reports
├── decisions/              # DRR files
└── sessions/               # Archived sessions
```

## When to Use FPF

**Use it for:**
- Architectural decisions with long-term consequences
- Multiple viable approaches requiring systematic evaluation
- Decisions needing auditable reasoning trails
- Building project knowledge over time

**Skip it for:**
- Quick fixes with obvious solutions
- Easily reversible decisions
- Time-critical situations

## Theoretical Foundation

### Core Methodology

- **[First Principles Framework (FPF)](https://github.com/ailev/FPF)** - Original methodology by Anatoly Levenchuk for structured epistemic reasoning
- **[quint-code](https://github.com/m0n0x41d/quint-code)** - Implementation this plugin is based on

### Supporting Concepts

- **Abduction-Deduction-Induction Cycle** - Classical scientific reasoning methodology
- **Weakest Link Principle** - Trust computation based on minimum evidence quality
- **Design Rationale** - Documenting not just decisions but the reasoning behind them
