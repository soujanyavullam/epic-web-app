#!/bin/bash

# Fix CORS for all OPTIONS methods in API Gateway
# This script updates all OPTIONS methods to properly return CORS headers

set -e

echo "🔧 Fixing CORS for all OPTIONS methods in API Gateway"
echo "======================================================"

# Configuration
API_ID="0108izew87"
REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${YELLOW}📡 API Gateway ID: $API_ID${NC}"
echo -e "${YELLOW}🌍 Region: $REGION${NC}"

# Function to fix OPTIONS method for a resource
fix_options_method() {
    local resource_id=$1
    local resource_path=$2
    
    echo -e "\n${YELLOW}🔧 Fixing OPTIONS method for $resource_path${NC}"
    
    # Update the method response to include CORS headers
    aws apigateway update-method-response \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --patch-operations file://patch-operations.json
    
    echo -e "${GREEN}✅ Method response updated for $resource_path${NC}"
    
    # Update the integration response to include proper CORS headers
    aws apigateway update-integration-response \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --patch-operations file://integration-patch.json
    
    echo -e "${GREEN}✅ Integration response updated for $resource_path${NC}"
}

# Fix all resources with OPTIONS methods
echo -e "\n${YELLOW}🔍 Fixing CORS for all resources...${NC}"

# /query endpoint
fix_options_method "jyf5nx" "/query"

# /upload endpoint  
fix_options_method "e3ep12" "/upload"

# /repo endpoint
fix_options_method "guwvqc" "/repo"

# /query/books endpoint
fix_options_method "pkwbia" "/query/books"

# Deploy the API to make changes take effect
echo -e "\n${YELLOW}🚀 Deploying API Gateway changes...${NC}"

# Create a deployment
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name dev \
    --description "CORS OPTIONS methods fix" \
    --query 'id' --output text)

echo -e "${GREEN}✅ Deployment created: $DEPLOYMENT_ID${NC}"

echo -e "\n${GREEN}🎉 CORS OPTIONS methods fixed successfully!${NC}"
echo -e "${YELLOW}📡 API Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/dev${NC}"
echo -e "${YELLOW}⏱️  Changes should be active within 1-2 minutes${NC}"
echo -e "\n${YELLOW}📋 Test CORS with:${NC}"
echo -e "curl -X OPTIONS https://$API_ID.execute-api.$REGION.amazonaws.com/dev/query \\"
echo -e "  -H 'Origin: https://dppwj92zt14xp.cloudfront.net' \\"
echo -e "  -H 'Access-Control-Request-Method: POST' \\"
echo -e "  -H 'Access-Control-Request-Headers: Content-Type'" 