#!/bin/bash
# create_faiss_layer.sh
# Script to create FAISS Lambda layer for vector search optimization

set -e

echo "🚀 Creating FAISS Lambda layer..."

# Create directory structure
mkdir -p faiss-layer/python
cd faiss-layer/python

# Install FAISS with specific versions for Lambda compatibility
echo "📦 Installing FAISS and dependencies..."
pip3 install faiss-cpu numpy -t .

# Clean up to reduce layer size
echo "🧹 Cleaning up package..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.so" ! -name "*faiss*" -delete

# Check final size
LAYER_SIZE=$(du -sh . | cut -f1)
echo "📏 Layer size: $LAYER_SIZE"

if [[ $(echo $LAYER_SIZE | sed 's/[^0-9]//g') -gt 200 ]]; then
    echo "⚠️  WARNING: Layer size is large ($LAYER_SIZE). Lambda limit is 250MB."
    echo "💡 Consider using faiss-cpu instead of faiss-gpu for smaller size."
fi

cd ..
zip -r faiss-layer.zip python/

echo "✅ FAISS layer created: faiss-layer.zip"
echo "📏 Size: $(du -sh faiss-layer.zip | cut -f1)"
echo ""
echo "🔧 Next steps:"
echo "1. Deploy the layer: aws lambda publish-layer-version --layer-name faiss-layer --zip-file fileb://faiss-layer.zip"
echo "2. Attach to function: aws lambda update-function-configuration --function-name epic-query-function --layers <LAYER_ARN>"
echo "3. Increase memory: aws lambda update-function-configuration --function-name epic-query-function --memory-size 1024" 