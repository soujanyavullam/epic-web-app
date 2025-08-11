#!/bin/bash

# Security Test Script for Book Q&A API
# This script tests different security configurations

set -e

echo "🔒 Security Test Script"
echo "======================"

API_ENDPOINT="https://0108izew87.execute-api.us-east-1.amazonaws.com/dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local method=$2
    local data=$3
    local headers=$4
    local expected_status=$5
    local test_name=$6

    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    echo "Endpoint: $endpoint"
    echo "Method: $method"
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_ENDPOINT$endpoint" \
            -H "Content-Type: application/json" \
            $headers \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X GET "$API_ENDPOINT$endpoint" \
            -H "Content-Type: application/json" \
            $headers)
    fi

    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract response body (all lines except last)
    response_body=$(echo "$response" | head -n -1)

    echo "Status Code: $status_code"
    echo "Response: $response_body"

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS: Expected status $expected_status, got $status_code${NC}"
    else
        echo -e "${RED}❌ FAIL: Expected status $expected_status, got $status_code${NC}"
    fi
}

echo "🧪 Testing Current Security Status"
echo "================================="

# Test 1: Query endpoint without authentication
echo -e "\n${YELLOW}Test 1: Query endpoint without authentication${NC}"
test_endpoint "/query" "POST" '{"question":"test","book_title":"test"}' "" "200" "Public Access (Current)"

# Test 2: Books endpoint without authentication
echo -e "\n${YELLOW}Test 2: Books endpoint without authentication${NC}"
test_endpoint "/books" "GET" "" "" "200" "Public Access (Current)"

# Test 3: Upload endpoint without authentication
echo -e "\n${YELLOW}Test 3: Upload endpoint without authentication${NC}"
test_endpoint "/upload" "POST" '{"filename":"test.txt","content":"dGVzdA=="}' "" "200" "Public Access (Current)"

# Test 4: Repo endpoint without authentication
echo -e "\n${YELLOW}Test 4: Repo endpoint without authentication${NC}"
test_endpoint "/repo" "POST" '{"github_url":"https://github.com/test/test"}' "" "200" "Public Access (Current)"

echo -e "\n${YELLOW}Security Assessment:${NC}"
echo "================================="

# Check if endpoints are publicly accessible
if curl -s -o /dev/null -w "%{http_code}" "$API_ENDPOINT/query" | grep -q "200"; then
    echo -e "${RED}⚠️  WARNING: API endpoints are publicly accessible!${NC}"
    echo -e "${RED}   Anyone can access your API without authentication.${NC}"
    echo -e "${YELLOW}   Recommendation: Implement security measures.${NC}"
else
    echo -e "${GREEN}✅ GOOD: API endpoints are protected.${NC}"
fi

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "============="
echo "1. Run: ./deploy_secure_api.sh"
echo "2. Choose security level (1-4)"
echo "3. Update frontend with authentication headers"
echo "4. Test again with this script"

echo -e "\n${GREEN}Security test completed!${NC}" 