# Smart Resume Analyzer

An AI-powered resume analysis tool that scores resumes against target job roles, identifies ATS keyword gaps, and provides actionable improvement suggestions.

> **Capstone Project** — Built with React + Vite (frontend) and Python Flask (backend).

---

## Features

- **Resume Upload** — Drag-and-drop or click-to-upload support for PDF and DOCX files (max 5 MB)
- **Role-Based Analysis** — Choose from Data Analyst, Web Developer, AI Engineer, or Cloud Engineer
- **Transparent Scoring** — 7-category breakdown (Contact, Education, Skills, Experience, Projects, Certifications, Completeness) with per-category explanations
- **ATS Keyword Matching** — Weighted scoring that distinguishes core skills (2×) from optional skills (1×)
- **Certification Detection** — Finds certification entries via section headings and inline keyword patterns
- **Skill Extraction** — Controlled vocabulary of 150+ technologies matched using longest-match-first
- **Actionable Suggestions** — Context-specific improvement tips based on score gaps and missing keywords
- **Privacy First** — Resumes are analysed in-memory and never stored or logged

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite 8, Vanilla CSS |
| Backend | Python 3.14, Flask 3.1 |
| PDF Parsing | PyMuPDF |
| DOCX Parsing | python-docx |
| Testing | pytest (35 tests) |
| Deployment | Render (Gunicorn) |

---

## Architecture

```
┌─────────────────────────────┐
│  React Frontend (Vite)      │
│  UploadForm → ResultsDash   │
│  GET/POST /api/*            │
└──────────┬──────────────────┘
           │  HTTP (same origin)
┌──────────▼──────────────────┐
│  Flask Backend              │
│  /api/health  (GET)         │
│  /api/analyze (POST)        │
│                             │
│  ┌──────────────────────┐   │
│  │ PDF/DOCX Extraction  │   │
│  │ Section Scoring      │   │
│  │ Keyword Matching     │   │
│  │ Suggestion Engine    │   │
│  └──────────────────────┘   │
│                             │
│  Serves frontend dist/      │
│  in production              │
└─────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend Setup

```bash
cd backend
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

The API starts at `http://127.0.0.1:5000`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` with API proxy to the backend.

### Production Build

```bash
cd frontend
npm run build
# Built files go to frontend/dist/
# Flask serves these automatically in production
```

---

## API Reference

### `GET /api/health`

Liveness check.

```json
{
  "status": "ok",
  "message": "Smart Resume Analyzer API is running.",
  "supported_roles": ["Data Analyst", "Web Developer", "AI Engineer", "Cloud Engineer"]
}
```

### `POST /api/analyze`

Upload a resume for analysis.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume` | File | Yes | PDF or DOCX file (max 5 MB) |
| `role` | String | Yes | One of the supported roles |

**Response (200):**

```json
{
  "resume_score": 85.0,
  "ats_score": 72.5,
  "role": "Web Developer",
  "category_scores": {
    "contact": { "score": 10, "max": 10, "explanation": "..." },
    "education": { "score": 15, "max": 15, "explanation": "..." },
    "skills": { "score": 15, "max": 15, "explanation": "..." },
    "experience": { "score": 20, "max": 20, "explanation": "..." },
    "projects": { "score": 10, "max": 15, "explanation": "..." },
    "certifications": { "score": 10, "max": 10, "explanation": "..." },
    "completeness": { "score": 15, "max": 15, "explanation": "..." }
  },
  "matched_skills": ["javascript", "react", "html", "css", "git", "rest api"],
  "missing_skills": ["angular", "vue"],
  "keyword_match_pct": 72.5,
  "suggestions": ["Consider adding: angular, vue"]
}
```

**Error Responses:** 400 (validation), 413 (file too large), 422 (unreadable file)

---

## Testing

```bash
cd backend
.venv\Scripts\activate
python -m pytest test_analyzer.py -v
```

**35 tests** covering:
- Text extraction (PDF + DOCX)
- Certification detection (7 tests including edge cases)
- Section scoring (education, contact, projects, skills)
- Keyword/ATS matching (core vs optional, weighted percentages)
- Score consistency (category sums, weight validation)
- API contract (response structure, all fields present)
- Error handling (missing file, bad extension, empty file, missing/invalid role)

---

## Deployment

The app is deployed on **Render**: [Live Demo →](https://smart-resume-analyzer.onrender.com)

To deploy your own instance:

1. Push to GitHub
2. Connect the repo to [Render](https://render.com)
3. Set build command: `cd frontend && npm install && npm run build`
4. Set start command: `cd backend && pip install -r requirements.txt && gunicorn app:app`
5. The app serves both the API and the frontend from a single process

---

## Project Structure

```
smart-resume-analyzer/
├── backend/
│   ├── app.py              # Flask application (API + analysis engine)
│   ├── test_analyzer.py    # pytest test suite (35 tests)
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Root component with routing logic
│   │   ├── main.jsx        # React entry point
│   │   ├── index.css       # Design tokens & global styles
│   │   └── components/
│   │       ├── Hero.jsx/css        # Landing hero section
│   │       ├── UploadForm.jsx/css  # File upload + role selection
│   │       ├── ResultsDashboard.jsx/css  # Score breakdown display
│   │       └── Footer.jsx/css      # Privacy notice footer
│   ├── public/             # Static assets (favicon, icons)
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite config with API proxy
├── docs/                   # Project report & presentation
└── README.md               # This file
```

---

## License

This project was built as a capstone submission. All rights reserved.
