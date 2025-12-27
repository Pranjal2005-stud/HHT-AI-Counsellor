from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

from state import ConversationState, ConversationStage
from state_controller import StateController
from engine import update_score, should_repeat
from gemini_service import rephrase

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store sessions
sessions = {}
controller = StateController()

class Answer(BaseModel):
    message: str

class StartResponse(BaseModel):
    session_id: str
    message: str
    question: str

class PersonalInfo(BaseModel):
    session_id: str
    name: str
    location: str
    education: str

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

@app.post("/start")
def start_conversation():
    session_id = str(uuid.uuid4())
    state = ConversationState()
    sessions[session_id] = state
    
    return {
        "session_id": session_id,
        "message": "Hello! I'm your Tech Skills Counsellor.",
        "question": "What's your name?"
    }

@app.post("/personal-info")
def submit_personal_info(request: PersonalInfo):
    if request.session_id in sessions:
        state = sessions[request.session_id]
        state.user_name = request.name
        state.user_location = request.location
        state.user_education = request.education
    
    return {
        "message": "Thanks for the information!",
        "question": "Which tech domain interests you?"
    }

@app.post("/answer")
def submit_answer(request: AnswerRequest):
    if request.session_id not in sessions:
        return {"message": "Session not found"}
    
    state = sessions[request.session_id]
    
    # Valid domains
    valid_domains = ['backend', 'frontend', 'data analytics', 'machine learning', 'devops', 'cybersecurity', 'data engineering', 'algorithms']
    
    # If no domain selected yet, handle domain selection
    if not hasattr(state, 'selected_domain') or not state.selected_domain:
        user_domain = request.answer.lower().strip()
        
        # Check if user input matches any valid domain
        matched_domain = None
        for domain in valid_domains:
            if domain in user_domain or user_domain in domain:
                matched_domain = domain
                break
        
        if matched_domain:
            state.selected_domain = matched_domain
            state.question_count = 0
            state.score = 0
            state.answers = []
            return {
                "message": f"Great! Let's assess your {matched_domain} skills.",
                "question": f"Do you have experience with {matched_domain} development?",
                "completed": False
            }
        else:
            return {
                "message": "Please select from the available domains only.",
                "question": "Which tech domain interests you most? Choose from: Backend, Frontend, Data Analytics, Machine Learning, DevOps, Cybersecurity, Data Engineering, or Algorithms.",
                "completed": False
            }
    
    # Initialize tracking if needed
    if not hasattr(state, 'question_count'):
        state.question_count = 0
        state.score = 0
        state.answers = []
    
    # Process current answer
    user_answer = request.answer.lower().strip()
    is_yes = user_answer in ['yes', 'y', 'yeah', 'yep', 'sure', 'definitely']
    is_no = user_answer in ['no', 'n', 'nope', 'never', 'not really']
    
    # Questions and explanations for each domain
    domain_questions = {
        'frontend': [
            {"q": "Do you have experience with frontend development?", "exp": "Frontend development involves creating user interfaces using HTML, CSS, and JavaScript. It's what users see and interact with in web applications."},
            {"q": "Have you worked with React, Vue, or Angular?", "exp": "These are popular JavaScript frameworks that help build interactive web applications more efficiently with reusable components."},
            {"q": "Do you understand responsive design principles?", "exp": "Responsive design ensures websites work well on all devices (mobile, tablet, desktop) by adapting layout and content to different screen sizes."},
            {"q": "Are you familiar with CSS preprocessors like Sass or Less?", "exp": "CSS preprocessors add features like variables, nesting, and functions to CSS, making stylesheets more maintainable and organized."},
            {"q": "Have you used build tools like Webpack or Vite?", "exp": "Build tools bundle and optimize your code for production, handling tasks like minification, transpilation, and asset management."},
            {"q": "Do you know about web performance optimization?", "exp": "Performance optimization involves techniques like lazy loading, code splitting, and image optimization to make websites load faster."}
        ],
        'backend': [
            {"q": "Do you have experience with backend development?", "exp": "Backend development involves server-side programming, databases, and APIs that power web applications behind the scenes."},
            {"q": "Have you worked with databases like MySQL or PostgreSQL?", "exp": "Databases store and manage application data. SQL databases use structured tables and relationships to organize information."},
            {"q": "Are you familiar with REST API development?", "exp": "REST APIs allow different applications to communicate using HTTP methods (GET, POST, PUT, DELETE) to exchange data."},
            {"q": "Do you understand authentication and authorization?", "exp": "Authentication verifies user identity (login), while authorization determines what authenticated users can access or do."},
            {"q": "Have you used cloud services like AWS or Azure?", "exp": "Cloud platforms provide scalable infrastructure, databases, and services to deploy and run applications without managing physical servers."},
            {"q": "Do you know about microservices architecture?", "exp": "Microservices break large applications into smaller, independent services that can be developed, deployed, and scaled separately."}
        ]
    }
    
    # Get questions for current domain (fallback to generic if domain not found)
    questions = domain_questions.get(state.selected_domain, [
        {"q": f"Do you have experience with {state.selected_domain}?", "exp": f"This involves working with {state.selected_domain} technologies and concepts."},
        {"q": f"Have you built projects in {state.selected_domain}?", "exp": f"Practical experience building {state.selected_domain} projects is valuable for skill development."},
        {"q": f"Are you familiar with {state.selected_domain} best practices?", "exp": f"Best practices help ensure code quality, maintainability, and performance in {state.selected_domain}."},
        {"q": f"Do you understand {state.selected_domain} testing?", "exp": f"Testing ensures your {state.selected_domain} code works correctly and prevents bugs in production."},
        {"q": f"Have you worked with {state.selected_domain} tools?", "exp": f"Tools and frameworks make {state.selected_domain} development more efficient and productive."},
        {"q": f"Do you know {state.selected_domain} deployment?", "exp": f"Deployment involves making your {state.selected_domain} applications available to users in production environments."}
    ])
    
    current_question = questions[state.question_count]
    
    if is_yes:
        state.score += 1
        state.answers.append({"question": current_question["q"], "answer": "Yes", "explanation": None})
        state.question_count += 1
        
        if state.question_count >= 6:
            return _generate_detailed_results(state, questions)
        
        next_question = questions[state.question_count]
        return {
            "message": "Great!",
            "question": next_question["q"],
            "completed": False
        }
    
    elif is_no:
        state.answers.append({"question": current_question["q"], "answer": "No", "explanation": current_question["exp"]})
        state.question_count += 1
        
        if state.question_count >= 6:
            return _generate_detailed_results(state, questions)
        
        next_question = questions[state.question_count]
        return {
            "message": f"No worries! {current_question['exp']}",
            "question": next_question["q"],
            "completed": False
        }
    
    else:
        return {
            "message": "Please answer with 'yes' or 'no'.",
            "question": current_question["q"],
            "completed": False
        }

def _generate_detailed_results(state, questions):
    # Calculate level
    percentage = (state.score / 6) * 100
    if percentage >= 80:
        level = "Advanced"
        level_desc = "You have strong expertise in this domain with comprehensive knowledge across multiple areas."
    elif percentage >= 50:
        level = "Intermediate"
        level_desc = "You have solid foundational knowledge with room to grow in some areas."
    else:
        level = "Beginner"
        level_desc = "You're starting your journey in this domain. Focus on building fundamental skills."
    
    # Areas to improve (questions answered 'No')
    areas_to_improve = [ans for ans in state.answers if ans["answer"] == "No"]
    
    # Domain-specific recommendations
    domain_recommendations = {
        'frontend': {
            'topics': ['HTML5 & CSS3', 'JavaScript ES6+', 'React/Vue/Angular', 'Responsive Design', 'Web Performance', 'Browser DevTools'],
            'projects': ['Personal Portfolio Website', 'Todo App with Framework', 'E-commerce Product Page', 'Weather Dashboard', 'Interactive Game']
        },
        'backend': {
            'topics': ['RESTful APIs', 'Database Design', 'Authentication Systems', 'Cloud Deployment', 'Testing Strategies', 'Security Best Practices'],
            'projects': ['REST API with Database', 'User Authentication System', 'File Upload Service', 'Real-time Chat App', 'Microservice Architecture']
        }
    }
    
    recommendations = domain_recommendations.get(state.selected_domain, {
        'topics': [f'{state.selected_domain} Fundamentals', 'Best Practices', 'Project Development', 'Testing', 'Deployment'],
        'projects': [f'Basic {state.selected_domain} Project', f'Intermediate {state.selected_domain} App', f'Advanced {state.selected_domain} System']
    })
    
    return {
        "message": "Assessment completed!",
        "question": None,
        "completed": True,
        "recommendations": {
            "level": level,
            "domain": state.selected_domain.title(),
            "score": f"{state.score}/6",
            "percentage": f"{percentage:.0f}%",
            "level_description": level_desc,
            "areas_to_improve": areas_to_improve,
            "topics": recommendations['topics'],
            "projects": recommendations['projects'],
            "explanation": f"Based on your {state.selected_domain} assessment, you scored {state.score} out of 6 questions correctly ({percentage:.0f}%). {level_desc} Focus on the recommended topics and try building the suggested projects to enhance your skills."
        }
    }

@app.post("/chat")
def chat(request: AnswerRequest):
    if request.session_id not in sessions:
        return {"message": "Session not found"}
    
    state = sessions[request.session_id]
    user_message = request.answer.lower().strip()
    
    # Handle improvement questions
    if any(word in user_message for word in ['improve', 'better', 'learn', 'study', 'focus', 'next', 'recommend']):
        if hasattr(state, 'selected_domain') and state.selected_domain:
            domain_tips = {
                'frontend': {
                    'beginner': ['HTML5 semantic elements', 'CSS Flexbox and Grid', 'JavaScript ES6+ features', 'Responsive design principles'],
                    'intermediate': ['React or Vue.js', 'State management', 'Build tools (Webpack/Vite)', 'CSS preprocessors'],
                    'advanced': ['Performance optimization', 'Advanced React patterns', 'Testing frameworks', 'Progressive Web Apps']
                },
                'backend': {
                    'beginner': ['HTTP and REST principles', 'Database fundamentals', 'Basic authentication', 'API design'],
                    'intermediate': ['Advanced SQL queries', 'Caching strategies', 'Microservices basics', 'Cloud deployment'],
                    'advanced': ['System design', 'Load balancing', 'Database optimization', 'Security best practices']
                }
            }
            
            # Determine level based on score
            if hasattr(state, 'score'):
                percentage = (state.score / 6) * 100
                level = 'advanced' if percentage >= 80 else 'intermediate' if percentage >= 50 else 'beginner'
            else:
                level = 'beginner'
            
            tips = domain_tips.get(state.selected_domain, {}).get(level, [f'{state.selected_domain} fundamentals', 'Best practices', 'Hands-on projects'])
            
            return {
                "message": f"To improve your {state.selected_domain} skills, I recommend focusing on: {', '.join(tips)}. Start with hands-on projects and practice regularly!"
            }
    
    # Handle general questions
    if any(word in user_message for word in ['how', 'what', 'why', 'when', 'where']):
        return {
            "message": "That's a great question! For specific technical guidance, I recommend checking official documentation, online tutorials, or joining developer communities. Is there a particular area you'd like to focus on?"
        }
    
    # Default response
    return {
        "message": "Thanks for your question! I'm here to help with your learning journey. Feel free to ask about improving your skills, learning resources, or career advice."
    }
