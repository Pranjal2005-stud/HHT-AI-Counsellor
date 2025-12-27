from typing import Tuple, Optional
from intent_detector import IntentDetector, UserIntent
from safe_gemini import safe_gemini
from state import ConversationState

class InterruptionHandler:
    """
    Handles interruptions during assessment flow
    Manages user questions while maintaining state
    """
    
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.fallback_responses = {
            UserIntent.OFF_TOPIC: "That's interesting! Let's focus on completing your assessment first, and we can chat more afterward.",
            UserIntent.CONFUSED: "I understand this might be confusing. Let me rephrase: ",
            UserIntent.GREETING: "Hello! Let's continue with your assessment.",
        }
    
    def handle_interruption(self, user_input: str, state: ConversationState, 
                          current_question: str) -> Tuple[str, bool]:
        """
        Handle user interruption during assessment
        Returns (response_message, should_advance_state)
        """
        intent = self.intent_detector.detect_intent(user_input, current_question)
        
        if intent == UserIntent.ANSWER:
            # Normal answer - let state machine handle it
            return "", True
        
        elif intent == UserIntent.CLARIFICATION_QUESTION:
            # Answer the question briefly, then continue
            context = f"Current assessment question: {current_question}. Domain: {state.selected_domain}"
            response = safe_gemini.answer_clarification_question(user_input, context)
            return response, False  # Don't advance state
        
        elif intent == UserIntent.CONFUSED:
            # Rephrase current question
            rephrased = safe_gemini.rephrase_question(current_question, state.selected_domain)
            response = f"Let me rephrase that: {rephrased}"
            return response, False  # Don't advance state
        
        elif intent == UserIntent.OFF_TOPIC:
            # Politely redirect
            response = self.fallback_responses[UserIntent.OFF_TOPIC]
            return response, False  # Don't advance state
        
        elif intent == UserIntent.GREETING:
            # Acknowledge and continue
            response = self.fallback_responses[UserIntent.GREETING]
            return response, False  # Don't advance state
        
        else:
            # Unknown intent - treat as unclear answer
            response = "I'm not sure I understand. Could you please answer the current question?"
            return response, False  # Don't advance state
    
    def is_valid_assessment_answer(self, user_input: str) -> bool:
        """
        Check if user input is a valid assessment answer
        """
        intent = self.intent_detector.detect_intent(user_input)
        return intent == UserIntent.ANSWER
    
    def get_answer_type(self, user_input: str) -> str:
        """
        Get the type of answer for acknowledgment generation
        """
        return self.intent_detector.classify_answer_type(user_input)
    
    def handle_domain_selection(self, user_input: str) -> Tuple[str, bool, Optional[str]]:
        """
        Handle domain selection with validation
        Returns (response_message, is_valid, suggested_domain)
        """
        intent = self.intent_detector.detect_intent(user_input)
        
        if intent == UserIntent.CONFUSED:
            response = "Let me help you choose! We have these domains: Backend (servers/APIs), Frontend (websites/apps), Data Analytics (analyzing data), Machine Learning (AI), DevOps (deployment), Cybersecurity (security), Data Engineering (data pipelines), and Algorithms (problem solving)."
            return response, False, None
        
        elif intent in [UserIntent.OFF_TOPIC, UserIntent.CLARIFICATION_QUESTION]:
            response = "Let's focus on selecting your tech domain first. Which area interests you most?"
            return response, False, None
        
        # Check if it's a valid domain selection
        if self.intent_detector.is_valid_domain_selection(user_input):
            return "Great choice! Let's begin your assessment.", True, user_input
        else:
            response = "I didn't recognize that domain. Please choose from: backend, frontend, data analytics, machine learning, devops, cybersecurity, data engineering, or algorithms."
            return response, False, None
    
    def handle_personal_info(self, user_input: str, info_type: str) -> Tuple[str, bool]:
        """
        Handle personal information collection
        Returns (response_message, is_valid)
        """
        intent = self.intent_detector.detect_intent(user_input)
        
        if intent == UserIntent.CONFUSED:
            prompts = {
                "name": "Just tell me what you'd like me to call you - your first name is fine!",
                "location": "Where are you based? City and country, or just country is fine.",
                "education": "What's your educational background? For example: Computer Science degree, self-taught, bootcamp, etc."
            }
            return prompts.get(info_type, "Please provide the requested information."), False
        
        elif intent in [UserIntent.OFF_TOPIC, UserIntent.CLARIFICATION_QUESTION]:
            return "Let's get your basic information first, then we can chat more!", False
        
        # Validate input is not empty and reasonable
        if len(user_input.strip()) < 1:
            return "Please provide a response.", False
        
        if len(user_input.strip()) > 100:
            return "That seems a bit long. Could you give me a shorter response?", False
        
        return "", True  # Valid input