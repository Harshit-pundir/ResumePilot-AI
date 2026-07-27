import re


def extract_section(text: str, headings: list[str]) -> str:
    lines = text.splitlines()
    all_headings = {
        "summary", "professional summary", "profile", "technical skills", "skills",
        "core skills", "professional skills", "projects", "project", "education",
        "academic", "qualification", "experience", "work experience",
        "professional experience", "leadership", "achievements", "certifications",
    }
    normalized_headings = {re.sub(r"[^a-z]", "", h.lower()) for h in headings}
    normalized_all_headings = {re.sub(r"[^a-z]", "", h.lower()) for h in all_headings}
    start = -1
    for i, line in enumerate(lines):
        current = re.sub(r"[^a-z]", "", line.strip().lower())
        if current in normalized_headings:
            start = i + 1
            break
    if start == -1:
        return ""
    section = []
    for i in range(start, len(lines)):
        current = re.sub(r"[^a-z]", "", lines[i].strip().lower())
        if current in normalized_all_headings:
            break
        section.append(lines[i])
    return "\n".join(section).strip()


def extract_resume_sections(text: str) -> dict[str, str]:
    return {
        "skills": extract_section(text, ["technical skills", "skills", "core skills", "professional skills"]),
        "projects": extract_section(text, ["projects", "project"]),
        "education": extract_section(text, ["education", "academic", "qualification"]),
        "experience": extract_section(text, ["experience", "work experience", "professional experience"]),
        "summary": extract_section(text, ["summary", "professional summary", "profile"]),
    }
