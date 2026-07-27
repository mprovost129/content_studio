# Code with Michael Content Studio TODO

## Completed in phase 32
- Added `RecommendationTuning` for editable CTA recommendation weights.
- Added migration `0024_recommendation_tuning.py` with a seeded default tuning profile.
- Added private tuning screen at `/studio/recommendations/tuning/`.
- Added admin support for recommendation tuning profiles.
- Connected tuning values to resource CTA recommendation ranking.
- Made lesson, quiz, challenge, PDF, PDF lead magnet, and newsletter CTA bonuses editable.
- Made lesson matching weights editable for related lesson, category, learner level, keyword overlap, quiz/challenge availability, practice code, conversions, and clicks.
- Made feedback weights editable for accepted, dismissed, ignored, similar-resource, and same-lesson signals.
- Added tuning links to Dashboard, Studio navigation, Resource detail pages, and Recommendation feedback report.
- Added tests for tuning-driven ranking and the tuning update screen.

## Recommended next phase
1. Add a tuning change history/audit log so you can see when recommendation weights were changed and why.
2. Add tuning presets such as Lead Magnet Growth, Lesson Completion, Quiz Engagement, and Challenge Practice.
3. Add side-by-side recommendation simulation before saving tuning changes.
4. Add CSV export for recommendation feedback and tuning impact analysis.


## Completed in phase 24
- Added generated branded PDF downloads for public learning resources.
- Added `pdf_download_enabled` and `pdf_footer_note` fields to `LearningResource`.
- Added public route `/learn/resources/<slug>/download.pdf` for eligible Ready/Published resources.
- Added private Studio PDF preview route `/studio/resources/<slug>/pdf/`.
- Added ReportLab-based PDF rendering service for resource headings, paragraphs, bullet lists, fenced code blocks, beginner tips, metadata, related lessons, and branded footers.
- Added generated PDF links to public and Studio resource detail pages.
- Updated resource generation so cheat sheets, practice references, and downloadable references enable generated PDFs by default.
- Added migration `0018_learning_resource_pdf_fields.py`.
- Added tests for PDF downloads, disabled-PDF redirects, and generated resource PDF defaults.

## Recommended next phase
1. Add downloadable PDF thumbnails/previews on Studio resource pages.
2. Add optional PDF lead-magnet gating for selected resources.
3. Add a printable worksheet resource type with answer keys.
4. Add S3-compatible media storage before production deployment.

## Completed in phase 19
- Added saved `SubscriberSegment` records for reusable newsletter audience groups.
- Added rule-based segment matching by subscriber status, signup source, learner skill level, source lesson, subscribed date window, rolling recency, and keyword.
- Added segment management screens at `/studio/newsletter/segments/`.
- Added segment create/edit/delete screens and per-segment subscriber CSV export.
- Added optional saved segment targeting to newsletter campaigns while preserving the existing quick segment dropdown.
- Campaigns now auto-fill estimated recipients from the saved segment when no estimate is entered.
- Added newsletter segment performance reporting at `/studio/newsletter/segments/performance/`.
- Added CSV export for segment performance reporting.
- Added dashboard and navigation links for saved audience segments.
- Added migration `0015_subscriber_segments.py`.

## Recommended next phase
1. Add email-platform integration preparation fields, such as external audience IDs, campaign IDs, and provider sync status.
2. Add resource-library pages for cheat sheets, common Python errors, and beginner setup guides.
3. Add S3-compatible media storage before production deployment on Render or similar hosting.
4. Add visual thumbnails to performance reports so top social posts are easier to review.

## Completed in phase 15
- Added CSV export for the private performance report.
- Added downloadable posted-content rows that match the selected date range and platform filter.
- Added downloadable format summary, platform summary, and format-by-platform matrix CSV files.
- Included useful spreadsheet columns such as content format, source, engagement rate, clicks, follower growth, caption snapshot, and notes.
- Added export buttons directly to `/studio/reports/performance/`.
- Added test coverage for filtered CSV downloads and format-summary exports.
- No migration required.

## Recommended next phase
1. Add lightweight email capture/newsletter workflow for beginner learners.
2. Add public resource pages for cheat sheets, common Python errors, and beginner setup guides.
3. Move generated media to S3-compatible storage before production deployment on Render or similar hosting.
4. Add image/comparison previews to performance reports so top posts are easier to evaluate visually.

## Completed in phase 14
- Added public SEO infrastructure for the learner website.
- Added `/sitemap.xml` with public learner routes, learning paths, and published/ready lessons.
- Added `/robots.txt` that allows the public learner site while blocking private Studio, admin, and account pages.
- Added `/feed.xml` RSS feed for the latest public Python lessons.
- Added canonical URL support across public learner pages.
- Added Open Graph/Twitter summary metadata for public learner pages.
- Added JSON-LD structured data for the learner homepage, individual lessons, and learning paths.
- Centralized SEO URL/schema helpers in `studio.services.seo`.
- No migration required.

## Completed in phase 13
- Added `/studio/reports/performance/` for private staff performance reporting.
- Added date-range and platform filters for publishing analytics.
- Added content-format ranking based on connected content plan carousel templates, then graphic templates, then caption/manual entry fallback.
- Added platform totals for posts, reach, engagement, clicks, and follower growth.
- Added format-by-platform breakdown to identify which post types work best on each platform.
- Added top-post ranking by follower growth, engagement, and reach.
- Added Reports navigation and dashboard shortcuts.
- No migration required.

## Completed in phase 11
- Added `PublishingRecord` to track posted content by platform.
- Added publishing fields for publish date, post URL, connected caption draft, connected graphic asset, final caption snapshot, notes, impressions, reach, likes, comments, saves, shares, clicks, follower growth, and follower count after posting.
- Added studio create/edit/delete screens for publishing records.
- Added a publishing panel to each private lesson detail page.
- Added recent publishing records and platform performance totals to the content calendar.
- Added dashboard metrics for recorded impressions and follower growth.
- Automatically updates Facebook, Instagram, Threads, or Website lesson platform status to Published when a matching publishing record is saved.
- Updated website exports to schema `1.3` with publishing record summaries.
- Added migration `0010_publishing_record.py`.

## Completed in phase 10
- Added social carousel templates mapped to Code with Michael brand-growth post formats:
  - Concept Explanation
  - Beginner Mistake
  - Spot the Bug
  - Code Output Quiz
  - Three Things to Remember
- Added a private social carousel application action at `/studio/lessons/<slug>/social-carousels/apply/`.
- Added a **Social Carousels** panel to lesson detail pages.
- Social carousel templates append carousel-ready lesson blocks using the lesson's title, summary, takeaway, common mistake, code, and expected output where available.
- Added matching reusable `GraphicTemplate` records on first use so each social carousel format can be reused from the normal graphics generator.
- Added optional immediate PNG generation when applying a social carousel template.
- Updated the Studio help guide with carousel format guidance and recommended posting cadence.

## Completed in phase 9
- Added reusable block templates that can be applied from a lesson detail page.
- Added templates for Beginner Concept, Code Example, Try It Yourself, Common Mistake, Spot the Bug, and Mini Project.
- Templates can append normal lesson blocks, structured quiz questions, code challenges, and challenge test cases.
- Added a private template-application action at `/studio/lessons/<slug>/blocks/templates/apply/`.
- Added template summaries to the lesson sidebar and updated the Studio help guide.
- Preserved U.S. dollar formatting in generic money/price practice content.

## Completed in phase 8
- Added a private **Generate lesson from idea** workflow at `/studio/lessons/generate/`.
- Added `LessonIdeaForm` for topic, audience, objective, optional category, optional series, quiz toggle, and challenge toggle.
- Added deterministic draft generation that creates a beginner lesson without requiring an OpenAI API call.
- Generated drafts now include beginner lesson fields, SEO title/description, explanation/code/output/tip blocks, optional structured quiz, optional code challenge, and an optional test case.
- Added dashboard and staff navigation links for the generator.
- Added a dedicated generator template and form styling.
- Preserved US dollar formatting for generic money/price lesson examples.

## Completed in phase 7
- Added learner-facing challenge attempt detail pages at `/learn/challenge-attempts/<id>/`.
- Added saved submitted-code review, observed output, individual test result review, prompt recap, and solution reveal on attempt detail pages.
- Linked dashboard recent challenge attempts and activity history challenge submissions to their saved attempt review pages.
- Added a “My code submissions for this lesson” section to public lesson pages for authenticated learners.
- Updated challenge save responses to include the saved attempt review URL.
- Fixed the learner dashboard weekly-goal percentage calculation.

## Completed in phase 6
- Added learner profile fields to the custom user model: display name, skill level, learning goal, weekly goal minutes, lesson reminder preference, and product update preference.
- Added `/accounts/profile/` so learners can edit their profile and preferences.
- Added `/learn/activity/` as a learner-facing history page for lesson progress, quiz attempts, code challenge submissions, and badge awards.
- Expanded the learner dashboard with a personalized heading, profile link, weekly practice target, recent quiz attempts, and recent challenge attempts.
- Updated learner navigation with Profile and Activity links.
- Updated admin support for learner profile fields and preferences.

## Completed in phase 5
- Added `ChallengeTestCase` so code challenges can validate function return values and printed output, not only one expected output string.
- Added studio CRUD screens for challenge test cases.
- Added test-case duplication when duplicating a lesson.
- Added public “Run tests” controls for code challenges with active test cases.
- Added saved test results, tests passed, and tests total fields to `ChallengeAttempt`.
- Updated challenge attempt saving so progress uses full test-case success when tests exist.
- Updated website exports to schema `1.2` with challenge test-case payloads.
- Added admin support for challenge test cases and richer challenge attempt review.

## Completed in phase 4
- Added optional learner account registration at `/accounts/signup/`.
- Added a learner progress dashboard at `/learn/dashboard/`.
- Added lesson completion tracking with `LessonProgress`.
- Added saved quiz attempts with `QuizAttempt`.
- Connected public quiz buttons to server-side attempt tracking for logged-in learners.
- Connected runnable code challenges to saved `ChallengeAttempt` records for logged-in learners.
- Added badge models and seed badges:
  - First Python Win
  - Python Starter
  - Quiz Checkpoint
  - Code Runner
- Updated public navigation so learners see learner pages and staff users can still access Studio.
- Restricted Studio views/actions to staff users so learner accounts cannot access the private creator dashboard.
- Changed the default login redirect to the learner dashboard while preserving `next=` redirects for Studio links.
- Added admin views for progress, quiz attempts, badges, and badge awards.

## Completed in phase 3
- Added structured quiz/challenge models:
  - `QuizQuestion`
  - `QuizChoice`
  - `CodeChallenge`
  - `ChallengeAttempt` foundation for future learner tracking
- Added studio CRUD screens for quiz questions, answer choices, and code challenges.
- Added structured quiz/challenge sections to the private lesson detail page.
- Updated duplicate lesson behavior so copied lessons include blocks, quiz questions, answer choices, and code challenges.
- Updated beginner-readiness diagnostics to count structured quizzes and challenges.
- Updated the public lesson page to display interactive quiz choices and runnable code challenges.
- Updated the public playground output checker to support exact output, contains output, and manual review modes.
- Updated website exports to schema `1.1` with structured quiz/challenge payloads.
- Added quiz/challenge support to admin.

## Completed in phase 2
- Added a public learner layer at `/learn/` that is separate from the private `/studio/` creator dashboard.
- Added public beginner lesson listing, searchable public lesson library, learning path pages, public lesson detail pages, and a standalone browser Python playground.
- Added a studio content calendar at `/studio/calendar/` with kanban-style lesson status columns and platform backlog tracking.
- Added navigation links for Calendar and Public Learn.
- Updated public lesson pages to show beginner objective, takeaway, common mistake, practice prompt, hints, starter code, solution reveal, expected output, and runnable code when playground is enabled.
- Updated playground JavaScript to support expected-output comparison for beginner challenges.
- Updated website export canonical URL pattern from `/lessons/<slug>/` to `/learn/<slug>/`.

## Already completed in phase 1
- Added beginner lesson fields: learning objective, beginner takeaway, common mistake, practice prompt, starter code, solution code, expected output, hints, and next lesson.
- Added separate Facebook, Instagram, Threads, and Website production statuses.
- Added beginner-readiness quality diagnostics.
- Added duplicate lesson and duplicate block actions.
- Added JSON validation for block structured data.
- Added beginner learning fields to private previews and exports.


## Completed in phase 12
- Added `ContentPlan` for weekly post planning before publishing.
- Added `/studio/planner/` as a week-at-a-glance planner with previous/next week navigation.
- Added planned-post CRUD screens from each lesson.
- Added planned post fields for platform, scheduled date/time, status, carousel template key, caption, graphic, post goal, and notes.
- Added planned posts to lesson detail pages with shortcuts to edit, delete, or record the final published post.
- Added upcoming planned posts to the dashboard and content calendar.
- Connected planned posts to publishing records so recording a post can mark the matching plan as posted.
- Added admin support for content plans.
- Updated website exports to schema `1.4` with `content_plans` data.



## Completed in phase 16
- Added `NewsletterSubscriber` for lightweight email capture.
- Added public newsletter signup at `/learn/newsletter/signup/`.
- Added signup forms to the public learner homepage and public lesson pages.
- Added source tracking for signups from the homepage, lesson pages, playground/import/manual sources, source URL, source lesson, and linked learner account when available.
- Added private subscriber management at `/studio/subscribers/`.
- Added subscriber editing for status, source metadata, consent text, and notes.
- Added subscriber CSV export at `/studio/subscribers/export/`.
- Added dashboard subscriber metrics and recent subscriber activity.
- Added admin support and tests for newsletter signup/export.


## Phase 17 completed - Newsletter campaign planning

- Added newsletter campaign planning, scheduling, status tracking, and performance fields.
- Added lesson-based deterministic newsletter draft generation.
- Added campaign list, create, edit, delete, and mark-sent workflows.
- Connected campaigns to Email content plans and optional Email publishing records.
- Updated website export schema to `1.5` with `newsletter_campaigns` data.

## Recommended next phase

Add imported email performance CSV support so Mailchimp/Beehiiv/ConvertKit metrics can be pasted or uploaded into campaign records without manual entry.

## Phase 18 complete - Email performance import
- Added newsletter campaign metric imports for Mailchimp, Beehiiv, ConvertKit, manual pasted summaries, and generic CSV exports.
- Added `/studio/newsletter/metrics/import/` and campaign-specific import shortcuts.
- Added normalized parsing for recipients, opens, clicks, unsubscribes, and bounces.
- Added import history with provider, raw payload snapshot, normalized data, warnings, and importer.
- Added automatic campaign metric updates and optional mark-sent behavior after import.

## Recommended next phase
- Add audience segmentation workflows: saved subscriber segments, campaign targeting rules, and segment performance reporting.

## Phase 20 complete - Email provider integration preparation
- Added shared email provider choices for Not connected, Mailchimp, Beehiiv, ConvertKit, and Other.
- Added shared provider sync statuses for Not connected, Ready to sync, Synced, Needs review, and Error.
- Added provider mapping fields to newsletter subscribers:
  - external provider
  - external contact/subscriber ID
  - external list/audience/publication ID
  - provider sync status
  - provider last synced timestamp
  - provider notes
- Added provider mapping fields to saved subscriber segments:
  - external provider
  - external segment/tag/audience ID
  - external audience/list/publication ID
  - provider sync status
  - provider last synced timestamp
  - provider notes
- Added provider mapping fields to newsletter campaigns:
  - external provider
  - external campaign ID
  - external audience/list/publication ID
  - provider dashboard URL
  - provider sync status
  - provider last synced timestamp
  - provider notes
- Added provider/sync filtering to campaign and subscriber management screens.
- Added provider/sync data to subscriber and segment CSV exports.
- Added provider/sync admin filters and search fields.
- Updated website export schema to `1.6` with optional campaign provider metadata.

## Recommended next phase
- Add a provider sync readiness report that lists missing external IDs, sync errors, records ready to sync, and records needing review before a future API integration is connected.

## Phase 21 complete - Provider sync readiness report
- Added a private provider sync readiness report at `/studio/newsletter/provider-readiness/`.
- Added CSV export at `/studio/newsletter/provider-readiness/export/`.
- Reports include subscribers, saved segments, and newsletter campaigns.
- Added filters for record type, provider, sync status, and readiness issue.
- Readiness issues include Not connected, Missing provider IDs, Ready to sync, Synced, Needs review, and Error.
- Added dashboard metrics and navigation links for provider sync readiness.
- Added provider readiness guidance to Studio Help.
- No migration required.

## Recommended next phase
- Add resource-library pages for cheat sheets, common Python errors, and beginner setup guides.
- Add direct provider API connectors later only after the readiness report and external IDs are stable.
- Move generated media to S3-compatible storage before production deployment on Render or similar hosting.

## Phase 22 complete - Public resource library
- Added a public beginner Python resource library for cheat sheets, common Python errors, setup guides, practice references, vocabulary, and downloadable references.
- Added public routes:
  - `/learn/resources/`
  - `/learn/resources/<slug>/`
- Added Studio resource management routes:
  - `/studio/resources/`
  - `/studio/resources/new/`
  - `/studio/resources/<slug>/`
  - `/studio/resources/<slug>/edit/`
  - `/studio/resources/<slug>/delete/`
- Added `LearningResource` model with type, status, difficulty, category, tags, related lessons, featured flag, content body, beginner tip, optional file download, optional external URL, read time, SEO fields, and internal notes.
- Added resource pages to navigation, sitemap, SEO metadata, and JSON-LD structured data.
- Added featured resources to the public learner homepage.
- Added admin support and test coverage for public resource pages and Studio resource creation.
- Added migration `0017_learning_resources.py`.

## Recommended next phase
- Add a deterministic resource generator that creates starter cheat sheets, error guides, and setup guides from a short topic, similar to the existing Generate Lesson From Idea workflow.

## Phase 23 complete - Generate Resource From Idea
- Added a private resource generator at `/studio/resources/generate/`.
- Added `ResourceIdeaForm` for topic, resource type, audience, category, related lessons, and featured status.
- Added deterministic draft generation for:
  - Cheat sheets
  - Common Python error guides
  - Setup guides
  - Practice references
  - Python vocabulary resources
  - Downloadable reference drafts
- Generated resources include title, summary, beginner tip, content body, code example, expected output, SEO title, SEO description, read time, and internal review notes.
- Added generator shortcuts from the resource library and resource detail pages.
- No migration required.

## Recommended next phase
- Add downloadable PDF generation for resource pages so selected cheat sheets and references can be exported as branded Code with Michael PDFs.

## Completed in Phase 25 — PDF lead magnet controls

- [x] Added optional email gating for generated resource PDFs.
- [x] Added public unlock page for gated resource downloads.
- [x] Captured or reactivated newsletter subscribers from gated PDF downloads.
- [x] Stored resource source attribution on subscriber records.
- [x] Added `ResourceLeadMagnetAccess` tracking for access grants and download counts.
- [x] Added Studio/admin controls for PDF lead magnet headline and description.
- [x] Updated subscriber management and CSV export with resource attribution.
- [x] Added tests for gated and open generated PDF downloads.

## Recommended next phase — Resource performance reporting

- [ ] Add a resource report showing views, PDF unlocks, PDF downloads, and subscriber conversion by resource.
- [ ] Add CSV export for resource lead magnet performance.
- [ ] Highlight best-performing cheat sheets and downloadable references on the Studio dashboard.
- [ ] Connect resource performance back to lessons and social posts that promote each resource.

## Phase 26 complete - Resource performance reporting

- [x] Track public resource page views.
- [x] Track PDF unlocks for email-gated lead magnets.
- [x] Track branded PDF downloads for open and gated resources.
- [x] Add a private resource performance report with date, event, and resource-type filters.
- [x] Add CSV exports for resource summaries, resource-type summaries, and event logs.
- [x] Add resource performance metrics to the Studio dashboard and individual resource detail pages.
- [x] Add admin review for resource performance events.

### Recommended next phase

- Add resource-to-lesson conversion tracking so Studio can show whether cheat sheets and setup guides drive learners into lesson completions, quiz attempts, challenge attempts, and account creation.

## Phase 27 complete - Resource-to-lesson conversion tracking

- [x] Added last-touch resource attribution from public resource views, PDF unlocks, and PDF downloads.
- [x] Added `ResourceLessonConversionEvent` for resource-attributed learner actions.
- [x] Tracked resource-attributed lesson views.
- [x] Tracked resource-attributed account signups.
- [x] Tracked resource-attributed quiz attempts.
- [x] Tracked resource-attributed coding challenge attempts.
- [x] Tracked resource-attributed lesson completions.
- [x] Added a private resource conversion report with date, conversion-type, and resource-type filters.
- [x] Added CSV exports for resource conversion summaries, conversion action summaries, and raw conversion events.
- [x] Added dashboard metrics and navigation links for resource conversions.
- [x] Added admin support and tests for conversion attribution/reporting.

### Recommended next phase

- Add content recommendation blocks on resource pages, such as “Start the matching lesson,” “Try this quiz next,” and “Practice with a challenge,” then use the conversion report to evaluate which calls to action perform best.

## Phase 28 complete - Resource CTA blocks

- [x] Added `ResourceCTA` for editable resource-page call-to-action blocks.
- [x] Added CTA types for matching lessons, quizzes, challenges, resource PDFs, newsletter signup, and external links.
- [x] Added public CTA cards to resource detail pages.
- [x] Added `ResourceCTAClickEvent` for click tracking.
- [x] Connected CTA clicks to last-touch resource attribution so later learner actions can be tied back to a specific CTA.
- [x] Added CTA fields to resource-attributed conversion events.
- [x] Added Studio create/edit/delete screens for resource CTA blocks.
- [x] Added CTA summary and recent click sections to Studio resource detail pages.
- [x] Added Resource CTA Performance report with filters and CSV exports.
- [x] Added admin support and tests for CTA clicks and reporting.

### Recommended next phase

- Add automatic resource recommendation suggestions, so Studio can propose the best matching lesson, quiz, or challenge based on related lessons, lesson category, learner level, and prior resource conversion performance.

## Phase 29 complete - Automatic resource CTA recommendations

- [x] Added deterministic CTA recommendation service for learning resources.
- [x] Ranked matching lessons using related lessons, category, difficulty, topic overlap, active quizzes/challenges, CTA clicks, and conversion history.
- [x] Added suggested lesson, quiz, challenge, PDF, and newsletter CTAs to Studio resource detail pages.
- [x] Added one-click apply workflow that creates normal editable `ResourceCTA` records.
- [x] Prevented duplicate recommendations when a matching CTA already exists.
- [x] Added test coverage for recommendation ranking and one-click CTA creation.

### Recommended next phase

- Add a recommendation feedback loop so Studio can mark recommendations as accepted, dismissed, or ignored and use that history to improve future CTA suggestions.

## Phase 30 complete - CTA recommendation feedback loop

- [x] Added `ResourceCTARecommendationFeedback` to track recommendation state.
- [x] Tracked when Studio shows a recommendation so repeated no-action suggestions become visible as ignored signals.
- [x] Marked recommendations as accepted when staff apply them to create CTA blocks.
- [x] Added dismiss controls for recommendations that should not be shown as actionable.
- [x] Added recommendation feedback history to each Studio resource detail page.
- [x] Added a private CTA recommendation feedback report with status and CTA-type filters.
- [x] Added admin support and tests for recommendation feedback.

### Recommended next phase

- Use CTA recommendation feedback in ranking so dismissed suggestion types are deprioritized and accepted patterns receive a scoring boost across similar resources.

## Phase 31 complete - Feedback-aware CTA recommendation ranking

- [x] Applied recommendation feedback directly to CTA recommendation scores.
- [x] Boosted exact suggestions that were previously accepted.
- [x] Deprioritized exact suggestions that were previously dismissed.
- [x] Penalized suggestions repeatedly shown without action as ignored signals.
- [x] Boosted accepted CTA-type patterns across similar resources with the same resource type, difficulty, and category.
- [x] Deprioritized dismissed or ignored CTA-type patterns across similar resources.
- [x] Applied lighter same-lesson feedback signals when a lesson CTA was accepted or dismissed elsewhere.
- [x] Added base score, feedback adjustment, and feedback ranking notes to Studio resource recommendation cards.
- [x] Expanded the CTA recommendation feedback report so staff can see which feedback signals are shaping future suggestions.
- [x] Added tests for exact feedback penalties and accepted-pattern boosts.

### Recommended next phase

- Add recommendation tuning controls so Studio can set manual weights for lesson CTAs, quiz CTAs, challenge CTAs, PDF lead magnets, and newsletter CTAs without editing code.
