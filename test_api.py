"""
Simple test script to verify the AI Tech Counsellor implementation
Run this after starting the FastAPI server to test the flow
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_conversation_flow():
    """Test the complete conversation flow"""
    
    print("🚀 Testing AI Tech Counsellor API with Gemini integration...")
    
    # 1. Start conversation
    print("\n1. Starting conversation...")
    response = requests.post(f"{BASE_URL}/start")
    data = response.json()
    session_id = data["session_id"]
    print(f"Session ID: {session_id}")
    print(f"Message: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 2. Submit personal info
    print("\n2. Submitting personal info...")
    personal_info = {
        "session_id": session_id,
        "name": "John Doe",
        "location": "New York",
        "education": "Computer Science"
    }
    response = requests.post(f"{BASE_URL}/personal-info", json=personal_info)
    data = response.json()
    print(f"Message: {data['message']}")
    print(f"Question: {data['question']}")
    
    # 3. Select domain
    print("\n3. Selecting domain...")
    domain_answer = {
        "session_id": session_id,
        "answer": "backend development"
    }
    response = requests.post(f"{BASE_URL}/answer", json=domain_answer)
    data = response.json()
    print(f"Message: {data['message']}")
    print(f"Question: {data['question']}")
    print(f"Progress: {data.get('progress', 0):.1f}%")
    
    # 4. Answer domain questions (simulate answers)
    print("\n4. Answering domain questions...")
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
            print("\n🎉 Assessment completed!")
            print(f"Final message: {data['message']}")
            if data['recommendations'].get('explanation'):
                print(f"\nPersonalized Explanation:\n{data['recommendations']['explanation']}")
            print(f"\nRecommendations: {json.dumps({k: v for k, v in data['recommendations'].items() if k != 'explanation'}, indent=2)}")
            break
        else:
            print(f"Progress: {data.get('progress', 0):.1f}%")
            if data.get('question'):
                print(f"Next question: {data['question']}")
    
    # 5. Check session status
    print("\n5. Checking final session status...")
    response = requests.get(f"{BASE_URL}/session/{session_id}")
    data = response.json()
    print(f"Final status: {json.dumps(data, indent=2)}")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    try:
        test_conversation_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")