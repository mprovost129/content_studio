## Phase 65: Complete Site Usage Instructions

Completed:

- Added `docs/SITE_USER_GUIDE.md` as the master operator guide for the public learner site and private Studio.
- Added step-by-step workflows for lessons, quizzes, challenges, resources, PDFs, lead magnets, CTAs, newsletters, publishing records, reports, recommendations, tuning, decision rules, snapshots, saved reports, templates, and Project Health.
- Marked major selections and fields as Required or Optional throughout the guide.
- Updated `README.md` with a prominent link to the new guide.

Recommended next work:

- Run the project locally and validate every guide path against the rendered navigation.
- Decide whether deeply nested advanced recommendation routes should be grouped under a simplified Reports or Experiments navigation page.
- Create seed/demo content so the guide can be followed with example lessons, resources, subscribers, and reports.


## Completed in phase 62
- Added `ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot` for before/after threshold-experiment snapshots.
- Added migration `0045_report_template_recommendation_decision_rule_snapshots.py`.
- Added snapshot create/list/detail/export routes for template-recommendation decision-rule changes.
- Added history-page shortcuts from decision-rule audit entries to create experiment snapshots.
- Added CSV export for template usage, saved report, report decision, and recommendation feedback deltas.
- Added admin visibility, navigation/help links, and test coverage for snapshot creation/export.

## Recommended next phase
1. Add decision recommendations for these decision-rule experiment snapshots.
2. Add editable decision thresholds specifically for decision-rule snapshot outcomes.
3. Add snapshot comparison across multiple decision-rule threshold experiments.
4. Add saved reports for decision-rule threshold snapshot comparisons.


## Phase 56: Report-template recommendation tuning experiments

Phase 56 adds experiment labels and outcomes to report-template recommendation tuning changes. Staff can now treat template-ranking weight updates as named experiments, record a hypothesis when saving the tuning change, filter audit history by experiment status/outcome, and later record whether the experiment was positive, negative, neutral, or inconclusive.

New migration:

- `studio/migrations/0040_report_template_recommendation_tuning_experiments.py`

Updated private Studio behavior:

- The Template tuning form includes optional experiment label, status, and hypothesis/notes fields.
- Template tuning history can be filtered by action, experiment status, experiment outcome, and experiment label.
- Each tuning history row now includes a Record outcome action.
- CSV exports include experiment labels, statuses, outcomes, notes, and outcome recorder metadata.
- Admin now exposes experiment status/outcome filters for template-recommendation tuning logs.

# Code with Michael Content Studio TODO

## Completed in phase 54
- Added `ReportTemplateRecommendationTuning` for editable saved report-template recommendation weights.
- Added migration `0038_report_template_recommendation_tuning.py` with a seeded default active profile.
- Added private Studio tuning route at `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/`.
- Connected active tuning values to report-template recommendation scoring, priority thresholds, usage weights, decision-outcome weights, focus-area/preset bonuses, and feedback boosts/penalties.
- Added active tuning visibility to the recommendation page and CSV export.
- Added navigation, admin support, and tests for template recommendation tuning.

## Recommended next phase
1. Add audit logging for report-template recommendation tuning changes.
2. Add preset profiles for template recommendations, such as Monthly Growth Bias, Lead Magnet Bias, and Learning Conversion Bias.
3. Add side-by-side simulation for report-template recommendation tuning before saving.
4. Add rollback controls once audit logging exists.

## Completed in phase 48
- Added report-level decision status for saved decision-rule snapshot comparison reports.
- Added statuses: No decision yet, Keep, Roll back, Watch, and Archived.
- Added decision summary, decision notes, decision owner, recorded-by, and recorded-at tracking.
- Added decision filters and status badges to the saved report list.
- Added decision blocks to saved report detail pages and printable reports.
- Added decision fields to CSV exports and admin screens.
- Added migration `0033_comparison_report_decision_status.py`.

## Recommended next phase
1. Add report cloning so a saved report can be reused for a new month or experiment family.
2. Add optional public/share-token links for selected report summaries.
3. Add scheduled monthly report reminders.
4. Add decision follow-up tasks with due dates.

## Completed in phase 47
- Added print-optimized saved decision-rule snapshot comparison report pages.
- Added route `/studio/recommendations/tuning/decision-rules/experiments/snapshots/reports/<id>/print/`.
- Added a standalone printable template with Code with Michael branding.
- Added executive summary cards for snapshots, decision profiles, most common recommendation, and largest metric movement.
- Preserved visual charts, recommendation matrix, summary table, and full metric comparison in the printable view.
- Added a **Print / Save as PDF** button and print-specific CSS.
- Added Studio detail-page link and test coverage.

## Recommended next phase
1. Add report cloning so a saved report can be reused for a new month or experiment family.
2. Add optional public/share-token links for selected report summaries.
3. Add scheduled monthly report reminders.
4. Add decision follow-up tasks with due dates.

## Completed in phase 45
- Added `ExperimentDecisionTuningSnapshotComparisonReport` for saved decision-rule snapshot comparisons.
- Added migration `0032_decision_rule_snapshot_comparison_reports.py`.
- Added saved report list, create, detail, edit, delete, and CSV export routes.
- Added Save report action from the live decision-rule snapshot comparison page.
- Saved reports preserve selected snapshots, selected decision-rule presets, description, and staff notes.
- Saved report detail pages show summary deltas, decision recommendation matrix, and full metric comparison.
- Added Studio navigation, Help links, admin support, and tests.

## Recommended next phase
1. Add visual comparison charts for saved snapshot reports.
2. Add shareable internal report links or PDF export for stakeholder review.
3. Add report-level decision status, such as Keep, Roll Back, Watch, or Archived.
4. Add report cloning so a saved report can be reused for a new month or experiment family.

## Completed in phase 35
- Added rollback controls for recommendation tuning audit entries.
- Added rollback review page at `/studio/recommendations/tuning/history/<id>/rollback/`.
- Staff can compare current active weights against the before-change and after-change snapshots from any tuning history record.
- Staff can restore either the before-change snapshot or after-change snapshot after review.
- Rollbacks are logged as new `Rollback restored` audit entries with before/after snapshots, field-level diffs, staff user, request path, and optional reason notes.
- Added restore links from the tuning history table.
- Added admin/search/filter support through the existing tuning change log model.
- Added tests for rollback review and restoring prior snapshots.

## Recommended next phase
1. Add visual score-delta charts comparing active tuning against simulated presets.
2. Add CSV export for recommendation feedback and tuning impact analysis.
3. Add optional experiment labels for tuning changes, such as "August Instagram growth test."
4. Add notes/outcome fields to rollback logs so completed experiments can record what happened.

## Completed in phase 34
- Added `RecommendationTuningChangeLog` for recommendation-weight audit history.
- Added migration `0025_recommendation_tuning_change_log.py`.
- Logged manual tuning saves with before/after snapshots, field-level diffs, user, request path, and optional reason notes.
- Logged preset applications with preset key, preset name, changed fields, user, and default reason text.
- Added tuning change history page at `/studio/recommendations/tuning/history/`.
- Added tuning change history CSV export at `/studio/recommendations/tuning/history/export/`.
- Added tuning-history links to navigation, dashboard, tuning, simulation, feedback, and help screens.
- Added admin support and test coverage for tuning history and CSV export.

## Recommended next phase
1. Add visual score-delta charts comparing active tuning against simulated presets.
2. Add CSV export for recommendation feedback and tuning impact analysis.
3. Add optional experiment labels for tuning changes, such as "August Instagram growth test."
4. Add rollback controls to restore a prior tuning snapshot after review.

## Completed in phase 33
- Added built-in recommendation tuning presets: Lead Magnet Growth, Lesson Completion, Quiz Engagement, and Challenge Practice.
- Added preset application from the private tuning screen.
- Added side-by-side recommendation simulation at `/studio/recommendations/tuning/simulation/`.
- Simulation compares active tuning against selected presets for a real learning resource without saving changes.
- Updated the recommendation service so simulated, unsaved tuning profiles can be passed into ranking.
- Added a preset service with shared tuning field copying, preset rows, and active-profile application.
- Added navigation, dashboard, help, and tuning-screen links for simulation.
- Added tests for preset application and read-only simulation behavior.

## Recommended next phase
1. Add a tuning change history/audit log so you can see when recommendation weights were changed, who changed them, and why.
2. Add CSV export for recommendation feedback and tuning impact analysis.
3. Add visual score-delta charts comparing active tuning against simulated presets.
4. Add optional per-resource tuning notes when a resource consistently needs a different recommendation strategy.

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


## Phase 36 complete - Recommendation tuning experiment labels and outcomes

- [x] Added experiment label, status, outcome, notes, outcome timestamp, and outcome recorder to tuning change logs.
- [x] Added migration `0026_recommendation_tuning_experiments.py`.
- [x] Added experiment fields to manual tuning saves.
- [x] Added optional experiment label/hypothesis fields to preset applications.
- [x] Added a staff page to record or update tuning experiment outcomes.
- [x] Added tuning history filters for experiment status, outcome, and label search.
- [x] Added active/completed experiment metrics to the tuning history screen.
- [x] Added experiment fields to tuning history CSV exports.
- [x] Added admin support for experiment tracking fields.

### Recommended next phase

- Add experiment performance snapshots that compare social, resource, newsletter, and CTA metrics before and after a tuning experiment window.


## Phase 37 — Experiment Performance Snapshots

- Added before/after performance snapshots for recommendation tuning experiments.
- Added snapshot generation from tuning change history with 7, 14, 30, or 60 day windows.
- Added metrics across social publishing, resource-library events, newsletter campaigns, resource CTA clicks, and resource-to-lesson conversions.
- Added snapshot detail pages, snapshot list page, CSV export, admin support, and navigation links.
- Snapshots are read-only records, so experiments can be reviewed later even after additional performance data changes.

## Phase 38 — Experiment Decision Recommendations

- Added deterministic keep / rollback / inconclusive recommendations for experiment performance snapshots.
- Evaluated before/after deltas across social publishing, resource downloads, newsletter clicks, CTA clicks, and learner conversions.
- Added positive and negative signal explanations so staff can see why a recommendation was made.
- Added confidence level and decision score to each snapshot detail page.
- Added one-click recording of the decision recommendation back onto the tuning experiment outcome.
- Recorded decision notes append to the existing experiment notes instead of replacing prior context.
- Added tests for keep and rollback recommendation paths.

### Recommended next phase

- Add experiment decision thresholds and weights as editable Studio settings so keep/rollback/inconclusive rules can be tuned without editing code.

## Phase 39 complete - Editable experiment decision thresholds and weights

- [x] Added `ExperimentDecisionTuning` for editable keep / rollback / inconclusive decision rules.
- [x] Added migration `0028_experiment_decision_tuning.py` with a seeded default active rules profile.
- [x] Added private Studio decision-rules screen at `/studio/recommendations/tuning/decision-rules/`.
- [x] Connected experiment decision recommendations to the active decision-rules profile.
- [x] Added editable weights for social, resource, newsletter, CTA, and learner-conversion metrics.
- [x] Added editable thresholds for keep, rollback, confidence, and per-metric score caps.
- [x] Added top weighted-signal explanations to experiment snapshot detail pages.
- [x] Added admin support and test coverage.

Next recommended phase:

- Add versioned decision-rule history/audit logging so changes to keep / rollback thresholds can be reviewed and rolled back like CTA recommendation tuning.


## Phase 40 complete - Decision-rule audit logging

- Added audit logging for experiment decision-rule changes.
- Added decision-rule history, CSV export, and rollback review/restore flow.
- Logged manual decision-rule saves and rollback restores with before/after snapshots and field-level diffs.

Next recommended phase: decision-rule presets and simulation for aggressive growth, conservative quality, and balanced learning outcomes.

## Phase 41 complete - Decision-rule presets and simulation

- [x] Added built-in decision-rule presets for Aggressive Growth, Conservative Quality, Balanced Learning, and Lead Magnet Focus.
- [x] Added read-only decision-rule simulation against saved experiment snapshots.
- [x] Added side-by-side keep / rollback / inconclusive comparisons by preset.
- [x] Added one-click preset application from the decision-rule screen and simulation screen.
- [x] Logged preset applications in the existing decision-rule audit log.
- [x] Added navigation, templates, tests, README, and TODO updates.

Next recommended phase:

- Add decision-rule preset experiment labels/outcomes so preset-based decision-rule changes can be tracked as named rule experiments.

## Phase 42 complete - Decision-rule preset experiment labels and outcomes

- [x] Added experiment labeling fields to decision-rule change logs.
- [x] Added preset key/name tracking for decision-rule preset applications.
- [x] Added experiment status, outcome, notes, recorded-at, and recorded-by fields.
- [x] Added migration `0030_experiment_decision_rule_experiments.py`.
- [x] Added experiment fields to manual decision-rule saves.
- [x] Added optional experiment label and hypothesis fields to preset application cards.
- [x] Added decision-rule outcome recording page from decision history.
- [x] Added experiment status/outcome/label filters to decision-rule history.
- [x] Added experiment fields to decision-rule history CSV export.
- [x] Added admin support and test coverage.

Next recommended phase:

- Add decision-rule experiment snapshots so preset-based decision-rule changes can compare before/after performance using the same social, resource, newsletter, CTA, and learner-conversion metrics.

## Phase 43 complete - Decision-rule experiment snapshots

- [x] Added decision-rule experiment performance snapshots for decision-rule preset/manual changes.
- [x] Added `ExperimentDecisionTuningExperimentSnapshot` model.
- [x] Added migration `0031_experiment_decision_rule_snapshots.py`.
- [x] Added snapshot creation from decision-rule history with 7, 14, 30, and 60 day windows.
- [x] Added before/after metrics across social publishing, resource performance, newsletters, CTA clicks, and resource-to-lesson conversions.
- [x] Added decision-rule snapshot list, detail review, CSV export, and admin support.
- [x] Connected decision-rule snapshots to the existing keep / rollback / inconclusive recommendation engine.
- [x] Added one-click recording of snapshot recommendations back onto decision-rule experiment outcomes.
- [x] Updated decision-rule simulation to use decision-rule snapshots instead of recommendation-tuning snapshots.

Next recommended phase:

- Add decision-rule experiment snapshot comparison, so multiple snapshots or rule presets can be compared side-by-side across different experiment windows.

## Phase 44 complete - Decision-rule snapshot comparison

- [x] Added side-by-side decision-rule experiment snapshot comparison.
- [x] Added comparison route `/studio/recommendations/tuning/decision-rules/experiments/snapshots/compare/`.
- [x] Added comparison CSV export route `/studio/recommendations/tuning/decision-rules/experiments/snapshots/compare/export/`.
- [x] Compared selected snapshots across follower growth, resource downloads, newsletter clicks, CTA clicks, and learner conversions.
- [x] Added a full metric comparison table across social, resource, newsletter, CTA, and conversion sections.
- [x] Added decision recommendation matrix so active rules and optional rule presets can be compared against each snapshot.
- [x] Added links from snapshot list/detail pages into the comparison workflow.
- [x] Added test coverage for comparison pages and CSV export.

Next recommended phase:

- Add saved snapshot comparison reports so useful multi-snapshot comparisons can be named, revisited, shared with notes, and exported later.

## Phase 49 Complete — Report Cloning

- Added clone controls for saved decision-rule snapshot comparison reports.
- Copied snapshots, preset keys, description, and notes into cloned reports.
- Reset decision status, decision summary, decision notes, decision owner, and recorded-decision metadata on clones.
- Added source-report tracking with a `cloned_from` relationship.
- Added clone page, list/detail links, admin visibility, migration, and tests.


## Phase 50: Report templates

Completed:
- Added reusable decision-rule snapshot comparison report templates.
- Added built-in starter templates for Monthly Growth Review, Lead Magnet Review, Instagram Experiment Review, and Learning Conversion Review.
- Added Studio template library, detail, create, edit, delete, and create-report-from-template workflows.
- Added template defaults for report title, description, notes, presets, focus areas, recommended snapshot count, and recommended snapshot window.
- Added navigation/help links and admin support.

Recommended next phase:
- Add report-template usage analytics so you can see which templates are creating the most saved reports and which template families lead to Keep, Roll back, Watch, or Archived decisions.

## Phase 51 Complete — Report-template usage analytics

- [x] Added source-template tracking to saved decision-rule snapshot comparison reports.
- [x] Added migration `0036_report_template_usage_tracking.py`.
- [x] Reports created from a template now retain a `source_template` relationship.
- [x] Cloned reports preserve the source-template attribution while still resetting decision fields.
- [x] Added Template Usage Analytics page for generated report counts and decision outcomes.
- [x] Added usage summaries by individual template and by template family.
- [x] Added filters for template type, active/inactive status, and report decision status.
- [x] Added CSV export for template usage analytics.
- [x] Added navigation, dashboard, detail/list links, admin support, and test coverage.

Next recommended phase:
- Add report-template conversion recommendations, so Studio can suggest which templates to use next based on recent experiments, underused report types, and prior Keep/Roll back/Watch decisions.

## Phase 52 Complete – Report Template Recommendations
- Added a recommendation page for saved decision-rule comparison report templates.
- Ranked templates using recent experiment snapshots, recommended snapshot windows, underused template families, prior Keep / Roll back / Watch outcomes, focus areas, and preset defaults.
- Added CSV export for recommended templates and reasoning.
- Added navigation links from the dashboard, base nav, help guide, template detail, and template usage pages.

## Recommended Phase 53
Add saved report-template recommendation feedback so suggestions can be marked useful, dismissed, or revisited later, then use that feedback to tune future recommendations.


## Completed — Phase 53

- [x] Add report-template recommendation feedback actions.
- [x] Track shown/ignored, useful, dismissed, and revisit-later signals.
- [x] Use feedback in future template recommendation ranking.
- [x] Add feedback history, CSV export, admin support, and documentation.

## Recommended Next Phase — Phase 54

- Add report-template recommendation tuning controls so template recommendation weights and feedback penalties can be adjusted without editing code.

## Phase 55 — Report-template recommendation tuning audit logging

Completed:
- Added audit logging for report-template recommendation tuning updates.
- Added history, CSV export, and rollback review/restore routes.
- Added before/after snapshots, field-level diffs, staff user, reason notes, and request path tracking.
- Added admin visibility and test coverage for manual updates, exports, and rollback restores.

Next recommended phase:
- Add experiment labels/outcomes for report-template recommendation tuning changes, so template-ranking weight changes can be evaluated like other recommendation experiments.

## Phase 57 Complete — Report-template recommendation tuning experiment snapshots

- Added before/after performance snapshots for report-template recommendation tuning experiments.
- Snapshot windows compare 7, 14, 30, or 60 days before and after a template-ranking tuning change.
- Snapshot metrics cover template usage, saved comparison report creation, report-level decisions, and report-template recommendation feedback.
- Added list/detail/create/export screens for template-recommendation tuning snapshots.
- Added CSV export for snapshot metric rows.
- Added admin visibility, navigation links, and test coverage.

Next recommended phase: decision recommendations for report-template recommendation tuning snapshots, so Studio can suggest whether to keep, roll back, or keep watching a template-ranking experiment based on usage and feedback deltas.

## Phase 58 Complete - Report-template recommendation tuning decisions

- [x] Added deterministic decision recommendations for report-template recommendation tuning snapshots.
- [x] Snapshot detail pages now recommend Keep changes, Rollback recommended, or Keep watching based on before/after template usage, saved reports, decision outcomes, and recommendation feedback.
- [x] Added weighted signal explanations so the decision is auditable instead of a black box.
- [x] Added one-click recording of the recommendation back onto the tuning experiment outcome.
- [x] Added decision recommendation rows to snapshot CSV exports.
- [x] Added tests for rendering and recording template-tuning snapshot decisions.

## Recommended Phase 59

Add editable decision thresholds for report-template recommendation tuning snapshots, so the Keep / Rollback / Watch logic can be adjusted from Studio instead of using fixed internal weights.

## Phase 60 Complete - Report-template recommendation decision-rule audit logging

- [x] Added change-log model for report-template recommendation decision rules.
- [x] Logged manual updates with before/after snapshots, diffs, staff user, reason note, and request path.
- [x] Added history, CSV export, and rollback review/restore screens.
- [x] Added admin support, navigation/help links, and test coverage.

## Recommended Phase 61

Add experiment labels and outcomes for report-template recommendation decision-rule changes, so Keep / Rollback / Watch threshold tests can be tracked and evaluated before staying in place.

## Phase 63 — Decision Recommendations for Report-Template Recommendation Decision-Rule Snapshots

- Added deterministic Keep / Rollback / Keep Watching recommendations for report-template recommendation decision-rule experiment snapshots.
- Snapshot detail pages now show confidence, score, weighted signals, positive/negative evidence, and recommended next steps.
- Added one-click recording of the recommendation back onto the decision-rule experiment outcome.
- Snapshot CSV exports now include the recommendation, confidence, score, summary, active rule profile, and weighted signal rows.
- Added `studio/services/report_template_recommendation_decision_rule_snapshot_decisions.py` and tests for rendering, recording, and export behavior.


## Phase 64 Completed - Project Health and Launch Readiness

- [x] Add private Project Health checklist.
- [x] Add CSV export for health checks.
- [x] Check learner-site readiness, lesson quality, challenge validation, resource lead magnets, CTAs, content planning, publishing metrics, newsletter operations, and recommendation-system configuration.
- [x] Add Studio navigation and Help documentation.
- [x] Add tests for health page and CSV export.

## Recommended Next Phase

- Add a pre-deployment smoke-test command that runs URL reversing checks, verifies expected templates exist, and reports missing environment variables before Render deployment.
