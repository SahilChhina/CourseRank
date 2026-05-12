# CourseRank AI

AI-powered course intelligence platform for **Western University** students. Search any course, see official details, grading breakdowns extracted from real syllabuses, student sentiment summaries from r/uwo, and explainable difficulty/workload scores.

> CourseRank AI provides unofficial, student-centered course summaries based on available course materials and aggregated feedback. It is not affiliated with Western University and should not replace official academic advising.

---

## What It Does

- **Course search** across 294+ Western courses (CS, SE, ECE, Math, Stats, Physics, etc.) scraped from the official Western Academic Calendar
- **Syllabus parsing** — upload a PDF or auto-find one online; extracts grading components and weights via a 3-layer pipeline (table → regex → fallback) with confidence scoring
- **Sentiment analysis** — pulls r/uwo posts/comments mentioning a course, runs VADER, surfaces positive/negative themes
- **Anonymous reviews** — students submit ratings (difficulty, workload, organization, fairness, usefulness, hours/week) which feed back into composite scores
- **Course comparison** — side-by-side grading, scores, sentiment, and a heuristic recommendation
- **Source transparency** — every report cites Western Calendar, syllabus, Reddit, and CourseRank reviews as data sources

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, Vite, Recharts |
| Backend | FastAPI, SQLAlchemy, Pydantic, Python 3.11 |
| Database | SQLite (dev) · PostgreSQL (prod) |
| NLP | VADER sentiment, regex-based theme extraction |
| PDF parsing | pdfplumber |
| Web scraping | requests + BeautifulSoup |
| Deployment | Vercel (frontend), Railway (backend + Postgres) |

---

## Architecture

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  React Frontend  │ ──API─▶│  FastAPI Backend │ ──SQL──▶│   PostgreSQL     │
│   (Vercel)       │         │    (Railway)     │         │    (Railway)     │
└──────────────────┘         └──────────────────┘         └──────────────────┘
                                      │
                                      ├──▶ Western Calendar Scraper
                                      ├──▶ Syllabus Finder (DDG + dept URLs)
                                      ├──▶ pdfplumber → Grading Extractor
                                      ├──▶ Reddit Scraper (r/uwo JSON)
                                      └──▶ VADER → Sentiment Analyzer
```

---

## Project Structure

```
courserank-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point + auto-seed
│   │   ├── database.py          # SQLAlchemy engine (sqlite/postgres)
│   │   ├── seed.py              # Starter course data
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── routes/              # API endpoints
│   │   ├── schemas/             # Pydantic request/response shapes
│   │   ├── services/            # Parsing, scoring, sentiment, scraping
│   │   └── scripts/             # Western calendar scraper
│   ├── requirements.txt
│   ├── Procfile                 # Railway deploy command
│   └── railway.json
└── frontend/
    ├── src/
    │   ├── api/                 # API client
    │   ├── components/          # ScorePill, GradingBreakdown, SentimentSummary, etc.
    │   ├── pages/               # Home, CourseReport, CompareCourses, SubmitReview
    │   └── types/
    ├── vite.config.ts
    └── vercel.json
```

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd courserank-ai/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed the SQLite DB with starter courses (auto-runs on first startup too)
python3 -m app.seed

# Start the API
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`. Interactive docs at `/docs`.

### Frontend

```bash
cd courserank-ai/frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`. The Vite dev server proxies `/api/*` to the backend.

---

## Populating Real Course Data

Three optional scripts/endpoints expand the database with real Western data:

**1. Scrape the Western Academic Calendar** (~5 min, polite delays):
```bash
python3 -m app.scripts.scrape_calendar              # priority subjects
python3 -m app.scripts.scrape_calendar --all        # all ~130 subjects
```

**2. Auto-find syllabus PDFs** for courses lacking grading data:
```bash
curl -X POST http://localhost:8000/admin/find-syllabus-batch?limit=50
```

**3. Pull r/uwo sentiment** for courses lacking sentiment data:
```bash
curl -X POST http://localhost:8000/admin/analyze-sentiment-batch?limit=50
```

---

## Deployment

### Backend → Railway

1. Push to GitHub
2. New project on [railway.app](https://railway.app) → Deploy from GitHub repo
3. Set root directory to `courserank-ai/backend`
4. Add a PostgreSQL plugin — Railway auto-injects `DATABASE_URL`
5. (Optional) Set `FRONTEND_URL` env var to your Vercel URL

Railway will run `uvicorn app.main:app --host 0.0.0.0 --port $PORT` from the Procfile. On first boot the DB is auto-seeded with starter courses.

### Frontend → Vercel

1. New project on [vercel.com](https://vercel.com) → Import from GitHub
2. Set root directory to `courserank-ai/frontend`
3. Add env var `VITE_API_URL` = your Railway backend URL (e.g. `https://courserank-backend.up.railway.app`)
4. Deploy

---

## API Highlights

```
GET  /health
GET  /courses/search?query=CS+2210
GET  /courses/{id}
POST /courses/compare
POST /courses/{id}/reviews
POST /admin/ingest-syllabus           (multipart PDF upload)
POST /admin/find-syllabus/{id}        (auto-find online)
POST /admin/analyze-sentiment/{id}    (r/uwo + VADER)
POST /admin/find-syllabus-batch
POST /admin/analyze-sentiment-batch
GET  /admin/stats
```

Full interactive docs at `/docs` (Swagger UI).

---

## Roadmap

- Admin/data dashboard UI
- Expand scraper to all 130 Western subjects
- Sentence-transformer embeddings for richer theme extraction
- Expand to other Canadian universities

---

## License

MIT
