---
title: Use Existing Libraries Instead of Custom Code
impact: HIGH
paths:
  - "**/*"
  - "**/*"
---

# Use Existing Libraries Instead of Custom Code

Always search for existing libraries, services, or third-party APIs before writing custom code:
- Check npm for existing libraries that solve the problem
- Evaluate existing services/SaaS solutions
- Consider third-party APIs for common functionality

Every line of custom code is a liability that requires maintenance, testing, and documentation. The Not Invented Here (NIH) syndrome leads to fragile, undertested reimplementations of solved problems.

Before writing any utility, helper, or infrastructure code, check npm for established packages that solve the problem. For example, use `cockatiel` instead of writing your own retry logic.

Custom code is only justified when:
- Specific business logic unique to the domain
- Performance-critical paths with special requirements
- When external dependencies would be overkill
- Security-sensitive code requiring full control
- When existing solutions don't meet requirements after thorough evaluation

## Incorrect

Custom retry logic is implemented from scratch instead of using an established library. This hand-rolled solution lacks features like exponential backoff, jitter, circuit breaking, and proper error classification that battle-tested libraries provide.

```typescript
// Custom retry utility - reinventing the wheel
async function retry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      await new Promise((resolve) => setTimeout(resolve, delay))
    }
  }
  throw lastError!
}

const data = await retry(() => fetchFromApi('/users'))
```

Anti-Pattern to Avoid: NIH (Not Invented Here) Syndrome:
- Don't build custom auth when Auth0/Supabase exists
- Don't write custom state management instead of using Redux/Zustand
- Don't create custom form validation instead of using established libraries

## Correct

An established library handles retry logic with proven patterns for backoff, jitter, and circuit breaking out of the box.

```typescript
import { retry, handleAll, ExponentialBackoff } from 'cockatiel'

const retryPolicy = retry(handleAll, {
  maxAttempts: 3,
  backoff: new ExponentialBackoff(),
})

const data = await retryPolicy.execute(() => fetchFromApi('/users'))
```
