# DDD Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the Domain-Driven Development plugin for establishing code quality standards and applying Clean Architecture principles.

## Examples


### Implementing a Feature with DDD Principles

**Scenario**: Building a user authentication service following Clean Architecture.

```bash
# Request implementation (software-architecture skill activates automatically)
claude "implement user authentication with email/password"
```

**Expected Output Structure**:

The AI will generate code following Clean Architecture layers:

```
src/
  domain/
    entities/
      User.ts              # Pure domain entity
      Credentials.ts       # Value object
    repositories/
      UserRepository.ts    # Repository interface
  application/
    use-cases/
      AuthenticateUser.ts  # Application business rules
      RegisterUser.ts
    services/
      TokenService.ts      # Application service interface
  infrastructure/
    repositories/
      PostgresUserRepository.ts  # Repository implementation
    services/
      JwtTokenService.ts         # Token service implementation
  interface/
    controllers/
      AuthController.ts    # HTTP interface
    dto/
      LoginRequest.ts      # Data transfer objects
      LoginResponse.ts
```

**Code Quality Applied**:

```typescript
// Domain Entity - No framework dependencies
// src/domain/entities/User.ts
export class User {
  private constructor(
    public readonly id: string,
    public readonly email: string,
    private passwordHash: string,
    public readonly createdAt: Date
  ) {}

  static create(email: string, passwordHash: string): User {
    return new User(
      crypto.randomUUID(),
      email,
      passwordHash,
      new Date()
    )
  }

  validatePassword(hash: string): boolean {
    return this.passwordHash === hash
  }
}
```

```typescript
// Use Case - Application business rules
// src/application/use-cases/AuthenticateUser.ts
export class AuthenticateUser {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly tokenService: TokenService,
    private readonly hashService: HashService
  ) {}

  async execute(credentials: Credentials): Promise<AuthResult> {
    const user = await this.userRepository.findByEmail(credentials.email)

    if (!user) {
      return { success: false, error: 'Invalid credentials' }
    }

    const isValid = await this.hashService.verify(
      credentials.password,
      user.passwordHash
    )

    if (!isValid) {
      return { success: false, error: 'Invalid credentials' }
    }

    const token = await this.tokenService.generate(user)

    return { success: true, token }
  }
}
```

### Refactoring Legacy Code to Clean Architecture

**Scenario**: Existing codebase has business logic mixed with controllers.

```bash
# Analyze current state
claude "analyze src/controllers/orderController.ts for architectural issues"
```

**AI Analysis Output**:
```
Architectural Issues Identified:

1. Business Logic in Controller (Violation: Separation of Concerns)
   - Lines 45-78: Order total calculation belongs in domain layer
   - Lines 102-134: Inventory check belongs in application layer

2. Direct Database Access (Violation: Dependency Inversion)
   - Lines 23-44: SQL queries directly in controller
   - Should use repository interface

3. Generic Naming (Violation: Ubiquitous Language)
   - `processOrder` should be `PlaceOrder` or `SubmitOrder`
   - `handleDiscount` should be `ApplyPromotionalDiscount`

Recommended Refactoring:
1. Extract Order entity to domain layer
2. Create PlaceOrderUseCase in application layer
3. Implement OrderRepository interface
4. Move database queries to PostgresOrderRepository
```

```bash
# Apply refactoring
claude "refactor orderController.ts following the recommended Clean Architecture structure"
```

### Library-First Decision Making

**Scenario**: Need to implement retry logic for API calls.

```bash
claude "implement retry logic for external API calls"
```

**Expected AI Response**:
```
Following library-first approach, I recommend using cockatiel for retry logic:

npm install cockatiel

Rationale:
- Mature, well-tested library with 500k+ weekly downloads
- Provides exponential backoff, circuit breaker, bulkhead patterns
- Type-safe with excellent TypeScript support
- More robust than custom implementation

Custom code would be justified if:
- You need domain-specific retry behavior
- Performance requirements exceed library capabilities
- You need to minimize dependencies in a critical path
```

```typescript
// Using cockatiel instead of custom retry logic
import { retry, handleAll, ExponentialBackoff } from 'cockatiel'

const retryPolicy = retry(handleAll, {
  maxAttempts: 3,
  backoff: new ExponentialBackoff()
})

export class ExternalApiClient {
  async fetchData(endpoint: string): Promise<ApiResponse> {
    return retryPolicy.execute(() => this.httpClient.get(endpoint))
  }
}
```

### Enforcing Naming Conventions

**Scenario**: Code review finds generic naming that violates DDD principles.

```bash
claude "rename utils/helpers.ts to follow domain-specific naming conventions"
```

**Before**:
```typescript
// utils/helpers.ts - 200 lines of unrelated functions
export function formatDate(date: Date): string { ... }
export function calculateTax(amount: number): number { ... }
export function validateEmail(email: string): boolean { ... }
export function generateOrderId(): string { ... }
export function parsePhoneNumber(phone: string): PhoneNumber { ... }
```

**After**:
```typescript
// domain/value-objects/DateFormatter.ts
export class DateFormatter {
  static toDisplayFormat(date: Date): string { ... }
  static toIsoFormat(date: Date): string { ... }
}

// domain/services/TaxCalculator.ts
export class TaxCalculator {
  constructor(private readonly taxRates: TaxRateProvider) {}
  calculate(amount: Money, jurisdiction: Jurisdiction): Money { ... }
}

// domain/value-objects/Email.ts
export class Email {
  private constructor(private readonly value: string) {}
  static create(email: string): Email | ValidationError { ... }
}

// domain/entities/Order.ts
export class Order {
  static generateId(): OrderId { ... }
}

// domain/value-objects/PhoneNumber.ts
export class PhoneNumber {
  static parse(input: string): PhoneNumber | ValidationError { ... }
}
```

### Setting Up a Microservice with Bounded Contexts

**Scenario**: Designing a new microservice that needs clear bounded context boundaries.

```bash


# Design the domain model
claude "design the domain model for a payment processing bounded context for payment microservice with Clean Architecture, bounded context for payment processing"
```

**Expected Domain Model**:
```
Payment Bounded Context

Entities:
- Payment (Aggregate Root)
- PaymentMethod
- Transaction

Value Objects:
- Money (amount, currency)
- PaymentStatus
- TransactionId
- CardDetails (last4, brand)

Domain Events:
- PaymentInitiated
- PaymentAuthorized
- PaymentCaptured
- PaymentFailed
- RefundRequested
- RefundCompleted

Repositories:
- PaymentRepository (interface)

Domain Services:
- PaymentProcessor
- FraudDetector

Application Use Cases:
- InitiatePayment
- CapturePayment
- ProcessRefund
- GetPaymentHistory
```

### Code Quality Review with DDD Standards

**Scenario**: Reviewing a pull request for architectural compliance.

```bash
# Review specific files
claude "review src/services/UserService.ts for Clean Architecture compliance"
```

**Expected Review Output**:
```
Clean Architecture Review: src/services/UserService.ts

Issues Found:

1. Layer Violation (Critical)
   Line 34: Direct database import in application layer
   - import { prisma } from '../db'
   - Should inject repository interface instead

2. Mixed Responsibilities (High)
   Lines 45-67: HTTP response formatting in service
   - Service should return domain objects
   - Controller handles HTTP formatting

3. Missing Domain Entity (Medium)
   Lines 78-92: User data handled as plain object
   - Create User entity with validation
   - Encapsulate business rules

4. Function Length (Low)
   createUser(): 67 lines
   - Extract validation to separate method
   - Extract notification to domain event

Suggested Refactoring:
1. Extract UserRepository interface
2. Move HTTP concerns to controller
3. Create User entity class
4. Split createUser into focused methods
```

## Integration Patterns

### With Reflexion for Continuous Improvement

```bash
# Implement feature with DDD
claude "implement order processing with Clean Architecture"

# Reflect on architectural decisions
/reflect architecture

# Save learnings
/memorize --section="Architecture Decisions"
```

### With SDD for Full Development Lifecycle

```bash

# Define
/brainstorm Add shopping cart feature
/add-task

# Plan specification
/plan-task

# Implementation (DDD skill active)
/implement-task

```

### With Code Review for Quality Gates

```bash
# Implement changes
claude "add payment processing integration"

# Review for DDD compliance
/review-local-changes

# The software-architecture skill ensures review checks:
# - Layer boundaries
# - Naming conventions
# - Separation of concerns
# - Repository pattern usage
```

## Anti-Pattern Detection Examples

### Detecting NIH Syndrome

```bash
claude "review src/utils/retry.ts for NIH anti-pattern"
```

**AI Response**:
```
NIH (Not Invented Here) Detection: src/utils/retry.ts

Finding: Custom retry implementation detected (145 lines)

Existing Solutions:
- cockatiel: Full-featured retry with circuit breaker
- p-retry: Simple promise retry
- async-retry: Configurable retry with backoff

Recommendation: Replace with cockatiel unless:
- Custom domain-specific retry behavior needed
- Performance requirements exceed library capabilities

Risk of Custom Implementation:
- Maintenance burden: 145 lines to test and maintain
- Edge cases: Library handles more scenarios
- Team knowledge: New developers must learn custom code
```

### Detecting Mixed Concerns

```bash
claude "check src/components/OrderForm.tsx for mixed concerns"
```

**AI Response**:
```
Mixed Concerns Detection: src/components/OrderForm.tsx

Issues:

1. Business Logic in UI Component (Lines 45-78)
   - Order total calculation
   - Tax computation
   - Discount application

   Move to: OrderCalculator domain service

2. Direct API Calls (Lines 102-134)
   - fetch() calls in component

   Move to: OrderRepository or use-case

3. Validation Logic (Lines 156-189)
   - Email validation
   - Phone validation

   Move to: Value objects (Email, PhoneNumber)

Recommended Structure:
- Component: UI rendering and user interaction only
- Use Case: Application flow orchestration
- Domain Services: Business calculations
- Value Objects: Validation and type safety
```
