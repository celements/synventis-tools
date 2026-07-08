---
name: celements-vue
description: Use when adding, reviewing, or debugging Vue islands in Celements or Celements-based Progon legacy pages, especially Vite frontend entrypoints, Velocity addExtJSfileOnce integration, Vue SFCs, reka-ui/headless components, Tailwind v4 with prefixed no-preflight utilities, Vite manifest JS/CSS resolution, and CSS cascade conflicts with legacy application.css.
---

# Celements Vue

## Overview

Build Vue as small page-level islands inside the legacy Celements page, not as a global SPA replacement. Keep the integration manifest-driven, CSS-conscious, and reversible: Velocity includes one stable frontend source path, Vite emits hashed JS/CSS, and the Celements frontend resource resolver maps the source path to the emitted assets.

Prefer Vue + reka-ui + locally styled Tailwind utilities for new interactive islands. Avoid copying full app setups from standalone frontends unless the page is truly isolated.

## Default Workflow

1. Inspect the existing frontend structure:
   - `src/main/frontend/<app>/index.ts` for Vite entrypoint names.
   - `vite.config.ts` for plugin setup, `build.manifest`, `outDir`, and Rollup input.
   - existing Velocity/appscript includes that call `services.javascript.addExtJSfileOnce`.
2. Add a standalone entry for each island or related page surface.
3. Mount into a stable DOM root from the legacy page. Pass server-rendered data through `data-*` attributes or JSON script tags.
4. Include the source entry from Velocity:

```velocity
$!services.javascript.addExtJSfileOnce(':frontend/<app>/<island>/main.ts', 'file')
```

5. Let the frontend resolver and Vite manifest handle hashed output. Do not hard-code `dist/*.mjs` or `assets/*.css` names in Velocity.
6. Run focused verification:
   - `rtk npm run format`
   - `rtk npm run type-check`
   - `rtk npm run build`
   - `rtk git diff --check -- <touched files>`

## Vue Island Shape

Use `src/main/frontend/shared/vue/mount.ts` instead of redefining mount logic in island entries. Pass props according to the island's needs.

```ts
import { mountVueApp } from "@/shared/vue/mount";
import Island from "@/progon/my-island/Island.vue";

mountVueApp("my-island", Island);
```

Keep the island root owned by Vue. Do not let legacy scripts mutate the same subtree after mount. If mixed ownership is unavoidable, split the DOM into separate roots.

## Reka UI Guidance

Use `reka-ui` for accessible headless primitives when a component needs behavior such as popovers, collapsibles, dialogs, tabs, menus, or selects.

Good defaults:

- import only the primitives needed by the island
- style them locally with prefixed Tailwind utilities
- check portal/overlay behavior on the actual Celements page
- keep popover/dialog z-index explicit when legacy overlays exist
- avoid global theme CSS from component libraries

Prefer Reka over heavy visual libraries in normal legacy pages. PrimeVue, Vuetify, and similar libraries bring more global theme, reset, overlay, and bundle assumptions. Use them only for a genuinely isolated tool surface where those costs are acceptable.

## Tailwind v4 Setup

When Tailwind is wanted in a Vue island, import `src/main/frontend/shared/vue/tailwind.css` from the island entry:

```ts
import "@/shared/vue/tailwind.css";
```

That stylesheet must keep the legacy-safe Tailwind setup: prefix enabled, preflight disabled, utilities important. Keep `important` because legacy Celements CSS is unlayered and often targets base elements, so layered Tailwind utilities may otherwise lose even with class selectors.

Do not use a plain global Tailwind import:

```css
@import "tailwindcss";
```

That includes preflight/base behavior and is too broad for normal Celements legacy pages.

Use Tailwind v4 prefix syntax in templates:

```vue
<button class="tw:border tw:bg-[#1f5f8b] tw:px-2 tw:py-1 tw:text-white">
  Save
</button>
```

The prefix is a variant-style prefix (`tw:text-white`), not Tailwind v3-style `tw-text-white`.

Avoid constructing class names dynamically with string concatenation unless the generated classes are safelisted or otherwise discoverable.

## Manifest CSS Requirements

Vite extracts CSS from Vue SFCs and imported stylesheets. The Celements frontend resource path must include both the emitted JS file and the manifest `css` entries for the source entrypoint.

When styling appears missing at runtime but the build is green:

- inspect `src/main/webapp/resources/dist/.vite/manifest*.json`
- confirm the entry has a `css` array
- confirm the Celements include path loads those CSS files when registering the frontend JS
- confirm the Velocity code uses the stable source path, such as `:frontend/<app>/<island>/main.ts`

If CSS manifest inclusion is not available in the target app, fix that integration before leaning on Tailwind or SFC CSS. Green Vite builds alone do not prove runtime styling.

## Legacy Page Limits

Keep these constraints in mind:

- No global SPA assumptions: the page may already have YUI, jQuery, Prototype-era behavior, Select2, or custom scripts.
- No global CSS resets unless the whole page is isolated.
- Avoid sharing a DOM subtree between Vue and legacy scripts.
- Treat overlays, focus trapping, scroll locking, and z-index as integration risks.
- Do not rely on router ownership of the page unless the app was designed as a full Vue surface.
- Prefer data passed at mount time over scraping legacy DOM after mount.
- Keep bundle scope intentional; shared dependencies can be fine, but unrelated pages should not pay for experiments.

## Review Checklist

- Velocity uses `:frontend/.../main.ts`, not hashed output files.
- The Vite entry is registered in the local entry map.
- Vue islands use `src/main/frontend/shared/vue/mount.ts`.
- Vue islands that need Tailwind import `src/main/frontend/shared/vue/tailwind.css`.
- SFC support has `*.vue` typing, usually via `src/main/frontend/env.d.ts`.
- Reka primitives are directly imported and locally styled.
- Tailwind uses `@tailwindcss/vite`, `prefix(tw)`, no preflight, and important utilities.
- Generated manifest CSS is included by the Celements frontend resolver.
- The build, type-check, formatter, and diff whitespace checks pass.
