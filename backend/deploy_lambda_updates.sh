#!/bin/bash

# Deploy Lambda Function Updates
# This script updates the Lambda functions with new CORS restrictions

set -e

echo "🚀 Deploying Lambda Function Updates"
echo "===================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to deploy Lambda function
deploy_lambda() {
    local function_name=$1
    local zip_file=$2
    local handler=$3
    
    echo -e "\n${YELLOW}Deploying $function_name...${NC}"
    
    if [ -f "$zip_file" ]; then
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file "fileb://$zip_file"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Successfully deployed $function_name${NC}"
        else
            echo -e "${RED}❌ Failed to deploy $function_name${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Zip file not found: $zip_file${NC}"
        return 1
    fi
}

# Check which Lambda packages exist
echo "📦 Checking available Lambda packages..."

QUERY_PACKAGE=""
UPLOAD_PACKAGE=""
REPO_PACKAGE=""

# Find the most recent packages
if [ -f "lambda_package_query_fixed.zip" ]; then
    QUERY_PACKAGE="lambda_package_query_fixed.zip"
elif [ -f "lambda_package_final.zip" ]; then
    QUERY_PACKAGE="lambda_package_final.zip"
elif [ -f "lambda_package_clean.zip" ]; then
    QUERY_PACKAGE="lambda_package_clean.zip"
fi

if [ -f "lambda_package_upload_enhanced.zip" ]; then
    UPLOAD_PACKAGE="lambda_package_upload_enhanced.zip"
elif [ -f "lambda_package_upload_fixed.zip" ]; then
    UPLOAD_PACKAGE="lambda_package_upload_fixed.zip"
elif [ -f "lambda_package_upload_simple.zip" ]; then
    UPLOAD_PACKAGE="lambda_package_upload_simple.zip"
fi

if [ -f "lambda_package_repo_generator_enhanced.zip" ]; then
    REPO_PACKAGE="lambda_package_repo_generator_enhanced.zip"
elif [ -f "lambda_package_repo_generator.zip" ]; then
    REPO_PACKAGE="lambda_package_repo_generator.zip"
fi

echo "Found packages:"
echo "  Query: $QUERY_PACKAGE"
echo "  Upload: $UPLOAD_PACKAGE"
echo "  Repo: $REPO_PACKAGE"

# Deploy Lambda functions
if [ -n "$QUERY_PACKAGE" ]; then
    deploy_lambda "epic-query-function" "$QUERY_PACKAGE" "query_handler.lambda_handler"
else
    echo -e "${RED}❌ No query function package found${NC}"
fi

if [ -n "$UPLOAD_PACKAGE" ]; then
    deploy_lambda "epic-upload-function" "$UPLOAD_PACKAGE" "upload_handler.lambda_handler"
else
    echo -e "${RED}❌ No upload function package found${NC}"
fi

if [ -n "$REPO_PACKAGE" ]; then
    deploy_lambda "epic-repo-generator" "$REPO_PACKAGE" "repo_documentation_generator.lambda_handler"
else
    echo -e "${RED}❌ No repo generator package found${NC}"
fi

echo -e "\n${GREEN}✅ Lambda deployment completed!${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Test the API endpoints"
echo "2. Run: ./test_security.sh"
echo "3. Deploy security measures if needed: ./deploy_secure_api.sh" 