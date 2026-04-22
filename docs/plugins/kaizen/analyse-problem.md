# /analyse-problem - A3 Problem Analysis

Comprehensive one-page problem documentation using the A3 format, covering Background, Current Condition, Goal, Root Cause, Countermeasures, Implementation Plan, and Follow-up.

- Purpose - Complete problem documentation for significant issues
- Output - Structured A3 report with actionable implementation plan

```bash
/analyse-problem ["problem description"]
```

## Arguments

Optional problem description to document. If not provided, you will be prompted for input.

## How It Works

1. **Background**: Why this problem matters (context, business impact, urgency)
2. **Current Condition**: What's happening now (data, metrics, examples - facts, not opinions)
3. **Goal/Target**: What success looks like (specific, measurable, time-bound)
4. **Root Cause Analysis**: Why the problem exists (using Five Whys or Fishbone)
5. **Countermeasures**: Proposed solutions that address root causes (not symptoms)
6. **Implementation Plan**: Who, what, when, how (timeline, responsibilities, dependencies)
7. **Follow-up**: How to verify success and prevent recurrence (metrics, monitoring, review dates)

### Named after A3 paper size

This format forces concise, complete thinking that fits on one page.

## Usage Examples

```bash
# Document a production incident
> /analyse-problem "API downtime due to connection pool exhaustion"

# Analyze a security vulnerability
> /analyse-problem "Critical SQL injection vulnerability discovered"

# Plan a major improvement initiative
> /analyse-problem "CI/CD pipeline takes 45 minutes"
```

### Example Output Structure

```
═══════════════════════════════════════════════════════════════
                    A3 PROBLEM ANALYSIS
═══════════════════════════════════════════════════════════════

TITLE: API Downtime Due to Connection Pool Exhaustion
OWNER: Backend Team Lead
DATE: 2024-11-14

1. BACKGROUND
• API goes down 2-3x per week during peak hours
• Affects 10,000+ users, average 15min downtime
• Revenue impact: ~$5K per incident

2. CURRENT CONDITION
• Connection pool size: 10 (unchanged since launch)
• Peak concurrent users: 500 (was 300 three weeks ago)
• Connections leaked: ~2 per hour (never released)

3. GOAL/TARGET
• Zero downtime due to connection exhaustion
• Support 1000 concurrent users (2x current peak)
• Achieve within 1 week

4. ROOT CAUSE ANALYSIS (5 Whys)
Problem: Connection pool exhausted
Why 1: All connections in use, none available
Why 2: Connections not released after requests
Why 3: Error handling doesn't close connections
Why 4: Try-catch blocks missing .finally()
Why 5: No code review checklist for resource cleanup

5. COUNTERMEASURES
Immediate: Audit all DB code, add .finally() for cleanup
Short-term: Increase pool size, add monitoring
Long-term: Migrate to connection pool library with auto-release

6. IMPLEMENTATION PLAN
Week 1: Fix leaks, increase pool, add monitoring
Week 2: Optimize slow queries, create best practices doc
Week 3-4: Evaluate and migrate to better pool library

7. FOLLOW-UP
• Success Metrics: Zero incidents for 4 weeks
• Monitoring: Daily pool usage dashboard
• Review Dates: Weekly check-ins until resolved
═══════════════════════════════════════════════════════════════
```

## Best Practices

- Use for significant issues - A3 is overkill for small bugs or one-line fixes
- Stick to facts - Current Condition should have data, not opinions
- Countermeasures address root causes - Not just symptoms
- Clear ownership - Every action item needs an owner and deadline
- Living document - Update as situation evolves until problem is closed
- Historical record - A3s become organizational learning artifacts
