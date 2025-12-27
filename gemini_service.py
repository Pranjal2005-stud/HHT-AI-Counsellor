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
    return model.generate_content(prompt).text.strip()
