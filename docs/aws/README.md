# ☁️ AWS Services Overview

Complete reference for all AWS services used in the Epic Web App project.

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   Lambda        │
│   (React/TS)    │◄──►│   (REST API)     │◄──►│   Functions     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Cognito        │    │   S3 Vectors    │
                       │   (Auth)         │    │   (Vector DB)   │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   S3             │    │   CloudFront    │
                       │   (File Storage) │    │   (CDN)         │
                       └──────────────────┘    └─────────────────┘
```

## 🔐 **Amazon Cognito**

### **Purpose**
User authentication and authorization service.

### **Components**
- **User Pool**: Manages user accounts and authentication
- **Identity Pool**: Provides temporary AWS credentials
- **JWT Tokens**: Secure authentication tokens

### **Configuration**
```yaml
UserPool:
  Type: AWS::Cognito::UserPool
  Properties:
    UserPoolName: epic-user-pool
    AutoVerifiedAttributes:
      - email
    Policies:
      PasswordPolicy:
        MinimumLength: 8
        RequireLowercase: true
        RequireNumbers: true
        RequireSymbols: true
        RequireUppercase: true
```

### **Common Operations**
```python
import boto3

cognito = boto3.client('cognito-idp')

# Sign up user
response = cognito.sign_up(
    ClientId='your-client-id',
    Username='user@example.com',
    Password='SecurePass123!',
    UserAttributes=[
        {'Name': 'email', 'Value': 'user@example.com'}
    ]
)

# Sign in user
response = cognito.initiate_auth(
    ClientId='your-client-id',
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'user@example.com',
        'PASSWORD': 'SecurePass123!'
    }
)
```

## 🚀 **AWS Lambda**

### **Purpose**
Serverless compute service for running code without managing servers.

### **Functions in This Project**
1. **Upload Handler**: Processes book uploads and creates embeddings
2. **Query Handler**: Handles Q&A requests using vector search
3. **List Books Handler**: Lists available books and their status

### **Configuration**
```yaml
LambdaFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: epic-query-handler
    Runtime: python3.11
    Handler: query_handler.lambda_handler
    Code:
      ZipFile: |
        def lambda_handler(event, context):
            return {'statusCode': 200}
    Environment:
      Variables:
        VECTOR_BUCKET_NAME: epic-vector-bucket
        VECTOR_INDEX_NAME: book-embeddings-index
```

### **Common Patterns**
```python
import json
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Standard Lambda handler pattern."""
    try:
        # Parse request
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        # Process request
        result = process_request(body)
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
```

## 🌐 **API Gateway**

### **Purpose**
Managed service for creating, deploying, and managing REST APIs.

### **Endpoints**
- `POST /upload` - Upload book content
- `POST /query` - Query book content
- `GET /books` - List available books

### **Configuration**
```yaml
ApiGateway:
  Type: AWS::ApiGateway::RestApi
  Properties:
    Name: epic-api
    Description: Epic Web App API

ApiResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref ApiGateway
    ParentId: !GetAtt ApiGateway.RootResourceId
    PathPart: query

ApiMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref ApiGateway
    ResourceId: !Ref ApiResource
    HttpMethod: POST
    AuthorizationType: NONE
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
      Uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryHandlerLambda.Arn}/invocations
```

### **CORS Configuration**
```python
# Lambda response headers for CORS
headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
}
```

## 🗄️ **S3 Vectors**

### **Purpose**
Managed vector database service for storing and searching vector embeddings.

### **Key Features**
- **Vector Storage**: Store high-dimensional vectors
- **Similarity Search**: Find similar vectors using various metrics
- **Metadata Support**: Store additional data with vectors
- **Filtering**: Query vectors based on metadata

### **Common Operations**
```python
import boto3

s3_vectors = boto3.client('s3vectors')

# Upload vector
response = s3_vectors.put_vectors(
    vectorBucketName='epic-vector-bucket',
    indexName='book-embeddings-index',
    vectors=[{
        'key': 'vector-id',
        'data': {'float32': [0.1, 0.2, ...]},
        'metadata': {'book_title': 'book-name', 'text': 'content...'}
    }]
)

# Search vectors
response = s3_vectors.query_vectors(
    vectorBucketName='epic-vector-bucket',
    indexName='book-embeddings-index',
    queryVector={'float32': [0.1, 0.2, ...]},
    topK=5,
    returnMetadata=True
)
```

## 📦 **Amazon S3**

### **Purpose**
Object storage service for storing files and data.

### **Buckets in This Project**
- **Main Bucket**: `epic-s3-bucket-ramayana` - Stores uploaded book files
- **Vector Bucket**: `epic-vector-bucket` - Stores vector embeddings

### **Common Operations**
```python
import boto3

s3 = boto3.client('s3')

# Upload file
s3.upload_file(
    'local-file.txt',
    'epic-s3-bucket-ramayana',
    'books/book-name.txt'
)

# Download file
s3.download_file(
    'epic-s3-bucket-ramayana',
    'books/book-name.txt',
    'local-file.txt'
)

# List objects
response = s3.list_objects_v2(
    Bucket='epic-s3-bucket-ramayana',
    Prefix='books/'
)
```

## 🎯 **Amazon Bedrock**

### **Purpose**
Fully managed service for foundation models and AI applications.

### **Models Used**
- **Titan Text Express**: Text generation and Q&A

### **Configuration**
```python
import boto3

bedrock = boto3.client('bedrock-runtime')

# Generate text
response = bedrock.invoke_model(
    modelId='amazon.titan-text-express-v1',
    body=json.dumps({
        'inputText': 'Your prompt here',
        'textGenerationConfig': {
            'maxTokenCount': 1000,
            'temperature': 0.5,
            'topP': 1,
            'stopSequences': ['User:']
        }
    })
)

response_body = json.loads(response['body'].read())
generated_text = response_body['results'][0]['outputText']
```

## 🌍 **CloudFront**

### **Purpose**
Content delivery network (CDN) for distributing content globally.

### **Configuration**
```json
{
  "DistributionConfig": {
    "Origins": {
      "Items": [
        {
          "Id": "S3-Origin",
          "DomainName": "epic-s3-bucket-ramayana.s3.amazonaws.com",
          "S3OriginConfig": {
            "OriginAccessIdentity": ""
          }
        }
      ]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3-Origin",
      "ViewerProtocolPolicy": "redirect-to-https",
      "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    }
  }
}
```

## 🔧 **IAM (Identity and Access Management)**

### **Purpose**
Manage access to AWS services and resources.

### **Common Policies**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::epic-s3-bucket-ramayana/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3vectors:PutVectors",
        "s3vectors:QueryVectors",
        "s3vectors:GetVectors"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📊 **CloudWatch**

### **Purpose**
Monitoring and observability service for AWS resources.

### **Key Metrics**
- **Lambda**: Duration, errors, invocations
- **API Gateway**: Request count, latency, 4xx/5xx errors
- **S3**: Request count, latency

### **Logging**
```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    
    try:
        # Process request
        result = process_request(event)
        logger.info(f"Request processed successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise
```

## 🚀 **Deployment & Infrastructure**

### **CloudFormation**
- **Templates**: Infrastructure as code
- **Stacks**: Manage related resources
- **Updates**: Rolling updates with minimal downtime

### **SAM (Serverless Application Model)**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  QueryFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: query_handler.lambda_handler
      Runtime: python3.11
      Events:
        Api:
          Type: Api
          Properties:
            Path: /query
            Method: post
```

## 📚 **Best Practices**

1. **Security**: Use IAM roles with least privilege
2. **Monitoring**: Enable CloudWatch logging for all services
3. **Error Handling**: Implement proper error handling in Lambda functions
4. **CORS**: Configure CORS properly for web applications
5. **Environment Variables**: Use environment variables for configuration
6. **Logging**: Log important events and errors
7. **Testing**: Test locally before deploying

## 🔗 **Related Documentation**

- [S3 Vectors Guide](./s3-vectors.md)
- [Lambda Functions](./lambda.md)
- [API Gateway](./api-gateway.md)
- [AWS Official Documentation](https://docs.aws.amazon.com/)
- [AWS SDK for Python](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) 