# Code Review Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the Code Review plugin.

## Basic Workflows

### Example 1: Pre-Commit Review

**Scenario**: Review changes before committing.

```bash
# Make changes
> claude "add user registration endpoint"

# Review before commit
> /code-review:review-local-changes
```

**Review Output**:
```
Critical Issues:
- [Security] Password stored in plain text (UserController.ts:45)
- [Bug Hunter] No email validation before database insert

High Priority:
- [Test Coverage] No tests for registration endpoint
- [Security] Missing rate limiting on registration endpoint

Action Required: Fix critical issues before committing
```

```bash
# Fix critical issues
> claude "hash passwords with bcrypt and add email validation"

# Re-review
> /code-review:review-local-changes

# Clean review - commit
> /git:commit "Add user registration with validation and security"
```

### Example 2: Pull Request Review

**Scenario**: Review PR before merging.

```bash
# Create PR
> /git:create-pr "Add payment processing"

# Review PR #456
> /code-review:review-pr 456
```

**Review Findings**:
```
Overall Assessment: ⚠️ Needs improvements before merging

Blocking Issues:
1. [Security] Stripe secret key hardcoded in PaymentService.ts
2. [Bug Hunter] Race condition in payment confirmation logic

Recommended:
3. [Test Coverage] Missing integration tests for payment flow
4. [Contracts] Breaking change in Payment API response format

Verdict: Request changes for security and race condition
```

```bash
# Address findings
> claude "move Stripe key to environment variable and fix race condition with distributed lock"

# Request re-review from team
```

## Security-Focused Reviews

### Example 3: Security Audit Focus

**Scenario**: New authentication feature needs security review.

```bash
# Implement OAuth
> claude "implement OAuth2 authentication with Google provider"

# Security-focused review
> /code-review:review-local-changes security
```

**Security Findings**:
```
Critical Vulnerabilities:
1. OAuth state parameter not validated (CSRF risk)
   - Location: OAuthController.ts:67
   - OWASP: A01:2021 - Broken Access Control
   - Fix: Validate state parameter matches session

2. Tokens stored in localStorage (XSS risk)
   - Location: AuthService.ts:123
   - OWASP: A03:2021 - Injection
   - Fix: Use httpOnly cookies instead

High Risk:
3. No OAuth redirect URI validation
   - Attacker can redirect to malicious site
   - Fix: Whitelist allowed redirect URIs

4. Missing PKCE for public clients
   - Recommendation: Implement PKCE flow
```

```bash
# Apply security fixes
> claude "implement all critical and high security fixes"

# Verify security
> /code-review:review-local-changes security

# Clean security audit
> /git:commit "Add OAuth2 with security best practices"
```

## Test Coverage Reviews

### Example 4: Ensuring Test Quality

**Scenario**: Feature complete, need to verify test coverage.

```bash
# Implement feature
> claude "add shopping cart functionality"

# Test coverage review
> /code-review:review-local-changes tests
```

**Coverage Analysis**:
```
Coverage Summary:
- CartService: 35% (Target: 80%)
- CartController: 60% (Target: 80%)
- CartRepository: 85% ✓

Missing Test Cases:

CartService:
1. addItem() - No edge case tests
   Missing: Add duplicate item test
   Missing: Exceeds maximum quantity test
   Missing: Invalid product ID test

2. checkout() - No error path tests
   Missing: Insufficient inventory test
   Missing: Payment failure test
   Missing: Concurrent checkout test

Test Quality Issues:
- Mock database calls use shared state
- No integration tests for cart workflow
- Test names not descriptive ("test1", "test2")
```

```bash
# Add missing tests
> claude "add all missing test cases identified by code review"

# Verify coverage
> /code-review:review-local-changes tests

# Coverage now: 82% ✓
> /git:commit "Add shopping cart with comprehensive tests"
```

## Code Quality Improvements

### Example 5: Refactoring Legacy Code

**Scenario**: Legacy code needs quality improvements.

```bash
# Review existing code
> claude "review src/legacy/order-processor.js for refactoring opportunities"

> /code-review:review-local-changes
```

**Quality Assessment**:
```
Code Quality Score: 3/10

Critical Issues:
1. OrderProcessor.process() - Complexity: 25 (Max: 10)
   - 150 lines in single function
   - Nesting depth: 7 levels
   - Multiple responsibilities

2. No error handling
   - Silent failures throughout
   - No logging
   - No transaction rollback

Refactoring Recommendations:

High Priority:
1. Extract Methods
   Before:
   function process(order) {
     if (order.type === 'express') {
       if (order.amount > 100) {
         if (order.user.isPremium) {
           // 100 more lines...
         }
       }
     }
   }

   After:
   function process(order) {
     validateOrder(order);
     const processor = getProcessor(order.type);
     return processor.handle(order);
   }

2. Introduce Error Handling
   - Wrap in try-catch
   - Add logging
   - Implement transaction management

3. Apply SOLID Principles
   - Single Responsibility: Separate validation, processing, storage
   - Open/Closed: Use strategy pattern for order types
   - Dependency Inversion: Inject dependencies
```

```bash
# Apply refactorings incrementally
> claude "extract methods from OrderProcessor"
> /code-review:review-local-changes

> claude "add error handling and logging"
> /code-review:review-local-changes

> claude "apply SOLID principles"
> /code-review:review-local-changes

# Final quality check
> /code-review:review-local-changes
# Code Quality Score: 8/10 ✓

> /git:commit "Refactor OrderProcessor - improved quality from 3/10 to 8/10"
```

## Contract Validation

### Example 6: API Contract Review

**Scenario**: New API endpoint needs contract validation.

```bash
# Add new API endpoint
> claude "add POST /api/v2/orders endpoint"

# Contract review
> /code-review:review-local-changes contracts
```

**Contract Findings**:
```
Contract Issues:

Breaking Changes:
1. Response format inconsistent with v1
   - v1: { data: order, error: null }
   - v2: { order: order }
   - Impact: Breaks client compatibility
   - Fix: Maintain consistent response wrapper

Type Safety:
2. OrderRequest interface missing required fields
   - customerId marked as optional but required in logic
   - quantity type is 'any' instead of 'number'
   - Fix: Update interface to match requirements

Inconsistencies:
3. Error format differs from other v2 endpoints
   - /orders returns: { error: { message, code } }
   - /products returns: { error: "message" }
   - Fix: Standardize error format across v2 API

Documentation:
4. Missing OpenAPI spec for new endpoint
   - No request/response schema
   - No error codes documented
   - Fix: Update OpenAPI spec
```

```bash
# Fix contract issues
> claude "fix all contract issues and update OpenAPI spec"

# Verify contracts
> /code-review:review-local-changes contracts

> /git:commit "Add POST /api/v2/orders with consistent contracts"
```

## Integration Patterns

### Example 7: Code Review + Reflexion

**Scenario**: Comprehensive quality check.

```bash
# Implement feature
> claude "add real-time notifications"

# Multi-layered review
> /code-review:review-local-changes
# Fix high/critical issues
> claude "address all critical and high priority findings"

# Deep reflection
> /reflexion:critique
# Additional perspective caught architectural concerns

# Apply all feedback
> claude "address reflexion critique findings"

# Final verification
> /code-review:review-local-changes
# Clean ✓

# Save learnings
> /reflexion:memorize

> /git:commit "Add real-time notifications with comprehensive quality review"
```

### Example 8: Code Review + SDD Workflow

**Scenario**: Feature development with specification.

```bash
# Specify and plan
> /sdd:01-specify "Add webhook system for third-party integrations"
> /sdd:02-plan
> /sdd:03-tasks

# Implement
> /sdd:04-implement

# Code review after implementation
> /code-review:review-local-changes
```

**Review finds issues**:
```
Critical:
- [Security] Webhook signatures not validated
- [Bug Hunter] Retry logic can cause duplicate processing

High:
- [Test Coverage] No tests for webhook validation
- [Contracts] Webhook payload schema not documented
```

```bash
# Fix issues
> claude "fix critical and high priority code review findings"

# Verify fixes
> /code-review:review-local-changes
# Clean ✓

# Document
> /sdd:05-document

> /git:commit "Add webhook system with security and validation"
```

## Historical Context Usage

### Example 9: Maintaining Consistency

**Scenario**: Adding feature to existing module.

```bash
# Add new authentication method
> claude "add API key authentication to existing auth system"

> /code-review:review-local-changes
```

**Historical Context Findings**:
```
Pattern Deviations:

1. Different pattern than existing auth methods
   - Existing: Factory pattern (AuthMethodFactory.create())
   - New code: Direct instantiation
   - Recommendation: Follow factory pattern for consistency

2. Different storage approach
   - Existing: All auth tokens in Redis
   - New code: API keys in PostgreSQL
   - Historical: Redis chosen for session performance (ADR-012)
   - Recommendation: Use Redis for consistency unless justified

3. Different error handling
   - Existing: Throws AuthenticationError
   - New code: Returns null on failure
   - Recommendation: Match existing error handling pattern

Similar Past Issues:
4. Similar pattern added in PR #234 (3 months ago)
   - Also deviated from factory pattern
   - Caused maintenance issues
   - Was refactored in PR #267
   - Learn from history: Use factory pattern from start
```

```bash
# Align with existing patterns
> claude "refactor to match existing authentication patterns and use factory pattern"

> /code-review:review-local-changes
# Historical context issues resolved ✓

> /git:commit "Add API key authentication following existing patterns"
```

## Bug Prevention

### Example 10: Catching Bugs Early

**Scenario**: Complex algorithm needs validation.

```bash
# Implement recommendation algorithm
> claude "implement product recommendation algorithm based on user behavior"

> /code-review:review-local-changes
```

**Bug Hunter Findings**:
```
Critical Bugs:

1. Division by zero risk
   - Location: RecommendationEngine.ts:89
   - Code: score = totalClicks / totalViews
   - Issue: totalViews can be 0 for new products
   - Fix: Add zero check or use default value

2. Infinite loop potential
   - Location: RecommendationEngine.ts:134
   - Code: while (recommendations.length < limit) { ... }
   - Issue: If no products match criteria, infinite loop
   - Fix: Add iteration limit or break condition

Potential Issues:

3. Race condition in cache update
   - Multiple concurrent requests can corrupt cache
   - Fix: Use atomic operations or locking

4. Memory leak in event listener
   - Event listeners not removed after processing
   - Fix: Ensure proper cleanup

Edge Cases Not Handled:

5. User with no behavior history
   - Algorithm fails for new users
   - Fix: Implement cold-start strategy

6. All products out of stock
   - Empty recommendations returned
   - Fix: Include similar in-stock products
```

```bash
# Fix all bugs
> claude "fix all bug hunter findings"

# Verify fixes
> /code-review:review-local-changes
# No critical bugs ✓

> /git:commit "Add recommendation engine with bug fixes"
```

## Performance Reviews

### Example 11: Performance-Critical Code

**Scenario**: API endpoint needs performance validation.

```bash
# Optimize search endpoint
> claude "optimize product search to handle 1000 req/sec"

> /code-review:review-local-changes
```

**Code Quality Reviewer Notes**:
```
Performance Concerns:

1. N+1 Query Problem
   - Location: ProductService.ts:56
   - Issue: Loading reviews in loop (N queries)
   - Impact: 100 products = 101 queries
   - Fix: Use JOIN or eager loading

2. Missing Pagination
   - Returns all matching products in one request
   - Can return thousands of products
   - Fix: Implement pagination with limits

3. No Caching
   - Popular searches repeated frequently
   - Each request hits database
   - Fix: Add Redis caching layer

4. Inefficient Filtering
   - Filters applied after fetching all records
   - Database does work client could do
   - Fix: Push filters to database query

Suggested Optimizations:
- Add database indexes on search fields
- Implement query result caching (5min TTL)
- Use database full-text search
- Add pagination (default 20, max 100)
```

```bash
# Apply performance improvements
> claude "implement all performance optimizations"

# Verify improvements
> /code-review:review-local-changes
# No performance concerns ✓

# Benchmark
> claude "add performance tests to verify 1000 req/sec target"

> /git:commit "Optimize product search for high throughput"
```

## Continuous Improvement

### Example 12: Building Quality Habits

**Week 1**: First PR
```bash
> /code-review:review-pr 100
# Result: 15 issues found (3 critical, 5 high, 7 medium)
```

**Week 2**: After learning from review
```bash
> /code-review:review-pr 110
# Result: 8 issues found (1 critical, 2 high, 5 medium)
```

**Week 3**: Habits forming
```bash
> /code-review:review-pr 120
# Result: 3 issues found (0 critical, 1 high, 2 medium)
```

**Week 4**: Consistent quality
```bash
> /code-review:review-pr 130
# Result: 1 issue found (0 critical, 0 high, 1 medium)
# Verdict: ✅ Ready to ship
```

**Result**: Code quality improved systematically by using review findings to learn and improve.

## Tips for Effective Usage

### Before Committing
1. **Review Small Changes Frequently**: Easier to address issues
2. **Focus on Critical/High First**: Don't get overwhelmed
3. **Re-review After Fixes**: Verify fixes don't introduce new issues
4. **Use Focused Reviews**: Pass review aspects (e.g., `security`) and `--min-impact` for specific concerns

### During PR Process
1. **Review Before Creating PR**: Catch issues privately
2. **Re-review After Updates**: Ensure feedback addressed
3. **Combine with Manual Review**: Automated + human is best
4. **Document Disagreements**: If you disagree with findings

### Building Quality
1. **Learn from Findings**: Understand why issues flagged
2. **Update CLAUDE.md**: Save common patterns
3. **Track Improvement**: Monitor issue counts over time
4. **Share Knowledge**: Discuss findings with team

## Common Pitfalls to Avoid

1. **Ignoring Low Priority**: They accumulate into technical debt
2. **Fixing Without Understanding**: Learn why it's an issue
3. **One-Time Reviews**: Make it part of every workflow
4. **Disagreeing Without Documentation**: Explain your reasoning
5. **Review Fatigue**: Start with small changes to build habit

## Measuring Success

### Metrics to Track
- Issues found per PR (should decrease over time)
- Critical/High priority issues (target: 0 before merge)
- Re-review cycles (fewer is better)
- Time to address findings (faster is better)
- Production bugs (should decrease)

### Success Indicators
- Consistently clean reviews (0-2 minor issues)
- Faster PR approvals
- Fewer production bugs
- Better code quality scores
- Team adopts similar patterns

## Next Steps

- Review [Commands Reference](./commands.md) for detailed command options
- Explore [Agents Reference](./agents.md) to understand each reviewer
- Check [Installation Guide](./installation.md) for setup details
- Read [Main Documentation](./README.md) for overview and best practices
