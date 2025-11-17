#!/bin/bash

# Setup S3 Vectors Infrastructure
# This script creates the necessary S3 Vectors bucket and index for the epic library

set -e

echo "🚀 Setting up S3 Vectors infrastructure..."

# Configuration
VECTOR_BUCKET_NAME="epic-vector-bucket"
INDEX_NAME="book-embeddings-index"
REGION="us-east-1"

echo "📦 Creating S3 Vectors bucket: $VECTOR_BUCKET_NAME"
if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket \
        --bucket "$VECTOR_BUCKET_NAME" \
        --region "$REGION" \
        || echo "Bucket already exists or error occurred"
else
    aws s3api create-bucket \
        --bucket "$VECTOR_BUCKET_NAME" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION" \
        || echo "Bucket already exists or error occurred"
fi

echo "🔍 Creating S3 Vectors index: $INDEX_NAME"
aws s3vectors create-index \
    --index-name "$INDEX_NAME" \
    --vector-bucket-name "$VECTOR_BUCKET_NAME" \
    --region "$REGION" \
    --data-type "float32" \
    --dimension 1536 \
    --distance-metric "cosine" \
    || echo "Index already exists or error occurred"

echo "✅ S3 Vectors infrastructure setup complete!"
echo ""
echo "📋 Created resources:"
echo "  - Bucket: $VECTOR_BUCKET_NAME"
echo "  - Index: $INDEX_NAME"
echo "  - Region: $REGION"
echo ""
echo "🧪 Test the setup:"
echo "  - List indexes: aws s3vectors list-indexes --bucket-name $VECTOR_BUCKET_NAME"
echo "  - List buckets: aws s3vectors list-buckets" 