#!/usr/bin/env python3
"""
Simple S3 Vectors Test
Focus on what we can test without embedding validation issues.
"""

import json
import boto3

def test_s3_vectors_simple():
    """Simple test focusing on what we can verify."""
    
    # Initialize client
    s3_vectors_client = boto3.client('s3vectors')
    
    # Configuration
    VECTOR_BUCKET_NAME = 'epic-vector-bucket'
    VECTOR_INDEX_NAME = 'book-embeddings-index'
    
    print("🔍 Simple S3 Vectors Test")
    print("=" * 40)
    
    try:
        # Test 1: List vectors (this should work)
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
                return
                
        except Exception as e:
            print(f"   ❌ List vectors failed: {e}")
            return
        
        # Test 2: Get specific vector (this should work)
        print(f"\n2️⃣ Testing get_vectors...")
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
                            
                            # Check for text content
                            if 'text' in metadata:
                                text = metadata['text']
                                if text:
                                    print(f"         Text: {len(text)} characters")
                                    print(f"         Preview: {text[:100]}...")
                                else:
                                    print(f"         Text: EMPTY or None")
                            else:
                                print(f"         ❌ No text in metadata")
                        else:
                            print(f"      ❌ NO METADATA in get_vectors result")
                    else:
                        print(f"      ❌ No vector data returned")
                        
                except Exception as e:
                    print(f"      ❌ Get vectors failed: {e}")
            else:
                print("   ❌ No test key available")
        
        # Test 3: Check S3 Vectors service capabilities
        print(f"\n3️⃣ Checking S3 Vectors service capabilities...")
        try:
            print(f"   Available S3 Vectors methods:")
            methods = [method for method in dir(s3_vectors_client) if not method.startswith('_')]
            for method in sorted(methods):
                print(f"     - {method}")
                
        except Exception as e:
            print(f"   ❌ Error checking capabilities: {e}")
        
        # Summary
        print(f"\n🎯 SIMPLE TEST SUMMARY:")
        print(f"   List vectors: {'✅' if 'vectors' in list_response else '❌'}")
        
        # Check if metadata exists in the vectors we can access
        metadata_found = False
        text_found = False
        
        if vectors:
            try:
                test_key = vectors[0].get('key', '')
                if test_key:
                    get_response = s3_vectors_client.get_vectors(
                        vectorBucketName=VECTOR_BUCKET_NAME,
                        indexName=VECTOR_INDEX_NAME,
                        keys=[test_key]
                    )
                    
                    if get_response.get('vectors'):
                        full_vector = get_response['vectors'][0]
                        if 'metadata' in full_vector:
                            metadata_found = True
                            metadata = full_vector['metadata']
                            if 'text' in metadata and metadata['text']:
                                text_found = True
            except:
                pass
        
        print(f"   Metadata field exists: {'✅' if metadata_found else '❌'}")
        print(f"   Text content in metadata: {'✅' if text_found else '❌'}")
        
        if not metadata_found:
            print(f"\n🚨 CRITICAL ISSUE CONFIRMED:")
            print(f"   S3 Vectors is NOT returning metadata!")
            print(f"   This explains why your query API can't get text content.")
            print(f"   ")
            print(f"   SOLUTION: Check S3 Vectors index configuration and re-upload vectors with metadata")
        elif not text_found:
            print(f"\n⚠️  PARTIAL ISSUE:")
            print(f"   Metadata exists but no text content!")
            print(f"   This means vectors were uploaded without text in metadata.")
            print(f"   ")
            print(f"   SOLUTION: Re-upload book content with text in metadata")
        else:
            print(f"\n✅ METADATA WORKING:")
            print(f"   Metadata and text content are available!")
            print(f"   The issue might be elsewhere in your query process.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_s3_vectors_simple() 