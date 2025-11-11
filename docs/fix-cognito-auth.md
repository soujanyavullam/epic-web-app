# Fix Cognito Authentication Issue

## 🔧 **Problem**: `USER_SRP_AUTH is not enabled for the client`

The Amazon Cognito Identity JS library requires `USER_SRP_AUTH` authentication flow, but our App Client doesn't have it enabled.

## 🛠️ **Solution 1: Update App Client via AWS Console**

1. **Go to AWS Cognito Console**: https://console.aws.amazon.com/cognito/users/
2. **Select your User Pool**: `us-east-1_8d5MmHizq`
3. **Go to "App integration" tab**
4. **Click on your App Client**: `73hfbldjkkbdjvsml57g671j4l`
5. **Scroll down to "Authentication flows"**
6. **Enable these flows**:
   - ✅ `ALLOW_USER_SRP_AUTH`
   - ✅ `ALLOW_USER_PASSWORD_AUTH`
   - ✅ `ALLOW_REFRESH_TOKEN_AUTH`
7. **Click "Save changes"**

## 🛠️ **Solution 2: Use AWS CLI (if credentials are valid)**

```bash
aws cognito-idp update-user-pool-client \
  --user-pool-id us-east-1_8d5MmHizq \
  --client-id 73hfbldjkkbdjvsml57g671j4l \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_SRP_AUTH
```

## 🛠️ **Solution 3: Alternative Authentication Approach**

If you prefer, we can modify the frontend to use a simpler authentication approach that doesn't require SRP. Let me know if you'd like me to implement this alternative.

## 🧪 **Test After Fix**

1. **Restart the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Try logging in** with the test user:
   - Email: `test@test.com`
   - Password: `TestPass123!`

3. **Check browser console** for any remaining errors

## 📋 **Expected Authentication Flows**

After enabling SRP, your App Client should support:
- **USER_SRP_AUTH**: Secure Remote Password protocol (recommended)
- **USER_PASSWORD_AUTH**: Username/password authentication
- **REFRESH_TOKEN_AUTH**: Token refresh for maintaining sessions

## 🔍 **Verify the Fix**

You can verify the App Client configuration by checking the AWS Console or running:

```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_8d5MmHizq \
  --client-id 73hfbldjkkbdjvsml57g671j4l
```

The `ExplicitAuthFlows` should include `ALLOW_USER_SRP_AUTH`. 