---
name: synventis-vue-style
description: Use when writing, reviewing, or changing Vue or TypeScript code in Synventis, Celements and Progon projects.
---

# Synventis Vue Style

## Verification

After changing relevant code, run available checks defined in `package.json` before submitting, e.g. linting, formatting, type checking and testing.

## Localization

If the app uses localization, place translation dictionaries under `@/conf/locale/`.

## JavaScript and TypeScript

- Prefer arrow functions over the `function` keyword.
- Use absolute imports through the `@` alias, where `@` represents the source root, for example `@/path/to/file`.
- Avoid empty lines inside functions. Allow them where they separate logical phases in top-level, `setup()` and test functions.
- Avoid unsafe TypeScript assertions and `any`. Prefer type guards and `unknown`.

## Styling

If the project uses Tailwind CSS, use it for all styling work. Avoid Vue `<style>` blocks or inline style attributes for CSS unless necessary.
