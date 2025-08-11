import re
from typing import List, Tuple

class ContentFilter:
    def __init__(self):
        # Define inappropriate words and their alternatives
        self.inappropriate_words = {
            'rape': 'assault',
            'raped': 'assaulted',
            'raping': 'assaulting',
            'rapist': 'assailant',
            'fuck': 'damn',
            'fucking': 'damned',
            'shit': 'stuff',
            'bitch': 'person',
            'whore': 'person',
            'slut': 'person',
            'bastard': 'person',
            'cunt': 'person',
            'pussy': 'person',
            'dick': 'person',
            'cock': 'person',
            'penis': 'private parts',
            'vagina': 'private parts',
            'sex': 'intimate relations',
            'sexual': 'intimate',
            'intercourse': 'intimate relations',
            'fornication': 'inappropriate relations',
            'prostitution': 'inappropriate activities',
            'porn': 'inappropriate content',
            'pornography': 'inappropriate content',
            'nude': 'inappropriate',
            'naked': 'inappropriate',
            'nudity': 'inappropriate content'
        }
        
        # Create regex patterns for word boundaries
        self.word_patterns = {}
        for word, replacement in self.inappropriate_words.items():
            # Match whole words only (case insensitive)
            pattern = r'\b' + re.escape(word) + r'\b'
            self.word_patterns[pattern] = replacement
    
    def filter_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Filter inappropriate content from text.
        
        Args:
            text: The text to filter
            
        Returns:
            Tuple of (filtered_text, list_of_replaced_words)
        """
        if not text:
            return text, []
        
        original_text = text
        filtered_text = text
        replaced_words = []
        
        # Apply each filter pattern with case preservation
        for pattern, replacement in self.word_patterns.items():
            matches = re.findall(pattern, filtered_text, re.IGNORECASE)
            if matches:
                replaced_words.extend(matches)
                # Replace with case preservation
                filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
        
        # If no replacements were made, return original text
        if not replaced_words:
            return original_text, []
        
        return filtered_text, list(set(replaced_words))
    
    def is_appropriate(self, text: str) -> bool:
        """
        Check if text contains inappropriate content.
        
        Args:
            text: The text to check
            
        Returns:
            True if text is appropriate, False otherwise
        """
        if not text:
            return True
        
        text_lower = text.lower()
        
        for pattern in self.word_patterns.keys():
            if re.search(pattern, text_lower):
                return False
        
        return True
    
    def get_filter_stats(self, text: str) -> dict:
        """
        Get statistics about content filtering.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with filtering statistics
        """
        filtered_text, replaced_words = self.filter_text(text)
        
        return {
            'original_length': len(text),
            'filtered_length': len(filtered_text),
            'replaced_words': replaced_words,
            'replacement_count': len(replaced_words),
            'is_appropriate': self.is_appropriate(text)
        } 

    def filter_sensitive_content(self, text: str, context: str = "") -> Tuple[str, List[str]]:
        """
        Filter sensitive content with context awareness.
        
        Args:
            text: The text to filter
            context: Context about the content (e.g., "historical", "religious")
            
        Returns:
            Tuple of (filtered_text, list_of_replaced_words)
        """
        # For historical or religious contexts, use more appropriate terminology
        if "historical" in context.lower() or "religious" in context.lower():
            historical_replacements = {
                'rape': 'violation',
                'raped': 'violated',
                'raping': 'violating',
                'rapist': 'perpetrator',
                'assault': 'attack',
                'assaulted': 'attacked',
                'assaulting': 'attacking'
            }
            
            # Apply historical context replacements
            filtered_text = text
            replaced_words = []
            
            for word, replacement in historical_replacements.items():
                pattern = r'\b' + re.escape(word) + r'\b'
                matches = re.findall(pattern, filtered_text, re.IGNORECASE)
                if matches:
                    replaced_words.extend(matches)
                    filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
            
            if replaced_words:
                return filtered_text, list(set(replaced_words))
        
        # Fall back to regular filtering
        return self.filter_text(text) 

    def add_custom_filter(self, word: str, replacement: str):
        """
        Add a custom word to the filter.
        
        Args:
            word: The word to filter
            replacement: The replacement word
        """
        self.inappropriate_words[word.lower()] = replacement
        pattern = r'\b' + re.escape(word) + r'\b'
        self.word_patterns[pattern] = replacement
    
    def remove_filter(self, word: str):
        """
        Remove a word from the filter.
        
        Args:
            word: The word to remove from filtering
        """
        if word.lower() in self.inappropriate_words:
            del self.inappropriate_words[word.lower()]
            pattern = r'\b' + re.escape(word) + r'\b'
            if pattern in self.word_patterns:
                del self.word_patterns[pattern]
    
    def get_filtered_words(self) -> List[str]:
        """
        Get list of currently filtered words.
        
        Returns:
            List of filtered words
        """
        return list(self.inappropriate_words.keys()) 