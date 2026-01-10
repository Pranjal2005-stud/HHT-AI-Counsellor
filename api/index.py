from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os
import random

# Import your modules
from state import ConversationState, ConversationStage
from state_controller import StateController
from engine import update_score, should_repeat

app = FastAPI(title="HHT AI Counsellor API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store sessions
sessions = {}
controller = StateController()

@app.get("/")
def read_root():
    return {"message": "HHT AI Counsellor API is running"}

@app.post("/start")
def start_conversation():
    session_id = str(uuid.uuid4())
    state = ConversationState()
    sessions[session_id] = state
    
    return {
        "session_id": session_id
    }

@app.post("/personal-info")
def submit_personal_info(request: dict):
    if request.get("session_id") in sessions:
        state = sessions[request["session_id"]]
        state.user_name = request.get("name")
        state.user_location = request.get("location")
        state.user_education = request.get("education")
    
    return {
        "message": "Thanks for the information!",
        "question": "Which tech domain interests you?"
    }

# Add all your other endpoints here (answer, chat, feedback, etc.)
# Copy from your main.py but keep it minimal

# Vercel handler
def handler(request, context):
    return app(request, context)