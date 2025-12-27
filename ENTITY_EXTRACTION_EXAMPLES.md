# Entity Extraction and Persistence - Examples

## Problem Fixed
**Before:** System repeatedly asked for name because it didn't extract or persist personal details
**After:** System extracts entities immediately and never asks for the same information twice

## Entity Extraction Examples

### Name Extraction
```
Input: "My name is John Smith"
Extracted: "John Smith"
Stored: state.user_name = "John Smith"
Response: "Nice to meet you, John Smith!"
```

```
Input: "I'm Sarah"
Extracted: "Sarah" 
Stored: state.user_name = "Sarah"
Response: "Nice to meet you, Sarah!"
```

```
Input: "Call me Bob Johnson"
Extracted: "Bob Johnson"
Stored: state.user_name = "Bob Johnson"
Response: "Nice to meet you, Bob Johnson!"
```

### Location Extraction
```
Input: "I'm from New York"
Extracted: "New York"
Stored: state.user_location = "New York"
Response: "Great! New York sounds like a nice place."
```

```
Input: "Live in London, UK"
Extracted: "London, Uk"
Stored: state.user_location = "London, Uk"
Response: "Great! London, Uk sounds like a nice place."
```

### Education Extraction
```
Input: "I studied Computer Science"
Extracted: "Computer Science"
Stored: state.user_education = "Computer Science"
Response: "Excellent! Computer Science is a great background."
```

```
Input: "My degree is in Engineering"
Extracted: "Engineering"
Stored: state.user_education = "Engineering"
Response: "Excellent! Engineering is a great background."
```

## Conversation Flow with Guardrails

### Normal Flow:
```
Stage: GREETING
System: "Hello! I'm your AI Tech Counsellor..."
→ Advances to ASK_NAME

Stage: ASK_NAME (user_name = None)
System: "What's your name?"
User: "I'm Alice"
→ Extracts "Alice", stores in state.user_name
→ Advances to ASK_LOCATION

Stage: ASK_LOCATION (user_location = None)
System: "Where are you located or from?"
User: "From Boston"
→ Extracts "Boston", stores in state.user_location
→ Advances to ASK_EDUCATION

Stage: ASK_EDUCATION (user_education = None)
System: "What's your educational background?"
User: "Computer Science degree"
→ Extracts "Computer Science Degree", stores in state.user_education
→ Advances to DOMAIN_SELECTION
```

### Guardrails in Action:
```
Stage: ASK_NAME (user_name = "Alice" - ALREADY EXISTS)
System: Detects name exists, automatically advances to ASK_LOCATION
→ NEVER asks for name again

Stage: ASK_LOCATION (user_location = "Boston" - ALREADY EXISTS)  
System: Detects location exists, automatically advances to ASK_EDUCATION
→ NEVER asks for location again

Stage: ASK_EDUCATION (user_education = "CS" - ALREADY EXISTS)
System: Detects education exists, automatically advances to DOMAIN_SELECTION
→ NEVER asks for education again
```

## Entity Extraction Patterns

### Name Patterns:
- "My name is [NAME]"
- "I'm [NAME]"
- "Call me [NAME]"
- "It's [NAME]"
- Just "[NAME]" (direct input)

### Location Patterns:
- "I'm from [LOCATION]"
- "I live in [LOCATION]"
- "From [LOCATION]"
- "In [LOCATION]"
- Just "[LOCATION]" (direct input)

### Education Patterns:
- "I studied [EDUCATION]"
- "My degree is [EDUCATION]"
- "I have a [EDUCATION]"
- "Degree in [EDUCATION]"
- Just "[EDUCATION]" (direct input)

## Validation Rules

### Name Validation:
- 2-50 characters
- Letters and spaces only
- Maximum 3 words
- Automatically title-cased

### Location Validation:
- 2-100 characters
- Letters, spaces, commas, periods, hyphens
- Maximum 5 words
- Automatically title-cased

### Education Validation:
- 2-100 characters
- Letters, spaces, commas, periods, hyphens
- Maximum 8 words
- Automatically title-cased

## Stage Advancement Logic

```python
def advance_to_next_stage(self) -> bool:
    if self.stage == ConversationStage.GREETING:
        self.stage = ConversationStage.ASK_NAME
        return True
    elif self.stage == ConversationStage.ASK_NAME and self.user_name:
        self.stage = ConversationStage.ASK_LOCATION
        return True
    elif self.stage == ConversationStage.ASK_LOCATION and self.user_location:
        self.stage = ConversationStage.ASK_EDUCATION
        return True
    elif self.stage == ConversationStage.ASK_EDUCATION and self.user_education:
        self.stage = ConversationStage.DOMAIN_SELECTION
        return True
    return False
```

## Gemini Integration Restrictions

### Gemini CAN:
- Rephrase questions: "What's your name?" → "Could you please tell me your name?"
- Generate confirmations: "Nice to meet you!" → "Pleasure to meet you!"

### Gemini CANNOT:
- Extract entities (done by regex patterns)
- Remember information (stored in ConversationState)
- Control conversation flow (handled by stage advancement)
- Decide when to advance stages (based on data presence)

## Error Handling

### Invalid Name Input:
```
Input: "123" or "A very long name that exceeds limits"
Result: extraction fails
Response: "I didn't catch your name clearly. Could you please tell me your name?"
Stage: Remains at ASK_NAME
```

### Invalid Location Input:
```
Input: "12345" or empty string
Result: extraction fails  
Response: "Could you please tell me where you're located or from?"
Stage: Remains at ASK_LOCATION
```

### Invalid Education Input:
```
Input: "!!!" or very long text
Result: extraction fails
Response: "Could you please tell me about your educational background?"
Stage: Remains at ASK_EDUCATION
```

## Benefits

1. **No Repeated Questions**: System never asks for information it already has
2. **Immediate Persistence**: Data stored as soon as extracted successfully
3. **Deterministic Flow**: Stage advancement only happens when data is confirmed
4. **Input Flexibility**: Handles various ways users provide information
5. **Validation**: Ensures extracted data meets quality standards
6. **Guardrails**: Prevents infinite loops and redundant questions