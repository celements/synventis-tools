---
name: celements-testing
description: Use when writing Celements Java tests with AbstractComponentTest and EasyMock.
---

# Celements Testing

Use `AbstractComponentTest` when the unit depends on Celements component wiring, XWiki APIs, Spring beans, or registered component mocks. Test public method behavior directly; use MVC tooling only when the web layer itself is under test.

## Setup

1. Extend `com.celements.common.test.AbstractComponentTest`.
2. Register common collaborators with `registerComponentMocks(...)`.
3. Use `registerComponentMock(...)` for a hinted or prebuilt component.
4. Load the real unit with the inherited `getBeanFactory().getBean(...)`.
5. Set expectations, call `replayDefault()`, invoke the unit, assert, then call `verifyDefault()`.

Use the parent POM's managed test dependencies. Add `celements-shared-tests`, JUnit, or EasyMock to the module only when they are not inherited.

## Mock Selection

- Use `getMock(Type.class)` for registered collaborators.
- Use `createDefaultMock(...)` for shared fixture mocks handled by `replayDefault()` and `verifyDefault()`.
- Use EasyMock `createMock(...)` for scenario-local or multiple same-type mocks; pass them explicitly to `replayDefault(mock)` and `verifyDefault(mock)`.
- Keep expectations local to the test unless shared setup removes meaningful duplication.

Do not replace core harness infrastructure such as `Execution` with standalone mocks unless the test requires it.

## Bean Lookup And Proxies

Use inherited container helpers, not static `SpringContextProvider` or `Utils.getComponent(...)` lookup. For hinted components:

```java
ClassDefinition classDef = getBeanFactory()
    .getBean(MyClass.CLASS_DEF_HINT, ClassDefinition.class);
```

When a Spring AOP proxy would test interceptors rather than the requested method logic, unwrap its target:

```java
@SuppressWarnings("unchecked")
private <T> T getBeanTarget(Class<T> beanClass) throws Exception {
  T bean = getBeanFactory().getBean(beanClass);
  if (bean instanceof Advised advised) {
    return (T) advised.getTargetSource().getTarget();
  }
  return bean;
}
```

Keep the proxy when annotation or interceptor behavior is part of the test.

## Conventions

- Name setup methods `prepareTest` and tests `test_...`.
- Assert observable results and contract-defining interactions.
- Cover the happy path and primary denial, not-found, or exception branch.
- Follow nearby Celements tests before introducing a new pattern.
- Do not mix plain EasyMock replay/verify calls with default helpers without a reason.
- Do not construct the unit manually when container wiring is relevant.
- Separate the replay/verify block with empty lines from the arrange and assert blocks for visual clarity.
