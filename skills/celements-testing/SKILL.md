---
name: celements-testing
description: Use when writing or refactoring tests in Celements Java codebases, including Celements-based Progon code, especially JUnit and EasyMock tests built on com.celements.common.test.AbstractComponentTest for components, Spring beans, controllers, listeners, and services. Covers registerComponentMocks, getMock, createDefaultMock, replayDefault and verifyDefault, bean lookup, and unwrapping Spring AOP proxies when the goal is to test method logic rather than annotations.
---

# Celements Testing

## Overview

Prefer Celements component-style tests when the code under test depends on the Celements component container, XWiki-derived APIs, Spring wiring, or existing component mocks. Progon is Celements-based, so the same test guidance applies there. Keep the test focused on method behavior: search params, rights checks, conversion, exception mapping, and returned DTOs.

## When To Use

Use this skill when:

- the test should extend `com.celements.common.test.AbstractComponentTest`
- collaborators should be registered with `registerComponentMocks(...)` or `registerComponentMock(...)`
- the class under test is loaded from the Celements or Spring container
- the code uses EasyMock and should rely on `replayDefault()` and `verifyDefault()`
- the goal is direct method testing, not HTTP annotation or MVC-layer testing

Do not default to Spring's `MockMvc` or annotation tests unless the user explicitly asks to test the web layer.

## Dependencies And Libraries

The standard stack for these tests is:

- `junit:junit` for JUnit style `@Before` and `@Test`
- `org.easymock:easymock` for EasyMock expectations and mocks
- `com.celements:celements-shared-tests` for `AbstractComponentTest`

In many Celements modules and Celements-based Progon modules these arrive from the shared parent pom already. If `AbstractComponentTest`, EasyMock helpers, or the test harness classes are missing, first inspect the parent pom before adding duplicate module-level dependencies.

If the module does need explicit test dependencies, the minimal set is usually:

```xml
<dependency>
  <groupId>com.celements</groupId>
  <artifactId>celements-shared-tests</artifactId>
  <version>...</version>
  <scope>test</scope>
</dependency>
<dependency>
  <groupId>junit</groupId>
  <artifactId>junit</artifactId>
  <scope>test</scope>
</dependency>
<dependency>
  <groupId>org.easymock</groupId>
  <artifactId>easymock</artifactId>
  <scope>test</scope>
</dependency>
```

Use the version managed by the parent pom when available instead of duplicating it in the module.

Additional test-scope dependencies are module-specific. Inspect the parent pom and neighboring
tests before adding or duplicating them.

## Default Workflow

1. Extend `AbstractComponentTest`.
2. In `@Before`, register collaborators with `registerComponentMocks(...)`.
3. Register hinted or special components individually with `registerComponentMock(...)` when needed.
4. Load the real class under test from the container.
5. Access registered collaborators through `getMock(...)` inside each test.
6. Use `createDefaultMock(...)` for fixture/shared mocks and plain EasyMock `createMock(...)` for scenario-local mocks, especially multiple same-type instances.
7. Use `replayDefault()` before invoking the method and `verifyDefault()` after assertions; pass explicit `createMock(...)` instances to these calls.

## Core Patterns

### Registering dependencies

- Prefer `registerComponentMocks(...)` for the common set of collaborators.
- Use `registerComponentMock(...)` only when a test needs a single special registration, a named hint, or a prebuilt instance.
- Avoid a large block of private mock fields. Use `getMock(TheClass.class)` at the call site unless the same mock is reused heavily in helper methods.

### Loading the unit under test

- In tests extending `AbstractComponentTest`, use the parent-class helpers directly:
  `getBeanFactory()`, `registerComponentMocks(...)`, `getMock(...)`, `createDefaultMock(...)`,
  `replayDefault()`, and `verifyDefault()`.
- For controllers, listeners, beans, roles, and hinted components in `AbstractComponentTest`-based tests, use `getBeanFactory().getBean(...)`.
- For hinted lookups such as class definitions, use the bean-factory form, e.g. `getBeanFactory().getBean(MyClass.CLASS_DEF_HINT, ClassDefinition.class)`.
- Avoid static lookups in tests that extend `AbstractComponentTest`: neither
  `SpringContextProvider.getBeanFactory().getBean(...)` nor legacy
  `com.xpn.xwiki.web.Utils.getComponent(...)`.
- If the bean is returned as a Spring AOP proxy and the user wants unit tests for the method body, unwrap the proxy target before invoking methods.

Example:

```java
private ActorController controller;

@Before
public void prepareTest() throws Exception {
  registerComponentMocks(
      UserService.class,
      IRightsAccessFacadeRole.class,
      ExportUtilService.class,
      IModelAccessFacade.class,
      IOrgServiceRole.class,
      IOrgObjectServiceRole.class,
      ActorDtoConverter.class,
      ActorSearcher.class,
      SearchParamsBuilder.class,
      ProgonApiUtils.class);
  controller = getBeanTarget(ActorController.class);
}

@SuppressWarnings("unchecked")
private <T> T getBeanTarget(Class<T> beanClass) throws Exception {
  T bean = getBeanFactory().getBean(beanClass);
  if (bean instanceof Advised advised) {
    return (T) advised.getTargetSource().getTarget();
  }
  return bean;
}
```

### Writing expectations

- Use `getMock(...)` for registered collaborators.
- Use `createDefaultMock(...)` for fixture or shared collaborators that naturally belong to the test setup and should be replayed and verified by plain `replayDefault()` and `verifyDefault()`.
- Use plain EasyMock `createMock(...)` for scenario-local mocks, especially when a test needs multiple instances of the same type or the mock is only meaningful inside one test method. Pass those mocks explicitly to `replayDefault(mock1, mock2)` and `verifyDefault(mock1, mock2)`.
- Do not convert shared collaborators to explicit mocks just because they are manually registered as Spring beans; if they are part of the fixture, keeping them in the default mock set is clearer.
- Keep expectations local to the scenario. Avoid a large shared fixture unless it removes real duplication.

Example:

```java
expect(getMock(SearchParamsBuilder.class).buildSearchParams(same(dto)))
    .andReturn(params);
expect(getMock(IOrgServiceRole.class).getOrgSpaceRef(eq(OrgType.COMPANY), isNull()))
    .andReturn(companySpace);
expect(getMock(IRightsAccessFacadeRole.class).hasAccessLevel(companySpace, EAccessLevel.VIEW))
    .andReturn(false);

replayDefault();
assertThrows(ForbiddenException.class, () -> controller.searchActors(dto));
verifyDefault();
```

## Best Practices

- Name JUnit setup methods `prepareTest`.
- Name test methods with the `test_...` convention.
- Test the public method directly. Do not add framework setup that is unrelated to the behavior under test.
- Keep assertions on observable outcomes: returned DTOs, response status, thrown exceptions, or interactions that define behavior.
- For controller tests, cover both the happy path and the main denial or not-found branches.
- If the code under test depends on named components such as configuration sources, register the hinted component explicitly.
- In `AbstractComponentTest`-based tests, use parent helpers such as `getBeanFactory()` before any
  direct container utility.
- Reuse real infrastructure only where the test harness expects it. In `AbstractComponentTest`, core infrastructure like `org.xwiki.context.Execution` may be safer left as the registered component than replaced with a standalone mock.
- When the project already has similar Celements tests, follow the local house style before introducing a new pattern.

## Common Pitfalls

- Loading a proxied Spring bean and then accidentally testing security interceptors instead of the method body.
- Keeping one private field per mock instead of using `registerComponentMocks(...)` plus `getMock(...)`.
- Mixing plain `replay(...)` and `verify(...)` calls with `replayDefault()` and `verifyDefault()` without a reason.
- Manually constructing the class under test when container wiring is part of what should be exercised.
- Testing annotations or framework metadata when the user only asked for unit tests of the method logic.

## Fast Checklist

- `AbstractComponentTest`
- `registerComponentMocks(...)` first
- prefer parent helpers from `AbstractComponentTest`
- use the parent `getBeanFactory().getBean(...)` helper for all component lookups
- unwrap `Advised` beans when avoiding annotation testing
- `getMock(...)` for registered collaborators
- `createDefaultMock(...)` for fixture/shared collaborators
- `createMock(...)` for multiple same-type or purely scenario-local mocks
- pass explicit mocks to `replayDefault(...)` and `verifyDefault(...)`
- name setup methods `prepareTest`
- name test methods `test_...`
