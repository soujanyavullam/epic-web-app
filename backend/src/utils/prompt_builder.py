from typing import List, Dict, Any

class PromptBuilder:
    @staticmethod
    def build_qa_prompt(question: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        """
        Build a prompt for the LLM using the question and relevant text chunks.
        
        Args:
            question: The user's question
            relevant_chunks: List of relevant text chunks with their metadata
            
        Returns:
            A formatted prompt string
        """
        # Combine all relevant chunks into context with source information
        context_parts = []
        for i, chunk in enumerate(relevant_chunks):
            source_info = f"[Source: {chunk.get('book_title', 'Unknown')}, Chunk {i+1}, Combined Score: {chunk.get('combined_score', 0):.3f}]"
            context_parts.append(f"{source_info}\n{chunk['text']}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""You are a knowledgeable assistant that answers questions about books based on the provided context.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY using information from the provided context
2. If the answer is not clearly stated in the context, say "I cannot find a clear answer to this question in the provided context"
3. Do not make assumptions or inferences beyond what is explicitly stated
4. Be precise and accurate in your response
5. If you find conflicting information in the context, mention this
6. Cite specific parts of the context when possible
7. Use appropriate, family-friendly language in your responses
8. Avoid vulgar, offensive, or inappropriate terms
9. If discussing sensitive topics, use respectful and appropriate terminology
10. Maintain a scholarly and professional tone throughout your response

Context:
{context}

Question: {question}

Answer:"""
        
        return prompt 