# Manual Cognito Setup Guide

Since your AWS CLI credentials are not configured, here's how to set up Cognito manually through the AWS Console.

## Step 1: Configure AWS Credentials

First, you need to configure your AWS credentials:

```bash
aws configure
```

You'll need:
- **AWS Access Key ID**: Get this from your AWS IAM console
- **AWS Secret Access Key**: Get this from your AWS IAM console  
- **Default region**: `us-east-1`
- **Default output format**: `json`

## Step 2: Create Cognito User Pool (AWS Console)

1. Go to [AWS Cognito Console](https://console.aws.amazon.com/cognito/)
2. Click "Create user pool"
3. Configure the following settings:

### Step 1: Configure sign-in experience
- **User pool name**: `EpicLibraryPool`
- **Cognito user pool sign-in options**: Email
- **User name requirements**: Allow email addresses
- **Case sensitivity**: Keep case sensitive

### Step 2: Configure password policy
- **Password policy**: Cognito defaults
- **Temporary password**: 7 days
- **User account recovery**: Self-service recovery

### Step 3: Configure sign-up experience
- **Self-service sign-up**: Enabled
- **Cognito-assisted verification and confirmation**: Enabled
- **MFA**: Off
- **User attributes**: 
  - Email (required, verified)
  - Name (required, mutable)

### Step 4: Configure message delivery
- **Email provider**: Cognito default email
- **From email address**: Use Cognito default

### Step 5: Integrate your app
- **User pool client name**: `EpicLibraryAppClient`
- **Client secret**: Do not generate a client secret
- **Authentication flows**: 
  - ✅ ALLOW_USER_PASSWORD_AUTH
  - ✅ ALLOW_REFRESH_TOKEN_AUTH
- **OAuth 2.0**: Not required

### Step 6: Review and create
- Review settings and click "Create user pool"

## Step 3: Get Your Configuration

After creating the user pool, note down:
- **User Pool ID**: `us-east-1_XXXXXXXXX`
- **App Client ID**: `XXXXXXXXXXXXXXXXXX`

## Step 4: Update Configuration Files

### Update Frontend Configuration

Create `frontend/src/config/cognito.ts`:

```typescript
export const COGNITO_CONFIG = {
  UserPoolId: 'us-east-1_XXXXXXXXX', // Replace with your User Pool ID
  ClientId: 'XXXXXXXXXXXXXXXXXX', // Replace with your App Client ID
  Region: 'us-east-1'
};
```

### Update Auth Components

Update `frontend/src/components/Auth.tsx`:

```typescript
// Replace these lines in the poolData object:
const poolData = {
  UserPoolId: 'us-east-1_XXXXXXXXX', // Your User Pool ID
  ClientId: 'XXXXXXXXXXXXXXXXXX' // Your App Client ID
};
```

Update `frontend/src/utils/auth.ts`:

```typescript
// Replace these lines in the poolData object:
const poolData = {
  UserPoolId: 'us-east-1_XXXXXXXXX', // Your User Pool ID
  ClientId: 'XXXXXXXXXXXXXXXXXX' // Your App Client ID
};
```

### Update Backend Configuration

Create `backend/src/lambda/cognito_config.py`:

```python
# Cognito Configuration
USER_POOL_ID = 'us-east-1_XXXXXXXXX'  # Your User Pool ID
REGION = 'us-east-1'
```

Update `backend/src/lambda/auth_middleware.py`:

```python
# Replace this line:
USER_POOL_ID = 'us-east-1_XXXXXXXXX'  # Your User Pool ID
```

## Step 5: Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Step 6: Configure API Gateway

1. Go to [AWS API Gateway Console](https://console.aws.amazon.com/apigateway/)
2. Select your API
3. Go to "Authorizers"
4. Click "Create authorizer"
5. Configure:
   - **Name**: `CognitoAuthorizer`
   - **Type**: Cognito
   - **User Pool**: Select your created User Pool
   - **Token Source**: Authorization
6. Click "Create"
7. Update your API routes to use this authorizer

## Step 7: Test the Setup

1. Start your frontend:
   ```bash
   cd frontend
   npm run dev
   ```

2. Register a new user
3. Login with the user
4. Test uploading books and asking questions

## Troubleshooting

### If you get CORS errors:
- Check API Gateway CORS configuration
- Ensure Authorization header is allowed

### If you get token validation errors:
- Verify User Pool ID is correct
- Check token expiration
- Ensure JWT library is installed

### If user registration fails:
- Check email verification settings
- Verify password meets policy requirements

## Next Steps

After manual setup:
1. Test authentication flow thoroughly
2. Monitor CloudWatch logs
3. Consider adding role-based access control
4. Implement user management features 