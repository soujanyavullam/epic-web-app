import json
import boto3
import os
from typing import Dict, Any, List
from datetime import datetime

# Initialize S3 Vectors client
s3_vectors_client = boto3.client('s3vectors')

# Configuration
VECTOR_BUCKET_NAME = 'epic-vector-bucket'  # Your vector bucket name
VECTOR_INDEX_NAME = 'book-embeddings-index'

def create_vector_bucket():
    """Create a vector bucket for storing embeddings"""
    try:
        response = s3_vectors_client.create_bucket(
            Bucket=VECTOR_BUCKET_NAME,
            CreateBucketConfiguration={
                'LocationConstraint': 'us-east-1'
            }
        )
        print(f"Created vector bucket: {VECTOR_BUCKET_NAME}")
        return True
    except Exception as e:
        print(f"Error creating vector bucket: {e}")
        return False

def create_vector_index():
    """Create a vector index within the vector bucket"""
    try:
        response = s3_vectors_client.create_index(
            Bucket=VECTOR_BUCKET_NAME,
            IndexName=VECTOR_INDEX_NAME,
            IndexConfiguration={
                'VectorConfiguration': {
                    'Dimension': 1536,  # Titan Embed Text v2 dimension
                    'MetricType': 'COSINE'
                }
            }
        )
        print(f"Created vector index: {VECTOR_INDEX_NAME}")
        return True
    except Exception as e:
        print(f"Error creating vector index: {e}")
        return False

def upload_vector_embedding(vector_id: str, embedding: List[float], metadata: Dict[str, Any]):
    """Upload a vector embedding to S3 Vectors"""
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
        print(f"Uploaded vector: {vector_id}")
        return True
    except Exception as e:
        print(f"Error uploading vector {vector_id}: {e}")
        return False

def search_vectors_s3(query_embedding: List[float], book_title: str, k: int = 5):
    """Search vectors using S3 Vectors similarity search"""
    try:
        # Create search query
        search_request = {
            'Bucket': VECTOR_BUCKET_NAME,
            'IndexName': VECTOR_INDEX_NAME,
            'SearchConfiguration': {
                'VectorSearchConfiguration': {
                    'QueryVector': query_embedding,
                    'K': k,
                    'FilterExpression': f"metadata.book_title = '{book_title}'"
                }
            }
        }
        
        response = s3_vectors_client.search(**search_request)
        
        # Process results
        results = []
        for hit in response.get('Hits', []):
            results.append({
                'id': hit['Id'],
                'score': hit['Score'],
                'metadata': hit.get('Metadata', {})
            })
        
        print(f"S3 Vectors search returned {len(results)} results")
        return results
        
    except Exception as e:
        print(f"Error in S3 Vectors search: {e}")
        return []

def batch_upload_embeddings(book_id: str, embeddings: List[Dict[str, Any]]):
    """Batch upload embeddings for a book"""
    try:
        successful_uploads = 0
        
        for i, embedding_data in enumerate(embeddings):
            vector_id = f"{book_id}-chunk-{i:04d}"
            
            # Extract embedding and metadata
            embedding_vector = embedding_data.get('embedding', [])
            metadata = {
                'book_title': book_id,
                'chunk_id': f"{i:04d}",
                'text': embedding_data.get('text', ''),
                'token_count': embedding_data.get('token_count', 0),
                'upload_timestamp': datetime.utcnow().isoformat()
            }
            
            if upload_vector_embedding(vector_id, embedding_vector, metadata):
                successful_uploads += 1
        
        print(f"Successfully uploaded {successful_uploads}/{len(embeddings)} embeddings for {book_id}")
        return successful_uploads
        
    except Exception as e:
        print(f"Error in batch upload: {e}")
        return 0

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for S3 Vectors operations
    """
    try:
        print(f"Received S3 Vectors request: {json.dumps(event)}")
        
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

        # Parse request
        body = json.loads(event.get('body', '{}'))
        operation = body.get('operation')
        
        if operation == 'search':
            # Vector search operation
            query_embedding = body.get('query_embedding', [])
            book_title = body.get('book_title', '')
            k = body.get('k', 5)
            
            results = search_vectors_s3(query_embedding, book_title, k)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'results': results,
                    'count': len(results)
                })
            }
            
        elif operation == 'upload':
            # Upload embeddings operation
            book_id = body.get('book_id', '')
            embeddings = body.get('embeddings', [])
            
            successful_uploads = batch_upload_embeddings(book_id, embeddings)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'message': f'Successfully uploaded {successful_uploads} embeddings',
                    'book_id': book_id,
                    'uploaded_count': successful_uploads
                })
            }
            
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Invalid operation. Supported operations: search, upload'
                })
            }
            
    except Exception as e:
        print(f"Error in S3 Vectors handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        } 