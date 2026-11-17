from utils.constants import (
    AVERAGE_SCORE_THRESHOLD, EXCELLENT_SCORE_THRESHOLD, GOOD_SCORE_THRESHOLD,
    VERY_GOOD_SCORE_THRESHOLD,
)

SECTION_RECOMMENDATIONS = (
    ("summary", "Add a professional summary."),
    ("skills", "Add a Technical Skills section."),
    ("projects", "Include at least one technical project."),
    ("education", "Add your education details."),
    ("experience", "Include work experience or internships."),
)
CONTACT_RECOMMENDATIONS = (
    ("email", "Add your email address."),
    ("phone", "Add your phone number."),
    ("linkedin", "Include your LinkedIn profile."),
    ("github", "Add your GitHub profile."),
    ("portfolio", "Add your portfolio website."),
)


def generate_score_feedback(score: float, mode: str) -> list[str]:
    """Return score-level feedback for resume or job-match mode."""
    feedback = []
    title = "Resume" if mode == "resume_analysis" else "ATS"
    if score >= EXCELLENT_SCORE_THRESHOLD:
        feedback.append(f"Excellent {title} score!")
        if mode == "job_match":
            feedback.append("Your resume is highly optimized for this job description.")
        else:
            feedback.append("Your resume follows most ATS best practices.")
    elif score >= VERY_GOOD_SCORE_THRESHOLD:
        feedback.append(f"Very good {title} score.")
        if mode == "job_match":
            feedback.append("Your resume has a strong match with the job description.")
        else:
            feedback.append("Your resume is well structured and ATS-friendly.")
    elif score >= GOOD_SCORE_THRESHOLD:
        feedback.append(f"Good {title} score.")
        if mode == "job_match":
            feedback.append("Adding the missing skills can further improve your score.")
        else:
            feedback.append("Improving resume sections and contact details can increase your score.")
    elif score >= AVERAGE_SCORE_THRESHOLD:
        feedback.append(f"Average {title} score.")
        if mode == "job_match":
            feedback.append("Your resume needs better alignment with the job description.")
        else:
            feedback.append("Your resume needs improvements to become more ATS-friendly.")
    else:
        feedback.append(f"Low {title} score.")
        if mode == "job_match":
            feedback.append("Your resume does not match the job description well.")
        else:
            feedback.append("Your resume is missing several important ATS sections.")
        feedback.append("Consider adding more relevant skills, projects, and professional information.")
    return feedback


def generate_skill_feedback(matched_skills: set[str], missing_skills: set[str]) -> list[str]:
    """Return the match count and ordered suggestions for missing skills."""
    feedback = [f"You matched {len(matched_skills)} required skill(s)."]
    if not missing_skills:
        feedback.append("Excellent! You matched all the required technical skills.")
        return feedback
    for skill in sorted(missing_skills):
        feedback.append(f"Consider adding '{skill}' if you have experience with it.")
    return feedback


def generate_resume_feedback(sections: dict[str, str], contact_details: dict[str, str | None]) -> list[str]:
    """Return recommendations for absent resume sections and contact fields."""
    feedback = []
    for section_name, recommendation in SECTION_RECOMMENDATIONS:
        if not sections[section_name].strip():
            feedback.append(recommendation)
    for contact_name, recommendation in CONTACT_RECOMMENDATIONS:
        if not contact_details[contact_name]:
            feedback.append(recommendation)
    if not feedback:
        feedback.append("Excellent! Your resume has all the important sections and contact details.")
    return feedback


def generate_feedback(
    score: float,
    matched_skills: set[str],
    missing_skills: set[str],
    sections: dict[str, str],
    contact_details: dict[str, str | None],
) -> list[str]:
    """Combine score, skill, and resume completeness feedback in order."""
    feedback = generate_score_feedback(score, "job_match")
    feedback.extend(generate_skill_feedback(matched_skills, missing_skills))
    feedback.extend(generate_resume_feedback(sections, contact_details))
    if not feedback:
        feedback.append("Excellent! No improvements required.")
    return feedback
