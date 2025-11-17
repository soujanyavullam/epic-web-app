import json
import boto3
import os
from typing import Dict, Any, List
from datetime import datetime

# Initialize AWS clients
s3 = boto3.client('s3')
s3_vectors_client = boto3.client('s3vectors')

# Configuration
VECTOR_BUCKET_NAME = 'epic-vector-bucket'
VECTOR_INDEX_NAME = 'book-embeddings-index'
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'epic-s3-bucket-ramayana')

def list_books_from_s3_vectors() -> List[Dict[str, Any]]:
    """List books from S3 Vectors."""
    try:
        print(f"Calling list_vectors with bucket: {VECTOR_BUCKET_NAME}, index: {VECTOR_INDEX_NAME}")
        response = s3_vectors_client.list_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            maxResults=1000
        )
        
        print(f"list_vectors response: {json.dumps(response, default=str)}")
        
        vectors = response.get('vectors', [])
        print(f"Found {len(vectors)} vectors in response")
        
        books = {}
        
        for vector in vectors:
            print(f"Processing vector: {vector}")
            # Extract book title from vector key (e.g., "computerscienceone-0256" -> "computerscienceone")
            vector_key = vector.get('key', '')
            print(f"Vector key: {vector_key}")
            
            if '-' in vector_key:
                # Find the last dash before the chunk number (e.g., "woman-in-science-0001" -> "woman-in-science")
                parts = vector_key.split('-')
                if len(parts) >= 3:
                    # Reconstruct the full book title (everything except the last part which is the chunk number)
                    book_title = '-'.join(parts[:-1])
                else:
                    # Fallback for simple cases like "computerscienceone-0256"
                    book_title = parts[0]
                print(f"Extracted book title: {book_title}")
                
                if book_title not in books:
                    books[book_title] = {
                        'title': book_title,
                        'filename': f"{book_title}.txt",
                        'upload_date': datetime.utcnow().isoformat(),
                        'chunk_count': 1,
                        'status': 'processed'
                    }
                else:
                    books[book_title]['chunk_count'] += 1
            else:
                print(f"No dash found in vector key: {vector_key}")
        
        book_list = list(books.values())
        print(f"Found {len(book_list)} books in S3 Vectors")
        return book_list
        
    except Exception as e:
        print(f"Error listing books from S3 Vectors: {e}")
        return []

def list_books_from_s3_fallback() -> List[Dict[str, Any]]:
    """Fallback method to list books from S3 bucket."""
    try:
        print("Listing books from S3 bucket (fallback)")
        
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix='books/',
            MaxKeys=1000
        )
        
        books = []
        for obj in response.get('Contents', []):
            if obj['Key'].endswith(('.txt', '.md', '.pdf')):
                filename = obj['Key'].split('/')[-1]
                book_title = filename.replace('.txt', '').replace('.md', '').replace('.pdf', '')
                
                books.append({
                    'title': book_title,
                    'filename': filename,
                    'upload_date': obj['LastModified'].isoformat(),
                    'file_size': obj['Size'],
                    'chunks_count': 0,  # Unknown for S3-only books
                    'status': 'uploaded'  # May not be processed yet
                })
        
        # Sort by title
        books.sort(key=lambda x: x['title'].lower())
        print(f"Found {len(books)} books in S3 bucket")
        return books
        
    except Exception as e:
        print(f"Error listing books from S3 bucket: {e}")
        return []

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for listing available books.
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
        
        # Get books from S3 Vectors only (no fallback to S3 bucket)
        books = list_books_from_s3_vectors()
        
        # Prepare response
        response_data = {
            'books': books,
            'total_count': len(books),
            'timestamp': datetime.utcnow().isoformat(),
            'source': 's3_vectors'  # Always S3 Vectors since no fallback
        }
        
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
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error in list books handler: {e}")
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