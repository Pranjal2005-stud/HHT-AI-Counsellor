#!/usr/bin/env python3
"""
Test script for entity extraction and persistence system
Demonstrates how the system extracts and stores personal details
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import TechCounsellorEngine
from state import ConversationState, ConversationStage

def test_entity_extraction():
    """Test entity extraction for name, location, and education"""
    engine = TechCounsellorEngine()
    state = ConversationState()
    
    print("=== ENTITY EXTRACTION TESTS ===\n")
    
    # Test name extraction
    print("1. NAME EXTRACTION:")
    name_tests = [
        ("John Smith", True),
        ("My name is Alice Johnson", True),
        ("I'm Bob", True),
        ("Call me Sarah", True),
        ("123", False),  # Invalid
        ("", False),     # Empty
        ("A very long name that exceeds reasonable limits for a person", False)
    ]
    
    for input_text, expected in name_tests:
        state.user_name = None  # Reset
        result = state.extract_name(input_text)\n        status = "✓" if result == expected else "✗"
        extracted = state.user_name if result else "None"
        print(f"{status} '{input_text}' → {extracted}")
    
    print("\\n2. LOCATION EXTRACTION:")
    location_tests = [
        ("New York", True),
        ("I'm from California", True),
        ("Live in London, UK", True),
        ("From Mumbai, India", True),
        ("123456", False),  # Invalid
        ("", False),        # Empty
    ]
    
    for input_text, expected in location_tests:
        state.user_location = None  # Reset
        result = state.extract_location(input_text)
        status = "✓" if result == expected else "✗"
        extracted = state.user_location if result else "None"
        print(f"{status} '{input_text}' → {extracted}")
    
    print("\\n3. EDUCATION EXTRACTION:")
    education_tests = [
        ("Computer Science", True),
        ("I studied Engineering", True),
        ("My degree is in Business", True),
        ("Bachelor's in Mathematics", True),
        ("12345", False),  # Invalid
        ("", False),       # Empty
    ]
    
    for input_text, expected in education_tests:
        state.user_education = None  # Reset
        result = state.extract_education(input_text)
        status = "✓" if result == expected else "✗"
        extracted = state.user_education if result else "None"
        print(f"{status} '{input_text}' → {extracted}")

def test_conversation_flow():
    """Test complete conversation flow with entity persistence"""
    engine = TechCounsellorEngine()
    state = ConversationState()
    
    print("\\n=== CONVERSATION FLOW TEST ===\\n")
    
    # Simulate conversation flow
    conversation_steps = [
        ("greeting", "Hello!", ConversationStage.ASK_NAME),
        ("name", "My name is John Doe", ConversationStage.ASK_LOCATION),
        ("location", "I'm from San Francisco", ConversationStage.ASK_EDUCATION),
        ("education", "I studied Computer Science", ConversationStage.DOMAIN_SELECTION),
    ]
    
    print(f"Initial stage: {state.stage}")
    print(f"Initial data: name={state.user_name}, location={state.user_location}, education={state.user_education}\\n")
    
    for step_name, user_input, expected_stage in conversation_steps:
        print(f"Step: {step_name}")
        print(f"User input: '{user_input}'")
        print(f"Current stage: {state.stage}")
        
        if state.stage in [ConversationStage.ASK_NAME, ConversationStage.ASK_LOCATION, ConversationStage.ASK_EDUCATION]:
            result = engine.process_personal_info(state, user_input)
            print(f"Processing result: {result}")
        elif state.stage == ConversationStage.GREETING:
            state.advance_to_next_stage()
        
        print(f"New stage: {state.stage}")
        print(f"Stored data: name={state.user_name}, location={state.user_location}, education={state.user_education}")
        print(f"Expected stage: {expected_stage}")
        print(f"Stage correct: {'✓' if state.stage == expected_stage else '✗'}")
        print("-" * 50)

def test_guardrails():
    """Test guardrails - system should never ask for info it already has"""
    engine = TechCounsellorEngine()
    state = ConversationState()
    
    print("\\n=== GUARDRAILS TEST ===\\n")
    
    # Pre-populate some data
    state.user_name = "Alice"
    state.user_location = "Boston"
    state.stage = ConversationStage.ASK_NAME
    
    print(f"Pre-populated: name={state.user_name}, location={state.user_location}")
    print(f"Current stage: {state.stage}")
    
    # Try to extract name again - should skip
    prompt = engine.get_personal_info_prompt(state)
    print(f"Prompt when name exists: '{prompt}'")
    print(f"Stage after prompt: {state.stage}")
    
    # Should advance to education since name and location exist
    if state.stage == ConversationStage.ASK_EDUCATION:
        print("✓ Correctly skipped asking for existing name and location")
    else:
        print("✗ Failed to skip existing information")

def demonstrate_examples():
    """Show example conversation with proper entity extraction"""
    print("\\n=== EXAMPLE CONVERSATION ===\\n")
    
    examples = [
        {
            "stage": "ASK_NAME",
            "input": "Hi, I'm Sarah Johnson",
            "expected_extraction": "Sarah Johnson",
            "expected_response": "Nice to meet you, Sarah Johnson!"
        },
        {
            "stage": "ASK_LOCATION", 
            "input": "I live in Seattle, Washington",
            "expected_extraction": "Seattle, Washington",
            "expected_response": "Great! Seattle, Washington sounds like a nice place."
        },
        {
            "stage": "ASK_EDUCATION",
            "input": "I have a degree in Software Engineering",
            "expected_extraction": "Software Engineering", 
            "expected_response": "Excellent! Software Engineering is a great background."
        }
    ]
    
    for example in examples:
        print(f"Stage: {example['stage']}")
        print(f"User says: '{example['input']}'")
        print(f"Expected extraction: {example['expected_extraction']}")
        print(f"Expected response: {example['expected_response']}")
        print()

if __name__ == "__main__":
    print("Testing Entity Extraction and Persistence System\\n")
    
    test_entity_extraction()
    test_conversation_flow()
    test_guardrails()
    demonstrate_examples()
    
    print("✓ All tests completed!")