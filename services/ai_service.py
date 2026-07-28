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

For a source section that is missing or has no usable content, write only this directly below its heading:
> Section not found in the uploaded resume.

For a source section that is present but needs no meaningful rewrite, present its faithful content directly below the heading. Do not use "Current" or "Improved" labels.

Only when a meaningful wording or structure improvement is possible, use this exact comparison structure:
### Current
[faithful extract that preserves headings, project names, bullet points, ordering, and all stated facts]

↓

### Improved
[only a clearer version of the same content]

Projects are especially important: preserve each project separately and retain its bullet-list structure in both Current and Improved. Do not merge projects into a paragraph, omit bullets, invent project details, or change the number of projects.

For ATS Tips, do not use Current/Improved. Provide 3-5 personalized, actionable bullets based only on specific strengths, wording, sections, or gaps visibly present in this resume. Point to the observed content or missing section that motivates each tip; never give generic advice and never claim an unlisted fact exists.

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
