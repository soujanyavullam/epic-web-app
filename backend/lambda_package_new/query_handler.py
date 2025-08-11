import json
import os
import boto3
from typing import Dict, Any
from utils.vector_search import VectorSearch
from utils.prompt_builder import PromptBuilder
from decimal import Decimal

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
vector_search = VectorSearch()
prompt_builder = PromptBuilder()

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

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for processing book-related questions.
    
    Expected event format:
    {
        "question": "What is the main theme of the book?",
        "book_title": "The Great Gatsby"
    }
    """
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': ''
        }
    
    try:
        # Parse input
        body = json.loads(event['body'])
        question = body['question']
        book_title = body['book_title']
        
        # Get embedding for the question
        question_embedding = get_embedding(question)
        
        # Find relevant chunks
        relevant_chunks = vector_search.find_relevant_chunks(
            query_embedding=question_embedding,
            book_title=book_title
        )
        
        if not relevant_chunks:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': f'No relevant content found for book: {book_title}'
                })
            }
        
        # Build prompt
        prompt = prompt_builder.build_qa_prompt(question, relevant_chunks)
        
        # Get LLM response
        answer = get_llm_response(prompt)
        
        # Convert any Decimal values to float before JSON serialization
        response_data = {
            'answer': answer
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': json.dumps({
                'error': 'Internal server error'
            })
        } 