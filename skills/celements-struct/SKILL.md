---
name: celements-struct
description: Use when changing Celements structured editor layouts, field bindings, object filters, object lists, autocomplete, or tables.
---

# Celements Struct

Celements Struct maps XWiki page-layout cells to document fields and XObjects. Treat Java and Velocity code as authoritative; exported layouts only illustrate possible DB content.

## Start Here

- `component/src/main/java/com/celements/struct/DefaultStructDataService.java`
- `component/src/main/java/com/celements/struct/StructDataScriptService.java`
- `component/src/main/java/com/celements/structEditor/DefaultStructuredDataEditorService.java`
- `component/src/main/java/com/celements/structEditor/*ScriptService.java`
- `component/src/main/java/com/celements/structEditor/fields/*PageType.java`
- `component/src/main/java/com/celements/structEditor/classes/*EditorClass.java`
- `component/src/main/java/com/celements/struct/classes/*Class.java`
- `component/src/main/java/com/celements/struct/table/*PresentationType.java`
- `web-module/src/main/webapp/templates/celTemplates/StructuredDataEditorView.vm`
- `web-module/src/main/webapp/templates/celMacros/struct/renderEditorLayout.vm`
- `web-module/src/main/webapp/templates/celTemplates/fieldTypeEdit/*.vm`
- `web-module/src/main/webapp/resources/structEditJS/*.mjs`

## Layout And Binding

`StructuredDataEditor` and `StructuredDataView` resolve a layout space, include its resources, and render its page-layout tree. Layout resolution is:

1. Existing `Celements.StructLayoutClass.layoutSpace` on the current document.
2. `<PageType>-EditFields` for page types with an edit template, otherwise `<PageType>-StructData`.
3. The same layout in the central wiki when local content is absent.

`Celements.StructEditFieldClass` binds a cell to an XObject property or document `title`/`content` through:

- `edit_field_class_fullname`
- `edit_field_name`
- `multilingual`
- `computed_obj_nb`

Normal XObject input names follow `Space.Class_0_field`. Request values override stored values.

Object number resolution checks request parameters, execution context, `computed_obj_nb`, the first matching object, then a request-cached negative number for a new object. Inspect rendered field names and object-number parameters before changing Java.

## Filters And Field Types

`Classes.KeyValueClass` objects on a cell define Velocity-evaluated filters:

- `struct-obj-filter` and `struct-obj-filter-and`: AND
- `struct-obj-filter-or`: OR

Filters affect object selection, object streams, request keys, and new-object numbers. A CelTag filter named `type` may also select its tag type.

Current page types include `FormField`, `InputTag`, `NumberTag`, `TextAreaTag`, `SelectTag`, `OptionTag`, `SelectTagAutocomplete`, `DateTime`, `HiddenTag`, `DisplayField`, `LabelTag`, `LanguageSelector`, `SubmitLink`, `ObjectList`, and `Table`.

Prefer current names over legacy `InputField`, `TextAreaField`, and `DateTimePicker` unless existing DB layouts depend on them. Field configuration lives in matching `*EditorClass` classes and `celTemplates/fieldTypeEdit/` templates.

## Autocomplete And Tables

`SelectTagAutocomplete` delegates search and selected-value behavior to an `AutocompleteRole`. Custom implementations need a distinct component hint and may provide extra JS through `getJsFilePath()`.

`Celements.StructTableClass` supports:

- `DOC`: query documents.
- `OBJ`: iterate matching XObjects on the current document.
- `OBJLINK`: resolve linked documents from `reference`, `ref`, or `link`.

Optional `StructTableColumnClass` objects sort by `order`, then object number. Column content resolves from configured Velocity, `col_<name>.vm`, an XObject field, then an XDocument pseudo-field. Without columns, `header_layout` and `row_layout` render through `LayoutServiceRole` with wiki fallback.

Client-created objects use negative numbers. Deletion marks form names with a `^`-prefixed object number. `StructEditor.mjs`, `cel-table.mjs`, and `StructObjectListEdit.mjs` manage this client behavior.

## Debugging And Changes

For a layout issue, identify the document page type and resolved layout, inspect the cell page type and objects, map it to Java and Velocity, then check field names, object number, language, request values, rights, and central-wiki fallback.

For a new stored option or field type, update the XClass definition, Java page type, view template, and field configuration template as needed. Register legacy components in `META-INF/components.txt` unless Spring scanning deliberately replaces registration. Run focused component tests and relevant client checks.
