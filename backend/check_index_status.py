#!/usr/bin/env python3
"""
Script to check S3 Vectors index status and configuration
Run this to understand why delete option might not be visible
"""

import boto3
import json
from datetime import datetime

# Configuration
VECTOR_BUCKET_NAME = "epic-vector-bucket"
VECTOR_INDEX_NAME = "book-embeddings-index"

def check_s3_vectors_status():
    """Check the status of S3 Vectors index and bucket"""
    try:
        # Initialize S3 Vectors client
        s3_vectors_client = boto3.client('s3vectors')
        
        print("🔍 Checking S3 Vectors Status")
        print("=" * 50)
        
        # Check if bucket exists
        try:
            bucket_response = s3_vectors_client.get_vector_bucket(
                vectorBucketName=VECTOR_BUCKET_NAME
            )
            print(f"✅ Bucket exists: {VECTOR_BUCKET_NAME}")
            print(f"   Creation Date: {bucket_response.get('CreationDate', 'Unknown')}")
            print(f"   Region: {bucket_response.get('Region', 'Unknown')}")
        except Exception as e:
            print(f"❌ Bucket not found or error: {e}")
            return
        
        # Check if index exists
        try:
            index_response = s3_vectors_client.get_index(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=VECTOR_INDEX_NAME
            )
            print(f"\n✅ Index exists: {VECTOR_INDEX_NAME}")
            print(f"   Status: {index_response.get('Status', 'Unknown')}")
            print(f"   Creation Date: {index_response.get('CreationDate', 'Unknown')}")
            print(f"   Last Modified: {index_response.get('LastModified', 'Unknown')}")
            
            # Check index configuration
            index_config = index_response.get('IndexConfiguration', {})
            print(f"\n📋 Index Configuration:")
            print(f"   Vector Configuration: {json.dumps(index_config.get('VectorConfiguration', {}), indent=2)}")
            
            # Check if metadata configuration exists
            metadata_config = index_config.get('MetadataConfiguration', {})
            if metadata_config:
                print(f"   ✅ Metadata Configuration: {json.dumps(metadata_config, indent=2)}")
            else:
                print(f"   ❌ No Metadata Configuration found!")
                print(f"   This explains why metadata isn't working!")
            
        except Exception as e:
            print(f"❌ Index not found or error: {e}")
            return
        
        # List all indexes in the bucket
        try:
            list_response = s3_vectors_client.list_indexes(
                vectorBucketName=VECTOR_BUCKET_NAME
            )
            indexes = list_response.get('Indexes', [])
            print(f"\n📚 All Indexes in Bucket:")
            for idx in indexes:
                status_icon = "✅" if idx['IndexName'] == VECTOR_INDEX_NAME else "📋"
                print(f"   {status_icon} {idx['IndexName']} - Status: {idx.get('Status', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ Could not list indexes: {e}")
        
        # Check if there are any vectors in the index
        try:
            list_vectors_response = s3_vectors_client.list_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=VECTOR_INDEX_NAME,
                maxResults=5  # Just check first few
            )
            vector_count = list_vectors_response.get('VectorCount', 0)
            print(f"\n🔢 Vectors in Index:")
            print(f"   Total Count: {vector_count}")
            
            if vector_count > 0:
                print(f"   First few keys:")
                for vector in list_vectors_response.get('Vectors', [])[:3]:
                    print(f"     - {vector.get('Key', 'Unknown')}")
            else:
                print(f"   No vectors found in index")
                
        except Exception as e:
            print(f"❌ Could not list vectors: {e}")
        
        print(f"\n" + "=" * 50)
        print("💡 Next Steps:")
        if metadata_config:
            print("   ✅ Index has metadata configuration - no need to recreate!")
        else:
            print("   ❌ Index missing metadata configuration - needs recreation")
            print("   🔧 Try using AWS CLI to delete index:")
            print(f"      aws s3vectors delete-index --vector-bucket-name {VECTOR_BUCKET_NAME} --index-name {VECTOR_INDEX_NAME}")
        
    except Exception as e:
        print(f"❌ Error checking S3 Vectors status: {e}")
        print("   This might indicate AWS credentials or permission issues")

if __name__ == "__main__":
    check_s3_vectors_status() 