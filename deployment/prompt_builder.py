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
        # Combine all relevant chunks into context
        context = "\n\n".join([
            f"Context {i+1}:\n{chunk['text']}"
            for i, chunk in enumerate(relevant_chunks)
        ])
        
        prompt = f"""You are a helpful assistant that answers questions about books based on the provided context.
Please answer the following question using ONLY the information from the provided context.
If the answer cannot be found in the context, please say so.

Context:
{context}

Question: {question}

Answer:"""
        
        return prompt 