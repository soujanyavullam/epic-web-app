#!/usr/bin/env python3
"""
Test script for S3 Vectors Lambda functions
"""

import json
import boto3
import time

def test_s3_vectors_functions():
    """Test the S3 Vectors Lambda functions"""
    
    lambda_client = boto3.client('lambda')
    
    # Test data
    test_upload_event = {
        'httpMethod': 'POST',
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'filename': 'test-book.txt',
            'content': 'This is a test book content for S3 Vectors testing.'
        })
    }
    
    test_query_event = {
        'httpMethod': 'POST',
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'question': 'What is this book about?',
            'book_title': 'test-book'
        })
    }
    
    print("🧪 Testing S3 Vectors Lambda Functions")
    print("=" * 50)
    
    # Test 1: Upload Function
    print("\n1. Testing epic-upload-s3-vectors...")
    try:
        response = lambda_client.invoke(
            FunctionName='epic-upload-s3-vectors',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_upload_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"✅ Upload function response: {result}")
        
    except Exception as e:
        print(f"❌ Upload function error: {e}")
    
    # Test 2: Query Function
    print("\n2. Testing epic-query-s3-vectors...")
    try:
        response = lambda_client.invoke(
            FunctionName='epic-query-s3-vectors',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_query_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"✅ Query function response: {result}")
        
    except Exception as e:
        print(f"❌ Query function error: {e}")
    
    # Test 3: Search Function
    print("\n3. Testing epic-s3-vectors-search...")
    try:
        test_search_event = {
            'httpMethod': 'POST',
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'action': 'list_buckets'
            })
        }
        
        response = lambda_client.invoke(
            FunctionName='epic-s3-vectors-search',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_search_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"✅ Search function response: {result}")
        
    except Exception as e:
        print(f"❌ Search function error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 S3 Vectors function testing completed!")

if __name__ == "__main__":
    test_s3_vectors_functions() 