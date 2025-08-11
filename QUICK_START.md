# Quick Start: Authentication with AWS Cognito

## 🚀 Get Started in 5 Minutes

### 1. Run the Setup Script

```bash
./setup-cognito.sh
```

This will:
- ✅ Create Cognito User Pool
- ✅ Create App Client
- ✅ Update all configuration files
- ✅ Optionally create a test user

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Configure API Gateway

1. Go to [AWS API Gateway Console](https://console.aws.amazon.com/apigateway/)
2. Select your API
3. Go to "Authorizers"
4. Create Cognito Authorizer:
   - Type: Cognito
   - User Pool: Select your created User Pool
   - Token Source: Authorization
5. Update your API routes to use the Cognito Authorizer

### 4. Test Authentication

```bash
cd frontend
npm run dev
```

Visit your app and:
1. Register a new user
2. Login with the user
3. Test uploading books and asking questions

## 🔧 What's Been Added

### Frontend Components
- `Auth.tsx` - Login/Register component
- `auth.ts` - Authentication utilities
- Updated `App.tsx` - Authentication flow
- Updated `BookQA.tsx` - Authenticated API calls
- Updated `BookUpload.tsx` - Authenticated API calls

### Backend Components
- `auth_middleware.py` - JWT validation and user extraction
- Updated Lambda functions with `@require_auth` decorator

### Configuration
- Cognito User Pool with email verification
- App Client with password authentication
- JWT token validation
- CORS configuration

## 🔐 Security Features

- **Password Policy**: 8+ chars, uppercase, lowercase, number, symbol
- **Email Verification**: Required for account activation
- **JWT Tokens**: Secure token-based authentication
- **CORS**: Proper cross-origin request handling
- **User Context**: Track who uploads books and asks questions

## 📋 Next Steps

1. **Test thoroughly** with multiple users
2. **Monitor CloudWatch logs** for any issues
3. **Add role-based access** if needed
4. **Implement user management** features
5. **Add MFA** for additional security

## 🆘 Troubleshooting

### Common Issues

**CORS Errors**
- Check API Gateway CORS configuration
- Ensure Authorization header is allowed

**Token Validation Errors**
- Verify User Pool ID in configuration
- Check token expiration
- Ensure JWT library is installed

**User Registration Issues**
- Check email verification settings
- Verify password meets policy requirements

### Debug Commands

```bash
# Check Cognito User Pool
aws cognito-idp describe-user-pool --user-pool-id YOUR_USER_POOL_ID

# List users
aws cognito-idp list-users --user-pool-id YOUR_USER_POOL_ID

# Test token validation
aws cognito-idp get-user --access-token YOUR_TOKEN
```

## 📚 Documentation

- [Full Authentication Guide](AUTHENTICATION_SETUP.md)
- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [API Gateway Authorization](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html)

## 🎯 Architecture Overview

```
User → React App → Cognito → API Gateway → Lambda → DynamoDB/OpenSearch
```

**Authentication Flow:**
1. User registers/logs in via Cognito
2. Cognito returns JWT tokens
3. Frontend sends requests with Authorization header
4. API Gateway validates tokens with Cognito
5. Lambda functions extract user context
6. User-specific data is processed and stored

**Security Benefits:**
- ✅ Protected API endpoints
- ✅ User-specific data isolation
- ✅ Secure token management
- ✅ Scalable user management
- ✅ AWS-native security features 