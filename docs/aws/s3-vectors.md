# 🚀 S3 Vectors Reference Guide

Complete reference for S3 Vectors implementation in the Epic Web App project.

## 📋 **Overview**

S3 Vectors is AWS's managed vector database service that stores and searches vector embeddings. This project uses it for semantic search across book content.

## 🏗️ **Architecture**

```
Frontend → API Gateway → Lambda → S3 Vectors → Vector Index
                                    ↓
                              S3 Vector Bucket
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
VECTOR_BUCKET_NAME=epic-vector-bucket
VECTOR_INDEX_NAME=book-embeddings-index
```

### **AWS Resources**
- **Vector Bucket**: `epic-vector-bucket`
- **Vector Index**: `book-embeddings-index`
- **Dimension**: 1536 (OpenAI embedding size)
- **Metric Type**: COSINE

## 📚 **API Reference**

### **1. Client Initialization**
```python
import boto3
s3_vectors_client = boto3.client('s3vectors')
```

### **2. Upload Vectors**
```python
def upload_vector_to_s3_vectors(vector_id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
    """Upload a vector embedding to S3 Vectors."""
    try:
        response = s3_vectors_client.put_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            vectors=[
                {
                    'key': vector_id,
                    'data': {
                        'float32': embedding
                    },
                    'metadata': metadata
                }
            ]
        )
        return True
    except Exception as e:
        print(f"Error uploading vector {vector_id}: {e}")
        return False
```

### **3. Search Vectors**
```python
def search_s3_vectors(book_title: str, query_embedding: List[float], top_k: int = 5):
    """Search for similar vectors in S3 Vectors."""
    filter_expression = f"metadata.book_title = '{book_title}'"
    
    response = s3_vectors_client.query_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        queryVector={'float32': query_embedding},
        topK=top_k,
        filter=filter_expression,
        returnMetadata=True,
        returnData=False
    )
    
    return response.get('vectors', [])
```

### **4. Get Vector Details**
```python
def get_vector_details(vector_key: str):
    """Get full vector data including metadata."""
    response = s3_vectors_client.get_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        keys=[vector_key]
    )
    
    return response.get('vectors', [])
```

### **5. List Vectors**
```python
def list_vectors(max_results: int = 1000):
    """List all vectors in the index."""
    response = s3_vectors_client.list_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        maxResults=max_results
    )
    
    return response.get('vectors', [])
```

## 📊 **Data Structure**

### **Vector Object Structure**
```json
{
  "key": "woman-in-science-0026",
  "data": {
    "float32": [-0.055229898542165756, -0.04298466444015503, ...]
  },
  "metadata": {
    "book_title": "woman-in-science",
    "chunk_number": 26,
    "chunk_id": "0026",
    "text": "Actual text content of the chunk..."
  }
}
```

### **Search Result Structure**
```json
{
  "key": "woman-in-science-0026",
  "score": 0.95,
  "metadata": {
    "book_title": "woman-in-science",
    "chunk_number": 26,
    "chunk_id": "0026",
    "text": "Actual text content..."
  }
}
```

## 🔍 **Search Parameters**

### **Query Vectors Parameters**
- `vectorBucketName`: S3 bucket containing vectors
- `indexName`: Vector index name
- `queryVector`: Query embedding in `{'float32': [...]}` format
- `topK`: Number of results to return
- `filter`: Filter expression (e.g., `metadata.book_title = 'book-name'`)
- `returnMetadata`: Whether to return metadata (default: true)
- `returnData`: Whether to return vector data (default: false)

### **Filter Expressions**
```python
# Filter by book title
filter_expression = f"metadata.book_title = '{book_title}'"

# Filter by chunk number range
filter_expression = "metadata.chunk_number >= 1 AND metadata.chunk_number <= 100"

# Multiple conditions
filter_expression = "metadata.book_title = 'book-name' AND metadata.chunk_number > 50"
```

## 📝 **Common Operations**

### **Uploading Book Content**
```python
def process_book_for_s3_vectors(book_id: str, chunks: List[Dict]):
    """Process book chunks and upload to S3 Vectors."""
    for chunk in chunks:
        # Generate embedding
        embedding = get_embedding(chunk['text'])
        
        # Prepare metadata
        metadata = {
            'book_title': book_id,
            'chunk_number': int(chunk['chunk_id']),
            'chunk_id': chunk['chunk_id'],
            'text': chunk['text']
        }
        
        # Upload to S3 Vectors
        vector_id = f"{book_id}-{chunk['chunk_id']}"
        success = upload_vector_to_s3_vectors(vector_id, embedding, metadata)
```

### **Searching Book Content**
```python
def search_book_content(book_title: str, question: str):
    """Search for relevant content in a specific book."""
    # Generate question embedding
    question_embedding = get_embedding(question)
    
    # Search S3 Vectors
    results = search_s3_vectors(book_title, question_embedding, top_k=5)
    
    # Extract text content
    chunk_texts = []
    for result in results:
        if 'metadata' in result and 'text' in result['metadata']:
            chunk_texts.append(result['metadata']['text'])
    
    return chunk_texts
```

## ⚠️ **Common Issues & Solutions**

### **1. Text Not Found in Metadata**
**Problem**: Search returns chunks but no text content
**Solution**: Ensure `returnMetadata=True` in search calls

### **2. Filter Not Working**
**Problem**: Filter expressions don't return expected results
**Solution**: Check metadata field names (use lowercase `metadata`, not `Metadata`)

### **3. Vector Upload Fails**
**Problem**: `put_vectors` returns error
**Solution**: Verify vector dimension matches index configuration (1536)

### **4. Search Returns Empty Results**
**Problem**: No vectors found for query
**Solution**: Check if vectors exist in the index and verify filter expressions

## 🧪 **Testing & Debugging**

### **Debug Script**
Use the provided debug script to test S3 Vectors operations:
```bash
cd backend
python debug_s3_vectors.py
```

### **CloudWatch Logs**
Monitor Lambda execution logs for:
- Search query parameters
- Filter expressions
- Returned metadata structure
- Text extraction results

### **Common Debug Outputs**
```python
# Check search results structure
print(f"Search response: {json.dumps(response, default=str)}")

# Verify metadata content
for result in results:
    metadata = result.get('metadata', {})
    print(f"Metadata keys: {list(metadata.keys())}")
    if 'text' in metadata:
        print(f"Text preview: {metadata['text'][:100]}...")
```

## 📚 **Best Practices**

1. **Always use `returnMetadata=True`** for search operations
2. **Store text content in metadata** for easy retrieval
3. **Use consistent metadata field names** (lowercase)
4. **Implement proper error handling** for all API calls
5. **Monitor CloudWatch logs** for debugging
6. **Test with small datasets** before processing large books

## 🔗 **Related Documentation**

- [AWS S3 Vectors Developer Guide](https://docs.aws.amazon.com/s3vectors/)
- [S3 Vectors API Reference](https://docs.aws.amazon.com/s3vectors/latest/APIReference/)
- [Vector Search Implementation](./vector-search.md)
- [Lambda Functions](./lambda.md)

## 📞 **Support**

For issues with S3 Vectors implementation:
1. Check CloudWatch logs for error details
2. Run the debug script to verify API behavior
3. Review this documentation for common solutions
4. Check AWS S3 Vectors service status 