# Deployment Directory

This directory contains all deployment scripts, configuration files, and infrastructure templates for the Epic Library project.

## 📁 Directory Structure

```
deployment/
├── scripts/              # Deployment and setup scripts
├── config/               # Configuration files (JSON)
├── infrastructure/       # CloudFormation templates (YAML)
└── *.py                  # Python deployment utilities
```

## 📜 Scripts (`scripts/`)

### Root Level Scripts
- `createLambda.sh` - Create Lambda function
- `createNumpy.sh` - Create NumPy layer
- `createNumpyLayer.sh` - Create NumPy layer for Lambda
- `setup-cognito.sh` - Setup AWS Cognito User Pool
- `update-cognito-config.sh` - Update Cognito configuration

### Backend Deployment Scripts
- `deploy_faiss_integration.sh` - Deploy FAISS integration
- `deploy_lambda_updates.sh` - Deploy Lambda function updates
- `deploy_logout_handler.sh` - Deploy logout handler
- `deploy_s3_vectors_functions.sh` - Deploy S3 vector functions
- `deploy_secure_api.sh` - Deploy secure API
- `create_faiss_layer.sh` - Create FAISS layer
- `fix_all_cors.sh` - Fix CORS issues
- `fix_cors_options.sh` - Fix CORS OPTIONS requests
- `package_reverted_query.sh` - Package reverted query handler

### Frontend Deployment Scripts
- `frontend-deploy.sh` - Deploy frontend to S3/CloudFront

## ⚙️ Configuration Files (`config/`)

- `acm-validation-records.json` - ACM certificate validation records
- `cloudfront-config.json` - CloudFront distribution configuration
- `cloudfront-current-config.json` - Current CloudFront configuration
- `cloudfront-updated-config.json` - Updated CloudFront configuration
- `route53-alias-records.json` - Route 53 DNS alias records
- `s3-bucket-policy.json` - S3 bucket policy
- `user-pool-config.json` - Cognito User Pool configuration

## 🏗️ Infrastructure Templates (`infrastructure/`)

CloudFormation/SAM templates for AWS infrastructure:

- `api_gateway.yaml` - API Gateway configuration
- `api_gateway_api_key.yaml` - API Gateway with API key
- `api_gateway_s3_vectors.yaml` - API Gateway for S3 vectors
- `api_gateway_secure.yaml` - Secure API Gateway configuration
- `logout_handler.yaml` - Logout handler Lambda function
- `s3_vectors_setup.yaml` - S3 vectors setup
- `vpc_private_api.yaml` - VPC private API configuration

## 🚀 Quick Start

### Deploy Backend
```bash
cd deployment/scripts
./deploy_lambda_updates.sh
```

### Deploy Frontend
```bash
cd deployment/scripts
./frontend-deploy.sh
```

### Setup Cognito
```bash
cd deployment/scripts
./setup-cognito.sh
```

### Deploy Infrastructure
```bash
cd deployment/infrastructure
aws cloudformation deploy --template-file api_gateway.yaml --stack-name epic-api
```

## 📝 Notes

- All scripts should be run from the project root directory
- Ensure AWS CLI is configured with appropriate credentials
- Check script paths if they reference files in other directories
- Update any hardcoded paths in scripts if needed after moving files

