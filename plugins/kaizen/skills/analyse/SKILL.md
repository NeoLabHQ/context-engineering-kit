---
description: Auto-selects best Kaizen method (Gemba Walk, Value Stream, or Muda) for target
argument-hint: Optional target description (e.g., code, workflow, or inefficiencies)
---

# Smart Analysis

Intelligently select and apply the most appropriate Kaizen analysis technique based on what you're analyzing.

## Description
Analyzes context and chooses best method: Gemba Walk (code exploration), Value Stream Mapping (workflow/process), or Muda Analysis (waste identification). Guides you through the selected technique.

## Usage
`/analyse [target_description]`

Examples:
- `/analyse authentication implementation`
- `/analyse deployment workflow`
- `/analyse codebase for inefficiencies`

## Variables
- TARGET: What to analyze (default: prompt for input)
- METHOD: Override auto-selection (gemba, vsm, muda)

## Method Selection Logic

**Gemba Walk** → When analyzing:
- Code implementation (how feature actually works)
- Gap between documentation and reality
- Understanding unfamiliar codebase areas
- Actual vs. assumed architecture

**Value Stream Mapping** → When analyzing:
- Workflows and processes (CI/CD, deployment, development)
- Bottlenecks in multi-stage pipelines
- Handoffs between teams/systems
- Time spent in each process stage

**Muda (Waste Analysis)** → When analyzing:
- Code quality and efficiency
- Technical debt
- Over-engineering or duplication
- Resource utilization

## Steps
1. Understand what's being analyzed
2. Determine best method (or use specified method)
3. Explain why this method fits
4. Guide through the analysis
5. Present findings with actionable insights

---

## Method 1: Gemba Walk

"Go and see" the actual code to understand reality vs. assumptions.

### When to Use
- Understanding how feature actually works
- Code archaeology (legacy systems)
- Finding gaps between docs and implementation
- Exploring unfamiliar areas before changes

### Process
1. **Define scope**: What code area to explore
2. **State assumptions**: What you think it does
3. **Observe reality**: Read actual code
4. **Document findings**: 
   - Entry points
   - Actual data flow
   - Surprises (differs from assumptions)
   - Hidden dependencies
   - Undocumented behavior
5. **Identify gaps**: Documentation vs. reality
6. **Recommend**: Update docs, refactor, or accept

### Example: Authentication System Gemba Walk

```
SCOPE: User authentication flow

ASSUMPTIONS (Before):
• JWT tokens stored in localStorage
• Single sign-on via OAuth only
• Session expires after 1 hour
• Password reset via email link

GEMBA OBSERVATIONS (Actual Code):

Entry Point: /api/auth/login (routes/auth.ts:45)
├─> AuthService.authenticate() (services/auth.ts:120)
├─> UserRepository.findByEmail() (db/users.ts:67)
├─> bcrypt.compare() (services/auth.ts:145)
└─> TokenService.generate() (services/token.ts:34)

Actual Flow:
1. Login credentials → POST /api/auth/login
2. Password hashed with bcrypt (10 rounds)
3. JWT generated with 24hr expiry (NOT 1 hour!)
4. Token stored in httpOnly cookie (NOT localStorage)
5. Refresh token in separate cookie (15 days)
6. Session data in Redis (30 days TTL)

SURPRISES:
✗ OAuth not implemented (commented out code found)
✗ Password reset is manual (admin intervention)
✗ Three different session storage mechanisms:
  - Redis for session data
  - Database for "remember me"
  - Cookies for tokens
✗ Legacy endpoint /auth/legacy still active (no auth!)
✗ Admin users bypass rate limiting (security issue)

GAPS:
• Documentation says OAuth, code doesn't have it
• Session expiry inconsistent (docs: 1hr, code: 24hr)
• Legacy endpoint not documented (security risk)
• No mention of "remember me" in docs

RECOMMENDATIONS:
1. HIGH: Secure or remove /auth/legacy endpoint
2. HIGH: Document actual session expiry (24hr)
3. MEDIUM: Clean up or implement OAuth
4. MEDIUM: Consolidate session storage (choose one)
5. LOW: Add rate limiting for admin users
```

### Example: CI/CD Pipeline Gemba Walk

```
SCOPE: Build and deployment pipeline

ASSUMPTIONS:
• Automated tests run on every commit
• Deploy to staging automatic
• Production deploy requires approval

GEMBA OBSERVATIONS:

Actual Pipeline (.github/workflows/main.yml):
1. On push to main:
   ├─> Lint (2 min)
   ├─> Unit tests (5 min) [SKIPPED if "[skip-tests]" in commit]
   ├─> Build Docker image (15 min)
   └─> Deploy to staging (3 min)

2. Manual trigger for production:
   ├─> Run integration tests (20 min) [ONLY for production!]
   ├─> Security scan (10 min)
   └─> Deploy to production (5 min)

SURPRISES:
✗ Unit tests can be skipped with commit message flag
✗ Integration tests ONLY run for production deploy
✗ Staging deployed without integration tests
✗ No rollback mechanism (manual kubectl commands)
✗ Secrets loaded from .env file (not secrets manager)
✗ Old "hotfix" branch bypasses all checks

GAPS:
• Staging and production have different test coverage
• Documentation doesn't mention test skip flag
• Rollback process not documented or automated
• Security scan results not enforced (warning only)

RECOMMENDATIONS:
1. CRITICAL: Remove test skip flag capability
2. CRITICAL: Migrate secrets to secrets manager
3. HIGH: Run integration tests on staging too
4. HIGH: Delete or secure hotfix branch
5. MEDIUM: Add automated rollback capability
6. MEDIUM: Make security scan blocking
```

---

## Method 2: Value Stream Mapping

Map workflow stages, measure time/waste, identify bottlenecks.

### When to Use
- Process optimization (CI/CD, deployment, code review)
- Understanding multi-stage workflows
- Finding delays and handoffs
- Improving cycle time

### Process
1. **Identify start and end**: Where process begins and ends
2. **Map all steps**: Including waiting/handoff time
3. **Measure each step**:
   - Processing time (work happening)
   - Waiting time (idle, blocked)
   - Who/what performs step
4. **Calculate metrics**:
   - Total lead time
   - Value-add time vs. waste time
   - % efficiency (value-add / total time)
5. **Identify bottlenecks**: Longest steps, most waiting
6. **Design future state**: Optimized flow
7. **Plan improvements**: How to achieve future state

### Example: Feature Development Value Stream Map

```
CURRENT STATE: Feature request → Production

Step 1: Requirements Gathering
├─ Processing: 2 days (meetings, writing spec)
├─ Waiting: 3 days (stakeholder review)
└─ Owner: Product Manager

Step 2: Design
├─ Processing: 1 day (mockups, architecture)
├─ Waiting: 2 days (design review, feedback)
└─ Owner: Designer + Architect

Step 3: Development
├─ Processing: 5 days (coding)
├─ Waiting: 2 days (PR review queue)
└─ Owner: Developer

Step 4: Code Review
├─ Processing: 0.5 days (review)
├─ Waiting: 1 day (back-and-forth changes)
└─ Owner: Senior Developer

Step 5: QA Testing
├─ Processing: 2 days (manual testing)
├─ Waiting: 1 day (bug fixes, retest)
└─ Owner: QA Engineer

Step 6: Staging Deployment
├─ Processing: 0.5 days (deploy, smoke test)
├─ Waiting: 2 days (stakeholder UAT)
└─ Owner: DevOps

Step 7: Production Deployment
├─ Processing: 0.5 days (deploy, monitor)
├─ Waiting: 0 days
└─ Owner: DevOps

───────────────────────────────────────
METRICS:
Total Lead Time: 22.5 days
Value-Add Time: 11.5 days (work)
Waste Time: 11 days (waiting)
Efficiency: 51%

BOTTLENECKS:
1. Requirements review wait (3 days)
2. Development time (5 days)
3. Stakeholder UAT wait (2 days)
4. PR review queue (2 days)

WASTE ANALYSIS:
• Waiting for reviews/approvals: 9 days (82% of waste)
• Rework due to unclear requirements: ~1 day
• Manual testing time: 2 days

FUTURE STATE DESIGN:

Changes:
1. Async requirements approval (stakeholders have 24hr SLA)
2. Split large features into smaller increments
3. Automated testing replaces manual QA
4. PR review SLA: 4 hours max
5. Continuous deployment to staging (no approval)
6. Feature flags for production rollout (no wait)

Projected Future State:
Total Lead Time: 9 days (60% reduction)
Value-Add Time: 8 days
Waste Time: 1 day
Efficiency: 89%

IMPLEMENTATION PLAN:
Week 1: Set review SLAs, add feature flags
Week 2: Automate test suite
Week 3: Enable continuous staging deployment
Week 4: Train team on incremental delivery
```

### Example: Incident Response Value Stream Map

```
CURRENT STATE: Incident detected → Resolution

Step 1: Detection
├─ Processing: 0 min (automated alert)
├─ Waiting: 15 min (until someone sees alert)
└─ System: Monitoring tool

Step 2: Triage
├─ Processing: 10 min (assess severity)
├─ Waiting: 20 min (find right person)
└─ Owner: On-call engineer

Step 3: Investigation
├─ Processing: 45 min (logs, debugging)
├─ Waiting: 30 min (access to production, gather context)
└─ Owner: Engineer + SRE

Step 4: Fix Development
├─ Processing: 60 min (write fix)
├─ Waiting: 15 min (code review)
└─ Owner: Engineer

Step 5: Deployment
├─ Processing: 10 min (hotfix deploy)
├─ Waiting: 5 min (verification)
└─ Owner: SRE

Step 6: Post-Incident
├─ Processing: 20 min (update status, notify)
├─ Waiting: 0 min
└─ Owner: Engineer

───────────────────────────────────────
METRICS:
Total Lead Time: 230 min (3h 50min)
Value-Add Time: 145 min
Waste Time: 85 min (37%)

BOTTLENECKS:
1. Finding right person (20 min)
2. Gaining production access (30 min)
3. Investigation time (45 min)

IMPROVEMENTS:
1. Slack integration for alerts (reduce detection wait)
2. Auto-assign by service owner (no hunt for person)
3. Pre-approved prod access for on-call (reduce wait)
4. Runbooks for common incidents (faster investigation)
5. Automated rollback for deployment incidents

Projected improvement: 230min → 120min (48% faster)
```

---

## Method 3: Muda (Waste Analysis)

Identify seven types of waste in code and development processes.

### When to Use
- Code quality audits
- Technical debt assessment
- Process efficiency improvements
- Identifying over-engineering

### The 7 Types of Waste (Applied to Software)

**1. Overproduction**: Building more than needed
- Features no one uses
- Overly complex solutions
- Premature optimization
- Unnecessary abstractions

**2. Waiting**: Idle time
- Build/test/deploy time
- Code review delays
- Waiting for dependencies
- Blocked by other teams

**3. Transportation**: Moving things around
- Unnecessary data transformations
- API layers with no value add
- Copying data between systems
- Repeated serialization/deserialization

**4. Over-processing**: Doing more than necessary
- Excessive logging
- Redundant validations
- Over-normalized databases
- Unnecessary computation

**5. Inventory**: Work in progress
- Unmerged branches
- Half-finished features
- Untriaged bugs
- Undeployed code

**6. Motion**: Unnecessary movement
- Context switching
- Meetings without purpose
- Manual deployments
- Repetitive tasks

**7. Defects**: Rework and bugs
- Production bugs
- Technical debt
- Flaky tests
- Incomplete features

### Process
1. **Define scope**: Codebase area or process
2. **Examine for each waste type**
3. **Quantify impact** (time, complexity, cost)
4. **Prioritize by impact**
5. **Propose elimination strategies**

### Example: API Codebase Waste Analysis

```
SCOPE: REST API backend (50K LOC)

1. OVERPRODUCTION
   Found:
   • 15 API endpoints with zero usage (last 90 days)
   • Generic "framework" built for "future flexibility" (unused)
   • Premature microservices split (2 services, could be 1)
   • Feature flags for 12 features (10 fully rolled out, flags kept)
   
   Impact: 8K LOC maintained for no reason
   Recommendation: Delete unused endpoints, remove stale flags

2. WAITING
   Found:
   • CI pipeline: 45 min (slow Docker builds)
   • PR review time: avg 2 days
   • Deployment to staging: manual, takes 1 hour
   
   Impact: 2.5 days wasted per feature
   Recommendation: Cache Docker layers, PR review SLA, automate staging

3. TRANSPORTATION
   Found:
   • Data transformed 4 times between DB and API response:
     DB → ORM → Service → DTO → Serializer
   • Request/response logged 3 times (middleware, handler, service)
   • Files uploaded → S3 → CloudFront → Local cache (unnecessary)
   
   Impact: 200ms avg response time overhead
   Recommendation: Reduce transformation layers, consolidate logging

4. OVER-PROCESSING
   Found:
   • Every request validates auth token (even cached)
   • Database queries fetch all columns (SELECT *)
   • JSON responses include full object graphs (nested 5 levels)
   • Logs every database query in production (verbose)
   
   Impact: 40% higher database load, 3x log storage
   Recommendation: Cache auth checks, selective fields, trim responses

5. INVENTORY
   Found:
   • 23 open PRs (8 abandoned, 6+ months old)
   • 5 feature branches unmerged (completed but not deployed)
   • 147 open bugs (42 duplicates, 60 not reproducible)
   • 12 hotfix commits not backported to main
   
   Impact: Context overhead, merge conflicts, lost work
   Recommendation: Close stale PRs, bug triage, deploy pending features

6. MOTION
   Found:
   • Developers switch between 4 tools for one deployment
   • Manual database migrations (error-prone, slow)
   • Environment config spread across 6 files
   • Copy-paste secrets to .env files
   
   Impact: 30min per deployment, frequent mistakes
   Recommendation: Unified deployment tool, automate migrations

7. DEFECTS
   Found:
   • 12 production bugs per month
   • 15% flaky test rate (wasted retry time)
   • Technical debt in auth module (refactor needed)
   • Incomplete error handling (crashes instead of graceful)
   
   Impact: Customer complaints, rework, downtime
   Recommendation: Stabilize tests, refactor auth, add error boundaries

───────────────────────────────────────
SUMMARY

Total Waste Identified:
• Code: 8K LOC doing nothing
• Time: 2.5 days per feature
• Performance: 200ms overhead per request
• Effort: 30min per deployment

Priority Fixes (by impact):
1. HIGH: Automate deployments (reduces Motion + Waiting)
2. HIGH: Fix flaky tests (reduces Defects)
3. MEDIUM: Remove unused code (reduces Overproduction)
4. MEDIUM: Optimize data transformations (reduces Transportation)
5. LOW: Triage bug backlog (reduces Inventory)

Estimated Recovery:
• 20% faster feature delivery
• 50% fewer production issues
• 30% less operational overhead
```

---

## Notes
- Method selection is contextual—choose what fits best
- Can combine methods (Gemba Walk → Muda Analysis)
- Start with Gemba Walk when unfamiliar with area
- Use VSM for process optimization
- Use Muda for efficiency and cleanup
- All methods should lead to actionable improvements
- Document findings for organizational learning
- Consider using `/analyse-problem` (A3) for comprehensive documentation of findings

