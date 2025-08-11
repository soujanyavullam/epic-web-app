import json
import boto3
import os
from typing import List, Dict, Any
from decimal import Decimal
import concurrent.futures
from tqdm import tqdm
import time
import chardet

def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def upload_to_s3(book_title: str, book_text: str) -> None:
    """Upload raw book text to S3."""
    s3 = boto3.client('s3')
    bucket_name = 'epic-s3-bucket-ramayana'
    key = f"{book_title}.txt"
    
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=book_text.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"✅ Uploaded {book_title}.txt to S3")
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")

def get_embedding(text: str) -> List[float]:
    """Get embedding for text using Bedrock."""
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-2')
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
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
            if attempt == max_retries - 1:
                print(f"Error getting embedding after {max_retries} attempts: {e}")
                raise
            time.sleep(retry_delay)
            retry_delay *= 2  # exponential backoff

def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    """Split text into chunks of approximately chunk_size characters."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(word) + 1  # +1 for space
        if current_size + word_size > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def process_chunk(args: tuple) -> Dict[str, Any]:
    """Process a single chunk and return the item for DynamoDB."""
    chunk, book_title, chunk_number = args
    try:
        embedding = get_embedding(chunk)
        decimal_embedding = [Decimal(str(x)) for x in embedding]
        
        return {
            'chunk_id': f"{book_title}-{chunk_number}",
            'book_title': book_title,
            'chunk_number': chunk_number,
            'text': chunk,
            'embedding': decimal_embedding
        }
    except Exception as e:
        print(f"Error processing chunk {chunk_number} of {book_title}: {e}")
        return None

def ingest_book(book_title: str, book_text: str) -> None:
    """Ingest a book into DynamoDB with embeddings using parallel processing."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('book-embeddings-dev')
    
    # Split book into chunks
    chunks = chunk_text(book_text)
    print(f"\nProcessing {len(chunks)} chunks for {book_title}")
    
    # Prepare arguments for parallel processing
    chunk_args = [(chunk, book_title, i) for i, chunk in enumerate(chunks)]
    
    # Process chunks in parallel with progress bar
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_chunk, args) for args in chunk_args]
        
        # Use tqdm to show progress
        for future in tqdm(concurrent.futures.as_completed(futures), 
                         total=len(futures), 
                         desc=f"Processing {book_title}"):
            item = future.result()
            if item:
                try:
                    table.put_item(Item=item)
                except Exception as e:
                    print(f"Error storing chunk in DynamoDB: {e}")

if __name__ == "__main__":
    # Get the absolute path to the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    raw_text_dir = os.path.join(project_root, "raw_text")
    
    print(f"Looking for text files in: {raw_text_dir}")
    
    if not os.path.exists(raw_text_dir):
        print(f"Error: Directory {raw_text_dir} does not exist")
        exit(1)
    
    # Process each text file
    text_files = [f for f in os.listdir(raw_text_dir) if f.endswith('.txt')]
    print(f"Found {len(text_files)} text files to process")
    
    for filename in text_files:
        book_title = os.path.splitext(filename)[0]
        file_path = os.path.join(raw_text_dir, filename)
        print(f"\nProcessing file: {file_path}")
        
        try:
            # Detect file encoding
            encoding = detect_encoding(file_path)
            print(f"Detected encoding: {encoding}")
            
            # Read file with detected encoding
            with open(file_path, 'r', encoding=encoding) as file:
                book_text = file.read()
            
            # Upload to S3 first
            upload_to_s3(book_title, book_text)
            
            # Then process for DynamoDB
            ingest_book(book_title, book_text)
            
            print(f"✅ Successfully processed {book_title}")
            
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            continue 