#!/usr/bin/env python3
"""
Quick test for name extraction fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from state import ConversationState

def test_name_extraction():
    """Test the fixed name extraction"""
    
    test_cases = [
        ("Hy my name is Pranjal", "Pranjal"),
        ("Hi, I'm John Smith", "John Smith"),
        ("Hello my name is Sarah", "Sarah"),
        ("Hey, call me Bob", "Bob"),
        ("My name is Alice Johnson", "Alice Johnson"),
        ("I'm Mike", "Mike"),
        ("Pranjal", "Pranjal"),  # Direct name
        ("Hi there, I'm David Wilson", "David Wilson"),
    ]
    
    print("=== NAME EXTRACTION TEST ===\n")
    
    for input_text, expected in test_cases:
        state = ConversationState()
        result = state.extract_name(input_text)
        extracted = state.user_name if result else "FAILED"
        status = "✓" if extracted == expected else "✗"
        print(f"{status} '{input_text}' → '{extracted}' (expected: '{expected}')")

if __name__ == "__main__":
    test_name_extraction()