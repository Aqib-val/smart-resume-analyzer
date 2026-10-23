# Frontend — Smart Resume Analyzer

React + Vite single-page application for the Smart Resume Analyzer.

## Components

| Component | Purpose |
|-----------|---------|
| `Hero` | Landing section with tagline |
| `UploadForm` | Drag-and-drop file upload + role selection |
| `ResultsDashboard` | Score cards, category bars, skills chips, suggestions |
| `Footer` | Privacy notice |

## Development

```bash
npm install
npm run dev      # Dev server at http://localhost:5173
npm run build    # Production build to dist/
npm run preview  # Preview production build
npm run lint     # Run Oxlint
```

The dev server proxies `/api/*` to `http://127.0.0.1:5000` (see `vite.config.js`).
