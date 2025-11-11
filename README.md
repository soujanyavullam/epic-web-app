# 📚 Epic Library - AI-Powered Book Q&A System

An intelligent web application that allows users to ask questions about uploaded books and receive context-aware answers using AWS services, vector embeddings, and large language models.

## 🎯 Overview

Epic Library is a full-stack AI-powered application that enables users to:
- **Upload books** as text files or from GitHub repositories
- **Ask questions** about any uploaded book
- **Receive intelligent answers** powered by Amazon Bedrock AI models
- **Search semantically** using vector embeddings for accurate context retrieval

The system uses advanced NLP techniques including hybrid search (semantic + keyword), content filtering, and prompt engineering to deliver high-quality, contextually relevant responses.

## ✨ Key Features

### Core Functionality
- 🤖 **AI-Powered Q&A**: Ask questions about any uploaded book and get intelligent, context-aware answers
- 📖 **Multi-Book Support**: Upload and query multiple books simultaneously
- 🔍 **Hybrid Search**: Combines semantic vector search with keyword matching for better accuracy
- 📝 **Content Filtering**: Automatic detection and filtering of inappropriate language
- 🔐 **User Authentication**: AWS Cognito integration for secure user management
- 📤 **Multiple Upload Methods**: Upload books via file upload or GitHub repository links

### Technical Features
- ⚡ **Serverless Architecture**: Fully serverless using AWS Lambda
- 🚀 **Scalable Design**: Cloud-native architecture that scales automatically
- 🔒 **Secure**: JWT-based authentication, IAM roles, and encrypted data storage
- 📊 **Real-time Processing**: Fast response times with optimized vector search
- 🎨 **Modern UI**: Responsive React frontend with TypeScript
- 📱 **Mobile-Friendly**: Works seamlessly on desktop and mobile devices

## 🏗️ Architecture

### High-Level Flow
```
User → React Frontend → CloudFront CDN → API Gateway → Lambda Functions
                                                              ↓
                                    DynamoDB (Embeddings) + S3 (Raw Files) + Bedrock (AI)
```

### Technology Stack

**Frontend:**
- React 19 with TypeScript
- Vite for build tooling
- Amazon Cognito Identity JS for authentication
- Modern CSS with responsive design

**Backend:**
- Python 3.9+ (Lambda runtime)
- AWS Lambda for serverless compute
- Amazon Bedrock (Titan models) for AI/ML
- Amazon DynamoDB for vector storage
- Amazon S3 for file storage

**Infrastructure:**
- AWS API Gateway (REST API)
- Amazon CloudFront (CDN)
- AWS Cognito (Authentication)
- Route 53 (DNS)
- CloudWatch (Monitoring & Logging)

## 📁 Project Structure

```
epic-web-app/
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── BookQA.tsx      # Main Q&A interface
│   │   │   ├── BookUpload.tsx  # File upload component
│   │   │   ├── RepoUpload.tsx  # GitHub repo upload
│   │   │   ├── Auth.tsx        # Authentication UI
│   │   │   └── ...
│   │   ├── utils/              # Utility functions
│   │   ├── config/             # Configuration files
│   │   └── App.tsx             # Main app component
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # Python backend
│   ├── src/
│   │   ├── query_handler.py    # Main Q&A Lambda function
│   │   ├── upload_handler.py   # File upload Lambda
│   │   ├── list_books.py       # List books Lambda
│   │   ├── auth_middleware.py  # JWT validation
│   │   └── utils/
│   │       ├── vector_search.py    # Vector similarity search
│   │       ├── prompt_builder.py   # LLM prompt construction
│   │       └── content_filter.py   # Content moderation
│   ├── infrastructure/         # CloudFormation templates
│   └── requirements.txt
│
├── deployment/                 # Deployment scripts
├── docs/                       # Additional documentation
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- AWS CLI configured with appropriate credentials
- AWS account with access to:
  - Lambda, API Gateway, DynamoDB, S3, Bedrock, Cognito, CloudFront

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd epic-web-app
```

2. **Install frontend dependencies**
```bash
cd frontend
npm install
```

3. **Install backend dependencies**
```bash
cd ../backend
pip install -r requirements.txt
```

4. **Configure AWS Cognito** (for authentication)
```bash
cd ..
./setup-cognito.sh
```

5. **Configure environment variables**
   - Update `frontend/src/config/cognito.ts` with your Cognito details
   - Set Lambda environment variables in AWS Console:
     - `DYNAMODB_TABLE`: Your DynamoDB table name
     - `BOOKS_BUCKET`: Your S3 bucket name
     - `BEDROCK_REGION`: AWS region (e.g., `us-east-1`)

### Development

**Run frontend locally:**
```bash
cd frontend
npm run dev
```

**Deploy backend Lambda functions:**
```bash
cd backend/src
zip -r ../lambda_package.zip *.py utils/ auth_middleware.py
aws lambda update-function-code --function-name epic-query-function --zip-file fileb://../lambda_package.zip
```

## 📡 API Documentation

### Base URL
```
https://<your-api-gateway-url>/dev
```

### Endpoints

#### 1. List Books
**GET** `/query/books`

Returns a list of all available books.

**Response:**
```json
{
  "books": [
    {
      "title": "Ramayana",
      "filename": "Ramayana.txt",
      "lastModified": "2025-01-15T10:30:00Z",
      "size": 2328165,
      "type": "uploaded_book"
    }
  ],
  "count": 1
}
```

#### 2. Ask Question
**POST** `/query`

Ask a question about a specific book.

**Request Body:**
```json
{
  "question": "Who is the main character in this book?",
  "book_title": "Ramayana"
}
```

**Response:**
```json
{
  "answer": "The main character is Rama, who is...",
  "sources": ["chunk_1", "chunk_2"]
}
```

#### 3. Upload Book
**POST** `/upload`

Upload a new book file (requires authentication).

**Request:**
- Content-Type: `application/json`
- Body: `{ "filename": "book.txt", "file_content": "<base64-encoded-content>" }`

**Response:**
```json
{
  "message": "File uploaded successfully to S3",
  "filename": "book.txt",
  "s3_key": "book.txt"
}
```

#### 4. Upload Repository
**POST** `/repo`

Upload documentation from a GitHub repository (requires authentication).

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "book_title": "My Repository"
}
```

## 🔧 Configuration

### Frontend Configuration

**Cognito Settings** (`frontend/src/config/cognito.ts`):
```typescript
export const COGNITO_CONFIG = {
  UserPoolId: 'us-east-1_XXXXXXXXX',
  ClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
  Region: 'us-east-1'
};
```

### Backend Environment Variables

Set these in your Lambda function configuration:

- `DYNAMODB_TABLE`: DynamoDB table name (e.g., `book-embeddings-dev`)
- `BOOKS_BUCKET`: S3 bucket for raw text files (e.g., `epic-s3-bucket-ramayana`)
- `BEDROCK_REGION`: AWS region for Bedrock (e.g., `us-east-1`)

### AWS IAM Permissions

Lambda execution role needs:
- DynamoDB: `GetItem`, `Query`, `Scan`, `PutItem`
- S3: `GetObject`, `PutObject`, `ListBucket`
- Bedrock: `InvokeModel`
- Cognito: `GetUser` (for JWT validation)

## 🚢 Deployment

### Frontend Deployment

1. **Build the frontend:**
```bash
cd frontend
npm run build
```

2. **Deploy to S3:**
```bash
aws s3 sync dist/ s3://epic-web-app-static --delete
```

3. **Invalidate CloudFront cache:**
```bash
aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
```

### Backend Deployment

1. **Package Lambda functions:**
```bash
cd backend/src
zip -r ../lambda_package.zip *.py utils/ auth_middleware.py
```

2. **Update Lambda functions:**
```bash
aws lambda update-function-code \
  --function-name epic-query-function \
  --zip-file fileb://../lambda_package.zip

aws lambda update-function-code \
  --function-name list-books-function \
  --zip-file fileb://../lambda_package.zip

aws lambda update-function-code \
  --function-name epic-upload-function \
  --zip-file fileb://../lambda_package.zip
```

## 🔐 Security

- **Authentication**: AWS Cognito with JWT tokens
- **Authorization**: API Gateway with Cognito authorizers
- **Data Encryption**: At-rest encryption in S3 and DynamoDB
- **Network Security**: VPC configuration for private subnets
- **Content Filtering**: Automatic inappropriate content detection
- **CORS**: Properly configured cross-origin resource sharing
- **IAM**: Least privilege access policies

## 📚 Additional Documentation

- [Full Documentation](EPIC_WEB_APP_DOCUMENTATION.md) - Comprehensive system documentation
- [Architecture Diagram](ARCHITECTURE_DIAGRAM.md) - Detailed architecture diagrams
- [Authentication Setup](AUTHENTICATION_SETUP.md) - Cognito configuration guide
- [Quick Start Guide](QUICK_START.md) - 5-minute setup guide
- [Security Guide](SECURITY_GUIDE.md) - Security best practices

## 🛠️ Development

### Tech Stack Details

**Frontend:**
- React 19.1.0
- TypeScript 5.8.3
- Vite 7.0.4
- Amazon Cognito Identity JS 6.3.0

**Backend:**
- Python 3.9+
- boto3 1.26.0+
- langchain 0.0.267+
- numpy 1.21.0+
- PyJWT 2.8.0+

### Running Tests

```bash
# Frontend linting
cd frontend
npm run lint

# Backend (if tests exist)
cd backend
pytest
```

## 🐛 Troubleshooting

### Common Issues

**CORS Errors:**
- Verify API Gateway CORS configuration
- Check that Authorization header is allowed

**Authentication Errors:**
- Verify Cognito User Pool ID and Client ID
- Check JWT token expiration
- Ensure user is confirmed in Cognito

**Lambda Errors:**
- Check CloudWatch logs for detailed error messages
- Verify handler configuration matches function name
- Ensure all dependencies are included in deployment package

**Bedrock Access:**
- Verify Bedrock is enabled in your AWS account
- Check IAM permissions for `bedrock:InvokeModel`
- Ensure you're using the correct region

## 📝 License

[Add your license information here]

## 👥 Contributing

[Add contribution guidelines here]

## 📞 Support

For issues and questions, please [open an issue](link-to-issues) or contact the development team.

---

**Last Updated**: January 2025  
**Version**: 1.0.0 