---
name: lambda-exception-util
description: Use when handling checked exceptions within Java streams, optionals, or lambda expressions in Celements or Progon code, using com.celements.common.lambda.LambdaExceptionUtil to sneakily throw checked exceptions while still enforcing compile-time checked exception handling at the caller/outer scope.
---

# Lambda Exception Utility

## Overview

`com.celements.common.lambda.LambdaExceptionUtil` is a utility designed to simplify handling checked exceptions inside Java lambdas. Standard Java functional interfaces (like `Function`, `Predicate`, `Consumer`, etc.) do not allow throwing checked exceptions. `LambdaExceptionUtil` resolves this by wrapping throwing lambdas and using a generics-based "sneaky throw" pattern to bypass the compiler check inside the lambda, while still declaring the throws signature on the wrapper method to enforce compile-time exception handling at the caller's outer scope.

## Core API & Throwing Interfaces

`LambdaExceptionUtil` defines several `@FunctionalInterface` matching Java's standard functional interfaces, but allowing exceptions:

| Standard Interface | Throwing Variant | Utility Wrapper Method |
| :--- | :--- | :--- |
| `java.util.function.Function<T, R>` | `ThrowingFunction<T, R, E>` | `rethrowFunction` or `rethrow` |
| `java.util.function.Predicate<T>` | `ThrowingPredicate<T, E>` | `rethrowPredicate` or `rethrow` |
| `java.util.function.Consumer<T>` | `ThrowingConsumer<T, E>` | `rethrowConsumer` or `rethrow` |
| `java.util.function.BiConsumer<T, U>` | `ThrowingBiConsumer<T, U, E>` | `rethrowBiConsumer` or `rethrow` |
| `java.util.function.Supplier<T>` | `ThrowingSupplier<T, E>` | `rethrowSupplier` or `rethrow` |
| `java.lang.Runnable` | `ThrowingRunnable<E>` | `rethrowRunnable` or `rethrow` |

## How to Import

Always use static imports for concise code:

```java
import static com.celements.common.lambda.LambdaExceptionUtil.*;
```

## Detailed Usage Patterns

### 1. Mapping with Checked Exceptions (`Function`)
When using `Stream.map` or `Optional.map` with a method that throws a checked exception:

**Standard Java (Verbose/Boilerplate):**
```java
List<String> results = documents.stream()
    .map(doc -> {
      try {
        return evaluateVelocityText(doc, text); // Throws XWikiVelocityException
      } catch (XWikiVelocityException e) {
        throw new RuntimeException(e);
      }
    })
    .collect(toList());
```

**With LambdaExceptionUtil:**
```java
// The enclosing method MUST declare: throws XWikiVelocityException
List<String> results = documents.stream()
    .map(rethrowFunction(doc -> evaluateVelocityText(doc, text)))
    .collect(toList());
```

### 2. Filtering with Checked Exceptions (`Predicate`)
When using `Stream.filter` with a predicate that checks a condition throwing a checked exception:

```java
// The enclosing method MUST declare: throws ClassNotFoundException
List<String> classes = classNames.stream()
    .filter(rethrowPredicate(className -> Class.forName(className) != null))
    .collect(toList());
```

### 3. Iterating/Consuming with Checked Exceptions (`Consumer`)
When executing side-effects inside `Stream.forEach` or `Iterable.forEach`:

```java
// The enclosing method MUST declare: throws ClassNotFoundException
classNames.forEach(rethrowConsumer(Class::forName));
```

### 4. Supplies and Computations (`Supplier`)
When loading resource values inside a container or context fallback (e.g. `computeIfAbsent`):

```java
public void initialize(ExecutionContext context) throws ExecutionContextException {
  try {
    // The supplier throws ExecutionException, caught by the enclosing try-catch
    context.computeIfAbsent(XWIKI, rethrow(() -> context.get(NO_AWAIT).orElse(false)
        ? wikiProvider.get().orElse(null)
        : wikiProvider.await(Duration.ofHours(1))));
  } catch (ExecutionException xwe) {
    throw new ExecutionContextException("failed initializing XWiki", xwe);
  }
}
```

### 5. Running Code Blocks (`Runnable`)
For throwing runnable blocks (e.g. background threads or custom runner closures):

```java
// The enclosing method MUST declare: throws ClassNotFoundException
rethrowRunnable(() -> Class.forName(Object.class.getName())).run();
```

---

## Best Practices

### 1. Resolve Compiler Ambiguity by Using Specific Names
While `rethrow(...)` is overloaded for all functional types, the Java compiler's type inference may occasionally fail or resolve to the wrong overload if the compiler cannot deduce the argument type.
* **Tip:** If the compiler complains about types, use the specific named wrapper methods:
  * Use `rethrowFunction(...)` instead of `rethrow(...)` for mappings.
  * Use `rethrowPredicate(...)` instead of `rethrow(...)` for filters.
  * Use `rethrowConsumer(...)` instead of `rethrow(...)` for iteration.
  * Use `rethrowSupplier(...)` instead of `rethrow(...)` for suppliers.
  * Use `rethrowRunnable(...)` instead of `rethrow(...)` for runnables.

### 2. Declare Exceptions on the Enclosing Method
Because `LambdaExceptionUtil` wrapper methods declare `throws E`, they enforce static compiler checks on the calling block. You **must** either:
- Add the thrown checked exception to your enclosing method's `throws` clause.
- Catch the specific checked exception at the caller scope (outside the stream/lambda).

### 3. Do Not Wrap in RuntimeException Manually
Avoid wrapping exceptions in `RuntimeException` just to bypass lambda limits when `LambdaExceptionUtil` can preserve the exact class of the checked exception, leading to much cleaner error handling and stack traces.

## Common Pitfalls

- **Separating wrapper creation from execution:** The checked-exception contract exists only at the rethrow* call. Do not return or store the functional interface for later execution. E.g. with streams, keep the terminal operation inside the same try-block or method.
- **Compiler type resolution failure:** Using generic `rethrow(...)` with an implicit parameter list that makes it hard for the Java compiler to infer the functional interface type. Prefer `rethrowFunction` or other explicit wrappers.
- **Forgetting caller-level exception handling:** Assuming that since it's a lambda, you don't need to handle the exception. You still must declare or catch it at the enclosing method scope.


