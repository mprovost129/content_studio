# Code with Michael Content Studio

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

Use the email entered during `createsuperuser`. The application does not use usernames or public registration.

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

## Quality checks

```bat
.\scripts\manage_local.cmd check
.\scripts\manage_local.cmd makemigrations --check --dry-run
.\.venv\Runtime\python.exe manage.py test studio users core --settings=config.Settings.test
.\.venv\Scripts\ruff.exe check config core users studio
```

OpenAI pricing is versioned in the database so historical cost estimates remain reproducible. Update pricing through Django admin when model pricing changes.
