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
        response = s3_vectors_client.put_object(
            Bucket=VECTOR_BUCKET_NAME,
            IndexName=VECTOR_INDEX_NAME,
            Key=vector_id,
            Body=json.dumps({
                'vector': embedding,
                'metadata': metadata
            }),
            ContentType='application/json'
        )
        print(f"Uploaded vector to S3 Vectors: {vector_id}")
        return True
    except Exception as e:
        print(f"Error uploading vector {vector_id} to S3 Vectors: {e}")
        return False

def process_chunk_for_s3_vectors(args: tuple) -> Dict[str, Any]:
    """Process a single chunk and upload to S3 Vectors."""
    chunk, book_id = args
    try:
        embedding = get_embedding(chunk['text'])
        
        # Prepare metadata for S3 Vectors
        metadata = {
            'book_title': book_id,
            'chunk_id': chunk['chunk_id'],
            'text': chunk['text'],
            'token_count': chunk['token_count'],
            'upload_timestamp': datetime.utcnow().isoformat()
        }
        
        vector_id = f"{book_id}-{chunk['chunk_id']}"
        
        # Upload to S3 Vectors
        success = upload_vector_to_s3_vectors(vector_id, embedding, metadata)
        
        if success:
            return {
                'vector_id': vector_id,
                'book_title': book_id,
                'chunk_id': chunk['chunk_id'],
                'status': 'success'
            }
        else:
            return {
                'vector_id': vector_id,
                'book_title': book_id,
                'chunk_id': chunk['chunk_id'],
                'status': 'failed'
            }
            
    except Exception as e:
        print(f"Error processing chunk {chunk['chunk_id']} of {book_id}: {e}")
        return {
            'vector_id': f"{book_id}-{chunk['chunk_id']}",
            'book_title': book_id,
            'chunk_id': chunk['chunk_id'],
            'status': 'failed',
            'error': str(e)
        }

def ingest_book_s3_vectors(book_id: str, book_text: str) -> int:
    """Ingest a book into S3 Vectors with embeddings using parallel processing."""
    try:
        print(f"Starting S3 Vectors ingestion for book: {book_id}")
        
        # Split book into chunks
        chunks = chunk_text(book_text, book_id)
        print(f"Created {len(chunks)} chunks for {book_id}")
        
        # Process chunks in parallel
        successful_chunks = 0
        failed_chunks = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(process_chunk_for_s3_vectors, (chunk, book_id)): chunk 
                for chunk in chunks
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                if result['status'] == 'success':
                    successful_chunks += 1
                else:
                    failed_chunks += 1
                    print(f"Failed to process chunk: {result}")
        
        print(f"S3 Vectors ingestion completed for {book_id}: {successful_chunks} successful, {failed_chunks} failed")
        return successful_chunks
        
    except Exception as e:
        print(f"Error during S3 Vectors ingestion for {book_id}: {e}")
        raise

def trigger_processing_lambda(book_id: str, s3_key: str):
    """Trigger asynchronous processing for large files."""
    try:
        payload = {
            'book_id': book_id,
            's3_key': s3_key,
            'processing_type': 's3_vectors'
        }
        
        lambda_client.invoke(
            FunctionName='epic-upload-function',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        print(f"Triggered async processing for {book_id}")
    except Exception as e:
        print(f"Error triggering async processing: {e}")

def process_book_from_s3_s3_vectors(book_id: str, s3_key: str) -> int:
    """Process a book from S3 and store embeddings in S3 Vectors."""
    try:
        print(f"Processing book from S3: {s3_key}")
        
        # Download file from S3
        response = s3.get_object(Bucket='epic-s3-bucket-ramayana', Key=s3_key)
        file_content = response['Body'].read()
        
        # Decode content
        text_content = decode_content(file_content)
        print(f"Downloaded and decoded {len(text_content)} characters")
        
        # Ingest into S3 Vectors
        successful_chunks = ingest_book_s3_vectors(book_id, text_content)
        
        return successful_chunks
        
    except Exception as e:
        print(f"Error processing book from S3: {e}")
        raise

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

        # Get the request body
        body = event.get('body', '')
        print(f"Body type: {type(body)}, isBase64Encoded: {event.get('isBase64Encoded', False)}")
        
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
            print(f"Decoded base64 body length: {len(body)}")
        
        # Parse the request
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE'
                },
                'body': json.dumps({
                    'error': 'Invalid JSON in request body'
                })
            }
        
        # Extract file data
        file_content = request_data.get('file_content', '')
        filename = request_data.get('filename', '')
        
        if not file_content or not filename:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE'
                },
                'body': json.dumps({
                    'error': 'Missing file_content or filename'
                })
            }
        
        # Generate book ID from filename
        book_id = filename.replace('.txt', '').replace('.md', '').replace('.pdf', '')
        book_id = book_id.replace(' ', '-').lower()
        
        # Upload file to S3
        s3_key = f"books/{filename}"
        try:
            s3.put_object(
                Bucket='epic-s3-bucket-ramayana',
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
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE'
                },
                'body': json.dumps({
                    'error': f'Failed to upload file to S3: {str(e)}'
                })
            }
        
        # Process embeddings based on file size
        content_size = len(file_content)
        if content_size > 50000:  # If book is larger than 50KB, process asynchronously
            print(f"Large book detected ({content_size} chars), triggering async processing")
            trigger_processing_lambda(book_id, s3_key)
            successful_chunks = 0  # Will be processed asynchronously
        else:
            # Process small books immediately
            print(f"Small book detected ({content_size} chars), processing immediately")
            try:
                successful_chunks = ingest_book_s3_vectors(book_id, file_content)
                print(f"Successfully processed {successful_chunks} chunks for {book_id}")
            except Exception as e:
                print(f"Error during S3 Vectors embedding generation: {e}")
                successful_chunks = 0
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE'
            },
            'body': json.dumps({
                'message': 'File uploaded successfully',
                'book_id': book_id,
                'filename': filename,
                's3_key': s3_key,
                'processing_mode': 'async' if content_size > 50000 else 'sync',
                'chunks_processed': successful_chunks,
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
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        } 