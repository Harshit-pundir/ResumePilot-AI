import requests

from config import GEMINI_API_KEY


def generate_ai_resume_feedback(resume_text):
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY")
    url = "https://generativelanguage.googleapis.com/v1beta/" f"models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f'''\n    You are an expert ATS Resume Writer.\n\n    Analyze this resume.\n\n    Improve only:\n\n    1. Professional Summary\n    2. Technical Skills\n    3. Projects\n    4. Experience\n    5. ATS Tips\n\n    Rules:\n    - Never invent fake experience.\n    - Never add technologies not present.\n    - Keep everything truthful.\n    - Return clean Markdown.\n\n    Resume:\n\n    {resume_text}\n    '''
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=30)
    print("Status:", response.status_code)
    print("Response:", response.text)
    response.raise_for_status()
    data = response.json()
    if "candidates" not in data:
        raise ValueError(data)
    return data["candidates"][0]["content"]["parts"][0]["text"]
