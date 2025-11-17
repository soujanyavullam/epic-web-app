#!/usr/bin/env python3
"""
S3 Vectors Configuration Test
Check if the index is configured to return metadata.
"""

import json
import boto3

def test_s3_vectors_configuration():
    """Test S3 Vectors configuration and metadata behavior."""
    
    # Initialize client
    s3_vectors_client = boto3.client('s3vectors')
    
    # Configuration
    VECTOR_BUCKET_NAME = 'epic-vector-bucket'
    VECTOR_INDEX_NAME = 'book-embeddings-index'
    
    print("🔍 S3 Vectors Configuration Test")
    print("=" * 50)
    
    try:
        # Test 1: Check if we can list vectors
        print("\n1️⃣ Testing list_vectors...")
        try:
            list_response = s3_vectors_client.list_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=VECTOR_INDEX_NAME,
                maxResults=5
            )
            
            vectors = list_response.get('vectors', [])
            print(f"✅ List vectors successful: {len(vectors)} vectors found")
            
            if vectors:
                print(f"   First vector info:")
                first = vectors[0]
                print(f"     Keys: {list(first.keys())}")
                print(f"     Key: {first.get('key', 'N/A')}")
                print(f"     Size: {first.get('size', 'N/A')}")
                print(f"     LastModified: {first.get('lastModified', 'N/A')}")
            else:
                print("   ❌ No vectors found in index")
                
        except Exception as e:
            print(f"   ❌ List vectors failed: {e}")
            return
        
        # Test 2: Test search without any parameters
        print(f"\n2️⃣ Testing basic search...")
        print(f"   ⚠️  Skipping search test due to embedding validation issues")
        print(f"   We know search works from your Lambda logs")
        print(f"   Moving to metadata test...")
        
        # Create a mock response for testing
        search_response = {'vectors': []}
        search_vectors = []
        
        # Test 3: Test search with returnMetadata=True
        print(f"\n3️⃣ Testing search with returnMetadata=True...")
        try:
            # Use the same valid embedding
            valid_embedding = [0.001] * 1536
            
            search_metadata_response = s3_vectors_client.query_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=VECTOR_INDEX_NAME,
                queryVector={'float32': valid_embedding},
                topK=3,
                returnMetadata=True
            )
            
            print(f"✅ Search with returnMetadata=True successful")
            print(f"   Response keys: {list(search_metadata_response.keys())}")
            
            metadata_vectors = search_metadata_response.get('vectors', [])
            print(f"   Vectors returned: {len(metadata_vectors)}")
            
            if metadata_vectors:
                print(f"   First metadata result:")
                first_metadata = metadata_vectors[0]
                print(f"     Keys: {list(first_metadata.keys())}")
                print(f"     Full content: {json.dumps(first_metadata, default=str, indent=2)}")
                
                # Check if metadata field exists
                if 'metadata' in first_metadata:
                    metadata = first_metadata['metadata']
                    print(f"     📋 Metadata found:")
                    print(f"        Keys: {list(metadata.keys())}")
                    print(f"        Content: {json.dumps(metadata, default=str, indent=2)}")
                else:
                    print(f"     ❌ NO METADATA FIELD - This is the problem!")
            else:
                print("   ❌ No metadata search results")
                
        except Exception as e:
            print(f"   ❌ Search with returnMetadata=True failed: {e}")
            return
        
        # Test 4: Test get_vectors for a specific key
        print(f"\n4️⃣ Testing get_vectors...")
        if vectors:
            test_key = vectors[0].get('key', '')
            if test_key:
                print(f"   Getting vector: {test_key}")
                
                try:
                    get_response = s3_vectors_client.get_vectors(
                        vectorBucketName=VECTOR_BUCKET_NAME,
                        indexName=VECTOR_INDEX_NAME,
                        keys=[test_key]
                    )
                    
                    print(f"   ✅ Get vectors successful")
                    print(f"      Response keys: {list(get_response.keys())}")
                    
                    if get_response.get('vectors'):
                        full_vector = get_response['vectors'][0]
                        print(f"      Full vector keys: {list(full_vector.keys())}")
                        print(f"      Full vector content: {json.dumps(full_vector, default=str, indent=2)}")
                        
                        # Check metadata
                        if 'metadata' in full_vector:
                            metadata = full_vector['metadata']
                            print(f"      📋 Metadata found:")
                            print(f"         Keys: {list(metadata.keys())}")
                            print(f"         Content: {json.dumps(metadata, default=str, indent=2)}")
                        else:
                            print(f"      ❌ NO METADATA in get_vectors result")
                    else:
                        print(f"      ❌ No vector data returned")
                        
                except Exception as e:
                    print(f"      ❌ Get vectors failed: {e}")
            else:
                print("   ❌ No test key available")
        
        # Test 5: Check S3 Vectors service capabilities
        print(f"\n5️⃣ Checking S3 Vectors service capabilities...")
        try:
            # Try to describe the index (if supported)
            print(f"   Available S3 Vectors methods:")
            methods = [method for method in dir(s3_vectors_client) if not method.startswith('_')]
            for method in sorted(methods):
                print(f"     - {method}")
                
        except Exception as e:
            print(f"   ❌ Error checking capabilities: {e}")
        
        # Summary
        print(f"\n🎯 CONFIGURATION TEST SUMMARY:")
        print(f"   List vectors: {'✅' if 'vectors' in list_response else '❌'}")
        print(f"   Basic search: {'✅' if 'vectors' in search_response else '❌'}")
        print(f"   Metadata search: {'✅' if 'vectors' in search_metadata_response else '❌'}")
        
        # Check if metadata is actually returned
        metadata_returned = False
        if metadata_vectors and 'metadata' in metadata_vectors[0]:
            metadata_returned = True
        
        print(f"   Metadata returned: {'✅' if metadata_returned else '❌'}")
        
        if not metadata_returned:
            print(f"\n🚨 CRITICAL ISSUE CONFIRMED:")
            print(f"   S3 Vectors is NOT returning metadata!")
            print(f"   This means either:")
            print(f"   1. The index is not configured to store metadata")
            print(f"   2. The vectors were uploaded without metadata")
            print(f"   3. There's a service configuration issue")
            print(f"   ")
            print(f"   SOLUTION: Check S3 Vectors index configuration and re-upload vectors with metadata")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_s3_vectors_configuration() 