import json
import os
import boto3
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
s3_vectors_client = boto3.client('s3vectors')

# Configuration
VECTOR_BUCKET_NAME = 'epic-vector-bucket'
VECTOR_INDEX_NAME = 'book-embeddings-index'

def convert_decimals_to_float(obj):
    """Convert Decimal values to float in a nested structure."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(v) for v in obj]
    return obj

def get_embedding(text: str) -> list:
    """Get embedding for text using Bedrock."""
    try:
        response = bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            body=json.dumps({
                'inputText': text
            })
        )
        response_body = json.loads(response['body'].read())
        return response_body['embedding']
    except Exception as e:
        print(f"Error getting embedding: {e}")
        raise

def get_llm_response(prompt: str) -> str:
    """Get response from LLM using Bedrock."""
    try:
        response = bedrock.invoke_model(
            modelId='amazon.titan-text-express-v1',
            body=json.dumps({
                'inputText': prompt,
                'textGenerationConfig': {
                    'maxTokenCount': 1000,
                    'temperature': 0.5,
                    'topP': 1,
                    'stopSequences': ['User:']
                }
            })
        )
        response_body = json.loads(response['body'].read())
        return response_body['results'][0]['outputText']
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        raise

def find_relevant_chunks_s3_vectors(question_embedding: list, book_title: str) -> list:
    """Find relevant chunks using S3 Vectors similarity search."""
    try:
        print(f"Searching for book_title: '{book_title}' using S3 Vectors")
        
        # Create search query for S3 Vectors
        search_request = {
            'Bucket': VECTOR_BUCKET_NAME,
            'IndexName': VECTOR_INDEX_NAME,
            'SearchConfiguration': {
                'VectorSearchConfiguration': {
                    'QueryVector': question_embedding,
                    'K': 5,
                    'FilterExpression': f"metadata.book_title = '{book_title}'"
                }
            }
        }
        
        response = s3_vectors_client.search(**search_request)
        
        print(f"S3 Vectors search returned {len(response.get('Hits', []))} results")
        
        # Format results
        relevant_chunks = []
        for hit in response.get('Hits', []):
            metadata = hit.get('Metadata', {})
            relevant_chunks.append({
                'text': metadata.get('text', ''),
                'chunk_id': metadata.get('chunk_id', ''),
                'similarity_score': hit.get('Score', 0.0)
            })
        
        return relevant_chunks
        
    except Exception as e:
        print(f"Error in S3 Vectors search: {e}")
        return []

def build_prompt(question: str, chunks: list) -> str:
    """Build prompt for LLM with relevant chunks."""
    if not chunks:
        return f"Question: {question}\n\nAnswer: I don't have enough information to answer this question."
    
    context = "\n\n".join([chunk['text'] for chunk in chunks])
    
    prompt = f"""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {question}

Answer:"""
    
    return prompt

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Q&A using S3 Vectors for vector search.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true'
                },
                'body': ''
            }

        # Parse request
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '')
        book_title = body.get('book_title', '')
        
        if not question or not book_title:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Missing question or book_title parameter'
                })
            }
        
        print(f"Processing question: '{question}' for book: '{book_title}'")
        
        # Get embedding for the question
        question_embedding = get_embedding(question)
        print(f"Generated question embedding with {len(question_embedding)} dimensions")
        
        # Find relevant chunks using S3 Vectors
        relevant_chunks = find_relevant_chunks_s3_vectors(question_embedding, book_title)
        
        if not relevant_chunks:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'error': f'No relevant content found for book: {book_title}'
                })
            }
        
        print(f"Found {len(relevant_chunks)} relevant chunks")
        
        # Build prompt with relevant chunks
        prompt = build_prompt(question, relevant_chunks)
        
        # Get LLM response
        answer = get_llm_response(prompt)
        
        # Prepare response
        response_data = {
            'answer': answer,
            'question': question,
            'book_title': book_title,
            'relevant_chunks': relevant_chunks,
            'chunks_used': len(relevant_chunks),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error in query handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        } 