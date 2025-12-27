from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from state import ConversationState, ConversationStage, UserLevel
from state_controller import StateController
from intent_detector import IntentDetector
from interruption_handler import InterruptionHandler
from safe_gemini import safe_gemini
from engine import TechCounsellorEngine

# Initialize FastAPI app
app = FastAPI(title="AI Tech Counsellor", version="2.0.0")

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
state_controller = StateController()
intent_detector = IntentDetector()
interruption_handler = InterruptionHandler()
engine = TechCounsellorEngine()

# In-memory session storage
sessions: Dict[str, ConversationState] = {}

# Request/Response models
class StartConversationResponse(BaseModel):
    session_id: str
    message: str
    question: str

class UserAnswerRequest(BaseModel):
    session_id: str
    answer: str

class ConversationResponse(BaseModel):
    message: str
    question: Optional[str] = None
    stage: str
    progress: Optional[float] = None
    recommendations: Optional[Dict[str, Any]] = None
    completed: bool = False

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Tech Counsellor API v2.0 is running"}

@app.post("/start", response_model=StartConversationResponse)
async def start_conversation():
    """Start a new conversation session"""
    session_id = str(uuid.uuid4())
    state = ConversationState()
    sessions[session_id] = state
    
    return StartConversationResponse(
        session_id=session_id,
        message="Hello! I'm your Tech Skills Counsellor. I'll help you assess your technical abilities and provide personalized recommendations.",
        question=state_controller.get_current_question(state)
    )

@app.post("/answer", response_model=ConversationResponse)
async def submit_answer(request: UserAnswerRequest):
    """Submit user answer with state machine control"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[request.session_id]
    user_input = request.answer.strip()
    
    # Handle different stages with state machine
    if state.stage == ConversationStage.PERSONAL_INFO:
        return _handle_personal_info_stage(state, user_input)
    
    elif state.stage == ConversationStage.INTEREST_SELECTION:
        return _handle_domain_selection_stage(state, user_input)
    
    elif state.stage == ConversationStage.DOMAIN_EVALUATION:
        return _handle_assessment_stage(state, user_input)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid conversation stage")

def _handle_personal_info_stage(state: ConversationState, user_input: str) -> ConversationResponse:
    """Handle personal information collection stage"""
    
    # Determine which info we're collecting
    if not state.user_name:
        info_type = "name"
    elif not state.user_location:
        info_type = "location"
    else:
        info_type = "education"
    
    # Handle interruptions and validate input
    response_msg, is_valid = interruption_handler.handle_personal_info(user_input, info_type)
    
    if not is_valid:
        return ConversationResponse(
            message=response_msg,
            question=state_controller.get_current_question(state),
            stage=state.stage.value,
            completed=False
        )
    
    # Valid input - advance state
    success, next_question = state_controller.advance_state(state, user_input)
    
    if not success:
        return ConversationResponse(
            message="There was an error processing your information.",
            question=state_controller.get_current_question(state),
            stage=state.stage.value,
            completed=False
        )
    
    # Generate acknowledgment
    acknowledgment = safe_gemini.generate_acknowledgment(user_input, "positive")
    
    return ConversationResponse(
        message=acknowledgment,
        question=next_question,
        stage=state.stage.value,
        completed=False
    )

def _handle_domain_selection_stage(state: ConversationState, user_input: str) -> ConversationResponse:
    """Handle domain selection stage"""
    
    # Handle domain selection with validation
    response_msg, is_valid, suggested_domain = interruption_handler.handle_domain_selection(user_input)
    
    if not is_valid:
        return ConversationResponse(
            message=response_msg,
            question="Which tech domain would you like to be assessed in?",
            stage=state.stage.value,
            completed=False
        )
    
    # Valid domain - map and load questions
    selected_domain = engine.map_user_input_to_domain(user_input)
    
    if not selected_domain:
        return ConversationResponse(
            message="I couldn't identify that domain. Please choose from: backend, frontend, data analytics, machine learning, devops, cybersecurity, data engineering, or algorithms.",
            question="Which tech domain would you like to be assessed in?",
            stage=state.stage.value,
            completed=False
        )
    
    # Load domain questions and start assessment
    try:
        questions = engine.load_domain_questions(selected_domain)
        state.selected_domain = selected_domain
        state.stage = ConversationStage.DOMAIN_EVALUATION
        state.total_questions = len(questions)
        state.current_question_index = 0
        
        # Get first question (potentially rephrased)
        first_question = engine.get_next_question(state)
        rephrased_question = safe_gemini.rephrase_question(
            first_question["question"], selected_domain
        )
        
        return ConversationResponse(
            message=f"Perfect! Let's assess your {selected_domain.replace('_', ' ')} skills.",
            question=rephrased_question,
            stage=state.stage.value,
            progress=state.get_progress_percentage(),
            completed=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading questions: {str(e)}")

def _handle_assessment_stage(state: ConversationState, user_input: str) -> ConversationResponse:
    """Handle assessment questions stage"""
    
    current_question = engine.get_next_question(state)
    if not current_question:
        return _generate_final_results(state)
    
    # Handle interruptions (questions, confusion, off-topic)
    interruption_response, should_advance = interruption_handler.handle_interruption(
        user_input, state, current_question["question"]
    )
    
    if not should_advance:
        # User asked question or was confused - don't advance state
        return ConversationResponse(
            message=interruption_response,
            question=current_question["question"],
            stage=state.stage.value,
            progress=state.get_progress_percentage(),
            completed=False
        )
    
    # Valid answer - process and advance
    answer_type = interruption_handler.get_answer_type(user_input)
    
    # Update score
    engine.update_score(state, user_input, current_question["weight"])
    state.add_answer(current_question["id"], user_input)
    state.current_question_index += 1
    
    # Generate acknowledgment
    acknowledgment = safe_gemini.generate_acknowledgment(user_input, answer_type)
    
    # Check if more questions remain
    next_question = engine.get_next_question(state)
    
    if next_question:
        # Rephrase next question
        rephrased_question = safe_gemini.rephrase_question(
            next_question["question"], state.selected_domain
        )
        
        return ConversationResponse(
            message=acknowledgment,
            question=rephrased_question,
            stage=state.stage.value,
            progress=state.get_progress_percentage(),
            completed=False
        )
    else:
        # Assessment complete
        result = _generate_final_results(state)
        result.message = acknowledgment + " " + result.message
        return result

def _generate_final_results(state: ConversationState) -> ConversationResponse:
    """Generate final results and recommendations"""
    
    # Calculate user level
    state.user_level = engine.calculate_user_level(state)
    state.stage = ConversationStage.RESULT
    
    # Get recommendations
    recommendations = engine.get_recommendations(state.selected_domain, state.user_level)
    
    # Generate personalized explanation using Gemini
    personalized_explanation = safe_gemini.generate_final_recommendation(
        state.user_name or "there",
        state.selected_domain,
        state.user_level.value,
        recommendations["topics"],
        recommendations["projects"]
    )
    
    # Calculate score percentage
    score_percentage = (state.current_score / state.max_possible_score) * 100 if state.max_possible_score > 0 else 0
    
    return ConversationResponse(
        message=personalized_explanation,
        stage=state.stage.value,
        progress=100.0,
        recommendations={
            "level": state.user_level.value,
            "domain": state.selected_domain,
            "score": f"{state.current_score}/{state.max_possible_score}",
            "percentage": f"{score_percentage:.1f}%",
            "topics": recommendations["topics"],
            "projects": recommendations["projects"],
            "explanation": personalized_explanation
        },
        completed=True
    )

@app.get("/session/{session_id}")
async def get_session_status(session_id: str):
    """Get current session status"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[session_id]
    return {
        "session_id": session_id,
        "stage": state.stage.value,
        "stage_name": state_controller.get_stage_name(state),
        "progress": state.get_progress_percentage(),
        "completed": state_controller.is_complete(state),
        "selected_domain": state.selected_domain,
        "current_score": state.current_score,
        "max_score": state.max_possible_score
    }

@app.post("/chat")
async def post_assessment_chat(request: UserAnswerRequest):
    """Handle post-assessment chat"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[request.session_id]
    
    if state.stage != ConversationStage.RESULT:
        return ConversationResponse(
            message="Please complete the assessment first.",
            stage=state.stage.value,
            completed=False
        )
    
    # Use safe Gemini for post-assessment questions
    context = f"User completed {state.selected_domain} assessment with {state.user_level.value} level."
    response = safe_gemini.answer_clarification_question(request.answer, context)
    
    return ConversationResponse(
        message=response,
        stage=state.stage.value,
        completed=True
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)