#!/usr/bin/env python3
"""
Metadata Verification Test
Check what's actually stored in S3 Vectors metadata.
"""

import json
import boto3

def verify_s3_vectors_metadata():
    """Verify what metadata is actually stored in S3 Vectors."""
    
    # Initialize client
    s3_vectors_client = boto3.client('s3vectors')
    
    # Configuration
    VECTOR_BUCKET_NAME = 'epic-vector-bucket'
    VECTOR_INDEX_NAME = 'book-embeddings-index'
    
    print("🔍 S3 Vectors Metadata Verification")
    print("=" * 50)
    
    try:
        # Step 1: List all vectors to see what's available
        print("\n1️⃣ Listing all vectors...")
        list_response = s3_vectors_client.list_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            maxResults=10
        )
        
        vectors = list_response.get('vectors', [])
        print(f"Found {len(vectors)} vectors")
        
        if not vectors:
            print("❌ No vectors found in the index!")
            return
        
        # Step 2: Check a few specific vectors
        print(f"\n2️⃣ Checking specific vectors...")
        
        for i, vector_info in enumerate(vectors[:3]):
            key = vector_info.get('key', '')
            print(f"\n   Vector {i+1}: {key}")
            
            # Get the full vector data
            try:
                get_response = s3_vectors_client.get_vectors(
                    vectorBucketName=VECTOR_BUCKET_NAME,
                    indexName=VECTOR_INDEX_NAME,
                    keys=[key]
                )
                
                if get_response.get('vectors'):
                    full_vector = get_response['vectors'][0]
                    print(f"     ✅ Retrieved vector data")
                    print(f"     Keys: {list(full_vector.keys())}")
                    
                    # Check metadata
                    if 'metadata' in full_vector:
                        metadata = full_vector['metadata']
                        print(f"     📋 Metadata found:")
                        print(f"        Keys: {list(metadata.keys())}")
                        
                        # Check each metadata field
                        for meta_key, meta_value in metadata.items():
                            if meta_key == 'text':
                                if meta_value:
                                    print(f"        Text: {len(meta_value)} characters")
                                    print(f"        Preview: {meta_value[:100]}...")
                                else:
                                    print(f"        Text: EMPTY or None")
                            else:
                                print(f"        {meta_key}: {meta_value}")
                    else:
                        print(f"     ❌ NO METADATA FIELD")
                    
                    # Check data
                    if 'data' in full_vector:
                        data = full_vector['data']
                        print(f"     📊 Data keys: {list(data.keys())}")
                        if 'float32' in data:
                            embedding = data['float32']
                            print(f"        Embedding: {len(embedding)} dimensions")
                        else:
                            print(f"        No float32 data")
                    else:
                        print(f"     ❌ NO DATA FIELD")
                        
                else:
                    print(f"     ❌ No vector data returned")
                    
            except Exception as e:
                print(f"     ❌ Error getting vector: {e}")
        
        # Step 3: Test search to see what's returned
        print(f"\n3️⃣ Testing search response...")
        
        # Try to find woman-in-science vectors
        search_response = s3_vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={'float32': [0.1] * 1536},
            topK=3,
            filter="metadata.book_title = 'woman-in-science'",
            returnMetadata=True
        )
        
        search_vectors = search_response.get('vectors', [])
        print(f"Search returned {len(search_vectors)} vectors")
        
        if search_vectors:
            print(f"\n   First search result:")
            first_search = search_vectors[0]
            print(f"     Keys: {list(first_search.keys())}")
            
            if 'metadata' in first_search:
                search_metadata = first_search['metadata']
                print(f"     Metadata keys: {list(search_metadata.keys())}")
                
                for meta_key, meta_value in search_metadata.items():
                    if meta_key == 'text':
                        if meta_value:
                            print(f"        Text: {len(meta_value)} characters")
                            print(f"        Preview: {meta_value[:100]}...")
                        else:
                            print(f"        Text: EMPTY or None")
                    else:
                        print(f"        {meta_key}: {meta_value}")
            else:
                print(f"     ❌ NO METADATA IN SEARCH RESULT")
        
        # Step 4: Summary
        print(f"\n🎯 METADATA VERIFICATION SUMMARY:")
        print(f"   Total vectors in index: {len(vectors)}")
        print(f"   Vectors checked: {min(3, len(vectors))}")
        print(f"   Search results: {len(search_vectors)}")
        
        # Check if we found any text content
        text_found = False
        for vector_info in vectors[:3]:
            key = vector_info.get('key', '')
            try:
                get_response = s3_vectors_client.get_vectors(
                    vectorBucketName=VECTOR_BUCKET_NAME,
                    indexName=VECTOR_INDEX_NAME,
                    keys=[key]
                )
                
                if get_response.get('vectors'):
                    full_vector = get_response['vectors'][0]
                    if 'metadata' in full_vector:
                        metadata = full_vector['metadata']
                        if 'text' in metadata and metadata['text']:
                            text_found = True
                            break
            except:
                continue
        
        print(f"   Text content found: {'✅ YES' if text_found else '❌ NO'}")
        
        if not text_found:
            print(f"\n🚨 CRITICAL ISSUE DETECTED:")
            print(f"   No text content found in S3 Vectors metadata!")
            print(f"   This means the upload process failed to store text content.")
            print(f"   Check the upload logs and re-upload the book content.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_s3_vectors_metadata() 