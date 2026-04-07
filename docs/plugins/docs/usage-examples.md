# Docs Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the Docs plugin for maintaining living documentation.

## Examples

### Post-Implementation Documentation Update

**Scenario**: You have implemented a new feature and need to update project documentation.

```bash
# Implement the feature
> claude "implement user authentication with JWT tokens"

# Update documentation to reflect changes
> /update-docs
```

**Expected Flow**:

1. Plugin analyzes changed files and existing documentation
2. Identifies documentation gaps (missing API docs, outdated README)
3. Creates or updates relevant documentation
4. Validates examples and links

**Documentation Output**:

```markdown
## Documentation Updates Completed

### Files Updated
- README.md - Added authentication section to Quick Start
- docs/api/authentication.md - New file with JWT flow documentation
- src/auth/README.md - Module README with purpose and exports

### Major Changes
- Added authentication endpoint documentation
- Created troubleshooting section for common auth errors
- Updated environment variables documentation
```

### API Documentation After Adding Endpoints

**Scenario**: You have added new REST API endpoints and need to document them.

```bash
# Add new API endpoints
> claude "add /api/v2/products endpoint with CRUD operations"

# Update API documentation specifically
> /update-docs api
```

**Expected Flow**:

1. Plugin scans for API-related changes (routes, controllers, schemas)
2. Checks for existing OpenAPI/Swagger documentation
3. Updates or generates API reference documentation
4. Adds request/response examples

**API Documentation Generated**:

```markdown
## POST /api/v2/products

Create a new product.

### Request

```json
{
  "name": "Widget Pro",
  "price": 29.99,
  "category": "electronics"
}
```

### Response (201 Created)

```json
{
  "id": "prod_abc123",
  "name": "Widget Pro",
  "price": 29.99,
  "category": "electronics",
  "createdAt": "2025-01-15T10:30:00Z"
}
```

### Error Responses

| Status | Description |
|--------|-------------|
| 400 | Invalid request body |
| 401 | Missing or invalid authentication |
| 409 | Product with same name already exists |
```

### Module Documentation Update

**Scenario**: You have made significant changes to a module and need to update its documentation.

```bash
# Implement changes to payments module
> claude "add Stripe subscription support to payments module"

# Document the specific module
> /update-docs src/payments/
```

**Expected Flow**:

1. Plugin focuses on the specified directory
2. Analyzes module structure and exports
3. Updates module README with purpose and usage
4. Adds JSDoc comments for complex functions

**Module README Generated**:

```markdown
# Payments Module

**Purpose**: Handle all payment processing including one-time charges and recurring subscriptions via Stripe.

**Key Exports**:

- `createPayment(options)` - Process one-time payment
- `createSubscription(options)` - Start recurring subscription
- `cancelSubscription(subscriptionId)` - Cancel active subscription
- `getPaymentHistory(userId)` - Retrieve payment history

**Usage**:

```typescript
import { createSubscription } from './payments';

const subscription = await createSubscription({
  customerId: 'cus_123',
  priceId: 'price_monthly',
  metadata: { userId: 'user_456' }
});
```

See: [Payment Integration Guide](../../docs/guides/payments.md) for detailed setup.
```

### Full Project Documentation Audit

**Scenario**: Project documentation has become stale and needs a comprehensive update.

```bash
# Run full documentation audit and update
> /update-docs
```

**Expected Flow**:

1. Inventories all existing documentation
2. Checks freshness (files older than 6 months flagged)
3. Identifies duplications and inconsistencies
4. Prioritizes high-impact updates
5. Removes or consolidates outdated content

**Audit Output**:

```markdown
## Documentation Audit Results

### High-Impact Gaps Addressed
- Added missing Quick Start section to root README
- Created API authentication guide (was causing support questions)
- Added troubleshooting section for common errors

### Outdated Content Removed
- Removed deprecated v1 API documentation
- Consolidated duplicate setup instructions
- Archived obsolete architecture diagrams

### Automation Recommendations
- Consider adding OpenAPI generation for REST endpoints
- JSDoc coverage for business logic in src/services/

### Quality Metrics
- Links verified: 47 valid, 3 fixed, 2 removed
- Code examples tested: 12 passing
- Freshness: All critical docs updated within 30 days
```

### JSDoc Update for Complex Logic

**Scenario**: Business logic functions need documentation for maintainability.

```bash
# Update JSDoc comments for complex code
> /update-docs jsdoc
```

**Expected Flow**:

1. Identifies complex functions lacking documentation
2. Adds JSDoc with parameters, return types, and examples
3. Skips obvious/simple functions (getters, setters, utilities)
4. Focuses on business logic and integration points

**JSDoc Added**:

```typescript
/**
 * Calculates shipping cost based on destination, weight, and delivery speed.
 * Applies promotional discounts when applicable and validates against
 * carrier rate limits.
 *
 * @param order - Order details including items and destination
 * @param options - Shipping configuration options
 * @param options.carrier - Preferred carrier ('fedex' | 'ups' | 'usps')
 * @param options.speed - Delivery speed ('standard' | 'express' | 'overnight')
 * @returns Calculated shipping cost with breakdown
 * @throws ShippingError when destination is not serviceable
 *
 * @example
 * ```typescript
 * const cost = await calculateShipping(order, {
 *   carrier: 'fedex',
 *   speed: 'express'
 * });
 * console.log(cost.total); // 24.99
 * console.log(cost.breakdown); // { base: 15.99, fuel: 4.00, handling: 5.00 }
 * ```
 */
async function calculateShipping(
  order: Order,
  options: ShippingOptions
): Promise<ShippingCost>
```

### README Files Only

**Scenario**: Quick update to README files across the project.

```bash
# Update only README files
> /update-docs readme
```

**Expected Flow**:

1. Scans all README.md files in the project
2. Updates root README with current quick start
3. Creates module READMEs where missing
4. Ensures consistent structure across READMEs

**README Updates**:

```markdown
## READMEs Updated

### Root README.md
- Updated Quick Start with current setup steps
- Added link to new API documentation
- Refreshed status badges

### Module READMEs Created
- src/auth/README.md - Authentication module
- src/payments/README.md - Payment processing
- src/notifications/README.md - Notification services

### Module READMEs Updated
- src/database/README.md - Added migration instructions
- src/utils/README.md - Updated export list
```

## Integration with Other Plugins

### Complete Feature Development Workflow

```bash
# 1. Implement feature
> claude "add user preferences with theme and notification settings"

# 2. Reflect on implementation
> /reflexion:reflect

# 3. Write tests
> /write-tests

# 4. Review code
> /review-local-changes

# 5. Update documentation
> /update-docs

# 6. Commit everything
> /git:commit
```

### SDD Workflow Integration

```bash
# Complete Spec-Driven Development with docs
> /sdd:01-specify "user dashboard feature"
> /sdd:02-plan
> /sdd:03-tasks
> /sdd:04-implement
> /sdd:05-document  # Feature-specific docs

# Broader project documentation update
> /update-docs
```

### Documentation After Refactoring

```bash
# Perform refactoring
> claude "refactor authentication to use middleware pattern"

# Review the changes
> /review-local-changes

# Update affected documentation
> /update-docs src/auth/

# Save refactoring insights
> /reflexion:memorize "Authentication refactoring patterns"
```

### API Version Migration Documentation

```bash
# Implement API v2
> claude "migrate /api/users to v2 with breaking changes"

# Document the migration
> /update-docs api

# Add migration guide
> claude "create migration guide from v1 to v2 API"

# Validate documentation
> /update-docs
```

## Common Patterns

### When to Run Documentation Updates

| Scenario | Command | Focus |
|----------|---------|-------|
| After implementing feature | `/update-docs` | Full assessment |
| After adding API endpoints | `/update-docs api` | API documentation |
| After module changes | `/update-docs src/module/` | Module-specific |
| Periodic maintenance | `/update-docs` | Full audit |
| Before release | `/update-docs` | Comprehensive review |

### Documentation Priority Order

1. **Onboarding blockers** - Setup instructions, quick start
2. **API documentation** - Endpoint references, authentication
3. **Module READMEs** - Navigation and purpose
4. **Troubleshooting** - Common errors and solutions
5. **Architecture decisions** - When they affect usage
6. **JSDoc comments** - Complex business logic

### Signs Documentation Needs Updating

- Issues contain "how do I...?" questions
- Multiple conflicting sources of truth
- Setup instructions do not work
- API responses do not match documentation
- New features have no documentation
- Links return 404 errors
