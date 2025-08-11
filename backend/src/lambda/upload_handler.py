import json
import boto3
import os
import base64
from typing import Dict, Any
import uuid
from datetime import datetime
import urllib.parse
from auth_middleware import require_auth, get_user_from_event

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

@require_auth
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for uploading text files to S3 and triggering processing.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': ''
            }

        # Get the request body
        body = event.get('body', '')
        print(f"Body type: {type(body)}, isBase64Encoded: {event.get('isBase64Encoded', False)}")
        
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
            print(f"Decoded base64 body length: {len(body)}")

        # Parse JSON body (frontend now sends JSON with base64 content)
        try:
            body_data = json.loads(body)
            filename = body_data.get('filename', '')
            file_content_base64 = body_data.get('file_content', '')
            
            print(f"Parsed filename: {filename}")
            print(f"Base64 content length: {len(file_content_base64)}")
            
            # Decode base64 content
            file_content = base64.b64decode(file_content_base64).decode('utf-8')
            print(f"Decoded file content length: {len(file_content)}")
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': 'Invalid JSON format',
                    'message': str(e)
                })
            }
        except Exception as e:
            print(f"Base64 decode error: {e}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': 'Failed to decode file content',
                    'message': str(e)
                })
            }

        # Get user information from authenticated request
        user = get_user_from_event(event)
        print(f"Upload request from user: {user.get('username') if user else 'Unknown'}")
        
        # Validate that we have file content and filename
        if not file_content or not filename:
            print(f"Validation failed - filename: {filename}, content length: {len(file_content) if file_content else 0}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': 'No file content or filename provided'
                })
            }

        # Validate file type
        if not filename.endswith('.txt'):
            print(f"Invalid file type: {filename}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': 'Only .txt files are supported'
                })
            }

        # Get S3 bucket name
        bucket_name = os.environ.get('BOOKS_BUCKET', 'epic-s3-bucket-ramayana')
        print(f"Using bucket: {bucket_name}")
        
        # Use simple filename for easier debugging
        s3_key = filename
        print(f"Uploading to S3 key: {s3_key}")

        # Upload file to S3
        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content.encode('utf-8'),
                ContentType='text/plain'
            )
            print(f"Successfully uploaded to S3: {bucket_name}/{s3_key}")
        except Exception as e:
            print(f"S3 upload error: {e}")
            raise

        # Extract book title from filename (remove .txt extension)
        book_title = filename.replace('.txt', '')

        response_body = {
            'message': 'File uploaded successfully to S3',
            'filename': filename,
            's3_key': s3_key,
            'book_title': book_title,
            'note': 'File uploaded to S3. Run ingest_book.py to process for embeddings.'
        }
        
        print(f"Returning response: {json.dumps(response_body)}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': json.dumps(response_body)
        }

    except Exception as e:
        print(f"Error in upload handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        } 