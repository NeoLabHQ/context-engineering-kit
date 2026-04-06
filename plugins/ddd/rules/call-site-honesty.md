---
title: Call-Site Honesty for Logging
paths:
  - "src/**/*"
impact: MEDIUM
---

# Call-Site Honesty for Logging

Logging calls must be visible at the call site, not buried inside utility functions. When a side effect like logging is wrapped in a helper such as `logResult()`, the reader cannot tell what is being logged, in what format, or to which logger without jumping into the implementation. This turns a transparent operation into an opaque one.

Instead of wrapping `logger.log()` inside helper functions, keep the logging call explicit and use pure functions only for formatting the data. The pure formatting function (`formatResult`) is a mechanism -- it transforms data deterministically with no side effects. The logging call (`logger.log`) is a policy decision -- it determines that a side effect occurs, what message is recorded, and where it goes. Policy belongs at the call site where the reader can see it. Mechanisms can be extracted into helpers because they hide no decisions, only computation.

## Incorrect

The logging side effect is hidden behind `logResult()`. The reader cannot see what is logged, what format is used, or which logger is invoked without opening the helper.

```typescript
const result = performProcess(param)
logResult(result)  // what does this log? where? what format? hidden behind abstraction
```

## Correct

The logging call is explicit at the call site. The reader sees the logger, the message, and the format. `formatResult` is a pure function (mechanism), while `logger.log` is the visible side effect (policy).

```typescript
const result = performProcess(param)
logger.log('Result of execution', formatResult(result))  // visible: what's logged, the format, the logger
```

