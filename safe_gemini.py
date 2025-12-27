import os
import google.generativeai as genai
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class SafeGeminiWrapper:
    """
    Safe wrapper for Gemini API with strict prompt templates
    Prevents hallucination and flow deviation
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini API: {e}")
                self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return self.model is not None
    
    def rephrase_question(self, original_question: str, domain: str) -> str:
        """
        Safely rephrase assessment questions
        ONLY for making questions more conversational
        """
        if not self.is_available():
            return original_question
        
        try:
            prompt = f"""
            STRICT INSTRUCTIONS:
            - You are rephrasing a technical assessment question
            - Keep the EXACT same technical meaning
            - Make it more conversational but professional
            - Do NOT change the question type (yes/no remains yes/no)
            - Do NOT add new concepts or requirements
            - Do NOT use emojis
            - Return ONLY the rephrased question, nothing else
            
            Domain: {domain}
            Original question: {original_question}
            
            Rephrased question:
            """
            
            response = self.model.generate_content(prompt)
            rephrased = response.text.strip()
            
            # Safety check - if response is too different, use original
            if len(rephrased) > len(original_question) * 2:
                return original_question
            
            return rephrased
            
        except Exception as e:
            print(f"Warning: Question rephrasing failed: {e}")
            return original_question
    
    def generate_acknowledgment(self, user_answer: str, answer_type: str) -> str:
        """
        Generate brief acknowledgment for user answers
        ONLY for natural conversation flow
        """
        if not self.is_available():
            return self._get_fallback_acknowledgment(answer_type)
        
        try:
            prompt = f"""
            STRICT INSTRUCTIONS:
            - You are acknowledging a user's answer in a tech assessment
            - Provide a brief, encouraging acknowledgment (1 sentence max)
            - Do NOT ask new questions
            - Do NOT change the conversation flow
            - Do NOT provide technical explanations
            - Keep it professional and supportive
            - Do NOT use emojis
            
            User's answer: {user_answer}
            Answer type: {answer_type}
            
            Brief acknowledgment:
            """
            
            response = self.model.generate_content(prompt)
            acknowledgment = response.text.strip()
            
            # Safety check - ensure it's brief
            if len(acknowledgment) > 100:
                return self._get_fallback_acknowledgment(answer_type)
            
            return acknowledgment
            
        except Exception as e:
            print(f"Warning: Acknowledgment generation failed: {e}")
            return self._get_fallback_acknowledgment(answer_type)
    
    def answer_clarification_question(self, user_question: str, context: str) -> str:
        """
        Answer user's clarification questions about tech topics
        ONLY for brief explanations during assessment
        """
        if not self.is_available():
            return "That's a great question! Let me continue with the assessment and we can discuss this more at the end."
        
        try:
            prompt = f"""
            STRICT INSTRUCTIONS:
            - User asked a clarification question during tech assessment
            - Provide a brief, helpful answer (2-3 sentences max)
            - Stay focused on the technical topic
            - Do NOT ask new questions
            - Do NOT change the assessment flow
            - End with "Now, let's continue with the assessment question."
            - Do NOT use emojis
            
            Context: {context}
            User's question: {user_question}
            
            Brief answer:
            """
            
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            
            # Ensure it ends with continuation prompt
            if "continue with the assessment" not in answer.lower():
                answer += " Now, let's continue with the assessment question."
            
            return answer
            
        except Exception as e:
            print(f"Warning: Clarification answer failed: {e}")
            return "That's a great question! Let me continue with the assessment and we can discuss this more at the end."
    
    def generate_final_recommendation(self, user_name: str, domain: str, level: str, 
                                    topics: list, projects: list) -> str:
        """
        Generate final personalized recommendations
        ONLY used at the end of assessment
        """
        if not self.is_available():
            return self._get_fallback_recommendation(user_name, domain, level)
        
        try:
            prompt = f"""
            STRICT INSTRUCTIONS:
            - Generate personalized career recommendations for completed assessment
            - Be encouraging and professional
            - Focus on the provided topics and projects
            - Do NOT ask new questions
            - Do NOT restart any flow
            - Keep it motivational but realistic
            - 2-3 paragraphs maximum
            - Do NOT use emojis
            
            User: {user_name}
            Domain: {domain}
            Level: {level}
            Recommended topics: {', '.join(topics)}
            Recommended projects: {', '.join(projects)}
            
            Personalized recommendation:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Warning: Recommendation generation failed: {e}")
            return self._get_fallback_recommendation(user_name, domain, level)
    
    def _get_fallback_acknowledgment(self, answer_type: str) -> str:
        """Fallback acknowledgments when Gemini unavailable"""
        fallbacks = {
            "positive": "Great! That's excellent knowledge to have.",
            "negative": "No worries, everyone starts somewhere!",
            "partial": "That's a good start! Having some familiarity is valuable.",
            "unclear": "Thank you for your response."
        }
        return fallbacks.get(answer_type, "Got it, thanks for sharing!")
    
    def _get_fallback_recommendation(self, user_name: str, domain: str, level: str) -> str:
        """Fallback recommendation when Gemini unavailable"""
        return f"""
        Congratulations {user_name} on completing your {domain} assessment! 
        
        Based on your {level} level results, I've identified specific areas for your growth. 
        Focus on the recommended topics to strengthen your foundation, and use the suggested 
        projects to build practical experience.
        
        Remember, consistent practice and hands-on projects are key to advancing your skills. 
        Keep learning and building!
        """

# Global instance
safe_gemini = SafeGeminiWrapper()