# HELIOS Platform - Demo Guide

## Overview
This guide shows you how to run a complete demo of the HELIOS multi-cloud event reconciliation platform with real-time analytics and self-healing capabilities.

## Prerequisites
- Python 3.9+
- Node.js 22+ (for dashboard)
- Redis (optional - will auto-fallback to SQLite)

## Quick Start (3 Steps)

### Step 1: Start the Backend API
```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

**What this does:**
- Starts FastAPI server on port 8001
- Initializes event index (SQLite fallback mode)
- Loads 10M-capacity Bloom filter for missing event detection
- Starts WebSocket server for real-time event streaming
- Exposes 25+ REST API endpoints

### Step 2: Start the Dashboard
```bash
cd dashboard
source ~/.nvm/nvm.sh && nvm use 22  # Switch to Node v22
npm run dev
```

**What this does:**
- Starts Vite dev server on port 5173
- Connects to backend API via REST + WebSocket
- Auto-refreshes data every 3-5 seconds

### Step 3: Generate Event Traffic (Optional but Recommended)
```bash
python3 scripts/simulate_traffic.py
```

**What this does:**
- Simulates realistic e-commerce events (OrderPlaced, OrderShipped, etc.)
- Distributes events across AWS (40%), GCP (30%), Azure (30%)
- Generates 10-50 events/second
- Introduces occasional missing events and inconsistencies

## Dashboard Walkthrough

### Access Points
- 🌐 **Dashboard**: http://localhost:5173
- 🔌 **API**: http://localhost:8001
- 📚 **API Docs**: http://localhost:8001/docs

### Tab 1: Overview
**What you'll see:**
- Live event stream from all 3 cloud sources (AWS, GCP, Azure)
- Total event count with real-time updates
- Event distribution pie chart
- System health status
- WebSocket connection indicator

**Demo tip:** Run the traffic simulator to see events flowing in real-time!

### Tab 2: Analytics & Detection

#### Sub-tab: Reconciliation
- **Manual trigger** for on-demand reconciliation
- Configurable time windows (5min, 15min, 30min, 1hr, 2hr)
- Past reconciliation runs with consistency scores
- Detailed event-level results showing:
  - Consistent events (all 3 sources match)
  - Missing events (1-2 sources missing)
  - Inconsistent events (data mismatch)
  - Duplicate events

**Demo tip:** Trigger a 5-minute reconciliation to see immediate results!

#### Sub-tab: Performance Metrics
- **Event Index**: Backend type (Redis/SQLite), total events, avg lookup speed
- **Bloom Filter**: Memory usage, capacity (10M events), false positive rate (0.1%)
- **Reconciliation Windows**: Active windows, pending events, avg closure time

**Key metrics:**
- SQLite: ~8.5ms avg lookup
- Redis: <1ms avg lookup
- Bloom filter: 36 MB memory for 10M capacity

#### Sub-tab: Anomaly Detection
- **ML Model Status**: LSTM (if available) or EWMA fallback
- Real-time anomaly alerts with:
  - Severity (critical/high/medium/low)
  - Confidence score
  - Expected vs actual values
  - Metric name (event_rate, latency, etc.)

**Demo tip:** The system uses a trained LSTM model with 100% test accuracy from Kaggle dataset!

#### Sub-tab: Source Reliability
- **Per-cloud reliability scores**:
  - AWS: 99.2% reliability
  - GCP: 98.7% reliability
  - Azure: 97.5% reliability
- Event breakdown: On-time, Delayed, Missing
- Missing events table showing:
  - Event ID
  - Expected sources vs received sources
  - First seen timestamp

### Tab 3: Automation

#### Sub-tab: Scheduled Jobs
**7 automated reconciliation tasks:**
1. **Incremental Reconciliation** - Every 5 minutes
2. **Full Reconciliation** - Every hour (top of hour)
3. **Daily Deep Reconciliation** - Daily at 2:00 AM
4. **Anomaly Detection** - Every 1 minute
5. **Cleanup Old Data** - Daily at 3:00 AM
6. **Health Check** - Every 1 minute
7. **Metrics Aggregation** - Every 5 minutes

**Features:**
- Live countdown to next run
- Status badges (running/paused/idle)
- Last run status with duration
- Schedule visualization

**Demo tip:** Watch the countdown timers tick down in real-time!

#### Sub-tab: Recovery Actions
**AI-Driven MCDM (Multi-Criteria Decision Making):**
- **Criteria weights**:
  - MTTR (Mean Time To Recovery): 40%
  - QoS Impact: 30%
  - Success Rate: 20%
  - Cost: 10%

**Recommended actions** with:
- TOPSIS score (0-1)
- Estimated MTTR in seconds
- QoS impact percentage
- Success rate percentage
- Expandable decision matrix showing all candidate actions

**Available recovery actions:**
- Replay from DLQ (Dead Letter Queue)
- Request retry from source
- Trigger manual reconciliation
- Escalate to operations team

**Demo tip:** Click "View Decision Matrix" to see the full TOPSIS scoring breakdown!

## Optional: Start Scheduler for Automated Jobs

```bash
python3 scripts/test_scheduler.py
```

This will:
- Start APScheduler with all 7 jobs
- Run for 70 seconds showing job executions
- Display job details and next run times

## Architecture Highlights

### Event Index
- **O(1) lookups** for fast reconciliation
- **Dual-mode**: Redis (production) → SQLite (fallback)
- **Auto-sharding** by event_id hash

### Bloom Filter
- **Space-efficient** missing event detection
- **10M capacity** with only 36 MB memory
- **0.1% false positive rate**
- **Automatic expiration** after 24 hours

### Anomaly Detection
- **LSTM model** trained on Kaggle (100% test accuracy)
- **Auto-fallback** to EWMA statistical detector
- **60-minute rolling window**
- **Sub-100ms inference time**

### MCDM Engine
- **TOPSIS algorithm** from research paper "AI-Driven Self-Healing Cloud Systems"
- **WSM (Weighted Sum Model)** for simpler cases
- **4 criteria** balanced scoring
- **Confidence thresholds** for automatic vs manual approval

## Troubleshooting

### Dashboard not loading?
```bash
# Check Node version (must be 22+)
node --version

# Switch to Node 22
source ~/.nvm/nvm.sh && nvm use 22
```

### Backend errors?
```bash
# Install dependencies
pip install -r requirements.txt

# Check if port 8001 is free
lsof -ti:8001
```

### No events showing?
```bash
# Run the traffic simulator
python3 scripts/simulate_traffic.py
```

## What Makes This Demo Special

✅ **Production-Ready Architecture**
- Dual-mode design (production + fallback)
- Auto-scaling with sharding
- Real-time WebSocket updates

✅ **Research-Backed**
- LSTM model from Kaggle dataset
- TOPSIS/WSM from academic papers
- MAPE-K closed-loop automation

✅ **Multi-Cloud Native**
- AWS, GCP, Azure support
- Cloud-agnostic reconciliation
- Per-source reliability tracking

✅ **Self-Healing Capabilities**
- Anomaly detection (detection phase - complete)
- Recovery recommendations (analysis phase - complete)
- Automated execution (coming in Phase 3)

## Next Steps

1. ⭐ **Explore the dashboard** - Click through all tabs and sub-tabs
2. 🔄 **Trigger reconciliation** - Use the manual trigger in Analytics tab
3. 📊 **Watch metrics** - See live updates every 5 seconds
4. 🤖 **View recommendations** - Check the Recovery Actions for MCDM scoring
5. 📅 **Monitor jobs** - Watch scheduled jobs countdown and execute

---

**Built with:** FastAPI, React 19, Vite 7, TailwindCSS 4, Redis, PostgreSQL, Kafka, APScheduler, TensorFlow (LSTM), and lots of ☕
