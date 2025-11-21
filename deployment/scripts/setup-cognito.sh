#!/bin/bash

# Setup script for AWS Cognito authentication
# This script will create a Cognito User Pool and App Client

set -e

echo "🚀 Setting up AWS Cognito for Epic Library App"
echo "================================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI and credentials are configured"

# Create Cognito User Pool
echo "📝 Creating Cognito User Pool..."

USER_POOL_RESPONSE=$(aws cognito-idp create-user-pool \
    --pool-name "EpicLibraryPool" \
    --policies '{
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireUppercase": true,
            "RequireLowercase": true,
            "RequireNumbers": true,
            "RequireSymbols": true
        }
    }' \
    --auto-verified-attributes email \
    --schema '[
        {
            "Name": "email",
            "AttributeDataType": "String",
            "Required": true,
            "Mutable": true
        },
        {
            "Name": "name",
            "AttributeDataType": "String",
            "Required": true,
            "Mutable": true
        }
    ]' \
    --mfa-configuration OFF \
    --admin-create-user-config '{
        "AllowAdminCreateUserOnly": false
    }')

USER_POOL_ID=$(echo $USER_POOL_RESPONSE | jq -r '.UserPool.Id')

if [ "$USER_POOL_ID" = "null" ] || [ -z "$USER_POOL_ID" ]; then
    echo "❌ Failed to create User Pool"
    exit 1
fi

echo "✅ User Pool created with ID: $USER_POOL_ID"

# Create App Client
echo "📱 Creating App Client..."

APP_CLIENT_RESPONSE=$(aws cognito-idp create-user-pool-client \
    --user-pool-id $USER_POOL_ID \
    --client-name "EpicLibraryAppClient" \
    --no-generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
    --supported-identity-providers COGNITO)

APP_CLIENT_ID=$(echo $APP_CLIENT_RESPONSE | jq -r '.UserPoolClient.ClientId')

if [ "$APP_CLIENT_ID" = "null" ] || [ -z "$APP_CLIENT_ID" ]; then
    echo "❌ Failed to create App Client"
    exit 1
fi

echo "✅ App Client created with ID: $APP_CLIENT_ID"

# Create configuration files
echo "📄 Creating configuration files..."

# Create frontend config directory if it doesn't exist
mkdir -p frontend/src/config

# Create frontend config
cat > frontend/src/config/cognito.ts << EOF
export const COGNITO_CONFIG = {
  UserPoolId: '$USER_POOL_ID',
  ClientId: '$APP_CLIENT_ID',
  Region: 'us-east-1'
};
EOF

# Create backend config
cat > backend/src/lambda/cognito_config.py << EOF
# Cognito Configuration
USER_POOL_ID = '$USER_POOL_ID'
REGION = 'us-east-1'
EOF

echo "✅ Configuration files created"

# Update the auth components with the correct IDs
echo "🔧 Updating authentication components..."

# Update Auth.tsx
sed -i '' "s/us-east-1_YOUR_USER_POOL_ID/$USER_POOL_ID/g" frontend/src/components/Auth.tsx
sed -i '' "s/YOUR_CLIENT_ID/$APP_CLIENT_ID/g" frontend/src/components/Auth.tsx

# Update auth.ts
sed -i '' "s/us-east-1_YOUR_USER_POOL_ID/$USER_POOL_ID/g" frontend/src/utils/auth.ts
sed -i '' "s/YOUR_CLIENT_ID/$APP_CLIENT_ID/g" frontend/src/utils/auth.ts

# Update auth_middleware.py
sed -i '' "s/us-east-1_YOUR_USER_POOL_ID/$USER_POOL_ID/g" backend/src/lambda/auth_middleware.py

echo "✅ Authentication components updated"

# Create a test user (optional)
echo ""
echo "🤔 Would you like to create a test user? (y/n)"
read -r create_test_user

if [[ $create_test_user =~ ^[Yy]$ ]]; then
    echo "📝 Creating test user..."
    
    echo "Enter email for test user:"
    read -r test_email
    
    echo "Enter name for test user:"
    read -r test_name
    
    echo "Enter password for test user (min 8 chars, uppercase, lowercase, number, symbol):"
    read -s test_password
    
    aws cognito-idp sign-up \
        --client-id $APP_CLIENT_ID \
        --username $test_email \
        --password $test_password \
        --user-attributes Name=email,Value=$test_email Name=name,Value="$test_name"
    
    echo "✅ Test user created successfully!"
    echo "📧 Check your email for verification link"
fi

echo ""
echo "🎉 Cognito setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "  User Pool ID: $USER_POOL_ID"
echo "  App Client ID: $APP_CLIENT_ID"
echo "  Region: us-east-1"
echo ""
echo "📝 Next steps:"
echo "  1. Install frontend dependencies: cd frontend && npm install"
echo "  2. Update your Lambda functions to include the auth_middleware.py file"
echo "  3. Update your API Gateway to use Cognito Authorizer"
echo "  4. Test the authentication flow"
echo ""
echo "🔗 Useful AWS Console links:"
echo "  Cognito User Pool: https://console.aws.amazon.com/cognito/users/?region=us-east-1&userPoolId=$USER_POOL_ID"
echo "  API Gateway: https://console.aws.amazon.com/apigateway/home?region=us-east-1" 