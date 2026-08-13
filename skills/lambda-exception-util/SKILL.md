---
name: lambda-exception-util
description: Use in Celements/Progon when a checked exception must pass through a Java lambda using LambdaExceptionUtil.
---

# Lambda Exception Utility

`com.celements.common.lambda.LambdaExceptionUtil` adapts checked-exception lambdas to standard Java functional interfaces. It sneaky-throws inside the lambda while requiring the caller to catch or declare the checked exception.

Use static imports:

```java
import static com.celements.common.lambda.LambdaExceptionUtil.*;
```

## Wrappers

| Lambda | Wrapper |
| --- | --- |
| `ThrowingFunction` | `rethrowFunction` |
| `ThrowingPredicate` | `rethrowPredicate` |
| `ThrowingConsumer` | `rethrowConsumer` |
| `ThrowingBiConsumer` | `rethrowBiConsumer` |
| `ThrowingSupplier` | `rethrowSupplier` |
| `ThrowingRunnable` | `rethrowRunnable` |

`rethrow(...)` is overloaded for all variants. Prefer the explicit name when type inference is ambiguous.

```java
List<String> results = documents.stream()
    .map(rethrowFunction(doc -> evaluateVelocityText(doc, text)))
    .toList();
```

The enclosing method must declare or catch the exception thrown by `evaluateVelocityText`.

## Rules

- Catch or declare the checked exception outside the lambda or stream.
- Keep wrapper creation and execution in the same exception-handling scope; do not store the adapted functional interface for later execution.
- Do not wrap the exception in `RuntimeException` merely to satisfy a functional interface.
- Keep a stream terminal operation inside the surrounding `try` block when it can trigger the exception.
