# Deployment Guide

## Prerequisites

- Neo4j AuraDB instance (free tier works)
- Sarvam AI API key (free tier)
- GitHub personal access token (for PR ingestion — optional for demo)
- Render.com account (backend)
- Vercel account (frontend)

## Backend (Render)

1. Push the repo to GitHub
2. Create a new Web Service on Render, connect the repo
3. Use the included `Dockerfile` (or `render.yaml` for IaC)
4. Set these environment variables in the Render dashboard:
   - `NEO4J_URI` — your AuraDB connection URI
   - `NEO4J_USER` — AuraDB username
   - `NEO4J_PASSWORD` — AuraDB password
   - `NEO4J_DATABASE` — database name (usually `neo4j`)
   - `SARVAM_API_KEY` — your Sarvam API key
   - `LLM_PROVIDER=sarvam`
   - `SARVAM_MODEL=sarvam-105b`
   - `ALLOWED_ORIGINS` — your Vercel frontend URL
   - `GITHUB_TOKEN` — optional, for PR ingestion
5. Deploy. Health check: `GET /health` should return `{"status":"ok"}`

## Frontend (Vercel)

1. `cd frontend && npm install && npm run build` — verify the build works
2. Import the `frontend/` directory to Vercel
3. Set the API base URL environment variable:
   - `VITE_API_BASE` — your Render backend URL (e.g., `https://intentlens-api.onrender.com`)
4. The Vite config proxies `/api` to the backend in dev mode; in production, the frontend calls the API base directly

## Post-deploy: Load the graph

```bash
# On your local machine (with the repo cloned and venv active):
# 1. Apply schema to the remote AuraDB
python -m scripts.apply_schema

# 2. Ingest data (git + docs)
python -m scripts.ingest

# 3. Build the graph (mines decisions via Sarvam — this takes ~30 min for 200 threads)
python -m scripts.build_graph --limit 200

# 4. Run supersession
python -m scripts.run_supersession

# 5. Warm the demo cache
python -m scripts.warm_demo
```

## Smoke test

```bash
python -m scripts.smoke_test https://your-render-url.onrender.com
```

## Security checklist

- [ ] No secrets in `.env` are committed (`.gitignore` excludes `.env`)
- [ ] `.env.example` has placeholder values only
- [ ] Render/Vercel env vars are set in the dashboard, not in code
- [ ] CORS is restricted via `ALLOWED_ORIGINS`
- [ ] No API keys in logs (Sarvam usage logs only show token counts, not the key)
