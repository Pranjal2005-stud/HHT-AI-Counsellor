#State Controller.py
from typing import Tuple
from state import ConversationState, ConversationStage


class StateController:
    def get_current_question(self, state: ConversationState) -> str:
        if state.stage == ConversationStage.ASK_NAME:
            return "Let's start with some basic information. What's your name?"

        if state.stage == ConversationStage.ASK_LOCATION:
            return f"Nice to meet you, {state.user_name}! Where are you located?"

        if state.stage == ConversationStage.ASK_EDUCATION:
            return "What's your educational background or field of study?"

        if state.stage == ConversationStage.DOMAIN_SELECTION:
            return "Which tech domain are you interested in? (Frontend, Backend, DevOps, ML, etc.)"

        return "Let's continue with your assessment."

    def advance(self, state: ConversationState, user_input: str) -> Tuple[bool, str]:
        if state.stage == ConversationStage.ASK_NAME:
            if state.extract_name(user_input):
                state.stage = ConversationStage.ASK_LOCATION
                return True, self.get_current_question(state)
            return False, "Please tell me your name using letters only."

        if state.stage == ConversationStage.ASK_LOCATION:
            if state.extract_location(user_input):
                state.stage = ConversationStage.ASK_EDUCATION
                return True, self.get_current_question(state)
            return False, "Please tell me your city or country."

        if state.stage == ConversationStage.ASK_EDUCATION:
            if state.extract_education(user_input):
                state.stage = ConversationStage.DOMAIN_SELECTION
                return True, self.get_current_question(state)
            return False, "Please tell me your educational background."

        return False, "Invalid state."
