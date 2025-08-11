import json
import boto3
import os
import base64
from typing import Dict, Any, List
import uuid
from datetime import datetime
import urllib.parse
from decimal import Decimal
import concurrent.futures
import time

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('book-embeddings-dev')

def decode_content(file_content: bytes) -> str:
    """Decode file content with simple encoding detection."""
    # Try UTF-8 first
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        # Try common encodings
        for encoding in ['latin-1', 'windows-1252', 'iso-8859-1']:
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        # If all else fails, use latin-1 (which never fails)
        return file_content.decode('latin-1')

def chunk_text(text: str, book_id: str, chunk_size: int = 4000) -> List[Dict]:
    """Split text into chunks using simple character-based approach."""
    try:
        chunks = []
        chunk_id = 0
        
        # Simple character-based chunking
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i + chunk_size]
            
            chunks.append({
                'book_id': book_id,
                'chunk_id': f"{chunk_id:04d}",
                'text': chunk_text,
                'token_count': len(chunk_text.split())  # Approximate token count
            })
            chunk_id += 1
            
        return chunks
    except Exception as e:
        print(f"Error chunking text for book {book_id}: {str(e)}")
        raise

def get_embedding(text: str) -> List[float]:
    """Get embedding for text using Bedrock."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            response = bedrock.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({
                    'inputText': text
                })
            )
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error getting embedding after {max_retries} attempts: {e}")
                raise
            time.sleep(retry_delay)
            retry_delay *= 2  # exponential backoff

def process_chunk(args: tuple) -> Dict[str, Any]:
    """Process a single chunk and return the item for DynamoDB."""
    chunk, book_id = args
    try:
        embedding = get_embedding(chunk['text'])
        decimal_embedding = [Decimal(str(x)) for x in embedding]
        
        return {
            'chunk_id': f"{book_id}-{chunk['chunk_id']}",
            'book_title': book_id,
            'chunk_number': int(chunk['chunk_id']),
            'text': chunk['text'],
            'embedding': decimal_embedding,
            'token_count': chunk['token_count']
        }
    except Exception as e:
        print(f"Error processing chunk {chunk['chunk_id']} of {book_id}: {e}")
        return None

def ingest_book(book_id: str, book_text: str) -> int:
    """Ingest a book into DynamoDB with embeddings using parallel processing."""
    # Split book into chunks using simple approach
    chunks = chunk_text(book_text, book_id)
    print(f"Processing {len(chunks)} chunks for {book_id}")
    
    # Prepare arguments for parallel processing
    chunk_args = [(chunk, book_id) for chunk in chunks]
    
    # Process chunks in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_chunk, args) for args in chunk_args]
        
        # Process completed futures
        successful_chunks = 0
        for future in concurrent.futures.as_completed(futures):
            item = future.result()
            if item:
                try:
                    table.put_item(Item=item)
                    successful_chunks += 1
                except Exception as e:
                    print(f"Error storing chunk in DynamoDB: {e}")
    
    return successful_chunks

def trigger_processing_lambda(book_id: str, s3_key: str):
    """Trigger the processing Lambda function asynchronously."""
    try:
        payload = {
            'book_id': book_id,
            's3_key': s3_key,
            'action': 'process_book'
        }
        
        response = lambda_client.invoke(
            FunctionName='epic-upload-function',  # Self-invoke for processing
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        print(f"Triggered processing Lambda for {book_id}: {response}")
        return True
    except Exception as e:
        print(f"Error triggering processing Lambda: {e}")
        return False

def process_book_from_s3(book_id: str, s3_key: str) -> int:
    """Process a book from S3 (called by the processing Lambda)."""
    try:
        # Get S3 bucket name
        bucket_name = os.environ.get('BOOKS_BUCKET', 'epic-s3-bucket-ramayana')
        
        # Download file from S3
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        file_content_bytes = response['Body'].read()
        
        # Decode content
        file_content = decode_content(file_content_bytes)
        print(f"Downloaded and decoded {len(file_content)} characters for {book_id}")
        
        # Process the book
        successful_chunks = ingest_book(book_id, file_content)
        print(f"Successfully processed {successful_chunks} chunks for {book_id}")
        
        return successful_chunks
    except Exception as e:
        print(f"Error processing book from S3: {e}")
        return 0

# @require_auth  # Temporarily disabled to avoid cryptography dependency
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

        # Check if this is a processing invocation (from S3)
        if 'action' in event and event['action'] == 'process_book':
            book_id = event['book_id']
            s3_key = event['s3_key']
            print(f"Processing book from S3: {book_id}")
            successful_chunks = process_book_from_s3(book_id, s3_key)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Processing completed',
                    'book_id': book_id,
                    'chunks_processed': successful_chunks
                })
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
            file_content_bytes = base64.b64decode(file_content_base64)
            print(f"Decoded file content length: {len(file_content_bytes)} bytes")
            
            # Decode with simple encoding detection
            file_content = decode_content(file_content_bytes)
            print(f"Decoded text content length: {len(file_content)} characters")
            
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
            print(f"Content decode error: {e}")
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

        # Get user information from authenticated request (temporarily disabled)
        # user = get_user_from_event(event)
        # print(f"Upload request from user: {user.get('username') if user else 'Unknown'}")
        print("Upload request from user: Anonymous (auth temporarily disabled)")
        
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
        book_id = filename.replace('.txt', '')

        # For large books, trigger asynchronous processing
        # For small books, process immediately
        content_size = len(file_content)
        if content_size > 50000:  # If book is larger than 50KB, process asynchronously
            print(f"Large book detected ({content_size} chars), triggering async processing")
            trigger_processing_lambda(book_id, s3_key)
            successful_chunks = 0  # Will be processed asynchronously
        else:
            # Process small books immediately
            print(f"Small book detected ({content_size} chars), processing immediately")
            try:
                successful_chunks = ingest_book(book_id, file_content)
                print(f"Successfully processed {successful_chunks} chunks for {book_id}")
            except Exception as e:
                print(f"Error during embedding generation: {e}")
                successful_chunks = 0

        response_body = {
            'message': 'File uploaded successfully to S3 and processing initiated',
            'filename': filename,
            's3_key': s3_key,
            'book_title': book_id,
            'chunks_processed': successful_chunks,
            'processing_mode': 'async' if content_size > 50000 else 'sync',
            'note': f'File uploaded to S3. Processing {"initiated asynchronously" if content_size > 50000 else f"completed with {successful_chunks} chunks"} in DynamoDB.'
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