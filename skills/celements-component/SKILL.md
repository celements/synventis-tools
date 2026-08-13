---
name: celements-component
description: Use when changing Celements XWiki/Spring component registration, lookup, hints, or injection.
---

# Celements Components

Celements combines legacy XWiki components with Spring beans. Verify behavior in the bridge code located in `celements-base/celements-component`before changing registration or lookup:

- `com.celements.spring.context.CelSpringContext`
- `com.celements.spring.context.SpringShimComponentManager`
- `com.celements.spring.context.XWikiShimBeanFactory`
- `com.celements.spring.context.XWikiShimBeanPostProcessor`
- `com.celements.spring.context.SpringContextProvider`
- `org.xwiki.component.annotation.ComponentAnnotationLoader`
- `org.xwiki.component.annotation.ComponentDescriptorFactory`
- `org.xwiki.component.descriptor.ComponentDescriptor`

## Runtime Model

`CelSpringContext` scans Spring components and registers XWiki descriptors from `META-INF/components.txt` as Spring bean definitions.

Legacy XWiki beans use an encoded role/hint name:

```java
roleClassName + "|||" + roleHint
```

Spring beans normally use Spring bean names. `SpringShimComponentManager` delegates XWiki lookups to the Spring `BeanFactory`, so plain `lookup(Role.class)` can resolve a Spring bean by type. `XWikiShimBeanPostProcessor` preserves `@Requirement` injection and `Initializable.initialize()` for Spring-managed beans.

## Lookup Compatibility

Plain and hinted lookups are not equivalent:

- Plain role lookup usually works when exactly one assignable Spring bean exists.
- Hinted lookup depends on the XWiki role/hint contract.
- `XWikiShimBeanFactory` applies role/hint fallback only when the requested type has `@ComponentRole`.
- `lookupList(Role.class)` and Spring `List<Role>` injection include all registered assignable beans.

Before changing a component, search for:

- `Utils.getComponent`
- `ComponentManager.lookup`
- `BeanFactory.getBean`
- `@Named` and `@Qualifier`
- `List<Role>` and `lookupList(Role.class)`

Do not remove `@ComponentRole` solely because the implementation becomes a Spring bean. It may still be required for hinted lookup.

## Migrating To Spring

1. Replace the XWiki `@Component` annotation with Spring `@Component` or `@Service`.
2. Prefer constructor injection.
3. Remove the class from `META-INF/components.txt` only after confirming component scanning covers it.
4. Preserve role interfaces used by callers.
5. Preserve `@ComponentRole` when hinted lookup remains supported.
6. Replace `Initializable` with `@PostConstruct` only when initialization timing remains equivalent.

Removing a `components.txt` entry is unsafe when the class lacks a Spring stereotype, is outside scanned packages, depends on descriptor naming or overrides, or runs in a bootstrap path without the Spring shim.

## Tests And Review

In `AbstractComponentTest`, use the inherited `getBeanFactory().getBean(...)` helper rather than static `SpringContextProvider` or `Utils.getComponent(...)` lookup.

Review the actual caller contract. A valid finding identifies a broken hinted/named lookup, missing registration, list membership change, or initialization change; the mere presence of legacy annotations or plain lookup is not enough.
