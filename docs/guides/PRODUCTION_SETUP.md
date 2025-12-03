# 🚀 HELIOS - Production Setup Guide

**Configure HELIOS to work with real AWS/GCP/Azure cloud services**

---

## 🎯 Overview

HELIOS supports **dual-mode operation**:
- **Demo Mode:** Uses mocks, no credentials required (default)
- **Production Mode:** Uses real cloud services with your credentials

The system **automatically detects** which mode to use based on environment variables.

---

## 📋 Prerequisites

Before setting up production mode, ensure you have:

1. **Cloud Accounts:**
   - AWS account with EventBridge access
   - GCP project with Pub/Sub API enabled
   - Azure subscription with Event Grid

2. **Required Permissions:**
   - AWS: `events:PutEvents` permission
   - GCP: `pubsub.topics.publish` permission
   - Azure: Event Grid Publisher role

3. **Local Setup:**
   - Python virtual environment activated
   - PostgreSQL running
   - Redis running

---

## 🔧 Configuration Steps

### Step 1: Create Environment File

```bash
cp .env.example .env
```

### Step 2: Configure AWS EventBridge

1. **Create EventBridge Event Bus** (optional, can use "default"):
   ```bash
   aws events create-event-bus --name helios-events
   ```

2. **Get AWS Credentials:**
   - Access Key ID
   - Secret Access Key

3. **Update `.env`:**
   ```bash
   DEPLOYMENT_MODE=production
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   AWS_EVENTBRIDGE_BUS_NAME=helios-events
   AWS_EVENT_SOURCE=helios.platform
   ```

### Step 3: Configure GCP Pub/Sub

1. **Create Pub/Sub Topic:**
   ```bash
   gcloud pubsub topics create helios-events
   ```

2. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create helios-publisher \
       --display-name="Helios Event Publisher"
   ```

3. **Grant Permissions:**
   ```bash
   gcloud pubsub topics add-iam-policy-binding helios-events \
       --member="serviceAccount:helios-publisher@your-project.iam.gserviceaccount.com" \
       --role="roles/pubsub.publisher"
   ```

4. **Create Key File:**
   ```bash
   gcloud iam service-accounts keys create helios-sa-key.json \
       --iam-account=helios-publisher@your-project.iam.gserviceaccount.com
   ```

5. **Update `.env`:**
   ```bash
   DEPLOYMENT_MODE=production
   GCP_PROJECT_ID=your-project-id
   GCP_PUBSUB_TOPIC=helios-events
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/helios-sa-key.json
   ```

### Step 4: Configure Azure Event Grid

1. **Create Event Grid Topic:**
   ```bash
   az eventgrid topic create \
       --name helios-events \
       --location eastus \
       --resource-group helios-rg
   ```

2. **Get Endpoint and Access Key:**
   ```bash
   # Get endpoint
   az eventgrid topic show \
       --name helios-events \
       --resource-group helios-rg \
       --query "endpoint" \
       --output tsv

   # Get access key
   az eventgrid topic key list \
       --name helios-events \
       --resource-group helios-rg \
       --query "key1" \
       --output tsv
   ```

3. **Update `.env`:**
   ```bash
   DEPLOYMENT_MODE=production
   AZURE_EVENT_GRID_ENDPOINT=https://helios-events.eastus-1.eventgrid.azure.net/api/events
   AZURE_EVENT_GRID_ACCESS_KEY=your_access_key
   AZURE_EVENT_GRID_TOPIC_HOSTNAME=helios-events.eastus-1.eventgrid.azure.net
   AZURE_EVENT_SUBJECT_PREFIX=helios
   ```

---

## 🚀 Running in Production Mode

### Option 1: Use .env File (Recommended)

```bash
# Create .env from example
cp .env.example .env

# Edit .env and set:
# DEPLOYMENT_MODE=production
# AWS_ACCESS_KEY_ID=...
# GCP_PROJECT_ID=...
# etc.

# Load environment
export $(cat .env | xargs)

# Start Helios
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```

### Option 2: Set Environment Variables Directly

```bash
export DEPLOYMENT_MODE=production
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export GCP_PROJECT_ID=...
# ... other variables

source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```

---

## ✅ Verify Production Setup

### Check Mode Detection

When you start Helios, check the logs:

```
{"event": "aws_client_mode", "mode": "production", "event_bus": "helios-events"}
{"event": "gcp_client_mode", "mode": "production", "project": "your-project-id"}
{"event": "azure_client_mode", "mode": "production", "endpoint": "https://..."}
```

If you see `"mode": "demo"`, credentials are not configured correctly.

### Test Event Publishing

Use the cloud publisher script:

```bash
# Test all clouds
python scripts/publish_to_cloud.py --cloud all

# Test specific cloud
python scripts/publish_to_cloud.py --cloud aws --order-id TEST-001

# Custom event
python scripts/publish_to_cloud.py \
    --cloud gcp \
    --event-type PaymentProcessed \
    --order-id ORD-123 \
    --amount 149.99
```

---

## 📊 Setting Up Cloud Webhooks

To receive events from cloud services back to Helios:

### AWS EventBridge → Helios

1. **Create EventBridge Rule:**
   ```bash
   aws events put-rule \
       --name helios-webhook \
       --event-pattern '{"source": ["helios.platform"]}'
   ```

2. **Add HTTP Target:**
   ```bash
   aws events put-targets \
       --rule helios-webhook \
       --targets "Id=1,Arn=arn:aws:events:us-east-1:123456789012:api-destination/helios,HttpParameters={HeaderParameters={Content-Type=application/json}}"
   ```

### GCP Pub/Sub → Helios

1. **Create Push Subscription:**
   ```bash
   gcloud pubsub subscriptions create helios-webhook \
       --topic=helios-events \
       --push-endpoint=https://your-helios-domain.com/api/v1/webhooks/gcp/pubsub
   ```

### Azure Event Grid → Helios

1. **Create Event Subscription:**
   ```bash
   az eventgrid event-subscription create \
       --name helios-webhook \
       --source-resource-id /subscriptions/.../resourceGroups/helios-rg/providers/Microsoft.EventGrid/topics/helios-events \
       --endpoint https://your-helios-domain.com/api/v1/webhooks/azure/eventgrid
   ```

---

## 🔒 Security Best Practices

### 1. Never Commit Credentials
```bash
# Add to .gitignore (already included in repo)
echo ".env" >> .gitignore
echo "*.json" >> .gitignore  # Service account keys
```

### 2. Use Secret Management

**AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
    --name helios/production \
    --secret-string file://.env
```

**GCP Secret Manager:**
```bash
gcloud secrets create helios-config \
    --data-file=.env
```

**Azure Key Vault:**
```bash
az keyvault secret set \
    --vault-name helios-vault \
    --name production-config \
    --file .env
```

### 3. Rotate Credentials Regularly

- AWS: Rotate access keys every 90 days
- GCP: Rotate service account keys quarterly
- Azure: Rotate Event Grid access keys monthly

### 4. Least Privilege

Only grant permissions needed:
- AWS: `events:PutEvents` only
- GCP: `pubsub.topics.publish` only
- Azure: Event Grid Publisher only

---

## 🐛 Troubleshooting

### "AWS credentials not configured"

**Check:**
```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

**Fix:**
Ensure variables are set in `.env` and loaded.

### "GCP project not found"

**Check:**
```bash
echo $GCP_PROJECT_ID
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS  # Should show JSON key
```

**Fix:**
1. Verify service account key file exists
2. Ensure path is absolute, not relative
3. Check file has read permissions

### "Azure Event Grid unauthorized"

**Check:**
```bash
echo $AZURE_EVENT_GRID_ENDPOINT
echo $AZURE_EVENT_GRID_ACCESS_KEY
```

**Fix:**
1. Verify endpoint URL is correct
2. Regenerate access key if needed
3. Check firewall rules allow your IP

### Events Not Appearing in Dashboard

**Check:**
1. Is Helios backend running?
2. Is the dashboard connected (green indicator)?
3. Check Helios logs for errors
4. Verify webhook subscriptions are active

---

## 📈 Monitoring Production

### CloudWatch (AWS)
```bash
aws cloudwatch get-metric-statistics \
    --namespace AWS/Events \
    --metric-name FailedInvocations \
    --dimensions Name=RuleName,Value=helios-webhook \
    --start-time 2025-01-01T00:00:00Z \
    --end-time 2025-01-02T00:00:00Z \
    --period 3600 \
    --statistics Sum
```

### Stackdriver (GCP)
```bash
gcloud logging read \
    "resource.type=pubsub_topic AND resource.labels.topic_id=helios-events" \
    --limit 50
```

### Azure Monitor
```bash
az monitor metrics list \
    --resource /subscriptions/.../providers/Microsoft.EventGrid/topics/helios-events \
    --metric PublishSuccessCount
```

---

## 💰 Cost Optimization

### AWS EventBridge
- First 1M events/month: FREE
- Additional: $1.00 per million events

### GCP Pub/Sub
- First 10 GB/month: FREE
- Additional: $0.06 per GB

### Azure Event Grid
- First 100K operations/month: FREE
- Additional: $0.60 per million operations

**Tip:** Use demo mode for development and testing to avoid cloud costs!

---

## 🎓 Next Steps

1. **Test Production Setup:** Run `python scripts/publish_to_cloud.py`
2. **Set Up Monitoring:** Configure CloudWatch/Stackdriver/Azure Monitor
3. **Configure Alerts:** Set up alerts for failed events
4. **Deploy to Cloud:** Move from local to cloud infrastructure

---

**Production Mode Status:** ✅ Available
**Last Updated:** November 26, 2025
**Documentation Version:** 1.0
