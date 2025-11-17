#!/usr/bin/env python3
"""
Minimal S3 Vectors Test Script
Run this in your Lambda environment to debug the metadata issue.
"""

import json
import boto3

def test_s3_vectors_search():
    """Test S3 Vectors search to see what's returned."""
    
    # Initialize client
    s3_vectors_client = boto3.client('s3vectors')
    
    # Configuration
    VECTOR_BUCKET_NAME = 'epic-vector-bucket'
    VECTOR_INDEX_NAME = 'book-embeddings-index'
    
    try:
        print("Testing S3 Vectors search...")
        
        # Test 1: Search without filter first
        print("\n1. Testing search without filter...")
        response = s3_vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={'float32': [0.1] * 1536},  # Dummy embedding
            topK=3,
            returnMetadata=True
        )
        
        print(f"Response keys: {list(response.keys())}")
        vectors = response.get('vectors', [])
        print(f"Number of vectors returned: {len(vectors)}")
        
        if vectors:
            print("\nFirst vector structure:")
            first_vector = vectors[0]
            print(f"  Keys: {list(first_vector.keys())}")
            
            if 'metadata' in first_vector:
                metadata = first_vector['metadata']
                print(f"  Metadata keys: {list(metadata.keys())}")
                if 'text' in metadata:
                    print(f"  Text preview: {metadata['text'][:100]}...")
                else:
                    print(f"  No text in metadata")
            else:
                print(f"  No metadata field")
        
        # Test 2: Search with filter
        print("\n2. Testing search with filter...")
        filter_expression = "metadata.book_title = 'woman-in-science'"
        print(f"Filter: {filter_expression}")
        
        response_filtered = s3_vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={'float32': [0.1] * 1536},
            topK=3,
            filter=filter_expression,
            returnMetadata=True
        )
        
        vectors_filtered = response_filtered.get('vectors', [])
        print(f"Filtered results: {len(vectors_filtered)}")
        
        if vectors_filtered:
            print("\nFirst filtered vector:")
            first_filtered = vectors_filtered[0]
            print(f"  Keys: {list(first_filtered.keys())}")
            
            if 'metadata' in first_filtered:
                metadata = first_filtered['metadata']
                print(f"  Metadata keys: {list(metadata.keys())}")
                if 'text' in metadata:
                    print(f"  Text preview: {metadata['text'][:100]}...")
                else:
                    print(f"  No text in metadata")
            else:
                print(f"  No metadata field")
        
        # Test 3: Try to get specific vector
        print("\n3. Testing get_vectors...")
        if vectors:
            test_key = vectors[0].get('key', '')
            if test_key:
                print(f"Getting vector: {test_key}")
                
                vector_data = s3_vectors_client.get_vectors(
                    vectorBucketName=VECTOR_BUCKET_NAME,
                    indexName=VECTOR_INDEX_NAME,
                    keys=[test_key]
                )
                
                if vector_data.get('vectors'):
                    full_vector = vector_data['vectors'][0]
                    print(f"  Full vector keys: {list(full_vector.keys())}")
                    
                    if 'metadata' in full_vector:
                        metadata = full_vector['metadata']
                        print(f"  Metadata keys: {list(metadata.keys())}")
                        if 'text' in metadata:
                            print(f"  Text preview: {metadata['text'][:100]}...")
                        else:
                            print(f"  No text in metadata")
                    else:
                        print(f"  No metadata field")
                else:
                    print(f"  No vector data returned")
        
        # Test 4: List vectors to see what's available
        print("\n4. Testing list_vectors...")
        try:
            list_response = s3_vectors_client.list_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=VECTOR_INDEX_NAME,
                maxResults=5
            )
            
            list_vectors = list_response.get('vectors', [])
            print(f"List vectors returned: {len(list_vectors)}")
            
            if list_vectors:
                print("\nFirst listed vector:")
                first_listed = list_vectors[0]
                print(f"  Keys: {list(first_listed.keys())}")
                print(f"  Key: {first_listed.get('key', 'N/A')}")
                print(f"  Size: {first_listed.get('size', 'N/A')}")
        except Exception as e:
            print(f"  List vectors error: {e}")
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_s3_vectors_search() 