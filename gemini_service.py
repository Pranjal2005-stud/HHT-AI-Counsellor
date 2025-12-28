import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def rephrase(text: str) -> str:
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"""
You are a professional technical counsellor.
Do NOT ask new questions.
Do NOT infer facts.
Only rephrase clearly and politely:

{text}
"""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return text  # Fallback to original text if API fails

def generate_personalized_response(user_name: str, domain: str, context: str) -> str:
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"""
You are a professional technical counsellor helping {user_name} with {domain} skills.
Be encouraging, professional, and concise (2-3 sentences max).
Context: {context}

Generate a personalized, motivating response that:
- Uses the person's name naturally
- Is specific to {domain}
- Encourages continued learning
- Sounds conversational but professional
"""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"Great work, {user_name}! Keep building your {domain} skills with consistent practice."

def enhance_feedback_response(feedback: str, user_name: str) -> str:
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"""
You are a professional technical counsellor. {user_name} just provided this feedback: "{feedback}"

Generate a warm, appreciative response (1-2 sentences) that:
- Thanks them personally
- Shows you value their input
- Sounds genuine and professional
"""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"Thank you so much for your valuable feedback, {user_name}! It helps us improve our service."
