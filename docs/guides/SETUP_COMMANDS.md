# Helios - Commands to Start the Server

## What We Did to Get Everything Running

### 1. Created Helios Database in PostgreSQL
```bash
createdb helios
```

### 2. Ran Database Schema Initialization
```bash
psql -d helios -f scripts/init.sql
```
This created all the tables (events, reconciliation_results, self_healing_actions, replay_history).

### 3. Created Python Virtual Environment
```bash
python3 -m venv venv
```

### 4. Installed Python Dependencies
```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Created .env Configuration File
Created `/Users/pratham.mittal/Desktop/helios-platform/.env` with:
```env
APP_NAME=Helios
APP_VERSION=1.0.0
ENV=development
DEBUG=True
LOG_LEVEL=INFO

API_HOST=0.0.0.0
API_PORT=8000

# Database (using local PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=helios
POSTGRES_USER=pratham.mittal
POSTGRES_PASSWORD=

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Kafka (not running yet - will mock for now)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SCHEMA_REGISTRY_URL=http://localhost:8081

# Other settings...
```

### 6. Started FastAPI Server
```bash
cd /Users/pratham.mittal/Desktop/helios-platform
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

**Note:** We used port 8001 instead of 8000 because port 8000 was already in use.

---

## Quick Start (After Initial Setup)

If you need to start the server again, just run:

```bash
cd /Users/pratham.mittal/Desktop/helios-platform
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

Or use the Makefile:
```bash
cd /Users/pratham.mittal/Desktop/helios-platform
make dev
```

---

## Verify Services Are Running

### Check PostgreSQL
```bash
pg_isready
# Should show: /tmp:5432 - accepting connections
```

### Check Redis
```bash
redis-cli ping
# Should return: PONG
```

### Check Helios API
```bash
curl http://localhost:8001/api/v1/health
# Should return health status JSON
```

---

## Access Points

- **API Documentation**: http://localhost:8001/docs (Official Helios Port)
- **Health Check**: http://localhost:8001/api/v1/health
- **Prometheus Metrics**: http://localhost:8001/metrics

---

## Services Currently Running

✅ **PostgreSQL**: localhost:5432 (database: helios)
✅ **Redis**: localhost:6379
✅ **FastAPI**: localhost:8001

❌ **Kafka/Redpanda**: Not installed (we'll use mock for now)
❌ **Grafana**: Not installed (Docker required)
❌ **Prometheus**: Not installed (Docker required)

---

## Stop the Server

Press `CTRL+C` in the terminal where uvicorn is running.

