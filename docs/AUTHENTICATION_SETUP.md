# Authentication & Authorization Setup Guide

This guide will help you set up AWS Cognito authentication and authorization for your Epic Library application.

## Overview

Your current architecture includes:
- **Frontend**: React app with TypeScript
- **Backend**: AWS Lambda functions with Python
- **API Gateway**: REST API endpoints
- **Database**: DynamoDB for book storage
- **Vector Search**: OpenSearch for semantic search

## Why You Need Cognito

1. **Security**: Currently, your Lambda functions are unprotected
2. **User Management**: Track who uploads books and asks questions
3. **Scalability**: Cognito handles user registration, login, and token management
4. **AWS Integration**: Seamless integration with API Gateway and Lambda

## Architecture with Cognito

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   API Gateway   │    │   Lambda        │
│                 │    │                 │    │   Functions     │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Cognito   │ │◄──►│ │  Cognito    │ │◄──►│ │   Auth      │ │
│ │   Client    │ │    │ │ Authorizer  │ │    │ │ Middleware  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Setup Steps

### 1. Run the Setup Script

```bash
chmod +x deployment/scripts/setup-cognito.sh
cd deployment/scripts
./setup-cognito.sh
```

This script will:
- Create a Cognito User Pool
- Create an App Client
- Update configuration files
- Optionally create a test user

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Update Lambda Functions

Make sure your Lambda functions include the `auth_middleware.py` file and use the `@require_auth` decorator.

### 4. Configure API Gateway

1. Go to AWS API Gateway Console
2. Select your API
3. Go to "Authorizers"
4. Create a new Cognito Authorizer:
   - Type: Cognito
   - User Pool: Select your created User Pool
   - Token Source: Authorization

5. Update your API routes to use the Cognito Authorizer

### 5. Test the Setup

1. Start your frontend: `npm run dev`
2. Register a new user
3. Login with the user
4. Test uploading books and asking questions

## Configuration Files

### Frontend Configuration

The setup script creates `frontend/src/config/cognito.ts`:

```typescript
export const COGNITO_CONFIG = {
  UserPoolId: 'us-east-1_XXXXXXXXX',
  ClientId: 'XXXXXXXXXXXXXXXXXX',
  Region: 'us-east-1'
};
```

### Backend Configuration

The setup script creates `backend/src/lambda/cognito_config.py`:

```python
USER_POOL_ID = 'us-east-1_XXXXXXXXX'
REGION = 'us-east-1'
```

## Authentication Flow

### 1. User Registration
1. User fills out registration form
2. Cognito creates user account
3. Email verification sent
4. User verifies email
5. User can now login

### 2. User Login
1. User enters credentials
2. Cognito validates credentials
3. Cognito returns JWT tokens
4. Frontend stores tokens
5. Tokens sent with API requests

### 3. API Authorization
1. Frontend sends request with JWT token
2. API Gateway validates token with Cognito
3. If valid, request forwarded to Lambda
4. Lambda middleware extracts user info
5. Lambda processes request with user context

## Security Features

### Password Policy
- Minimum 8 characters
- Requires uppercase letter
- Requires lowercase letter
- Requires number
- Requires symbol

### Token Security
- JWT tokens with RS256 signing
- Automatic token refresh
- Token expiration handling
- Secure token storage

### CORS Configuration
- Proper CORS headers for cross-origin requests
- Authorization header support
- Preflight request handling

## User Management

### User Attributes
- **email**: Required, verified
- **name**: Required, mutable
- **username**: Auto-generated from email

### User Groups (Optional)
You can create user groups for role-based access:

```bash
# Create admin group
aws cognito-idp create-group \
  --user-pool-id YOUR_USER_POOL_ID \
  --group-name "admin" \
  --description "Administrators"

# Add user to group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id YOUR_USER_POOL_ID \
  --username user@example.com \
  --group-name "admin"
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure API Gateway CORS is configured
   - Check Authorization header is allowed

2. **Token Validation Errors**
   - Verify User Pool ID is correct
   - Check token expiration
   - Ensure proper JWT library installation

3. **User Registration Issues**
   - Check email verification settings
   - Verify password policy compliance
   - Check User Pool configuration

### Debug Steps

1. Check CloudWatch logs for Lambda errors
2. Verify Cognito User Pool settings
3. Test token validation manually
4. Check API Gateway authorizer configuration

## Advanced Features

### Role-Based Access Control

You can implement role-based access using Cognito groups:

```python
@require_role("admin")
def admin_only_function(event, context):
    # Only accessible by admin users
    pass
```

### Custom Attributes

Add custom user attributes:

```bash
aws cognito-idp add-custom-attributes \
  --user-pool-id YOUR_USER_POOL_ID \
  --custom-attributes Name="preferences",AttributeDataType="String",Mutable=true
```

### Multi-Factor Authentication

Enable MFA for additional security:

```bash
aws cognito-idp set-user-pool-mfa-config \
  --user-pool-id YOUR_USER_POOL_ID \
  --mfa-configuration ON \
  --software-token-mfa-configuration Enabled=true
```

## Monitoring and Analytics

### CloudWatch Metrics
- User sign-ups
- Authentication attempts
- Token validations
- Error rates

### Cognito Analytics
- User engagement
- Authentication patterns
- Security events

## Best Practices

1. **Token Management**
   - Store tokens securely
   - Implement automatic refresh
   - Handle token expiration gracefully

2. **Error Handling**
   - Provide clear error messages
   - Implement retry logic
   - Log authentication events

3. **Security**
   - Use HTTPS for all communications
   - Implement proper CORS policies
   - Regular security audits

4. **User Experience**
   - Clear login/registration forms
   - Helpful error messages
   - Smooth authentication flow

## Next Steps

After completing this setup:

1. **Test thoroughly** with multiple users
2. **Monitor logs** for any issues
3. **Implement additional security** features as needed
4. **Add user management** features
5. **Consider implementing** role-based access control

## Support

If you encounter issues:

1. Check AWS CloudWatch logs
2. Verify configuration files
3. Test with AWS CLI commands
4. Review Cognito documentation
5. Check API Gateway settings

## Resources

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [API Gateway Authorization](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html)
- [JWT Token Validation](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html) 