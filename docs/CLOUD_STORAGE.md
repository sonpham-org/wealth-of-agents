# Cloud Storage Setup Guide

## Overview
The Wealth of Agents platform supports multiple storage backends for simulation outputs:
- **Local**: Files stored on server filesystem (default, no setup required)
- **AWS S3**: Cloud storage with automatic upload (recommended for production)
- **Google Cloud Storage**: Alternative cloud storage option

## Local Storage (Default)
No configuration needed. Simulation outputs are stored in `output/` directory.

## AWS S3 Setup

### 1. Create S3 Bucket
```bash
# Using AWS CLI
aws s3 mb s3://wealth-of-agents-simulations --region us-east-1
```

Or create via AWS Console:
1. Go to S3 → Create bucket
2. Name: `wealth-of-agents-simulations`
3. Region: Choose closest to your server
4. Block all public access: **Enabled**
5. Enable versioning: **Optional** (recommended)

### 2. Configure IAM User/Role
Create an IAM user or role with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::wealth-of-agents-simulations",
        "arn:aws:s3:::wealth-of-agents-simulations/*"
      ]
    }
  ]
}
```

### 3. Configure Credentials

**Option A: AWS CLI** (Recommended for local development)
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

**Option B: Environment Variables** (For production/Railway)
```bash
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here
export AWS_REGION=us-east-1
export STORAGE_TYPE=s3
export S3_BUCKET_NAME=wealth-of-agents-simulations
```

**Option C: .env file**
```bash
cd /home/son/Desktop/GitHub/wealth-of-agents/api
cp .env.example .env
# Edit .env and set:
# STORAGE_TYPE=s3
# S3_BUCKET_NAME=wealth-of-agents-simulations
```

### 4. Test S3 Connection
```python
from api.storage import StorageManager

storage = StorageManager(storage_type='s3', bucket_name='wealth-of-agents-simulations')
runs = storage.list_runs()
print(f"Found {len(runs)} runs in S3")
```

## Google Cloud Storage Setup

### 1. Create GCS Bucket
```bash
gsutil mb -l us-east1 gs://wealth-of-agents-simulations
```

### 2. Create Service Account
1. Go to GCP Console → IAM & Admin → Service Accounts
2. Create service account with Storage Object Admin role
3. Download JSON key file

### 3. Configure Credentials
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export STORAGE_TYPE=gcs
export GCS_BUCKET_NAME=wealth-of-agents-simulations
```

## Railway Deployment

For Railway deployment with S3:

1. Add environment variables in Railway dashboard:
```
STORAGE_TYPE=s3
S3_BUCKET_NAME=wealth-of-agents-simulations
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_REGION=us-east-1
```

2. Update `requirements.txt` (already done):
```txt
boto3>=1.34.0
```

3. Deploy:
```bash
git add .
git commit -m "Add cloud storage support"
git push
```

## Storage Features

### Automatic Upload
When a simulation completes, files are automatically uploaded to configured storage:
- `simulation_data.json` - Complete simulation state
- `visualizer.html` - Standalone visualization
- `list_runs.json` - Index of all runs
- Any other generated outputs

### Dual Storage
With cloud storage enabled:
- Files are **always** saved locally first (for immediate access)
- Then uploaded to cloud storage in background
- This ensures no data loss if upload fails

### Retrieval
The API can retrieve simulations from either local or cloud storage transparently.

## Cost Considerations

### AWS S3 Pricing (as of 2026)
- Storage: ~$0.023/GB/month
- PUT requests: $0.005 per 1,000 requests
- GET requests: $0.0004 per 1,000 requests

**Estimated costs for 100 simulations/day:**
- Storage (10MB per simulation): ~$0.70/month
- Uploads: ~$0.15/month
- Downloads: ~$0.012/month
- **Total: ~$0.90/month**

### Cost Optimization
1. Enable S3 Lifecycle policies to archive old simulations to Glacier
2. Delete old local files after successful cloud upload
3. Use CloudFront CDN for frequently accessed visualizations

## Monitoring

Check storage usage:
```bash
# AWS S3
aws s3 ls s3://wealth-of-agents-simulations/ --recursive --human-readable --summarize

# Local
du -sh output/
```

## Troubleshooting

**"No module named 'boto3'"**
```bash
pip install boto3
```

**"Access Denied" errors**
- Check IAM permissions
- Verify bucket name matches configuration
- Confirm AWS credentials are set

**Slow uploads**
- Check network connection
- Consider using S3 Transfer Acceleration
- Upload in background (already implemented)
