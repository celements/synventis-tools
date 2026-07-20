---
name: celements-velocity
description: Use when maintaining, reviewing, or adding Apache Velocity 1.7 templates in Celements or Celements-based Progon projects, especially file-based `.vm` templates, `#parse` integration from XAR pages, legacy `$xwiki` calls, Celements `$services` APIs, quiet references, AppScripts, and decisions about moving logic to Java or existing frontend components.
---

# Celements Velocity

## Before Using Velocity

Treat Velocity as legacy technology. Before adding or substantially extending a Velocity template, check for an existing Java service, ScriptService, frontend component, or other established project mechanism. Use Velocity only when the surrounding Celements infrastructure requires it or no practical alternative exists.

Do not rewrite working legacy templates merely because they use Velocity. Apply these guidelines to new work and substantial rewrites.

## Use Velocity 1.7

Write Apache Velocity 1.7-compatible VTL. Consult only the official Apache documentation for the language:

- [Velocity 1.7 VTL reference](https://velocity.apache.org/engine/1.7/vtl-reference.html)
- [Velocity 1.7 user guide](https://velocity.apache.org/engine/1.7/user-guide.html)

Do not copy Velocity 2.x syntax or behavior without verifying compatibility. Do not use XWiki documentation as Celements documentation: Celements forked XWiki long ago, so current XWiki behavior and examples may not apply.

## Keep Velocity Code on Disk

Store substantial Velocity code in version-controlled `.vm` files. Use `#parse('path/to/template.vm')` to invoke and compose disk templates. Keep Velocity embedded in Wiki or XAR content to the minimal integration needed to parse the disk template.

Prefer existing shared disk templates over copying their implementation. When Java extraction is not practical, split a large implementation into focused `.vm` files. Do not use `#evaluate` as a substitute for a version-controlled template.

## Prefer Celements ScriptServices

Treat `$xwiki.xxx` calls as a legacy-code smell. For new or substantially rewritten code, look for an existing Celements ScriptService exposed through `$services.xxx`.

Do not mechanically replace `$xwiki` calls. Verify the available Celements API and its behavior in local Java code, tests, and known-modern templates:

1. Search current `.vm` files for relevant `$services.<name>` usage.
2. Find and inspect the corresponding Java `ScriptService` implementation.
3. Read its public methods and focused tests.
4. Prefer examples from the same module or another known-modern project.
5. If no suitable service exists, report that before introducing a new legacy `$xwiki` call.

Common modern Celements services include `$services.reference`, `$services.modelAccess`, `$services.url`, `$services.rightsAccess`, `$services.date`, `$services.json`, and `$services.celementsweb`. Verify each service locally rather than treating this list as a complete API reference.

## Use Quiet References

Use quiet references such as `$!value` and `$!{value}` when a value may legitimately resolve to `null`. Velocity 1.7 otherwise renders the unresolved Velocity expression, which is not useful to customers.

Use `$!{value}` when braces are needed to separate the reference from adjacent text. Quiet references suppress output; they do not provide a fallback value or change control flow. Use an explicit `#if` when absence changes behavior.

## Keep Templates Focused

Use Velocity for small amounts of orchestration, service invocation, template composition, configuration, and markup. During substantial rewrites, move domain logic and complex processing into Java where practical. If Java extraction is not practical, divide the implementation among focused disk-based templates.

Prefer configuring an existing frontend or Celements component over reimplementing its behavior with Velocity loops and logic. Keep AppScript and setup templates small and delegate work to services or dedicated templates.

## Follow Established Modern Patterns

- Resolve and serialize references through `$services.reference` where the target service supports reference objects. Do not manually assemble or split document names without first checking the service API.
- Use `$services.modelAccess`, `$services.url`, and other verified local ScriptServices instead of introducing new legacy `$xwiki` usage.
- Use `$services.json.newBuilder()` for JSON produced by Velocity instead of manually concatenating JSON strings.
- Use Velocity to configure existing frontend components when those components already provide the required rendering or interaction.

Treat these as patterns established by current Celements code, not instructions to mechanically refactor unrelated legacy templates.

## Review Checklist

- Confirm that Velocity is necessary and no established alternative fits better.
- Confirm compatibility with Apache Velocity 1.7.
- Keep substantial VTL in a version-controlled `.vm` file invoked with `#parse`.
- Investigate every new or changed `$xwiki.xxx` call for a verified Celements ScriptService alternative.
- Use quiet references for legitimately nullable rendered values.
- Keep orchestration small and move substantial logic to Java where practical.
- Reuse existing disk templates and frontend or Celements components.
- Use the Celements JSON builder when producing JSON in Velocity.
