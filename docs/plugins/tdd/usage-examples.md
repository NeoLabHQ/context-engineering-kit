# TDD Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the TDD plugin for test-first development and comprehensive test coverage.

## Examples

### Simple Feature with TDD

**Scenario**: You've implemented a utility function and need to ensure it has proper test coverage.

```bash
# Implement the function
> claude "create a function to validate email addresses with proper regex"

# Add test coverage
> /write-tests
```

**Expected Flow**:

1. Plugin analyzes changes (single simple file)
2. Writes tests directly (no agent orchestration needed)
3. Creates test file with comprehensive cases:
   - Valid email formats
   - Invalid email formats
   - Edge cases (empty, special characters)
   - Error handling

**Generated Test Example**:

```typescript
describe('validateEmail', () => {
  test('accepts valid email addresses', () => {
    expect(validateEmail('user@example.com')).toBe(true);
    expect(validateEmail('user.name@domain.org')).toBe(true);
    expect(validateEmail('user+tag@example.co.uk')).toBe(true);
  });

  test('rejects invalid email addresses', () => {
    expect(validateEmail('invalid')).toBe(false);
    expect(validateEmail('missing@domain')).toBe(false);
    expect(validateEmail('@nodomain.com')).toBe(false);
  });

  test('handles edge cases', () => {
    expect(validateEmail('')).toBe(false);
    expect(validateEmail(null)).toBe(false);
    expect(validateEmail(undefined)).toBe(false);
  });
});
```

### Complex Feature with Agent Orchestration

**Scenario**: You've implemented a multi-file payment processing feature and need comprehensive test coverage.

```bash
# Implement payment processing
> claude "implement Stripe payment processing with subscription support, webhooks, and retry logic"

# Generate comprehensive tests using agents
> /write-tests Focus on payment flows and error handling
```

**Expected Flow**:

1. Plugin detects multiple changed files with complex logic
2. Launches parallel coverage reviewer agents per file
3. Coverage reviewers identify test cases needed:

```
Payment Service (payment-service.ts):
- CRITICAL: Successful payment flow
- CRITICAL: Failed payment handling
- CRITICAL: Subscription creation
- IMPORTANT: Retry logic on network errors
- IMPORTANT: Webhook signature validation
- NICE_TO_HAVE: Idempotency key handling

Webhook Handler (webhook-handler.ts):
- CRITICAL: subscription.created event
- CRITICAL: payment_intent.succeeded event
- CRITICAL: payment_intent.failed event
- IMPORTANT: Invalid signature rejection
- NICE_TO_HAVE: Duplicate event handling
```

4. Launches parallel developer agents to write tests
5. Verification agents confirm coverage completeness
6. Full test suite runs to verify all pass

### Fixing Tests After Refactoring

**Scenario**: You refactored the authentication system from sessions to JWT, and now tests are failing.

```bash
# After refactoring
> claude "refactor user authentication from sessions to JWT tokens"

# Fix all failing tests
> /fix-tests
```

**Expected Flow**:

1. Plugin runs full test suite, identifies 12 failing tests across 4 files
2. Groups failures by file:

```
auth.test.ts - 5 failures
session.test.ts - 3 failures
middleware.test.ts - 2 failures
user.test.ts - 2 failures
```

3. Launches parallel agents per test file
4. Each agent analyzes failures and fixes:

```
auth.test.ts:
- ✅ Updated login test to check for JWT instead of session cookie
- ✅ Fixed logout test to verify token invalidation
- ✅ Updated token refresh test assertions
- ✅ Fixed authentication middleware expectations
- ✅ Updated user context extraction

session.test.ts:
- ❌ REMOVED - Session tests no longer applicable (confirmed with verification)
```

5. Full suite passes after fixes

**Agent Output Example**:

```
Analyzing auth.test.ts failures...

Failure 1: "login should create session"
  - Expected: res.cookies to contain 'sessionId'
  - Actual: res.body contains 'accessToken' and 'refreshToken'
  - Fix: Update assertions to check JWT response

Failure 2: "logout should destroy session"
  - Expected: session.destroy() to be called
  - Actual: JWT invalidation via token blacklist
  - Fix: Update to verify token added to blacklist

Implementing fixes...
Running tests...
All 5 tests in auth.test.ts now passing ✅
```

### Test-First Bug Fix

**Scenario**: Bug reported - empty usernames are accepted during registration.

```bash
# Write failing test first (TDD approach)
> claude "write a test that fails because empty usernames are accepted"

# Implement the fix
> claude "fix the validation to reject empty usernames"

# Verify and add edge case tests
> /write-tests Focus on username validation edge cases
```

**Expected Flow**:

1. Initial test written to fail:

```typescript
test('rejects empty username during registration', () => {
  const result = validateRegistration({ username: '', email: 'test@example.com' });
  expect(result.valid).toBe(false);
  expect(result.errors).toContain('Username is required');
});
```

2. Test fails (RED phase confirmed)
3. Fix implemented
4. Test passes (GREEN)
5. `/write-tests` adds comprehensive edge cases:

```typescript
describe('username validation', () => {
  test('rejects empty username', () => { /* ... */ });
  test('rejects whitespace-only username', () => { /* ... */ });
  test('rejects username shorter than 3 characters', () => { /* ... */ });
  test('rejects username longer than 30 characters', () => { /* ... */ });
  test('rejects username with special characters', () => { /* ... */ });
  test('accepts valid username', () => { /* ... */ });
});
```

### Coverage Review for Critical Module

**Scenario**: Before deploying a critical financial calculation module, you want to ensure comprehensive test coverage.

```bash
# Review existing coverage
> /write-tests Focus on financial calculations - ensure all edge cases covered

# Run coverage report
> npm run test:coverage

# Address any gaps identified
> /write-tests Cover the remaining uncovered branches
```

**Expected Coverage Review Output**:

```
Coverage Analysis for financial-calculator.ts:

Current Coverage: 72% (below recommended 90% for critical modules)

Missing Coverage:
- CRITICAL: Negative amount handling (line 45-52)
- CRITICAL: Currency conversion edge cases (line 78-85)
- CRITICAL: Rounding precision for sub-cent amounts (line 102-108)
- IMPORTANT: Zero amount edge case (line 33)
- IMPORTANT: Maximum amount boundary (line 67)

Launching test generation for missing cases...
```

**After Test Generation**:

```
Coverage Analysis Complete:

New Coverage: 94% ✅

Tests Added:
- test('handles negative amounts correctly')
- test('converts currencies with proper precision')
- test('rounds sub-cent amounts consistently')
- test('handles zero amount gracefully')
- test('enforces maximum amount limits')
```

### Post-Dependency Update Test Fixes

**Scenario**: After updating a major dependency (React 17 to 18), several tests are failing due to API changes.

```bash
# Update dependencies
> npm update react react-dom

# Run tests to see failures
> npm test

# Fix tests for new API
> /fix-tests React 18 API changes - focus on rendering and act() warnings
```

**Expected Agent Analysis**:

```
Analyzing failures related to React 18 migration...

Pattern Detected: act() warnings and async rendering changes

Common Fixes Applied:
1. Wrapped state updates in act()
2. Used waitFor() for async assertions
3. Updated findBy* to handle concurrent rendering
4. Fixed flaky tests due to Suspense changes

Files Fixed:
- components/UserProfile.test.tsx - 3 tests fixed
- hooks/useAuth.test.tsx - 2 tests fixed
- pages/Dashboard.test.tsx - 4 tests fixed

All 9 previously failing tests now pass ✅
```

### Multi-Module Test Coverage

**Scenario**: New microservice with multiple modules needs comprehensive test coverage before first deployment.

```bash
# After implementing all modules
> claude "implement user service with CRUD operations, authentication, and notifications"

# Generate tests for entire service
> /write-tests Cover all critical business logic across the service
```

**Expected Multi-Agent Orchestration**:

```
Analyzing changes across 8 files...

Launching Coverage Review Agents:
- Agent 1: user-controller.ts
- Agent 2: user-service.ts
- Agent 3: user-repository.ts
- Agent 4: auth-middleware.ts
- Agent 5: notification-service.ts

Coverage Review Complete. Test Cases Identified: 47

Launching Developer Agents:
- Agent 1: Writing user-controller.test.ts (12 cases)
- Agent 2: Writing user-service.test.ts (15 cases)
- Agent 3: Writing user-repository.test.ts (8 cases)
- Agent 4: Writing auth-middleware.test.ts (6 cases)
- Agent 5: Writing notification-service.test.ts (6 cases)

All agents complete. Running verification...

Final Results:
- 47 test cases written ✅
- All tests passing ✅
- Coverage: 89% (critical paths: 96%) ✅
```

## Integration with Other Plugins

### With Reflexion (Implement-Reflect-Test-Memorize)

```bash
# Implement feature
> claude "implement rate limiting middleware"

# Reflect on implementation quality
> /reflexion:reflect

# Ensure test coverage
> /write-tests

# Save testing insights
> /reflexion:memorize "Rate limiting test patterns"
```

**Memorized Knowledge** (added to CLAUDE.md):

```markdown
## Testing Strategies

### Rate Limiting Tests
- Use fake timers for time-based tests
- Test both success and throttled scenarios
- Include concurrent request handling tests
- Verify rate limit headers in responses
- Test rate limit reset behavior
```

### With Code Review (TDD-Review-Fix Cycle)

```bash
# Write tests for changes
> /write-tests

# Get multi-agent code review
> /review-local-changes

# Fix any test issues identified
> /fix-tests address code review findings
```

**Code Review Output**:

```
Test Quality Review:

Findings:
- MEDIUM: test in user.test.ts line 45 tests mock behavior
- LOW: Missing async/await in promise-based test
- LOW: Test names could be more descriptive

Recommendations:
- Unmock the repository, use test database instead
- Add await before async assertions
- Rename 'test1' to 'creates user with valid data'
```

### With SDD (Spec-Driven Development)

```bash
# Follow SDD workflow with TDD integration
> /sdd:01-clarify
> /sdd:02-research
> /sdd:03-design
> /sdd:04-implement  # Implementation phase

# TDD for implementation
> /write-tests  # Cover all implemented logic
> /fix-tests    # Fix any issues

# Continue SDD workflow
> /sdd:05-document
```

### With Git (Complete Pre-Commit Workflow)

```bash
# Implement feature
> claude "add password strength validation"

# Ensure test coverage
> /write-tests

# Fix any failing tests
> /fix-tests

# Review all changes
> /review-local-changes

# Commit with confidence
> /git:commit
```

## Anti-Pattern Detection Examples

### Detecting Mock Abuse

**Scenario**: Test is asserting on mock existence rather than behavior.

```bash
> /write-tests
```

**Plugin Detection**:

```
⚠️ Anti-Pattern Detected: Testing Mock Behavior

In payment.test.ts line 23:
  expect(screen.getByTestId('stripe-mock')).toBeInTheDocument();

Problem: Testing that the mock exists, not that the component works correctly.

Fix Applied:
- Unmocked Stripe component
- Updated test to verify actual payment flow
- Added proper assertions on payment result
```

### Detecting Test-Only Methods

**Scenario**: Production class contains methods only used in tests.

```bash
> /fix-tests
```

**Plugin Detection**:

```
⚠️ Anti-Pattern Detected: Test-Only Method in Production

In Session.ts line 45:
  destroy() { /* cleanup logic */ }

This method is only called from test files.

Recommendation:
- Move cleanup logic to test utilities
- Remove destroy() from Session class
- Use dependency injection for testable cleanup
```

### Detecting Incomplete Mocks

**Scenario**: Mock is missing fields that downstream code depends on.

```bash
> /write-tests
```

**Plugin Warning**:

```
⚠️ Potential Issue: Incomplete Mock

In api.test.ts line 78:
  const mockResponse = { status: 'success', data: { userId: '123' } };

Real API also returns: metadata, requestId, timestamp

Tests may pass but integration will fail.

Fix Applied:
- Updated mock to include all real API fields
- Added type checking to prevent future incomplete mocks
```

## Command Cheat Sheet

| Scenario | Command |
|----------|---------|
| Cover all local changes | `/write-tests` |
| Cover specific module | `/write-tests authentication module` |
| Focus on edge cases | `/write-tests Focus on edge cases and error handling` |
| Fix all failing tests | `/fix-tests` |
| Fix specific test files | `/fix-tests payment tests` |
| Fix after refactoring | `/fix-tests after API refactoring` |
| Fix after dependency update | `/fix-tests React 18 migration` |
