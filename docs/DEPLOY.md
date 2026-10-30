# Deployment Guide — Render (backend) + Vercel (frontend)

This guide walks you through deploying IntentLens with:
- **Render** (free Python web service) — FastAPI backend
- **Vercel** (free hobby plan) — React frontend

The Neo4j AuraDB and Sarvam AI are cloud services — no additional hosting needed.

---

## Architecture after deployment

```
Browser
  │
  ▼
Vercel (React SPA)
  │  direct API calls via VITE_API_URL
  ▼
Render (FastAPI)  ──►  Neo4j AuraDB (cloud)
                  ──►  Sarvam AI (cloud)
```

---

## Prerequisites

- GitHub repository with this code pushed
- Neo4j AuraDB instance running (keep your URI, user, password)
- Sarvam AI API key
- Accounts at render.com and vercel.com (both free)

---

## Step 1 — Deploy the backend on Render

### 1a. Connect your repo

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
2. Connect your GitHub account and select your `intentlens` repository
3. Render will auto-detect `render.yaml` — click **Apply**

### 1b. Configure environment variables

In the Render dashboard → your service → **Environment**, add these secrets
(they are marked `sync: false` in `render.yaml` so Render won't auto-fill them):

| Key | Value |
|-----|-------|
| `NEO4J_URI` | `neo4j+s://xxxxxxxx.databases.neo4j.io` |
| `NEO4J_USER` | `xxxxxxxx` |
| `NEO4J_PASSWORD` | your AuraDB password |
| `NEO4J_DATABASE` | `xxxxxxxx` (same as user on AuraDB free) |
| `SARVAM_API_KEY` | `sk_...` |
| `GITHUB_TOKEN` | `ghp_...` (only needed if you re-run ingest) |
| `ALLOWED_ORIGINS` | leave blank for now — fill in after Vercel deploy |

### 1c. Deploy

Click **Save Changes** → Render builds and deploys automatically.

After ~3 minutes the service will be live. Copy the URL — it looks like:
```
https://intentlens-api.onrender.com
```

Test it:
```bash
curl https://intentlens-api.onrender.com/health
# → {"status":"ok"}

curl https://intentlens-api.onrender.com/stats
# → {"commits":1372,"decisions":570,...}
```

### 1d. Update ALLOWED_ORIGINS (after Vercel deploy)

Once you have your Vercel URL (Step 2), come back to Render → Environment and set:
```
ALLOWED_ORIGINS = https://your-app.vercel.app
```
Then click **Save** — Render redeploys automatically.

---

## Step 2 — Deploy the frontend on Vercel

### 2a. Import project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **Import Git Repository** → select your `intentlens` repo
3. Set the **Root Directory** to `frontend` (important!)
4. Framework: **Vite** (auto-detected)

### 2b. Set environment variables

In the Vercel project settings → **Environment Variables**, add:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://intentlens-api.onrender.com` |

> This is the Render URL from Step 1c. Vercel injects it at build time
> via `import.meta.env.VITE_API_URL` in `src/api.js`.

### 2c. Build settings (Vercel auto-detects these from package.json)

| Setting | Value |
|---------|-------|
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |

Click **Deploy**.

After ~2 minutes your frontend is live at:
```
https://intentlens.vercel.app
```

### 2d. Update Render CORS (loop back to Step 1d)

In Render → Environment → `ALLOWED_ORIGINS`:
```
https://intentlens.vercel.app
```
Save → redeploy.

---

## Step 3 — Verify end-to-end

Open your Vercel URL and test all three demo states:

```
/ask?demo=1
```

| Button | Expected |
|--------|----------|
| Multi-Part AOF | ANSWERED — High confidence, evidence rail |
| Bind address | ANSWERED with superseded banner + history |
| updateSlavesWaitingBgsave | REFUSED — last changers shown |

Check `/explore` — search `repl-backlog-size` and the graph loads.

---

## Troubleshooting

### "Failed to load resource: CORS error" in browser console

The Render `ALLOWED_ORIGINS` doesn't include your Vercel URL. Update it in
Render → Environment → `ALLOWED_ORIGINS` and redeploy.

### Backend returns 500 on `/ask`

Check Render logs. Most common cause: Neo4j AuraDB is paused (free tier pauses
after 72 hours of inactivity). Resume it at console.neo4j.io.

### Render service is sleeping (free tier)

Render free tier spins down after 15 minutes of inactivity. The first request
after sleep takes ~30 seconds. For a demo, send one warmup request first:
```bash
curl https://intentlens-api.onrender.com/health
```

### Stats strip shows zeros on landing page

The Sarvam key or Neo4j connection failed. Check `/ready` endpoint:
```bash
curl https://intentlens-api.onrender.com/ready
```

### "VITE_API_URL not set" — all API calls going to /api/...

The `VITE_API_URL` env var was not set before building on Vercel. Go to
Vercel → Settings → Environment Variables → add it → Redeploy.

---

## Free tier limits

| Service | Limit | Notes |
|---------|-------|-------|
| Render free | 750 hours/month, sleeps after 15 min | Upgrade to Starter $7/mo to avoid sleep |
| Vercel hobby | 100 GB bandwidth/month | More than enough |
| Neo4j AuraDB free | 1 instance, pauses after 72h idle | Resume takes ~30 sec |
| Sarvam AI | Pay-per-use | Very cheap for demo volumes |

---

## Custom domain (optional)

**Vercel:** Project → Settings → Domains → Add domain.

**Render:** Service → Settings → Custom Domain.

After adding a custom domain, update `ALLOWED_ORIGINS` in Render to include it.
