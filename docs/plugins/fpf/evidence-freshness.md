# Evidence Freshness

Evidence has an expiration date. This guide explains why that matters and what to do about it.

## Why Evidence Expires

Imagine you benchmarked Redis vs Memcached six months ago. Redis won. You made the decision, recorded the DRR, moved on.

Now it's six months later. The Memcached team shipped a major performance update. Your Node.js version changed. The benchmark numbers you relied on? They might not be accurate anymore.

**The decision isn't necessarily wrong — it's just unverified.**

This is what FPF calls **Evidence Decay**. Every piece of evidence has a `valid_until` date. When that date passes, the evidence is "stale" and the decisions built on it become questionable.

## The Problem with Stale Evidence

Stale evidence creates hidden risk. You're operating on assumptions that haven't been re-checked. Maybe they're still true. Maybe they're not. You don't know.

Quint Code makes this visible instead of hiding it.

## Checking Your Evidence

Run `/fpf:decay` to see what's stale:

```
/fpf:decay
```

You'll get a freshness report showing which holons have expired evidence:

```
## Evidence Freshness Report

### STALE (1 holon requires action)

#### Use Redis for Caching (L2)
| Evidence ID | Type | Status | Details |
|-------------|------|--------|---------|
| ev-benchmark-2024-06-15 | validation | EXPIRED | 180 days overdue |
| ev-load-test-2024-06-20 | validation | EXPIRED | 175 days overdue |

### FRESH (3 holons)
- Use TypeScript for API (L2)
- PostgreSQL for primary storage (L2)
- JWT for auth tokens (L2)
```

## Three Ways to Handle Stale Evidence

When you see stale evidence, you have three options:

### 1. Refresh — Re-run the test

**When:** The decision is still correct, you just need fresh proof.

**How:** Run `/fpf:propose-hypotheses run only validation step` on the hypothesis to gather new evidence.

```
User: The Redis benchmark is old but Redis is still the right choice.
      Refresh the evidence.

Agent: Running validation for hypothesis-redis-caching...
       [executes benchmark]
       Evidence refreshed. Valid until 2025-06-21.
```

### 2. Deprecate — Reconsider the decision

**When:** The world has changed. The decision itself is questionable.

**How:** Tell the agent to deprecate the hypothesis. It gets downgraded one level (L2→L1 or L1→L0).

```
User: AWS announced they're deprecating this service.
      Deprecate that decision.

Agent: Deprecated: hypothesis-aws-service L2 → L1
       This decision now needs re-evaluation.
       Run /q1-hypothesize to explore alternatives.
```

### 3. Waive — Accept the risk temporarily

**When:** You know it's stale, but you're shipping Tuesday and can't re-test everything right now.

**How:** Tell the agent to waive the evidence with a deadline and reason.

```
User: We're launching next week. Waive the benchmark until January 15th,
      we have a full test cycle scheduled for the 20th.

Agent: Waiver recorded:
       - Evidence: ev-benchmark-2024-06-15
       - Waived until: 2025-01-15
       - Rationale: Launch deadline. Full test cycle Jan 20.

       Warning: Returns to EXPIRED after 2025-01-15.
```

**A waiver is not ignoring the problem.** It's explicitly documenting that you know about the risk and accept it until a specific date. The waiver goes in the audit log — who waived what, why, and until when.

## Natural Language Usage

You don't need to memorize evidence IDs or parameters. Just describe what you want.

The agent sees the freshness report and understands context. When you say "waive the benchmark until February," it finds the right evidence ID and calls the tool for you.

**These all work:**

```
"Waive everything until January 15th, we're launching"

"The load test is only 2 weeks overdue, refresh it"

"That API is being deprecated, deprecate our decision to use it"

"Waive the security audit until the 15th with rationale: re-audit scheduled"
```

If you want to be explicit, you can:

```
/fpf:decay --waive ev-benchmark-2024-06-15 --until 2025-02-01 --rationale "Migration pending"
```

But natural language works fine.

## The WLNK Principle

A holon is **STALE** if *any* of its evidence is expired (and not waived).

This is the Weakest Link (WLNK) principle. If you have three pieces of evidence and one is stale, the whole decision is questionable. You don't get to average it out.

Think of it like a chain. Three strong links and one rusted link? The chain breaks at the rust.

## Practical Workflows

### Weekly Maintenance

```
/fpf:decay                    # What's stale?
# For each item: refresh, deprecate, or waive
```

### Before a Release

```
/fpf:decay                    # Check for stale decisions
# Either refresh evidence or explicitly waive with rationale
# Waivers become part of release documentation
```

### After Major Changes

Dependency update? API change? Security advisory?

```
/fpf:decay                    # What's affected?
# Deprecate obsolete decisions
# Start new hypothesis cycle for replacements
```

## Audit Trail

All actions are logged:

| Action | What's Recorded |
|--------|----------------|
| Deprecate | from_layer, to_layer, who, when |
| Waive | evidence_id, until_date, rationale, who, when |

You can always answer: "Who waived what and why?"

