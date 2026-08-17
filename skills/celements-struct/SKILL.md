---
name: celements-struct
description: Use for Celements structured data editor layouts.
---

# Celements Struct

Celements struct connects XWiki page-layout documents to fields on the current data document. Layout cells are XWiki documents containing normal cell/menu objects, a page type, and struct configuration. The layout cell supplies configuration; it is not the data document.

Treat Java and templates in celements-structuredDataEditor as the source of truth. Use `example-layouts/` only as examples of stored XWiki documents, never as a universal schema.

## Runtime Model

`StructuredDataEditor` and `StructuredDataView` are page types rendered through `StructuredDataEditorView.vm`. The view resolves the editor layout space, includes layout-specific JS and CSS, sets the struct context-menu classes, and renders the page layout.

The layout space is resolved in this order:

1. Prefer `Celements.StructLayoutClass` / `layoutSpace` on the current document when it names an existing layout.
2. Otherwise compute from the current page type config name: `<PageType>-EditFields` if the page type has an edit template, or `<PageType>-StructData` otherwise.
3. Fall back to the central wiki when the local layout is absent.

A struct layout is a page-layout tree. Each cell is an XWiki document with normal layout objects such as `Celements.CellClass` and menu ordering or parenting, a page type such as `InputTag`, `SelectTag`, `Table`, or `ObjectList`, and any struct-specific configuration. Field page types use their view template for editor output and `StructDataFieldEdit.vm` when editing the field configuration.

Velocity templates use two public script services:

- `$services.structuredDataEditor` provides cell attributes, values, labels, possible values, object streams, autocomplete data, and field metadata.
- `$services.structData` loads table configuration, renders tables, and provides JS files configured on the layout document.

Both services suppress output when view rights are missing. Layout-space resolution is separate from skin and resource resolution.

## Field Binding

`Celements.StructEditFieldClass` binds a cell to data:

- `edit_field_class_fullname`: XClass reference for XObject-backed fields.
- `edit_field_name`: property name, or special document fields `title` and `content`.
- `multilingual`: restricts selection by the request/default language when the target class has a language field.
- `computed_obj_nb`: Velocity-evaluated object number fallback.

An XObject field name has the form `Space.Class_0_field`, built from the configured class, selected object number, and property. Without a class reference, the field name stands alone for document fields and plain hidden or form controls.

Resolve object numbers in this order:

1. Request parameters: `objNb`, `objNb_<classRef>`, and class/filter-specific keys.
2. Object-number keys in the cell-rendering execution context.
3. `computed_obj_nb` on the cell.
4. The first matching object, applying multilingual filtering when enabled.
5. A negative create number cached per request by class and key/value filters.

Request values override stored values. Stored values come from the selected XObject or from the translated document `title` or `content` when configured.

## Object Filters

Struct filters are `Classes.KeyValueClass` objects on the layout cell. Their keys and values are evaluated as Velocity.

- `struct-obj-filter` and `struct-obj-filter-and` are AND filters.
- `struct-obj-filter-or` is an OR filter.

The exact labels matter. Filters affect object selection, object streams, request object-number keys, and negative numbers for new objects. For CelTag fields, a filter with the key `type` can also select the tag type used to load possible values.

## Page Types

Use current names in new layouts:

- `FormField` renders a form with configurable action, method, optional multipart encoding, prefix, validation class, and autocomplete disabled.
- `InputTag` renders a text input with a generated name and value; `NumberTag` extends it with `type=number`.
- `TextAreaTag` renders a textarea with rows, columns, and optional TinyMCE classes.
- `SelectTag` reads XClass possible values or rendered child `OptionTag` cells and supports Bootstrap and multiselect configuration.
- `OptionTag` renders option content and attributes, including selected or disabled state.
- `SelectTagAutocomplete` renders a Select2-backed select using an `AutocompleteRole`.
- `DateTime` renders the custom date-time element and includes its JavaScript.
- `HiddenTag` uses an explicit name and value or falls back to the field binding and request value.
- `DisplayField` displays the bound value; `LabelTag` displays its resolved pretty name.
- `LanguageSelector` renders the language selector; `SubmitLink` renders the standard save label.
- `ObjectList` repeats a row layout for matching XObjects.
- `Table` renders document, object, or linked-object rows.

`InputField`, `TextAreaField`, and `DateTimePicker` remain legacy aliases. Preserve them in existing DB layouts, but prefer `InputTag`, `TextAreaTag`, and `DateTime` for new content.

Field-specific configuration is defined by the corresponding `*EditorClass`. Its edit UI is under `web-module/src/main/webapp/templates/celTemplates/fieldTypeEdit/`.

## Autocomplete

`SelectTagAutocomplete` combines `SelectTagAutocompleteEditorClass` with an `AutocompleteRole`. The default implementation:

- uses web search configured on the cell document;
- returns JSON through `templates/celAjax/struct/autocomplete/search.vm`;
- can render result names and HTML from Velocity fields on the cell;
- can expose an add-new URL from the cell configuration; and
- loads Select2, its i18n files, and `structEditJS/autocomplete.mjs`.

A custom autocomplete must implement `AutocompleteRole` with a distinct component hint, search and selected-value behavior, and any additional JavaScript path returned by `getJsFilePath()`.

## Tables

`Table` uses `Celements.StructTableClass` and optional `Celements.StructTableColumnClass` objects.

Table configuration includes:

- `type`: `DOC`, `OBJ`, or `OBJLINK`;
- `query`: a Velocity-evaluated Lucene query for `DOC`; an empty query uses web search;
- `sort_fields`, `result_limit`, `css_id`, and `css_classes`; and
- `header_layout` and `row_layout` for layout-driven rendering.

Column configuration includes `name`, `title`, `content`, `order`, and `css_classes`. Columns sort by `order` and then object number. The name is normalized to word characters for CSS and fallback lookup.

The table type determines the row source:

- `DOC` searches documents and renders each result.
- `OBJ` streams matching XObjects on the current document and sets the execution object number for each row.
- `OBJLINK` streams link objects, uses the first non-empty `reference`, `ref`, or `link`, and exposes `$srcdoc` and `$rowdoc`.

Explicit column content resolves in this order:

1. `StructTableColumnClass.content` evaluated with `$rowdoc` and `$colcfg`.
2. A `col_<columnName>.vm` template through the layout/table fallbacks.
3. The matching XObject field display value.
4. An XDocument pseudo-field value.

Without explicit columns, `row_layout` and `header_layout` render through `LayoutServiceRole`, including local-to-central-wiki fallback. Inline editing supplies create/delete actions and a template row.

## Client Behavior

Struct editor JavaScript runs on legacy pages alongside Prototype, YUI, jQuery, and Select2.

- `StructEditor.mjs` manages dirty state, close and save actions, and save-and-continue.
- `cel-table.mjs` defines the `cel-table` custom element for creating and deleting table rows.
- `StructObjectListEdit.mjs` manages repeated-object editing for `ObjectList`.
- New client-created objects use negative object numbers. Deleting an existing object prefixes its object number in submitted field names with `^`.

Inspect rendered field names and data attributes before changing Java code.

The main lifecycle events are `structEdit:finishedInitialize`, `structEdit:finishedLoading`, `structEdit:saveAndContinueButtonSuccessful`, and `structEdit:saveAndContinueButtonFailed`.

## Sources

Start from the narrowest relevant source:

- Services: `component/src/main/java/com/celements/struct/DefaultStructDataService.java`, `component/src/main/java/com/celements/structEditor/DefaultStructuredDataEditorService.java`, their `*ScriptService.java` classes, and `StructuredDataEditorNavigationConfigurator.java`.
- Definitions and rendering: `component/src/main/java/com/celements/structEditor/{fields,classes}/`, `component/src/main/java/com/celements/struct/{classes,table}/`, and `component/src/main/resources/META-INF/components.txt`.
- Views and configuration UI: `web-module/src/main/webapp/templates/celTemplates/`, `web-module/src/main/webapp/templates/celTemplates/fieldTypeEdit/`, and `web-module/src/main/webapp/templates/celMacros/struct/renderEditorLayout.vm`.
- Browser behavior: `web-module/src/main/webapp/resources/structEditJS/`.

## Change Workflow

For layout or content issues:

1. Identify the current document page type and resolved layout space.
2. Inspect the cell's page type, parent and menu order, `Celements.CellClass`, field binding, field-specific configuration, and filters.
3. Map the page type to its Java implementation and Velocity view.
4. Check the rendered field name, object-number source, document context, language, and request parameters.
5. Check view rights and central-wiki fallback.

For code changes:

1. Update the class definition when new configuration is stored on XWiki objects.
2. Update the Java page type when a field type needs new attribute handling.
3. Add or update its view and field-configuration templates.
4. Preserve `META-INF/components.txt` registration unless Spring scanning has been verified.
5. Update JavaScript or CSS only where the rendered templates include it.
6. Run focused tests under `component/src/test/java` and check whitespace on changed files.
