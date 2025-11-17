#!/usr/bin/env python3
"""
S3 Vectors Debug Test Function
Call this to see exactly what S3 Vectors returns.
"""

import json
import boto3

def test_s3_vectors_response():
    """Test what S3 Vectors actually returns."""
    
    # Initialize client
    s3_vectors_client = boto3.client('s3vectors')
    
    # Configuration
    VECTOR_BUCKET_NAME = 'epic-vector-bucket'
    VECTOR_INDEX_NAME = 'book-embeddings-index'
    
    print("🔍 S3 Vectors Debug Test")
    print("=" * 50)
    
    try:
        # Test 1: Basic search
        print("\n1️⃣ Testing basic search...")
        response = s3_vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={'float32': [0.1] * 1536},
            topK=2,
            returnMetadata=True
        )
        
        print(f"✅ Search successful")
        print(f"Response keys: {list(response.keys())}")
        
        vectors = response.get('vectors', [])
        print(f"Number of vectors: {len(vectors)}")
        
        if vectors:
            print(f"\n📊 FIRST VECTOR ANALYSIS:")
            first = vectors[0]
            print(f"   Type: {type(first)}")
            print(f"   Keys: {list(first.keys())}")
            print(f"   Full content: {json.dumps(first, default=str, indent=2)}")
            
            # Check metadata specifically
            if 'metadata' in first:
                metadata = first['metadata']
                print(f"\n   📋 METADATA FOUND:")
                print(f"      Type: {type(metadata)}")
                print(f"      Keys: {list(metadata.keys())}")
                print(f"      Content: {json.dumps(metadata, default=str, indent=2)}")
                
                if 'text' in metadata:
                    text = metadata['text']
                    print(f"      Text type: {type(text)}")
                    print(f"      Text length: {len(text) if text else 0}")
                    print(f"      Text preview: {text[:200] if text else 'None'}...")
                else:
                    print(f"      ❌ NO TEXT IN METADATA")
            else:
                print(f"\n   ❌ NO METADATA FIELD")
        
        # Test 2: Search with filter
        print(f"\n2️⃣ Testing filtered search...")
        filter_response = s3_vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={'float32': [0.1] * 1536},
            topK=2,
            filter="metadata.book_title = 'woman-in-science'",
            returnMetadata=True
        )
        
        filtered_vectors = filter_response.get('vectors', [])
        print(f"Filtered results: {len(filtered_vectors)}")
        
        if filtered_vectors:
            print(f"\n📊 FIRST FILTERED VECTOR:")
            first_filtered = filtered_vectors[0]
            print(f"   Keys: {list(first_filtered.keys())}")
            
            if 'metadata' in first_filtered:
                metadata = first_filtered['metadata']
                print(f"   Metadata keys: {list(metadata.keys())}")
                if 'text' in metadata:
                    print(f"   Text preview: {metadata['text'][:100]}...")
                else:
                    print(f"   ❌ No text in filtered metadata")
            else:
                print(f"   ❌ No metadata in filtered result")
        
        # Test 3: Get specific vector
        print(f"\n3️⃣ Testing get_vectors...")
        if vectors:
            test_key = vectors[0].get('key', '')
            if test_key:
                print(f"Getting vector: {test_key}")
                
                get_response = s3_vectors_client.get_vectors(
                    vectorBucketName=VECTOR_BUCKET_NAME,
                    indexName=VECTOR_INDEX_NAME,
                    keys=[test_key]
                )
                
                if get_response.get('vectors'):
                    full_vector = get_response['vectors'][0]
                    print(f"   Full vector keys: {list(full_vector.keys())}")
                    
                    if 'metadata' in full_vector:
                        metadata = full_vector['metadata']
                        print(f"   Metadata keys: {list(metadata.keys())}")
                        if 'text' in metadata:
                            print(f"   Text preview: {metadata['text'][:100]}...")
                        else:
                            print(f"   ❌ No text in get_vectors metadata")
                    else:
                        print(f"   ❌ No metadata in get_vectors result")
        
        print(f"\n🎯 SUMMARY:")
        print(f"   Basic search returned: {len(vectors)} vectors")
        print(f"   Filtered search returned: {len(filtered_vectors)} vectors")
        print(f"   Metadata present in basic: {'Yes' if vectors and 'metadata' in vectors[0] else 'No'}")
        print(f"   Metadata present in filtered: {'Yes' if filtered_vectors and 'metadata' in filtered_vectors[0] else 'No'}")
        
        if vectors and 'metadata' in vectors[0]:
            metadata = vectors[0]['metadata']
            text_present = 'text' in metadata
            print(f"   Text in metadata: {'Yes' if text_present else 'No'}")
            
            if text_present:
                text_length = len(metadata['text']) if metadata['text'] else 0
                print(f"   Text length: {text_length} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_s3_vectors_response() 