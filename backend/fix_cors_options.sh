#!/bin/bash

# Fix CORS OPTIONS methods in API Gateway
# This script updates the OPTIONS methods to properly return CORS headers

set -e

echo "🔧 Fixing CORS OPTIONS methods in API Gateway"
echo "=============================================="

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
    local http_method=$3
    
    echo -e "\n${YELLOW}🔧 Fixing OPTIONS method for $resource_path${NC}"
    
    # Update the method response to include CORS headers
    aws apigateway update-method-response \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Origin": true,
            "method.response.header.Access-Control-Allow-Headers": true,
            "method.response.header.Access-Control-Allow-Methods": true,
            "method.response.header.Access-Control-Max-Age": true,
            "method.response.header.Access-Control-Allow-Credentials": true
        }' \
        --response-models '{"application/json": "Empty"}'
    
    echo -e "${GREEN}✅ Method response updated for $resource_path${NC}"
    
    # Update the integration response to include proper CORS headers
    aws apigateway update-integration-response \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Origin": "'\''*'\''",
            "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With'\''",
            "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,PUT,DELETE,OPTIONS'\''",
            "method.response.header.Access-Control-Max-Age": "'\''86400'\''",
            "method.response.header.Access-Control-Allow-Credentials": "'\''true'\''"
        }'
    
    echo -e "${GREEN}✅ Integration response updated for $resource_path${NC}"
}

# Get all resources and fix their OPTIONS methods
echo -e "\n${YELLOW}🔍 Finding resources with OPTIONS methods...${NC}"

RESOURCES=$(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?resourceMethods.OPTIONS].{Id:id,Path:path}' --output json)

echo "$RESOURCES" | jq -r '.[] | "\(.Id) \(.Path)"' | while read resource_id resource_path; do
    if [ ! -z "$resource_id" ] && [ ! -z "$resource_path" ]; then
        fix_options_method "$resource_id" "$resource_path" "OPTIONS"
    fi
done

# Deploy the API to make changes take effect
echo -e "\n${YELLOW}🚀 Deploying API Gateway changes...${NC}"

# Get the current stage name
STAGE_NAME=$(aws apigateway get-stages --rest-api-id $API_ID --query 'item[0].stageName' --output text)

if [ "$STAGE_NAME" == "None" ] || [ -z "$STAGE_NAME" ]; then
    STAGE_NAME="dev"
fi

echo -e "${YELLOW}📋 Deploying to stage: $STAGE_NAME${NC}"

# Create a deployment
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --description "CORS OPTIONS methods fix" \
    --query 'id' --output text)

echo -e "${GREEN}✅ Deployment created: $DEPLOYMENT_ID${NC}"

# Get the API endpoint
API_ENDPOINT=$(aws apigateway get-rest-api --rest-api-id $API_ID --query 'endpointConfiguration.urls[0]' --output text)

echo -e "\n${GREEN}🎉 CORS OPTIONS methods fixed successfully!${NC}"
echo -e "${YELLOW}📡 API Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME${NC}"
echo -e "${YELLOW}⏱️  Changes should be active within 1-2 minutes${NC}"
echo -e "\n${YELLOW}📋 Test CORS with:${NC}"
echo -e "curl -X OPTIONS https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME/query \\"
echo -e "  -H 'Origin: https://dppwj92zt14xp.cloudfront.net' \\"
echo -e "  -H 'Access-Control-Request-Method: POST' \\"
echo -e "  -H 'Access-Control-Request-Headers: Content-Type'" 