import json
import jwt
import boto3
import requests
from typing import Dict, Any, Optional
from functools import wraps

# Cognito User Pool configuration
USER_POOL_ID = 'us-east-1_8d5MmHizq'  # Replace with your User Pool ID
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

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
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

def extract_token_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """Extract JWT token from Authorization header"""
    auth_header = headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None

def require_auth(func):
    """Decorator to require authentication for Lambda functions"""
    @wraps(func)
    def wrapper(event, context):
        try:
            # Extract headers
            headers = event.get('headers', {}) or {}
            
            # Extract token
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
            
            # Verify token
            decoded_token = verify_jwt_token(token)
            if not decoded_token:
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
            
            # Add user info to event
            event['user'] = {
                'username': decoded_token.get('cognito:username'),
                'email': decoded_token.get('email'),
                'sub': decoded_token.get('sub'),
                'groups': decoded_token.get('cognito:groups', [])
            }
            
            # Call original function
            return func(event, context)
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Internal server error during authentication'
                })
            }
    
    return wrapper

def get_user_from_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract user information from authenticated event"""
    return event.get('user')

def require_role(required_role: str):
    """Decorator to require specific role for Lambda functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            # First apply authentication
            auth_result = require_auth(func)(event, context)
            
            # If authentication failed, return the error
            if auth_result.get('statusCode') != 200:
                return auth_result
            
            # Check role
            user = get_user_from_event(event)
            if not user:
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({
                        'error': 'User information not found'
                    })
                }
            
            user_groups = user.get('groups', [])
            if required_role not in user_groups:
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({
                        'error': f'Insufficient permissions. Required role: {required_role}'
                    })
                }
            
            return func(event, context)
        
        return wrapper
    return decorator 