---
name: celements-component
description: Use for XWiki component and Spring bean registration, lookup, wiring, or migration in Celements and Progon.
---

# Celements Component

Celements uses a hybrid component system. Legacy XWiki components are registered as Spring beans, while legacy XWiki lookup APIs delegate to Spring. A migration must therefore preserve both Spring wiring and any XWiki role-and-hint contracts.

## Source Of Truth

For details inspect the current implementation of the bridge code in `celements-base/celements-component`:

- `com.celements.spring.context.CelSpringContext`
- `com.celements.spring.context.SpringShimComponentManager`
- `com.celements.spring.context.XWikiShimBeanFactory`
- `com.celements.spring.context.XWikiShimBeanPostProcessor`
- `com.celements.spring.context.SpringContextProvider`
- `org.xwiki.component.annotation.ComponentAnnotationLoader`
- `org.xwiki.component.annotation.ComponentDescriptorFactory`
- `org.xwiki.component.descriptor.ComponentDescriptor`

## Runtime Model

`CelSpringContext` creates an `XWikiShimBeanFactory`, configures Spring component scanning, then loads XWiki descriptors from every `META-INF/components.txt` resource and registers them as Spring bean definitions.

An `org.xwiki.component.annotation.Component` listed in `META-INF/components.txt` becomes a Spring bean with an encoded XWiki name:

```java
roleClassName + "|||" + roleHint
```

A scanned Spring component uses normal Spring naming unless it has an explicit name. With `org.springframework.context.annotation.FullyQualifiedAnnotationBeanNameGenerator`, the bean name is normally the implementation's fully qualified class name. This differs from the XWiki role-and-hint namespace.

`SpringShimComponentManager` implements XWiki `ComponentManager` by delegating to the Spring `BeanFactory`. Legacy lookup APIs can therefore resolve descriptor-backed XWiki components and native Spring beans from the same container.

`XWikiShimBeanPostProcessor` preserves `@Requirement` injection and `Initializable.initialize()` for Spring-managed beans. Existing components can therefore move to Spring registration before all legacy injection and initialization mechanisms are replaced.

When injection is unavailable, use `SpringContextProvider` for direct Spring access and `Utils.getComponent(...)` for XWiki lookup. `SpringContextProvider` exposes `getSpringContext()`, `getBeanFactory()`, and `getEventPublisher()`. Tests extending `AbstractComponentTest` must instead use the inherited `getBeanFactory().getBean(...)`.

## Lookup Semantics

### Plain Role Lookup

`ComponentManager.lookup(role)` first tries the encoded XWiki bean name and then falls back to `beanFactory.getBean(type)`. Calls such as `Utils.getComponent(MyRole.class)` and `componentManager.lookup(MyRole.class)` can therefore resolve a unique assignable Spring bean even if the role has no `@ComponentRole`.

### Hinted And Named Lookup

XWiki looks up a component by role and hint:

```java
componentManager.lookup(MyRole.class, "myHint")
```

Spring looks up a bean by name and type:

```java
beanFactory.getBean("myBeanName", MyRole.class)
```

These names are not equivalent. XWiki descriptors are registered in Spring as `MyRole.class.getName() + "|||" + hint`. `XWikiShimBeanFactory` translates a requested hint to this encoded name only when the requested type has `@ComponentRole`.

Converting `@org.xwiki.component.annotation.Component("myHint")` to `@Service` changes the naming contract unless the role-and-hint registration or expected bean name is preserved, or all hinted callers are updated. Keep `@ComponentRole` when this fallback remains part of the contract. It is role metadata, not implementation registration.

### Collection Lookup

`lookupList(role)` and Spring `List<Role>` injection return beans assignable to the role. `lookupMap(role)` returns the same beans keyed by the decoded XWiki hint for descriptor-backed components and by the Spring bean name otherwise. Before changing registration or bean naming, verify another registration path remains, check list consumers such as extensions, listeners, and converters, and check map consumers that select entries by key.

## Refactoring To Spring Beans

First identify whether each changed type is a role, an implementation, or both. Search callers for `Utils.getComponent`, `componentManager.lookup`, `webUtilsService.lookup`, `BeanFactory.getBean`, `@Named`, and `@Qualifier`. Distinguish plain type lookups from hinted or named lookups. Report a compatibility risk from removing `@ComponentRole` only when an actual hinted or named caller depends on it.

1. Replace the implementation's XWiki `@Component` with Spring `@Component` or `@Service`.
2. Prefer constructor injection with `javax.inject.Inject` or compatible Spring injection.
3. Remove the implementation from `META-INF/components.txt` when Spring scanning registers it.
4. Keep the role interface if callers use it for injection or lookup.
5. Keep `@ComponentRole` when hinted lookup compatibility matters.
6. Update or preserve callers that depend on component hints or bean names.
7. Keep `@Requirement` only when a broader injection refactor is out of scope.
8. Replace `Initializable` with `@PostConstruct` only after preserving initialization timing.

## Removing `components.txt` Entries

Removal is normally safe when:

- the class has a Spring stereotype and lies in a scanned package;
- no caller depends on descriptor-based role-and-hint registration; and
- runtime and tests use `CelSpringContext` or the Spring shim.

The configured Celements context typically scans `com.celements`, `org.xwiki`, and `com.xpn.xwiki`. Verify the actual scan configuration rather than relying on this list.

Keep the entry when:

- the class is outside the scanned packages or lacks a Spring stereotype;
- its role-and-hint name is part of lookup behavior;
- a bootstrap or test path uses an embeddable XWiki component manager without the shim; or
- registration depends on `META-INF/component-overrides.txt`.

A review finding about removing a `components.txt` entry should identify why Spring does not provide equivalent registration.
