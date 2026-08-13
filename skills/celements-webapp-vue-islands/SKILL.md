---
name: celements-webapp-vue-islands
description: Use when integrating Vue islands, Vite assets, or scoped Tailwind into legacy Celements pages.
---

# Celements Webapp Vue Islands

Build page-level Vue islands, not a global SPA. Keep Vue and legacy scripts from owning the same DOM subtree.

## Integration

1. Inspect `vite.config.ts`, existing `src/main/frontend` entries, and nearby Velocity includes.
2. Add an entry for the island and mount it into a stable root.
3. Pass server data through `data-*` attributes or a JSON script element.
4. Include the stable source entry from Velocity:

```velocity
$!services.javascript.addExtJSfileOnce(':frontend/<app>/<island>/main.ts', 'file')
```

5. Let the Vite manifest resolve hashed JS and CSS. Never hard-code `dist` asset names in Velocity.

Use the shared mount helper when available:

```ts
import { mountVueApp } from "@/shared/vue/mount";
import Island from "@/progon/my-island/Island.vue";

mountVueApp("my-island", Island);
```

## Reka UI And Tailwind

Use `reka-ui` for accessible dialogs, popovers, tabs, menus, and similar behavior. Import only needed primitives, style them locally, and verify portals, focus handling, scroll locking, and z-index on the legacy page. API reference: <https://reka-ui.com/llms.txt>.

For Tailwind, import the shared legacy-safe stylesheet:

```ts
import "@/shared/vue/tailwind.css";
```

It must retain the project prefix, disabled preflight, and important utilities. Use Tailwind v4 prefix syntax such as `tw:text-white`, not `tw-text-white`. Avoid dynamically constructed classes unless Vite can discover or safelist them.

Do not use a global `@import "tailwindcss"`; its reset is too broad for legacy pages.

## Manifest CSS

Vite extracts imported and SFC CSS. The Celements resource resolver must load the manifest entry's `css` files as well as its JS file.

If runtime styles are missing despite a green build:

1. Inspect `src/main/webapp/resources/dist/.vite/manifest*.json`.
2. Confirm the source entry has a `css` array.
3. Confirm the Celements include resolves those CSS files.
4. Confirm Velocity references `:frontend/.../main.ts`.

Fix manifest integration rather than hard-coding generated CSS names.

## Verify

Use the scripts defined by the project, including formatting, type checking, linting, and build checks. Also verify the island on the real page for legacy CSS conflicts, overlays, and unrelated-page bundle loading.
