#State.py
from enum import Enum
from typing import Dict, Optional


class ConversationStage(str, Enum):
    ASK_NAME = "ask_name"
    ASK_LOCATION = "ask_location"
    ASK_EDUCATION = "ask_education"
    DOMAIN_SELECTION = "domain_selection"
    DOMAIN_EVALUATION = "domain_evaluation"
    RESULT = "result"


class UserLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class ConversationState:
    def __init__(self):
        self.stage: ConversationStage = ConversationStage.ASK_NAME

        # Personal info slots
        self.user_name: Optional[str] = None
        self.user_location: Optional[str] = None
        self.user_education: Optional[str] = None

        # Domain info
        self.selected_domain: Optional[str] = None

        # Assessment tracking
        self.current_question_index: int = 0
        self.score: int = 0
        self.answers: Dict[str, str] = {}

    # ---------- ENTITY EXTRACTION (NO RAW STORAGE) ----------

    def extract_name(self, text: str) -> bool:
        cleaned = text.strip()
        if cleaned.isalpha() and 2 <= len(cleaned) <= 20:
            self.user_name = cleaned.title()
            return True
        return False

    def extract_location(self, text: str) -> bool:
        cleaned = text.strip()
        if cleaned.replace(" ", "").isalpha() and len(cleaned) >= 2:
            self.user_location = cleaned.title()
            return True
        return False

    def extract_education(self, text: str) -> bool:
        cleaned = text.strip()
        if len(cleaned) >= 3:
            self.user_education = cleaned.title()
            return True
        return False
