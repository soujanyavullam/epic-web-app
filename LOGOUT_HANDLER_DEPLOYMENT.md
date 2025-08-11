# 🔐 Logout Handler Deployment Guide

## Overview

This guide will help you deploy the new backend logout handler Lambda function that provides proper server-side logout functionality with token invalidation and session cleanup.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Lambda        │
│   (React)       │    │                 │    │   Function      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Logout    │ │◄──►│ │   /logout   │ │◄──►│ │ Logout      │ │
│ │   Button    │ │    │ │   Endpoint  │ │    │ │ Handler     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Cognito       │
                       │   (Token        │
                       │   Invalidation) │
                       └─────────────────┘
```

## 📋 Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Existing API Gateway** with your other endpoints
3. **Cognito User Pool** already set up
4. **IAM permissions** to create Lambda functions and API Gateway resources

## 🚀 Deployment Steps

### Step 1: Deploy the Lambda Function

```bash
# Navigate to backend directory
cd backend

# Make the deployment script executable
chmod +x deploy_logout_handler.sh

# Update the ROLE_ARN in the script with your actual IAM role
# Edit deploy_logout_handler.sh and replace YOUR_ACCOUNT_ID with your AWS account ID

# Run the deployment script
./deploy_logout_handler.sh
```

### Step 2: Add API Gateway Endpoint

#### Option A: Using AWS Console

1. **Go to API Gateway Console**
2. **Select your existing API**
3. **Create a new resource**:
   - Click "Actions" → "Create Resource"
   - Resource Name: `logout`
   - Resource Path: `/logout`
4. **Create POST method**:
   - Click "Actions" → "Create Method"
   - Method: `POST`
   - Integration Type: `Lambda Function`
   - Lambda Function: `epic-logout-function`
5. **Create OPTIONS method** (for CORS):
   - Click "Actions" → "Create Method"
   - Method: `OPTIONS`
   - Integration Type: `Mock`
   - Add CORS headers in response

#### Option B: Using CloudFormation

```bash
# Deploy the CloudFormation template
aws cloudformation create-stack \
  --stack-name epic-logout-handler \
  --template-body file://infrastructure/logout_handler.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

### Step 3: Update Frontend Configuration

1. **Update API Base URL** in `frontend/src/utils/simple-auth.ts`:

```typescript
const API_BASE_URL = 'https://your-actual-api-gateway-url.amazonaws.com/prod';
```

2. **Deploy the updated frontend**:

```bash
cd frontend
npm run build
# Deploy to your hosting service (S3, CloudFront, etc.)
```

### Step 4: Test the Logout Functionality

1. **Login to the application**
2. **Click the logout button**
3. **Check browser console** for logout process logs
4. **Verify** that you're redirected to login page
5. **Try to access protected resources** - should be denied

## 🔧 Configuration Details

### Lambda Function Configuration

- **Function Name**: `epic-logout-function`
- **Runtime**: Python 3.9
- **Handler**: `logout_handler.lambda_handler`
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **Environment Variables**:
  - `USER_POOL_ID`: Your Cognito User Pool ID
  - `REGION`: AWS region

### IAM Permissions Required

The Lambda function needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminUserGlobalSignOut",
        "cognito-idp:AdminGetUser"
      ],
      "Resource": "arn:aws:cognito-idp:REGION:ACCOUNT:userpool/USER_POOL_ID"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### API Gateway Configuration

- **Endpoint**: `POST /logout`
- **Authorization**: None (handled by Lambda)
- **CORS**: Enabled with proper headers
- **Integration**: Lambda Proxy

## 🧪 Testing

### Test Cases

1. **Valid Token Logout**:
   ```bash
   curl -X POST https://your-api-url.amazonaws.com/prod/logout \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json"
   ```

2. **Invalid Token Logout**:
   ```bash
   curl -X POST https://your-api-url.amazonaws.com/prod/logout \
     -H "Authorization: Bearer INVALID_TOKEN" \
     -H "Content-Type: application/json"
   ```

3. **No Token Logout**:
   ```bash
   curl -X POST https://your-api-url.amazonaws.com/prod/logout \
     -H "Content-Type: application/json"
   ```

### Expected Responses

**Success (200)**:
```json
{
  "message": "Logout successful",
  "user_id": "user-sub-id",
  "username": "user@example.com",
  "email": "user@example.com",
  "tokens_invalidated": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Unauthorized (401)**:
```json
{
  "error": "No authorization token provided"
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Lambda Function Not Found**:
   - Check if the function was created successfully
   - Verify the function name in API Gateway integration

2. **Permission Denied**:
   - Ensure the Lambda role has Cognito permissions
   - Check if the User Pool ID is correct

3. **CORS Errors**:
   - Verify OPTIONS method is configured
   - Check CORS headers in API Gateway

4. **Token Validation Fails**:
   - Ensure the User Pool ID matches
   - Check if the JWT token is valid

### Debug Steps

1. **Check CloudWatch Logs**:
   ```bash
   aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/epic-logout-function"
   ```

2. **Test Lambda Directly**:
   ```bash
   aws lambda invoke \
     --function-name epic-logout-function \
     --payload '{"headers":{"Authorization":"Bearer YOUR_TOKEN"}}' \
     response.json
   ```

3. **Check API Gateway Logs**:
   - Enable CloudWatch logging in API Gateway
   - Check the logs for request/response details

## 📊 Monitoring

### CloudWatch Metrics to Monitor

- **Lambda Invocations**: Number of logout requests
- **Lambda Duration**: How long logout takes
- **Lambda Errors**: Failed logout attempts
- **API Gateway 4xx/5xx**: Client/Server errors

### Log Analysis

The Lambda function logs:
- User logout attempts
- Token validation results
- Cognito API calls
- Error details

## 🔒 Security Considerations

1. **Token Validation**: All tokens are verified before logout
2. **Global Sign Out**: Invalidates all user sessions
3. **Audit Logging**: Logs all logout activities
4. **Error Handling**: Graceful handling of invalid tokens
5. **CORS Protection**: Proper CORS headers for browser security

## 📈 Performance

- **Lambda Cold Start**: ~100-200ms
- **Token Validation**: ~50-100ms
- **Cognito API Call**: ~100-300ms
- **Total Response Time**: ~250-600ms

## 🔄 Future Enhancements

1. **Rate Limiting**: Add API Gateway throttling
2. **Enhanced Logging**: Log to DynamoDB or CloudWatch Insights
3. **Metrics**: Add custom CloudWatch metrics
4. **Caching**: Cache Cognito public keys
5. **Multi-Region**: Deploy to multiple regions for latency

## 📞 Support

If you encounter issues:

1. **Check CloudWatch Logs** for detailed error messages
2. **Verify IAM Permissions** are correctly set
3. **Test with AWS CLI** to isolate issues
4. **Review API Gateway Configuration** for CORS and integration issues 