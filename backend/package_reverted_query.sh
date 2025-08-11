#!/bin/bash

# Package the reverted query handler for deployment
# This script creates a deployment package with the working query handler code

set -e

echo "📦 Packaging reverted query handler for deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create temporary directory for packaging
PACKAGE_DIR="lambda_package_reverted_$(date +%Y%m%d_%H%M%S)"
echo -e "\n${YELLOW}Creating package directory: $PACKAGE_DIR${NC}"

mkdir -p "$PACKAGE_DIR"

# Copy the reverted query handler
echo -e "\n${YELLOW}Copying reverted query handler...${NC}"
cp "src/lambda/query_handler.py" "$PACKAGE_DIR/"

# Copy dependencies from the working package
echo -e "\n${YELLOW}Copying dependencies from working package...${NC}"
if [ -f "lambda_package_repo_generator_enhanced.zip" ]; then
    echo "Extracting dependencies from working package..."
    unzip -q "lambda_package_repo_generator_enhanced.zip" -d "$PACKAGE_DIR"
    
    # Remove the old query handler and replace with reverted one
    rm -f "$PACKAGE_DIR/query_handler.py"
    cp "src/lambda/query_handler.py" "$PACKAGE_DIR/"
    
    echo -e "${GREEN}✅ Dependencies copied successfully${NC}"
else
    echo -e "${RED}❌ Working package not found${NC}"
    exit 1
fi

# Create the deployment zip
ZIP_NAME="lambda_package_query_reverted.zip"
echo -e "\n${YELLOW}Creating deployment package: $ZIP_NAME${NC}"

cd "$PACKAGE_DIR"
zip -r "../$ZIP_NAME" . -q
cd ..

# Clean up
echo -e "\n${YELLOW}Cleaning up temporary files...${NC}"
rm -rf "$PACKAGE_DIR"

# Verify the package
if [ -f "$ZIP_NAME" ]; then
    PACKAGE_SIZE=$(du -h "$ZIP_NAME" | cut -f1)
    echo -e "\n${GREEN}✅ Successfully created deployment package!${NC}"
    echo "Package: $ZIP_NAME"
    echo "Size: $PACKAGE_SIZE"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Deploy using: aws lambda update-function-code --function-name epic-query-function --zip-file fileb://$ZIP_NAME"
    echo "2. Or use the deploy script: ./deploy_lambda_updates.sh"
else
    echo -e "\n${RED}❌ Failed to create deployment package${NC}"
    exit 1
fi 