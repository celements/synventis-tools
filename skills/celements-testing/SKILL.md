---
name: celements-testing
description: Use for Celements or Progon JUnit and EasyMock tests involving the component container, XWiki APIs, Spring wiring, component mocks, or AbstractComponentTest.
---

# Celements Testing

Use `com.celements.common.test.AbstractComponentTest` when a Celements or Progon test depends on the component container, XWiki APIs, Spring wiring, or component mocks. Test public method behavior directly; use `MockMvc` or annotation tests only when the requested subject is the HTTP or MVC layer.

The usual test dependencies are `junit:junit`, `org.easymock:easymock`, and `com.celements:celements-shared-tests`. Inspect the parent pom and neighboring tests before adding module dependencies; use parent-managed versions and add only missing test-scope artifacts.

## Workflow

1. Extend `AbstractComponentTest`.
2. Register common collaborators with `registerComponentMocks(...)` in the `@Before` method `prepareTest`.
3. Register hinted or prebuilt components with `registerComponentMock(...)`.
4. Load the class under test through `getBeanFactory().getBean(...)`.
5. Retrieve registered collaborators with `getMock(...)` in each test.
6. Use `createDefaultMock(...)` for shared fixture mocks and `createMock(...)` for scenario-local mocks.
7. Use `replayDefault(...)` and `verifyDefault(...)`, passing scenario-local mocks as arguments.

Name tests `test_...` unless the project has stricter conventions.

## Components And Lookups

Load controllers, listeners, services, roles, and hinted components through the inherited `getBeanFactory().getBean(...)`. For example, use `getBeanFactory().getBean(MyClass.CLASS_DEF_HINT, ClassDefinition.class)` for a hinted class definition. Do not use `SpringContextProvider.getBeanFactory().getBean(...)` or `com.xpn.xwiki.web.Utils.getComponent(...)` in these tests.

Load the class under test from the container when its wiring matters instead of constructing it manually. Keep harness infrastructure such as the registered `org.xwiki.context.Execution` unless the scenario requires a replacement.

## Mock Lifecycle

Use `createMock(...)` when a test needs several mocks of the same type. Manual Spring registration does not add such mocks to the default lifecycle, so pass them explicitly to `replayDefault(mock1, mock2)` and `verifyDefault(mock1, mock2)`. Do not mix plain `replay(...)` or `verify(...)` with the default lifecycle without a specific reason.

Keep expectations in the test that uses them. Call `replayDefault()` before invoking the method and `verifyDefault()` after the assertions. Assert observable results such as DTOs, response status, exceptions, and behavior-defining interactions. Controller tests should cover the successful path and the main denial or not-found branches.

## Spring Proxies

If Spring returns an AOP proxy but the test concerns the method body rather than security or annotations, unwrap only the target:

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
