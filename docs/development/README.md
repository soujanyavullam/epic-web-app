# 🛠️ Development Setup Guide

Complete guide for setting up the Epic Web App development environment.

## 🚀 **Quick Start**

1. **Clone the repository**
2. **Install dependencies**
3. **Configure AWS credentials**
4. **Set up local environment**
5. **Run the application**

## 📋 **Prerequisites**

### **Required Software**
- **Python 3.11+** - Backend development
- **Node.js 18+** - Frontend development
- **Git** - Version control
- **AWS CLI** - AWS service management
- **Docker** - Optional, for containerized development

### **AWS Account Requirements**
- **AWS Account** with appropriate permissions
- **IAM User** with programmatic access
- **S3 Vectors** service access
- **Lambda** execution permissions
- **API Gateway** access

## 🔧 **Installation Steps**

### **1. Clone Repository**
```bash
git clone <repository-url>
cd epic-web-app
```

### **2. Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### **3. Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Install development dependencies
npm install --save-dev
```

### **4. AWS Configuration**
```bash
# Configure AWS CLI
aws configure

# Enter your credentials:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: [your-region]
# Default output format: json
```

## ⚙️ **Environment Configuration**

### **Backend Environment Variables**
Create `.env` file in `backend/` directory:
```bash
# AWS Configuration
AWS_REGION=us-east-1
VECTOR_BUCKET_NAME=epic-vector-bucket
VECTOR_INDEX_NAME=book-embeddings-index
S3_BUCKET_NAME=epic-s3-bucket-ramayana

# Lambda Configuration
LAMBDA_FUNCTION_NAME=epic-query-handler
API_GATEWAY_URL=https://your-api-gateway-url.amazonaws.com

# Bedrock Configuration
BEDROCK_MODEL_ID=amazon.titan-text-express-v1
BEDROCK_MAX_TOKENS=1000
BEDROCK_TEMPERATURE=0.5

# Development Configuration
DEBUG=True
LOG_LEVEL=INFO
```

### **Frontend Environment Variables**
Create `.env` file in `frontend/` directory:
```bash
# API Configuration
REACT_APP_API_BASE_URL=https://your-api-gateway-url.amazonaws.com
REACT_APP_API_VERSION=v1

# Authentication
REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id
REACT_APP_COGNITO_CLIENT_ID=your-client-id
REACT_APP_COGNITO_REGION=us-east-1

# Development Configuration
REACT_APP_DEBUG=true
REACT_APP_LOG_LEVEL=info
```

## 🧪 **Local Development**

### **Backend Development**
```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Run local development server
python -m flask run --debug

# Or use the development script
python dev_server.py
```

### **Frontend Development**
```bash
cd frontend

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### **Lambda Function Testing**
```bash
cd backend

# Test Lambda function locally
python -m pytest tests/

# Test specific function
python -c "
from query_handler_s3_vectors import lambda_handler
import json

event = {
    'httpMethod': 'POST',
    'body': json.dumps({
        'question': 'What is this book about?',
        'book_title': 'test-book'
    })
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

## 🔍 **Testing & Debugging**

### **Unit Tests**
```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### **Integration Tests**
```bash
# Test S3 Vectors integration
cd backend
python debug_s3_vectors.py

# Test API endpoints
python test_api.py
```

### **Debugging Tools**
- **VS Code**: Use Python and TypeScript extensions
- **PyCharm**: Professional Python IDE with AWS integration
- **AWS Toolkit**: VS Code extension for AWS services
- **CloudWatch Logs**: Monitor Lambda execution logs

## 📚 **Development Workflow**

### **1. Feature Development**
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# Test locally
# Commit changes
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/new-feature
```

### **2. Testing**
```bash
# Run all tests
npm run test:all

# Run specific test suite
npm run test:backend
npm run test:frontend

# Run with coverage
npm run test:coverage
```

### **3. Code Quality**
```bash
# Backend linting
cd backend
flake8 .
black .
isort .

# Frontend linting
cd frontend
npm run lint
npm run lint:fix
```

## 🚀 **Deployment**

### **Development Deployment**
```bash
# Deploy to development environment
./deploy.sh dev

# Deploy specific components
./deploy_lambda_updates.sh
./deploy_faiss_integration.sh
```

### **Production Deployment**
```bash
# Deploy to production
./deploy.sh prod

# Deploy with specific configuration
./deploy.sh prod --config production.yaml
```

## 🔧 **Common Development Tasks**

### **Adding New Lambda Function**
1. Create function file in `backend/`
2. Add to `requirements.txt`
3. Update deployment scripts
4. Test locally
5. Deploy to AWS

### **Adding New API Endpoint**
1. Create Lambda function
2. Update API Gateway configuration
3. Add CORS headers
4. Test endpoint
5. Update frontend

### **Adding New AWS Service**
1. Update IAM permissions
2. Add service client initialization
3. Update environment variables
4. Test integration
5. Update documentation

## 📖 **Development Resources**

### **Documentation**
- [AWS Services Overview](../aws/README.md)
- [S3 Vectors Guide](../aws/s3-vectors.md)
- [API Reference](../api/README.md)

### **External Resources**
- [AWS SDK for Python](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [React Documentation](https://reactjs.org/docs/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)

## 🆘 **Troubleshooting**

### **Common Issues**

#### **AWS Credentials Not Working**
```bash
# Check credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

#### **Python Dependencies Issues**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **Node.js Dependencies Issues**
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### **S3 Vectors Connection Issues**
```bash
# Check service availability
aws s3vectors list-vectors --vector-bucket-name epic-vector-bucket

# Verify permissions
aws iam get-user
aws iam list-attached-user-policies --user-name your-username
```

### **Getting Help**
1. **Check logs**: CloudWatch, console, terminal
2. **Review documentation**: This guide and related docs
3. **Search issues**: GitHub issues, Stack Overflow
4. **Ask team**: Slack, email, meetings

## 📝 **Development Standards**

### **Code Style**
- **Python**: PEP 8, Black formatter
- **TypeScript**: ESLint, Prettier
- **Git**: Conventional commits
- **Documentation**: Markdown, docstrings

### **Testing Requirements**
- **Unit tests**: 80%+ coverage
- **Integration tests**: All API endpoints
- **E2E tests**: Critical user flows
- **Performance tests**: Lambda cold starts

### **Security**
- **Secrets**: Use environment variables
- **IAM**: Least privilege principle
- **Input validation**: Sanitize all inputs
- **HTTPS**: Always use secure connections

## 🔄 **Continuous Integration**

### **GitHub Actions**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/
```

This setup guide provides everything needed to get started with development on the Epic Web App project. Follow the steps in order and refer to the troubleshooting section if you encounter any issues. 