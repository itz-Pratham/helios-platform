# Phase 2 Dashboard Integration Plan

**Date:** December 20, 2025
**Status:** Backend Complete → Dashboard Integration Starting
**Goal:** Visual showcase of Phase 2 ML-Enhanced Reconciliation capabilities

---

## ⚠️ Important Constraint

**Phase 2 = DETECTION + ANALYSIS (NOT Execution)**

Self-healing **execution** happens in Phase 3. Phase 2 focuses on:
- Detecting problems (anomalies, missing events, latency)
- Analyzing root causes
- Recommending recovery actions
- **NOT** executing those actions

---

## 🎨 What We CAN Showcase (6 Dashboard Components)

### 1. **Reconciliation Metrics Tab** ⭐ PRIMARY TAB

**Visual Components:**
- **Event Index Stats Card**
  - Total events indexed: 1,234,567
  - Redis/SQLite mode indicator
  - Lookup performance: <1ms (Redis) or <10ms (SQLite)
  - Events by source: AWS (40%), GCP (30%), Azure (30%)

- **Bloom Filter Stats Card**
  - Memory usage: 36 MB / 50 MB
  - False positive rate: 0.1%
  - Capacity: 10M events
  - Current load: 2.4M events

- **Reconciliation Window Stats**
  - Active windows: 45
  - Events pending reconciliation: 123
  - Average window closure time: 32s
  - Window timeout rate: 2%

- **Shard Distribution Chart** (Pie/Bar)
  - Events per shard (if multi-shard mode)
  - Single shard mode indicator (local dev)

**API Endpoints Needed:**
```python
GET /api/v1/reconciliation/metrics
{
  "event_index": {
    "backend": "redis",  # or "sqlite"
    "total_events": 1234567,
    "avg_lookup_ms": 0.8,
    "by_source": {"aws": 493827, "gcp": 370370, "azure": 370370}
  },
  "bloom_filter": {
    "memory_mb": 36,
    "capacity": 10000000,
    "current_load": 2400000,
    "false_positive_rate": 0.001
  },
  "reconciliation_windows": {
    "active": 45,
    "pending_events": 123,
    "avg_closure_sec": 32,
    "timeout_rate": 0.02
  }
}
```

---

### 2. **LSTM Anomaly Alerts Display** ⚠️ CRITICAL FOR DEMO

**Visual Components:**
- **Real-Time Alert Feed** (like Twitter feed)
  - Timestamp: "2025-12-20 11:45:32"
  - Severity badge: 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / 🟢 LOW
  - Alert message: "Missing event rate spike detected (0.15 → 0.87)"
  - Confidence score: 94% (from LSTM)
  - Model type badge: "LSTM" or "EWMA Fallback"
  - Expected vs Actual values

- **Anomaly Chart** (Time Series)
  - X-axis: Last 60 minutes
  - Y-axis: Anomaly probability (0-1)
  - Threshold line: 0.5 (configurable)
  - Color-coded: Green (normal) → Red (anomaly)
  - Annotations for detected anomalies

- **Model Status Card**
  - Model type: LSTM (if loaded) or EWMA (if fallback)
  - Window size: 60 minutes
  - Features tracked: 8
  - Total parameters: 121,665 (LSTM)
  - Last inference time: 45ms

**WebSocket Stream:**
```javascript
ws://localhost:8001/api/v1/ws/anomaly-alerts

// Message format:
{
  "timestamp": "2025-12-20T11:45:32Z",
  "metric_name": "missing_event_rate",
  "is_anomaly": true,
  "confidence": 0.94,
  "severity": "critical",
  "model_type": "lstm",
  "expected_value": 0.02,
  "actual_value": 0.87,
  "message": "Missing event rate spike detected (expected: 0.02, actual: 0.87)"
}
```

**API Endpoints:**
```python
GET /api/v1/anomaly/recent?limit=50
GET /api/v1/anomaly/stats
GET /api/v1/anomaly/model-status
```

---

### 3. **Scheduled Jobs Status Panel** 📅 SECONDARY TAB

**Visual Components:**
- **Jobs Table** (7 rows)
  - Job name
  - Schedule (cron/interval)
  - Next run time (countdown timer)
  - Last run result: ✅ Success / ❌ Failed
  - Last run duration: 0.5s
  - Status: 🟢 Running / 🔴 Paused / ⚪ Idle

- **Job Execution Timeline** (Gantt-like chart)
  - X-axis: Last 24 hours
  - Y-axis: 7 jobs
  - Visual bars showing when each job ran
  - Color-coded by success/failure

- **Recent Executions Log** (scrollable list)
  - Timestamp: "11:45:00"
  - Job: "Incremental Reconciliation"
  - Status: ✅ Completed in 0.32s
  - Events reconciled: 1,234

**API Endpoints:**
```python
GET /api/v1/scheduler/jobs
{
  "jobs": [
    {
      "id": "incremental_reconciliation",
      "name": "Incremental Reconciliation",
      "schedule": "interval[0:05:00]",
      "next_run": "2025-12-20T11:50:00Z",
      "last_run": {
        "timestamp": "2025-12-20T11:45:00Z",
        "status": "success",
        "duration_sec": 0.32,
        "events_reconciled": 1234
      }
    },
    // ... 6 more jobs
  ]
}

GET /api/v1/scheduler/execution-history?hours=24
```

---

### 4. **Missing Events Timeline** 📊 DETECTION SHOWCASE

**Visual Components:**
- **Missing Events Chart** (Time Series)
  - X-axis: Last 6 hours
  - Y-axis: Missing event count
  - 3 lines: AWS, GCP, Azure
  - Annotations for spikes

- **Missing Events Table** (Recent 50)
  - Event ID
  - Expected sources: [AWS, GCP, Azure]
  - Received sources: [AWS, GCP] ← Missing: Azure
  - First seen: "11:30:45"
  - Window timeout: "11:31:45" (60s)
  - Status: 🔴 Missing / 🟡 Delayed / 🟢 Reconciled

- **Source Reliability Score**
  - AWS: 99.2% (events received on time)
  - GCP: 98.7%
  - Azure: 97.5% ← Lowest (highlight in yellow)

**API Endpoints:**
```python
GET /api/v1/reconciliation/missing-events?hours=6
GET /api/v1/reconciliation/source-reliability
```

**WebSocket Stream:**
```javascript
ws://localhost:8001/api/v1/ws/missing-events

// Message format:
{
  "event_id": "ORD-12345",
  "expected_sources": ["aws", "gcp", "azure"],
  "received_sources": ["aws", "gcp"],
  "missing_sources": ["azure"],
  "first_seen": "2025-12-20T11:30:45Z",
  "window_timeout": "2025-12-20T11:31:45Z",
  "status": "missing"
}
```

---

### 5. **Recovery Action Recommendations Log** 💡 PLANNING SHOWCASE

**Visual Components:**
- **Recommendations Feed** (like GitHub Actions log)
  - Timestamp: "11:45:32"
  - Detected Issue: "3 missing events from Azure (last 5 min)"
  - Recommended Action: "Replay from Kafka DLQ"
  - TOPSIS Score: 0.87 / 1.0
  - Rationale: Click to expand decision matrix
  - Status: ⏳ **Awaiting Phase 3 Execution Engine**

- **MCDM Decision Matrix** (Modal/Expandable)
  - Shows all candidate actions evaluated
  - Criteria: MTTR, QoS Impact, Success Rate, Cost
  - Scores for each action
  - Final ranking
  - Why the top action was chosen

- **Action Success Rate Chart** (from Feedback Loop)
  - X-axis: Recovery actions
  - Y-axis: Historical success rate
  - Data from previous executions (simulated for Phase 2)

**API Endpoints:**
```python
GET /api/v1/recovery/recommendations?limit=50
{
  "recommendations": [
    {
      "timestamp": "2025-12-20T11:45:32Z",
      "issue": {
        "type": "missing_events",
        "description": "3 missing events from Azure (last 5 min)",
        "severity": "high",
        "event_ids": ["ORD-123", "ORD-124", "ORD-125"]
      },
      "recommended_action": {
        "name": "replay_from_kafka",
        "description": "Replay missing events from Kafka DLQ",
        "topsis_score": 0.87,
        "estimated_mttr_sec": 45,
        "qos_impact": 0.1,
        "success_rate": 0.95
      },
      "decision_matrix": {
        "criteria": ["mttr", "qos_impact", "success_rate", "cost"],
        "candidates": [
          {"action": "replay_from_kafka", "scores": [0.9, 0.95, 0.95, 0.8]},
          {"action": "scale_consumers", "scores": [0.5, 0.98, 0.85, 0.4]},
          // ...
        ],
        "weights": [0.4, 0.3, 0.2, 0.1]
      },
      "status": "pending_phase3_executor"
    }
  ]
}

GET /api/v1/recovery/action-success-rates
```

---

### 6. **MCDM Decision Explanations** 🧠 RESEARCH SHOWCASE

**Visual Components:**
- **Interactive Decision Tree Visualization**
  - Root: Detected anomaly
  - Branches: Criteria evaluated (MTTR, QoS, etc.)
  - Leaves: Candidate actions
  - Color-coded by score

- **Criteria Weights Card**
  - MTTR (Mean Time To Recovery): 40%
  - QoS Impact: 30%
  - Historical Success Rate: 20%
  - Resource Cost: 10%
  - Source: Entropy-weighted model

- **Comparison Table**
  - Rows: All candidate actions
  - Columns: MTTR, QoS, Success Rate, Cost, TOPSIS Score
  - Highlight: Top-ranked action in green

**API Endpoints:**
```python
GET /api/v1/mcdm/decision-tree?recommendation_id={id}
GET /api/v1/mcdm/criteria-weights
```

---

## 🚫 What We CANNOT Showcase (Phase 3 Features)

These will be grayed out or show "Phase 3 Coming Soon" badges:

1. ❌ **Execution Progress Bars** - No actual execution yet
2. ❌ **Circuit Breaker Status** - Detection only, not control
3. ❌ **Auto-scaling Visualization** - Recommendations only
4. ❌ **DLQ Replay Progress** - Planning only
5. ❌ **Success/Failure Rate from Real Executions** - Using simulated data

**Strategy:** Show these sections with placeholder states:
- "Execution Engine: Phase 3"
- "Current Status: Analysis & Planning Mode"
- "Actions will be executed in Phase 3"

---

## 📱 Dashboard Navigation Structure

```
HELIOS Dashboard
├── 🏠 Home (Phase 1.5 - existing)
│   ├── Live Event Stream
│   ├── Stats Cards
│   └── Cloud Distribution Chart
│
├── 🔍 Reconciliation (Phase 2 - NEW)
│   ├── Overview Tab (Metrics)
│   ├── Anomaly Alerts Tab (LSTM)
│   ├── Scheduled Jobs Tab
│   ├── Missing Events Tab
│   └── Recommendations Tab (MCDM)
│
├── 🔧 Self-Healing (Phase 3 - Placeholder)
│   └── "Coming in Phase 3" badge
│
├── 📋 Schema Registry (Phase 4 - Placeholder)
│   └── "Coming in Phase 4" badge
│
└── ⏪ Time Travel (Phase 5 - Placeholder)
    └── "Coming in Phase 5" badge
```

---

## 🛠️ Implementation Priority

### **Week 1: Core Metrics & Alerts**
1. ✅ Backend API endpoints for metrics
2. ✅ Reconciliation Metrics Tab UI
3. ✅ LSTM Anomaly Alerts Display
4. ✅ WebSocket integration for real-time alerts

### **Week 2: Jobs & Missing Events**
5. ✅ Scheduled Jobs Status Panel
6. ✅ Missing Events Timeline
7. ✅ Source reliability tracking

### **Week 3: Decision Engine Showcase**
8. ✅ Recovery Recommendations Log
9. ✅ MCDM Decision Explanations
10. ✅ Interactive decision tree visualization

### **Week 4: Polish & Integration**
11. ✅ Navigation between tabs
12. ✅ Responsive design for all components
13. ✅ Loading states and error handling
14. ✅ Phase 3 placeholder sections

---

## 🎯 Success Criteria

**Phase 2 is COMPLETE when:**

✅ Backend APIs return all required data
✅ Dashboard shows 6 new components
✅ Real-time WebSocket streams working
✅ Can demo to non-technical person and they understand:
   - System is detecting problems
   - System is analyzing solutions
   - System is NOT yet executing (Phase 3)
✅ Screenshots/screen recording for portfolio
✅ README updated with Phase 2 dashboard features

---

## 📸 Demo Script (30 seconds)

1. **Open Dashboard** → Shows Reconciliation tab
2. **Point to Anomaly Alert** → "LSTM detected missing event spike"
3. **Show Missing Events Timeline** → "Azure is 2% slower than AWS"
4. **Open Recommendation** → "System recommends Kafka replay (87% confidence)"
5. **Show Decision Matrix** → "Uses TOPSIS algorithm from research paper"
6. **Conclude** → "Phase 3 will execute these actions automatically"

---

## 🔗 Technical Stack (Same as Phase 1.5)

- **Frontend:** React 19 + Vite 7
- **Styling:** TailwindCSS 4
- **Charts:** Recharts 3
- **State:** React Query 5 + Zustand
- **WebSocket:** Native WebSocket API
- **Backend:** FastAPI + WebSockets

---

## 🚀 Let's Start Building!

**First Task:** Create backend API endpoints for reconciliation metrics.

Ready to proceed? 🎨

---
