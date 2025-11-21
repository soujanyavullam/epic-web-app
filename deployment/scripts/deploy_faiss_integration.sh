#!/bin/bash
# deploy_faiss_integration.sh
# Script to deploy FAISS integration to Lambda function

set -e

FUNCTION_NAME="epic-query-function"
REGION="us-east-1"
ACCOUNT_ID="317476927840"

echo "🚀 Deploying FAISS integration..."

# Check if FAISS layer exists, if not create it
if [ ! -f "faiss-layer.zip" ]; then
    echo "📦 FAISS layer not found. Creating it first..."
    chmod +x create_faiss_layer.sh
    ./create_faiss_layer.sh
fi

# Create Lambda layer
echo "🔧 Creating Lambda layer..."
LAYER_ARN=$(aws lambda publish-layer-version \
    --layer-name faiss-layer \
    --description "FAISS for vector search optimization" \
    --zip-file fileb://faiss-layer.zip \
    --compatible-runtimes python3.9 python3.10 python3.11 \
    --query 'LayerVersionArn' \
    --output text)

echo "✅ Layer created: $LAYER_ARN"

# Update function configuration
echo "⚙️  Updating function configuration..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --layers $LAYER_ARN \
    --memory-size 1024 \
    --timeout 60

# Set environment variables
echo "🔑 Setting environment variables..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables='{
        "FAISS_INDEX_CACHE_TTL":"3600",
        "FAISS_INDEX_REBUILD_THRESHOLD":"100"
    }'

# Update function code
echo "📝 Updating function code..."
cd src
zip -r lambda-code.zip .

aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://lambda-code.zip

cd ..

echo "🎉 FAISS integration deployed successfully!"
echo ""
echo "📊 Performance improvements expected:"
echo "   • Code Search: 1-2.5s → 0.5-1s (2-3x faster)"
echo "   • Large Books: 8-9s → 2-4s (2-5x faster)"
echo "   • Overall Average: 6s → 1.5-3s (2-4x faster)"
echo ""
echo "🔍 Monitor CloudWatch logs for FAISS performance metrics" 