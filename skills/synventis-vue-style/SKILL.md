---
name: synventis-vue-style
description: Use when writing, reviewing, or changing Vue, JavaScript, or TypeScript code in Synventis frontend projects, especially for imports, functions, TypeScript types, Tailwind CSS, localization, and required npm verification.
---

# Synventis Vue Style

## Verification

Use the scripts defined in `package.json`. After changing code, run all available required checks before submitting:

```bash
npm run lint-fix
npm run format-fix
npm run test
npm run type-check
```

Do not run these checks when no code was changed.

## Localization

If the project contains localization, dictionary and translation files should be located in `src/conf/locale/`. Use this path for localization work and when searching for existing labels.

## JavaScript And TypeScript

- Use arrow functions. Do not use the `function` keyword.
- Use absolute imports through the `@` alias, where `@` represents the `src` directory, for example `@/path/to/file`.
- Do not add empty lines inside local functions, except in tests where blank lines may separate test setup from assertions and in Vue `setup()` functions or top-level composable functions where they improve readability.
- Do not use TypeScript `as` assertions or `any`.

## Styling

If the project uses Tailwind CSS, use it for all styling work. Do not add Vue `<style>` blocks or inline style attributes for CSS.

## Review Checklist

- Required `package.json` checks were run after code changes.
- When the project contains localization, it uses `src/conf/locale/` and reuses existing labels where possible.
- JavaScript and TypeScript use arrow functions and absolute `@/` imports.
- Local functions contain no empty lines, except where tests separate setup from assertions or where Vue `setup()` and top-level composable functions benefit from them.
- TypeScript contains no `as` assertions or `any`.
- When the project uses Tailwind CSS, all styling uses it rather than Vue `<style>` blocks or inline style attributes.
