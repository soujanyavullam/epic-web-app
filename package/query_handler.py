import json
import os
import boto3
from typing import Dict, Any
from utils.vector_search import VectorSearch
from utils.prompt_builder import PromptBuilder

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
vector_search = VectorSearch()
prompt_builder = PromptBuilder()

def get_embedding(text: str) -> list:
    """Get embedding for text using Bedrock."""
    try:
        response = bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v1',
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
            modelId='anthropic.claude-v2',
            body=json.dumps({
                'prompt': prompt,
                'max_tokens_to_sample': 1000,
                'temperature': 0.5,
                'top_p': 1,
                'stop_sequences': ['\n\nHuman:']
            })
        )
        response_body = json.loads(response['body'].read())
        return response_body['completion']
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
                'body': json.dumps({
                    'error': f'No relevant content found for book: {book_title}'
                })
            }
        
        # Build prompt
        prompt = prompt_builder.build_qa_prompt(question, relevant_chunks)
        
        # Get LLM response
        answer = get_llm_response(prompt)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'answer': answer,
                'relevant_chunks': relevant_chunks
            })
        }
        
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        } 