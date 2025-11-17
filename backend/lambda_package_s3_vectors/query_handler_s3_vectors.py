import json
import os
import boto3
from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
s3_vectors_client = boto3.client('s3vectors')

# Configuration
VECTOR_BUCKET_NAME = 'epic-vector-bucket'
VECTOR_INDEX_NAME = 'book-embeddings-index'
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'epic-s3-bucket-ramayana')

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

def search_s3_vectors(book_title: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar vectors in S3 Vectors."""
    try:
        # Use query_vectors method for similarity search with correct parameter names
        # Note: S3 Vectors filter syntax may be different - let's try without filter first
        print(f"Searching for book: {book_title}")
        
        # Try search without filter first to see what's returned
        response = s3_vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={'float32': query_embedding},  # Wrap embedding in float32 key as per S3 Vectors format
            topK=top_k * 2,  # Get more results since we'll filter manually
            returnMetadata=True  # Request metadata to be returned with results
        )
        
        print(f"S3 Vectors search successful for {book_title}")
        print(f"Full response structure: {json.dumps(response, default=str)}")
        
        results = response.get('vectors', [])
        print(f"Results from response: {json.dumps(results, default=str)}")
        print(f"Number of results returned: {len(results)}")
        
        # Debug: Show all vector keys and metadata to understand the format
        if results:
            print("All vector keys and metadata found:")
            for i, result in enumerate(results[:5]):  # Show first 5
                key = result.get('key', '')
                metadata = result.get('metadata', {})
                print(f"  {i+1}. Key: {key}")
                print(f"     Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
                if metadata and 'text' in metadata:
                    print(f"     Text preview: {metadata['text'][:100]}...")
                else:
                    print(f"     No text in metadata")
            
            # ADDITIONAL DEBUGGING: Log the complete structure of first result
            if results:
                print(f"\n=== COMPLETE FIRST RESULT STRUCTURE ===")
                first_result = results[0]
                print(f"First result type: {type(first_result)}")
                print(f"First result keys: {list(first_result.keys())}")
                print(f"First result full content: {json.dumps(first_result, default=str, indent=2)}")
                
                # Check if metadata exists and what it contains
                if 'metadata' in first_result:
                    metadata = first_result['metadata']
                    print(f"Metadata type: {type(metadata)}")
                    print(f"Metadata content: {json.dumps(metadata, default=str, indent=2)}")
                else:
                    print("NO METADATA FIELD FOUND in first result")
        else:
            print("No results returned from S3 Vectors query")
        
        # MANUAL FILTERING: Filter results by book title since S3 Vectors filter syntax is problematic
        print(f"\n=== MANUAL FILTERING ===")
        print(f"Requested book title: '{book_title}'")
        print(f"Total results before filtering: {len(results)}")
        
        filtered_results = []
        for result in results:
            vector_key = result.get('key', '')
            # Extract book title from key (format: book-title-chunkid)
            if '-' in vector_key:
                parts = vector_key.split('-')
                if len(parts) >= 3:
                    result_book_title = '-'.join(parts[:-1])
                else:
                    result_book_title = parts[0]
            else:
                result_book_title = vector_key
            
            print(f"  Key: {vector_key} -> Book: {result_book_title}")
            
            if result_book_title == book_title:
                filtered_results.append(result)
                print(f"    ✅ MATCH - Adding to filtered results")
            else:
                print(f"    ❌ NO MATCH - Skipping")
        
        print(f"Results after manual filtering: {len(filtered_results)}")
        
        # Return filtered results
        return filtered_results
        
    except Exception as e:
        print(f"Error in S3 Vectors search: {e}")
        # Fallback: try to get vectors directly by listing and filtering
        try:
            response = s3_vectors_client.list_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=VECTOR_INDEX_NAME,
                maxResults=1000
            )
            
            vectors = response.get('vectors', [])  # Use lowercase 'vectors' key
            # Filter by book title using the same logic as above
            book_vectors = []
            for v in vectors:
                vector_key = v.get('key', '')
                if '-' in vector_key:
                    parts = vector_key.split('-')
                    if len(parts) >= 3:
                        vector_book_title = '-'.join(parts[:-1])
                    else:
                        vector_book_title = parts[0]
                else:
                    vector_book_title = vector_key
                
                if vector_book_title == book_title:
                    book_vectors.append(v)
            
            if book_vectors:
                print(f"Found {len(book_vectors)} vectors for {book_title} via list_vectors")
                return book_vectors[:top_k]
            else:
                print(f"No vectors found for {book_title}")
                return []
                
        except Exception as fallback_e:
            print(f"Fallback search also failed: {fallback_e}")
            return []

def build_prompt(question: str, chunks: list) -> str:
    """Build a prompt for the LLM using relevant chunks."""
    # Handle both string chunks and dictionary chunks
    chunk_texts = []
    for i, chunk in enumerate(chunks):
        if isinstance(chunk, dict):
            # If chunk is a dictionary, try to extract text from S3 Vectors metadata
            if 'metadata' in chunk and 'text' in chunk['metadata']:
                chunk_texts.append(f"Chunk {i+1}: {chunk['metadata']['text']}")
            elif 'Metadata' in chunk and 'text' in chunk['Metadata']:
                chunk_texts.append(f"Chunk {i+1}: {chunk['Metadata']['text']}")
            elif 'text' in chunk:
                chunk_texts.append(f"Chunk {i+1}: {chunk['text']}")
            else:
                chunk_texts.append(f"Chunk {i+1}: {str(chunk)}")
        else:
            # If chunk is already a string, use it directly
            chunk_texts.append(f"Chunk {i+1}: {str(chunk)}")
    
    context = "\n\n".join(chunk_texts)
    
    prompt = f"""You are a helpful AI assistant that answers questions based on the provided text chunks. Please answer the following question using only the information from the chunks below. If the information is not available in the chunks, say so.

Text Chunks:
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
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': ''
            }

        # Parse request
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON body: {e}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                        'Access-Control-Max-Age': '86400',
                        'Access-Control-Allow-Credentials': 'true',
                        'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                    },
                    'body': json.dumps({
                        'error': 'Invalid JSON format in request body',
                        'message': str(e)
                    })
                }
        
        question = body.get('question', '')
        book_title = body.get('book_title', '')
        
        if not question or not book_title:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': 'Missing question or book_title parameter',
                    'message': 'Both question and book_title are required'
                })
            }
        
        print(f"Processing question: '{question}' for book: '{book_title}'")
        
        # Get embedding for the question
        try:
            question_embedding = get_embedding(question)
            print(f"Generated question embedding with {len(question_embedding)} dimensions")
        except Exception as e:
            print(f"Error generating question embedding: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': 'Failed to generate question embedding',
                    'message': str(e)
                })
            }
        
        # Find relevant chunks using S3 Vectors
        relevant_chunks = search_s3_vectors(book_title, question_embedding)
        
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
                    'error': f'No relevant content found for book: {book_title}',
                    'message': 'The book may not exist or may not have been processed yet'
                })
            }
        
        # Check if search results already contain the text content
        print(f"Checking if search results contain text content...")
        chunks_with_text = 0
        for chunk in relevant_chunks:
            if isinstance(chunk, dict) and 'metadata' in chunk and 'text' in chunk['metadata']:
                chunks_with_text += 1
        
        print(f"Found {chunks_with_text} chunks with text content out of {len(relevant_chunks)} total chunks")
        
        # If search results already have text, use them directly
        if chunks_with_text > 0:
            print("Using search results directly as they contain text content")
            enriched_chunks = relevant_chunks
        else:
            # Fetch the full vector content for each relevant chunk
            print(f"Fetching full content for {len(relevant_chunks)} relevant chunks...")
            enriched_chunks = []
            
            for chunk in relevant_chunks:
                vector_key = chunk.get('key', '')
                try:
                    # Get the full vector data including metadata and text content
                    # S3 Vectors get_vectors returns the complete vector with metadata
                    vector_data = s3_vectors_client.get_vectors(
                        vectorBucketName=VECTOR_BUCKET_NAME,
                        indexName=VECTOR_INDEX_NAME,
                        keys=[vector_key]
                    )
                    
                    if vector_data.get('vectors'):
                        full_vector = vector_data['vectors'][0]
                        print(f"Retrieved full vector for key: {vector_key}")
                        print(f"Full vector structure: {json.dumps(full_vector, default=str)}")
                        enriched_chunks.append(full_vector)
                    else:
                        print(f"No vector data found for key: {vector_key}")
                        enriched_chunks.append(chunk)  # Fallback to original chunk
                        
                except Exception as e:
                    print(f"Error retrieving vector data for key {vector_key}: {e}")
                    enriched_chunks.append(chunk)  # Fallback to original chunk
            
            print(f"Successfully enriched {len(enriched_chunks)} chunks with full content")
            
            # Additional debugging: Check what we actually got from get_vectors
            print(f"Enrichment debugging - checking enriched chunks structure:")
            for i, chunk in enumerate(enriched_chunks):
                print(f"  Chunk {i+1}: {type(chunk)}")
                if isinstance(chunk, dict):
                    print(f"    Keys: {list(chunk.keys())}")
                    if 'metadata' in chunk:
                        print(f"    Metadata keys: {list(chunk['metadata'].keys())}")
                        if 'text' in chunk['metadata']:
                            print(f"    Text preview: {chunk['metadata']['text'][:100]}...")
                        else:
                            print(f"    No text in metadata")
                    else:
                        print(f"    No metadata field")
                else:
                    print(f"    Not a dict: {chunk}")
        
        # Extract text from enriched chunks with reasonable token-based limits
        chunk_texts = []
        total_tokens = 0
        max_tokens_per_chunk = 1000   # Limit each chunk to ~1000 tokens (~4000 chars)
        max_total_tokens = 4000       # More reasonable limit for better context
        
        # If enrichment failed, try to use original search results
        if not enriched_chunks or all(isinstance(chunk, str) and not chunk.strip() for chunk in enriched_chunks):
            print("Enrichment failed, falling back to original search results")
            enriched_chunks = relevant_chunks
            
        # Final check: If we still don't have text content, try to get it from S3 directly
        chunks_with_text_final = 0
        for chunk in enriched_chunks:
            if isinstance(chunk, dict) and 'metadata' in chunk and 'text' in chunk['metadata']:
                chunks_with_text_final += 1
        
        if chunks_with_text_final == 0:
            print("WARNING: No text content found in any chunks after enrichment!")
            print("This suggests a fundamental issue with S3 Vectors metadata retrieval.")
            print("Attempting emergency fallback to get text content...")
            
            # Emergency fallback: Try to get text from S3 bucket directly
            try:
                import boto3
                s3_client = boto3.client('s3')
                
                emergency_chunks = []
                for chunk in relevant_chunks:
                    vector_key = chunk.get('key', '')
                    if vector_key:
                        # Try to get the original text file from S3
                        try:
                            # Try different possible paths for the text file
                            possible_paths = [
                                f"books/{vector_key}.txt",
                                f"books/{vector_key}",
                                f"{vector_key}.txt",
                                f"{vector_key}",
                                f"books/{book_title}/{vector_key}.txt",
                                f"books/{book_title}/{vector_key}"
                            ]
                            
                            text_content = None
                            successful_path = None
                            
                            for path in possible_paths:
                                try:
                                    print(f"    Trying path: {path}")
                                    response = s3_client.get_object(
                                        Bucket=S3_BUCKET_NAME,
                                        Key=path
                                    )
                                    text_content = response['Body'].read().decode('utf-8')
                                    successful_path = path
                                    print(f"    ✅ Found text at: {path}")
                                    break
                                except Exception as path_error:
                                    print(f"    ❌ Path failed: {path} - {path_error}")
                                    continue
                            
                            if not text_content:
                                raise Exception("No text file found at any of the attempted paths")
                            
                            emergency_chunk = {
                                'key': vector_key,
                                'metadata': {
                                    'text': text_content,
                                    'source': 'emergency_s3_fallback'
                                }
                            }
                            emergency_chunks.append(emergency_chunk)
                            print(f"Emergency fallback: Retrieved text for {vector_key}")
                            
                        except Exception as e:
                            print(f"Emergency fallback failed for {vector_key}: {e}")
                            # Create a minimal chunk with just the key
                            emergency_chunk = {
                                'key': vector_key,
                                'metadata': {
                                    'text': f"Text content for {vector_key} could not be retrieved. This may indicate a data processing issue.",
                                    'source': 'fallback_error'
                                }
                            }
                            emergency_chunks.append(emergency_chunk)
                
                if emergency_chunks:
                    print(f"Emergency fallback created {len(emergency_chunks)} chunks")
                    enriched_chunks = emergency_chunks
                else:
                    print("Emergency fallback also failed")
                    
            except Exception as e:
                print(f"Emergency fallback setup failed: {e}")
                # Last resort: Create informative error chunks
                enriched_chunks = [{
                    'key': chunk.get('key', 'unknown'),
                    'metadata': {
                        'text': f"Unable to retrieve text content for chunk {chunk.get('key', 'unknown')}. This indicates a system configuration issue that needs immediate attention.",
                        'source': 'last_resort_error'
                    }
                } for chunk in relevant_chunks]
        
        print(f"Extracting text from {len(enriched_chunks)} enriched chunks with token limits...")
        
        for i, chunk in enumerate(enriched_chunks):
            print(f"Processing chunk {i+1}: {type(chunk)}")
            if isinstance(chunk, dict):
                print(f"  Chunk keys: {list(chunk.keys())}")
                # Handle different response formats from S3 Vectors
                if 'metadata' in chunk and 'text' in chunk['metadata']:
                    print(f"  Found text in metadata: {chunk['metadata']['text'][:100]}...")
                    text = chunk['metadata']['text']
                elif 'Metadata' in chunk and 'text' in chunk['Metadata']:
                    print(f"  Found text in Metadata: {chunk['Metadata']['text'][:100]}...")
                    text = chunk['Metadata']['text']
                elif 'text' in chunk:
                    print(f"  Found text directly: {chunk['text'][:100]}...")
                    text = chunk['text']
                else:
                    print(f"  No text found, using str(chunk)")
                    text = str(chunk)
                
                # Estimate tokens (roughly 1 token = 4 characters)
                estimated_tokens = len(text) // 4
                
                # Truncate chunk if it's too long
                if estimated_tokens > max_tokens_per_chunk:
                    max_chars = max_tokens_per_chunk * 4
                    text = text[:max_chars] + "... [truncated]"
                    estimated_tokens = max_tokens_per_chunk
                    print(f"  Chunk truncated from {len(chunk.get('text', str(chunk)))} chars to {len(text)} chars (~{estimated_tokens} tokens)")
                
                # Check if adding this chunk would exceed total token limit
                if total_tokens + estimated_tokens > max_total_tokens:
                    print(f"  Stopping at chunk {i+1} to avoid exceeding {max_total_tokens} total tokens (current: {total_tokens})")
                    break
                
                print(f"  Extracted text: {text[:100]}... ({len(text)} chars, ~{estimated_tokens} tokens)")
                chunk_texts.append(text)
                total_tokens += estimated_tokens
            else:
                text = str(chunk)
                estimated_tokens = len(text) // 4
                
                if estimated_tokens > max_tokens_per_chunk:
                    max_chars = max_tokens_per_chunk * 4
                    text = text[:max_chars] + "... [truncated]"
                    estimated_tokens = max_tokens_per_chunk
                
                if total_tokens + estimated_tokens > max_total_tokens:
                    print(f"  Stopping at chunk {i+1} to avoid exceeding {max_total_tokens} total tokens (current: {total_tokens})")
                    break
                
                print(f"  Chunk is not dict, using str(chunk): {text[:100]}... ({len(text)} chars, ~{estimated_tokens} tokens)")
                chunk_texts.append(text)
                total_tokens += estimated_tokens
        
        print(f"Final text extraction: {len(chunk_texts)} chunks, {total_tokens} estimated tokens")
        
        # Debug: Show what text was extracted
        if chunk_texts:
            print("Extracted text previews:")
            for i, text in enumerate(chunk_texts[:3]):  # Show first 3 chunks
                print(f"  Chunk {i+1}: {text[:200]}...")
        else:
            print("WARNING: No text was extracted from chunks!")
            print("This will result in an empty prompt for the LLM.")
        
        # Check if we have any text content to work with
        if not chunk_texts or all(not text.strip() for text in chunk_texts):
            print("ERROR: No text content extracted from chunks")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'answer': 'The model cannot find sufficient information to answer the question.',
                    'question': question,
                    'book_title': book_title,
                    'relevant_chunks': relevant_chunks,
                    'enriched_chunks': enriched_chunks,
                    'chunks_used': len(relevant_chunks),
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': 'No text content found in retrieved chunks',
                    'debug_info': {
                        'chunks_found': len(relevant_chunks),
                        'text_extracted': len(chunk_texts),
                        'chunk_structure': [{'key': chunk.get('key', ''), 'has_metadata': 'metadata' in chunk, 'has_text': 'text' in chunk.get('metadata', {})} for chunk in relevant_chunks[:3]]
                    }
                })
            }
        
        # Build prompt with found chunks
        prompt = build_prompt(question, chunk_texts)
        
        # Get LLM response
        try:
            answer = get_llm_response(prompt)
            print(f"Generated LLM response with {len(answer)} characters")
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
                },
                'body': json.dumps({
                    'error': 'Failed to generate answer',
                    'message': str(e)
                })
            }
        
        # Prepare response
        response_data = {
            'answer': answer,
            'question': question,
            'book_title': book_title,
            'relevant_chunks': relevant_chunks,  # Keep original chunks for reference
            'enriched_chunks': enriched_chunks,  # Add enriched chunks with full content
            'chunks_used': len(relevant_chunks),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
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
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        } 