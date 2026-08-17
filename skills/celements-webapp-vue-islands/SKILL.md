---
name: celements-webapp-vue-islands
description: Use for Vue islands embedded in legacy Celements or Progon pages.
---

# Celements Vue Islands

Use page-level islands, not a global SPA, unless the page is an isolated Vue surface. Load each island only where it is needed.
Prefer Vue + reka-ui + locally styled Tailwind utilities for new interactive islands. Avoid copying full app setups from standalone frontends unless the page is truly isolated.

## Integration

Inspect the local setup before changing it:

- `src/main/frontend/<app>/index.ts` for Vite entrypoints
- `vite.config.ts` for plugins, `build.manifest`, `outDir`, and Rollup input
- Velocity or appscript calls to `services.javascript.addExtJSfileOnce`

Register the island entry, mount it through `src/main/frontend/shared/vue/mount.ts`, and include its stable source path from Velocity:

```velocity
$!services.javascript.addExtJSfileOnce(':frontend/<app>/<island>/main.ts', 'file')
```

Let the Celements frontend resolver use the Vite manifest. Never reference hashed `dist/*.mjs` or `assets/*.css` files from Velocity. Ensure `*.vue` typing is available, normally through `src/main/frontend/env.d.ts`.

Pass server data through props derived from `data-*` attributes or JSON script elements. Vue must exclusively own its mount subtree; give legacy scripts separate roots. Do not scrape or mutate Vue-owned DOM after mounting.

## CSS And UI Components

For Tailwind, import `src/main/frontend/shared/vue/tailwind.css` from the island entry. It must retain the Tailwind v4 legacy-safe configuration:

- `@tailwindcss/vite`
- `prefix(tw)` with variant syntax such as `tw:text-white`, not `tw-text-white`
- preflight disabled; do not use a global `@import "tailwindcss"`
- important utilities, because unlayered legacy Celements CSS can otherwise override layered utilities

Avoid runtime-generated utility names unless Tailwind can discover or safelist them.

Vite extracts imported and SFC CSS. The Celements resolver must load the entry's emitted JS and every manifest `css` entry. If runtime styles are missing despite a successful build, inspect `src/main/webapp/resources/dist/.vite/manifest*.json`, verify the entry's `css` array, and confirm that the stable `:frontend/<app>/<island>/main.ts` include loads those files. Fix manifest CSS resolution before changing component styles.

Use `reka-ui` for accessible headless behavior where appropriate. Import only required primitives, style them locally, and test portals, focus handling, scroll locking, overlays, and z-index on the legacy page. Do not import global library themes. API reference: https://reka-ui.com/llms.txt.

## Runtime Constraints

- Expect YUI, jQuery, Select2, and other legacy scripts on the same page.
- Do not add global resets or assume router ownership.
- Keep island dependencies off unrelated pages.
- Test interactions and CSS cascade in the rendered Celements page; a green Vite build does not verify runtime asset loading.

Run the relevant formatter, type check, and build scripts from `package.json`, then inspect the touched-file diff and whitespace.
