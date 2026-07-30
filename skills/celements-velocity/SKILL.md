---
name: celements-velocity
description: Use when maintaining, reviewing, or adding Apache Velocity 1.7 templates in Celements or Celements-based Progon projects, especially choosing between Velocity server-side rendering, Spring MVC, and Vue.js; working with file-based `.vm` templates, `#parse`, Celements `$services` APIs, quiet references, output encoding, or authorization and CSRF checks for request-triggered mutations.
---

# Celements Velocity

## Choose the Technology by Context

Use Velocity for server-side rendering where it fits the surrounding Celements architecture. Velocity remains an established part of Celements and is not generally considered legacy or scheduled for replacement.

Treat many existing Velocity scripts as legacy because Velocity was historically overused in this codebase. Do not assume an existing template is a good example without checking its age, structure, and use of modern Celements APIs.

Choose the technology according to the responsibility:

- Use Velocity for server-rendered markup and template composition.
- Prefer Java and Spring MVC for request handling, domain logic, and complex server-side behavior.
- Prefer Vue.js or an existing frontend component for substantial client-side interaction.

Do not rewrite working templates merely because they use Velocity. Apply these choices to new work and substantial rewrites.

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

Use `$!{value}` when braces are needed to separate the reference from adjacent text. Quiet references only suppress unresolved output. They do not provide a fallback value, change control flow, or escape the resolved value. Use an explicit `#if` when absence changes behavior.

## Encode Output for Its Context

Encode request data, document data, and other dynamic values for the context where they are rendered:

- Use `$escapetool.html(...)` or `$escapetool.xml(...)` for HTML text and attributes, following the convention of the surrounding template.
- Use `$escapetool.javascript(...)` for values embedded in JavaScript.
- Use `$escapetool.url(...)` for dynamic URL values or components. Also HTML/XML-encode the resulting value when rendering it into an HTML attribute.
- Use `$services.json.newBuilder()` for JSON instead of manually concatenating or escaping JSON strings.

Do not treat a quiet reference as output encoding.

## Guard Request-Triggered Mutations

Before a request-triggered save, delete, or other mutation, verify that the current user has the required authorization through `$services.rightsAccess` and validate the CSRF token with `$services.csrf.isTokenValid(...)`.

Do not rely on hiding an action in the UI. For complex mutations, delegate to a secured Java controller or service instead of implementing the mutation in an AppScript or `celAjax` template.

## Keep Templates Focused

Use Velocity for server-rendered markup, template composition, configuration, and small amounts of orchestration. During substantial rewrites, move domain logic and complex processing into Java where practical. If Java extraction is not practical, divide the implementation among focused disk-based templates.

Prefer configuring an existing frontend or Celements component over reimplementing its behavior with Velocity loops and logic. Keep AppScript and setup templates small and delegate work to services or dedicated templates.

## Follow Established Modern Patterns

- Resolve and serialize references through `$services.reference` where the target service supports reference objects. Do not manually assemble or split document names without first checking the service API.
- Use `$services.modelAccess`, `$services.url`, and other verified local ScriptServices instead of introducing new legacy `$xwiki` usage.
- Use `$services.json.newBuilder()` for JSON produced by Velocity instead of manually concatenating JSON strings.
- Use Velocity to configure existing frontend components when those components already provide the required rendering or interaction.

Treat these as patterns established by current Celements code, not instructions to mechanically refactor unrelated legacy templates.

## Review Checklist

- Confirm that Velocity fits the responsibility; consider Spring MVC for complex server-side behavior and Vue.js for substantial client-side interaction.
- Confirm compatibility with Apache Velocity 1.7.
- Keep substantial VTL in a version-controlled `.vm` file invoked with `#parse`.
- Investigate every new or changed `$xwiki.xxx` call for a verified Celements ScriptService alternative.
- Use quiet references for legitimately nullable rendered values.
- Encode every dynamic output for its HTML/XML, JavaScript, URL, or JSON context; do not treat quiet references as escaping.
- Require `$services.rightsAccess` authorization and `$services.csrf.isTokenValid(...)` before request-triggered mutations, or delegate complex mutations to secured Java code.
- Keep orchestration small and move substantial logic to Java where practical.
- Reuse existing disk templates and frontend or Celements components.
- Use the Celements JSON builder when producing JSON in Velocity.
