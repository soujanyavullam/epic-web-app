import boto3
from typing import List, Dict, Any
import os
from botocore.exceptions import ClientError
from decimal import Decimal
import re

class VectorSearch:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.environ['EMBEDDINGS_TABLE'])
        
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        # Convert any Decimal values to float
        vec1 = [float(x) if isinstance(x, Decimal) else x for x in vec1]
        vec2 = [float(x) if isinstance(x, Decimal) else x for x in vec2]
        
        # Manual cosine similarity calculation without numpy
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = sum(a * a for a in vec1) ** 0.5
        norm_b = sum(b * b for b in vec2) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)
    
    def keyword_similarity(self, query: str, text: str) -> float:
        """Calculate keyword-based similarity between query and text."""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not query_words:
            return 0.0
            
        intersection = query_words.intersection(text_words)
        return len(intersection) / len(query_words)
    
    def hybrid_search(self, query: str, query_embedding: List[float], book_title: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword similarity.
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
            
            # Calculate both semantic and keyword similarity
            scored_chunks = []
            for chunk in chunks:
                # Semantic similarity
                chunk_embedding = [float(x) if isinstance(x, Decimal) else x for x in chunk['embedding']]
                semantic_similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                
                # Keyword similarity
                keyword_similarity = self.keyword_similarity(query, chunk['text'])
                
                # Combined score (weighted average)
                combined_score = 0.7 * semantic_similarity + 0.3 * keyword_similarity
                
                scored_chunks.append({
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'semantic_score': float(semantic_similarity),
                    'keyword_score': float(keyword_similarity),
                    'combined_score': float(combined_score),
                    'chunk_number': chunk['chunk_number'],
                    'book_title': chunk.get('book_title', book_title)
                })
            
            # Sort by combined score
            scored_chunks.sort(key=lambda x: x['combined_score'], reverse=True)
            return scored_chunks[:top_k]
            
        except ClientError as e:
            print(f"Error in hybrid search: {e}")
            return [] 