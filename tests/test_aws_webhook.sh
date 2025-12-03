#!/bin/bash

# Test AWS EventBridge webhook adapter
echo "Testing AWS EventBridge webhook..."

# Test 1: Direct EventBridge event (without SNS wrapper)
echo -e "\n1. Testing direct EventBridge event (OrderPlaced)..."
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "aws-event-001",
    "detail-type": "OrderPlaced",
    "source": "ecommerce.orders",
    "account": "123456789012",
    "time": "2025-11-18T20:30:00Z",
    "region": "us-east-1",
    "resources": [],
    "detail": {
      "order_id": "ORD-AWS-001",
      "customer_id": "CUST-AWS-123",
      "amount": 2999.99,
      "items": [
        {"sku": "MACBOOK-PRO", "quantity": 1, "price": 2999.99}
      ]
    }
  }' | jq .

# Test 2: PaymentProcessed event
echo -e "\n2. Testing PaymentProcessed event from AWS..."
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "aws-event-002",
    "detail-type": "PaymentProcessed",
    "source": "ecommerce.payments",
    "account": "123456789012",
    "time": "2025-11-18T20:31:00Z",
    "region": "us-east-1",
    "resources": [],
    "detail": {
      "order_id": "ORD-AWS-001",
      "payment_id": "PAY-AWS-999",
      "amount": 2999.99,
      "status": "success",
      "payment_method": "credit_card"
    }
  }' | jq .

# Test 3: InventoryReserved event
echo -e "\n3. Testing InventoryReserved event from AWS..."
curl -X POST http://localhost:8001/api/v1/webhooks/aws/eventbridge \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0",
    "id": "aws-event-003",
    "detail-type": "InventoryReserved",
    "source": "ecommerce.inventory",
    "account": "123456789012",
    "time": "2025-11-18T20:32:00Z",
    "region": "us-west-2",
    "resources": [],
    "detail": {
      "order_id": "ORD-AWS-001",
      "warehouse": "WH-AWS-WEST",
      "items": [
        {"sku": "MACBOOK-PRO", "quantity": 1}
      ]
    }
  }' | jq .

echo -e "\n✅ AWS EventBridge tests completed!"
