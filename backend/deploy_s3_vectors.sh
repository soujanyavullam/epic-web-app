#!/bin/bash

# 🚀 Deploy S3 Vectors Implementation
# This script packages and deploys the updated S3 vectors lambda functions

set -e

echo "🚀 Deploying S3 Vectors Implementation"
echo "======================================"

# Configuration - Updated to use existing function names
PACKAGE_DIR="lambda_package_s3_vectors"
LAMBDA_FUNCTION_UPLOAD="epic-upload-s3-vectors"
LAMBDA_FUNCTION_QUERY="epic-query-s3-vectors"
LAMBDA_FUNCTION_SEARCH="epic-s3-vectors-search"

# Clean up previous package
echo "🧹 Cleaning up previous package..."
rm -rf "$PACKAGE_DIR"
rm -f "${PACKAGE_DIR}.zip"

# Create package directory
echo "📦 Creating package directory..."
mkdir -p "$PACKAGE_DIR"

# Copy lambda functions with CORRECT filenames
echo "📋 Copying lambda functions..."
cp lambda_minimal/upload_handler_s3_vectors.py "$PACKAGE_DIR/upload_handler_s3_vectors.py"
cp lambda_minimal/query_handler_s3_vectors.py "$PACKAGE_DIR/query_handler_s3_vectors.py"
cp lambda_minimal/list_books_s3_vectors.py "$PACKAGE_DIR/s3_vectors_search.py"

# Copy dependencies from working package
echo "📚 Copying dependencies..."
cp -r package/* "$PACKAGE_DIR/"

# Create package
echo "📦 Creating deployment package..."
cd "$PACKAGE_DIR"
zip -r "../${PACKAGE_DIR}.zip" .
cd ..

echo "✅ Package created: ${PACKAGE_DIR}.zip"

# Deploy to Lambda functions
echo "🚀 Deploying to Lambda functions..."

# Deploy upload function
echo "📤 Deploying upload function..."
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_UPLOAD" \
    --zip-file "fileb://${PACKAGE_DIR}.zip" \
    --region us-east-1

# Deploy query function
echo "🔍 Deploying query function..."
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_QUERY" \
    --zip-file "fileb://${PACKAGE_DIR}.zip" \
    --region us-east-1

# Deploy search function (this will be our list books handler)
echo "🔍 Deploying search function..."
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_SEARCH" \
    --zip-file "fileb://${PACKAGE_DIR}.zip" \
    --region us-east-1

echo "✅ S3 Vectors implementation deployed successfully!"
echo ""
echo "📋 Deployed Functions:"
echo "  - Upload: $LAMBDA_FUNCTION_UPLOAD"
echo "  - Query: $LAMBDA_FUNCTION_QUERY"
echo "  - Search: $LAMBDA_FUNCTION_SEARCH"
echo ""
echo "🎯 Features:"
echo "  ✅ S3 Vectors integration"
echo "  ✅ Base64 content handling"
echo "  ✅ Proper field names (file_content)"
echo "  ✅ Complete CORS support"
echo "  ✅ Error handling and logging"
echo "  ✅ Async processing for large files"
echo "  ✅ Fallback to S3 bucket for listing"
echo ""
echo "🧪 Test the implementation:"
echo "  - Upload: Test with frontend upload"
echo "  - Query: Test Q&A functionality"
echo "  - Search: Test book listing functionality" 