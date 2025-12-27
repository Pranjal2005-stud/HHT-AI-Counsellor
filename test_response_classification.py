#!/usr/bin/env python3
"""
Test script for the new response classification system
Demonstrates how the engine handles different types of user responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import TechCounsellorEngine, ResponseType
from state import ConversationState, ConversationStage

def test_response_classification():
    """Test the response classification system"""
    engine = TechCounsellorEngine()
    
    print("=== RESPONSE CLASSIFICATION TESTS ===\n")
    
    test_cases = [
        # POSITIVE responses
        ("yes", ResponseType.POSITIVE),
        ("definitely", ResponseType.POSITIVE),
        ("I have used it", ResponseType.POSITIVE),
        ("implemented that", ResponseType.POSITIVE),
        ("familiar with it", ResponseType.POSITIVE),
        
        # NEGATIVE responses
        ("no", ResponseType.NEGATIVE),
        ("never", ResponseType.NEGATIVE),
        ("haven't used it", ResponseType.NEGATIVE),
        ("not familiar", ResponseType.NEGATIVE),
        
        # CONFUSED responses
        ("what is that?", ResponseType.CONFUSED),
        ("not sure", ResponseType.CONFUSED),
        ("can you explain?", ResponseType.CONFUSED),
        ("what does it mean?", ResponseType.CONFUSED),
        ("?", ResponseType.CONFUSED),
        ("unclear", ResponseType.CONFUSED),
        
        # OFF_TOPIC responses
        ("I like pizza", ResponseType.OFF_TOPIC),
        ("tell me about your day", ResponseType.OFF_TOPIC),
        ("random text here", ResponseType.OFF_TOPIC),
    ]
    
    for user_input, expected in test_cases:
        result = engine.classify_response(user_input)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{user_input}' → {result.value} (expected: {expected.value})")
    
    print("\n" + "="*50 + "\n")

def test_assessment_flow():
    """Test the complete assessment flow with different response types"""
    engine = TechCounsellorEngine()
    
    # Create test state
    state = ConversationState()
    state.stage = ConversationStage.DOMAIN_EVALUATION
    state.selected_domain = "backend"
    state.current_question_index = 0
    
    print("=== ASSESSMENT FLOW TESTS ===\n")
    print(f"Domain: {state.selected_domain}")
    print(f"Starting question index: {state.current_question_index}")
    print(f"Starting score: {state.current_score}/{state.max_possible_score}\n")
    
    # Test scenarios
    scenarios = [
        ("yes", "POSITIVE - should advance"),
        ("what is REST API?", "CONFUSED - should explain, not advance"),
        ("I like cats", "OFF_TOPIC - should redirect, not advance"),
        ("no", "NEGATIVE - should advance"),
    ]
    
    for user_input, description in scenarios:
        print(f"User input: '{user_input}' ({description})")
        
        # Get current question
        current_question = engine.get_next_question(state)
        if current_question:
            print(f"Current question: {current_question['question']}")
        
        # Process response
        result = engine.process_assessment_response(state, user_input)
        
        print(f"Response type: {result['type']}")
        print(f"Message: {result['message']}")
        if result.get('explanation'):
            print(f"Explanation: {result['explanation']}")
        print(f"Advance question: {result['advance']}")
        print(f"New question index: {state.current_question_index}")
        print(f"New score: {state.current_score}/{state.max_possible_score}")
        print("-" * 40)

def demonstrate_examples():
    """Show example outputs for different response types"""
    engine = TechCounsellorEngine()
    
    print("=== EXAMPLE OUTPUTS ===\n")
    
    # Create sample state
    state = ConversationState()
    state.stage = ConversationStage.DOMAIN_EVALUATION
    state.selected_domain = "backend"
    state.current_question_index = 0
    
    examples = [
        {
            "input": "yes, I've built REST APIs",
            "expected_behavior": "POSITIVE → Add score, advance to next question"
        },
        {
            "input": "no, never used it",
            "expected_behavior": "NEGATIVE → No score, but advance to next question"
        },
        {
            "input": "what is Docker?",
            "expected_behavior": "CONFUSED → Explain concept, repeat same question"
        },
        {
            "input": "I prefer tea over coffee",
            "expected_behavior": "OFF_TOPIC → Redirect politely, repeat same question"
        }
    ]
    
    for example in examples:
        print(f"Input: '{example['input']}'")
        print(f"Expected: {example['expected_behavior']}")
        
        # Get current question before processing
        question_before = state.current_question_index
        score_before = state.current_score
        
        # Process the response
        result = engine.process_assessment_response(state, example['input'])
        
        print(f"Actual result:")
        print(f"  - Type: {result['type']}")
        print(f"  - Message: {result['message']}")
        if result.get('explanation'):
            print(f"  - Explanation: {result['explanation'][:100]}...")
        print(f"  - Question index: {question_before} → {state.current_question_index}")
        print(f"  - Score: {score_before} → {state.current_score}")
        print()

if __name__ == "__main__":
    print("Testing Response Classification System\n")
    
    test_response_classification()
    test_assessment_flow()
    demonstrate_examples()
    
    print("✓ All tests completed!")