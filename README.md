# Book Q&A Application

A web application that answers questions about books using AWS services and LLMs.

## Architecture

```
[User Input (Question + Book Title)]
     ↓
[Web App / API Gateway + Lambda]
     ↓
[Book Data Store (S3)]
     ↓
[Index + Embeddings Store (DynamoDB)]
     ↓
[LLM Query Handler (Lambda)]
     ↓
[LLM (OpenAI/Bedrock)]
     ↓
[Answer]
```

## Project Structure

```
epic-web-app/
├── backend/
│   ├── src/
│   │   ├── lambda/
│   │   │   ├── query_handler.py
│   │   │   └── search_handler.py
│   │   └── utils/
│   │       ├── vector_search.py
│   │       └── prompt_builder.py
│   ├── infrastructure/
│   │   ├── api_gateway.yaml
│   │   ├── lambda.yaml
│   │   └── iam_roles.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## Setup Instructions

1. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Configure AWS credentials and environment variables

4. Deploy the infrastructure:
```bash
cd backend/infrastructure
aws cloudformation deploy --template-file api_gateway.yaml --stack-name book-qa-api
```

## Features

- Question answering about specific books
- Vector similarity search for relevant context
- Integration with AWS Bedrock/OpenAI
- Scalable architecture for adding more books
- Simple and intuitive web interface

## Development

- Backend: Python 3.9+
- Frontend: React with TypeScript
- Infrastructure: AWS CloudFormation 