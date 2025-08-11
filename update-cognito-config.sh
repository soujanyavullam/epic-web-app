#!/bin/bash

# Script to update Cognito configuration files with actual IDs
# Run this after creating your Cognito User Pool and App Client

echo "🔧 Updating Cognito Configuration Files"
echo "========================================"

# Check if User Pool ID is provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./update-cognito-config.sh <USER_POOL_ID> <APP_CLIENT_ID>"
    echo ""
    echo "Example:"
    echo "  ./update-cognito-config.sh us-east-1_gc1GbO2tn 6ikt5rvgcv0ovrveel3hhlo1dh"
    echo ""
    echo "You can find these IDs in the AWS Cognito Console:"
    echo "  User Pool ID: https://console.aws.amazon.com/cognito/users/"
    echo "  App Client ID: In your User Pool > App integration > App client list"
    exit 1
fi

USER_POOL_ID=$1
APP_CLIENT_ID=$2

echo "User Pool ID: $USER_POOL_ID"
echo "App Client ID: $APP_CLIENT_ID"
echo ""

# Create frontend config directory if it doesn't exist
mkdir -p frontend/src/config

# Create frontend config file
echo "📄 Creating frontend configuration..."
cat > frontend/src/config/cognito.ts << EOF
export const COGNITO_CONFIG = {
  UserPoolId: '$USER_POOL_ID',
  ClientId: '$APP_CLIENT_ID',
  Region: 'us-east-1'
};
EOF

# Update Auth.tsx
echo "🔧 Updating Auth.tsx..."
sed -i '' "s/us-east-1_YOUR_USER_POOL_ID/$USER_POOL_ID/g" frontend/src/components/Auth.tsx
sed -i '' "s/YOUR_CLIENT_ID/$APP_CLIENT_ID/g" frontend/src/components/Auth.tsx

# Update auth.ts
echo "🔧 Updating auth.ts..."
sed -i '' "s/us-east-1_YOUR_USER_POOL_ID/$USER_POOL_ID/g" frontend/src/utils/auth.ts
sed -i '' "s/YOUR_CLIENT_ID/$APP_CLIENT_ID/g" frontend/src/utils/auth.ts

# Create backend config
echo "📄 Creating backend configuration..."
cat > backend/src/lambda/cognito_config.py << EOF
# Cognito Configuration
USER_POOL_ID = '$USER_POOL_ID'
REGION = 'us-east-1'
EOF

# Update auth_middleware.py
echo "🔧 Updating auth_middleware.py..."
sed -i '' "s/us-east-1_YOUR_USER_POOL_ID/$USER_POOL_ID/g" backend/src/lambda/auth_middleware.py

echo ""
echo "✅ Configuration files updated successfully!"
echo ""
echo "📋 Summary of changes:"
echo "  ✅ frontend/src/config/cognito.ts - Created"
echo "  ✅ frontend/src/components/Auth.tsx - Updated"
echo "  ✅ frontend/src/utils/auth.ts - Updated"
echo "  ✅ backend/src/lambda/cognito_config.py - Created"
echo "  ✅ backend/src/lambda/auth_middleware.py - Updated"
echo ""
echo "🚀 Next steps:"
echo "  1. Install frontend dependencies: cd frontend && npm install"
echo "  2. Configure API Gateway with Cognito Authorizer"
echo "  3. Test the authentication flow"
echo ""
echo "🔗 Useful links:"
echo "  Cognito Console: https://console.aws.amazon.com/cognito/users/?region=us-east-1"
echo "  API Gateway: https://console.aws.amazon.com/apigateway/home?region=us-east-1" 