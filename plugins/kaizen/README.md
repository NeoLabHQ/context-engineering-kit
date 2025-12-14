# Kaizen Plugin

Continuous improvement framework inspired by the Toyota Production System that brings Lean manufacturing principles to software development through systematic problem analysis, root cause investigation, and iterative improvement cycles.

## Plugin Target

- Find root causes - Stop fixing symptoms; address fundamental issues
- Prevent recurrence - Understand why problems exist to prevent similar issues
- Continuous improvement - Small, incremental changes that compound into major gains
- Reduce waste - Identify and eliminate non-value-adding activities in code and processes

## Overview

The Kaizen plugin implements proven manufacturing problem-solving techniques adapted for software development. Named after the Japanese word for "continuous improvement," Kaizen philosophy emphasizes that small, ongoing positive changes can lead to major improvements over time.

The plugin is based on methodologies from the **Toyota Production System (TPS)** and **Lean manufacturing**, which have been validated across industries for over 70 years.

They are based on the idea that most bugs and quality issues are symptoms of deeper systemic problems. Fixing only the symptom leads to recurring issues; finding and addressing the root cause prevents entire classes of problems.

## Quick Start

```bash
# Install the plugin
/plugin install kaizen@NeoLabHQ/context-engineering-kit

# Investigate a bug's root cause
> /kaizen:why "API returns 500 error on checkout"

# Analyze code for improvement opportunities
> /kaizen:analyse src/checkout/

# Document a complex problem comprehensively
> /kaizen:analyse-problem "Database connection exhaustion during peak traffic"
```

[Usage Examples](./usage-examples.md)

## Commands Overview

### /kaizen:why - Five Whys Root Cause Analysis

Iterative questioning technique that drills from surface symptoms to fundamental root causes by repeatedly asking "why."

- Purpose - Find the true root cause, not just symptoms
- Output - Chain of causation leading to actionable root cause

```bash
/kaizen:why ["issue or symptom description"]
```

#### Arguments

Optional description of the issue or symptom to analyze. If not provided, you will be prompted for input.

#### How It Works

1. **State the Problem**: Clearly define the observable symptom or issue
2. **First Why**: Ask why this problem occurs; document the immediate cause
3. **Iterate**: For each answer, ask "why" again to go deeper
4. **Branch When Needed**: If multiple causes emerge, explore each branch separately
5. **Identify Root Cause**: Usually reached after 5 iterations when you hit systemic/process issues
6. **Validate**: Work backwards from root cause to symptom to verify the chain
7. **Propose Solutions**: Address root causes, not symptoms

**Depth Guidelines**

- **Stop when**: You reach process, policy, or systemic issues
- **Keep going if**: "Human error" appears (ask why error was possible)
- **Branch when**: Multiple contributing factors exist
- **Not always 5**: Stop at true root cause, whether 3 or 7 whys deep

#### Usage Examples

```bash
# Investigate a production bug
> /kaizen:why "Users see 500 error on checkout"

# Analyze a recurring issue
> /kaizen:why "E2E tests fail intermittently"

# Understand a performance problem
> /kaizen:why "Feature deployment takes 2 hours"
```

**Example Output**:
```
Problem: Users see 500 error on checkout
Why 1: Payment service throws exception
Why 2: Request timeout after 30 seconds
Why 3: Database query takes 45 seconds
Why 4: Missing index on transactions table
Why 5: Index creation wasn't in migration scripts

Root Cause: Migration review process doesn't check query performance
Solution: Add query performance checks to migration PR template
```

#### Best Practices

- Do not stop at symptoms - Keep asking "why" until you reach systemic causes
- Explore multiple branches - Complex problems often have multiple contributing factors
- Avoid blame - Focus on process and systems, not individuals
- Document everything - The chain of causation is valuable for future reference
- Test solutions - Implement, verify the symptom is resolved, then monitor for recurrence

---

### /kaizen:root-cause-tracing - Bug Tracing Through Call Stack

Systematically traces bugs backward through the call stack to identify where invalid data or incorrect behavior originates.

- Purpose - Find the source of bugs that manifest deep in execution
- Output - Trace chain from symptom to original trigger with fix recommendation

```bash
/kaizen:root-cause-tracing
```

#### Arguments

None. The command works with the current bug context from your conversation.

#### How It Works

1. **Observe Symptom**: Identify where the error appears (e.g., wrong file created, incorrect output)
2. **Find Immediate Cause**: Locate the code that directly causes the error
3. **Trace Upward**: Ask "what called this?" and follow the chain
4. **Track Values**: Note what values were passed at each level
5. **Find Origin**: Continue until you find where invalid data originated
6. **Add Instrumentation**: If manual tracing fails, add stack trace logging
7. **Fix at Source**: Address the root trigger, not the symptom location

**Key Principle**: Never fix just where the error appears. Trace back to find the original trigger.

#### Usage Examples

```bash
# After encountering a deep stack error
> /kaizen:root-cause-tracing

# When debugging file creation in wrong location
> /kaizen:root-cause-tracing
```

**Example Trace**:
```
Symptom: .git created in packages/core/ (source code)

Trace chain:
1. git init runs in process.cwd() <- empty cwd parameter
2. WorktreeManager called with empty projectDir
3. Session.create() passed empty string
4. Test accessed context.tempDir before beforeEach
5. setupCoreTest() returns { tempDir: '' } initially

Root cause: Top-level variable initialization accessing empty value
Fix: Made tempDir a getter that throws if accessed before beforeEach

Defense-in-depth added:
- Layer 1: Project.create() validates directory
- Layer 2: WorkspaceManager validates not empty
- Layer 3: NODE_ENV guard refuses git init outside tmpdir
- Layer 4: Stack trace logging before git init
```

#### Best practices

- Use console.error in tests - Loggers may be suppressed in test environments
- Log before dangerous operations - Capture state before failure, not after
- Include full context - Directory, cwd, environment variables, timestamps
- Add defense-in-depth - Fix at source AND add validation at each layer
- Capture stack traces - Use `new Error().stack` for complete call chains

---

### /kaizen:cause-and-effect - Fishbone Analysis

Systematic exploration of problem causes across six categories using the Ishikawa (Fishbone) diagram approach.

- Purpose - Comprehensive multi-factor root cause exploration
- Output - Structured analysis across People, Process, Technology, Environment, Methods, and Materials

```bash
/kaizen:cause-and-effect ["problem description"]
```

#### Arguments

Optional problem description to analyze. If not provided, you will be prompted for input.

#### How It Works

1. **State the Problem**: Define the "head" of the fish - the effect you're analyzing
2. **Explore Each Category**: Brainstorm potential causes in six domains:
   - **People**: Skills, training, communication, team dynamics
   - **Process**: Workflows, procedures, standards, reviews
   - **Technology**: Tools, infrastructure, dependencies, configuration
   - **Environment**: Workspace, deployment targets, external factors
   - **Methods**: Approaches, patterns, architectures, practices
   - **Materials**: Data, dependencies, third-party services, resources
3. **Dig Deeper**: For each potential cause, ask "why" to uncover deeper issues
4. **Identify Root Causes**: Distinguish contributing factors from fundamental causes
5. **Prioritize**: Rank causes by impact and likelihood
6. **Propose Solutions**: Address highest-priority root causes

#### Usage Examples

```bash
# Analyze performance issues
> /kaizen:cause-and-effect "API responses take 3+ seconds"

# Investigate test reliability
> /kaizen:cause-and-effect "15% of test runs fail, passing on retry"

# Understand delivery delays
> /kaizen:cause-and-effect "Feature took 12 weeks instead of 3"
```

**Example Output**:
```
Problem: API responses take 3+ seconds (target: <500ms)

PEOPLE
├─ Team unfamiliar with performance optimization
├─ No one owns performance monitoring
└─ Frontend team doesn't understand backend constraints

PROCESS
├─ No performance testing in CI/CD
├─ No SLA defined for response times
└─ Performance regression not caught in code review

TECHNOLOGY
├─ Database queries not optimized
│  └─ Why: No query analysis tools in place
├─ N+1 queries in ORM
│  └─ Why: Eager loading not configured
└─ No caching layer

ROOT CAUSES:
- No performance requirements defined (Process)
- Missing performance monitoring tooling (Technology)
- Architecture doesn't support caching/async (Methods)

SOLUTIONS (Priority Order):
1. Add database indexes (quick win, high impact)
2. Implement Redis caching layer (medium effort, high impact)
3. Define and monitor performance SLAs (low effort, prevents regression)
```

#### Best practices

- Do not stop at first cause - Explore deeply within each category
- Look for cross-category connections - Some causes span multiple domains
- Root causes usually involve process or methods - Not just technology
- Combine with /kaizen:why - Use Five Whys to dig deeper on specific causes
- Prioritize by impact x feasibility / effort - Focus on highest-value fixes

---

### /kaizen:analyse-problem - A3 Problem Analysis

Comprehensive one-page problem documentation using the A3 format, covering Background, Current Condition, Goal, Root Cause, Countermeasures, Implementation Plan, and Follow-up.

- Purpose - Complete problem documentation for significant issues
- Output - Structured A3 report with actionable implementation plan

```bash
/kaizen:analyse-problem ["problem description"]
```

#### Arguments

Optional problem description to document. If not provided, you will be prompted for input.

#### How It Works

1. **Background**: Why this problem matters (context, business impact, urgency)
2. **Current Condition**: What's happening now (data, metrics, examples - facts, not opinions)
3. **Goal/Target**: What success looks like (specific, measurable, time-bound)
4. **Root Cause Analysis**: Why the problem exists (using Five Whys or Fishbone)
5. **Countermeasures**: Proposed solutions that address root causes (not symptoms)
6. **Implementation Plan**: Who, what, when, how (timeline, responsibilities, dependencies)
7. **Follow-up**: How to verify success and prevent recurrence (metrics, monitoring, review dates)

**Named after A3 paper size**, this format forces concise, complete thinking that fits on one page.

#### Usage Examples

```bash
# Document a production incident
> /kaizen:analyse-problem "API downtime due to connection pool exhaustion"

# Analyze a security vulnerability
> /kaizen:analyse-problem "Critical SQL injection vulnerability discovered"

# Plan a major improvement initiative
> /kaizen:analyse-problem "CI/CD pipeline takes 45 minutes"
```

**Example Output Structure**:
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

#### Best Practices

- Use for significant issues - A3 is overkill for small bugs or one-line fixes
- Stick to facts - Current Condition should have data, not opinions
- Countermeasures address root causes - Not just symptoms
- Clear ownership - Every action item needs an owner and deadline
- Living document - Update as situation evolves until problem is closed
- Historical record - A3s become organizational learning artifacts

---

### /kaizen:analyse - Smart Analysis Method Selection

Intelligently selects and applies the most appropriate Kaizen analysis technique based on what you're analyzing: Gemba Walk, Value Stream Mapping, or Muda (Waste) Analysis.

- Purpose - Auto-select best analysis method for your target
- Output - Detailed analysis using the most appropriate technique

```bash
/kaizen:analyse ["target description"]
```

#### Arguments

Optional target description (e.g., code area, workflow, or inefficiencies to investigate). You can override auto-selection with METHOD variable.

#### How It Works

**Method Selection Logic**:

| Method | Use When Analyzing |
|--------|-------------------|
| **Gemba Walk** | Code implementation, gap between docs and reality, unfamiliar codebase areas |
| **Value Stream Mapping** | Workflows, CI/CD pipelines, bottlenecks, handoffs between teams |
| **Muda (Waste)** | Code quality, technical debt, over-engineering, resource utilization |

**Gemba Walk** ("Go and see"):
1. Define scope of code to explore
2. State assumptions about how it works
3. Read actual code and observe reality
4. Document: entry points, data flow, surprises, hidden dependencies
5. Identify gaps between documentation and implementation
6. Recommend: update docs, refactor, or accept as-is

**Value Stream Mapping**:
1. Identify process start and end points
2. Map all steps including wait/handoff time
3. Measure processing time vs. waiting time for each step
4. Calculate efficiency (value-add time / total time)
5. Identify bottlenecks and waste
6. Design future state with optimizations

**Muda (Waste) Analysis** - Seven types of waste in software:
1. **Overproduction**: Features no one uses, premature optimization
2. **Waiting**: Build time, code review delays, blocked dependencies
3. **Transportation**: Unnecessary data transformations, API layers with no value
4. **Over-processing**: Excessive logging, redundant validations
5. **Inventory**: Unmerged branches, half-finished features, untriaged bugs
6. **Motion**: Context switching, manual deployments, repetitive tasks
7. **Defects**: Production bugs, technical debt, flaky tests

#### Usage Examples

```bash
# Explore unfamiliar code
> /kaizen:analyse authentication implementation

# Optimize a workflow
> /kaizen:analyse deployment pipeline

# Find waste in codebase
> /kaizen:analyse codebase for inefficiencies
```

#### Best Practices

- Start with Gemba Walk when unfamiliar - Understand reality before optimizing
- Use VSM for process improvements - CI/CD, deployment, code review workflows
- Use Muda for efficiency audits - Technical debt, cleanup initiatives
- Combine methods - Gemba Walk can lead to Muda analysis findings
- Document findings - Use /kaizen:analyse-problem for comprehensive documentation

---

### /kaizen:plan-do-check-act - PDCA Improvement Cycle

Four-phase iterative cycle for continuous improvement through systematic experimentation: Plan, Do, Check, Act.

- Purpose - Structured approach to measured, sustainable improvements
- Output - PDCA cycle documentation with baseline, hypothesis, results, and next steps

```bash
/kaizen:plan-do-check-act ["improvement goal"]
```

#### Arguments

Optional improvement goal or problem to address. If not provided, you will be prompted for input.

#### How It Works

**Phase 1: PLAN**
1. Define the problem or improvement goal
2. Analyze current state (baseline metrics)
3. Identify root causes (use /kaizen:why or /kaizen:cause-and-effect)
4. Develop hypothesis: "If we change X, Y will improve"
5. Design experiment: what to change, how to measure
6. Set success criteria (measurable targets)

**Phase 2: DO**
1. Implement the planned change (small scale first)
2. Document what was actually done
3. Record any deviations from plan
4. Collect data throughout implementation
5. Note unexpected observations

**Phase 3: CHECK**
1. Measure results against success criteria
2. Compare to baseline (before vs. after)
3. Analyze: did hypothesis hold?
4. Identify what worked and what did not
5. Document learnings

**Phase 4: ACT**
- **If successful**: Standardize the change, update docs, train team, monitor
- **If unsuccessful**: Learn why, refine hypothesis, start new cycle
- **If partially successful**: Standardize what worked, plan next cycle for remainder

#### Usage Examples

```bash
# Reduce build time
> /kaizen:plan-do-check-act "Reduce Docker build from 45min to under 10min"

# Improve code quality
> /kaizen:plan-do-check-act "Reduce production bugs from 8 to 4 per month"

# Speed up code review
> /kaizen:plan-do-check-act "Reduce PR merge time from 3 days to 1 day"
```

**Example Cycle**:
```
CYCLE 1
───────
PLAN:
  Problem: Docker build takes 45 minutes
  Current State: Full rebuild every time, no layer caching
  Root Cause: Package manager cache not preserved between builds
  Hypothesis: Caching dependencies will reduce build to <10 minutes
  Success Criteria: Build time <10 minutes on unchanged dependencies

DO:
  - Restructured Dockerfile: COPY package*.json before src files
  - Added .dockerignore for node_modules
  - Configured CI cache for Docker layers

CHECK:
  Results:
    - Unchanged dependencies: 8 minutes (was 45)
    - Changed dependencies: 12 minutes (was 45)
  Analysis: 82% reduction on cached builds, hypothesis confirmed

ACT:
  Standardize:
    ✓ Merged Dockerfile changes
    ✓ Updated CI pipeline config
    ✓ Documented in README

  New Problem: 12 minutes still slow when deps change
  → Start CYCLE 2
```

#### Best Practices

- Start small - Make measurable changes, not big overhauls
- Expect multiple cycles - PDCA is iterative; 2-3 cycles is normal
- Failed experiments are learning - Document why and adjust hypothesis
- Success criteria must be measurable - "Faster" is not a criteria; "<10 minutes" is
- Standardize successes - Document and train team on what works
- If stuck after 3 cycles - Revisit root cause analysis


## Skills Overview

### kaizen - Continuous Improvement Skill

Automatically applied skill guiding continuous improvement mindset, error-proofing, standardized work, and just-in-time principles.

#### The Four Pillars of Kaizen

The Kaizen plugin also includes a skill that applies continuous improvement principles automatically during development:

1. Continuous Improvement - Small, frequent improvements compound into major gains. Always leave code better than you found it.
2. Poka-Yoke (Error Proofing) - Design systems that prevent errors at compile/design time, not runtime. Make invalid states unrepresentable.
3. Standardized Work - Follow established patterns. Document what works. Make good practices easy to follow.
4. Just-In-Time (JIT) - Build what's needed now. No "just in case" features. Avoid premature optimization.

---

## Foundation

The Kaizen plugin is based on methodologies with over 70 years of real-world validation in manufacturing, now adapted for software development:

### Toyota Production System (TPS)

The foundation of Lean manufacturing, developed at Toyota starting in the 1940s:

- **[The Toyota Way](https://en.wikipedia.org/wiki/The_Toyota_Way)** - 14 principles of continuous improvement and respect for people
- **[Toyota Kata](https://en.wikipedia.org/wiki/Toyota_Kata)** - Scientific thinking routines for improvement (PDCA)
- **Proven Results**: Toyota achieved highest quality ratings while reducing production costs by 50%+

### Lean Manufacturing Principles

- **[Kaizen](https://en.wikipedia.org/wiki/Kaizen)** - Philosophy of continuous improvement through small, incremental changes
- **[Muda (Waste)](https://en.wikipedia.org/wiki/Muda_(Japanese_term))** - Seven types of waste to eliminate
- **[Value Stream Mapping](https://en.wikipedia.org/wiki/Value-stream_mapping)** - Visualizing process flow to identify improvement opportunities
- **Industry Impact**: Lean principles have spread to healthcare, software, services, achieving **20-50% efficiency improvements**

### Problem-Solving Techniques

- **[Five Whys](https://en.wikipedia.org/wiki/Five_whys)** - Developed by Sakichi Toyoda, founder of Toyota Industries
- **[Ishikawa (Fishbone) Diagram](https://en.wikipedia.org/wiki/Ishikawa_diagram)** - Created by Kaoru Ishikawa for quality management
- **[A3 Problem Solving](https://en.wikipedia.org/wiki/A3_problem_solving)** - Toyota's structured approach to problem documentation
- **[PDCA Cycle](https://en.wikipedia.org/wiki/PDCA)** - Deming cycle for iterative improvement
