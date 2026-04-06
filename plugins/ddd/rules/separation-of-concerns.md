---
title: Enforce Separation of Concerns Between Layers
paths:
  - "src/**/*"
impact: HIGH
---

# Enforce Separation of Concerns Between Layers

Do NOT mix business logic with UI components or place database queries directly in controllers. Each architectural layer must have a single responsibility: controllers handle HTTP concerns, services encapsulate business logic, and repositories manage data access. Violating these boundaries creates tightly coupled code that is difficult to test, refactor, and reason about. When business rules live inside controllers, they cannot be reused across different entry points (API, CLI, events) and changes to infrastructure leak into domain logic. Maintain clear boundaries between contexts by delegating work through well-defined interfaces rather than inlining cross-cutting concerns.

## Critical principles

- Do NOT mix business logic with UI components
- Keep database queries out of controllers
- Maintain clear boundaries between contexts
- Ensure proper separation of responsibilities

## Incorrect

The controller mixes HTTP handling, business logic, and database queries in a single function, making it impossible to reuse or test the business rules independently.

```typescript
// OrderController.ts — everything in one place
import { db } from "../database";

export class OrderController {
  async createOrder(req: Request, res: Response) {
    const { items, customerId } = req.body;

    // Database query directly in controller
    const customer = await db.query("SELECT * FROM customers WHERE id = $1", [customerId]);
    if (!customer) {
      return res.status(404).json({ error: "Customer not found" });
    }

    // Business logic mixed into controller
    let total = 0;
    for (const item of items) {
      const product = await db.query("SELECT * FROM products WHERE id = $1", [item.productId]);
      total += product.price * item.quantity;
    }
    if (total > 10000) {
      total = total * 0.9; // 10% discount for large orders
    }

    // More database queries inline
    const order = await db.query(
      "INSERT INTO orders (customer_id, total) VALUES ($1, $2) RETURNING *",
      [customerId, total]
    );

    return res.status(201).json(order);
  }
}
```

## Correct

The controller delegates to a service for business logic and a repository for data access. Each layer has a single responsibility and can be tested and reused independently.

```typescript
// OrderController.ts — handles HTTP only
export class OrderController {
  constructor(private orderService: OrderService) {}

  async createOrder(req: Request, res: Response) {
    const { items, customerId } = req.body;
    const order = await this.orderService.createOrder(customerId, items);
    return res.status(201).json(order);
  }
}

// OrderService.ts — business logic only
export class OrderService {
  constructor(
    private customerRepo: CustomerRepository,
    private productRepo: ProductRepository,
    private orderRepo: OrderRepository
  ) {}

  async createOrder(customerId: string, items: OrderItem[]): Promise<Order> {
    const customer = await this.customerRepo.findById(customerId);
    if (!customer) {
      throw new NotFoundError("Customer not found");
    }

    const total = await this.calculateTotal(items);
    return this.orderRepo.create({ customerId, total });
  }

  private async calculateTotal(items: OrderItem[]): Promise<number> {
    let total = 0;
    for (const item of items) {
      const product = await this.productRepo.findById(item.productId);
      total += product.price * item.quantity;
    }
    return total > 10000 ? total * 0.9 : total;
  }
}

// OrderRepository.ts — data access only
export class OrderRepository {
  async create(data: CreateOrderData): Promise<Order> {
    return db.query(
      "INSERT INTO orders (customer_id, total) VALUES ($1, $2) RETURNING *",
      [data.customerId, data.total]
    );
  }
}
```

## Reference

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
