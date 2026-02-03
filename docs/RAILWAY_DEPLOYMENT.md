# Railway Deployment Guide for Wealth of Agents

## Architecture

```
Railway Project: wealth-of-agents
├── API Service (api.main_production:app)
│   ├── PostgreSQL Database (Railway addon)
│   └── Environment variables
├── Web Service (Next.js frontend)
│   └── Environment variables
└── S3 Bucket (external AWS)
```

## Step-by-Step Deployment

### 1. Prepare Repository

```bash
cd /home/son/Desktop/GitHub/wealth-of-agents

# Ensure all files are committed
git add .
git commit -m "Add production backend with PostgreSQL"
git push origin main
```

### 2. Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `wealth-of-agents` repository

### 3. Set Up API Service

#### A. Add PostgreSQL Database
1. In Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create `DATABASE_URL` variable

#### B. Configure API Service
1. Click "New" → "GitHub Repo"
2. Select `wealth-of-agents`
3. Root Directory: `/` (leave empty for repo root)
4. Add environment variables:

```bash
# Required
PORT=8000
STORAGE_TYPE=s3
S3_BUCKET_NAME=wealth-of-agents-simulations
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
AWS_REGION=us-east-1

# Optional
CORS_ORIGINS=https://agents.sonpham.net,https://sonpham.net

# Database - automatically set by Railway when you add PostgreSQL
# DATABASE_URL=postgresql://user:pass@host:5432/railway
```

#### C. Configure Build
Railway auto-detects Python. If needed, customize:

**Build Command** (optional):
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
uvicorn api.main_production:app --host 0.0.0.0 --port $PORT
```

### 4. Set Up Web Service

1. In same Railway project, click "New" → "GitHub Repo"
2. Select `wealth-of-agents` again
3. Root Directory: `web`
4. Add environment variables:

```bash
NEXT_PUBLIC_API_URL=https://<your-api-service>.railway.app

# Or with custom domain:
NEXT_PUBLIC_API_URL=https://agents-api.sonpham.net
```

**Build Command**:
```bash
npm install && npm run build
```

**Start Command**:
```bash
npm start
```

### 5. Configure Custom Domains

#### API Service:
1. Click on API service
2. Settings → Networking → Custom Domain
3. Add: `agents-api.sonpham.net`
4. Copy the CNAME target

#### Web Service:
1. Click on Web service
2. Settings → Networking → Custom Domain
3. Add: `agents.sonpham.net`
4. Copy the CNAME target

#### DNS Configuration (HostGator):
```
Type: CNAME
Host: agents-api
Points to: <railway-cname-for-api>
TTL: 300

Type: CNAME
Host: agents
Points to: <railway-cname-for-web>
TTL: 300
```

### 6. Set Up AWS S3

```bash
# Create bucket
aws s3 mb s3://wealth-of-agents-simulations --region us-east-1

# Set CORS policy
aws s3api put-bucket-cors \
  --bucket wealth-of-agents-simulations \
  --cors-configuration file://s3-cors.json
```

**s3-cors.json**:
```json
{
  "CORSRules": [{
    "AllowedOrigins": ["https://agents.sonpham.net", "https://agents-api.sonpham.net"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}
```

### 7. Database Migrations (if needed)

Railway automatically runs migrations if you use Alembic:

```bash
# Local setup (optional)
cd /home/son/Desktop/GitHub/wealth-of-agents
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial tables"

# Railway will run this on deploy:
alembic upgrade head
```

Or tables are auto-created by SQLAlchemy on first run (current setup).

### 8. Test Deployment

```bash
# Health check
curl https://agents-api.sonpham.net/health

# Create test job
curl -X POST https://agents-api.sonpham.net/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "num_agents": 5,
    "num_steps": 50,
    "description": "Production test"
  }'

# Check job status
curl https://agents-api.sonpham.net/jobs/<job-id>
```

### 9. Monitor

Railway provides:
- **Logs**: View in real-time from dashboard
- **Metrics**: CPU, memory, network usage
- **Deployments**: Automatic on git push

## Environment Variables Reference

### API Service (Required):
```bash
DATABASE_URL          # Auto-set by Railway PostgreSQL addon
PORT                  # Auto-set by Railway (typically 8000)
STORAGE_TYPE          # 's3' for production
S3_BUCKET_NAME        # Your S3 bucket name
AWS_ACCESS_KEY_ID     # AWS credentials
AWS_SECRET_ACCESS_KEY # AWS credentials
AWS_REGION            # e.g., 'us-east-1'
```

### API Service (Optional):
```bash
CORS_ORIGINS          # Comma-separated allowed origins
ANTHROPIC_API_KEY     # For cognitive agents (LLM)
OPENAI_API_KEY        # Alternative LLM provider
```

### Web Service (Required):
```bash
NEXT_PUBLIC_API_URL   # URL of your API service
```

## Key Differences from Old Backend

| Feature | Old (In-Memory) | New (Production) |
|---------|----------------|------------------|
| Job Storage | ❌ RAM (lost on restart) | ✅ PostgreSQL (persistent) |
| File Storage | ❌ Local (ephemeral) | ✅ S3 (permanent) |
| Crash Recovery | ❌ No | ✅ Yes |
| Multiple Instances | ❌ No sync | ✅ Shared database |
| Health Checks | ❌ None | ✅ /health endpoint |
| Scalability | ❌ Single instance | ✅ Multiple workers possible |
| Database Migrations | ❌ N/A | ✅ Alembic support |

## Advantages for Railway

1. **Persistent Jobs**: Survives restarts and redeployments
2. **Health Checks**: Railway monitors `/health` endpoint
3. **PostgreSQL Integration**: Railway's managed database
4. **Auto-scaling Ready**: Can run multiple API instances
5. **Proper Timeouts**: 30-minute timeout for simulations
6. **Error Tracking**: All errors saved to database
7. **Cloud Storage**: Required (no ephemeral filesystem reliance)

## Cost Estimates

### Railway:
- **Hobby Plan**: $5/month (500 hours)
- **Pro Plan**: $20/month (unlimited hours)
- **PostgreSQL**: Included in plan
- **Bandwidth**: 100GB included

### AWS S3:
- **Storage**: $0.023/GB/month
- **Requests**: Minimal (<$1/month for typical usage)
- **Estimated**: ~$2-5/month

**Total**: ~$25-30/month for production-grade deployment

## Troubleshooting

### "relation does not exist" error:
Tables auto-create on first run. If issues:
```bash
railway run alembic upgrade head
```

### Database connection errors:
Check `DATABASE_URL` is set by Railway PostgreSQL addon.

### Simulation timeouts:
Increase timeout in `main_production.py` line 201:
```python
timeout=3600  # 60 minutes
```

### S3 upload failures:
Verify AWS credentials and bucket permissions.

## Rollback Plan

If production backend has issues, quickly revert:

1. Change Railway start command to old backend:
```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

2. Keep in-memory mode (no database required)

3. Accept that jobs won't persist across restarts

## Next Steps

1. ✅ Deploy to Railway with PostgreSQL
2. ✅ Configure S3 bucket and credentials
3. ✅ Set up custom domains
4. ✅ Test end-to-end workflow
5. 🔄 Monitor logs and performance
6. 🔄 Set up alerts (optional: Sentry, LogDNA)
7. 🔄 Configure automatic backups (Railway PostgreSQL)

---

**Status**: Ready for production deployment to Railway with persistent storage
