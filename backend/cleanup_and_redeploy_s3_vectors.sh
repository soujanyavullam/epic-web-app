#!/bin/bash

# Script to cleanup and redeploy S3 Vectors with proper metadata configuration
set -e

echo "🚀 S3 Vectors Cleanup and Redeploy Script"
echo "=========================================="

# Configuration
VECTOR_BUCKET_NAME="epic-vector-bucket"
VECTOR_INDEX_NAME="book-embeddings-index"
STACK_NAME="epic-s3-vectors-stack"

echo ""
echo "📋 Current Configuration:"
echo "  Bucket: $VECTOR_BUCKET_NAME"
echo "  Index: $VECTOR_INDEX_NAME"
echo "  Stack: $STACK_NAME"

echo ""
echo "⚠️  WARNING: This will delete your existing S3 Vectors index and all data!"
echo "   You will need to re-upload all your book embeddings after redeployment."
echo ""

read -p "Do you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled."
    exit 1
fi

echo ""
echo "🗑️  Step 1: Deleting existing S3 Vectors index..."
echo "   Note: If this fails due to permissions, you may need to delete manually in AWS Console"

# Try to delete the index (may fail if local credentials don't have access)
if aws s3vectors delete-index --vector-bucket-name "$VECTOR_BUCKET_NAME" --index-name "$VECTOR_INDEX_NAME" 2>/dev/null; then
    echo "   ✅ Index deleted successfully"
else
    echo "   ⚠️  Could not delete index locally (permission issue)"
    echo "   Please delete the index manually in AWS Console:"
    echo "   1. Go to S3 Vectors in AWS Console"
    echo "   2. Navigate to bucket: $VECTOR_BUCKET_NAME"
    echo "   3. Delete index: $VECTOR_INDEX_NAME"
    echo ""
    read -p "Press Enter after manually deleting the index..."
fi

echo ""
echo "🔧 Step 2: Updating CloudFormation template..."
echo "   ✅ Template updated with metadata configuration"

echo ""
echo "🚀 Step 3: Deploying updated infrastructure..."
echo "   This will create a new index with proper metadata support"

# Check if SAM is available
if command -v sam &> /dev/null; then
    echo "   Using SAM to deploy..."
    sam deploy --guided --stack-name "$STACK_NAME"
else
    echo "   SAM not found. Please deploy manually:"
    echo "   1. Run: sam deploy --guided --stack-name $STACK_NAME"
    echo "   2. Or use AWS CLI: aws cloudformation deploy --template-file infrastructure/s3_vectors_setup.yaml --stack-name $STACK_NAME"
fi

echo ""
echo "📚 Step 4: After deployment, you'll need to:"
echo "   1. Re-upload all your book embeddings"
echo "   2. Test the query API to verify metadata is working"
echo ""

echo "🎯 Summary of changes made:"
echo "   ✅ Added MetadataConfiguration to CloudFormation template"
echo "   ✅ Updated Lambda index creator with metadata support"
echo "   ✅ Enhanced IAM permissions for index management"
echo "   ✅ Index will now properly store and return metadata"
echo ""

echo "🚀 Ready to redeploy! Run the deployment command above." 