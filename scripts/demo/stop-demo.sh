#!/bin/bash

# 🛑 HELIOS - Stop Demo Script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping Helios Demo...${NC}"
echo ""

# Read PIDs
if [ -f /tmp/helios-demo.pid ]; then
    read -r BACKEND_PID DASHBOARD_PID SIMULATOR_PID < /tmp/helios-demo.pid

    # Kill processes
    if [ -n "$BACKEND_PID" ]; then
        echo -e "${YELLOW}⏹️  Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null && echo -e "${GREEN}✓ Backend stopped${NC}" || echo -e "${RED}✗ Backend not running${NC}"
    fi

    if [ -n "$DASHBOARD_PID" ]; then
        echo -e "${YELLOW}⏹️  Stopping dashboard (PID: $DASHBOARD_PID)...${NC}"
        kill $DASHBOARD_PID 2>/dev/null && echo -e "${GREEN}✓ Dashboard stopped${NC}" || echo -e "${RED}✗ Dashboard not running${NC}"
    fi

    if [ -n "$SIMULATOR_PID" ]; then
        echo -e "${YELLOW}⏹️  Stopping simulator (PID: $SIMULATOR_PID)...${NC}"
        kill $SIMULATOR_PID 2>/dev/null && echo -e "${GREEN}✓ Simulator stopped${NC}" || echo -e "${RED}✗ Simulator not running${NC}"
    fi

    rm /tmp/helios-demo.pid
else
    echo -e "${YELLOW}No PID file found. Searching for processes...${NC}"

    # Find and kill by port
    echo -e "${YELLOW}⏹️  Stopping processes on port 8001...${NC}"
    lsof -ti:8001 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✓ Port 8001 freed${NC}" || echo -e "${YELLOW}  Port 8001 already free${NC}"

    echo -e "${YELLOW}⏹️  Stopping processes on port 5173...${NC}"
    lsof -ti:5173 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✓ Port 5173 freed${NC}" || echo -e "${YELLOW}  Port 5173 already free${NC}"

    echo -e "${YELLOW}⏹️  Stopping event simulator...${NC}"
    pkill -f "simulate_traffic.py" 2>/dev/null && echo -e "${GREEN}✓ Simulator stopped${NC}" || echo -e "${YELLOW}  Simulator not running${NC}"
fi

echo ""
echo -e "${GREEN}✅ Helios demo stopped successfully!${NC}"
echo ""
