from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import uuid
import json
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
sessions = {}

class ConversationState:
    def __init__(self):
        self.user_name = None
        self.selected_domain = None
        self.question_count = 0
        self.score = 0
        self.answers = []

@app.post("/start")
def start_conversation():
    session_id = str(uuid.uuid4())
    sessions[session_id] = ConversationState()
    return {"session_id": session_id}

@app.post("/personal-info")
def submit_personal_info(request: dict):
    if request.get("session_id") in sessions:
        state = sessions[request["session_id"]]
        state.user_name = request.get("name")
    return {"message": "Thanks!"}

@app.post("/answer")
def submit_answer(request: dict):
    if request.get("session_id") not in sessions:
        return {"message": "Session not found"}
    
    state = sessions[request["session_id"]]
    answer = request["answer"].lower()
    
    # Simple domain selection
    if not hasattr(state, 'selected_domain') or not state.selected_domain:
        domains = ['backend', 'frontend', 'data analytics', 'machine learning']
        for domain in domains:
            if domain in answer:
                state.selected_domain = domain
                return {
                    "message": f"Great! Let's assess your {domain} skills.",
                    "question": f"Do you have experience with {domain}?",
                    "completed": False
                }
    
    # Simple Q&A
    if not hasattr(state, 'question_count'):
        state.question_count = 0
        state.score = 0
    
    if answer in ['yes', 'y', 'sure']:
        state.score += 1
    
    state.question_count += 1
    
    if state.question_count >= 3:
        return {
            "message": "Assessment completed!",
            "completed": True,
            "recommendations": {
                "level": "Intermediate",
                "score": f"{state.score}/3",
                "topics": ["Practice more", "Build projects"],
                "projects": ["Todo app", "Portfolio site"]
            }
        }
    
    return {
        "message": "Good!",
        "question": f"Question {state.question_count + 1}: Do you know advanced concepts?",
        "completed": False
    }

@app.post("/chat")
def chat(request: dict):
    return {"message": "Thanks for your question!"}

# Vercel handler
handler = Mangum(app)