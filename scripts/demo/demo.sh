#!/bin/bash

# 🚀 HELIOS - One-Click Demo Script
# Starts all services and opens dashboard in browser

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root (go up 2 directories from scripts/demo/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                  ║${NC}"
echo -e "${BLUE}║       🚀 HELIOS PLATFORM - DEMO MODE 🚀          ║${NC}"
echo -e "${BLUE}║                                                  ║${NC}"
echo -e "${BLUE}║   Multi-Cloud Event Reconciliation Platform     ║${NC}"
echo -e "${BLUE}║                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${RED}✗ PostgreSQL not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL found${NC}"

# Check Redis
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}✗ Redis not found${NC}"
    echo -e "${YELLOW}  Starting Redis might require: brew services start redis${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis found${NC}"

echo ""

# Check if services are running
echo -e "${YELLOW}🔍 Checking if required services are running...${NC}"

# Check PostgreSQL
if ! pg_isready &> /dev/null; then
    echo -e "${RED}✗ PostgreSQL is not running${NC}"
    echo -e "${YELLOW}  Please start PostgreSQL first${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# Check Redis
if ! redis-cli ping &> /dev/null; then
    echo -e "${RED}✗ Redis is not running${NC}"
    echo -e "${YELLOW}  Starting Redis: brew services start redis${NC}"
    brew services start redis || exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"

echo ""

# Start backend
echo -e "${YELLOW}🔧 Starting Helios Backend (Port 8001)...${NC}"
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload > /tmp/helios-backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        cat /tmp/helios-backend.log
        kill $BACKEND_PID 2> /dev/null
        exit 1
    fi
done

echo ""

# Start dashboard
echo -e "${YELLOW}🎨 Starting Dashboard (Port 5173)...${NC}"
cd dashboard
pnpm run dev > /tmp/helios-dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd ..
echo -e "${GREEN}✓ Dashboard started (PID: $DASHBOARD_PID)${NC}"

# Wait for dashboard to be ready
echo -e "${YELLOW}⏳ Waiting for dashboard to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Dashboard is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Dashboard failed to start${NC}"
        cat /tmp/helios-dashboard.log
        kill $BACKEND_PID $DASHBOARD_PID 2> /dev/null
        exit 1
    fi
done

echo ""

# Start traffic simulator
echo -e "${YELLOW}📊 Starting Event Simulator (10 events/sec)...${NC}"
python scripts/simulate_traffic.py --rate 10 > /tmp/helios-simulator.log 2>&1 &
SIMULATOR_PID=$!
echo -e "${GREEN}✓ Simulator started (PID: $SIMULATOR_PID)${NC}"

echo ""

# Save PIDs for cleanup
echo "$BACKEND_PID $DASHBOARD_PID $SIMULATOR_PID" > /tmp/helios-demo.pid

echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║          ✅ HELIOS DEMO IS RUNNING! ✅           ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Services:${NC}"
echo -e "   Dashboard:    ${GREEN}http://localhost:5173${NC}"
echo -e "   API Docs:     ${GREEN}http://localhost:8001/docs${NC}"
echo -e "   Metrics:      ${GREEN}http://localhost:8001/metrics${NC}"
echo ""
echo -e "${BLUE}📊 Real-time Stats:${NC}"
echo -e "   Event Rate:   ${GREEN}~10 events/sec${NC}"
echo -e "   Sources:      ${GREEN}AWS (40%), GCP (30%), Azure (30%)${NC}"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo -e "   Backend:      ${YELLOW}/tmp/helios-backend.log${NC}"
echo -e "   Dashboard:    ${YELLOW}/tmp/helios-dashboard.log${NC}"
echo -e "   Simulator:    ${YELLOW}/tmp/helios-simulator.log${NC}"
echo ""
echo -e "${BLUE}🛑 To stop demo:${NC}"
echo -e "   ${YELLOW}./stop-demo.sh${NC}"
echo ""

# Wait for some events to accumulate
echo -e "${YELLOW}⏳ Generating sample events (waiting 10 seconds)...${NC}"
sleep 10

# Trigger reconciliation
echo -e "${YELLOW}🔍 Triggering reconciliation run...${NC}"
RECON_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/reconciliation/trigger \
  -H "Content-Type: application/json" \
  -d '{"window_minutes":30}')

if echo "$RECON_RESPONSE" | grep -q "run_id"; then
    RUN_ID=$(echo "$RECON_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['run_id'])" 2>/dev/null || echo "N/A")
    TOTAL=$(echo "$RECON_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_events'])" 2>/dev/null || echo "N/A")
    echo -e "${GREEN}✓ Reconciliation completed!${NC}"
    echo -e "   Run ID:       ${BLUE}${RUN_ID:0:30}...${NC}"
    echo -e "   Events:       ${BLUE}$TOTAL${NC}"
else
    echo -e "${YELLOW}⚠ Reconciliation trigger failed (continuing demo)${NC}"
fi

echo ""

# Open browser
echo -e "${YELLOW}🌐 Opening dashboard in browser...${NC}"
sleep 2
if command -v open &> /dev/null; then
    open http://localhost:5173
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
else
    echo -e "${YELLOW}   Please open http://localhost:5173 in your browser${NC}"
fi

echo ""
echo -e "${GREEN}✨ Enjoy the demo! Press Ctrl+C to stop all services${NC}"
echo -e "${BLUE}💡 Try:${NC}"
echo -e "   • Click the ${GREEN}Reconciliation${NC} tab to see event consistency"
echo -e "   • Trigger new reconciliation runs with different time windows"
echo -e "   • View detailed results for each reconciliation run"
echo ""

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping all services...${NC}"

    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null && echo -e "${GREEN}✓ Backend stopped${NC}"
    fi

    if [ -n "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null && echo -e "${GREEN}✓ Dashboard stopped${NC}"
    fi

    if [ -n "$SIMULATOR_PID" ]; then
        kill $SIMULATOR_PID 2>/dev/null && echo -e "${GREEN}✓ Simulator stopped${NC}"
    fi

    rm -f /tmp/helios-demo.pid
    echo -e "${GREEN}✅ All services stopped!${NC}"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT TERM

# Tail logs (this keeps the script running)
tail -f /tmp/helios-backend.log
