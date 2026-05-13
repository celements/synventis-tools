---
name: celements-component
description: Use when working in Celements code, including Celements-based Progon code, that touches the mixed XWiki component and Spring bean system, especially when refactoring legacy org.xwiki.component.annotation.Component classes to Spring @Component/@Service beans, reviewing ComponentManager/Utils.getComponent/BeanFactory lookups, handling @ComponentRole/@Requirement/@Inject, component hints, META-INF/components.txt, or diagnosing bean wiring and lookup pitfalls.
---

# Celements Component

## Overview

Celements runs a hybrid component system: legacy XWiki components are loaded into the Spring bean factory, while legacy XWiki lookup APIs are shimmed back onto Spring. Use the actual bridge code as the source of truth before judging whether a refactor from XWiki component annotations to Spring annotations is safe.

## First Checks

Inspect these classes when behavior is unclear in the `celements-base/celements-component` module:

- `com.celements.spring.context.CelSpringContext`
- `com.celements.spring.context.SpringShimComponentManager`
- `com.celements.spring.context.XWikiShimBeanFactory`
- `com.celements.spring.context.XWikiShimBeanPostProcessor`
- `com.celements.spring.context.SpringContextProvider`
- `org.xwiki.component.annotation.ComponentAnnotationLoader`
- `org.xwiki.component.annotation.ComponentDescriptorFactory`
- `org.xwiki.component.descriptor.ComponentDescriptor`

Prefer live code over memory when reviewing a branch, because this bridge is central infrastructure and details may change.

## Runtime Model

`CelSpringContext` creates an `XWikiShimBeanFactory`, configures Spring component scanning, then loads XWiki descriptors from every `META-INF/components.txt` resource and registers them as Spring bean definitions.

Legacy `org.xwiki.component.annotation.Component` classes listed in `META-INF/components.txt` become Spring beans using XWiki role and hint naming. The bean name is normally:

```java
roleClassName + "|||" + roleHint
```

Spring-native beans have normal Spring bean names unless explicitly named. With
`org.springframework.context.annotation.FullyQualifiedAnnotationBeanNameGenerator`, scanned Spring
components normally get their fully qualified implementation class name as bean name. That is a
different namespace from XWiki's role-and-hint model.

`SpringShimComponentManager` implements XWiki `ComponentManager` by delegating lookups to the Spring `BeanFactory`. This means legacy calls such as `Utils.getComponent(MyRole.class)` or `componentManager.lookup(MyRole.class)` may still resolve plain Spring beans by type.

`XWikiShimBeanPostProcessor` keeps old `@Requirement` injection and `Initializable.initialize()` support working for Spring-managed beans. A bean can therefore be Spring-managed and still receive legacy XWiki requirements.

For code that cannot use injection and needs static access, use `SpringContextProvider` for direct
Spring context access and legacy `Utils.getComponent(...)` for XWiki component lookup.
`SpringContextProvider` exposes `getSpringContext()`, `getBeanFactory()`, and
`getEventPublisher()`.

## Hints And Bean Names

XWiki components are addressed by role plus hint:

```java
componentManager.lookup(MyRole.class, "myHint")
```

Spring beans are addressed by bean name plus type:

```java
beanFactory.getBean("myBeanName", MyRole.class)
```

Those are not naturally equivalent. A Spring bean named `"myHint"` is not the same as an XWiki
component with role `MyRole.class` and hint `"myHint"` unless the bridge maps between them.

The bridge handles this in two directions:

- XWiki descriptors are registered into Spring with the encoded role/hint bean name:
  `MyRole.class.getName() + "|||" + hint`
- `XWikiShimBeanFactory` can translate a requested hint/name into that encoded bean name, but only
  when the requested type is annotated with `@ComponentRole`

This means a refactor from XWiki component to Spring bean has two different compatibility questions:

- Plain role lookup: usually OK if there is exactly one Spring bean assignable to the role.
- Hinted lookup: not automatically OK; preserve the XWiki role/hint contract or update all callers.

If an implementation used `@org.xwiki.component.annotation.Component("myHint")`, converting it to
`@Service` changes the naming contract unless you deliberately preserve the bean name or remove all
hinted callers. For XWiki compatibility, prefer keeping `@ComponentRole` on the role and checking
all hinted lookup sites before removing descriptor registration.

## Lookup Rules

For `ComponentManager.lookup(role)`:

- first tries the XWiki role/hint bean name
- then falls back to plain type lookup with `beanFactory.getBean(type)`
- therefore a Spring `@Component` implementing a role can satisfy plain role lookup even if the role no longer has `@ComponentRole`

For hinted lookup, named lookup, or fallback from a hint to the XWiki role/hint bean name:

- `XWikiShimBeanFactory` only applies the XWiki hint fallback when the requested type is annotated with `@ComponentRole`
- removing `@ComponentRole` is risky if callers use custom hints, `@Named`, `@Qualifier`, `lookup(role, hint)`, or `getBean(hint, role)`

For list and map lookup:

- `lookupList(role)` and Spring `List<Role>` injection use beans assignable to the role
- XWiki components listed in `META-INF/components.txt` are included because descriptors are registered into Spring
- check whether a refactor removes the only mechanism that registers the implementation

## Refactoring To Spring Beans

When converting a legacy XWiki component implementation to Spring:

1. Replace `org.xwiki.component.annotation.Component` on the implementation with Spring `@Component` or `@Service`.
2. Prefer constructor injection with `javax.inject.Inject` or Spring-compatible injection.
3. Remove the implementation from `META-INF/components.txt` when it is now discovered by Spring component scanning.
4. Keep the role interface if callers use it as the injection or lookup type.
5. Keep `@ComponentRole` on the role when hinted lookup compatibility matters.
6. Check callers for `lookup(Role.class, hint)`, `Utils.getComponent(Role.class, hint)`, `@Named`, `@Qualifier`, and `getBean(hint, Role.class)` before removing role metadata.
7. Keep `@Requirement` only where a broader refactor is out of scope; otherwise prefer constructor injection.
8. If the component used `Initializable`, prefer `@PostConstruct` for Spring-native components.

Do not remove `@ComponentRole` just because the implementation is now a Spring bean. It is role metadata, not implementation registration. It may still be part of hint compatibility.

## When Removing `components.txt` Entries Is Safe

Usually safe:

- the class is under a package covered by Spring component scanning, such as `com.celements`, `org.xwiki`, or `com.xpn.xwiki` in the configured Celements context
- the class has a Spring stereotype annotation
- there are no callers depending on the XWiki descriptor by custom hint
- tests and runtime modules use `CelSpringContext` or the Spring shim

Risky:

- the class is outside scanned packages
- the implementation only had XWiki `@Component` and no Spring stereotype
- the role/hint name is part of public lookup behavior
- tests or bootstrapping paths still use an embeddable XWiki component manager without the Spring shim
- component overrides rely on `META-INF/component-overrides.txt`

## Annotation Guidance

Use Spring annotations for new or refactored implementations:

```java
@Service
public class MyService implements MyRole {

  private final Dependency dependency;

  @Inject
  public MyService(Dependency dependency) {
    this.dependency = dependency;
  }
}
```

Use XWiki role annotations selectively:

```java
@ComponentRole
public interface MyRole {
}
```

Keep `@ComponentRole` when role/hint lookup is part of the contract. Removing it can break hint fallback even if plain type lookup still works.

## Review Checklist

- Identify whether each changed class is an implementation, a role interface, or both.
- Search for `Utils.getComponent`, `componentManager.lookup`, `webUtilsService.lookup`, `BeanFactory.getBean`, `@Named`, and `@Qualifier` usages of the changed role.
- Check whether lookups are plain type lookups or hinted/named lookups.
- Verify whether the implementation is discovered by Spring scanning after removing a `components.txt` entry.
- Verify `List<Role>` or `lookupList(Role.class)` injection if the component is an extension/listener/converter.
- Check test harness assumptions. In tests extending `AbstractComponentTest`, use the parent
  class' `getBeanFactory().getBean(...)` helper instead of static lookup through
  `SpringContextProvider` or `Utils.getComponent(...)`.
- Avoid changing runtime behavior by converting too many related components in one PR.

## Common Pitfalls

- Treating `@ComponentRole` as obsolete registration metadata. It still controls XWiki hint fallback.
- Removing a `components.txt` entry from a class that has no Spring stereotype or is outside scanned packages.
- Assuming `lookup(role)` and `lookup(role, hint)` have the same compatibility behavior.
- Forgetting that XWiki `@Requirement` is still injected by `XWikiShimBeanPostProcessor`.
- Replacing `Initializable.initialize()` without preserving initialization timing.
- Breaking listener/converter registration by changing component names or hints.
- Using static lookup through `SpringContextProvider` or `Utils.getComponent(...)` in tests instead
  of the parent `getBeanFactory()` helper provided by `AbstractComponentTest`.

## Practical Review Language

When a PR removes `@ComponentRole`, be precise:

- Plain type lookup is usually still covered by `SpringShimComponentManager`.
- Hinted lookup compatibility may still require `@ComponentRole`.
- The finding should cite actual hinted/named callers, not just the existence of legacy `Utils.getComponent(Role.class)` plain lookups.

When a PR removes `components.txt` entries, be precise:

- The removal is fine if Spring scanning now registers the class.
- It is not fine if the class remains only an XWiki component or relies on descriptor-based role/hint registration.
