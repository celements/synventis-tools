---
name: synventis-vue-style
description: Use when writing, reviewing, or changing Vue or TypeScript code in Synventis, Celements and Progon projects.
---

# Synventis Vue Style

## Verification

After changing relevant code, run available checks defined in `package.json` before submitting, e.g. linting, formatting, type checking and testing.

## Localization

If app uses localization, use dictionaries in `@/conf/locale/` or legacy `@/locale`.

## Vue

- Order SFC blocks: `<template>`, `<script>`, `<style>`.

## JavaScript and TypeScript

- Prefer arrow functions over the `function` keyword.
- Use absolute imports through the `@` alias, where `@` represents the source root, for example `@/path/to/file`.
- Avoid empty lines inside functions. Allow them where they separate logical phases in top-level, `setup()` and test functions.
- Avoid unsafe TypeScript assertions and `any`. Prefer type guards and `unknown`.

## Styling

In Tailwind projects, use it on Vue-owned elements, including states and pseudo-elements. Arbitrary properties and variants
are acceptable when concise and local.

Use `<style>` for third-party or legacy DOM, or when complex selectors are clearer than Tailwind.

Keep semantic class hooks only when consumed by JavaScript, CSS, or external code.

When static utilities exceed the line limit, use a `:class` array with the fewest reasonably packed strings. Keep dynamic
conditions separate.
