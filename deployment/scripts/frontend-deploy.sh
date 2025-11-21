#!/bin/bash

# Frontend Deployment Script for Epic Web App
# This script builds and deploys the frontend to S3 and invalidates CloudFront cache

set -e

echo "🚀 Deploying Epic Web App Frontend"
echo "==================================="

# Configuration
S3_BUCKET="epic-web-app-static"
CLOUDFRONT_DISTRIBUTION_ID="ECREN1Z6RL4JJ"
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

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo -e "${YELLOW}📦 Building frontend...${NC}"
    npm run build
fi

# Check if build was successful
if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Build failed. dist directory not found.${NC}"
    exit 1
fi

echo -e "${YELLOW}📤 Uploading to S3 bucket: ${S3_BUCKET}${NC}"

# Sync dist folder to S3 bucket
aws s3 sync dist/ s3://${S3_BUCKET}/ \
    --delete \
    --cache-control "max-age=31536000,public" \
    --exclude "*.html" \
    --exclude "*.js" \
    --exclude "*.css"

# Upload HTML, JS, and CSS files with no-cache headers
echo -e "${YELLOW}📤 Uploading HTML, JS, and CSS files...${NC}"
aws s3 cp dist/index.html s3://${S3_BUCKET}/ \
    --cache-control "no-cache,no-store,must-revalidate" \
    --content-type "text/html"

# Upload JS and CSS files with no-cache headers
aws s3 cp dist/assets/ s3://${S3_BUCKET}/assets/ \
    --recursive \
    --cache-control "no-cache,no-store,must-revalidate"

echo -e "${GREEN}✅ Frontend uploaded to S3 successfully!${NC}"

# Invalidate CloudFront cache
echo -e "${YELLOW}🔄 Invalidating CloudFront cache...${NC}"
aws cloudfront create-invalidation \
    --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} \
    --paths "/*"

echo -e "${GREEN}✅ CloudFront cache invalidation initiated!${NC}"

# Get CloudFront domain
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id ${CLOUDFRONT_DISTRIBUTION_ID} --query 'Distribution.DomainName' --output text)

echo -e "\n${GREEN}🎉 Frontend deployment completed successfully!${NC}"
echo -e "\n${YELLOW}📱 Your app is now available at:${NC}"
echo -e "${GREEN}https://${CLOUDFRONT_DOMAIN}${NC}"
echo -e "\n${YELLOW}⏱️  Note: CloudFront cache invalidation may take 5-10 minutes to complete.${NC}"
echo -e "${YELLOW}   You may need to wait a few minutes for the latest changes to appear.${NC}" 