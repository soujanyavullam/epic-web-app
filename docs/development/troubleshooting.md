# 🆘 Troubleshooting Guide

Comprehensive guide for resolving common issues in the Epic Web App project.

## 🚨 **Critical Issues**

### **API Returns "Insufficient Information"**
**Problem**: Query API returns "The model cannot find sufficient information to answer the question."

**Symptoms**:
- API finds relevant chunks but no text content
- LLM receives empty or minimal context
- Search results contain metadata but no text

**Root Causes**:
1. **Text extraction failure** - Metadata structure mismatch
2. **S3 Vectors search not returning text** - `returnMetadata=True` not working
3. **Token limits too restrictive** - Cutting off content prematurely

**Solutions**:
```python
# 1. Check metadata structure in search results
for result in results:
    metadata = result.get('metadata', {})
    print(f"Metadata keys: {list(metadata.keys())}")
    if 'text' in metadata:
        print(f"Text found: {metadata['text'][:100]}...")

# 2. Verify S3 Vectors search parameters
response = s3_vectors_client.query_vectors(
    vectorBucketName=VECTOR_BUCKET_NAME,
    indexName=VECTOR_INDEX_NAME,
    queryVector={'float32': query_embedding},
    topK=5,
    filter=filter_expression,
    returnMetadata=True,  # Ensure this is True
    returnData=False
)

# 3. Check text extraction logic
if 'metadata' in chunk and 'text' in chunk['metadata']:
    text = chunk['metadata']['text']  # Use lowercase 'metadata'
elif 'Metadata' in chunk and 'text' in chunk['Metadata']:
    text = chunk['Metadata']['text']  # Fallback to uppercase
```

**Debug Steps**:
1. Run `python debug_s3_vectors.py` to verify API behavior
2. Check CloudWatch logs for text extraction process
3. Verify vector upload included text in metadata
4. Test with smaller token limits

### **Lambda Function Deployment Fails**
**Problem**: Lambda function fails to deploy or update

**Symptoms**:
- Deployment script returns errors
- Function not found in AWS console
- Runtime errors in deployed function

**Root Causes**:
1. **IAM permissions insufficient** - Lambda deployment requires specific permissions
2. **Package size too large** - Lambda has 50MB limit for direct upload
3. **Dependencies missing** - Required packages not included in deployment package

**Solutions**:
```bash
# 1. Check IAM permissions
aws iam list-attached-user-policies --user-name your-username

# 2. Verify package size
du -sh lambda_package_new/
# Should be under 50MB for direct upload

# 3. Check dependencies
pip list --format=freeze > requirements_check.txt
# Ensure all required packages are in requirements.txt
```

**Debug Steps**:
1. Check AWS CLI credentials: `aws sts get-caller-identity`
2. Verify IAM permissions for Lambda operations
3. Check deployment package contents and size
4. Review CloudFormation/CloudWatch logs

## 🔍 **Common Issues by Component**

### **S3 Vectors Issues**

#### **Search Returns No Results**
```bash
# Check if vectors exist
aws s3vectors list-vectors \
  --vector-bucket-name epic-vector-bucket \
  --index-name book-embeddings-index \
  --max-results 10

# Verify filter expression
filter_expression = f"metadata.book_title = '{book_title}'"
print(f"Using filter: {filter_expression}")

# Test without filter first
response = s3_vectors_client.query_vectors(
    vectorBucketName=VECTOR_BUCKET_NAME,
    indexName=VECTOR_INDEX_NAME,
    queryVector={'float32': [0.1] * 1536},
    topK=5,
    returnMetadata=True
)
```

#### **Vector Upload Fails**
```python
# Check vector dimension
if len(embedding) != 1536:
    print(f"Invalid embedding dimension: {len(embedding)}")
    return False

# Verify metadata structure
metadata = {
    'book_title': book_id,
    'chunk_number': int(chunk['chunk_id']),
    'chunk_id': chunk['chunk_id'],
    'text': chunk['text']  # Ensure text is included
}

# Check S3 Vectors service status
try:
    response = s3_vectors_client.list_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        maxResults=1
    )
    print("S3 Vectors service is accessible")
except Exception as e:
    print(f"S3 Vectors service error: {e}")
```

### **Lambda Function Issues**

#### **Function Times Out**
```python
# Check function timeout setting
# Default is 3 seconds, increase if needed

# Add timeout handling
import signal
import contextlib

@contextlib.contextmanager
def timeout(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError("Function timed out")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# Use in function
try:
    with timeout(25):  # 25 seconds
        result = process_request(event)
    return result
except TimeoutError:
    return {
        'statusCode': 408,
        'body': json.dumps({'error': 'Request timeout'})
    }
```

#### **Memory Issues**
```python
# Monitor memory usage
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")

# Call at key points
log_memory_usage()
result = process_large_data()
log_memory_usage()
```

### **API Gateway Issues**

#### **CORS Errors**
```python
# Ensure all required CORS headers
headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
}

# Handle OPTIONS preflight
if event.get('httpMethod') == 'OPTIONS':
    return {
        'statusCode': 200,
        'headers': headers,
        'body': ''
    }
```

#### **API Key Issues**
```bash
# Check API key status
aws apigateway get-api-key --api-key your-api-key-id

# Verify usage plan
aws apigateway get-usage-plan --usage-plan-id your-usage-plan-id

# Test API key
curl -H "x-api-key: your-api-key" \
  https://your-api-gateway-url.amazonaws.com/query
```

### **Authentication Issues**

#### **Cognito Token Expired**
```javascript
// Frontend token refresh
import { CognitoUser, CognitoUserSession } from 'amazon-cognito-identity-js';

const refreshToken = async (user) => {
  return new Promise((resolve, reject) => {
    user.getSession((err, session) => {
      if (err) {
        reject(err);
      } else if (session.isValid()) {
        resolve(session);
      } else {
        user.refreshSession(session.getRefreshToken(), (err, session) => {
          if (err) {
            reject(err);
          } else {
            resolve(session);
          }
        });
      }
    });
  });
};
```

#### **JWT Validation Fails**
```python
# Verify JWT token
import jwt
from jwt.algorithms import RSAAlgorithm

def verify_jwt_token(token, user_pool_id, region):
    try:
        # Get public keys from Cognito
        keys_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
        response = requests.get(keys_url)
        keys = response.json()['keys']
        
        # Decode token header to get key ID
        header = jwt.get_unverified_header(token)
        key_id = header['kid']
        
        # Find matching key
        key = next((k for k in keys if k['kid'] == key_id), None)
        if not key:
            raise ValueError('Invalid key ID')
        
        # Convert to PEM format
        public_key = RSAAlgorithm.from_jwk(json.dumps(key))
        
        # Verify token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience='your-client-id'
        )
        
        return payload
        
    except Exception as e:
        print(f"JWT validation error: {e}")
        return None
```

## 🧪 **Debugging Tools & Techniques**

### **CloudWatch Logs Analysis**
```bash
# Get recent log events
aws logs filter-log-events \
  --log-group-name /aws/lambda/epic-query-handler \
  --start-time $(date -d '1 hour ago' +%s)000

# Search for specific errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/epic-query-handler \
  --filter-pattern "ERROR"

# Get function metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=epic-query-handler \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --period 300 \
  --statistics Average
```

### **Local Testing**
```python
# Test Lambda function locally
def test_lambda_locally():
    # Mock event
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'question': 'Test question',
            'book_title': 'test-book'
        })
    }
    
    # Mock context
    class MockContext:
        function_name = 'test-function'
        function_version = '$LATEST'
        invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
        memory_limit_in_mb = '128'
        aws_request_id = 'test-request-id'
        log_group_name = '/aws/lambda/test-function'
        log_stream_name = 'test-stream'
        remaining_time_in_millis = 30000
    
    context = MockContext()
    
    # Test function
    result = lambda_handler(event, context)
    print(json.dumps(result, indent=2))
    return result

# Run test
if __name__ == "__main__":
    test_lambda_locally()
```

### **Performance Profiling**
```python
import time
import functools

def profile_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

# Use decorator
@profile_function
def search_s3_vectors(book_title, query_embedding, top_k=5):
    # Function implementation
    pass
```

## 📊 **Monitoring & Alerting**

### **Key Metrics to Monitor**
1. **Lambda**: Duration, errors, invocations, memory usage
2. **API Gateway**: Request count, latency, 4xx/5xx errors
3. **S3 Vectors**: Request count, latency, error rate
4. **S3**: Request count, latency, storage usage

### **CloudWatch Alarms**
```yaml
# CloudFormation template for alarms
LambdaErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: epic-lambda-errors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: epic-query-handler
    AlarmActions:
      - !Ref SNSTopicArn
```

## 🚀 **Performance Optimization**

### **Lambda Optimization**
```python
# 1. Reuse clients outside handler
import boto3

# Initialize clients at module level
s3_vectors_client = boto3.client('s3vectors')
bedrock_client = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    # Use pre-initialized clients
    pass

# 2. Optimize imports
# Move heavy imports inside functions if not always needed
def process_with_numpy():
    import numpy as np  # Import only when needed
    # Process data

# 3. Use connection pooling
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

### **S3 Vectors Optimization**
```python
# 1. Batch operations
def batch_upload_vectors(vectors_batch):
    """Upload multiple vectors in one call."""
    try:
        response = s3_vectors_client.put_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            vectors=vectors_batch
        )
        return True
    except Exception as e:
        print(f"Batch upload error: {e}")
        return False

# 2. Optimize search parameters
def optimized_search(book_title, query_embedding, top_k=5):
    """Optimized search with appropriate parameters."""
    filter_expression = f"metadata.book_title = '{book_title}'"
    
    response = s3_vectors_client.query_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        queryVector={'float32': query_embedding},
        topK=top_k,
        filter=filter_expression,
        returnMetadata=True,
        returnData=False  # Don't return vector data if not needed
    )
    
    return response.get('vectors', [])
```

## 📞 **Getting Help**

### **Escalation Path**
1. **Check documentation** - This guide and related docs
2. **Search logs** - CloudWatch, console, terminal
3. **Run debug scripts** - `debug_s3_vectors.py`
4. **Test locally** - Verify issue reproduces locally
5. **Check AWS status** - Service health dashboard
6. **Contact team** - Slack, email, meetings
7. **AWS support** - If service-level issue

### **Information to Provide**
When seeking help, include:
- **Error message** - Exact error text
- **Logs** - Relevant CloudWatch logs
- **Steps to reproduce** - Clear reproduction steps
- **Environment** - AWS region, function version
- **Recent changes** - What changed before issue
- **Expected behavior** - What should happen

### **Useful Commands**
```bash
# Check AWS service status
aws health describe-events

# Verify credentials
aws sts get-caller-identity

# Check S3 Vectors service
aws s3vectors list-vectors --vector-bucket-name epic-vector-bucket

# Monitor Lambda metrics
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Duration

# Check API Gateway
aws apigateway get-rest-apis
```

This troubleshooting guide covers the most common issues and provides practical solutions. Always start with the debugging tools and work through the escalation path systematically. 