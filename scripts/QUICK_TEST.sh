#!/bin/bash

# Helios Quick Test Script
# Run this to quickly verify all cloud adapters are working

echo "🎯 HELIOS QUICK TEST"
echo "===================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Testing $name... "
    response=$(curl -s "$url")

    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        echo "  Response: $response"
    fi
}

# Test AWS webhook
echo -e "${YELLOW}1. Testing AWS EventBridge${NC}"
curl -s -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "quick-test-aws-'"$(date +%s)"'",
    "detail-type": "OrderPlaced",
    "source": "test",
    "account": "123",
    "time": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
    "region": "us-east-1",
    "detail": {
      "order_id": "QUICK-AWS-'"$(date +%s)"'",
      "customer_id": "TEST",
      "amount": 100
    }
  }' | jq -r '.status' | grep -q "accepted" && echo -e "${GREEN}✓ AWS PASS${NC}" && ((PASSED++)) || (echo -e "${RED}✗ AWS FAIL${NC}" && ((FAILED++)))

echo ""

# Test Azure webhook
echo -e "${YELLOW}2. Testing Azure Event Grid${NC}"
curl -s -X POST http://localhost:8001/api/v1/webhooks/azure/eventgrid \
  -H "Content-Type: application/json" \
  -d '[{
    "id": "quick-test-azure-'"$(date +%s)"'",
    "eventType": "OrderPlaced",
    "subject": "test",
    "eventTime": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
    "data": {
      "order_id": "QUICK-AZURE-'"$(date +%s)"'",
      "customer_id": "TEST",
      "amount": 200
    },
    "dataVersion": "1.0"
  }]' | jq -r '.status' | grep -q "processed" && echo -e "${GREEN}✓ AZURE PASS${NC}" && ((PASSED++)) || (echo -e "${RED}✗ AZURE FAIL${NC}" && ((FAILED++)))

echo ""

# Test Direct Ingestion
echo -e "${YELLOW}3. Testing Direct Ingestion${NC}"
curl -s -X POST http://localhost:8001/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "OrderPlaced",
    "source": "aws",
    "payload": {
      "order_id": "QUICK-DIRECT-'"$(date +%s)"'",
      "customer_id": "TEST",
      "amount": 300
    },
    "metadata": {}
  }' | jq -r '.status' | grep -q "accepted" && echo -e "${GREEN}✓ DIRECT PASS${NC}" && ((PASSED++)) || (echo -e "${RED}✗ DIRECT FAIL${NC}" && ((FAILED++)))

echo ""

# Test Reconciliation
echo -e "${YELLOW}4. Testing Reconciliation - Trigger${NC}"
RECON_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/reconciliation/trigger \
  -H "Content-Type: application/json" \
  -d '{"window_minutes":30}')

if echo "$RECON_RESPONSE" | jq -e '.run_id' > /dev/null 2>&1; then
    RUN_ID=$(echo "$RECON_RESPONSE" | jq -r '.run_id')
    TOTAL_EVENTS=$(echo "$RECON_RESPONSE" | jq -r '.total_events')
    echo -e "${GREEN}✓ RECONCILIATION TRIGGERED${NC}"
    echo "  Run ID: $RUN_ID"
    echo "  Events checked: $TOTAL_EVENTS"
    ((PASSED++))
else
    echo -e "${RED}✗ RECONCILIATION TRIGGER FAIL${NC}"
    echo "  Response: $RECON_RESPONSE"
    ((FAILED++))
fi

echo ""

# Test Reconciliation Results
if [ -n "$RUN_ID" ]; then
    echo -e "${YELLOW}5. Testing Reconciliation - Get Results${NC}"
    RESULTS=$(curl -s "http://localhost:8001/api/v1/reconciliation/results?run_id=$RUN_ID&limit=5")

    if echo "$RESULTS" | jq -e '. | length' > /dev/null 2>&1; then
        RESULT_COUNT=$(echo "$RESULTS" | jq '. | length')
        echo -e "${GREEN}✓ RESULTS RETRIEVED${NC}"
        echo "  Found $RESULT_COUNT reconciliation results"
        ((PASSED++))
    else
        echo -e "${RED}✗ RESULTS RETRIEVAL FAIL${NC}"
        ((FAILED++))
    fi

    echo ""

    # Test Reconciliation Summary
    echo -e "${YELLOW}6. Testing Reconciliation - Summary Stats${NC}"
    SUMMARY=$(curl -s "http://localhost:8001/api/v1/reconciliation/summary?hours=24")

    if echo "$SUMMARY" | jq -e '.total_events_checked' > /dev/null 2>&1; then
        TOTAL_CHECKED=$(echo "$SUMMARY" | jq -r '.total_events_checked')
        CONSISTENCY=$(echo "$SUMMARY" | jq -r '.consistency_percentage')
        echo -e "${GREEN}✓ SUMMARY RETRIEVED${NC}"
        echo "  Total events checked: $TOTAL_CHECKED"
        echo "  Consistency: ${CONSISTENCY}%"
        ((PASSED++))
    else
        echo -e "${RED}✗ SUMMARY RETRIEVAL FAIL${NC}"
        ((FAILED++))
    fi

    echo ""

    # Test Reconciliation Runs
    echo -e "${YELLOW}7. Testing Reconciliation - Recent Runs${NC}"
    RUNS=$(curl -s "http://localhost:8001/api/v1/reconciliation/runs?limit=5")

    if echo "$RUNS" | jq -e '. | length' > /dev/null 2>&1; then
        RUN_COUNT=$(echo "$RUNS" | jq '. | length')
        echo -e "${GREEN}✓ RUNS RETRIEVED${NC}"
        echo "  Found $RUN_COUNT recent runs"
        ((PASSED++))
    else
        echo -e "${RED}✗ RUNS RETRIEVAL FAIL${NC}"
        ((FAILED++))
    fi
fi

echo ""
echo "===================="
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo ""

# Check database
echo -e "${YELLOW}Database Stats:${NC}"
psql -d helios -c "SELECT source, COUNT(*) FROM events GROUP BY source;" 2>/dev/null || echo "Database check skipped"

echo ""
echo -e "${GREEN}✅ Quick test complete!${NC}"
echo ""
echo "📚 For detailed testing, see: TESTING_GUIDE.md"
echo "📊 For API docs, visit: http://localhost:8001/docs"
