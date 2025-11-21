#!/bin/bash

# Deploy Logout Handler Lambda Function
echo "🚀 Deploying Logout Handler Lambda Function..."

# Set variables
LAMBDA_FUNCTION_NAME="epic-logout-function"
LAMBDA_HANDLER="logout_handler.lambda_handler"
RUNTIME="python3.9"
ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role"  # Update with your role ARN

# Create deployment package
echo "📦 Creating deployment package..."
cd lambda_minimal

# Create a temporary directory for the package
rm -rf logout_package
mkdir logout_package

# Copy the logout handler
cp logout_handler.py logout_package/

# Copy required dependencies
cp -r jwt/ logout_package/
cp -r requests/ logout_package/
cp -r urllib3/ logout_package/
cp -r certifi/ logout_package/
cp -r charset_normalizer/ logout_package/
cp -r idna/ logout_package/
cp -r six.py logout_package/

# Create the ZIP file
cd logout_package
zip -r ../logout_handler.zip .
cd ..

# Deploy to AWS Lambda
echo "☁️ Deploying to AWS Lambda..."

# Check if function exists
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME 2>/dev/null; then
    echo "📝 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --zip-file fileb://logout_handler.zip
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name $LAMBDA_FUNCTION_NAME \
        --handler $LAMBDA_HANDLER \
        --runtime $RUNTIME \
        --timeout 30 \
        --memory-size 256
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $LAMBDA_HANDLER \
        --zip-file fileb://logout_handler.zip \
        --timeout 30 \
        --memory-size 256 \
        --description "Logout handler for Epic Library application"
fi

# Clean up
rm -rf logout_package logout_handler.zip

echo "✅ Logout handler deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Update the ROLE_ARN in this script with your actual IAM role"
echo "2. Add the Lambda function to API Gateway with endpoint /logout"
echo "3. Update frontend to call the logout endpoint"
echo "4. Test the logout functionality" 