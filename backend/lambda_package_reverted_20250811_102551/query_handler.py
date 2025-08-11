import json
import os
import boto3
from typing import Dict, Any
from decimal import Decimal

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('book-embeddings-dev')

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

def find_relevant_chunks(question_embedding: list, book_title: str) -> list:
    """Find relevant chunks using simple similarity."""
    try:
        print(f"Searching for book_title: '{book_title}'")
        
        # Use the GSI to query by book_title
        response = table.query(
            IndexName='book_title-index',
            KeyConditionExpression='book_title = :book_title',
            ExpressionAttributeValues={':book_title': book_title}
        )
        
        chunks = response.get('Items', [])
        print(f"Query returned {len(chunks)} items")
        
        if not chunks:
            print("No chunks found, returning empty list")
            return []
        
        print(f"Processing {len(chunks)} chunks")
        
        # Simple similarity calculation (cosine similarity without numpy)
        def cosine_similarity(vec1, vec2):
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        
        # Calculate similarities
        scored_chunks = []
        for chunk in chunks:
            chunk_embedding = [float(x) for x in chunk.get('embedding', [])]
            similarity = cosine_similarity(question_embedding, chunk_embedding)
            
            scored_chunks.append({
                'text': chunk.get('text', ''),
                'similarity': similarity,
                'chunk_id': chunk.get('chunk_id', '')
            })
        
        # Sort by similarity and return top 3
        scored_chunks.sort(key=lambda x: x['similarity'], reverse=True)
        print(f"Returning {len(scored_chunks[:3])} top chunks")
        return scored_chunks[:3]
        
    except Exception as e:
        print(f"Error finding relevant chunks: {e}")
        return []

def build_prompt(question: str, chunks: list) -> str:
    """Build prompt for LLM."""
    context = "\n\n".join([f"Context {i+1}: {chunk['text']}" for i, chunk in enumerate(chunks)])
    
    prompt = f"""You are a helpful assistant that answers questions based on the provided context. Answer ONLY using information from the provided context. Do not make assumptions or inferences.

Question: {question}

Context:
{context}

Answer:"""
    
    return prompt

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
        print(f"Generated embedding of length: {len(question_embedding)}")
        
        # Find relevant chunks
        relevant_chunks = find_relevant_chunks(question_embedding, book_title)
        print(f"Found {len(relevant_chunks)} relevant chunks")
        
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
        prompt = build_prompt(question, relevant_chunks)
        print(f"Built prompt of length: {len(prompt)}")
        
        # Get LLM response
        answer = get_llm_response(prompt)
        print(f"Generated answer: {answer[:100]}...")
        
        # Validate response quality
        if len(answer.strip()) < 10:
            answer = "I cannot find a clear answer to this question in the provided context."
        
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