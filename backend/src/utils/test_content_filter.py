#!/usr/bin/env python3
"""
Test script for content filter functionality.
"""

from content_filter import ContentFilter

def test_content_filter():
    """Test the content filter with various inputs."""
    
    filter = ContentFilter()
    
    # Test cases
    test_cases = [
        ("Rama killed Vaali because he raped Sita", "religious"),
        ("The story contains violence and assault", "general"),
        ("This is a normal response without issues", "general"),
        ("The text mentions sexual content", "general"),
        ("Historical accounts describe the violation", "religious")
    ]
    
    print("Testing Content Filter:")
    print("=" * 50)
    
    for text, context in test_cases:
        print(f"\nOriginal: {text}")
        print(f"Context: {context}")
        
        filtered, replaced = filter.filter_sensitive_content(text, context)
        print(f"Filtered: {filtered}")
        print(f"Replaced words: {replaced}")
        print("-" * 30)

if __name__ == "__main__":
    test_content_filter() 