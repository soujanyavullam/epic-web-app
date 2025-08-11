#!/bin/bash

# Deploy S3 Vectors Lambda Functions (New Functions)
# This script creates NEW Lambda functions for S3 Vectors testing

set -e

echo "🚀 Deploying S3 Vectors Lambda Functions (New Functions)"
echo "========================================================"

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

# Configuration
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::317476927840:role/epic-s3-vectors-role"  # Using new S3 Vectors role

# Function to create new Lambda function
create_lambda() {
    local function_name=$1
    local zip_file=$2
    local handler=$3
    local description=$4
    
    echo -e "\n${YELLOW}Creating $function_name...${NC}"
    
    # Check if function already exists
    if aws lambda get-function --function-name "$function_name" &> /dev/null; then
        echo -e "${YELLOW}Function $function_name already exists. Updating...${NC}"
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file "fileb://$zip_file"
    else
        echo -e "${YELLOW}Creating new function $function_name...${NC}"
        aws lambda create-function \
            --function-name "$function_name" \
            --runtime python3.9 \
            --role "$ROLE_ARN" \
            --handler "$handler" \
            --zip-file "fileb://$zip_file" \
            --timeout 300 \
            --memory-size 512 \
            --description "$description"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Successfully deployed $function_name${NC}"
    else
        echo -e "${RED}❌ Failed to deploy $function_name${NC}"
        return 1
    fi
}

# Create deployment packages
echo "📦 Creating S3 Vectors deployment packages..."

cd lambda_minimal

# Create package for S3 Vectors Query Function
echo "Creating S3 Vectors Query package..."
zip -r ../s3_vectors_query_package.zip query_handler_s3_vectors.py s3_vectors_search.py boto3/ botocore/ requests/ urllib3/ certifi/ charset_normalizer/ idna/ jmespath/ python_dateutil/ s3transfer/ six.py jwt/ dotenv/ tqdm/ chardet/ regex/ tiktoken/

# Create package for S3 Vectors Upload Function
echo "Creating S3 Vectors Upload package..."
zip -r ../s3_vectors_upload_package.zip upload_handler_s3_vectors.py s3_vectors_search.py boto3/ botocore/ requests/ urllib3/ certifi/ charset_normalizer/ idna/ jmespath/ python_dateutil/ s3transfer/ six.py jwt/ dotenv/ tqdm/ chardet/ regex/ tiktoken/

# Create package for S3 Vectors Search Function
echo "Creating S3 Vectors Search package..."
zip -r ../s3_vectors_search_package.zip s3_vectors_search.py boto3/ botocore/ requests/ urllib3/ certifi/ charset_normalizer/ idna/ jmespath/ python_dateutil/ s3transfer/ six.py jwt/ dotenv/ tqdm/ chardet/ regex/ tiktoken/

cd ..

# Deploy new Lambda functions
echo -e "\n${YELLOW}Deploying new S3 Vectors Lambda functions...${NC}"

# 1. S3 Vectors Query Function
create_lambda \
    "epic-query-s3-vectors" \
    "s3_vectors_query_package.zip" \
    "query_handler_s3_vectors.lambda_handler" \
    "Query function using S3 Vectors for vector search"

# 2. S3 Vectors Upload Function
create_lambda \
    "epic-upload-s3-vectors" \
    "s3_vectors_upload_package.zip" \
    "upload_handler_s3_vectors.lambda_handler" \
    "Upload function using S3 Vectors for embedding storage"

# 3. S3 Vectors Search Function
create_lambda \
    "epic-s3-vectors-search" \
    "s3_vectors_search_package.zip" \
    "s3_vectors_search.lambda_handler" \
    "Dedicated S3 Vectors search function"

echo -e "\n${GREEN}✅ S3 Vectors Lambda functions deployed successfully!${NC}"

# Clean up packages
echo "🧹 Cleaning up deployment packages..."
rm -f s3_vectors_*_package.zip

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Set up S3 Vector bucket and index"
echo "2. Update IAM roles with S3 Vectors permissions"
echo "3. Create API Gateway endpoints for new functions"
echo "4. Test the new functions"
echo "5. Compare performance with current functions" 