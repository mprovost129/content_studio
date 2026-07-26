# Website lesson export contract

Schema version: `1.0`

The Content Studio produces immutable, numbered export revisions. Every revision contains a standalone HTML page and a JSON document intended for future ingestion by the existing Code with Michael website.

## Top-level fields

- `schema_version`: Contract version. Consumers should reject unsupported major versions.
- `content_type`: Always `code_with_michael.lesson` for this contract.
- `exported_at`: ISO 8601 timestamp for the export operation.
- `lesson`: Website-ready lesson data.
- `brand`: Publisher name and social handle.

## Lesson fields

- Identity: `id`, `slug`, `title`, `status`
- Presentation: `summary`, `difficulty`, `difficulty_label`, `reading_minutes`, `accent_color`, `call_to_action`
- Interactivity: `playground_enabled` indicates whether compatible code blocks may run in a browser Python environment
- Organization: `category`, `tags`, `series`
- Discovery: `seo.title`, `seo.description`, `seo.canonical_url`
- Content: ordered `blocks`
- Media: generated `assets` with format, dimensions, slide number, URL, and alt text
- Change tracking: `updated_at`

## Content blocks

Every block contains `position`, `type`, `label`, `title`, `content`, and `data`. Consumers must preserve `position` ordering and gracefully ignore unfamiliar block types so new studio features remain backward compatible.

Current types are `heading`, `text`, `code`, `output`, `callout`, `list`, `image`, `quiz`, `challenge`, and `comparison`.

## Integration rules

1. Treat an export revision as immutable.
2. Use `content_hash` from the export record to detect unchanged lesson content.
3. Use the latest supported revision for website synchronization.
4. Do not infer publication from export creation; publishing remains a separate future action.
5. Escape rendered content according to its destination even though the studio-generated HTML is already escaped.
