---
name: celements-velocity
description: Use for Apache Velocity templates in Celements or Progon projects.
---

# Celements Velocity

## Choose the Technology

Use Velocity for server-rendered markup, template composition, configuration, and small orchestration tasks. Prefer Java and Spring MVC for request handling, domain logic, or complex server behavior. Prefer Vue.js or an existing frontend component for substantial client interaction. Do not rewrite a working template solely because it uses Velocity. Assess older templates critically because historical usage was broader.

## Use Velocity 1.7

Write VTL compatible with Apache Velocity 1.7 and consult its official [VTL reference](https://velocity.apache.org/engine/1.7/vtl-reference.html) and [user guide](https://velocity.apache.org/engine/1.7/user-guide.html). Verify any newer Velocity example before use. Current XWiki documentation is not authoritative for Celements, which forked XWiki long ago.

## Keep Templates on Disk

Store substantial VTL in version-controlled `.vm` files and compose it with `#parse('path/to/template.vm')`. Keep Wiki or XAR content limited to integration, reuse shared templates, and do not use `#evaluate` as a substitute for disk templates. Move complex logic to Java when practical; otherwise split it into focused templates.

## Verify ScriptServices

Prefer Celements ScriptServices exposed as `$services.<name>` over new `$xwiki.xxx` calls. Before using a service, inspect current `.vm` usages, its Java `ScriptService` implementation, and focused tests. Services commonly include `reference`, `modelAccess`, `url`, `rightsAccess`, `date`, `json`, and `celementsweb`; this is not a complete API list. Do not mechanically replace legacy calls or invent an unverified service contract.

Resolve and serialize document references through `$services.reference` when the target service supports reference objects. Do not manually assemble or split document names without first checking the service API.

## Render Safely

Use `$!value` or `$!{value}` for legitimately nullable output; use braces next to adjacent text and an explicit `#if` when absence changes behavior. Quiet references suppress unresolved expressions but neither supply defaults nor encode output.

Encode every dynamic value for its destination:

- HTML text or attributes: `$escapetool.html(...)` or the surrounding template's established XML convention.
- JavaScript: `$escapetool.javascript(...)`.
- URLs: `$escapetool.url(...)`; also HTML/XML-encode a URL rendered in an attribute.
- JSON: `$services.json.newBuilder()`, not string concatenation.

## Protect Mutations

Before any request-triggered save, delete, or other mutation, check authorization with `$services.rightsAccess` and validate CSRF with `$services.csrf.isTokenValid(...)`. Hiding UI controls is not authorization. Delegate complex mutations to secured Java controllers or services.

## Review Flow

1. Confirm that Velocity fits the responsibility and that substantial VTL resides on disk.
2. Check syntax and behavior against Velocity 1.7 sources.
3. Trace changed service calls to local implementations and tests.
4. Classify each dynamic output context and each request-triggered mutation.
5. Verify quiet references, encoding, authorization, and CSRF handling from those classifications.
