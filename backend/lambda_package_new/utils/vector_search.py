import boto3
import numpy as np
from typing import List, Dict, Any
import os
from botocore.exceptions import ClientError
from decimal import Decimal

class VectorSearch:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.environ['EMBEDDINGS_TABLE'])
        
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        # Convert any Decimal values to float
        vec1 = [float(x) if isinstance(x, Decimal) else x for x in vec1]
        vec2 = [float(x) if isinstance(x, Decimal) else x for x in vec2]
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def find_relevant_chunks(self, query_embedding: List[float], book_title: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find the most relevant chunks for a given query embedding and book title.
        
        Args:
            query_embedding: The embedding vector of the query
            book_title: The title of the book to search in
            top_k: Number of most relevant chunks to return
            
        Returns:
            List of dictionaries containing chunk information and similarity scores
        """
        try:
            # Query DynamoDB for chunks of the specified book
            response = self.table.query(
                IndexName='book_title-index',
                KeyConditionExpression='book_title = :title',
                ExpressionAttributeValues={
                    ':title': book_title
                }
            )
            
            chunks = response['Items']
            
            # Calculate similarity scores
            scored_chunks = []
            for chunk in chunks:
                # Convert embedding from DynamoDB to list of floats
                chunk_embedding = [float(x) if isinstance(x, Decimal) else x for x in chunk['embedding']]
                similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                scored_chunks.append({
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'similarity_score': float(similarity),  # Convert to float for JSON serialization
                    'chunk_number': chunk['chunk_number']
                })
            
            # Sort by similarity score and return top_k results
            scored_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
            return scored_chunks[:top_k]
            
        except ClientError as e:
            print(f"Error querying DynamoDB: {e}")
            return [] 