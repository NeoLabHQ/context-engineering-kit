---
title: Functional Core, Imperative Shell
paths:
  - "src/**/*"
impact: HIGH
---

# Functional Core, Imperative Shell

Keep business logic in pure functions that take inputs and return outputs with no side effects. Push all side effects -- database calls, HTTP requests, logging, file I/O, and state mutations -- to an outer "imperative shell" that orchestrates the pure core. Pure functions are deterministic: given the same inputs they always produce the same outputs. This makes them trivially testable without mocks, easy to reason about, and safe to compose and parallelize. When side effects are mixed into calculation logic, tests become slow and brittle (requiring database stubs, log spies, HTTP interceptors), bugs hide behind non-deterministic execution, and refactoring becomes dangerous because any change might alter when and how I/O occurs. Separate what to compute from how to execute it.

## Incorrect

Business calculation is tangled with logging, database reads, and persistence. Testing the pricing logic requires mocking the logger, database, and notification service.

```typescript
async function applySubscriptionRenewal(
  customerId: string,
  logger: Logger,
  db: Database,
  mailer: Mailer
): Promise<void> {
  const customer = await db.customers.findById(customerId);
  const plan = await db.plans.findById(customer.planId);

  // Pure calculation mixed with side effects
  let price = plan.basePrice;
  if (customer.loyaltyYears >= 3) {
    price = price * 0.85;
    logger.info(`Applied 15% loyalty discount for ${customerId}`);
  }
  if (customer.referralCount >= 5) {
    price = price - 10;
    logger.info(`Applied $10 referral credit for ${customerId}`);
  }
  const tax = price * customer.taxRate;
  const total = price + tax;

  await db.invoices.create({ customerId, total, tax });
  await mailer.send(customer.email, `Your renewal total is $${total}`);
  logger.info(`Renewal processed: ${customerId}, total: ${total}`);
}
```

## Correct

The pure core calculates the renewal price with no side effects. The imperative shell fetches data, calls the pure function, then performs all I/O. The core is testable with plain assertions and zero mocks.

```typescript
// Pure core — deterministic, no side effects, trivially testable
interface RenewalInput {
  basePrice: number;
  loyaltyYears: number;
  referralCount: number;
  taxRate: number;
}

interface RenewalResult {
  price: number;
  tax: number;
  total: number;
  appliedDiscounts: string[];
}

function calculateRenewal(input: RenewalInput): RenewalResult {
  const discounts: string[] = [];
  let price = input.basePrice;

  if (input.loyaltyYears >= 3) {
    price = price * 0.85;
    discounts.push("loyalty_15pct");
  }
  if (input.referralCount >= 5) {
    price = price - 10;
    discounts.push("referral_credit_10");
  }

  const tax = price * input.taxRate;
  return { price, tax, total: price + tax, appliedDiscounts: discounts };
}

// Imperative shell — orchestrates I/O around the pure core
async function processRenewal(
  customerId: string,
  db: Database,
  mailer: Mailer,
  logger: Logger
): Promise<void> {
  const customer = await db.customers.findById(customerId);
  const plan = await db.plans.findById(customer.planId);

  const result = calculateRenewal({
    basePrice: plan.basePrice,
    loyaltyYears: customer.loyaltyYears,
    referralCount: customer.referralCount,
    taxRate: customer.taxRate,
  });

  await db.invoices.create({ customerId, total: result.total, tax: result.tax });
  await mailer.send(customer.email, `Your renewal total is $${result.total}`);
  logger.info("Renewal processed", { customerId, ...result });
}
```

## Reference

- [Functional Core, Imperative Shell - Gary Bernhardt](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)
- [Boundaries - Gary Bernhardt (talk)](https://www.destroyallsoftware.com/talks/boundaries)
