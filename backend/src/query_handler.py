import json
import os
import boto3
from typing import Dict, Any
from utils.vector_search import VectorSearch
from utils.prompt_builder import PromptBuilder
from utils.content_filter import ContentFilter
# from auth_middleware import require_auth, get_user_from_event
from decimal import Decimal

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
vector_search = VectorSearch()
prompt_builder = PromptBuilder()
content_filter = ContentFilter()

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

# @require_auth
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
        
        # Get user information from authenticated request
        # user = get_user_from_event(event)
        # print(f"Request from user: {user.get('username') if user else 'Unknown'}")
        
        # Get embedding for the question
        question_embedding = get_embedding(question)
        
        # Find relevant chunks using hybrid search
        relevant_chunks = vector_search.hybrid_search(
            query=question,
            query_embedding=question_embedding,
            book_title=book_title
        )
        
        # Debug: Log the chunks being used
        print(f"Found {len(relevant_chunks)} relevant chunks for question: {question}")
        for i, chunk in enumerate(relevant_chunks):
            print(f"Chunk {i+1} (combined: {chunk['combined_score']:.3f}, semantic: {chunk['semantic_score']:.3f}, keyword: {chunk['keyword_score']:.3f}): {chunk['text'][:200]}...")
        
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
        
        # Debug: Log the prompt being sent to LLM
        print(f"Prompt sent to LLM: {prompt[:500]}...")
        
        # Get LLM response
        answer = get_llm_response(prompt)
        
        # Debug: Log the response
        print(f"LLM Response: {answer}")
        
        # Filter inappropriate content from the response
        # Use context-aware filtering for historical/religious texts
        context_type = "religious" if "ramayana" in book_title.lower() else "general"
        filtered_answer, replaced_words = content_filter.filter_sensitive_content(answer, context_type)
        
        # Log filtering activity
        if replaced_words:
            print(f"Content filter replaced words: {replaced_words}")
            print(f"Original response: {answer}")
            print(f"Filtered response: {filtered_answer}")
        
        # Validate response quality
        if len(filtered_answer.strip()) < 10:
            filtered_answer = "I cannot find a clear answer to this question in the provided context."
        elif "cannot find" not in filtered_answer.lower() and len(relevant_chunks) == 0:
            filtered_answer = "I cannot find a clear answer to this question in the provided context."
        
        # Convert any Decimal values to float before JSON serialization
        response_data = {
            'answer': filtered_answer
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
