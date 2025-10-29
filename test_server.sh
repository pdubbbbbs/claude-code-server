#!/bin/bash

echo "======================================"
echo "Claude Code Server - Test Script"
echo "======================================"
echo ""

# Set your API key here or export it before running
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set!"
    echo "Please set it:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo "  or edit this script"
    exit 1
fi

BASE_URL="http://localhost:8002"

echo "1. Testing root endpoint..."
curl -s $BASE_URL/ | jq .
echo ""

echo "2. Testing health endpoint..."
curl -s $BASE_URL/health | jq .
echo ""

echo "3. Testing /execute endpoint..."
curl -s -X POST $BASE_URL/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from Claude!\")\nprint(2 + 2)",
    "language": "python",
    "stream": false
  }' | jq .
echo ""

echo "4. Testing /chat endpoint..."
curl -s -X POST $BASE_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is FastAPI?",
    "stream": false
  }' | jq -r '.response' | head -n 10
echo "..."
echo ""

echo "5. Testing /analyze endpoint..."
curl -s -X POST $BASE_URL/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(x, y):\n    return x + y",
    "language": "python",
    "stream": false
  }' | jq -r '.analysis' | head -n 10
echo "..."
echo ""

echo "6. Testing metrics endpoint..."
curl -s $BASE_URL/metrics | grep -E "^(http_requests_total|claude_api_calls_total|claude_tokens_total)" | head -n 5
echo ""

echo "======================================"
echo "✅ Tests complete!"
echo "======================================"
