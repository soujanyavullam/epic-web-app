#!/bin/bash

# Secure API Gateway Deployment Script
# This script deploys different security configurations for the Book Q&A API

set -e

echo "🔒 Secure API Gateway Deployment"
echo "================================"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Function to deploy API Key protected API
deploy_api_key_protected() {
    echo "🚀 Deploying API Key Protected API Gateway..."
    
    aws cloudformation deploy \
        --template-file infrastructure/api_gateway_api_key.yaml \
        --stack-name book-qa-api-key-protected \
        --parameter-overrides Environment=dev \
        --capabilities CAPABILITY_IAM
    
    echo "✅ API Key Protected API deployed successfully!"
    echo "📋 Getting API Key..."
    
    API_KEY=$(aws cloudformation describe-stacks \
        --stack-name book-qa-api-key-protected \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiKey`].OutputValue' \
        --output text)
    
    echo "🔑 API Key: $API_KEY"
    echo "📝 Add this API key to your frontend requests:"
    echo "   headers: { 'x-api-key': '$API_KEY' }"
}

# Function to deploy Cognito protected API
deploy_cognito_protected() {
    echo "🚀 Deploying Cognito Protected API Gateway..."
    
    # Get Cognito User Pool ARN
    USER_POOL_ARN=$(aws cognito-idp list-user-pools --max-items 1 --query 'UserPools[0].Arn' --output text)
    USER_POOL_ID=$(aws cognito-idp list-user-pools --max-items 1 --query 'UserPools[0].Id' --output text)
    CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id $USER_POOL_ID --query 'UserPoolClients[0].ClientId' --output text)
    
    if [ "$USER_POOL_ARN" == "None" ] || [ "$CLIENT_ID" == "None" ]; then
        echo "❌ No Cognito User Pool found. Please create one first."
        echo "   You can use the setup-cognito.sh script."
        exit 1
    fi
    
    aws cloudformation deploy \
        --template-file infrastructure/api_gateway_secure.yaml \
        --stack-name book-qa-cognito-protected \
        --parameter-overrides \
            Environment=dev \
            CognitoUserPoolArn=$USER_POOL_ARN \
            CognitoUserPoolClientId=$CLIENT_ID \
        --capabilities CAPABILITY_IAM
    
    echo "✅ Cognito Protected API deployed successfully!"
    echo "🔐 API is now protected with Cognito authentication"
}

# Function to deploy VPC private API
deploy_vpc_private() {
    echo "🚀 Deploying VPC Private API Gateway..."
    
    aws cloudformation deploy \
        --template-file infrastructure/vpc_private_api.yaml \
        --stack-name book-qa-vpc-private \
        --parameter-overrides Environment=dev \
        --capabilities CAPABILITY_IAM
    
    echo "✅ VPC Private API deployed successfully!"
    echo "🔒 API is now accessible only from within the VPC"
    
    # Get VPC and subnet information
    VPC_ID=$(aws cloudformation describe-stacks \
        --stack-name book-qa-vpc-private \
        --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' \
        --output text)
    
    echo "🌐 VPC ID: $VPC_ID"
    echo "📝 To access this API, you need to be within the VPC or use a VPN"
}

# Function to update CORS restrictions
update_cors_restrictions() {
    echo "🔧 Updating CORS restrictions..."
    
    # Update Lambda functions with restricted CORS
    echo "📦 Creating deployment package..."
    cd lambda_minimal
    zip -r ../lambda_package_secure_cors.zip . -x "*.pyc" "__pycache__/*"
    cd ..
    
    # Update Lambda functions
    aws lambda update-function-code \
        --function-name epic-query-function \
        --zip-file fileb://lambda_package_secure_cors.zip
    
    aws lambda update-function-code \
        --function-name list-books-function \
        --zip-file fileb://lambda_package_secure_cors.zip
    
    aws lambda update-function-code \
        --function-name epic-upload-function \
        --zip-file fileb://lambda_package_secure_cors.zip
    
    aws lambda update-function-code \
        --function-name epic-repo-generator \
        --zip-file fileb://lambda_package_secure_cors.zip
    
    echo "✅ CORS restrictions updated!"
    echo "🌐 API now only accepts requests from specified domains"
}

# Function to show current security status
show_security_status() {
    echo "🔍 Current Security Status"
    echo "========================="
    
    # Check API Gateway endpoints
    echo "📡 API Gateway Endpoints:"
    aws apigateway get-rest-apis --query 'items[?name==`book-qa-api`].{Name:name,Id:id,EndpointConfiguration:endpointConfiguration}' --output table
    
    # Check Lambda function permissions
    echo "🔐 Lambda Function Permissions:"
    aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `epic-`)].{Name:FunctionName,Runtime:Runtime,Timeout:Timeout}' --output table
    
    # Check IAM roles
    echo "👤 IAM Roles:"
    aws iam list-roles --query 'Roles[?contains(RoleName, `epic`)].{Name:RoleName,Arn:Arn}' --output table
}

# Main menu
echo "Choose a security configuration to deploy:"
echo "1. API Key Protection (Simple)"
echo "2. Cognito Authentication (Recommended)"
echo "3. VPC Private API (Advanced)"
echo "4. Update CORS Restrictions"
echo "5. Show Current Security Status"
echo "6. Exit"

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        deploy_api_key_protected
        ;;
    2)
        deploy_cognito_protected
        ;;
    3)
        deploy_vpc_private
        ;;
    4)
        update_cors_restrictions
        ;;
    5)
        show_security_status
        ;;
    6)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please enter a number between 1-6."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment completed successfully!"
echo "📚 Your Book Q&A API is now more secure!" 