import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_ai_resume_feedback(resume_text):

    prompt = f"""
You are a precise ATS resume editor. Analyze only the resume supplied below.

Non-negotiable rules:
- Never hallucinate, infer, or invent experience, employers, responsibilities, metrics, skills, certifications, education, projects, or achievements.
- Do not add technologies, tools, project details, dates, titles, or results that are not explicitly present in the resume.
- Improve only the clarity, structure, grammar, action verbs, and ATS readability of existing content.
- If a section is absent or lacks usable content, say "Not present in the resume" rather than creating content for it.
- Keep facts, meaning, and scope faithful to the source resume.

Return clean Markdown only. Use exactly these level-two sections, in this order:
## Professional Summary
## Projects
## Skills
## Experience
## Achievements
## ATS Tips

For every section, use this exact structure:
### Current
[faithful concise extract or "Not present in the resume"]

↓

### Improved
[only an improved version of the existing content, or "No rewrite suggested because this content is not present."]

For ATS Tips, use Current to list only gaps visible in the resume, and Improved to list factual, actionable bullets. Do not claim that a missing item exists.

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
        timeout=45.0,
    )

    return response.choices[0].message.content
