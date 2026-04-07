# Kaizen Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the Kaizen plugin for root cause analysis, problem solving, and continuous improvement.

## Examples

### Production Bug Investigation

**Scenario**: Users report 500 errors on the checkout page during peak hours.

```bash
# Start with Five Whys to find root cause
> /why "Users see 500 error on checkout during peak hours"
```

**Expected Flow**:

1. Kaizen asks "why" iteratively
2. Documents each level of causation
3. Branches if multiple causes emerge
4. Stops at systemic root cause
5. Proposes solutions addressing the root

**Example Five Whys Output**:
```
Problem: Users see 500 error on checkout during peak hours

Why 1: Payment service throws exception
Why 2: Request timeout after 30 seconds
Why 3: Database query takes 45 seconds during peak load
Why 4: Missing index on transactions table for user_id lookup
Why 5: Database migrations don't have performance validation in CI

Root Cause: No automated performance testing for database changes
Contributing Factor: Transactions table grew 10x, exposing the issue

Solutions:
1. IMMEDIATE: Add index on transactions.user_id
2. SHORT-TERM: Add query performance tests to CI for migrations
3. LONG-TERM: Set up database query monitoring and alerting
```

**Next Steps**:
```bash
# Implement the fix
> claude "Add index on transactions.user_id and update migration"

# Memorize the pattern for future reference
> /reflexion:memorize "Database performance patterns"
```

---

### Investigating Flaky Tests

**Scenario**: E2E tests fail 15% of the time, passing on retry.

```bash
# Use Fishbone analysis for multi-factor investigation
> /cause-and-effect "E2E tests fail intermittently, pass on retry"
```

**Expected Fishbone Output**:
```
Problem: 15% of E2E test runs fail, passing on retry

PEOPLE
├─ Test-writing skills vary across team
├─ New developers copy existing flaky patterns
└─ No one assigned to fix flaky tests

PROCESS
├─ Flaky tests marked as "known issue" and ignored
├─ No policy against merging with flaky tests
└─ Test failures don't block deployments

TECHNOLOGY
├─ Race conditions in async test setup
│  └─ Why: setTimeout used instead of proper waiting
├─ Tests share global state
│  └─ Why: Test database not isolated per test
├─ CI environment inconsistent
│  └─ Why: Different CPU/memory allocation

ENVIRONMENT
├─ CI runner under heavy load during business hours
├─ Network timing varies for external API mocks
└─ Timezone differences between local and CI

METHODS
├─ Integration tests not properly isolated
├─ No retry logic for legitimate timing issues
└─ Tests depend on execution order

ROOT CAUSES:
1. No test isolation strategy (Methods + Technology)
2. Process accepts flaky tests (Process)
3. Async timing not handled properly (Technology)

SOLUTIONS (Priority Order):
1. Implement per-test database isolation (high impact)
2. Replace setTimeout with proper async/await patterns
3. Add pre-commit hook blocking flaky test patterns
4. Enforce policy: flaky test = block merge
```

**Follow-up with PDCA**:
```bash
# Plan systematic improvement
> /plan-do-check-act "Reduce flaky test rate from 15% to under 2%"
```

---

### Comprehensive Incident Documentation

**Scenario**: Production database went down, need formal documentation for post-mortem.

```bash
# Create comprehensive A3 problem analysis
> /analyse-problem "Production database outage during peak traffic"
```

**Expected A3 Output**:
```
═══════════════════════════════════════════════════════════════
                    A3 PROBLEM ANALYSIS
═══════════════════════════════════════════════════════════════

TITLE: Production Database Outage Due to Connection Pool Exhaustion
OWNER: Backend Team Lead
DATE: 2024-11-14

┌─────────────────────────────────────────────────────────────┐
│ 1. BACKGROUND                                                │
├─────────────────────────────────────────────────────────────┤
│ • Database went down during peak hours (2pm-4pm)            │
│ • Complete API unavailability for 45 minutes                │
│ • Affected 15,000 active users                              │
│ • Revenue impact: ~$12K                                     │
│ • Customer satisfaction score dropped from 4.5 to 3.2       │
│ • Third incident this month with same symptoms              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. CURRENT CONDITION                                         │
├─────────────────────────────────────────────────────────────┤
│ Observations:                                                │
│ • Connection pool size: 10 (unchanged since launch)         │
│ • Peak concurrent users: 500 (was 200 at launch)            │
│ • Connections leaked: ~3 per hour (never released)          │
│ • Error logs: "Connection pool exhausted"                   │
│ • Recovery required full application restart                │
│                                                              │
│ Timeline:                                                    │
│ • 14:05 - First connection errors in logs                   │
│ • 14:15 - Alert triggered (>80% pool usage)                 │
│ • 14:20 - On-call engineer notified                         │
│ • 14:35 - Root cause identified                             │
│ • 14:50 - Application restarted, service restored           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 3. GOAL/TARGET                                               │
├─────────────────────────────────────────────────────────────┤
│ • Zero connection pool exhaustion incidents                 │
│ • Support 1000 concurrent users without degradation         │
│ • All connections released within 5 seconds of request end  │
│ • Time to recovery: <5 minutes (from 45 minutes)            │
│ • Achieve within 2 weeks                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 4. ROOT CAUSE ANALYSIS                                       │
├─────────────────────────────────────────────────────────────┤
│ 5 Whys:                                                      │
│ Problem: Connection pool exhausted                          │
│ Why 1: All 10 connections in use, none available            │
│ Why 2: Connections not released after requests              │
│ Why 3: Error handling code doesn't close connections        │
│ Why 4: Try-catch blocks missing .finally() cleanup          │
│ Why 5: No code review checklist for resource management     │
│                                                              │
│ Contributing factors:                                        │
│ • Pool size never scaled with user growth                   │
│ • No connection timeout configured                          │
│ • No monitoring on pool metrics until too late              │
│                                                              │
│ ROOT CAUSE: Systematic lack of resource cleanup in code     │
│             + No pool sizing review as system scaled        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 5. COUNTERMEASURES                                           │
├─────────────────────────────────────────────────────────────┤
│ Immediate (This Week):                                       │
│ 1. Audit all DB code, add .finally() for connection release │
│ 2. Increase pool size: 10 → 50                              │
│ 3. Add connection timeout: 10 seconds                       │
│ 4. Add pool monitoring dashboard and alerts                 │
│                                                              │
│ Short-term (Week 2):                                         │
│ 5. Create code review checklist for resource management     │
│ 6. Add automated test for connection leaks                  │
│ 7. Document connection handling best practices              │
│                                                              │
│ Long-term (Month 1):                                         │
│ 8. Migrate to connection pool library with auto-release     │
│ 9. Add linter rule detecting missing .finally()             │
│ 10. Quarterly capacity planning reviews                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 6. IMPLEMENTATION PLAN                                       │
├─────────────────────────────────────────────────────────────┤
│ Week 1 (Nov 14-18):                                          │
│ • Day 1: Audit & fix connection leaks [Dev Team]            │
│ • Day 2: Increase pool size, add timeout [DevOps]           │
│ • Day 3: Set up monitoring dashboard [SRE]                  │
│ • Day 4: Test under load [QA]                               │
│ • Day 5: Deploy to production [DevOps]                      │
│                                                              │
│ Week 2 (Nov 21-25):                                          │
│ • Create PR checklist [Tech Lead]                           │
│ • Write leak detection tests [QA Team]                      │
│ • Document best practices [Dev Lead]                        │
│                                                              │
│ Dependencies: None blocking Week 1 fixes                     │
│ Resources: 2 developers, 1 DevOps, 1 SRE                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 7. FOLLOW-UP                                                 │
├─────────────────────────────────────────────────────────────┤
│ Success Metrics:                                             │
│ • Zero pool exhaustion incidents (monitor 4 weeks)          │
│ • Pool usage stays <70% during peak                         │
│ • No connection leaks detected in monitoring                │
│                                                              │
│ Monitoring:                                                  │
│ • Real-time: Pool usage dashboard                           │
│ • Daily: Connection leak alerts                             │
│ • Weekly: Team retrospective on progress                    │
│                                                              │
│ Review Dates:                                                │
│ • Nov 18: Verify immediate fixes effective                  │
│ • Nov 25: Review short-term measures                        │
│ • Dec 9: Final review, close A3                             │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
```

---

### Performance Optimization with PDCA

**Scenario**: Docker builds take 45 minutes, slowing down the team.

```bash
# Start PDCA cycle for measured improvement
> /plan-do-check-act "Reduce Docker build time from 45 minutes to under 10 minutes"
```

**Expected PDCA Cycle**:
```
CYCLE 1
───────
PLAN:
  Problem: Docker build takes 45 minutes
  Current State: Full rebuild every time, no layer caching
  Baseline: 45 minutes average build time

  Root Cause Analysis:
  - Package manager cache not preserved between builds
  - All dependencies reinstalled on every build
  - Source code changes invalidate entire cache

  Hypothesis: Optimizing Dockerfile layer order and caching
              will reduce build time to <10 minutes

  Changes Planned:
  1. Restructure Dockerfile: COPY package*.json before src
  2. Add .dockerignore for node_modules
  3. Configure CI cache for Docker layers

  Success Criteria: Build time <10 minutes when dependencies unchanged

DO:
  Actions Taken:
  - Restructured Dockerfile to copy package.json first
  - Added comprehensive .dockerignore
  - Enabled Docker layer caching in CI pipeline
  - Tested on 5 consecutive builds

  Deviations from Plan: None

CHECK:
  Results:
  - Unchanged dependencies: 8 minutes (target: <10) ✓
  - Changed dependencies: 12 minutes (was 45)
  - Fresh builds: 45 minutes (same, expected)

  Analysis:
  - 82% reduction on cached builds
  - Hypothesis confirmed for dependency-stable builds
  - Dependency changes still slow

ACT:
  Standardize:
  ✓ Merged Dockerfile changes to main
  ✓ Updated CI pipeline configuration
  ✓ Added build time monitoring
  ✓ Documented in team README

  Next Cycle Needed:
  - 12 minutes still slow when dependencies change
  - Investigate npm ci vs npm install
  → Start CYCLE 2


CYCLE 2
───────
PLAN:
  Problem: Build still 12 min when dependencies change
  Root Cause: npm install rebuilds all packages from scratch
  Hypothesis: npm ci + binary mirrors will reduce to <5 minutes
  Success Criteria: <5 minutes on dependency changes

DO:
  - Changed to npm ci (uses package-lock.json)
  - Added .npmrc with binary mirror configuration
  - Tested across 5 dependency updates

CHECK:
  Results:
  - Dependency changes: 4.5 minutes ✓ (was 12)
  - Compilation errors reduced to 0 (was occasional)

  Analysis: npm ci is faster AND more reliable

ACT:
  Standardize:
  ✓ Use npm ci everywhere (local scripts + CI)
  ✓ Committed .npmrc to repository
  ✓ Updated developer onboarding docs

  TOTAL IMPROVEMENT: 45min → 4.5min (90% reduction)
  ✓ PDCA Complete - Monitor for 2 weeks
```

---

### Code Quality Audit with Smart Analysis

**Scenario**: Technical debt review of the authentication module.

```bash
# Use smart analysis to auto-select best method
> /analyse authentication module for technical debt
```

**Kaizen auto-selects Muda (Waste) Analysis**:
```
SCOPE: Authentication module (8K LOC)
METHOD SELECTED: Muda (Waste) Analysis
REASON: Technical debt assessment matches waste identification

1. OVERPRODUCTION
   Found:
   • 5 authentication methods implemented (only OAuth used)
   • Abstract "AuthProvider" framework (single implementation)
   • 12 feature flags (8 for features fully rolled out)

   Impact: 3K LOC maintained for no purpose
   Recommendation: Remove unused auth methods, clean up flags

2. WAITING
   Found:
   • Token validation calls external service (200ms per request)
   • Session lookup not cached (DB query every time)

   Impact: 200ms added to every authenticated request
   Recommendation: Cache tokens and sessions in Redis

3. TRANSPORTATION
   Found:
   • User object transformed 4 times: DB → ORM → Service → DTO → Response
   • Auth headers parsed in 3 different places

   Impact: Unnecessary allocations and CPU cycles
   Recommendation: Reduce transformation layers

4. OVER-PROCESSING
   Found:
   • Password hashed twice (once on creation, once on comparison)
   • Full user profile loaded for simple auth checks
   • Verbose logging on every token validation

   Impact: Wasted CPU, storage, and slower response
   Recommendation: Load minimal data, reduce logging verbosity

5. INVENTORY
   Found:
   • 3 open PRs for auth improvements (oldest: 4 months)
   • Commented-out OAuth2 migration code
   • 15 "TODO: fix this" comments

   Impact: Mental overhead, merge conflicts
   Recommendation: Close stale PRs, remove dead code, address TODOs

6. MOTION
   Found:
   • Auth config spread across 4 files
   • Developers must check 3 places for auth logic
   • Manual token rotation (no automation)

   Impact: Developer time wasted, error-prone changes
   Recommendation: Consolidate config, automate rotation

7. DEFECTS
   Found:
   • 3 auth-related bugs in last month
   • No integration tests for token refresh flow
   • Race condition in concurrent login handling

   Impact: Security risk, customer complaints
   Recommendation: Add tests, fix race condition

───────────────────────────────────────
SUMMARY

Total Waste Identified:
• Code: 3K LOC doing nothing useful
• Time: 200ms per request overhead
• Effort: Developer confusion from scattered config

Priority Fixes (by impact):
1. HIGH: Add Redis caching for tokens/sessions
2. HIGH: Fix race condition in concurrent login
3. MEDIUM: Remove unused authentication methods
4. MEDIUM: Consolidate auth configuration
5. LOW: Clean up stale PRs and TODOs

Estimated Recovery:
• 30% code reduction in module
• 50% faster auth operations
• Reduced maintenance burden
```

---

### Bug Tracing Through Call Stack

**Scenario**: Files being created in wrong directory during tests.

```bash
# Use root cause tracing for deep stack bugs
> /root-cause-tracing
```

**Expected Trace**:
```
SYMPTOM:
.git directory created in packages/core/ (source code directory)
instead of temporary test directory

IMMEDIATE CAUSE:
git init runs with empty cwd parameter, defaulting to process.cwd()

TRACE CHAIN:

Level 1: Where error occurs
  File: WorktreeManager.ts:45
  Code: await execFileAsync('git', ['init'], { cwd: projectDir });
  Value: projectDir = '' (empty string)

Level 2: What called this?
  File: Session.ts:120
  Code: WorktreeManager.createSessionWorktree(projectDir, sessionId)
  Value: projectDir passed as empty string

Level 3: Where did empty string come from?
  File: Session.ts:80
  Code: const projectDir = context.tempDir;
  Value: context.tempDir = ''

Level 4: Why is tempDir empty?
  File: test-helpers.ts:30
  Code: const context = setupCoreTest();
  Issue: context.tempDir accessed BEFORE beforeEach runs

Level 5: Why is access allowed before beforeEach?
  File: test-helpers.ts:15
  Code: return { tempDir: '' }; // Initial value
  Issue: Returns object with empty defaults

ROOT CAUSE:
setupCoreTest() returns an object with empty string defaults.
Tests access context.tempDir at module load time (top-level),
before beforeEach has a chance to populate it.

FIX AT SOURCE:
Make tempDir a getter that throws if accessed before initialization:

export function setupCoreTest() {
  let _tempDir = '';
  let _initialized = false;

  beforeEach(() => {
    _tempDir = fs.mkdtempSync(...);
    _initialized = true;
  });

  return {
    get tempDir() {
      if (!_initialized) {
        throw new Error('tempDir accessed before beforeEach');
      }
      return _tempDir;
    }
  };
}

DEFENSE-IN-DEPTH LAYERS ADDED:
1. Project.create() validates directory is non-empty
2. WorkspaceManager.init() validates not current directory
3. NODE_ENV guard refuses git init outside /tmp in test mode
4. Stack trace logging before any git init call

VERIFICATION:
✓ 1847 tests pass
✓ No .git created in source directories
✓ Error thrown immediately on early access
```

---

### Exploring Unfamiliar Code with Gemba Walk

**Scenario**: Need to understand authentication flow before making changes.

```bash
# Use analyse with Gemba Walk focus
> /analyse authentication implementation
```

**Kaizen selects Gemba Walk**:
```
SCOPE: User authentication flow
METHOD SELECTED: Gemba Walk
REASON: Understanding unfamiliar implementation matches "go and see"

ASSUMPTIONS (Before Investigation):
• JWT tokens stored in localStorage
• Single sign-on via OAuth only
• Session expires after 1 hour
• Password reset via email link

GEMBA OBSERVATIONS (Actual Code):

Entry Point: /api/auth/login
File: routes/auth.ts:45

Flow Traced:
1. POST /api/auth/login
   └─> AuthController.login()
       └─> AuthService.authenticate(email, password)
           └─> UserRepository.findByEmail(email)
           └─> bcrypt.compare(password, user.passwordHash)
           └─> TokenService.generate(user.id)

Actual Implementation:
• Tokens stored in httpOnly cookies (NOT localStorage)
• Refresh token in separate cookie (15 days TTL)
• Session data in Redis (30 days TTL)
• JWT expiry: 24 hours (NOT 1 hour)
• OAuth code exists but is commented out
• Password reset requires admin intervention (no email flow)

SURPRISES (Reality vs. Assumptions):

✗ OAuth NOT implemented
  Location: services/oauth.ts (entire file commented out)
  Comment: "// TODO: finish OAuth integration"

✗ Password reset is MANUAL
  Location: routes/admin.ts:89
  Process: Admin generates temporary password, emails manually

✗ THREE different session storage mechanisms:
  - Redis for session data
  - Database for "remember me" tokens
  - Cookies for JWT tokens
  No documentation explaining why

✗ Legacy endpoint still active
  Location: routes/legacy-auth.ts
  Issue: /auth/legacy has NO authentication check
  Risk: Security vulnerability

✗ Admin users bypass rate limiting
  Location: middleware/rate-limit.ts:23
  Code: if (user.role === 'admin') return next();
  Risk: Admin accounts vulnerable to brute force

GAPS (Documentation vs. Reality):
• Docs say OAuth, code doesn't have it
• Session expiry: docs say 1hr, code says 24hr
• Legacy endpoint not documented (security risk)
• "Remember me" feature undocumented

RECOMMENDATIONS:

Priority: HIGH
1. Secure or remove /auth/legacy endpoint
2. Add rate limiting for admin users

Priority: MEDIUM
3. Update documentation with actual behavior
4. Either implement OAuth or remove dead code
5. Consolidate session storage (pick one approach)

Priority: LOW
6. Clean up commented-out code
7. Document "remember me" feature
```

---

## Integration with Other Plugins

### With Reflexion (Bug Investigation Workflow)

```bash
# Investigate bug root cause
> /why "Why does the payment fail for international cards?"

# After understanding root cause, memorize the pattern
> /reflexion:memorize "International payment processing patterns"
```

### With Code Review

```bash
# Get code review first
> /review-local-changes

# Analyze any quality issues found
> /cause-and-effect "High complexity in reviewed code"

# Plan systematic improvement
> /plan-do-check-act "Reduce cyclomatic complexity"
```

### With Git (Full Bug Fix Workflow)

```bash
# 1. Load issue context
> /git:analyze-issue #456

# 2. Trace to root cause
> /root-cause-tracing

# 3. Understand why it happened
> /why

# 4. Implement fix based on root cause
> claude "Fix the issue based on root cause analysis"

# 5. Memorize learnings
> /reflexion:memorize "Bug patterns from issue #456"

# 6. Commit with context
> /git:commit
```

### With SDD (Quality Improvement After Implementation)

```bash
# After implementing feature
> /sdd:04-implement

# Analyze for waste and improvements
> /analyse "Check implementation for waste"

# If issues found, plan improvement
> /plan-do-check-act "Optimize implementation"

# Document final implementation
> /sdd:05-document
```
