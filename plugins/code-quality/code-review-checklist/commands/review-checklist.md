Review the current changes using this systematic checklist:

## Code Quality Checklist

Analyze recent git changes and check each category:

### 1. Correctness
- [ ] Logic errors or edge cases
- [ ] Null/undefined handling
- [ ] Error handling completeness
- [ ] Off-by-one errors
- [ ] Race conditions

### 2. Security
- [ ] Input validation
- [ ] SQL injection vulnerabilities
- [ ] XSS vulnerabilities
- [ ] Authentication/authorization
- [ ] Sensitive data exposure

### 3. Performance
- [ ] Unnecessary loops or operations
- [ ] Memory leaks
- [ ] Database query optimization
- [ ] Caching opportunities
- [ ] Algorithmic complexity

### 4. Maintainability
- [ ] Code duplication (DRY)
- [ ] Function/method length
- [ ] Clear naming conventions
- [ ] Commented complex logic
- [ ] Consistent style

### 5. Testing
- [ ] Test coverage adequate
- [ ] Edge cases tested
- [ ] Error cases tested
- [ ] Integration points tested

## Instructions

For each failed check:
1. Quote the problematic code
2. Explain the issue clearly
3. Suggest a specific fix
4. Indicate severity (critical/major/minor)

Focus on actionable feedback. Skip checks that pass without comment.
