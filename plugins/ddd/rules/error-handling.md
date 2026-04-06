---
title: Typed Error Handling with Logging
paths:
  - "src/**/*"
impact: HIGH
---

# Typed Error Handling with Logging

Never silently swallow exceptions. Every catch block must use typed error handling and log the error before rethrowing or returning a failure result. Generic `catch (e)` blocks hide the root cause of failures, making production debugging nearly impossible. Use typed catch blocks that distinguish between expected domain errors and unexpected system failures. When error handling logic grows complex, extract it into smaller, reusable handler functions rather than duplicating catch logic across the codebase. Log the error with sufficient context (operation name, relevant IDs) before rethrowing so that the failure is traceable in logs even if the caller also catches it.

## Incorrect

Errors are caught with an untyped generic block, silently swallowed or rethrown without logging. The caller has no trace of what failed or why.

```typescript
async function processPayment(orderId: string, amount: number) {
  try {
    const result = await paymentGateway.charge(orderId, amount);
    await db.orders.update(orderId, { status: "paid" });
    return result;
  } catch (e) {
    // Silently swallowed — no logging, no typed handling
    return null;
  }
}
```

## Correct

Errors are caught with typed checks, logged with context before rethrowing, and complex handling is extracted into a reusable function.

```typescript
async function processPayment(orderId: string, amount: number) {
  try {
    const result = await paymentGateway.charge(orderId, amount);
    await db.orders.update(orderId, { status: "paid" });
    return result;
  } catch (error) {
    if (error instanceof PaymentDeclinedError) {
      logger.warn("Payment declined", { orderId, amount, reason: error.reason });
      throw new DomainError(`Payment declined for order ${orderId}`);
    }
    if (error instanceof NetworkError) {
      logger.error("Payment gateway unreachable", { orderId, amount, cause: error });
      throw new InfrastructureError("Payment service unavailable", { cause: error });
    }
    logger.error("Unexpected payment failure", { orderId, amount, error });
    throw error;
  }
}
```

## Reference

- [TypeScript Error Handling Best Practices](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [Node.js Error Handling Guide](https://nodejs.org/en/docs/guides/error-handling)
