---
title: Use Domain-Specific Names Instead of Generic Module Names
paths:
  - "**/*"
  - "**/*"
impact: HIGH
---

# Use Domain-Specific Names Instead of Generic Module Names

Avoid generic module names like `utils`, `helpers`, `common`, and `shared`. These names attract unrelated functions, creating grab-bag files with no cohesion. Use domain-specific names that reflect the bounded context and the module's single responsibility -- names like `OrderCalculator`, `UserAuthenticator`, or `InvoiceGenerator` make purpose immediately clear and enforce cohesion by design.

Generic names signal missing domain analysis. When a developer reaches for `utils.ts`, it usually means the function belongs in a domain module that has not been identified yet. Naming modules after their domain concept prevents them from becoming dumping grounds and keeps each module focused on a single, clear purpose.

## Critical princeples

- Follow domain-driven design and ubiquitous language
- **AVOID** generic names: `utils`, `helpers`, `common`, `shared`
- **USE** domain-specific names: `OrderCalculator`, `UserAuthenticator`, `InvoiceGenerator`
- Follow bounded context naming patterns
- Each module should have a single, clear purpose

## Incorrect

Generic module names attract unrelated functions, making the file a dumping ground with no cohesion or clear ownership.

```typescript
// utils.ts — grab-bag of unrelated functions
export function calculateOrderTotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

export function formatUserDisplayName(user: User): string {
  return `${user.firstName} ${user.lastName}`;
}

export function generateInvoiceNumber(): string {
  return `INV-${Date.now()}`;
}
```

Generic Naming Anti-Patterns:
- `utils.js` with 50 unrelated functions
- `helpers/misc.js` as a dumping ground
- `common/shared.js` with unclear purpose

## Correct

Each function lives in a module named after its bounded context, enforcing single responsibility and making purpose self-documenting.

```typescript
// order-calculator.ts — all order pricing logic
export function calculateOrderTotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// user-display.ts — user presentation formatting
export function formatUserDisplayName(user: User): string {
  return `${user.firstName} ${user.lastName}`;
}

// invoice-generator.ts — invoice creation logic
export function generateInvoiceNumber(): string {
  return `INV-${Date.now()}`;
}
```

## Reference

- [Domain-Driven Design: Tackling Complexity in the Heart of Software](https://www.domainlanguage.com/ddd/) — Eric Evans
- Source: `plugins/ddd/skills/software-architecture/SKILL.md` — Naming Conventions and Generic Naming Anti-Patterns
