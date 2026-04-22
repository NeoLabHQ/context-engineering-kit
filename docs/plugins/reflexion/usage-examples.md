# Reflexion Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the Reflexion plugin.

## Automatic Reflection with Hooks

The simplest way to use reflection is with the automatic hooks. Include the word "reflect" in your prompt and Claude will automatically reflect on its work.

### Basic Automatic Reflection

```bash
# Automatic reflection - no manual command needed
> claude "implement user authentication, then reflect"

# Claude implements the feature, then automatically:
# 1. Runs /reflect
# 2. Reviews its own work
# 3. Fixes any issues found or suggests improvements
```

### Automatic Reflection in Workflows

```bash
# Feature implementation with automatic reflection
> claude "add payment processing with Stripe, reflect on security"
# Claude implements payment processing
# Hook triggers automatic reflection focused on security

# Bug fix with automatic verification
> claude "fix the null pointer exception in user service, reflect"
# Claude fixes the bug and automatically verifies the fix
```

## Manual Reflection Examples

### Quick Quality Check

**Scenario**: You've implemented a simple utility function and want to verify it's correct.

```bash
# Implement the function
> claude "create a function to format phone numbers to (XXX) XXX-XXXX format"

# Quick reflection
> /reflect
```

**Expected Flow**:

1. Reflexion triages as "Quick Path" (simple task)
2. Performs 5-second verification
3. Either confirms quality or suggests specific improvements
4. No memorization needed for trivial utility

**When Reflection Finds Issues**:
```
Reflection Output:
- ✅ Function works for standard US numbers
- ⚠️ No validation for input format
- ⚠️ Doesn't handle international numbers
- Refined version includes input validation and clear error messages
```

### Comprehensive Feature Review

**Scenario**: Complex authentication feature needs thorough review.

```bash
# Implement authentication
> claude "implement OAuth2 authentication with Google and GitHub providers"

# Comprehensive multi-perspective review
> /critique

# Address findings
> claude "implement the Critical and High priority items from the critique"

# Quick check
> /reflect

# Save learnings
> /memorize
```

**Expected Critique Output**:
```
Executive Summary:
Overall Quality Score: 7.3/10 - Good implementation with security improvements needed

Judge Scores:
- Requirements Validator: 8/10 - All requirements met, one edge case missing
- Solution Architect: 7/10 - Good architecture, session management could improve
- Code Quality Reviewer: 7/10 - Clean code, needs error handling improvements

Critical Issues:
- OAuth tokens stored in localStorage (security risk)
  → Use httpOnly cookies for token storage

High Priority:
- Missing CSRF protection
- No token refresh mechanism
```

### Implement → Reflect → Memorize

```bash
# Implement feature
> claude "implement Stripe payment processing with subscription support"

# Reflect on implementation
> /reflect
```

**Reflection finds optimization opportunity**:

```md
Issue Identified: Stripe API called synchronously in request handler
Solution: Move to background job queue for better response time
Performance Analysis:
- Current: 2-3s response time
- Improved: <200ms with async processing
```

```bash
# Apply improvement
> claude "refactor payment processing to use background jobs"

# Confirm improvement
> /reflect

# Save pattern
> /memorize
```

**Memorized Knowledge** (added to CLAUDE.md):

```markdown
## Development Guidelines

### API Integration Patterns

- For third-party API calls (Stripe, SendGrid, etc.) that take >500ms:
  - Move to background job queue (Bull/BullMQ)
  - Return immediate response with job ID
  - Use webhooks for status updates
  - Improves API response time from ~2s to <200ms
  - Example: Stripe payment processing, email sending
```


### Design → Critique → Refine

**Scenario**: Designing a caching strategy.

```bash
# Initial design
> claude "design a caching strategy for our product catalog API"

# Get multi-perspective review
> /critique

# Debate reveals issues
> claude "update caching design based on critique"

# Re-evaluate
> /critique

# Finalize
> /memorize --section="Architecture Decisions"
```

**First Critique**:
```
Requirements Validator: Meets performance requirements but unclear invalidation strategy
Solution Architect: Redis good choice, but missing cache warming strategy
Code Quality: Need monitoring and fallback mechanisms
```

**Second Critique** (after refinement):
```
Requirements Validator: 9/10 - All concerns addressed
Solution Architect: 8/10 - Comprehensive solution with good trade-offs
Code Quality: 9/10 - Includes monitoring, fallback, and cache warming

Verdict: ✅ Ready to ship
```

### Continuous Improvement Cycle

```bash
# Initial implementation
> claude "implement caching layer"

# First reflection
> /reflect

# Address issues and reflect again
> claude "fix the issues identified"
> /reflect

# Capture final insights
> /memorize
```

## Integration with Other Plugins

### With Code Review
```bash
> /review-local-changes
> /memorize "Code review findings"
```

### With SDD
```bash
> /implement-task
> /reflect
```

### With Kaizen
```bash
> /why "Why did the bug occur?"
> /memorize "Root cause patterns"
```
