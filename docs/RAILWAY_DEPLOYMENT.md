# Railway Deployment Guide for Wealth of Agents

## Architecture

```
Railway Project: wealth-of-agents
├── API Service (api.main_production:app)
│   ├── PostgreSQL Database (Railway addon)
│   └── Volume (/app/output) for simulation files
└── Web Service (Next.js frontend)
    └── Environment variables
```

**No external services required** — everything runs on Railway.

## Step-by-Step Deployment

### 1. Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `wealth-of-agents` repository

### 2. Set Up API Service

#### A. Add PostgreSQL Database
1. In Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create `DATABASE_URL` variable and link it to your service

#### B. Configure API Service
1. Click on your deployed service
2. Go to **Settings** tab
3. Set **Root Directory**: leave empty (repo root)
4. Set **Start Command**: `uvicorn api.main_production:app --host 0.0.0.0 --port $PORT`

#### C. Add Persistent Volume
1. Go to **Settings** → **Volumes**
2. Click "Add Volume"
3. **Mount Path**: `/app/output`
4. This ensures simulation output files persist across deploys

#### D. Set Environment Variables
Go to **Variables** tab and add:

```bash
# Storage (Railway-only, no AWS needed)
STORAGE_TYPE=local

# Optional: restrict CORS to your domains
CORS_ORIGINS=https://your-frontend.railway.app

# These are auto-set by Railway:
# DATABASE_URL (from PostgreSQL addon)
# PORT (Railway sets this)
```

### 3. Set Up Web Service

1. In same Railway project, click "New" → "GitHub Repo"
2. Select `wealth-of-agents` again
3. Configure:
   - **Root Directory**: `web`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`

4. Add environment variables:

```bash
NEXT_PUBLIC_API_URL=https://<your-api-service>.railway.app
```

> Tip: Get your API service URL from its Settings → Networking → Public Networking

### 4. Configure Networking (Optional)

#### Generate Public URLs
For each service:
1. Click on service → Settings → Networking
2. Click "Generate Domain" to get a `.railway.app` URL

#### Custom Domains (Optional)
1. Settings → Networking → Custom Domain
2. Add your domain (e.g., `agents-api.yourdomain.com`)
3. Configure DNS with the provided CNAME target

### 5. Test Deployment

```bash
# Health check
curl https://<your-api>.railway.app/health

# Create test job
curl -X POST https://<your-api>.railway.app/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "num_agents": 5,
    "num_steps": 50,
    "description": "Test simulation"
  }'

# Check job status
curl https://<your-api>.railway.app/jobs/<job-id>
```

## Environment Variables Reference

### API Service

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Auto | Set by Railway PostgreSQL addon |
| `PORT` | Auto | Set by Railway |
| `STORAGE_TYPE` | No | `local` (default) - uses Railway Volume |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `ANTHROPIC_API_KEY` | No | For LLM-powered agents |

### Web Service

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | URL of your API service |

## How It Works

1. **Jobs** are stored in PostgreSQL (persists across restarts)
2. **Simulation files** are stored in the Railway Volume at `/app/output`
3. **No external services** — everything is self-contained on Railway

## Cost Estimate

| Component | Cost |
|-----------|------|
| Railway Hobby Plan | $5/month |
| PostgreSQL | Included |
| Volume Storage | Included (up to 5GB) |
| **Total** | **~$5/month** |

## Monitoring

Railway provides:
- **Logs**: Real-time in dashboard
- **Metrics**: CPU, memory, network
- **Deployments**: Automatic on git push

## Troubleshooting

### "relation does not exist" error
Tables auto-create on first run. If issues persist, redeploy the service.

### Database connection errors
Ensure PostgreSQL addon is linked to your service (check Variables tab for `DATABASE_URL`).

### Simulation files disappear after redeploy
Make sure you've attached a Volume to `/app/output`.

### Health check failing
Check logs for startup errors. Common issues:
- Missing `DATABASE_URL`
- Import errors (missing dependencies)

## Rollback Plan

If production backend has issues:

1. Change start command to use simple backend:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

2. This uses in-memory storage (jobs won't persist, but it works without database)
