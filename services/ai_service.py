import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_ai_resume_feedback(resume_text):

    prompt = f"""
You are an expert ATS Resume Writer.

Analyze this resume carefully.

Improve only:

1. Professional Summary
2. Technical Skills
3. Projects
4. Experience
5. ATS Tips

Rules:

- Never invent fake experience.
- Never add technologies not present.
- Improve wording only.
- Make it ATS friendly.
- Return clean Markdown.

Resume:

{resume_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=1500,
    )

    return response.choices[0].message.content