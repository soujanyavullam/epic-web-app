import json
import boto3
import os
from typing import Dict, Any, List

s3 = boto3.client('s3')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for listing available books from S3.
    """
    try:
        # Get the S3 bucket name from environment variable
        bucket_name = os.environ.get('BOOKS_BUCKET', 'epic-s3-bucket-ramayana')
        
        # List objects in the bucket
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix='',  # List all objects
            Delimiter='/'  # Group by folders
        )
        
        books = []
        
        # Process the objects
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                
                # Only include .txt files
                if key.endswith('.txt'):
                    # Extract book title from filename (remove .txt extension)
                    book_title = key.replace('.txt', '')
                    
                    books.append({
                        'title': book_title,
                        'filename': key,
                        'lastModified': obj['LastModified'].isoformat(),
                        'size': obj['Size']
                    })
        
        # Return the data directly for API Gateway integration
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Max-Age': '86400'
            },
            'body': json.dumps({
                'books': books,
                'count': len(books)
            })
        }
        
    except Exception as e:
        print(f"Error listing books: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Max-Age': '86400'
            },
            'body': json.dumps({
                'error': 'Failed to list books',
                'message': str(e)
            })
        } 