# Code with Michael Content Studio

## Phase 36: Recommendation tuning experiment labels and outcomes

Phase 36 adds experiment tracking to recommendation tuning changes. Staff can now label a tuning update or preset application as a named experiment, record a hypothesis or success criteria, update the outcome later, and filter/export tuning history by experiment status and result.

New private Studio route:

- `/studio/recommendations/tuning/history/<id>/experiment/` — record or update the experiment label, status, outcome, and notes for a tuning change.

New model fields and migration:

- Added experiment fields to `RecommendationTuningChangeLog`.
- `studio/migrations/0026_recommendation_tuning_experiments.py`

Experiment workflow:

- Add an experiment label when saving manual tuning changes.
- Add an experiment label/hypothesis when applying a tuning preset.
- Review active and completed experiments from the tuning history page.
- Record outcomes such as Positive, Neutral, Negative, or Inconclusive.
- Mark the decision as Keep changes, Rollback recommended, Complete, or Inconclusive.
- Export experiment labels, statuses, outcomes, and notes with the tuning history CSV.


## Phase 35: Recommendation tuning rollback controls

Phase 35 adds safe rollback controls for recommendation tuning experiments. Staff can now open a prior tuning history record, compare the current active profile against the before-change and after-change snapshots, and restore either snapshot after review. Every restore creates a new audit entry, so rollback activity remains traceable.

New private Studio route:

- `/studio/recommendations/tuning/history/<id>/rollback/` — review and restore a saved tuning snapshot.

Rollback behavior:

- Restore **before-change snapshot** to undo an experiment.
- Restore **after-change snapshot** to re-apply a historical tuning configuration.
- Capture rollback reason notes, staff user, request path, before/after snapshots, and field-level diffs.
- Add restore shortcuts from the tuning history table.

No new database migration is required because rollback uses the existing `RecommendationTuningChangeLog` table and adds a new action choice in code.

## Phase 34: Recommendation tuning audit log

Phase 34 adds a staff-facing audit trail for recommendation tuning changes. Manual tuning edits and preset applications now capture before/after snapshots, field-level diffs, the staff user who made the change, the route used, and an optional reason note.

New private Studio routes:

- `/studio/recommendations/tuning/history/` — review tuning change history.
- `/studio/recommendations/tuning/history/export/` — export the audit log to CSV.

New model and migration:

- `RecommendationTuningChangeLog`
- `studio/migrations/0025_recommendation_tuning_change_log.py`

The tuning form now includes an optional reason field. Preset applications are logged automatically with the preset key and preset name. The history page helps compare recommendation experiments over time before making additional scoring changes.

## Phase 33: Tuning presets and recommendation simulation

Phase 33 adds a safer way to tune the resource CTA recommendation engine before changing live scoring weights. Studio now includes strategic presets and a side-by-side simulation screen that compares how those presets rank recommendations for a real learning resource.

New private Studio routes:

- `/studio/recommendations/tuning/` — edit the active recommendation weights and apply presets.
- `/studio/recommendations/tuning/simulation/` — compare active tuning against selected presets without saving.
- `/studio/recommendations/tuning/presets/apply/` — staff-only POST action that applies a preset to the active profile.

Built-in presets:

- **Lead Magnet Growth** — favors gated PDFs and newsletter signups.
- **Lesson Completion** — favors matching lesson CTAs and related lesson/category/topic signals.
- **Quiz Engagement** — favors quick quiz CTAs and lessons with active quizzes.
- **Challenge Practice** — favors coding challenge CTAs and lessons with active practice code.

Simulation is read-only. It builds temporary tuning profiles in memory and passes them into the existing deterministic recommendation service, so no weights are saved until a staff user explicitly applies a preset or edits the active tuning form.

## Phase 32: Recommendation tuning controls

This phase adds editable Studio controls for the automatic Resource CTA recommendation engine. Staff can now change the scoring weights for lesson CTAs, quiz CTAs, challenge CTAs, open PDFs, PDF lead magnets, newsletter CTAs, lesson matching, prior clicks/conversions, and feedback-based boosts/penalties without editing Python code.

Key route:

- `/studio/recommendations/tuning/` — private recommendation tuning controls

What the tuning profile controls:

- Base CTA bonuses for lesson, quiz, challenge, PDF, lead magnet, and newsletter suggestions.
- Match weights for related lessons, category, difficulty, keyword overlap, active quizzes/challenges, practice code, prior conversions, and prior CTA clicks.
- Feedback weights for accepted, dismissed, and ignored recommendations.
- Global floor/ceiling limits for feedback adjustments.

Only one tuning profile is active at a time. Saving an active profile automatically disables other active profiles, so recommendation scoring stays deterministic. Resource detail pages and the recommendation feedback report now link directly to the tuning screen.


## Phase 25: PDF lead magnet controls

This phase adds optional email-gated PDF downloads for public learning resources. A resource can now keep its branded generated PDF open, or require a learner to enter an email address before download. Gated downloads create or reactivate a newsletter subscriber, store the resource as the signup source, unlock the PDF in the learner session, and record resource lead-magnet access/download counts for later review.

Key routes:

- `/learn/resources/<slug>/unlock-pdf/` — public email unlock page for gated resource PDFs
- `/learn/resources/<slug>/download.pdf` — generated PDF download route; redirects to the unlock page when gated and not yet unlocked

New controls on learning resources:

- `pdf_requires_email`
- `pdf_lead_magnet_headline`
- `pdf_lead_magnet_description`

New tracking model:

- `ResourceLeadMagnetAccess`
A private Django workspace for turning one programming lesson into reviewed captions, branded social graphics, and website-ready exports for Facebook, Instagram, and Threads.

Nothing publishes automatically. Captions begin as drafts, graphics remain local downloads, and website exports remain private until you intentionally use them.

## First-time setup on this workstation

The project includes a repaired local Python runtime and a lightweight SQLite development database. You do not need Docker for normal local use.

1. Open Command Prompt or PowerShell in the project directory.
2. Apply database migrations:

   ```bat
   .\scripts\manage_local.cmd migrate
   ```

3. Create your private account:

   ```bat
   .\scripts\manage_local.cmd createsuperuser
   ```

   Enter an email and password. There is no username.

4. Start Content Studio:

   ```bat
   .\scripts\run_local.cmd
   ```

5. Leave that terminal open and visit <http://127.0.0.1:8000/accounts/login/>.
6. Sign in with the superuser email and password.

For future sessions, you normally need only:

```bat
.\scripts\run_local.cmd
```

The launcher applies pending migrations, verifies Pillow, and starts the local server.


## Current improvement roadmap

The main development backlog now lives in `TODO.md`. The highest-priority direction is to keep Content Studio as the private creator system and build the public Code with Michael learner website as a separate layer that consumes reviewed lessons and website exports.

The latest updates add weekly planning, publishing records, and a performance report so staff can track the real-world performance of Facebook, Instagram, Threads, website, email, or other posts. Each record can store the publish date, post URL, caption used, graphic used, impressions, reach, likes, comments, saves, shares, clicks, follower growth, and follower count after posting.

## Public learner experience

The public learner site now lives under `/learn/`. Key pages are:

- `/learn/` — learner home page.
- `/learn/lessons/` — searchable public lesson library.
- `/learn/playground/` — standalone browser Python playground.
- `/learn/dashboard/` — logged-in learner progress dashboard.
- `/learn/activity/` — learner history for lessons, quizzes, challenges, and badges.
- `/accounts/signup/` — learner account creation.
- `/accounts/profile/` — learner profile and preferences.

Learners can mark lessons complete, save quiz attempts, run coding challenge tests, save coding challenge attempts, and earn foundational badges. Staff users can still access `/studio/` after signing in.


## Generate lesson from idea

Staff users can open `/studio/lessons/generate/` or use **Generate** in the Studio navigation. Enter a beginner topic such as `Python variables`, `for loops`, `functions`, `lists`, or `calculating a total price`. The studio creates a draft lesson with:

- Beginner learning objective, takeaway, common mistake, practice prompt, hints, starter code, solution code, and expected output
- SEO title and description draft
- Explanation, code, expected output, and beginner-tip content blocks
- Optional structured multiple-choice quiz
- Optional code challenge and active test case

This is intentionally a draft generator, not an auto-publisher. Review all code, output, quiz answers, challenge tests, SEO copy, and publishing statuses before using a generated lesson publicly. Generic money examples use US dollar formatting, such as `$75`, to match the default project locale.



## Weekly content planner

Phase 12 adds a planning layer before publishing. Staff can use **Planner** or `/studio/planner/` to view a week-at-a-glance schedule, move between weeks, and see what is planned for Facebook, Instagram, Threads, the website, email, or another channel.

From a lesson detail page, use **Plan post** to choose:

- platform
- scheduled publish date and time
- planning status
- optional carousel template key
- optional caption draft
- optional generated graphic
- post goal
- internal notes

When a planned post goes live, use **Record post** from the planner or lesson detail page. The publishing form is prefilled from the plan when possible, and the plan is marked as posted after the publishing record is saved.

Website exports now use schema version `1.5` and include a `content_plans` section so external tools can understand planned distribution without treating it as a published post.

## Publishing records and content performance

From any private lesson detail page, use **Add publishing record** after you post a lesson, carousel, caption, or website page. A publishing record tracks:

- platform and publish date
- direct post or page URL
- connected caption draft and generated graphic
- final caption snapshot used at publish time
- impressions, reach, likes, comments, saves, shares, clicks
- follower growth and follower count after posting

Saving a Facebook, Instagram, Threads, or Website publishing record automatically moves that lesson's matching platform status to **Published**. The content calendar now shows recent publishing records and platform performance totals so you can compare which formats are actually growing Code with Michael.

## Performance reporting

Phase 13 adds **Reports** at `/studio/reports/performance/`. Use this report after entering publishing records to compare which content formats are producing the best results. The report supports date-range and platform filters and summarizes:

- content format ranking, including carousel formats such as Concept Explanation, Beginner Mistake, Spot the Bug, Code Output Quiz, and Three Things to Remember
- platform totals for Facebook, Instagram, Threads, Website, Email, and Other
- format-by-platform combinations so you can see where each post type works best
- top recorded posts by follower growth, engagement, clicks, and reach

The report derives a post's format from the connected content plan's `carousel_template` first, then from the attached graphic template, then from caption-only/manual entry metadata. This means the most accurate reporting comes from planning posts first, then recording the final post after publishing.

## Social carousel templates

From any private lesson detail page, use **Social Carousels** in the sidebar to append a carousel-ready post structure. These templates are intended for Facebook, Instagram, and Threads growth content. Available formats include:

- **Concept Explanation** — hook, plain-English idea, code example, output reveal, and takeaway.
- **Beginner Mistake** — common beginner error, why it happens, code to inspect, and fixing habit.
- **Spot the Bug** — debugging prompt designed for comments and predictions.
- **Code Output Quiz** — code-first quiz where followers predict the output before seeing the answer.
- **Three Things to Remember** — saveable quick-reference carousel.

When you apply a social carousel template, the studio appends normal lesson blocks using the lesson's existing title, summary, beginner takeaway, common mistake, code, and expected output where available. You can either review the blocks first or check **Generate PNG assets now** to immediately create graphics in the selected output sizes. Matching graphic templates are created automatically the first time each social carousel format is used.

A practical posting cadence is: Concept Explanation for teaching, Beginner Mistake for saves, Spot the Bug and Code Output Quiz for comments, and Three Things to Remember for quick reference posts.

## Reusable block templates

From any private lesson detail page, use **Block Templates** in the sidebar to append a common teaching pattern. Available templates include:

- **Beginner Concept** — explanation, small code example, output, common mistake, and practice block.
- **Code Example** — setup, finished code, output, and line-by-line breakdown.
- **Try It Yourself** — structured code challenge with starter code, hints, solution, expected output, and test case.
- **Common Mistake** — wrong code, error context, corrected code, and reminder.
- **Spot the Bug** — debugging prompt, broken code, error output, fixed code, and quiz.
- **Mini Project** — project goal, requirements, challenge, solution, and test case.

Templates append content to the end of the lesson. Review and edit the generated blocks, quizzes, challenges, and tests before publishing or exporting. Generic money examples use U.S. dollar formatting such as `$25` to match the default project locale.

## Recommended first practice lesson

Start small while learning the interface:

1. Create a lesson such as **Python Variables**.
2. Add one Explanation block.
3. Add one Code block.
4. Add one Output block.
5. Generate only an Instagram/Facebook square graphic.
6. Generate only an Instagram caption.
7. Edit and approve the caption.
8. Open the website preview.

This lets you learn the entire workflow without managing a large lesson or generating unnecessary AI requests.

## Daily lesson workflow

### 1. Create the lesson

Select **New lesson** from the dashboard.

Complete these fields first:

- **Title:** The learner-facing topic.
- **Summary:** One or two sentences describing the learning outcome.
- **Status:** Use Draft while building the lesson.
- **Difficulty:** Beginner, intermediate, advanced, or mixed.
- **Category:** The primary subject area.

Optional fields include tags, series information, accent color, call to action, SEO metadata, and private internal notes.

The lesson is the source of truth. Correct technical or editorial problems in the lesson before regenerating captions, graphics, or website exports.

### 2. Add content blocks

Open the lesson and select **Add block**. Add blocks in the order the learner should read them.

| Block | Use it for |
| --- | --- |
| Explanation | Normal instructional text |
| Code | Source code with preserved spacing |
| Output | The exact expected program result |
| Heading | A section divider in a longer lesson |
| Callout / tip | Warnings, shortcuts, or important reminders |
| List | Steps, rules, or related points |
| Quiz | A knowledge check with optional JSON choices and answers |
| Challenge | A task for the learner to complete |
| Comparison | Before/after or side-by-side concepts |
| Image | A reference for future image-supported content |

A reliable beginner lesson structure is:

1. Short explanation
2. Code example
3. Expected output
4. Explanation or tip
5. Optional challenge or quiz

Use the up and down arrows to reorder blocks. Editing a source block does not alter old exports; regenerate anything that should reflect the change.

### 3. Review the source lesson

Before generating assets, confirm:

- The code is valid and safe to share.
- The output exactly matches the code.
- The explanation uses consistent terminology.
- The difficulty is appropriate.
- No internal notes or private information appear in public content blocks.

### 4. Generate social graphics

In the lesson sidebar:

1. Choose a graphic template.
2. Select one or more output formats.
3. Select **Generate graphics**.
4. Review every generated slide.
5. Select **Download PNG** for the files you want.

Available formats include:

- Instagram/Facebook square: 1080×1080
- Instagram/Threads portrait: 1080×1350
- Instagram/Facebook Story: 1080×1920
- Facebook landscape: 1200×630

Large lessons can produce multiple carousel slides. Files are stored under `media/generated/` in addition to being available from the lesson page.

### 5. Generate caption drafts

In **Draft captions**:

1. Select Facebook, Instagram, Threads, or any combination.
2. Select **Generate caption drafts**.
3. Read each draft carefully.
4. Select **Edit or approve**.
5. Revise the copy and change the status to Approved when it is ready.

Generation never publishes the caption. You remain responsible for technical accuracy, tone, links, hashtags, and final platform formatting.

### 6. Review AI usage and cost

Every request records:

- Purpose and platform
- OpenAI model
- Input, cached input, output, and reasoning tokens
- Request duration
- Success or failure
- Estimated cost
- Original prompt and returned response

The dashboard displays the running estimated cost and recent AI activity. Failed requests remain recorded for diagnosis but do not show an estimated successful-generation charge.

### 7. Preview the website lesson

The **Page readiness** panel reports an SEO score and specific warnings. Before exporting, aim to include:

- A lesson summary
- At least one content block
- A dedicated SEO title
- A dedicated SEO description
- A category
- At least one tag

Select **Website preview** to inspect the private standalone lesson page. The preview includes metadata and Schema.org `TechArticle` structured data.

### 8. Create a website export

After reviewing the preview:

1. Select **Create website export**.
2. Download **HTML** for a standalone page.
3. Download **JSON** for future integration with the existing Code with Michael website.

Exports receive immutable revision numbers. If the source lesson changes, create a new revision. Exporting does not publish anything publicly.

The JSON integration contract is documented in `docs/website_export_schema.md`.

### Optional: enable the interactive Python playground

Edit a lesson and select **Enable playground** when its Code blocks should be runnable in the website preview.

The playground:

- Runs Python entirely in the visitor’s browser using a version-pinned Pyodide runtime
- Uses a web worker so normal execution does not freeze the page
- Provides Run, Stop, Reset, and Ctrl+Enter controls
- Stops code that runs for more than 12 seconds
- Never executes learner code on the Django server

Use it for Python fundamentals and supported browser packages. Do not enable it for examples that require local files, operating-system commands, desktop interfaces, private credentials, or server-only services. The first run downloads the browser Python runtime and therefore requires an internet connection.


### Optional: add challenge test cases

For stronger coding challenges, open a lesson, create or edit a code challenge, then select **Add test**. A test case contains Python code that is appended after the learner's submitted code in the browser playground.

Use test cases to check function return values:

```python
assert add_numbers(2, 3) == 5
assert add_numbers(-1, 10) == 9
print("passed")
```

Then set the expected output to:

```text
passed
```

A challenge with active test cases shows a **Run tests** button on the public lesson page. Logged-in learners can save the attempt, including submitted code, observed output, test results, and pass counts. The submitted code is still executed in the browser, not on the Django server.

### 9. Download and publish manually

The current release uses a download-first workflow:

1. Download the selected PNG files.
2. Copy the Approved platform caption.
3. Publish through Facebook, Instagram, or Threads.
4. Change the lesson status to Published when appropriate.

Direct Meta API scheduling and publishing will be added later.

## Lesson statuses

| Status | Meaning |
| --- | --- |
| Idea | A topic that has not been developed |
| Draft | Actively being written or generated |
| In review | Waiting for accuracy or presentation review |
| Ready | Approved for download, scheduling, or publication |
| Published | Released on at least one intended channel |
| Archived | Retained for history but no longer active |

## Finding content

The Lessons search field searches across:

- Titles and summaries
- SEO titles and descriptions
- Explanations and code blocks
- Categories and tags
- Series names
- Private internal notes

Use the status filter to narrow the library to Ideas, Drafts, review work, Ready lessons, Published lessons, or archived material.

## Branding

Open **Branding** from the main navigation to change:

- Brand name
- Social handle
- Default accent color
- Background color
- Default call to action
- Logo

Individual lessons can override the default accent color and call to action.

## In-app help

Select **Help** in the main navigation for the same workflow in a compact visual guide. The dashboard onboarding checklist tracks whether you have created content, generated graphics and captions, and completed a website export.

## OpenAI configuration

Store the API key only in `.env`:

```env
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-5.6-terra
OPENAI_REASONING_EFFORT=low
```

Never place the key in source code, `.env.example`, screenshots, chat messages, or Git. Use a separate production key when deploying to Render.

## Troubleshooting

### The server is not running

Run:

```bat
.\scripts\run_local.cmd
```

Leave the terminal window open while using the application.

### Pillow is reported as missing

The launcher now checks Pillow before Django starts. Verify it with the exact project runtime:

```bat
.\.venv\Runtime\python.exe -c "from PIL import Image; print(Image.__version__)"
```

Avoid using a bare `pip` command. To repair dependencies, use:

```bat
.\.venv\Runtime\python.exe -m pip install -r requirements.txt
```

### Caption generation fails

Confirm `OPENAI_API_KEY` is present in `.env`, restart the server, and inspect the failed run on the dashboard. Do not disable TLS certificate verification.

### I cannot sign in

Use the email entered during `createsuperuser` for staff access. Learners can register through `/accounts/signup/`, but only staff users can open private `/studio/` routes.

### I changed a lesson after generating assets

Existing captions, graphics, and website exports are historical outputs. Generate a new version when the source lesson changes.

### Password-reset email does not arrive locally

Local development uses console email by default. The reset link appears in the server terminal. Configure an SMTP provider for production delivery.

## Docker and PostgreSQL

Production remains designed for PostgreSQL. To run the full Docker stack:

1. Copy `.env.example` to `.env` and set its secret values.
2. Start Docker Desktop.
3. Run:

   ```bat
   docker compose up --build -d
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

4. Visit <http://localhost:8000/accounts/login/>.

For a non-Docker local PostgreSQL process, set `DB_HOST=localhost`. Set `USE_SQLITE=1` only for the lightweight single-user local environment.

When the final website URL is available, set `CONTENT_WEBSITE_BASE_URL` so exports include the correct canonical lesson URLs.


## Phase 15 CSV performance exports

Phase 15 adds spreadsheet-friendly exports for the private performance reporting workflow. The performance report at `/studio/reports/performance/` now includes CSV download buttons for:

- Posted content rows
- Content format summary
- Platform summary
- Format × platform matrix

Each export uses the same date range and platform filter currently applied to the report screen. This lets Code with Michael performance data move cleanly into Excel, Google Sheets, or a longer-term reporting workbook without re-entering metrics manually.

The posted-content CSV includes published date, lesson, platform, content format, format source, post URL, impressions, reach, likes, comments, saves, shares, clicks, engagement total, engagement rate, new followers, follower count after posting, caption snapshot, and notes.

No database migration is required for phase 15.

## Phase 14 public SEO infrastructure

Phase 14 adds the core SEO surface for the public learner website:

- `/sitemap.xml` lists the public learner homepage, lesson library, playground, active learning paths, and lessons marked Website Ready or Published.
- `/robots.txt` allows the public learner site and blocks `/studio/`, `/admin/`, and `/accounts/`.
- `/feed.xml` provides an RSS feed of the latest public Python lessons.
- Public learner pages now expose canonical URLs.
- Public learner pages now include Open Graph/Twitter summary metadata.
- The learner homepage, learning path pages, and lesson pages include JSON-LD structured data.

Set `CONTENT_WEBSITE_BASE_URL` in production so canonical links, sitemap URLs, RSS links, and structured data point at the real public domain. Without that value, local requests use the current request origin.

No database migration is required for phase 14.

## Quality checks

```bat
.\scripts\manage_local.cmd check
.\scripts\manage_local.cmd makemigrations --check --dry-run
.\.venv\Runtime\python.exe manage.py test studio users core --settings=config.Settings.test
.\.venv\Scripts\ruff.exe check config core users studio
```

OpenAI pricing is versioned in the database so historical cost estimates remain reproducible. Update pricing through Django admin when model pricing changes.

## Phase 3 update
This version adds structured learner practice. Lessons can now include reusable quiz questions, answer choices, and code challenges in addition to the original flexible content blocks. Public lesson pages display interactive quiz feedback in the browser and runnable code challenges when the lesson playground is enabled. Website exports now use schema version 1.1 and include the structured quiz/challenge payload.


### Optional: learner profiles and activity history

Logged-in learners can open **Profile** to set:

- Display name
- Skill level
- Private learning goal
- Weekly practice target
- Lesson reminder preference
- Product update preference

The dashboard estimates recent weekly practice activity from saved lesson, quiz, and challenge records. The activity page keeps a fuller learner-facing history so students can review what they completed, what quizzes they answered, which challenge attempts passed tests, and which badges they earned.

## Phase 7 learner review updates

Phase 7 adds the first learner-facing code review layer. Logged-in learners can now open a saved challenge attempt and review the submitted code, observed output, individual test results, challenge prompt, and reviewed solution when one exists.

New learner routes:

- `/learn/challenge-attempts/<id>/` - review one saved coding challenge attempt.
- `/learn/activity/` - now links each challenge submission to its detail page.
- `/learn/<lesson-slug>/` - now shows a “My code submissions for this lesson” section when the learner has saved attempts.

No new database migration is required for phase 7. It uses the phase 5/6 attempt, test result, and learner profile data already in the schema.



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


## Phase 17 - Newsletter campaign planning

The Studio now includes newsletter campaign planning at `/studio/newsletter/campaigns/`. Campaigns can be drafted from lessons, scheduled, marked as sent, connected to email-list content plans, and updated with basic performance metrics such as recipients, opens, clicks, unsubscribes, and bounces. The app still does not send email automatically; use this layer to plan copy and track performance after sending through your email platform.

## Phase 18: Email performance imports

Newsletter campaigns can now be updated from pasted metrics or CSV exports instead of typing performance values manually.

Routes added:

- `/studio/newsletter/metrics/import/` — import metrics into any campaign.
- `/studio/newsletter/campaigns/<id>/metrics/import/` — import metrics into one selected campaign.

Supported fields include common labels for recipients/delivered/sent, opens, clicks, unsubscribes, and bounces. The importer accepts both CSV rows and simple copied summaries such as:

```text
Recipients: 421
Opens: 212
Clicks: 38
Unsubscribes: 1
Bounces: 0
```

Each import keeps a history record with provider, filename, raw payload snapshot, normalized values, warnings, and the user who imported it. Applying an import updates the connected `NewsletterCampaign` metrics and can optionally mark the campaign as sent.


## Phase 19: Audience segmentation

The Studio now includes saved newsletter audience segments for repeatable campaign targeting. Segments are dynamic rule sets, not static subscriber lists, so the matched subscriber count updates as new learners sign up or update their profiles.

Routes added:

- `/studio/newsletter/segments/` — manage saved subscriber segments.
- `/studio/newsletter/segments/new/` — create a segment.
- `/studio/newsletter/segments/<id>/edit/` — edit segment rules.
- `/studio/newsletter/segments/<id>/export/` — export matching subscribers as CSV.
- `/studio/newsletter/segments/performance/` — compare sent campaign performance by saved segment or legacy quick segment.
- `/studio/newsletter/segments/performance/export/` — download the segment performance report as CSV.

Segment rules can filter by subscriber status, signup source, learner skill level, source lesson, subscribed date range, rolling recency window, and keyword. Newsletter campaigns now include an optional saved segment field. When a saved segment is selected and no manual estimate is entered, the campaign estimates recipients from the current segment match count.

Added migration: `studio/migrations/0015_subscriber_segments.py`.

## Phase 20: Email provider integration preparation

Phase 20 prepares the newsletter system for future email-platform API integrations without sending or syncing automatically yet. Subscribers, saved segments, and campaigns now have dedicated mapping fields for provider IDs and sync state.

Supported provider labels:

- Not connected
- Mailchimp
- Beehiiv
- ConvertKit
- Other

Supported sync statuses:

- Not connected
- Ready to sync
- Synced
- Needs review
- Error

The practical workflow is now:

1. Plan or create the subscriber, segment, or campaign in Studio.
2. Set the provider and external ID once the matching record exists in Mailchimp, Beehiiv, ConvertKit, or another platform.
3. Use sync status and provider notes to track whether the record is ready, synced, blocked, or needs manual review.
4. Export subscribers or segment members to CSV with provider mapping fields included.

New migration:

- `studio/migrations/0016_email_provider_sync_fields.py`

Website exports now use schema `1.6` and include optional provider metadata for newsletter campaigns.

## Phase 21: Provider sync readiness report

Phase 21 adds a private email-provider sync readiness report for future Mailchimp, Beehiiv, ConvertKit, or custom-provider integrations.

Open it at:

- `/studio/newsletter/provider-readiness/`

The report reviews three record types:

- Newsletter subscribers
- Saved subscriber segments
- Newsletter campaigns

It classifies each record as:

- Not connected
- Missing provider IDs
- Ready to sync
- Synced
- Needs review
- Error

The report can be filtered by record type, provider, sync status, and readiness issue. It also includes a CSV export at `/studio/newsletter/provider-readiness/export/` that can be used as a manual sync checklist.

No database migration is required for phase 21. It uses the provider mapping fields added in phase 20.

## Phase 22: Public resource library

Phase 22 adds a public-facing beginner resource library to support SEO, social traffic, and learners who need quick references instead of a full lesson.

Public routes:

- `/learn/resources/` — browsable and searchable resource library.
- `/learn/resources/<slug>/` — individual resource page.

Private Studio routes:

- `/studio/resources/` — manage resources.
- `/studio/resources/new/` — create a resource.
- `/studio/resources/<slug>/` — inspect a resource.
- `/studio/resources/<slug>/edit/` — edit a resource.
- `/studio/resources/<slug>/delete/` — delete a resource.

Resource types currently supported:

- Cheat sheet
- Common Python error
- Setup guide
- Practice reference
- Python vocabulary
- Downloadable reference

Each resource can include a public content body, beginner tip, optional downloadable file, optional external URL, related lessons, SEO title/description, and an estimated read time. Ready and Published resources appear publicly; Draft and Archived resources remain private.

New migration:

- `studio/migrations/0017_learning_resources.py`

The sitemap now includes public resources, and individual resource pages include `LearningResource` JSON-LD structured data.

## Phase 23: Generate Resource From Idea

Phase 23 adds a private Studio workflow for quickly drafting beginner resources from a short topic.

Open it at:

- `/studio/resources/generate/`

The generator can create draft resources for:

- Cheat sheets
- Common Python error guides
- Setup guides
- Practice references
- Python vocabulary
- Downloadable reference drafts

The workflow is deterministic and does not require an OpenAI API call. It creates a Draft resource with beginner-friendly body content, a code example, expected output, beginner tip, SEO title/description, estimated read time, and internal review notes. Generic price/money examples use U.S. dollar formatting consistently.

No database migration is required for phase 23.

## Phase 24: Downloadable branded PDFs for resources

Phase 24 adds on-demand PDF generation for beginner learning resources. Selected Ready or Published resources can now show a public branded PDF download generated from the resource body. This is useful for cheat sheets, practice references, setup guides, and printable Code with Michael handouts.

Public route:

- `/learn/resources/<slug>/download.pdf` — downloads a generated branded PDF when `PDF download enabled` is checked. Disabled resources redirect back to the public resource page.

Private Studio route:

- `/studio/resources/<slug>/pdf/` — previews/downloads the generated PDF for review before publishing.

New resource fields:

- `pdf_download_enabled` — controls whether the public generated PDF button appears.
- `pdf_footer_note` — optional short evergreen note shown near the end of generated PDFs.

The PDF generator is implemented in `studio/services/resource_pdfs.py` and supports lightweight markdown-style headings, paragraphs, bullet lists, fenced code blocks, beginner tips, resource metadata, related public lessons, and branded Code with Michael page footers.

New dependency:

- `reportlab>=4.2,<5`

New migration:

- `studio/migrations/0018_learning_resource_pdf_fields.py`

## Phase 26 - Resource Performance Reporting

This phase adds lightweight analytics for the public resource library and PDF lead magnets.

New tracking events:

- Public resource page view
- Email-gated PDF unlock
- Branded PDF download

New Studio screens:

- `/studio/reports/resources/` - resource performance report
- `/studio/reports/resources/export/` - CSV export endpoint

The resource report includes:

- resource views
- PDF unlocks
- PDF downloads
- subscriber conversions
- unlock rate
- download rate
- subscriber conversion rate
- resource type breakdown
- recent event log

CSV exports include:

- resource summary
- resource type summary
- raw event log

New migration:

- `studio/migrations/0020_resource_performance_events.py`

After updating, run:

```cmd
.\scripts\manage_local.cmd migrate
.\scripts\manage_local.cmd check
.\scripts\manage_local.cmd test studio
```

## Phase 27 - Resource-to-lesson conversion tracking

This phase connects the public resource library to learner outcomes. When a visitor views a resource, unlocks a gated PDF, or downloads a branded PDF, the app stores a lightweight last-touch attribution record in the session. If that visitor later views a lesson, creates an account, submits a quiz answer, submits a coding challenge, or completes a lesson, Studio records a `ResourceLessonConversionEvent` tying the action back to the originating resource.

New private report routes:

- `/studio/reports/resource-conversions/`
- `/studio/reports/resource-conversions/export/`

The report shows which cheat sheets, setup guides, common-error guides, and downloadable references are driving:

- lesson views
- account signups
- quiz attempts
- challenge attempts
- lesson completions

CSV exports are available for resource summaries, conversion action summaries, and raw conversion events. A new migration is included:

```bash
python manage.py migrate
```

Migration added:

- `studio/migrations/0021_resource_lesson_conversion_events.py`

Recommended workflow:

1. Publish or feature a resource.
2. Promote the resource on Facebook, Instagram, Threads, or email.
3. Let learners click from the resource into related lessons.
4. Review `/studio/reports/resource-conversions/` to see which resources are producing actual learning actions.


## Phase 28: Resource CTA Blocks

Resource pages now support editable call-to-action blocks that push learners toward the next best action after reading a cheat sheet or reference. Studio users can add CTAs such as **Start the matching lesson**, **Try quiz next**, **Practice with a challenge**, **Download resource PDF**, **Join the newsletter**, or **External link** from each resource detail page.

Public CTA clicks are tracked and stored as last-touch attribution so later lesson views, account signups, quiz attempts, challenge attempts, and lesson completions can be connected back to the specific resource CTA that drove the action. The new report at `/studio/reports/resource-ctas/` ranks CTA blocks by clicks, conversion rate, quiz/challenge activity, and lesson completions. CSV exports are available for CTA summaries, raw clicks, and CTA-attributed conversions.

## Phase 29: Automatic Resource CTA Recommendations

Studio resource detail pages now generate ranked CTA suggestions automatically. Recommendations use a deterministic scoring service at `studio/services/resource_recommendations.py` and consider:

- lessons already attached as related lessons
- matching category
- matching learner difficulty
- title/summary/objective topic overlap
- whether the lesson has an active quiz
- whether the lesson has an active coding challenge
- prior resource-attributed conversions
- prior CTA clicks from the same resource to the same lesson
- whether the resource has a branded PDF download available

The resource detail page shows a **Suggested CTA blocks** panel above the manually configured CTA list. Staff users can apply a recommendation with one click, which creates a normal editable `ResourceCTA` block. The created CTA can still be edited, reordered, disabled, or deleted just like any manually created CTA.

New route:

- `/studio/resources/<slug>/ctas/recommendations/apply/`

No database migration is required for this phase. Recommendations are generated dynamically from existing resource, lesson, CTA, and conversion data.

## Phase 30: CTA Recommendation Feedback Loop

Resource CTA recommendations now have a feedback layer. When staff open a resource detail page, Studio records which suggested CTAs were shown. Applying a suggestion marks it as accepted and links the feedback record to the CTA that was created. Staff can also dismiss suggestions that are not useful.

The resource detail page now includes:

- Suggested CTA blocks with accepted, dismissed, and ignored-state labels.
- A **Dismiss** action for recommendations that should not be used.
- A recommendation feedback history panel.
- A link to the full recommendation feedback report.

New report route:

- `/studio/reports/resource-cta-recommendations/`

The report shows shown/ignored, accepted, and dismissed recommendations with filters for status and CTA type. This creates the foundation for future ranking improvements based on which recommendation patterns are actually useful.

New migration:

- `studio/migrations/0023_resource_cta_recommendation_feedback.py`

## Phase 31: Feedback-aware CTA recommendation ranking

Phase 31 makes the automatic resource CTA suggestions learn from Studio feedback. Recommendations are still deterministic and review-first, but their final ranking now includes a feedback adjustment on top of the normal base score.

The ranking now considers:

- Exact accepted suggestions as a strong positive signal.
- Exact dismissed suggestions as a strong negative signal.
- Repeatedly shown suggestions with no action as ignored signals.
- Accepted CTA types on similar resources as a positive pattern.
- Dismissed or ignored CTA types on similar resources as a negative pattern.
- Same-lesson CTA feedback from other resources as a lighter ranking signal.

On each Studio resource detail page, suggested CTA blocks now show their base score, feedback adjustment, final score, and ranking notes. The CTA recommendation feedback report also explains that accepted/dismissed/ignored feedback is now used to influence future recommendations.

No database migration is required for phase 31. It uses the feedback model added in phase 30.


## Phase 37 — Experiment Performance Snapshots

- Added before/after performance snapshots for recommendation tuning experiments.
- Added snapshot generation from tuning change history with 7, 14, 30, or 60 day windows.
- Added metrics across social publishing, resource-library events, newsletter campaigns, resource CTA clicks, and resource-to-lesson conversions.
- Added snapshot detail pages, snapshot list page, CSV export, admin support, and navigation links.
- Snapshots are read-only records, so experiments can be reviewed later even after additional performance data changes.

## Phase 38: Experiment Decision Recommendations

Phase 38 adds a decision layer on top of tuning experiment snapshots. After creating a before/after snapshot, Studio now recommends whether to **keep**, **roll back**, or mark the experiment **inconclusive**.

The recommendation reviews changes in:

- social follower growth, reach, engagement, and clicks
- resource PDF unlocks, downloads, and subscribers
- newsletter clicks, open rate, unsubscribes, and bounces
- resource CTA clicks
- learner conversions, including lesson views, quiz attempts, challenge attempts, and completions

Each snapshot detail page now includes the decision recommendation, confidence level, decision score, positive signals, negative signals, and recommended next steps. Staff can record the recommendation directly onto the tuning experiment outcome or manually record a different outcome.

No database migration is required for this phase. The decision result uses the existing experiment status, outcome, and notes fields added in earlier phases.

## Phase 39 - Editable experiment decision thresholds and weights

Phase 39 adds Studio controls for the recommendation experiment decision engine. The keep / rollback / inconclusive recommendation no longer depends only on hard-coded thresholds. Staff can now edit an active **Experiment Decision Tuning** profile at `/studio/recommendations/tuning/decision-rules/`.

The decision-rules screen controls:

- keep recommendation score threshold
- required primary positive-signal count
- high-confidence keep score
- rollback recommendation score threshold
- required primary negative-signal count
- high-confidence rollback score
- low-confidence inconclusive boundary
- per-metric score cap
- social, resource, newsletter, CTA, and learner-conversion metric weights
- unsubscribe and bounce penalty weights

Snapshot detail pages now show the active decision-rules profile, the rule thresholds used for that recommendation, and the top weighted metric contributions behind the decision score. This makes the recommendation explainable and tunable without editing Python code.
