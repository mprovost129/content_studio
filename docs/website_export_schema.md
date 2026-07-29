# Website lesson export contract

Schema version: `1.6`

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
- Beginner learning: `learning.objective`, `beginner_takeaway`, `common_mistake`, `practice_prompt`, `starter_code`, `solution_code`, `expected_output`, `hints`, `next_lesson`, `quiz_questions`, and `code_challenges`
- Organization: `category`, `tags`, `series`
- Discovery: `seo.title`, `seo.description`, `seo.canonical_url`
- Content: ordered `blocks`
- Media: generated `assets` with format, dimensions, slide number, URL, and alt text
- Planning: `content_plans` with platform, scheduled timestamp, planning status, carousel template key, post goal, notes, linked asset/caption flags, and optional publishing record linkage
- Publishing: `publishing_records` with platform, publish timestamp, URL, caption snapshot, key engagement metrics, follower growth, and calculated engagement data
- Email: `newsletter_campaigns` with planned or sent campaign metadata, audience segment, schedule/send dates, recipient counts, opens, clicks, calculated email rates, and optional provider sync metadata
- Change tracking: `updated_at`

## Content blocks

Every block contains `position`, `type`, `label`, `title`, `content`, and `data`. Consumers must preserve `position` ordering and gracefully ignore unfamiliar block types so new studio features remain backward compatible.

Current types are `heading`, `text`, `code`, `output`, `callout`, `list`, `image`, `quiz`, `challenge`, and `comparison`.

## Structured practice

`learning.quiz_questions` contains active structured quiz questions with ordered choices and answer flags. Use this for learner-facing checks and progress tracking.

`learning.code_challenges` contains active code challenges with starter code, optional solution code, expected output, hints, validation mode, and optional `test_cases`.

Each challenge test case contains:

- `position`
- `name`
- `description`
- `test_code` — Python code intended to run after the learner submission in a browser sandbox
- `expected_output` — optional exact stdout expected for that individual test

The studio does not execute learner code on the Django server. Browser-based consumers should run tests client-side or send submissions to a separate sandboxed execution service.


## Content plans

`content_plans` contains optional pre-publication scheduling data. Each plan contains:

- `platform` and `platform_label`
- `scheduled_at`
- `status` and `status_label`
- `carousel_template`
- `post_goal`
- `notes`
- `has_caption` and `has_graphic`
- `publishing_record_id` when the planned post has been connected to a saved publishing record

Content plans are editorial workflow data. They should not be treated as proof that content has been published.

## Publishing records

`publishing_records` contains optional post-performance data created after content is published. Each record contains:

- `platform` and `platform_label`
- `published_at`
- `post_url`
- `caption_text`
- `impressions`, `reach`, `likes`, `comments`, `saves`, `shares`, and `clicks`
- `new_followers` and `follower_count_after`
- `engagement_total` and `engagement_rate`

Publishing records are operational analytics. They should not be required for rendering the public lesson page.

## Newsletter campaigns

`newsletter_campaigns` contains optional email planning and performance data for lessons used in weekly emails. Each campaign contains:

- `title`, `subject`, and `preview_text`
- `status` and `status_label`
- `target_segment` and `target_segment_label`
- `scheduled_at` and `sent_at` when available
- `estimated_recipients` and `actual_recipients`
- `opens`, `clicks`, `open_rate`, `click_rate`, and `click_to_open_rate`

Campaigns are planning and analytics records. They are safe to ignore when rendering the public lesson page.

## Integration rules

1. Treat an export revision as immutable.
2. Use `content_hash` from the export record to detect unchanged lesson content.
3. Use the latest supported revision for website synchronization.
4. Do not infer publication from export creation or `content_plans`. Use `publishing_records` for real-world publication and performance history when present.
5. Escape rendered content according to its destination even though the studio-generated HTML is already escaped.


## Version 1.6 notes

Phase 20 adds email-platform integration preparation metadata to exported newsletter campaigns. These fields are optional and are intended for future Mailchimp, Beehiiv, ConvertKit, or custom-provider sync work:

- `external_provider` and `external_provider_label`
- `external_campaign_id`
- `external_audience_id`
- `provider_url`
- `provider_sync_status` and `provider_sync_status_label`
- `provider_last_synced_at`

The studio still treats sending and syncing as manual/planned actions. These fields provide stable mapping locations for future API integrations.
