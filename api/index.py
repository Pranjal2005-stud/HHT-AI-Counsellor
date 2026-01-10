from http.server import BaseHTTPRequestHandler
import json
import uuid
import urllib.parse

# Simple in-memory storage
sessions = {}

class ConversationState:
    def __init__(self):
        self.user_name = None
        self.selected_domain = None
        self.question_count = 0
        self.score = 0
        self.answers = []

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        # Route handling
        path = self.path
        
        if path == '/api/start':
            session_id = str(uuid.uuid4())
            sessions[session_id] = ConversationState()
            response = {"session_id": session_id}
            
        elif path == '/api/personal-info':
            session_id = data.get("session_id")
            if session_id in sessions:
                state = sessions[session_id]
                state.user_name = data.get("name")
            response = {"message": "Thanks for the information!"}
            
        elif path == '/api/answer':
            session_id = data.get("session_id")
            if session_id not in sessions:
                response = {"message": "Session not found"}
            else:
                state = sessions[session_id]
                answer = data.get("answer", "").lower()
                
                # Domain selection
                if not hasattr(state, 'selected_domain') or not state.selected_domain:
                    domains = ['backend', 'frontend', 'data analytics', 'machine learning', 'devops', 'cybersecurity', 'data engineering', 'algorithms']
                    for domain in domains:
                        if domain in answer:
                            state.selected_domain = domain
                            state.question_count = 0
                            state.score = 0
                            response = {
                                "message": f"Great! Let's assess your {domain} skills.",
                                "question": f"Do you have experience with {domain} development?",
                                "completed": False
                            }
                            break
                    else:
                        response = {"message": "Please select a valid domain"}
                else:
                    # Handle answers
                    if answer in ['yes', 'y', 'sure', 'definitely']:
                        state.score += 1
                        msg = "Great!"
                    else:
                        msg = "No worries!"
                    
                    state.question_count += 1
                    
                    if state.question_count >= 3:
                        percentage = (state.score / 3) * 100
                        level = "Advanced" if percentage >= 80 else "Intermediate" if percentage >= 50 else "Beginner"
                        
                        response = {
                            "message": "Assessment completed!",
                            "completed": True,
                            "recommendations": {
                                "level": level,
                                "domain": state.selected_domain.title(),
                                "score": f"{state.score}/3",
                                "percentage": f"{percentage:.0f}%",
                                "topics": [f"{state.selected_domain} fundamentals", "Best practices", "Project development"],
                                "projects": [f"Basic {state.selected_domain} project", f"Advanced {state.selected_domain} app"],
                                "explanation": f"You scored {state.score} out of 3 questions correctly."
                            }
                        }
                    else:
                        questions = [
                            f"Are you familiar with {state.selected_domain} frameworks?",
                            f"Do you know {state.selected_domain} best practices?",
                            f"Have you worked on {state.selected_domain} projects?"
                        ]
                        response = {
                            "message": msg,
                            "question": questions[state.question_count - 1] if state.question_count <= len(questions) else "Do you have more experience?",
                            "completed": False
                        }
                        
        elif path == '/api/chat':
            response = {"message": "Thanks for your question! Keep learning and practicing."}
            
        else:
            response = {"message": "Endpoint not found"}
        
        self.wfile.write(json.dumps(response).encode('utf-8'))