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
s3_vectors_client = boto3.client('s3vectors')

# S3 Vectors Configuration
VECTOR_BUCKET_NAME = 'epic-vector-bucket'
VECTOR_INDEX_NAME = 'book-embeddings-index'
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'epic-s3-bucket-ramayana')

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

def upload_vector_to_s3_vectors(vector_id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
    """Upload a vector embedding to S3 Vectors."""
    try:
        # Use the correct put_vectors method for S3 Vectors with proper parameter names
        response = s3_vectors_client.put_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            vectors=[
                {
                    'key': vector_id,  # Use 'key' as required by S3 Vectors API
                    'data': {
                        'float32': embedding  # Wrap embedding in float32 key as per S3 Vectors format
                    },
                    'metadata': metadata
                }
            ]
        )
        
        print(f"Uploaded vector to S3 Vectors: {vector_id}")
        return True
    except Exception as e:
        print(f"Error uploading vector {vector_id} to S3 Vectors: {e}")
        print(f"Available methods: {[method for method in dir(s3_vectors_client) if not method.startswith('_')]}")
        return False

def process_chunk_for_s3_vectors(args: tuple) -> Dict[str, Any]:
    """Process a single chunk and return the item for S3 Vectors."""
    chunk, book_id = args
    try:
        embedding = get_embedding(chunk['text'])
        
        # Upload to S3 Vectors
        vector_id = f"{book_id}-{chunk['chunk_id']}"
        metadata = {
            'book_title': book_id,
            'chunk_number': int(chunk['chunk_id']),
            'chunk_id': chunk['chunk_id'],
            'text': chunk['text']  # Store the actual text content in metadata
        }
        
        success = upload_vector_to_s3_vectors(vector_id, embedding, metadata)
        if success:
            return {
                'chunk_id': chunk['chunk_id'],
                'success': True,
                'vector_id': vector_id
            }
        else:
            return {
                'chunk_id': chunk['chunk_id'],
                'success': False,
                'error': 'Failed to upload to S3 Vectors'
            }
    except Exception as e:
        print(f"Error processing chunk {chunk['chunk_id']} of {book_id}: {e}")
        return {
            'chunk_id': chunk['chunk_id'],
            'success': False,
            'error': str(e)
        }

def ingest_book_s3_vectors(book_id: str, book_text: str) -> int:
    """Ingest a book into S3 Vectors with embeddings using parallel processing."""
    # Split book into chunks using simple approach
    chunks = chunk_text(book_text, book_id)
    print(f"Split book into {len(chunks)} chunks")
    
    # Process chunks in parallel
    successful_chunks = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Create arguments for each chunk
        chunk_args = [(chunk, book_id) for chunk in chunks]
        
        # Submit all chunks for processing
        future_to_chunk = {executor.submit(process_chunk_for_s3_vectors, args): args for args in chunk_args}
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_chunk):
            result = future.result()
            if result['success']:
                successful_chunks += 1
                print(f"Successfully processed chunk {result['chunk_id']}")
            else:
                print(f"Failed to process chunk {result['chunk_id']}: {result.get('error', 'Unknown error')}")
    
    print(f"Successfully processed {successful_chunks} out of {len(chunks)} chunks")
    return successful_chunks

def trigger_processing_lambda(book_id: str, s3_key: str):
    """Trigger the processing lambda for large books."""
    try:
        lambda_client.invoke(
            FunctionName='epic-upload-s3-vectors',  # Use the correct function name
            InvocationType='Event',
            Payload=json.dumps({
                'action': 'process_book',
                'book_id': book_id,
                's3_key': s3_key
            })
        )
        print(f"Triggered processing lambda for {book_id}")
    except Exception as e:
        print(f"Error triggering processing lambda: {e}")

def process_book_from_s3_s3_vectors(book_id: str, s3_key: str) -> int:
    """Process a book from S3 (for async processing)."""
    try:
        # Download from S3
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        book_content = response['Body'].read().decode('utf-8')
        
        # Process with S3 Vectors
        successful_chunks = ingest_book_s3_vectors(book_id, book_content)
        print(f"Successfully processed {successful_chunks} chunks for {book_id} from S3")
        return successful_chunks
    except Exception as e:
        print(f"Error processing book {book_id} from S3: {e}")
        return 0

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for uploading text files to S3 and triggering S3 Vectors processing.
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
            successful_chunks = process_book_from_s3_s3_vectors(book_id, s3_key)
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
        # user_info = get_user_info_from_request(event)
        # if not user_info:
        #     return {
        #         'statusCode': 401,
        #         'headers': {
        #             'Content-Type': 'application/json',
        #             'Access-Control-Allow-Origin': '*',
        #             'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
        #             'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
        #             'Access-Control-Max-Age': '86400',
        #             'Access-Control-Allow-Credentials': 'true',
        #             'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
        #         },
        #         'body': json.dumps({
        #             'error': 'User not authenticated'
        #         })
        #     }

        # Generate book ID from filename
        book_id = filename.replace('.txt', '').replace('.md', '').replace('.pdf', '')
        book_id = book_id.replace(' ', '-').lower()
        
        # Upload file to S3
        s3_key = f"books/{filename}"
        try:
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType='text/plain'
            )
            print(f"Uploaded file to S3: {s3_key}")
        except Exception as e:
            print(f"Error uploading to S3: {e}")
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
                    'error': f'Failed to upload file to S3: {str(e)}'
                })
            }
        
        # Process embeddings asynchronously to avoid timeout
        content_size = len(file_content)
        print(f"Processing book ({content_size} chars) asynchronously")
        
        # Trigger async processing
        try:
            trigger_processing_lambda(book_id, s3_key)
            successful_chunks = -1  # -1 indicates async processing
            print(f"Triggered async processing for {book_id}")
        except Exception as e:
            print(f"Error triggering async processing: {e}")
            successful_chunks = 0
        
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
            'body': json.dumps({
                'message': 'File uploaded successfully',
                'book_id': book_id,
                'filename': filename,
                's3_key': s3_key,
                'processing_mode': 'async' if successful_chunks == -1 else 'sync',
                'chunks_processed': successful_chunks if successful_chunks >= 0 else 'processing',
                'file_size': content_size
            })
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