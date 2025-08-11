import boto3
import numpy as np
from typing import List, Dict, Any
import os
from botocore.exceptions import ClientError
from decimal import Decimal
import re
import faiss  # Add FAISS import
import time   # Add time import for index caching

class VectorSearch:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.environ['EMBEDDINGS_TABLE'])
        # Add FAISS index caching
        self.faiss_indices = {}
        self.index_build_times = {}
        self.chunk_mapping = {}  # Map FAISS indices to chunk_ids
        
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        # Convert any Decimal values to float
        vec1 = [float(x) if isinstance(x, Decimal) else x for x in vec1]
        vec2 = [float(x) if isinstance(x, Decimal) else x for x in vec2]
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def keyword_similarity(self, query: str, text: str) -> float:
        """Calculate keyword-based similarity between query and text."""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not query_words:
            return 0.0
            
        intersection = query_words.intersection(text_words)
        return len(intersection) / len(query_words)
    
    # New FAISS methods
    def _build_faiss_index(self, book_title: str, vectors: List[List[float]], chunk_ids: List[str]) -> faiss.Index:
        """Build FAISS index for a specific book."""
        try:
            # Convert to numpy array with float32 for FAISS
            vectors_array = np.array(vectors, dtype=np.float32)
            
            # Create index - using Inner Product for cosine similarity
            # Note: FAISS doesn't have direct cosine similarity, so we normalize vectors
            index = faiss.IndexFlatIP(vectors_array.shape[1])  # Inner Product
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(vectors_array)
            
            # Add vectors to index
            index.add(vectors_array)
            
            # Store chunk_id mapping for this book
            self.chunk_mapping[book_title] = chunk_ids
            
            print(f"Built FAISS index for {book_title} with {len(vectors)} vectors")
            return index
            
        except Exception as e:
            print(f"Error building FAISS index: {e}")
            raise
    
    def _get_or_build_index(self, book_title: str) -> faiss.Index:
        """Get cached index or build new one."""
        current_time = time.time()
        
        # Check if we have a cached index
        if book_title in self.faiss_indices:
            # Check if index is still valid (rebuild every hour)
            if current_time - self.index_build_times.get(book_title, 0) < 3600:
                return self.faiss_indices[book_title]
        
        # Build new index
        vectors, chunk_ids = self._get_book_vectors_and_ids(book_title)
        if not vectors:
            raise ValueError(f"No vectors found for book: {book_title}")
        
        index = self._build_faiss_index(book_title, vectors, chunk_ids)
        
        # Cache the index
        self.faiss_indices[book_title] = index
        self.index_build_times[book_title] = current_time
        
        return index
    
    def _get_book_vectors_and_ids(self, book_title: str) -> tuple[List[List[float]], List[str]]:
        """Get all vectors and chunk_ids for a specific book from DynamoDB."""
        try:
            response = self.table.query(
                IndexName='book_title-index',
                KeyConditionExpression='book_title = :title',
                ExpressionAttributeValues={
                    ':title': book_title
                }
            )
            
            vectors = []
            chunk_ids = []
            for chunk in response['Items']:
                # Convert Decimal to float
                embedding = [float(x) if isinstance(x, Decimal) else x for x in chunk['embedding']]
                vectors.append(embedding)
                chunk_ids.append(chunk['chunk_id'])
            
            return vectors, chunk_ids
            
        except ClientError as e:
            print(f"Error getting vectors from DynamoDB: {e}")
            return [], []
    
    def _get_chunks_by_indices(self, book_title: str, indices: List[int], top_k: int) -> List[Dict[str, Any]]:
        """Get chunk metadata by FAISS indices from DynamoDB."""
        try:
            # Get chunk_ids from the mapping
            if book_title not in self.chunk_mapping:
                print(f"No chunk mapping found for book: {book_title}")
                return []
            
            chunk_ids = self.chunk_mapping[book_title]
            
            # Get chunks by chunk_ids
            results = []
            for idx in indices:
                if idx < len(chunk_ids):
                    chunk_id = chunk_ids[idx]
                    
                    # Get chunk from DynamoDB
                    response = self.table.get_item(Key={'chunk_id': chunk_id})
                    if 'Item' in response:
                        chunk = response['Item']
                        results.append({
                            'chunk_id': chunk['chunk_id'],
                            'text': chunk['text'],
                            'chunk_number': chunk['chunk_number'],
                            'book_title': chunk.get('book_title', book_title),
                            'semantic_score': 0.0,  # Will be updated later
                            'keyword_score': 0.0,   # Will be updated later
                            'combined_score': 0.0   # Will be updated later
                        })
                        
                        if len(results) >= top_k:
                            break
            
            return results
            
        except ClientError as e:
            print(f"Error getting chunks by indices: {e}")
            return []
    
    def hybrid_search_faiss(self, query: str, query_embedding: List[float], book_title: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using FAISS for vector similarity + DynamoDB for metadata.
        """
        try:
            # Get or build FAISS index
            index = self._get_or_build_index(book_title)
            
            # Normalize query vector for cosine similarity
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            # Perform FAISS search
            D, I = index.search(query_vector, top_k)
            
            # Get metadata for top results
            results = self._get_chunks_by_indices(book_title, I[0].tolist(), top_k)
            
            # Add similarity scores and calculate combined scores
            for i, result in enumerate(results):
                if i < len(D[0]):
                    # FAISS returns inner product scores, convert to similarity
                    semantic_score = float(D[0][i])
                    result['semantic_score'] = semantic_score
                    
                    # Calculate keyword similarity
                    keyword_score = self.keyword_similarity(query, result['text'])
                    result['keyword_score'] = keyword_score
                    
                    # Combined score (weighted average)
                    result['combined_score'] = 0.7 * semantic_score + 0.3 * keyword_score
            
            # Sort by combined score
            results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"Error in FAISS hybrid search: {e}")
            # Fallback to original method
            return self.hybrid_search(query, query_embedding, book_title, top_k)
    
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