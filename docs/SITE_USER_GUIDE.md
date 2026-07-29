# Code with Michael Content Studio — Complete Site Usage Guide

Last updated for: Phase 64 project package

This guide explains how to use the Code with Michael Content Studio and public learning site correctly. It is written for the site owner, staff users, and future assistants who need to understand the workflow without reading the code.

The project has two major areas:

1. **Public learner site** — the beginner-facing Python learning experience under `/learn/`.
2. **Private Studio** — the staff-only content, publishing, newsletter, reporting, recommendation, and health dashboard under `/studio/`.

Use the public learner site to teach beginners. Use the private Studio to create lessons, resources, social content, newsletters, reports, and growth experiments.

---

## 1. First-Time Setup and Daily Login

### 1.1 Run the local app

Use this when you are testing the project locally.

1. Open a terminal in the project folder.
2. Run database migrations:

```bash
.\scripts\manage_local.cmd migrate
```

3. Run Django checks:

```bash
.\scripts\manage_local.cmd check
```

4. Run tests:

```bash
.\scripts\manage_local.cmd test studio
```

5. Start the local server:

```bash
.\scripts\run_local.cmd
```

6. Open the local site in your browser.

Required:
- Run migrations after downloading a new phase zip.
- Use a staff account to access `/studio/`.

Optional:
- Run tests before every deployment.
- Create a separate test learner account to preview the public learning experience.

### 1.2 Login roles

The site uses two practical user types.

**Learner account**
- Used by students/beginners.
- Can view lessons, run code, complete quizzes, submit challenges, track progress, edit profile, and view activity.

**Staff account**
- Used by you or trusted admins.
- Can access `/studio/` and manage lessons, resources, reports, subscribers, campaigns, recommendations, and tuning controls.

Required:
- Staff users must have staff permissions enabled in Django admin.

Optional:
- Learners can browse public content without logging in, but progress tracking requires an account.

---

## 2. Recommended Overall Workflow

Use this workflow to keep the site organized.

1. Create or generate a lesson idea in Studio.
2. Add lesson blocks, starter code, solution code, quiz questions, and challenges.
3. Add challenge test cases when the challenge has a function or expected output.
4. Preview the lesson publicly.
5. Apply a social carousel template to create social content from the lesson.
6. Plan posts in the weekly planner.
7. Publish manually on Facebook, Instagram, Threads, or the website.
8. Record the actual published post and metrics in Studio.
9. Create or generate supporting resources such as cheat sheets.
10. Add resource CTAs and enable PDF lead magnets where appropriate.
11. Collect newsletter subscribers.
12. Draft newsletter campaigns from strong lessons/resources.
13. Review performance reports.
14. Use Project Health to find gaps before launch.

Required:
- Every public lesson should have beginner learning fields, at least one useful content block, and a clear next action.
- Every coding challenge should have a solution.
- Every published social post should eventually receive a publishing record.

Optional:
- Use recommendation/tuning experiments only after the basic content workflow is stable.

---

## 3. Public Learner Site

Base area: `/learn/`

The public learner site is what beginners see. It contains the lesson library, learning paths, resources, playground, learner dashboard, profile, and activity history.

### 3.1 Learner homepage

Path: `/learn/`

What it does:
- Introduces Code with Michael.
- Shows featured lessons, resources, and beginner learning paths.
- Provides newsletter signup.
- Sends learners to lessons, resources, or the playground.

How to use it:
1. Visit `/learn/` as a public visitor.
2. Click a featured lesson or resource.
3. Use the newsletter signup if you want to test subscriber capture.
4. Confirm the homepage communicates that the site is for beginner Python developers.

Required for a strong homepage:
- At least a few published lessons.
- At least one featured or useful resource.
- Clear beginner-friendly positioning.

Optional:
- Featured resources.
- Newsletter signup.
- Learning path links.

### 3.2 Lesson library

Path: `/learn/lessons/`

What it does:
- Lists public lessons.
- Lets beginners browse topics and choose what to learn.

How to use it:
1. Open `/learn/lessons/`.
2. Select a lesson title.
3. Review whether the listing has enough detail for a beginner to understand what the lesson covers.

Required for a lesson to be useful:
- Published or website-ready status.
- Title.
- Summary.
- Difficulty.
- Category or topic.

Optional:
- Tags.
- Series/path connection.
- SEO title and SEO description.

### 3.3 Lesson detail page

Path pattern: `/learn/<lesson-slug>/`

What it does:
- Teaches one beginner Python concept.
- Shows explanations, code examples, expected output, tips, quizzes, challenges, hints, and solution reveals.
- Allows logged-in learners to save quiz/challenge attempts and completion progress.

How a learner should use it:
1. Read the lesson title and summary.
2. Review the learning objective.
3. Read the explanation blocks.
4. Study the code example.
5. Run starter code in the browser playground area when available.
6. Compare observed output with expected output.
7. Answer the quiz.
8. Try the coding challenge.
9. Reveal hints only after attempting the challenge.
10. Reveal the solution after trying the challenge.
11. Mark the lesson complete if logged in.
12. Continue to the next lesson or recommended resource.

Required lesson content:
- Title — required.
- Slug — required.
- Summary — required.
- Difficulty — required.
- Status — required.
- Learning objective — required for beginner quality.
- Beginner takeaway — required for beginner quality.
- At least one explanation or code block — required for public quality.

Optional lesson content:
- Common mistake — optional but strongly recommended.
- Practice prompt — optional but strongly recommended.
- Starter code — optional unless the lesson has an interactive challenge.
- Solution code — optional for simple explanation lessons, required for challenges.
- Expected output — optional for concept lessons, required when checking printed output.
- Hints — optional but useful for beginners.
- Next lesson — optional but recommended for learning paths.

### 3.4 Learning paths / series

Path pattern: `/learn/paths/<series-slug>/`

What it does:
- Groups lessons into an ordered beginner pathway.
- Helps beginners avoid random browsing.

How to use it:
1. Open a learning path.
2. Start with the first lesson.
3. Complete lessons in order.
4. Use the next lesson links to keep moving.

Required:
- Series/path title.
- Ordered lessons.

Optional:
- Path summary.
- Estimated time.
- Prerequisites.

Recommended beginner paths:
- Python Starter Path.
- Variables and Data Types.
- Strings and Numbers.
- Lists and Loops.
- Functions.
- Mini Projects.
- Debugging for Beginners.

### 3.5 Public Python playground

Path: `/learn/playground/`

What it does:
- Lets beginners run Python code in the browser.
- Supports small practice examples without needing a local Python install.

How to use it:
1. Open `/learn/playground/`.
2. Type or paste Python code.
3. Click the run button.
4. Review the output.
5. Fix any errors and run again.

Required:
- Code entered in the editor.

Optional:
- Expected output comparison.
- Starting from a lesson’s starter code.

Best practices:
- Keep examples short.
- Avoid advanced package dependencies.
- Use beginner-readable print statements.
- Explain errors in plain English when writing lessons.

### 3.6 Learner signup

Path: `/accounts/signup/`

What it does:
- Creates a learner account.
- Allows progress, quiz attempts, challenge submissions, badges, and activity history to be saved.

How to use it:
1. Open `/accounts/signup/`.
2. Enter account details.
3. Submit the form.
4. After login, visit `/learn/dashboard/`.

Required:
- Username or account identifier.
- Password.

Optional:
- Email, depending on your auth settings.
- Profile details after signup.

### 3.7 Learner dashboard

Path: `/learn/dashboard/`

What it does:
- Shows a learner’s recent progress.
- Displays completed lessons, quiz attempts, challenge attempts, badges, and weekly practice goal information.

How to use it:
1. Login as a learner.
2. Open `/learn/dashboard/`.
3. Review recent learning activity.
4. Click any recent challenge attempt to review submitted code and test results.
5. Continue to the next unfinished lesson.

Required:
- Learner must be logged in.

Optional:
- Learner profile details.
- Weekly practice target.

### 3.8 Learner profile

Path: `/accounts/profile/`

What it does:
- Lets learners add a display name, skill level, learning goal, weekly practice goal, and communication preferences.

How to use it:
1. Login as a learner.
2. Open `/accounts/profile/`.
3. Fill out profile information.
4. Save changes.

Required:
- Logged-in account.

Optional fields:
- Display name.
- Skill level.
- Learning goal.
- Weekly practice goal minutes.
- Lesson reminder preference.
- Product update preference.

### 3.9 Learner activity

Path: `/learn/activity/`

What it does:
- Shows a learner’s history of lesson completions, quiz attempts, challenge submissions, and badges.

How to use it:
1. Login as a learner.
2. Open `/learn/activity/`.
3. Review previous work.
4. Open challenge attempts to inspect code and test results.

Required:
- Logged-in account.

Optional:
- None.

### 3.10 Challenge attempt review

Path pattern: `/learn/challenge-attempts/<id>/`

What it does:
- Shows a saved coding challenge submission.
- Displays submitted code, output, tests passed, tests failed, and solution context.

How to use it:
1. Submit a challenge from a lesson.
2. Open the saved attempt detail link.
3. Review what passed and failed.
4. Compare submitted code with the solution.
5. Try again from the original lesson.

Required:
- Logged-in learner.
- Saved challenge attempt.

Optional:
- Test cases, depending on the challenge.

---

## 4. Private Studio Overview

Base area: `/studio/`

The Studio is the private operating system for Code with Michael. It manages learning content, social posting, resources, newsletters, reporting, recommendations, experiments, and launch readiness.

### 4.1 Studio dashboard

Path: `/studio/`

What it does:
- Shows a summary of lessons, subscribers, planned posts, recent publishing activity, reports, campaign metrics, and health links.

How to use it:
1. Login as a staff user.
2. Open `/studio/`.
3. Review the dashboard cards.
4. Use the shortcuts to create lessons, generate resources, plan content, view reports, or check health.

Required:
- Staff login.

Optional:
- Use dashboard metrics as a daily review checklist.

### 4.2 Studio Help

Path: `/studio/help/`

What it does:
- Provides in-app guidance and links for Studio features.

How to use it:
1. Open `/studio/help/`.
2. Use it as a quick reference for feature groups.
3. Use this master guide for the full step-by-step process.

Required:
- Staff login.

Optional:
- Keep this page open while working through a content batch.

### 4.3 Project Health / Launch Readiness

Path: `/studio/project-health/`

What it does:
- Checks whether the project is ready for public use and content operations.
- Surfaces gaps like missing lesson blocks, missing challenge tests, missing publishing metrics, missing resource CTAs, and open experiments.

How to use it:
1. Open `/studio/project-health/`.
2. Review checks marked Needs action first.
3. Review Watch items second.
4. Export CSV if you want a checklist.
5. Fix the most important gaps before adding more features.

Required:
- Staff login.

Optional:
- CSV export.

Recommended use:
- Run this weekly.
- Run this before launch.
- Run this before major content pushes.

---

## 5. Lessons in Studio

### 5.1 Lesson list

Path: `/studio/lessons/`

What it does:
- Shows all lessons and their current content status.

How to use it:
1. Open the lesson list.
2. Filter or scan by status, category, difficulty, or platform readiness.
3. Click a lesson to edit details and content.

Required:
- Staff login.

Optional:
- Use filters when the lesson library becomes large.

### 5.2 Create a lesson manually

Typical path: `/studio/lessons/new/`

What it does:
- Creates a structured lesson record that can later become a public lesson, social carousel, newsletter topic, and website export.

How to use it:
1. Click New Lesson or equivalent create action.
2. Enter required core fields.
3. Add beginner learning fields.
4. Save the lesson.
5. Add lesson blocks, quizzes, challenges, and test cases from the lesson detail page.

Required fields:
- Title — required.
- Slug — required if not auto-generated.
- Status — required.
- Difficulty — required.
- Summary — required for public quality.

Recommended fields:
- Category — recommended.
- Tags — recommended.
- Series/path — recommended for ordered learning.
- Learning objective — recommended for every lesson.
- Beginner takeaway — recommended for every lesson.
- Common mistake — recommended for beginner clarity.
- Practice prompt — recommended for active learning.

Optional fields:
- Internal notes.
- SEO title.
- SEO description.
- Starter code.
- Solution code.
- Expected output.
- Hints.
- Next lesson.
- Platform-specific statuses.

### 5.3 Generate Lesson From Idea

Path: `/studio/lessons/generate/`

What it does:
- Creates a draft beginner lesson from a topic without requiring an AI API call.
- Adds structured fields, starter content blocks, optional quiz, and optional challenge scaffolding.

How to use it:
1. Open Generate Lesson From Idea.
2. Enter the lesson idea/topic.
3. Choose the audience.
4. Select category and series if known.
5. Choose whether to include a quiz.
6. Choose whether to include a challenge.
7. Submit the form.
8. Review the generated draft.
9. Edit all content before publishing.

Required selections:
- Lesson idea/topic — required.
- Audience — required or defaulted.

Optional selections:
- Learning objective — optional; use when you already know the exact objective.
- Category — optional but recommended.
- Series/path — optional but recommended for structured learning.
- Include quiz — optional.
- Include challenge — optional.

Important:
- Generated lessons are drafts. Always review code accuracy and beginner clarity.

### 5.4 Lesson detail page in Studio

Path pattern: `/studio/lessons/<slug>/`

What it does:
- Central command page for a lesson.
- Manage blocks, quizzes, challenges, test cases, carousel templates, publishing records, planned posts, newsletter campaigns, and export readiness.

How to use it:
1. Open a lesson.
2. Review beginner-readiness diagnostics.
3. Add missing learning fields.
4. Add or edit lesson blocks.
5. Add structured quiz questions.
6. Add coding challenges.
7. Add challenge test cases.
8. Apply block templates when needed.
9. Apply social carousel templates when ready to create posts.
10. Plan posts or record published posts.
11. Preview the public lesson.

Required:
- A saved lesson.

Optional:
- Quizzes.
- Challenges.
- Social carousel templates.
- Publishing records.
- Newsletter campaign.

### 5.5 Lesson blocks

What they do:
- Break a lesson into reusable sections such as explanation, code, output, quiz-like prompts, challenge prompts, comparisons, callouts, and images.

How to add a block:
1. Open a lesson detail page.
2. Click Add Block.
3. Choose the block type.
4. Enter the block title.
5. Enter content.
6. Add structured JSON only when the block type needs it.
7. Save.

Required fields:
- Lesson — required.
- Block type — required.
- Sort order — required or defaulted.
- Content — required for meaningful display.

Optional fields:
- Block title.
- Structured data JSON.
- Image or asset, depending on the block type.

Block type guidance:
- Explanation — use for beginner-friendly teaching text.
- Code — use for Python examples.
- Output — use for expected output.
- Quiz — use for simple block-based prompts; structured quizzes are better for real tracking.
- Challenge — use for challenge instructions; structured CodeChallenge is better for real tracking.
- Comparison — use for before/after or good/bad code.
- Callout — use for tips, mistakes, warnings, or reminders.
- Image — use when a visual helps explain the concept.

### 5.6 Block templates

What they do:
- Quickly append common lesson structures.

Available templates:
- Beginner Concept.
- Code Example.
- Try It Yourself.
- Common Mistake.
- Spot the Bug.
- Mini Project.

How to use them:
1. Open a lesson detail page.
2. Find the Block Templates panel.
3. Choose a template.
4. Apply it.
5. Edit the inserted blocks, quizzes, challenges, and tests.

Required:
- Existing lesson.
- Template selection.

Optional:
- Edit generated content after applying.

Recommended use:
- Use Beginner Concept for most new lessons.
- Use Spot the Bug for engagement posts.
- Use Mini Project for milestone lessons.

### 5.7 Duplicate lesson

What it does:
- Copies a lesson structure, including blocks, quizzes, challenges, and challenge tests.

How to use it:
1. Open the lesson you want to copy.
2. Click Duplicate Lesson.
3. Rename the new lesson.
4. Update slug, summary, learning fields, code, quizzes, and challenges.
5. Save and review.

Required:
- Source lesson.

Optional:
- Use when creating lessons in a repeated format.

Warning:
- Always update copied solution code and test cases so they match the new lesson.

---

## 6. Quizzes, Challenges, and Test Cases

### 6.1 Structured quizzes

What they do:
- Create trackable quiz questions with answer choices and saved attempts.

How to create a quiz:
1. Open a lesson detail page.
2. Click Add Quiz Question.
3. Enter the question prompt.
4. Choose question type.
5. Add choices.
6. Mark the correct choice.
7. Add explanation feedback.
8. Save.

Required fields:
- Lesson — required.
- Question prompt — required.
- Question type — required.
- At least one answer choice — required.
- Correct answer choice — required for automatic grading.

Optional fields:
- Explanation.
- Sort order.
- Active/inactive status.

Best practices:
- Keep each question focused on one concept.
- Always explain why the answer is correct.
- Use beginner language.

### 6.2 Coding challenges

What they do:
- Let learners submit code and receive feedback.
- Save attempts for logged-in learners.

How to create a challenge:
1. Open a lesson detail page.
2. Click Add Challenge.
3. Enter the challenge prompt.
4. Add starter code.
5. Add solution code.
6. Select validation mode.
7. Add expected output when output checking is used.
8. Add hints.
9. Save.

Required fields:
- Lesson — required.
- Challenge title or prompt — required.
- Starter code — required for beginner usability.
- Solution code — required for review/solution reveal.
- Validation mode — required.

Optional fields:
- Expected output — required only for output matching.
- Hints.
- Test cases.
- Manual review instructions.

Validation modes:
- Exact output match — use when printed output must match exactly.
- Contains output match — use when output can include extra text.
- Manual review — use when automatic validation is not reliable.
- Test cases — use when checking functions or assertions.

### 6.3 Challenge test cases

What they do:
- Run assertion-style checks against learner-submitted code.
- Help validate function-based challenges more accurately than output comparison.

How to create test cases:
1. Open a lesson detail page.
2. Find the coding challenge.
3. Click Add Test.
4. Enter the test code.
5. Add expected output if the test prints confirmation.
6. Mark the test active.
7. Save.

Required fields:
- Challenge — required.
- Test code — required.

Optional fields:
- Expected output.
- Sort order.
- Active/inactive status.

Example:

```python
assert add_numbers(2, 3) == 5
assert add_numbers(-1, 10) == 9
print("passed")
```

Expected output:

```text
passed
```

Best practices:
- Keep tests simple.
- Test the function name used in starter code.
- Include positive and edge-case examples.
- Avoid destructive or long-running code.

---

## 7. Social Content and Publishing Workflow

### 7.1 Social carousel templates

What they do:
- Turn a lesson into social post/carousel structures for growth content.

Available templates:
- Concept Explanation.
- Beginner Mistake.
- Spot the Bug.
- Code Output Quiz.
- Three Things to Remember.

How to use them:
1. Open a lesson detail page.
2. Find the Social Carousels panel.
3. Choose a carousel template.
4. Choose whether to generate PNG assets now.
5. Apply the template.
6. Review/edit the created content blocks and assets.

Required selections:
- Lesson — required.
- Carousel template — required.

Optional selections:
- Generate PNG assets now — optional.

Recommended usage:
- Concept Explanation for teaching.
- Beginner Mistake for saves/shares.
- Spot the Bug for comments.
- Code Output Quiz for engagement.
- Three Things to Remember for quick reminders.

### 7.2 Graphic templates and generated assets

What they do:
- Define reusable visual formats and create social graphics.

How to use them:
1. Apply a social carousel template or create/select a graphic template.
2. Generate assets.
3. Review the PNGs before posting.
4. Use the generated asset in a publishing record or planned post.

Required:
- Lesson or content source.
- Template selection.

Optional:
- Regenerate assets if layout or wording needs improvement.

Best practices:
- Keep text short on each card.
- Use one concept per graphic.
- Maintain Code with Michael branding.

### 7.3 Caption drafts

What they do:
- Store caption options for social platforms.

How to use them:
1. Create or generate a caption draft from a lesson.
2. Select platform or purpose.
3. Edit the caption for the specific platform.
4. Use the final caption when posting.
5. Connect the caption draft to the publishing record.

Required:
- Caption text.
- Purpose/platform.

Optional:
- Hashtags.
- Notes.
- Connected lesson.

### 7.4 Weekly content planner

Path: `/studio/planner/`

What it does:
- Creates a planned posting schedule.
- Tracks platform, scheduled date, content goal, caption draft, graphic, and status.

How to use it:
1. Open `/studio/planner/`.
2. Choose the week.
3. Click New Planned Post or Plan Post from a lesson.
4. Select platform.
5. Select scheduled date/time.
6. Select planning status.
7. Attach lesson, caption draft, graphic, and carousel template if available.
8. Save.
9. After publishing, click Record Post from the plan.

Required fields:
- Platform — required.
- Scheduled date/time — required.
- Planning status — required.

Optional fields:
- Lesson.
- Carousel template key.
- Caption draft.
- Generated graphic.
- Post goal.
- Internal notes.

Planning statuses:
- Planned — idea is scheduled.
- Drafting — content is being prepared.
- Ready — content is ready to post.
- Posted — content has been published.
- Skipped — content was not used.

### 7.5 Content calendar

Path: `/studio/calendar/`

What it does:
- Shows lesson workflow status, platform backlog, planned posts, and recent publishing records.

How to use it:
1. Open `/studio/calendar/`.
2. Review planned/upcoming posts.
3. Check platform statuses for lessons.
4. Find gaps where a lesson is ready for one platform but not another.
5. Use it to decide what to work on next.

Required:
- Staff login.

Optional:
- Use with weekly planner for campaign planning.

### 7.6 Publishing records

What they do:
- Record what was actually published and how it performed.

How to create a publishing record:
1. Open a lesson detail page or a planned post.
2. Click Record Post.
3. Select platform.
4. Enter publish date/time.
5. Paste the post URL.
6. Attach caption draft and graphic asset if available.
7. Paste the final caption snapshot.
8. Enter metrics after the post has had time to perform.
9. Save.

Required fields:
- Lesson or content connection — recommended/required for useful reporting.
- Platform — required.
- Publish date/time — required.

Optional fields:
- Post URL — optional at first, strongly recommended after publishing.
- Caption draft.
- Graphic asset.
- Final caption snapshot.
- Notes.
- Impressions.
- Reach.
- Likes.
- Comments.
- Saves.
- Shares.
- Clicks.
- New followers.
- Follower count after posting.

Important:
- Saving a publishing record can update the lesson’s matching platform status to Published.
- Add metrics later if you do not have them immediately.

---

## 8. Performance Reports

### 8.1 Social performance report

Path: `/studio/reports/performance/`

What it does:
- Compares post performance by platform and content format.

How to use it:
1. Open the report.
2. Choose start date and end date.
3. Select platform or all platforms.
4. Review format rankings.
5. Review top posts.
6. Export CSV for Excel/Google Sheets if needed.

Required filters:
- None; defaults can be used.

Optional filters:
- Start date.
- End date.
- Platform.

Metrics explained:
- Reach — how many people saw it.
- Engagements — likes, comments, saves, shares, and similar actions.
- Engagement rate — engagement relative to reach.
- Clicks — link clicks or tracked click metric.
- New followers — follower growth attributed to the post.

### 8.2 Performance CSV export

Path: `/studio/reports/performance/export/`

What it does:
- Downloads performance report data.

Available exports:
- Posted content rows.
- Content format summary.
- Platform summary.
- Format by platform matrix.

Required:
- Staff login.

Optional:
- Same filters as the report page.

---

## 9. Learning Resources

### 9.1 Public resource library

Path: `/learn/resources/`

What it does:
- Shows public cheat sheets, common-error guides, setup guides, practice references, vocabulary resources, and downloadable references.

How learners use it:
1. Open `/learn/resources/`.
2. Choose a resource.
3. Read the guide.
4. Download the PDF if available.
5. Click resource CTAs to continue to lessons, quizzes, challenges, or newsletter signup.

Required for public quality:
- Published resource.
- Title.
- Summary.
- Resource type.
- Content body.

Optional:
- PDF download.
- Email gate.
- Related lessons.
- CTAs.

### 9.2 Resource detail page

Path pattern: `/learn/resources/<slug>/`

What it does:
- Displays the full resource content, beginner tip, related lessons, PDF download, and CTA cards.

How to use it:
1. Open the resource.
2. Read the summary and content.
3. Use the beginner tip.
4. Download the PDF if available.
5. Follow the recommended CTA.

Optional public actions:
- Download branded PDF.
- Unlock PDF download with email.
- Start matching lesson.
- Try quiz next.
- Practice with a challenge.
- Join newsletter.

### 9.3 Manage resources in Studio

Path: `/studio/resources/`

What it does:
- Lists and manages learning resources.

How to use it:
1. Open `/studio/resources/`.
2. Create a new resource or open an existing one.
3. Edit content, PDF settings, lead magnet settings, related lessons, and CTAs.
4. Preview the public resource.

Required fields:
- Title — required.
- Slug — required.
- Resource type — required.
- Status — required.
- Difficulty — required.
- Summary — required for quality.
- Content body — required for public usefulness.

Optional fields:
- Category.
- Tags.
- Related lessons.
- Featured flag.
- Beginner tip.
- Downloadable file.
- External URL.
- Estimated read time.
- SEO title.
- SEO description.
- Internal notes.

### 9.4 Generate Resource From Idea

Path: `/studio/resources/generate/`

What it does:
- Creates draft resources from a topic, such as cheat sheets, error guides, setup guides, practice references, and vocabulary resources.

How to use it:
1. Open Generate Resource From Idea.
2. Enter the resource topic.
3. Choose resource type.
4. Choose audience.
5. Select category if known.
6. Select related lessons if relevant.
7. Choose featured status if needed.
8. Generate the resource.
9. Review and edit before publishing.

Required selections:
- Resource topic — required.
- Resource type — required.
- Audience — required or defaulted.

Optional selections:
- Category.
- Related lessons.
- Featured status.

### 9.5 Branded resource PDFs

Public path pattern: `/learn/resources/<slug>/download.pdf`

Studio preview path pattern: `/studio/resources/<slug>/pdf/`

What it does:
- Generates a Code with Michael branded PDF from a resource.

How to use it:
1. Open a resource in Studio.
2. Enable PDF download.
3. Add a PDF footer note if desired.
4. Preview the PDF in Studio.
5. Open the public resource and test the download button.

Required:
- PDF download enabled — required for the public PDF button.
- Resource title and content — required for a useful PDF.

Optional:
- PDF footer note.
- Email gate.
- Lead magnet headline.
- Lead magnet description.

### 9.6 PDF lead magnets

What they do:
- Require an email signup before a selected PDF can be downloaded.
- Track resource download subscribers.

How to use them:
1. Open a resource in Studio.
2. Enable PDF download.
3. Enable Requires Email.
4. Add a lead magnet headline.
5. Add a lead magnet description.
6. Save.
7. Test the public unlock flow.

Required for gated PDFs:
- PDF download enabled — required.
- PDF requires email — required for gating.
- Lead magnet headline — recommended.
- Lead magnet description — recommended.

Optional:
- Custom footer note.

### 9.7 Resource CTA blocks

What they do:
- Add action cards to resource pages, such as Start matching lesson, Try quiz next, Practice with a challenge, Download PDF, Join newsletter, or External link.

How to create a CTA:
1. Open a resource detail page in Studio.
2. Click Add CTA.
3. Choose CTA type.
4. Enter CTA title and description.
5. Select target lesson/challenge/resource or enter external URL.
6. Save.
7. Test the public CTA click.

Required fields:
- Resource — required.
- CTA type — required.
- CTA title — required.
- Target — required depending on CTA type.

Optional fields:
- Description.
- Button label.
- Sort order.
- Active/inactive status.

CTA target requirements:
- Start matching lesson — target lesson required.
- Try quiz next — target lesson with quiz recommended.
- Practice with a challenge — target lesson/challenge recommended.
- Download resource PDF — resource PDF must be enabled.
- Join newsletter — no external target required.
- External link — external URL required.

### 9.8 Resource CTA recommendations

What they do:
- Suggest CTA blocks based on related lessons, category, difficulty, quizzes, challenges, PDF availability, prior clicks, conversions, and feedback.

How to use them:
1. Open a resource detail page in Studio.
2. Review Suggested CTA Blocks.
3. Read the score and ranking notes.
4. Click Add CTA for useful suggestions.
5. Dismiss suggestions that are not useful.
6. Revisit reports later to see which CTAs converted.

Required:
- Existing resource.

Optional:
- Related lessons improve suggestion quality.
- Feedback improves future ranking.

---

## 10. Resource Reports and Conversion Tracking

### 10.1 Resource performance report

Path: `/studio/reports/resources/`

What it does:
- Tracks resource page views, PDF unlocks, PDF downloads, subscribers, and conversion rates.

How to use it:
1. Open the report.
2. Choose date range.
3. Filter by event type or resource type if needed.
4. Review top resources.
5. Export CSV if needed.

Required:
- Resource pages must receive traffic to generate data.

Optional filters:
- Start date.
- End date.
- Event type.
- Resource type.

### 10.2 Resource conversion report

Path: `/studio/reports/resource-conversions/`

What it does:
- Shows whether resource visits/downloads lead to lesson views, signups, quiz attempts, challenge attempts, and lesson completions.

How to use it:
1. Open the conversion report.
2. Select a date range.
3. Filter by conversion type or resource type if needed.
4. Review which resources drive deeper learning actions.
5. Export CSV if needed.

Required:
- Resource attribution must be present through page views, unlocks, downloads, or CTA clicks.

Optional:
- Use this report to prioritize which resources deserve more promotion.

### 10.3 Resource CTA performance report

Path: `/studio/reports/resource-ctas/`

What it does:
- Shows CTA clicks and CTA-attributed conversions.

How to use it:
1. Open the report.
2. Review click totals by CTA.
3. Review conversion totals by CTA.
4. Export summary, clicks, or conversions to CSV.
5. Improve or remove weak CTAs.

Required:
- Public CTA clicks.

Optional:
- Use feedback reports to improve suggestions.

### 10.4 Resource CTA recommendation feedback report

Path: `/studio/reports/resource-cta-recommendations/`

What it does:
- Tracks accepted, dismissed, ignored, and shown CTA recommendations.

How to use it:
1. Open the report.
2. Filter by status or CTA type.
3. Look for patterns in accepted/dismissed suggestions.
4. Tune recommendation weights if the system is over-suggesting weak CTAs.

Required:
- Recommendation views or actions.

Optional:
- Use it before changing recommendation tuning.

---

## 11. Newsletter and Email Capture

### 11.1 Public newsletter signup

Path: `/learn/newsletter/signup/`

What it does:
- Captures emails from learners.
- Tracks source such as homepage, lesson page, resource download, or Studio import.

How learners use it:
1. Enter email.
2. Enter first name if desired.
3. Submit.
4. Subscriber record is created or updated.

Required:
- Email — required.

Optional:
- First name.
- Source lesson/resource is tracked automatically when available.

### 11.2 Subscriber management

Path: `/studio/subscribers/`

What it does:
- Lets staff manage newsletter subscribers.

How to use it:
1. Open Subscribers.
2. Search or filter records.
3. Edit subscriber details when needed.
4. Export CSV for provider import.

Required fields:
- Email — required.
- Status — required.
- Source — required or defaulted.

Optional fields:
- First name.
- Source lesson.
- Source resource.
- Source URL.
- Consent text.
- Notes.
- Provider mapping fields.

Subscriber statuses:
- Active — can receive email.
- Unsubscribed — should not receive email.
- Bounced — email failed.
- Complained — should not receive marketing.

### 11.3 Subscriber segments

Path: `/studio/newsletter/segments/`

What they do:
- Create saved groups of subscribers using rules.

How to create a segment:
1. Open Segments.
2. Click New Segment.
3. Name the segment.
4. Choose matching rules.
5. Save.
6. Export matching subscribers if needed.

Required fields:
- Segment name — required.
- Status filter or rules — optional but needed for meaningful targeting.

Optional rules:
- Subscriber status.
- Signup source.
- Learner skill level.
- Source lesson.
- Subscribed date range.
- Rolling recency window.
- Keyword search.
- Provider mapping.

### 11.4 Segment performance

Path: `/studio/newsletter/segments/performance/`

What it does:
- Shows performance by saved segment.

How to use it:
1. Open segment performance.
2. Review which segments are being targeted.
3. Compare campaign performance by segment.
4. Export CSV if needed.

Required:
- Saved segments.
- Campaign records connected to segments.

Optional:
- Use this before changing targeting strategy.

### 11.5 Newsletter campaigns

Path: `/studio/newsletter/campaigns/`

What they do:
- Plan and track email campaigns connected to lessons, resources, or content plans.

How to create a campaign manually:
1. Open Newsletter Campaigns.
2. Click New Campaign.
3. Connect a lesson if relevant.
4. Enter title, subject, preview text, and body.
5. Add CTA label and CTA URL.
6. Choose status.
7. Choose target segment.
8. Schedule the campaign.
9. Save.
10. After sending, mark it sent and enter metrics.

Required fields:
- Title — required.
- Subject — required.
- Status — required.
- Target segment — required or defaulted.

Optional fields:
- Connected lesson.
- Preview text.
- Email body.
- CTA label.
- CTA URL.
- Scheduled date/time.
- Sent date/time.
- Estimated recipients.
- Actual recipients.
- Opens.
- Clicks.
- Unsubscribes.
- Bounces.
- Notes.
- Provider mapping fields.

### 11.6 Draft newsletter from lesson

Path pattern: `/studio/lessons/<slug>/newsletter/new/`

What it does:
- Creates an email campaign draft based on a lesson.

How to use it:
1. Open a lesson detail page.
2. Click Draft Newsletter or equivalent action.
3. Review the generated subject, preview, body, and CTA.
4. Choose target segment.
5. Schedule or save as draft.

Required:
- Source lesson.
- Campaign title/subject.

Optional:
- Target segment.
- Scheduled date/time.
- Notes.

### 11.7 Import email performance metrics

Paths:
- `/studio/newsletter/metrics/import/`
- `/studio/newsletter/campaigns/<id>/metrics/import/`

What it does:
- Lets you paste or upload provider metrics from Mailchimp, Beehiiv, ConvertKit, or manual reports.

How to use it:
1. Open campaign-specific Import Metrics when possible.
2. Select provider.
3. Paste summary text or CSV-style data.
4. Preview normalized values.
5. Apply metrics.
6. Optionally mark the campaign as sent.

Required:
- Campaign — required for campaign-specific import.
- Provider label — required or defaulted.
- Metric payload — required.

Optional:
- Source filename.
- Mark as sent.

Supported metric names:
- Recipients.
- Opens.
- Clicks.
- Unsubscribes.
- Bounces.

### 11.8 Provider sync readiness

Path: `/studio/newsletter/provider-readiness/`

What it does:
- Shows which subscribers, segments, and campaigns have enough provider IDs and sync fields to connect with email platforms later.

How to use it:
1. Open Provider Sync Readiness.
2. Filter by record type, provider, sync status, or readiness issue.
3. Review missing IDs.
4. Export CSV as a checklist.
5. Fill missing provider fields as needed.

Required:
- Provider fields only matter if you are integrating with an email platform.

Optional fields:
- External contact ID.
- External campaign ID.
- External segment ID.
- External audience/list/publication ID.
- Provider dashboard URL.
- Provider sync status.
- Provider notes.

---

## 12. Website Exports and SEO

### 12.1 Website preview/export

What it does:
- Exports lesson and related data for use on a separate public site or static build.

How to use it:
1. Open a lesson in Studio.
2. Review the website preview/export section.
3. Confirm learning fields, blocks, quizzes, challenges, publishing records, plans, and campaigns are correct.
4. Export JSON or website data as supported by the project.

Required:
- Lesson must exist.

Optional:
- Quizzes.
- Challenges.
- Publishing records.
- Content plans.
- Newsletter campaigns.

### 12.2 SEO infrastructure

Public routes:
- `/sitemap.xml`
- `/robots.txt`
- `/feed.xml`

What it does:
- Helps search engines find public lessons and resources.
- Provides an RSS feed for latest public lessons.
- Adds structured metadata to public pages.

How to use it:
1. Open each route locally to confirm it loads.
2. Confirm public lessons/resources appear in the sitemap.
3. Confirm page titles and descriptions are meaningful.
4. Use SEO title/description fields on lessons/resources when default text is not enough.

Required:
- Public content must be published to appear usefully.

Optional:
- Custom SEO titles.
- Custom SEO descriptions.

---

## 13. Recommendation Systems and Tuning

The project includes several recommendation engines. These are powerful but should be used after the basic content workflow is stable.

### 13.1 Resource CTA recommendation tuning

Path: `/studio/recommendations/tuning/`

What it does:
- Controls how strongly the system recommends lesson, quiz, challenge, PDF, and newsletter CTAs for resources.

How to use it:
1. Open Recommendation Tuning.
2. Review the active tuning profile.
3. Adjust weights only when recommendations are consistently poor.
4. Add a reason note.
5. Optionally label the change as an experiment.
6. Save.

Required:
- Profile name — required.
- Active status — required.
- Weight values — required/defaulted.

Optional:
- Reason note.
- Experiment label.
- Experiment status.
- Experiment notes.

Best practice:
- Change one group of weights at a time.
- Use simulation before saving major changes.

### 13.2 Recommendation tuning presets

Path: `/studio/recommendations/tuning/simulation/`

What it does:
- Compares preset scoring profiles without saving changes.

Presets:
- Lead Magnet Growth.
- Lesson Completion.
- Quiz Engagement.
- Challenge Practice.

How to use it:
1. Open simulation.
2. Select resources or review available comparisons.
3. Compare current tuning to presets.
4. Apply a preset only if it supports your current goal.

Required:
- Existing resources and recommendation candidates.

Optional:
- Apply preset after review.

### 13.3 Recommendation tuning history and rollback

Paths:
- `/studio/recommendations/tuning/history/`
- `/studio/recommendations/tuning/history/<id>/rollback/`

What it does:
- Tracks tuning changes and lets you restore before/after snapshots.

How to use it:
1. Open tuning history.
2. Review changes by date, staff user, action, or experiment.
3. Open rollback for a prior change.
4. Compare current values with before/after snapshots.
5. Restore only when needed.
6. Add a rollback reason.

Required:
- Existing change log.

Optional:
- CSV export.
- Experiment outcome recording.

### 13.4 Experiment snapshots and decisions

What they do:
- Compare before/after performance around tuning experiments.
- Recommend Keep, Rollback, or Inconclusive/Watch depending on the experiment type.

How to use them:
1. Open the relevant tuning history page.
2. Find an experiment change.
3. Create a snapshot.
4. Choose comparison window: 7, 14, 30, or 60 days.
5. Review before/after metrics.
6. Review the decision recommendation.
7. Record the outcome back to the experiment.

Required:
- Experiment-labeled change.
- Enough before/after data to evaluate.

Optional:
- CSV export.
- Decision-rule tuning.

---

## 14. Decision Rules, Report Templates, and Advanced Reports

This part of the Studio evaluates experiments and creates saved comparison reports. Use it after you have real publishing, resource, newsletter, and conversion data.

### 14.1 Experiment decision rules

Path: `/studio/recommendations/tuning/decision-rules/`

What they do:
- Control Keep / Rollback / Inconclusive decision recommendations for recommendation tuning experiment snapshots.

How to use them:
1. Open Decision Rules.
2. Review thresholds and metric weights.
3. Adjust only when the default decision guidance is too aggressive or too conservative.
4. Add reason and experiment fields if testing.
5. Save.

Required:
- Thresholds and weights — required/defaulted.

Optional:
- Reason note.
- Experiment label.
- Preset application.

### 14.2 Decision-rule presets and simulation

Path: `/studio/recommendations/tuning/decision-rules/simulation/`

Presets:
- Aggressive Growth.
- Conservative Quality.
- Balanced Learning.
- Lead Magnet Focus.

How to use it:
1. Choose an existing experiment snapshot.
2. Compare preset outcomes against the current rules.
3. Review decision scores and top signals.
4. Apply a preset only when the preset matches your strategy.

Required:
- Existing experiment snapshot.

Optional:
- Apply preset.
- Record experiment label/hypothesis.

### 14.3 Decision-rule history, rollback, outcomes, and snapshots

Common paths:
- `/studio/recommendations/tuning/decision-rules/history/`
- `/studio/recommendations/tuning/decision-rules/history/<id>/rollback/`
- `/studio/recommendations/tuning/decision-rules/history/<id>/experiment/`
- `/studio/recommendations/tuning/decision-rules/history/<id>/snapshot/`

What they do:
- Track changes to decision rules.
- Allow rollback.
- Record experiment outcomes.
- Create before/after snapshots.

How to use them:
1. Open decision-rule history.
2. Find the change you want to evaluate.
3. Record or update experiment label/outcome if needed.
4. Create a snapshot after enough time has passed.
5. Review recommendation and metrics.
6. Roll back if the experiment underperformed.

Required:
- History entry.

Optional:
- CSV export.
- Snapshot creation.
- Outcome recording.

### 14.4 Decision-rule snapshot comparison

Path: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/compare/`

What it does:
- Compares multiple decision-rule snapshots side by side.

How to use it:
1. Open the comparison page.
2. Select snapshots.
3. Select preset profiles if desired.
4. Review summary deltas, metric comparison, and recommendation matrix.
5. Export CSV if needed.
6. Save as a report if the comparison is useful.

Required:
- At least one snapshot.

Optional:
- Multiple snapshots.
- Preset profiles.
- CSV export.
- Save report.

### 14.5 Saved comparison reports

Path: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/reports/`

What they do:
- Save useful snapshot comparisons so they can be revisited, annotated, printed, and used as decision records.

How to create a report:
1. Open saved reports.
2. Click New Report or Save Report from a live comparison.
3. Enter report title.
4. Add description.
5. Select snapshots.
6. Select decision-rule presets.
7. Add staff notes.
8. Save.

Required fields:
- Report title — required.
- Selected snapshots — required for useful report.

Optional fields:
- Description.
- Selected presets.
- Staff notes.
- Decision status.
- Decision summary.
- Decision notes.
- Decision owner.

### 14.6 Report decision status

What it does:
- Turns a saved report into an actual decision record.

Available statuses:
- No decision yet.
- Keep.
- Roll back.
- Watch.
- Archived.

How to use it:
1. Open a saved report.
2. Review charts and recommendation matrix.
3. Edit the report.
4. Choose decision status.
5. Add decision summary.
6. Add decision notes.
7. Add decision owner.
8. Save.

Required:
- Decision status — required/defaulted.

Optional:
- Decision summary.
- Decision notes.
- Decision owner.

### 14.7 Printable saved reports

Path pattern: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/reports/<id>/print/`

What it does:
- Opens a clean report layout suitable for browser printing or saving as PDF.

How to use it:
1. Open a saved report.
2. Click Printable Report.
3. Review the print layout.
4. Click Print / Save as PDF.
5. Save the browser-generated PDF.

Required:
- Saved report.

Optional:
- Report decision status and notes improve the printed output.

### 14.8 Report cloning

What it does:
- Copies an existing saved report for a new month, campaign, or experiment family.

How to use it:
1. Open saved reports.
2. Click Clone on a report.
3. Review what will be copied.
4. Create clone.
5. Edit title, snapshots, notes, and decision fields.

Required:
- Source report.

Optional:
- Use cloned reports for recurring monthly reviews.

Important:
- Decision fields reset on clone.
- Source template attribution is preserved when applicable.

### 14.9 Report templates

Path: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/`

What they do:
- Provide reusable report structures.

Built-in starter templates:
- Monthly Growth Review.
- Lead Magnet Review.
- Instagram Experiment Review.
- Learning Conversion Review.

How to use them:
1. Open Report Templates.
2. Choose a template.
3. Review recommended snapshot count, window, focus areas, and default presets.
4. Create a saved report from the template.
5. Adjust selected snapshots and notes.
6. Save.

Required template fields:
- Template name/title — required.
- Template type — required.
- Default report title — required.
- Active status — required/defaulted.

Optional template fields:
- Default description.
- Default notes.
- Default presets.
- Recommended snapshot count.
- Recommended window days.
- Focus areas.

### 14.10 Report-template usage analytics

Path: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/usage/`

What it does:
- Shows which templates are used and what decisions their reports lead to.

How to use it:
1. Open Template Usage.
2. Filter by template type, active status, or report decision.
3. Review reports created per template.
4. Review Keep/Rollback/Watch/Archived counts.
5. Export CSV if needed.

Required:
- Reports created from templates.

Optional:
- Use before editing or deleting templates.

### 14.11 Report-template recommendations

Path: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/`

What it does:
- Suggests which saved report template to use next based on recent snapshots, underused template types, prior decisions, focus areas, presets, and feedback.

How to use it:
1. Open Template Recommendations.
2. Review ranked template suggestions.
3. Read the score breakdown and reasons.
4. Mark useful, dismiss, or revisit later.
5. Create a report from a useful template.

Required:
- Active report templates.

Optional:
- Recommendation feedback.
- CSV export.

### 14.12 Report-template recommendation tuning

Path: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/`

What it does:
- Controls how report-template suggestions are ranked.

How to use it:
1. Open Template Tuning.
2. Review scoring weights.
3. Adjust only after reviewing recommendation feedback.
4. Add reason note.
5. Add experiment label if testing.
6. Save.

Required:
- Active tuning profile.
- Weight values.

Optional:
- Reason note.
- Experiment label/status/notes.

### 14.13 Template tuning history, rollback, experiments, and snapshots

Common paths:
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/history/`
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/history/<id>/rollback/`
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/history/<id>/experiment/`
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/history/<id>/snapshot/`

What they do:
- Track changes to report-template recommendation tuning.
- Allow rollback.
- Record experiment outcomes.
- Compare before/after template usage and feedback.

How to use them:
1. Open Template Tuning History.
2. Review changes and experiments.
3. Create a snapshot after an experiment has run.
4. Review Keep/Rollback/Watch recommendation.
5. Record the outcome.
6. Roll back if needed.

Required:
- Existing tuning history entry.

Optional:
- CSV export.
- Snapshot creation.
- Outcome recording.

### 14.14 Template recommendation decision rules

Path: `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/decision-rules/`

What they do:
- Control Keep/Rollback/Watch decisions for report-template recommendation tuning snapshots.

How to use them:
1. Open Template Decision Rules.
2. Review thresholds and weights.
3. Adjust only when recommendations are too aggressive or too conservative.
4. Save with a reason and experiment label if needed.

Required:
- Threshold values.
- Weight values.

Optional:
- Reason note.
- Experiment label/status/notes.

### 14.15 Template decision-rule history and snapshots

Common paths:
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/decision-rules/history/`
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/decision-rules/history/<id>/rollback/`
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/decision-rules/history/<id>/experiment/`
- `/studio/recommendations/tuning/decision-rules/experiments/snapshots/report-templates/recommendations/tuning/decision-rules/history/<id>/snapshot/`

What they do:
- Track, evaluate, and roll back changes to the rules used to decide template recommendation experiments.

How to use them:
1. Open Template Decision Rules History.
2. Review changes.
3. Record experiment labels/outcomes as needed.
4. Create snapshots after a test period.
5. Review Keep/Rollback/Watch recommendation.
6. Restore a prior snapshot if needed.

Required:
- History entry.

Optional:
- CSV export.
- Experiment outcome.
- Snapshot.

---

## 15. Admin Area

Path: `/admin/`

What it does:
- Provides raw database management for staff/superusers.

Use it for:
- Creating staff users.
- Reviewing records that do not need custom Studio screens.
- Inspecting models and relationships.
- Emergency edits.

Required:
- Superuser or staff permissions.

Optional:
- Use Studio screens whenever available; they are safer and workflow-focused.

Warning:
- Direct admin edits can bypass the intended workflow. Use carefully.

---

## 16. Recommended Weekly Operating Routine

Use this routine once the site is live.

### Monday: Plan
1. Open Project Health.
2. Fix Needs action items related to public content.
3. Open Weekly Planner.
4. Schedule posts for the week.
5. Choose one lesson/resource to promote.

### Tuesday–Thursday: Create and publish
1. Generate or polish lessons/resources.
2. Apply carousel templates.
3. Publish manually to Facebook/Instagram/Threads.
4. Record publishing records.
5. Add metrics when available.

### Friday: Review
1. Open Social Performance Report.
2. Open Resource Performance Report.
3. Open Resource CTA Report.
4. Check subscriber growth.
5. Decide which topics performed best.

### Weekend or monthly: Improve
1. Review saved reports.
2. Create snapshots for experiments that have enough data.
3. Record outcomes.
4. Adjust tuning only when there is evidence.
5. Clone or create report templates for the next review.

---

## 17. Required vs Optional Content Checklist

### Every public lesson should have
Required:
- Title.
- Slug.
- Summary.
- Difficulty.
- Status appropriate for public display.
- Learning objective.
- Beginner takeaway.
- At least one explanation/code block.

Optional but recommended:
- Common mistake.
- Practice prompt.
- Quiz.
- Challenge.
- Challenge test case.
- Next lesson.
- SEO title/description.
- Social carousel.

### Every coding challenge should have
Required:
- Prompt.
- Starter code.
- Solution code.
- Validation mode.

Optional but recommended:
- Expected output.
- Hints.
- Test cases.

### Every resource should have
Required:
- Title.
- Slug.
- Resource type.
- Status.
- Summary.
- Content body.

Optional but recommended:
- Beginner tip.
- Related lessons.
- PDF download.
- Resource CTA.
- SEO fields.

### Every lead magnet should have
Required:
- PDF enabled.
- Email gate enabled.
- Subscriber capture flow.

Optional but recommended:
- Lead magnet headline.
- Lead magnet description.
- Matching lesson CTA.

### Every published social post should have
Required:
- Platform.
- Publish date/time.
- Connected lesson/content.

Optional but recommended:
- Post URL.
- Final caption snapshot.
- Graphic asset.
- Impressions.
- Reach.
- Engagement metrics.
- New followers.

### Every newsletter campaign should have
Required:
- Title.
- Subject.
- Status.
- Target segment.

Optional but recommended:
- Lesson/resource connection.
- Preview text.
- CTA URL.
- Scheduled date/time.
- Sent date/time.
- Metrics import.

---

## 18. Stabilization Notes

At phase 64, the project has many advanced analytics and recommendation features. The best next practical work is stabilization, not more feature layers.

Recommended stabilization steps:
1. Run migrations locally.
2. Run Django checks.
3. Run tests.
4. Click through the public learner flow.
5. Click through the core Studio workflow: lesson → resource → plan post → record post → report.
6. Fix any template, URL, or migration issues.
7. Simplify navigation if it feels too deeply nested.
8. Seed the database with a small starter curriculum.
9. Launch with a small number of strong beginner lessons.

Recommended launch minimum:
- 10 beginner lessons.
- 3 learning paths.
- 5 resources.
- 2 downloadable PDFs.
- 1 lead magnet.
- 1 weekly newsletter draft.
- Working playground.
- Working signup and dashboard.
- Clean Project Health page with no major Needs action items.

---

## 19. Glossary

**Lesson** — A structured teaching page for one Python concept.

**Lesson block** — A reusable piece of lesson content, such as explanation, code, output, callout, or image.

**Quiz question** — A structured, trackable learner question.

**Code challenge** — A learner coding task with starter code, solution, and optional tests.

**Challenge test case** — Code used to verify a learner’s challenge submission.

**Resource** — A cheat sheet, guide, error reference, setup guide, vocabulary page, or downloadable reference.

**Lead magnet** — A gated resource PDF that collects an email before download.

**CTA** — Call to action, such as Start lesson, Try quiz, Practice challenge, Download PDF, or Join newsletter.

**Publishing record** — A record of a real post published to a platform and its performance metrics.

**Content plan** — A scheduled planned post before it is published.

**Subscriber segment** — A saved group of newsletter subscribers based on matching rules.

**Recommendation tuning** — Weight settings that control what the Studio recommends.

**Decision rules** — Thresholds and weights that determine whether an experiment should be kept, rolled back, or watched.

**Snapshot** — A before/after comparison around a tuning or decision-rule experiment.

**Saved comparison report** — A reusable report created from one or more snapshots.

**Report template** — A reusable structure for creating saved comparison reports.

**Project Health** — The launch-readiness checklist dashboard.
