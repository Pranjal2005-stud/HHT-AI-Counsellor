"""
Test script for State Machine based AI Tech Counsellor
Tests deterministic flow and interruption handling
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_state_machine_flow():
    """Test the complete state machine flow with interruptions"""
    
    print("Testing State Machine AI Tech Counsellor...")
    
    # 1. Start conversation
    print("\n1. Starting conversation...")
    response = requests.post(f"{BASE_URL}/start")
    data = response.json()
    session_id = data["session_id"]
    print(f"Session ID: {session_id}")
    print(f"Message: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 2. Test greeting interruption
    print("\n2. Testing greeting interruption...")
    answer_request = {"session_id": session_id, "answer": "Hi there!"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 3. Provide name
    print("\n3. Providing name...")
    answer_request = {"session_id": session_id, "answer": "John"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 4. Provide location
    print("\n4. Providing location...")
    answer_request = {"session_id": session_id, "answer": "New York"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 5. Provide education
    print("\n5. Providing education...")
    answer_request = {"session_id": session_id, "answer": "Computer Science"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 6. Test confusion in domain selection
    print("\n6. Testing confusion in domain selection...")
    answer_request = {"session_id": session_id, "answer": "I don't understand"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 7. Select domain
    print("\n7. Selecting domain...")
    answer_request = {"session_id": session_id, "answer": "backend development"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 8. Test clarification question during assessment
    print("\n8. Testing clarification question...")
    answer_request = {"session_id": session_id, "answer": "What is HTTP?"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 9. Answer the assessment question
    print("\n9. Answering assessment question...")
    answer_request = {"session_id": session_id, "answer": "yes"}
    response = requests.post(f"{BASE_URL}/answer", json=answer_request)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    print(f"Progress: {data.get('progress', 0):.1f}%")
    
    # 10. Continue with more answers to complete assessment
    print("\n10. Completing assessment...")
    answers = ["no", "yes", "somewhat", "yes", "no", "yes", "no", "yes", "no"]
    
    for i, answer in enumerate(answers):
        print(f"\nQuestion {i+2}: Answering '{answer}'")
        answer_request = {"session_id": session_id, "answer": answer}
        response = requests.post(f"{BASE_URL}/answer", json=answer_request)
        data = response.json()
        
        if data.get("completed"):
            print("\nAssessment completed!")
            print(f"Final message: {data['message']}")
            print(f"Recommendations: {json.dumps(data['recommendations'], indent=2)}")
            break
        else:
            print(f"Progress: {data.get('progress', 0):.1f}%")
            if data.get('question'):
                print(f"Next question: {data['question']}")
    
    # 11. Test post-assessment chat
    print("\n11. Testing post-assessment chat...")
    chat_request = {"session_id": session_id, "answer": "How can I improve my backend skills?"}
    response = requests.post(f"{BASE_URL}/chat", json=chat_request)
    data = response.json()
    print(f"Chat response: {data['message']}")
    
    # 12. Check final session status
    print("\n12. Checking final session status...")
    response = requests.get(f"{BASE_URL}/session/{session_id}")
    data = response.json()
    print(f"Final status: {json.dumps(data, indent=2)}")
    
    print("\nState machine test completed successfully!")

def test_interruption_scenarios():
    """Test various interruption scenarios"""
    
    print("\n" + "="*50)
    print("Testing Interruption Scenarios")
    print("="*50)
    
    # Start new session
    response = requests.post(f"{BASE_URL}/start")
    session_id = response.json()["session_id"]
    
    # Quick setup to assessment stage
    setup_requests = [
        {"session_id": session_id, "answer": "Alice"},
        {"session_id": session_id, "answer": "California"},
        {"session_id": session_id, "answer": "Self-taught"},
        {"session_id": session_id, "answer": "frontend development"}
    ]
    
    for req in setup_requests:
        requests.post(f"{BASE_URL}/answer", json=req)
    
    # Test different interruption types
    interruptions = [
        ("Off-topic question", "What's the weather like?"),
        ("Confusion", "I don't understand this question"),
        ("Clarification", "What does DOM mean?"),
        ("Greeting", "Hello again!"),
        ("Valid answer", "yes")
    ]
    
    for test_name, user_input in interruptions:
        print(f"\nTesting: {test_name}")
        print(f"User input: '{user_input}'")
        
        answer_request = {"session_id": session_id, "answer": user_input}
        response = requests.post(f"{BASE_URL}/answer", json=answer_request)
        data = response.json()
        
        print(f"Response: {data['message']}")
        print(f"Question: {data.get('question', 'N/A')}")
        print(f"Progress changed: {data.get('progress', 0) > 0}")

if __name__ == "__main__":
    try:
        test_state_machine_flow()
        test_interruption_scenarios()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        print("Run: python main_v2.py")
    except Exception as e:
        print(f"Error: {e}")