# Epic Web App - AI-Powered Book Q&A System

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Backend Components](#backend-components)
4. [Frontend Components](#frontend-components)
5. [AWS Services](#aws-services)
6. [Deployment Guide](#deployment-guide)
7. [API Documentation](#api-documentation)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Features](#features)

## 🎯 Project Overview

The Epic Web App is an AI-powered book Q&A system that allows users to ask questions about uploaded books and receive intelligent, context-aware answers. The system uses advanced NLP techniques including vector embeddings, hybrid search, and content filtering to provide accurate and appropriate responses.

### Key Features
- **AI-Powered Q&A**: Ask questions about any uploaded book
- **Content Filtering**: Automatic filtering of inappropriate language
- **Hybrid Search**: Combines semantic and keyword-based search
- **Multi-Book Support**: Upload and query multiple books
- **Responsive UI**: Modern, professional web interface
- **Authentication**: AWS Cognito integration (optional)

## 🏗️ Architecture

### High-Level Architecture
```
Frontend (React + Vite) → API Gateway → Lambda Functions → AWS Services
                                    ↓
                            DynamoDB (Book Chunks + Embeddings)
                            S3 (Raw Text Files)
                            Bedrock (AI Models)
                            CloudFront (CDN)
```

### Technology Stack
- **Frontend**: React, TypeScript, Vite
- **Backend**: Python, AWS Lambda
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **AI**: Amazon Bedrock (Titan models)
- **CDN**: Amazon CloudFront
- **Authentication**: AWS Cognito
- **DNS**: Route 53

## 🔧 Backend Components

### Lambda Functions

#### 1. `epic-query-function` (query_handler.py)
**Purpose**: Main Q&A processing function
**Handler**: `query_handler.lambda_handler`
**Features**:
- Question embedding generation
- Hybrid search (semantic + keyword)
- LLM response generation
- Content filtering
- Response validation

**Key Functions**:
```python
def get_embedding(text: str) -> list
def get_llm_response(prompt: str) -> str
def lambda_handler(event, context) -> Dict
```

#### 2. `list-books-function` (list_books.py)
**Purpose**: List available books from S3
**Handler**: `list_books.lambda_handler`
**Features**:
- S3 bucket scanning
- Book metadata extraction
- CORS support

#### 3. `epic-upload-function` (upload_handler.py)
**Purpose**: Upload new books to S3
**Handler**: `upload_handler.lambda_handler`
**Features**:
- File validation
- S3 upload
- Error handling

### Utility Modules

#### `utils/vector_search.py`
**Purpose**: Vector similarity calculations and chunk retrieval
**Key Features**:
- Cosine similarity calculation
- Hybrid search (70% semantic, 30% keyword)
- Chunk filtering and scoring
- Decimal type handling

#### `utils/prompt_builder.py`
**Purpose**: Construct LLM prompts
**Features**:
- Context-aware prompt building
- Source citation
- Content moderation instructions
- Response quality guidelines

#### `utils/content_filter.py`
**Purpose**: Content moderation and word replacement
**Features**:
- Inappropriate word detection
- Context-aware replacements
- Custom filter management
- Statistics tracking

#### `utils/auth_middleware.py`
**Purpose**: JWT token validation and user authentication
**Features**:
- Cognito JWT verification
- User session management
- Role-based access control

## 🎨 Frontend Components

### Core Components

#### `App.tsx`
**Purpose**: Main application component
**Features**:
- Routing between pages
- Authentication state management
- Global error handling

#### `BookQA.tsx`
**Purpose**: Main Q&A interface
**Features**:
- Book selection dropdown
- Question input form
- Answer display
- Loading states
- Error handling

#### `BookUpload.tsx`
**Purpose**: Book upload interface
**Features**:
- File selection
- Upload progress
- Success/error feedback

#### `Auth.tsx`
**Purpose**: Authentication interface
**Features**:
- Login/register forms
- Cognito integration
- Session management

### Supporting Components

#### `LoadingSpinner.tsx`
**Purpose**: Loading animation
**Features**:
- Customizable spinner
- Optional message display

#### `BookSelector.tsx`
**Purpose**: Book selection dropdown
**Features**:
- Dynamic book loading
- Search functionality
- Responsive design

#### `QuestionForm.tsx`
**Purpose**: Question input form
**Features**:
- Text area input
- Submit button
- Form validation

#### `AnswerDisplay.tsx`
**Purpose**: Answer display component
**Features**:
- Formatted answer display
- Error message handling
- Responsive layout

## ☁️ AWS Services

### Core Services

#### Amazon Lambda
- **Functions**: 3 Lambda functions for different operations
- **Runtime**: Python 3.9
- **Memory**: 256MB (query), 128MB (list, upload)
- **Timeout**: 30 seconds

#### Amazon DynamoDB
- **Table**: `book-embeddings-dev`
- **Purpose**: Store book chunks and embeddings
- **Schema**:
  - Partition Key: `book_title`
  - Sort Key: `chunk_id`
  - Attributes: `text`, `embedding`, `metadata`

#### Amazon S3
- **Buckets**:
  - `epic-s3-bucket-ramayana`: Raw text files
  - `epic-web-app-static`: Frontend hosting
- **Features**: Versioning, lifecycle policies

#### Amazon Bedrock
- **Models**:
  - `amazon.titan-embed-text-v2:0`: Embedding generation
  - `amazon.titan-text-express-v1`: Text generation
- **Features**: High-quality embeddings and responses

#### Amazon API Gateway
- **API**: REST API with Lambda proxy integration
- **Endpoints**:
  - `POST /dev/query`: Q&A processing
  - `GET /dev/query/books`: Book listing
  - `POST /dev/upload`: Book upload
- **CORS**: Enabled for all endpoints

#### Amazon CloudFront
- **Distribution**: Global CDN for frontend
- **Features**: HTTPS, caching, compression
- **Origin**: S3 bucket with OAC

#### Route 53
- **Domain**: `epiclibrary.org`
- **Features**: DNS management, SSL certificate

#### AWS Cognito
- **User Pool**: `us-east-1_8d5MmHizq`
- **App Client**: `73hfbldjkkbdjvsml57g671j4l`
- **Features**: User registration, authentication, JWT tokens

## 🚀 Deployment Guide

### Prerequisites
- AWS CLI configured
- Node.js and npm installed
- Python 3.9+ with virtual environment

### Backend Deployment

#### 1. Prepare Lambda Package
```bash
cd backend/src
zip -r ../lambda_package_updated.zip *.py utils/ lambda/ auth_middleware.py cognito_config.py
```

#### 2. Deploy Lambda Functions
```bash
# Deploy query function
aws lambda update-function-code --function-name epic-query-function --zip-file fileb://lambda_package_updated.zip

# Deploy list function
aws lambda update-function-code --function-name list-books-function --zip-file fileb://lambda_package_updated.zip

# Deploy upload function
aws lambda update-function-code --function-name epic-upload-function --zip-file fileb://lambda_package_updated.zip
```

#### 3. Update Handler Configuration
For each Lambda function, set the correct handler:
- `epic-query-function`: `query_handler.lambda_handler`
- `list-books-function`: `list_books.lambda_handler`
- `epic-upload-function`: `upload_handler.lambda_handler`

### Frontend Deployment

#### 1. Build Frontend
```bash
cd frontend
npm run build
```

#### 2. Deploy to S3
```bash
aws s3 sync dist/ s3://epic-web-app-static --delete
```

#### 3. Invalidate CloudFront Cache
```bash
aws cloudfront create-invalidation --distribution-id ECREN1Z6RL4JJ --paths "/*"
```

### Manual Deployment Steps

#### Lambda Functions (AWS Console)
1. Go to AWS Lambda Console
2. Find the function (`epic-query-function`, etc.)
3. Go to "Code" tab
4. Click "Upload from" → ".zip file"
5. Upload `lambda_package_updated.zip`
6. Click "Save"

#### Frontend (AWS Console)
1. Go to S3 Console
2. Find bucket `epic-web-app-static`
3. Click "Upload"
4. Drag files from `frontend/dist/`
5. Click "Upload"

#### CloudFront Cache Invalidation
1. Go to CloudFront Console
2. Find distribution `ECREN1Z6RL4JJ`
3. Go to "Invalidations" tab
4. Click "Create invalidation"
5. Enter `/*`
6. Click "Create invalidation"

## 📡 API Documentation

### Base URL
```
https://0108izew87.execute-api.us-east-1.amazonaws.com/dev
```

### Endpoints

#### 1. Query Books
**Endpoint**: `GET /query/books`
**Purpose**: List available books
**Response**:
```json
{
  "books": [
    {
      "title": "Ramayana",
      "filename": "Ramayana.txt",
      "lastModified": "2025-08-03T16:55:30+00:00",
      "size": 2328165
    }
  ],
  "count": 1
}
```

#### 2. Ask Question
**Endpoint**: `POST /query`
**Purpose**: Process Q&A requests
**Request Body**:
```json
{
  "question": "Who is Rama?",
  "book_title": "Ramayana"
}
```
**Response**:
```json
{
  "answer": "Rama is the main protagonist of the Ramayana..."
}
```

#### 3. Upload Book
**Endpoint**: `POST /upload`
**Purpose**: Upload new book files
**Request**: Multipart form data
**Response**:
```json
{
  "message": "Book uploaded successfully",
  "filename": "new_book.txt"
}
```

### Error Responses
```json
{
  "error": "Error message"
}
```

## ⚙️ Configuration

### Environment Variables

#### Lambda Functions
- `DYNAMODB_TABLE`: DynamoDB table name
- `S3_BUCKET`: S3 bucket for raw files
- `BEDROCK_REGION`: AWS region for Bedrock

#### Frontend
- `VITE_API_URL`: API Gateway URL
- `VITE_COGNITO_USER_POOL_ID`: Cognito User Pool ID
- `VITE_COGNITO_CLIENT_ID`: Cognito App Client ID

### AWS IAM Permissions

#### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/book-embeddings-dev"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::epic-s3-bucket-ramayana",
        "arn:aws:s3:::epic-s3-bucket-ramayana/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Lambda Function Errors
**Issue**: "Unable to import module"
**Solution**: Check handler configuration and deployment package structure

#### 2. API Gateway 502 Errors
**Issue**: Internal server error
**Solution**: Check Lambda function logs in CloudWatch

#### 3. CORS Errors
**Issue**: Frontend can't access API
**Solution**: Verify CORS headers in Lambda responses

#### 4. Authentication Errors
**Issue**: "User is not confirmed"
**Solution**: Confirm user in Cognito Console or enable auto-confirmation

#### 5. Content Filtering Issues
**Issue**: Inappropriate content in responses
**Solution**: Check content filter configuration and word lists

### Debugging Steps

#### 1. Check CloudWatch Logs
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/epic"
```

#### 2. Test Lambda Functions Directly
```bash
aws lambda invoke --function-name epic-query-function --payload '{"body": "{\"question\":\"test\",\"book_title\":\"test\"}"}' response.json
```

#### 3. Test API Endpoints
```bash
curl -X POST "https://0108izew87.execute-api.us-east-1.amazonaws.com/dev/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "book_title": "test"}'
```

## ✨ Features

### Core Features
- ✅ **AI-Powered Q&A**: Intelligent question answering
- ✅ **Multi-Book Support**: Upload and query multiple books
- ✅ **Content Filtering**: Automatic inappropriate content detection
- ✅ **Hybrid Search**: Semantic + keyword search
- ✅ **Responsive UI**: Mobile-friendly interface
- ✅ **Real-time Processing**: Fast response times

### Advanced Features
- ✅ **Context-Aware Filtering**: Different filters for different content types
- ✅ **Response Validation**: Quality checks for AI responses
- ✅ **Detailed Logging**: Comprehensive debugging information
- ✅ **Error Handling**: Graceful error management
- ✅ **CORS Support**: Cross-origin resource sharing
- ✅ **Authentication**: Optional user authentication

### Technical Features
- ✅ **Vector Embeddings**: High-dimensional text representations
- ✅ **Cosine Similarity**: Accurate similarity calculations
- ✅ **Prompt Engineering**: Optimized LLM prompts
- ✅ **Decimal Handling**: Proper JSON serialization
- ✅ **Memory Optimization**: Efficient resource usage
- ✅ **Scalable Architecture**: Cloud-native design

## 📝 Notes

### Development History
- Initial setup with basic Q&A functionality
- Added content filtering for inappropriate language
- Implemented hybrid search for better accuracy
- Enhanced prompt engineering for better responses
- Added authentication and authorization
- Deployed to production with CDN

### Future Enhancements
- User management and book sharing
- Advanced analytics and usage tracking
- Multi-language support
- Voice input/output capabilities
- Advanced content moderation
- Performance optimizations

### Security Considerations
- All API endpoints use HTTPS
- Content filtering prevents inappropriate responses
- Authentication protects sensitive operations
- CORS properly configured
- IAM roles follow least privilege principle

---

**Last Updated**: August 2025
**Version**: 1.0.0
**Maintainer**: Epic Web App Team 