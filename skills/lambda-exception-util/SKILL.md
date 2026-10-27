---
name: lambda-exception-util
description: Use when checked exceptions occur in Java lambdas and LambdaExceptionUtil is available.
---

# Lambda Exception Utility

## Contract

`com.celements.common.lambda.LambdaExceptionUtil` adapts lambdas that throw checked exceptions to standard Java functional interfaces. It uses a generic sneaky throw internally, but each wrapper declares `throws E`; the calling method must catch or declare the original checked exception. Do not wrap it in `RuntimeException` merely to satisfy a lambda signature.

Use a static import:

```java
import static com.celements.common.lambda.LambdaExceptionUtil.*;
```

## Wrappers

| Java interface | Throwing interface | Wrapper |
| --- | --- | --- |
| `Function<T, R>` | `ThrowingFunction<T, R, E>` | `rethrowFunction` |
| `Predicate<T>` | `ThrowingPredicate<T, E>` | `rethrowPredicate` |
| `Consumer<T>` | `ThrowingConsumer<T, E>` | `rethrowConsumer` |
| `BiConsumer<T, U>` | `ThrowingBiConsumer<T, U, E>` | `rethrowBiConsumer` |
| `Supplier<T>` | `ThrowingSupplier<T, E>` | `rethrowSupplier` |
| `Runnable` | `ThrowingRunnable<E>` | `rethrowRunnable` |

Each also has an overloaded `rethrow(...)` form. Prefer the named wrapper when overload resolution or generic inference is ambiguous.

## Usage

Declare the exception on the enclosing method:

```java
public List<String> render(List<Document> documents, String text)
    throws XWikiVelocityException {
  return documents.stream()
      .map(rethrowFunction(doc -> evaluateVelocityText(doc, text)))
      .collect(toList());
}
```

Or catch it outside the lambda operation:

```java
try {
  context.computeIfAbsent(XWIKI, rethrowSupplier(() -> wikiProvider.await(timeout)));
} catch (ExecutionException exc) {
  throw new ExecutionContextException("failed initializing XWiki", exc);
}
```

The compiler checks the exception where the wrapper is created, not where a stored functional interface is later executed. Keep wrapper creation and execution, including a stream terminal operation, in the same method or `try` block. Do not return or store the adapted interface for deferred execution.
