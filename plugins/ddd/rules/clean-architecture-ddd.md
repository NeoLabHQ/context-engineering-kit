---
title: Separate Domain Logic from Infrastructure
paths:
  - "src/**/*"
impact: HIGH
---

# Separate Domain Logic from Infrastructure

Keep business logic in pure domain and use case layers, free of framework or infrastructure dependencies. When domain logic is coupled to controllers, ORMs, or HTTP libraries, it becomes untestable in isolation, impossible to reuse across delivery mechanisms, and fragile to infrastructure changes. Define domain entities that model business rules with no imports from framework or database packages. Implement use cases as classes that depend on abstract repository interfaces, not concrete database clients. Let the infrastructure layer implement those interfaces and inject them at composition time. This dependency inversion ensures the domain drives the architecture rather than the framework dictating how business rules are organized.

## Critical Clean Architecture & DDD Principles

- Separate domain entities from infrastructure concerns
- Keep business logic independent of frameworks
- Define use cases clearly and keep them isolated
- Avoid code duplication through creation of reusable functions and modules

## Incorrect

Business logic is embedded directly in the HTTP handler, coupled to the web framework and database client. Testing requires spinning up the full server and database.

```typescript
import express from "express";
import { PrismaClient } from "@prisma/client";

const app = express();
const prisma = new PrismaClient();

app.post("/orders", async (req, res) => {
  const { customerId, items } = req.body;

  // Business rule mixed into the controller
  const total = items.reduce((sum, i) => sum + i.price * i.qty, 0);
  const discount = total > 100 ? total * 0.1 : 0;

  const order = await prisma.order.create({
    data: { customerId, total: total - discount, items: { create: items } },
  });

  res.json(order);
});
```

Poor Architectural Choices:
- Mixing business logic with UI components
- Database queries directly in controllers
- Lack of clear separation of concerns

## Correct

Domain logic lives in a framework-free use case that depends on an abstract repository. The controller is a thin adapter that delegates to the use case.

```typescript
// domain/order.ts — pure business logic, no framework imports
export function calculateOrderTotal(items: OrderItem[]): number {
  const subtotal = items.reduce((sum, i) => sum + i.price * i.qty, 0);
  const discount = subtotal > 100 ? subtotal * 0.1 : 0;
  return subtotal - discount;
}

// application/create-order.ts — use case depends on abstraction
export class CreateOrder {
  constructor(private readonly orders: OrderRepository) {}

  async execute(customerId: string, items: OrderItem[]): Promise<Order> {
    const total = calculateOrderTotal(items);
    return this.orders.save({ customerId, total, items });
  }
}

// infrastructure/controller.ts — thin adapter
app.post("/orders", async (req, res) => {
  const order = await createOrder.execute(req.body.customerId, req.body.items);
  res.json(order);
});
```

## Reference

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
