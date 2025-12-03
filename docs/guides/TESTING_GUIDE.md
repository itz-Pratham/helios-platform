# 🧪 Helios Testing Guide

Complete curl commands to test all endpoints and features.

---

## 📋 Table of Contents
1. [System Health Checks](#system-health-checks)
2. [AWS EventBridge Tests](#aws-eventbridge-tests)
3. [GCP Pub/Sub Tests](#gcp-pubsub-tests)
4. [Azure Event Grid Tests](#azure-event-grid-tests)
5. [Direct Event Ingestion](#direct-event-ingestion)
6. [Validation Tests](#validation-tests)
7. [Deduplication Tests](#deduplication-tests)
8. [Database Queries](#database-queries)

---

## System Health Checks

### 1. Root Endpoint
```bash
curl http://localhost:8001/
```

**Expected Response:**
```json
{
  "name": "Helios",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/docs",
  "metrics": "/metrics"
}
```

### 2. API Health Check
```bash
curl http://localhost:8001/api/v1/health
```

### 3. AWS Webhook Health
```bash
curl http://localhost:8001/api/v1/webhooks/aws/health
```

### 4. GCP Webhook Health
```bash
curl http://localhost:8001/api/v1/webhooks/gcp/health
```

### 5. Azure Webhook Health
```bash
curl http://localhost:8001/api/v1/webhooks/azure/health
```

### 6. Prometheus Metrics
```bash
curl http://localhost:8001/metrics
```

---

## AWS EventBridge Tests

### Test 1: OrderPlaced Event
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "aws-order-001",
    "detail-type": "OrderPlaced",
    "source": "ecommerce.orders",
    "account": "123456789012",
    "time": "2025-11-20T08:00:00Z",
    "region": "us-east-1",
    "resources": [],
    "detail": {
      "order_id": "ORD-AWS-2025-001",
      "customer_id": "CUST-12345",
      "amount": 2999.99,
      "currency": "USD",
      "items": [
        {
          "sku": "MACBOOK-PRO-16",
          "quantity": 1,
          "price": 2999.99,
          "name": "MacBook Pro 16-inch"
        }
      ],
      "shipping_address": {
        "country": "US",
        "state": "CA",
        "city": "San Francisco"
      }
    }
  }'
```

### Test 2: PaymentProcessed Event
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "aws-payment-001",
    "detail-type": "PaymentProcessed",
    "source": "ecommerce.payments",
    "account": "123456789012",
    "time": "2025-11-20T08:01:00Z",
    "region": "us-east-1",
    "resources": [],
    "detail": {
      "order_id": "ORD-AWS-2025-001",
      "payment_id": "PAY-STRIPE-789",
      "amount": 2999.99,
      "currency": "USD",
      "status": "success",
      "payment_method": "credit_card",
      "card_last4": "4242"
    }
  }'
```

### Test 3: InventoryReserved Event
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "aws-inventory-001",
    "detail-type": "InventoryReserved",
    "source": "ecommerce.inventory",
    "account": "123456789012",
    "time": "2025-11-20T08:02:00Z",
    "region": "us-west-2",
    "resources": [],
    "detail": {
      "order_id": "ORD-AWS-2025-001",
      "warehouse": "WH-SF-01",
      "warehouse_location": "San Francisco",
      "items": [
        {
          "sku": "MACBOOK-PRO-16",
          "quantity": 1,
          "bin_location": "A-23-45"
        }
      ]
    }
  }'
```

### Test 4: SNS Subscription Confirmation (Simulated)
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "SubscriptionConfirmation",
    "MessageId": "msg-123",
    "TopicArn": "arn:aws:sns:us-east-1:123456789012:helios-events",
    "Message": "test",
    "Timestamp": "2025-11-20T08:00:00Z",
    "SignatureVersion": "1",
    "Signature": "test-signature",
    "SigningCertURL": "https://sns.amazonaws.com/cert.pem",
    "SubscribeURL": "https://sns.amazonaws.com/subscribe?token=test"
  }'
```

---

## GCP Pub/Sub Tests

### Test 1: OrderPlaced Event (Base64 Encoded)
```bash
# The payload {"order_id": "ORD-GCP-001", "customer_id": "CUST-789", "amount": 1599.99}
# is base64 encoded as: eyJvcmRlcl9pZCI6ICJPUkQtR0NQLTA0MiIsICJjdXN0b21lcl9pZCI6ICJDVVNULTU2NyIsICJhbW91bnQiOiAxNTk5Ljk5fQ==

curl -X POST http://localhost:8001/api/v1/webhooks/gcp/pubsub \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "eyJvcmRlcl9pZCI6ICJPUkQtR0NQLTA0MiIsICJjdXN0b21lcl9pZCI6ICJDVVNULTU2NyIsICJhbW91bnQiOiAxNTk5Ljk5fQ==",
      "attributes": {
        "eventType": "OrderPlaced",
        "source": "ecommerce"
      },
      "messageId": "gcp-msg-001",
      "publishTime": "2025-11-20T08:00:00Z"
    },
    "subscription": "projects/my-project-123/subscriptions/helios-events"
  }'
```

### Test 2: PaymentProcessed Event
```bash
# Payload: {"order_id": "ORD-GCP-042", "payment_id": "PAY-GCP-111", "amount": 1599.99}
# Base64: eyJvcmRlcl9pZCI6ICJPUkQtR0NQLTA0MiIsICJwYXltZW50X2lkIjogIlBBWS1HQ1AtMTExIiwgImFtb3VudCI6IDE1OTkuOTl9

curl -X POST http://localhost:8001/api/v1/webhooks/gcp/pubsub \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "eyJvcmRlcl9pZCI6ICJPUkQtR0NQLTA0MiIsICJwYXltZW50X2lkIjogIlBBWS1HQ1AtMTExIiwgImFtb3VudCI6IDE1OTkuOTl9",
      "attributes": {
        "eventType": "PaymentProcessed"
      },
      "messageId": "gcp-msg-002",
      "publishTime": "2025-11-20T08:01:00Z"
    },
    "subscription": "projects/my-project-123/subscriptions/helios-events"
  }'
```

### Helper: Generate Base64 for GCP
```bash
# To encode your own JSON payload:
echo -n '{"order_id": "YOUR-ORDER", "customer_id": "YOUR-CUSTOMER", "amount": 999.99}' | base64
```

---

## Azure Event Grid Tests

### Test 1: Single OrderPlaced Event
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/azure/eventgrid \
  -H "Content-Type: application/json" \
  -d '[{
    "id": "azure-event-001",
    "eventType": "Contoso.Orders.OrderPlaced",
    "subject": "orders/ORD-AZURE-555",
    "eventTime": "2025-11-20T08:00:00Z",
    "data": {
      "order_id": "ORD-AZURE-555",
      "customer_id": "CUST-AZURE-999",
      "amount": 899.99,
      "currency": "USD",
      "items": [
        {
          "sku": "SURFACE-PRO-9",
          "quantity": 1,
          "price": 899.99
        }
      ]
    },
    "dataVersion": "1.0",
    "metadataVersion": "1",
    "topic": "/subscriptions/sub-123/resourceGroups/rg-helios/providers/Microsoft.EventGrid/topics/orders"
  }]'
```

### Test 2: Batch Events (Multiple Events)
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/azure/eventgrid \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "azure-event-batch-001",
      "eventType": "Contoso.Orders.OrderPlaced",
      "subject": "orders/ORD-AZURE-777",
      "eventTime": "2025-11-20T08:00:00Z",
      "data": {
        "order_id": "ORD-AZURE-777",
        "customer_id": "CUST-BATCH-001",
        "amount": 499.99
      },
      "dataVersion": "1.0",
      "metadataVersion": "1"
    },
    {
      "id": "azure-event-batch-002",
      "eventType": "Contoso.Payments.PaymentProcessed",
      "subject": "payments/PAY-AZURE-888",
      "eventTime": "2025-11-20T08:01:00Z",
      "data": {
        "order_id": "ORD-AZURE-777",
        "payment_id": "PAY-AZURE-888",
        "amount": 499.99
      },
      "dataVersion": "1.0",
      "metadataVersion": "1"
    },
    {
      "id": "azure-event-batch-003",
      "eventType": "Contoso.Inventory.InventoryReserved",
      "subject": "inventory/WH-AZURE-01",
      "eventTime": "2025-11-20T08:02:00Z",
      "data": {
        "order_id": "ORD-AZURE-777",
        "warehouse": "WH-AZURE-01"
      },
      "dataVersion": "1.0",
      "metadataVersion": "1"
    }
  ]'
```

### Test 3: Subscription Validation
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/azure/eventgrid \
  -H "Content-Type: application/json" \
  -d '[{
    "id": "validation-001",
    "eventType": "Microsoft.EventGrid.SubscriptionValidationEvent",
    "subject": "",
    "eventTime": "2025-11-20T08:00:00Z",
    "data": {
      "validationCode": "ABC123-VALIDATION-CODE-XYZ789"
    },
    "dataVersion": "1.0",
    "metadataVersion": "1"
  }]'
```

---

## Direct Event Ingestion

### Test 1: Direct OrderPlaced
```bash
curl -X POST http://localhost:8001/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "OrderPlaced",
    "source": "aws",
    "payload": {
      "order_id": "ORD-DIRECT-999",
      "customer_id": "CUST-DIRECT-123",
      "amount": 1299.99,
      "items": [
        {
          "sku": "IPHONE-15-PRO",
          "quantity": 1,
          "price": 1299.99
        }
      ]
    },
    "metadata": {
      "region": "us-west-2",
      "environment": "production",
      "source_system": "api"
    }
  }'
```

### Test 2: Direct PaymentProcessed
```bash
curl -X POST http://localhost:8001/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "PaymentProcessed",
    "source": "gcp",
    "payload": {
      "order_id": "ORD-DIRECT-999",
      "payment_id": "PAY-DIRECT-456",
      "amount": 1299.99,
      "status": "success"
    },
    "metadata": {
      "processor": "stripe",
      "region": "us-central1"
    }
  }'
```

---

## Validation Tests

### Test 1: Missing customer_id (Should FAIL)
```bash
curl -X POST http://localhost:8001/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "OrderPlaced",
    "source": "aws",
    "payload": {
      "order_id": "ORD-INVALID-001",
      "amount": 999.99
    },
    "metadata": {}
  }'
```

**Expected Response:**
```json
{
  "detail": "Event validation failed: OrderPlaced event must contain customer_id"
}
```

### Test 2: Missing amount in Payment (Should FAIL)
```bash
curl -X POST http://localhost:8001/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "PaymentProcessed",
    "source": "gcp",
    "payload": {
      "order_id": "ORD-INVALID-002",
      "payment_id": "PAY-123"
    },
    "metadata": {}
  }'
```

**Expected Response:**
```json
{
  "detail": "Event validation failed: PaymentProcessed event must contain amount"
}
```

### Test 3: Invalid amount type (Should FAIL)
```bash
curl -X POST http://localhost:8001/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "PaymentProcessed",
    "source": "aws",
    "payload": {
      "order_id": "ORD-INVALID-003",
      "payment_id": "PAY-456",
      "amount": "not-a-number"
    },
    "metadata": {}
  }'
```

---

## Deduplication Tests

### Test 1: Send Same Event Twice
```bash
# First request (should succeed)
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "duplicate-test-001",
    "detail-type": "OrderPlaced",
    "source": "test",
    "account": "123",
    "time": "2025-11-20T08:00:00Z",
    "region": "us-east-1",
    "detail": {
      "order_id": "ORD-DEDUP-TEST",
      "customer_id": "CUST-DEDUP",
      "amount": 100
    }
  }'

# Second request with SAME ID (should be rejected as duplicate)
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "duplicate-test-001",
    "detail-type": "OrderPlaced",
    "source": "test",
    "account": "123",
    "time": "2025-11-20T08:00:00Z",
    "region": "us-east-1",
    "detail": {
      "order_id": "ORD-DEDUP-TEST",
      "customer_id": "CUST-DEDUP",
      "amount": 100
    }
  }'
```

**Expected Second Response:**
```json
{
  "status": "duplicate",
  "event_id": "duplicate-test-001",
  "message": "Event already processed"
}
```

---

## Database Queries

### Check All Events
```bash
psql -d helios -c "SELECT event_id, event_type, source, order_id, payload->>'amount' as amount FROM events ORDER BY ingested_at DESC LIMIT 10;"
```

### Statistics by Source
```bash
psql -d helios -c "SELECT source, COUNT(*) as total_events, COUNT(DISTINCT order_id) as unique_orders FROM events GROUP BY source ORDER BY source;"
```

### Events for Specific Order
```bash
psql -d helios -c "SELECT event_id, event_type, source, ingested_at FROM events WHERE order_id = 'ORD-AWS-2025-001' ORDER BY ingested_at;"
```

### Recent Events (Last Hour)
```bash
psql -d helios -c "SELECT event_id, event_type, source, order_id FROM events WHERE ingested_at > NOW() - INTERVAL '1 hour' ORDER BY ingested_at DESC;"
```

### Event Count by Type
```bash
psql -d helios -c "SELECT event_type, COUNT(*) FROM events GROUP BY event_type ORDER BY count DESC;"
```

---

## Redis Checks

### Check Deduplication Keys
```bash
redis-cli KEYS "event:dedup:*"
```

### Check Specific Event TTL
```bash
redis-cli TTL "event:dedup:aws-order-001"
```

### Count All Dedup Keys
```bash
redis-cli --scan --pattern "event:dedup:*" | wc -l
```

---

## Complete E2E Test Script

Save this as `test_complete_flow.sh`:

```bash
#!/bin/bash

echo "🚀 Helios Complete E2E Test"
echo "=============================="

ORDER_ID="ORD-E2E-$(date +%s)"

echo ""
echo "1️⃣  Sending OrderPlaced (AWS)..."
curl -s -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d "{
    \"version\": \"0\",
    \"id\": \"e2e-order-$(date +%s)\",
    \"detail-type\": \"OrderPlaced\",
    \"source\": \"test\",
    \"account\": \"123\",
    \"time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"region\": \"us-east-1\",
    \"detail\": {
      \"order_id\": \"$ORDER_ID\",
      \"customer_id\": \"CUST-E2E\",
      \"amount\": 999.99
    }
  }" | jq .

sleep 1

echo ""
echo "2️⃣  Sending PaymentProcessed (GCP)..."
PAYMENT_PAYLOAD=$(echo -n "{\"order_id\": \"$ORDER_ID\", \"payment_id\": \"PAY-E2E\", \"amount\": 999.99}" | base64)
curl -s -X POST http://localhost:8001/api/v1/webhooks/gcp/pubsub \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": {
      \"data\": \"$PAYMENT_PAYLOAD\",
      \"attributes\": {\"eventType\": \"PaymentProcessed\"},
      \"messageId\": \"e2e-payment-$(date +%s)\",
      \"publishTime\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
    },
    \"subscription\": \"projects/test/subscriptions/helios\"
  }" | jq .

sleep 1

echo ""
echo "3️⃣  Sending InventoryReserved (Azure)..."
curl -s -X POST http://localhost:8001/api/v1/webhooks/azure/eventgrid \
  -H "Content-Type: application/json" \
  -d "[{
    \"id\": \"e2e-inventory-$(date +%s)\",
    \"eventType\": \"InventoryReserved\",
    \"subject\": \"inventory/test\",
    \"eventTime\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"data\": {
      \"order_id\": \"$ORDER_ID\",
      \"warehouse\": \"WH-E2E\"
    },
    \"dataVersion\": \"1.0\"
  }]" | jq .

echo ""
echo "4️⃣  Checking database for order: $ORDER_ID"
psql -d helios -c "SELECT event_type, source, ingested_at FROM events WHERE order_id = '$ORDER_ID' ORDER BY ingested_at;"

echo ""
echo "✅ E2E Test Complete!"
```

Make it executable:
```bash
chmod +x test_complete_flow.sh
./test_complete_flow.sh
```

---

## Troubleshooting

### Server Not Responding
```bash
# Check if server is running
ps aux | grep uvicorn

# Check port
lsof -i :8001

# Restart server
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### Database Issues
```bash
# Check connection
psql -d helios -c "SELECT 1;"

# Check table exists
psql -d helios -c "\dt"
```

### Redis Issues
```bash
# Check Redis
redis-cli ping

# Clear all dedup keys (CAUTION!)
redis-cli FLUSHDB
```

---

## API Documentation

**Interactive Swagger UI:**
```
http://localhost:8001/docs
```

**ReDoc:**
```
http://localhost:8001/redoc
```

---

**Happy Testing! 🎉**
