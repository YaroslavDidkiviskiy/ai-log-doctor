# AI Log Doctor

> Early prototype. Core idea is defined, implementation is incomplete.

AI-powered log incident analyzer built with FastAPI. Upload logs, group recurring errors, and get structured incident summaries with likely causes and debugging steps.

## What it does

Upload a `.log` or `.txt` file → the system parses events, extracts errors and warnings, normalizes messages, groups them by fingerprint into incidents, and generates structured analysis with probable causes and next debugging steps.

This is **not** a chat over logs. It's an incident analysis tool.

```
upload → parse → filter → normalize → fingerprint → group → summarize
```

## Features

- Upload `.log` / `.txt` files via drag-and-drop or API
- Parse plain timestamps, bracketed timestamps, Python tracebacks
- Filter only significant events (ERROR, WARNING, exceptions, timeouts, connection failures)
- Normalize dynamic values (UUIDs, IPs, emails, numbers, tokens)
- Fingerprint and group similar events into incidents
- Aggregate stats: count, first seen, last seen, severity
- AI summary per incident (OpenAI) with fallback rule-based summarizer
- Dark-themed dashboard UI with HTMX live updates

## Tech stack

- **Python 3.12** / **FastAPI**
- **SQLAlchemy 2.0** / SQLite
- **Jinja2** + **HTMX** (server-rendered UI)
- **Pydantic v2** for validation
- **OpenAI API** (optional) for incident summaries
- **BackgroundTasks** for async processing

## Architecture

```
app/
├── models/         SQLAlchemy models (Upload, LogEvent, Incident)
├── schemas/        Pydantic response schemas
├── routers/        API + web routes
├── services/       Core logic (parser, normalizer, fingerprint, grouper, summarizer)
├── tasks/          Background processing pipeline
├── templates/      Jinja2 templates
└── static/         CSS
```

### Processing pipeline

1. **Upload** — file saved to `uploads/`, DB record created
2. **Parse** — line-by-line parser extracts timestamp, level, service, message, traceback
3. **Filter** — keep only errors, warnings, exceptions, timeouts, failures
4. **Normalize** — replace UUIDs, IPs, emails, numbers, tokens with placeholders
5. **Fingerprint** — SHA-256 hash of normalized message
6. **Group** — events with same fingerprint → one incident
7. **Aggregate** — count, first/last seen, sample message, sample traceback
8. **Summarize** — AI or rule-based summary with causes and next steps

## Setup

```bash
git clone <repo-url>
cd ai-log-doctor

python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# optionally set OPENAI_API_KEY in .env

uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest tests/ -v
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./ai_log_doctor.db` | Database connection string |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded files |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max upload size in MB |
| `OPENAI_API_KEY` | — | OpenAI key (leave blank for fallback summarizer) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for AI summaries |

## Sample logs

Three sample log files are included in `sample_logs/`:

- `django_error.log` — Django app with DB connection failures, tracebacks, auth errors
- `fastapi_traceback.log` — FastAPI app with database locks, email failures, timeouts
- `mixed_app.log` — Scheduler with billing errors, push notification failures, pool exhaustion

## Roadmap

- [ ] Secret redaction in displayed logs
- [ ] Filters and search on uploads/incidents pages
- [ ] Compare incidents across uploads
- [ ] PostgreSQL support
- [ ] Celery/Redis for background jobs
- [ ] Log format auto-detection
- [ ] Structured JSON log support
- [ ] Export incident reports
- [ ] Webhook/Telegram alerts
