import json
import boto3
import os
from typing import Dict, Any
from datetime import datetime
import jwt
import requests

# Initialize AWS clients
cognito_idp = boto3.client('cognito-idp')

# Cognito configuration
USER_POOL_ID = 'us-east-1_8d5MmHizq'
REGION = 'us-east-1'

def get_cognito_public_keys():
    """Fetch Cognito public keys for JWT verification"""
    try:
        url = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['keys']
    except Exception as e:
        print(f"Error fetching Cognito public keys: {e}")
        return None

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token from Cognito"""
    try:
        # Decode token header to get key ID
        header = jwt.get_unverified_header(token)
        key_id = header.get('kid')
        
        if not key_id:
            print("No key ID found in token header")
            return None
        
        # Get public keys
        public_keys = get_cognito_public_keys()
        if not public_keys:
            print("Failed to fetch public keys")
            return None
        
        # Find the correct public key
        public_key = None
        for key in public_keys:
            if key['kid'] == key_id:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            print(f"Public key with ID {key_id} not found")
            return None
        
        # Verify and decode token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=None,  # Cognito doesn't use audience
            issuer=f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}'
        )
        
        return decoded
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None

def extract_token_from_headers(headers: Dict[str, str]) -> str:
    """Extract JWT token from Authorization header"""
    auth_header = headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None

def invalidate_user_tokens(username: str):
    """Invalidate all tokens for a user"""
    try:
        # Admin sign out user (invalidates all tokens)
        response = cognito_idp.admin_user_global_sign_out(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        print(f"Successfully invalidated tokens for user: {username}")
        return True
    except Exception as e:
        print(f"Error invalidating tokens for user {username}: {e}")
        return False

def log_logout_activity(user_info: Dict[str, Any]):
    """Log logout activity for audit purposes"""
    try:
        # You could log to CloudWatch, DynamoDB, or other services
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'logout',
            'user_id': user_info.get('sub'),
            'username': user_info.get('cognito:username'),
            'email': user_info.get('email'),
            'ip_address': 'client_ip',  # Would need to extract from event
            'user_agent': 'client_user_agent'  # Would need to extract from event
        }
        print(f"Logout activity logged: {json.dumps(log_entry)}")
        return True
    except Exception as e:
        print(f"Error logging logout activity: {e}")
        return False

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for handling logout requests.
    Validates the user's token and invalidates their session.
    """
    try:
        print(f"Received logout request: {json.dumps(event)}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true'
                },
                'body': ''
            }

        # Extract headers
        headers = event.get('headers', {}) or {}
        
        # Extract and verify token
        token = extract_token_from_headers(headers)
        if not token:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'error': 'No authorization token provided'
                })
            }
        
        # Verify the token
        user_info = verify_jwt_token(token)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Invalid or expired token'
                })
            }
        
        # Extract user information
        username = user_info.get('cognito:username')
        user_id = user_info.get('sub')
        email = user_info.get('email')
        
        print(f"Processing logout for user: {username} ({email})")
        
        # Invalidate user tokens
        token_invalidated = invalidate_user_tokens(username)
        
        # Log the logout activity
        log_logout_activity(user_info)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'message': 'Logout successful',
                'user_id': user_id,
                'username': username,
                'email': email,
                'tokens_invalidated': token_invalidated,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error during logout: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error during logout',
                'message': str(e)
            })
        } 