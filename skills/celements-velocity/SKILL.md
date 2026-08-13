---
name: celements-velocity
description: Use when writing or reviewing Celements Apache Velocity 1.7 templates.
---

# Celements Velocity

Use Velocity for server-rendered markup, template composition, configuration, and light orchestration. Prefer Java/Spring MVC for complex request or domain logic and Vue for substantial client interaction. Do not rewrite working templates only because they use Velocity.

## Compatibility And Structure

Write Velocity 1.7-compatible VTL. Use the official [VTL reference](https://velocity.apache.org/engine/1.7/vtl-reference.html) and [user guide](https://velocity.apache.org/engine/1.7/user-guide.html); Velocity 2.x and current XWiki behavior may differ from Celements.

Keep substantial VTL in version-controlled `.vm` files and compose it with `#parse`. Keep Wiki/XAR content limited to integration. Reuse shared templates; do not use `#evaluate` as a substitute for a disk template.

## Celements Services

Prefer verified `$services.<name>` APIs over new `$xwiki.xxx` calls. Before replacing or adding an API call:

1. Search current templates for local usage.
2. Inspect the Java `ScriptService` and focused tests.
3. Follow a modern example from the same module when possible.

Common services include `$services.reference`, `$services.modelAccess`, `$services.url`, `$services.rightsAccess`, `$services.date`, `$services.json`, and `$services.celementsweb`. This is not a complete API list.

## Rendering Safety

- Use `$!value` or `$!{value}` only to suppress legitimately unresolved output; it does not escape or provide a fallback.
- Escape dynamic HTML/XML, JavaScript, and URL data for its output context with the local `$escapetool` conventions.
- Also HTML/XML-escape a URL when placing it in an HTML attribute.
- Build JSON with `$services.json.newBuilder()`, not string concatenation.

For request-triggered mutations, check authorization through `$services.rightsAccess` and validate `$services.csrf.isTokenValid(...)`. UI visibility is not authorization. Delegate complex mutations to secured Java code.

## Review

Check Velocity 1.7 compatibility, disk-based template composition, nullable references, contextual encoding, verified Celements service usage, authorization, CSRF protection, and whether substantial logic belongs in Java or an existing frontend component.
