from enum import Enum
from typing import List, Dict
import re

class UserIntent(str, Enum):
    ANSWER = "answer"
    CLARIFICATION_QUESTION = "clarification_question"
    OFF_TOPIC = "off_topic"
    CONFUSED = "confused"
    GREETING = "greeting"

class IntentDetector:
    """
    Rule-based intent detection system
    No LLM dependency - uses patterns and keywords
    """
    
    def __init__(self):
        self.question_patterns = [
            r'\?',
            r'^(what|how|why|when|where|who)',
            r'(tell me|explain|can you|could you|would you)',
            r'(what does|what is|how does|how do)',
        ]
        
        self.confusion_patterns = [
            r'(i don\'t understand|confused|unclear|not sure what)',
            r'(what do you mean|i\'m lost|huh|what)',
            r'^(huh|what|eh)[\?\.]?$',
        ]
        
        self.greeting_patterns = [
            r'^(hi|hello|hey|good morning|good afternoon|good evening)',
            r'(how are you|nice to meet you)',
        ]
        
        self.positive_answers = [
            'yes', 'yeah', 'yep', 'sure', 'definitely', 'absolutely',
            'of course', 'correct', 'right', 'true', 'indeed'
        ]
        
        self.negative_answers = [
            'no', 'nope', 'nah', 'not really', 'never', 'false',
            'incorrect', 'wrong', 'not at all'
        ]
        
        self.partial_answers = [
            'somewhat', 'kind of', 'sort of', 'a little', 'a bit',
            'partially', 'maybe', 'sometimes', 'occasionally'
        ]
        
        self.tech_domains = [
            'backend', 'frontend', 'data analytics', 'machine learning',
            'devops', 'cybersecurity', 'data engineering', 'algorithms',
            'dsa', 'web development', 'mobile', 'ai', 'ml'
        ]
    
    def detect_intent(self, user_input: str, context: str = "") -> UserIntent:
        """
        Detect user intent based on input and context
        """
        user_input_lower = user_input.lower().strip()
        
        # Check for greetings
        if self._matches_patterns(user_input_lower, self.greeting_patterns):
            return UserIntent.GREETING
        
        # Check for confusion
        if self._matches_patterns(user_input_lower, self.confusion_patterns):
            return UserIntent.CONFUSED
        
        # Check for questions
        if self._matches_patterns(user_input_lower, self.question_patterns):
            # Determine if it's clarification or off-topic
            if self._is_tech_related(user_input_lower) or 'assessment' in context.lower():
                return UserIntent.CLARIFICATION_QUESTION
            else:
                return UserIntent.OFF_TOPIC
        
        # Default to answer
        return UserIntent.ANSWER
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given patterns"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _is_tech_related(self, text: str) -> bool:
        """Check if text contains tech-related keywords"""
        tech_keywords = [
            'api', 'database', 'server', 'code', 'programming', 'software',
            'development', 'framework', 'library', 'algorithm', 'data',
            'security', 'network', 'cloud', 'deployment', 'testing'
        ]
        
        # Check for tech domains
        for domain in self.tech_domains:
            if domain in text:
                return True
        
        # Check for tech keywords
        for keyword in tech_keywords:
            if keyword in text:
                return True
        
        return False
    
    def classify_answer_type(self, user_input: str) -> str:
        """
        Classify the type of answer for assessment questions
        """
        user_input_lower = user_input.lower().strip()
        
        # Check for clear positive answers
        if any(pos in user_input_lower for pos in self.positive_answers):
            return "positive"
        
        # Check for clear negative answers
        if any(neg in user_input_lower for neg in self.negative_answers):
            return "negative"
        
        # Check for partial/uncertain answers
        if any(partial in user_input_lower for partial in self.partial_answers):
            return "partial"
        
        # Check for numeric responses
        if re.search(r'\d+', user_input):
            return "numeric"
        
        return "unclear"
    
    def is_valid_domain_selection(self, user_input: str) -> bool:
        """Check if input contains a valid domain selection"""
        user_input_lower = user_input.lower()
        return any(domain in user_input_lower for domain in self.tech_domains)