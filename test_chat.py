"""
Test script for the ChatGPT-like interface
Run this after starting the backend server
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat_interface():
    """Test the complete chat conversation flow"""
    
    print("Testing AI Tech Counsellor Chat Interface...")
    
    # 1. Start conversation
    print("\n1. Starting conversation...")
    response = requests.post(f"{BASE_URL}/start")
    data = response.json()
    session_id = data["session_id"]
    print(f"Session ID: {session_id}")
    
    # 2. Submit personal info step by step
    print("\n2. Submitting personal info...")
    personal_info = {
        "session_id": session_id,
        "name": "Alex",
        "location": "San Francisco",
        "education": "Computer Science"
    }
    response = requests.post(f"{BASE_URL}/personal-info", json=personal_info)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 3. Select domain
    print("\n3. Selecting domain...")
    domain_answer = {
        "session_id": session_id,
        "answer": "backend development"
    }
    response = requests.post(f"{BASE_URL}/answer", json=domain_answer)
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 4. Answer assessment questions
    print("\n4. Answering assessment questions...")
    answers = ["yes", "no", "yes", "yes", "no", "yes", "no", "yes", "no", "yes"]
    
    for i, answer in enumerate(answers):
        print(f"\nQuestion {i+1}: Answering '{answer}'")
        question_answer = {
            "session_id": session_id,
            "answer": answer
        }
        response = requests.post(f"{BASE_URL}/answer", json=question_answer)
        data = response.json()
        
        if data.get("completed"):
            print("\nAssessment completed!")
            print(f"Final message: {data['message']}")
            if data['recommendations'].get('explanation'):
                print(f"\\nPersonalized Explanation:\\n{data['recommendations']['explanation']}")
            break
        else:
            if data.get('question'):
                print(f"Next question: {data['question']}")
    
    # 5. Test post-assessment chat
    print("\n5. Testing post-assessment chat...")
    chat_questions = [
        "How can I improve my skills?",
        "What should I focus on next?",
        "How long will it take to advance?"
    ]
    
    for question in chat_questions:
        print(f"\nUser: {question}")
        chat_request = {
            "session_id": session_id,
            "answer": question
        }
        response = requests.post(f"{BASE_URL}/chat", json=chat_request)
        data = response.json()
        print(f"AI: {data['message']}")
    
    print("\nChat interface test completed successfully!")

if __name__ == "__main__":
    try:
        test_chat_interface()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")