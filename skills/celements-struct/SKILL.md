---
name: celements-struct
description: Use when working with celements-struct or Celements structured data editor layouts, including DB/XAR layout cells, StructEditFieldClass bindings, StructuredDataEditor/StructuredDataView page types, form field page types, object filters, ObjectList/Table layouts, SelectTagAutocomplete, struct Java services, Velocity templates, and structEditJS behavior.
---

# Celements Struct

## Overview

Use celements-struct as a bridge between XWiki page-layout documents and structured data editing. Most behavior is configured in XWiki documents: layout cells choose a page type, attach Celements cell/menu objects, and add struct-specific objects that bind the cell to document fields or XObjects.

Treat code as the source of truth and exported layouts as examples of possible DB content. Do not hard-code assumptions from one exported layout into reusable code.

## First Checks

Start with these files before guessing:

- `component/src/main/java/com/celements/struct/DefaultStructDataService.java`
- `component/src/main/java/com/celements/structEditor/DefaultStructuredDataEditorService.java`
- `component/src/main/java/com/celements/structEditor/StructuredDataEditorScriptService.java`
- `component/src/main/java/com/celements/struct/StructDataScriptService.java`
- `component/src/main/java/com/celements/structEditor/StructuredDataEditorNavigationConfigurator.java`
- `component/src/main/java/com/celements/structEditor/fields/*PageType.java`
- `component/src/main/java/com/celements/structEditor/classes/*EditorClass.java`
- `component/src/main/java/com/celements/struct/classes/*Class.java`
- `component/src/main/java/com/celements/struct/table/*PresentationType.java`
- `component/src/main/resources/META-INF/components.txt`
- `web-module/src/main/webapp/templates/celTemplates/StructuredDataEditorView.vm`
- `web-module/src/main/webapp/templates/celMacros/struct/renderEditorLayout.vm`
- `web-module/src/main/webapp/templates/celTemplates/*View.vm`
- `web-module/src/main/webapp/templates/celTemplates/fieldTypeEdit/*.vm`
- `web-module/src/main/webapp/resources/structEditJS/*.mjs`

Use `example-layouts/` only to understand the shape of exported XWiki documents and the range of authoring patterns.

## Runtime Model

`StructuredDataEditor` and `StructuredDataView` are page types rendered through `StructuredDataEditorView.vm`. The view resolves an editor layout space, includes layout-specific JS/CSS, sets struct context-menu classes, then renders the page layout.

Layout-space resolution is important:

1. Prefer `Celements.StructLayoutClass` / `layoutSpace` on the current document if it points to an existing layout.
2. Otherwise compute from the current page type config name: `<PageType>-EditFields` when the page type has an edit template, or `<PageType>-StructData` otherwise.
3. Fall back to the central wiki when the local layout does not exist.

A struct layout is a page-layout tree. Each cell is an XWiki document with normal layout objects such as `Celements.CellClass` and menu ordering/parenting, plus a page type such as `InputTag`, `SelectTag`, `Table`, or `ObjectList`. The struct field page types render their view template for normal editor output and use `StructDataFieldEdit.vm` when editing the field configuration itself.

The public Velocity script services are:

- `$services.structuredDataEditor` for cell attributes, values, labels, possible values, object streams, autocomplete metadata, and field metadata.
- `$services.structData` for table config loading, table rendering, and JS files configured on the layout config document.

## Field Binding

The central binding object is `Celements.StructEditFieldClass`:

- `edit_field_class_fullname`: XClass reference for XObject-backed fields.
- `edit_field_name`: property name, or special document fields `title` and `content`.
- `multilingual`: restrict object selection to the request/default language field when the target class has a language field.
- `computed_obj_nb`: Velocity-evaluated object number fallback.

Attribute names are built from the configured class reference, selected object number, and field name. For a normal XObject field this produces names shaped like `Space.Class_0_field`. If no class reference is configured, the field name can stand alone, which is used for document-level fields and plain hidden/form control fields.

Object number resolution is contextual. Check these sources in order when a field shows or saves the wrong object:

1. Request parameters: `objNb`, `objNb_<classRef>`, and class/filter-specific keys.
2. Execution context object number keys from cell rendering.
3. `computed_obj_nb` on the cell.
4. First matching object, with multilingual filtering if enabled.
5. A negative create object number cached per request by class and key/value filters.

Request values win over stored values. Stored values come from the selected XObject field, or from translated document `title` / `content` when those special field names are configured.

## Object Filters

Struct filters are `Classes.KeyValueClass` objects on the layout cell. The key and value are Velocity-evaluated.

- `struct-obj-filter` and `struct-obj-filter-and` are AND filters.
- `struct-obj-filter-or` is an OR filter.

Filters affect object selection, object streams, request object-number keys, and generated negative object numbers for new objects. For CelTag fields, a filter with key `type` can also define the tag type used to load possible tag values.

## Field Types

Prefer current page types when adding new layouts:

- `FormField`: renders a form with configured action, method, optional multipart encoding, prefix, validation class, and autocomplete off.
- `InputTag`: renders a text input with generated name/value. `NumberTag` extends it with `type=number`.
- `TextAreaTag`: renders a textarea with rows/cols and optional TinyMCE classes.
- `SelectTag`: renders a select from XClass possible values or rendered child option cells; supports bootstrap and multiselect config.
- `OptionTag`: renders option content/attributes and can mark selected/disabled options.
- `SelectTagAutocomplete`: renders a Select2-backed select using an `AutocompleteRole`.
- `DateTime`: renders the current custom date/time element and includes date-time JS.
- `HiddenTag`: renders explicit hidden name/value fields or falls back to the struct field binding and request value.
- `DisplayField`: displays the bound value.
- `LabelTag`: displays the resolved pretty name.
- `LanguageSelector`: renders the language selector macro.
- `SubmitLink`: renders the standard save label.
- `ObjectList`: repeats an object row layout for all matching XObjects.
- `Table`: renders document/object/object-link tables.

Legacy aliases still exist: `InputField`, `TextAreaField`, and `DateTimePicker`. Prefer `InputTag`, `TextAreaTag`, and `DateTime` for new work unless the surrounding layout already depends on the old names.

Field-type-specific configuration lives in editor classes such as `FormFieldEditorClass`, `SelectTagEditorClass`, `SelectTagAutocompleteEditorClass`, `TextAreaFieldEditorClass`, `HiddenTagEditorClass`, `OptionTagEditorClass`, and `DateTimePickerEditorClass`. The edit UI for those objects is in `web-module/src/main/webapp/templates/celTemplates/fieldTypeEdit/`.

## Autocomplete

`SelectTagAutocomplete` uses `SelectTagAutocompleteEditorClass` plus an `AutocompleteRole` component. The default implementation:

- uses web search configured on the cell document,
- returns JSON through `templates/celAjax/struct/autocomplete/search.vm`,
- can render result names and result HTML from Velocity fields on the cell,
- can expose an add-new URL from the cell config,
- loads Select2, i18n files, and `structEditJS/autocomplete.mjs`.

For custom autocomplete, implement `AutocompleteRole` with a distinct component hint/name, provide search and selected-value behavior, and include any extra JS through `getJsFilePath()`.

## Tables

A `Table` cell is configured by `Celements.StructTableClass` and optional `Celements.StructTableColumnClass` objects.

Table config fields:

- `type`: `DOC`, `OBJ`, or `OBJLINK`.
- `query`: Velocity-evaluated Lucene query for `DOC` tables; empty query falls back to web search.
- `sort_fields`, `result_limit`, `css_id`, `css_classes`.
- `header_layout` and `row_layout` for layout-driven rows.

Column config fields:

- `name`, `title`, `content`, `order`, `css_classes`.
- Columns sort by `order`, then object number.
- `name` is normalized to word characters for CSS/fallback lookup.

Table renderers:

- `DOC`: search documents and render each result.
- `OBJ`: stream matching XObjects on the current document and render the current doc once per object while setting the execution object number.
- `OBJLINK`: stream matching link objects, read the first non-empty `reference`, `ref`, or `link` field as a document reference, expose `$srcdoc` and `$rowdoc`, and render linked rows.

With explicit columns, cell content is resolved in this order:

1. `StructTableColumnClass.content` evaluated as Velocity with `$rowdoc` and `$colcfg`.
2. A disk template named `col_<columnName>.vm`, resolved through layout/table naming fallbacks.
3. The matching XObject field display value.
4. An XDocument pseudo-field value.

Without columns, the table uses `row_layout` / `header_layout` through `LayoutServiceRole`, with local-wiki and central-wiki fallback. Edit/inline actions add create/delete links and a template row for client-side insertion.

## Client Behavior

Struct editor JS is legacy-page JS. Expect Prototype/YUI/jQuery/Select2 integration rather than a modern isolated frontend.

- `StructEditor.mjs` manages dirty editors, close/save buttons, save-and-continue, and events such as `structEdit:finishedInitialize`, `structEdit:finishedLoading`, `structEdit:saveAndContinueButtonSuccessful`, and `structEdit:saveAndContinueButtonFailed`.
- `cel-table.mjs` defines the `cel-table` custom element for table row create/delete behavior.
- New client-created objects get negative object numbers. Existing objects are deleted by prefixing the object number in form field names with `^`.
- `StructObjectListEdit.mjs` handles similar repeated-object editing for `ObjectList`.

When debugging browser behavior, inspect the rendered form field names and data attributes before changing Java code.

## Change Workflow

For layout/content issues:

1. Identify the current document page type and resolved struct layout space.
2. Inspect the relevant layout cell documents, their page types, parent/menu order, `Celements.CellClass`, `Celements.StructEditFieldClass`, field-type-specific objects, and `Classes.KeyValueClass` filters.
3. Map the cell page type to its Java page type and Velocity view template.
4. Check the rendered field name, object number source, current document context, request language, and request parameters.
5. Check rights: both script services hide output when view rights are missing.

For code changes:

1. Add or update the class definition if new configuration is stored on XWiki objects.
2. Add or update the Java page type when a new field type or tag needs attribute collection.
3. Add the view template under `celTemplates/` and the edit-config template under `celTemplates/fieldTypeEdit/` when editors must configure it.
4. Register legacy components in `META-INF/components.txt` unless the module has been deliberately migrated to Spring scanning.
5. Update JS/CSS only where the rendered templates actually include it.
6. Run focused tests in `component/src/test/java`, plus a whitespace check on changed files.

## Pitfalls

- Do not confuse layout space resolution with skin/resource resolution.
- Do not assume a layout cell document is the data document. The cell config is read from the layout; field values are read from the current document.
- Do not ignore request values. They intentionally override stored values while rendering validation failures or partial saves.
- Do not delete `components.txt` entries as cleanup unless component registration has been revalidated.
- Be precise with `struct-obj-filter` labels; a spelling or label-family change alters object selection.
- Check central-wiki fallback before declaring a layout missing.
- Check old page type names before renaming layouts; existing DB content may still use deprecated aliases.
