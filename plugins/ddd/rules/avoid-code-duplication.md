---
title: Avoid Code Duplication — Function, Logic, Concept, and Pattern
paths:
  - "src/**/*"
impact: HIGH
---

# Avoid Code Duplication — Function, Logic, Concept, and Pattern

- Do NOT duplicate functions, business logic, domain concepts, or behavioral patterns. 
- Apply DRY (Hunt & Thomas): "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system." 
- Allways extract on the third occurrence (Fowler's Rule of Three).

## Incorrect — Function Duplication

Identical bodies copy-pasted across modules.

```typescript
// user-repository.ts
function findUserById(id: string): Promise<User | null> {
  return db.collection('users').findOne({ _id: id });
}

// product-repository.ts — identical body, different name
function findProductById(id: string): Promise<Product | null> {
  return db.collection('products').findOne({ _id: id });
}
```

## Correct — Function Duplication

Extract a generic function; callers specify only what differs.

```typescript
// repository.ts
function findById<T>(collection: string, id: string): Promise<T | null> {
  return db.collection(collection).findOne({ _id: id });
}

const findUserById = (id: string) => findById<User>('users', id);
const findProductById = (id: string) => findById<Product>('products', id);
```

## Incorrect — Logic Duplication

Same business rule in three services with different variable names. More subtle than function duplication — code looks different but encodes the same decision. When thresholds change, missed sites silently drift.

```typescript
// order-service.ts
function calculateOrderDiscount(order: Order): number {
  if (order.total > 500) return order.total * 0.1;
  if (order.total > 200) return order.total * 0.05;
  return 0;
}

// invoice-service.ts — same rule, different names and types
function getInvoiceDiscount(invoice: Invoice): number {
  if (invoice.amount > 500) return invoice.amount * 0.1;
  if (invoice.amount > 200) return invoice.amount * 0.05;
  return 0;
}

// report-service.ts — same thresholds embedded in a reduce
function getDiscountedRevenue(transactions: Transaction[]): number {
  return transactions.reduce((sum, t) => {
    const discount = t.amount > 500 ? 0.1 : t.amount > 200 ? 0.05 : 0;
    return sum + t.amount * (1 - discount);
  }, 0);
}
```

## Correct — Logic Duplication

One domain function owns the rule. Changing thresholds happens in exactly one place.

```typescript
// pricing.ts — single source of truth
function getDiscountRate(amount: number): number {
  if (amount > 500) return 0.1;
  if (amount > 200) return 0.05;
  return 0;
}

// order-service.ts
const discount = order.total * getDiscountRate(order.total);

// invoice-service.ts
const discount = invoice.amount * getDiscountRate(invoice.amount);

// report-service.ts
const revenue = transactions.reduce(
  (sum, t) => sum + t.amount * (1 - getDiscountRate(t.amount)), 0
);
```

## Incorrect — Concept Duplication

The concept "active user" is scattered as ad-hoc conditions across modules. Most dangerous form — code differs so tools will not flag it, yet every instance must stay in sync. Missed sites become silent bugs.

```typescript
// auth-middleware.ts
if (user.status === 'active' && !user.deletedAt && user.emailVerified) {
  allowAccess(user);
}

// notification-service.ts — subtly different expression
if (user.status === 'active' && user.deletedAt === null && user.emailVerified === true) {
  sendNotification(user);
}

// billing-service.ts — concept drift: forgot emailVerified
if (user.status === 'active' && !user.deletedAt) {
  chargeSubscription(user);
}

// analytics-service.ts — further drift: added own interpretation
if (user.status === 'active' && !user.deletedAt && user.lastLoginAt) {
  trackActiveUser(user);
}
```

## Correct — Concept Duplication

Name the concept in a single predicate. When requirements change, update one function.

```typescript
// user-status.ts — authoritative definition
function isActiveUser(user: User): boolean {
  return user.status === 'active' && !user.deletedAt && user.emailVerified;
}

// auth-middleware.ts
if (isActiveUser(user)) allowAccess(user);

// notification-service.ts
if (isActiveUser(user)) sendNotification(user);

// billing-service.ts — now correct
if (isActiveUser(user)) chargeSubscription(user);

// analytics-service.ts — shared definition + own criteria
if (isActiveUser(user) && user.lastLoginAt) trackActiveUser(user);
```

## Incorrect — Pattern Duplication

Same fetch-validate-transform pattern repeated per API resource.

```typescript
// user-api.ts
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new ApiError(`Failed: ${res.status}`);
  return { ...(await res.json()), fetchedAt: new Date() };
}

// product-api.ts — same pattern, different resource
async function fetchProduct(id: string): Promise<Product> {
  const res = await fetch(`/api/products/${id}`);
  if (!res.ok) throw new ApiError(`Failed: ${res.status}`);
  return { ...(await res.json()), fetchedAt: new Date() };
}
```

## Correct — Pattern Duplication

Extract the recurring pattern into a generic abstraction.

```typescript
// api-client.ts
async function fetchResource<T>(resource: string, id: string): Promise<T> {
  const res = await fetch(`/api/${resource}/${id}`);
  if (!res.ok) throw new ApiError(`Failed: ${res.status}`);
  return { ...(await res.json()), fetchedAt: new Date() };
}

const user = await fetchResource<User>('users', id);
const product = await fetchResource<Product>('products', id);
```

## Reference

- [The Pragmatic Programmer — Hunt & Thomas](https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/) — DRY principle
- [Refactoring — Martin Fowler](https://refactoring.com/) — Rule of Three
- [Extreme Programming Explained — Kent Beck](https://www.oreilly.com/library/view/extreme-programming-explained/0201616416/) — Once and Only Once (OAOO)
