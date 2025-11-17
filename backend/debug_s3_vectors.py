#!/usr/bin/env python3
"""
Debug script to test S3 Vectors API and understand data structure
"""

import boto3
import json
from typing import Dict, Any, List

# Initialize S3 Vectors client
s3_vectors_client = boto3.client('s3vectors')

# Configuration
VECTOR_BUCKET_NAME = 'epic-vector-bucket'
VECTOR_INDEX_NAME = 'book-embeddings-index'

def test_s3_vectors_search():
    """Test S3 Vectors search to see what data is returned"""
    try:
        print("Testing S3 Vectors search...")
        
        # Test with a simple query (no embedding, just to see structure)
        response = s3_vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={'float32': [0.1] * 1536},  # Dummy embedding
            topK=3,
            returnMetadata=True
        )
        
        print(f"Search response: {json.dumps(response, default=str, indent=2)}")
        
        vectors = response.get('vectors', [])
        if vectors:
            print(f"\nFound {len(vectors)} vectors")
            for i, vector in enumerate(vectors):
                print(f"\nVector {i+1}:")
                print(f"  Key: {vector.get('key', 'N/A')}")
                print(f"  Score: {vector.get('score', 'N/A')}")
                print(f"  Metadata keys: {list(vector.get('metadata', {}).keys())}")
                
                metadata = vector.get('metadata', {})
                if 'text' in metadata:
                    print(f"  Text preview: {metadata['text'][:100]}...")
                else:
                    print(f"  No text in metadata")
        else:
            print("No vectors returned")
            
    except Exception as e:
        print(f"Error in search: {e}")

def test_s3_vectors_get():
    """Test S3 Vectors get_vectors to see full data structure"""
    try:
        print("\nTesting S3 Vectors get_vectors...")
        
        # First get a list of vectors to find a key
        list_response = s3_vectors_client.list_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            maxResults=5
        )
        
        vectors = list_response.get('vectors', [])
        if vectors:
            test_key = vectors[0].get('key', '')
            print(f"Testing get_vectors with key: {test_key}")
            
            get_response = s3_vectors_client.get_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=VECTOR_INDEX_NAME,
                keys=[test_key]
            )
            
            print(f"Get response: {json.dumps(get_response, default=str, indent=2)}")
            
            if get_response.get('vectors'):
                vector = get_response['vectors'][0]
                print(f"\nRetrieved vector:")
                print(f"  Key: {vector.get('key', 'N/A')}")
                print(f"  Metadata keys: {list(vector.get('metadata', {}).keys())}")
                
                metadata = vector.get('metadata', {})
                if 'text' in metadata:
                    print(f"  Text preview: {metadata['text'][:100]}...")
                else:
                    print(f"  No text in metadata")
        else:
            print("No vectors found to test get_vectors")
            
    except Exception as e:
        print(f"Error in get_vectors: {e}")

def test_s3_vectors_list():
    """Test S3 Vectors list_vectors to see what's available"""
    try:
        print("\nTesting S3 Vectors list_vectors...")
        
        response = s3_vectors_client.list_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            maxResults=10
        )
        
        print(f"List response: {json.dumps(response, default=str, indent=2)}")
        
        vectors = response.get('vectors', [])
        if vectors:
            print(f"\nFound {len(vectors)} vectors")
            for i, vector in enumerate(vectors[:5]):
                print(f"\nVector {i+1}:")
                print(f"  Key: {vector.get('key', 'N/A')}")
                print(f"  Size: {vector.get('size', 'N/A')}")
                print(f"  LastModified: {vector.get('lastModified', 'N/A')}")
        else:
            print("No vectors found")
            
    except Exception as e:
        print(f"Error in list_vectors: {e}")

if __name__ == "__main__":
    print("S3 Vectors Debug Script")
    print("=" * 50)
    
    test_s3_vectors_list()
    test_s3_vectors_search()
    test_s3_vectors_get()
    
    print("\nDebug complete!") 