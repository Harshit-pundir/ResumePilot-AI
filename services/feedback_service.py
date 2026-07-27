from utils.constants import (
    AVERAGE_SCORE_THRESHOLD, EXCELLENT_SCORE_THRESHOLD, GOOD_SCORE_THRESHOLD,
    VERY_GOOD_SCORE_THRESHOLD,
)


def generate_score_feedback(score: float, mode: str) -> list[str]:
    feedback = []
    title = "Resume" if mode == "resume_analysis" else "ATS"
    if score >= EXCELLENT_SCORE_THRESHOLD:
        feedback.append(f"Excellent {title} score!")
        feedback.append("Your resume is highly optimized for this job description." if mode == "job_match" else "Your resume follows most ATS best practices.")
    elif score >= VERY_GOOD_SCORE_THRESHOLD:
        feedback.append(f"Very good {title} score.")
        feedback.append("Your resume has a strong match with the job description." if mode == "job_match" else "Your resume is well structured and ATS-friendly.")
    elif score >= GOOD_SCORE_THRESHOLD:
        feedback.append(f"Good {title} score.")
        feedback.append("Adding the missing skills can further improve your score." if mode == "job_match" else "Improving resume sections and contact details can increase your score.")
    elif score >= AVERAGE_SCORE_THRESHOLD:
        feedback.append(f"Average {title} score.")
        feedback.append("Your resume needs better alignment with the job description." if mode == "job_match" else "Your resume needs improvements to become more ATS-friendly.")
    else:
        feedback.append(f"Low {title} score.")
        feedback.append("Your resume does not match the job description well." if mode == "job_match" else "Your resume is missing several important ATS sections.")
        feedback.append("Consider adding more relevant skills, projects, and professional information.")
    return feedback


def generate_skill_feedback(matched_skills: set[str], missing_skills: set[str]) -> list[str]:
    feedback = [f"You matched {len(matched_skills)} required skill(s)."]
    if not missing_skills:
        feedback.append("Excellent! You matched all the required technical skills.")
        return feedback
    for skill in sorted(missing_skills):
        feedback.append(f"Consider adding '{skill}' if you have experience with it.")
    return feedback


def generate_resume_feedback(sections: dict[str, str], contact_details: dict[str, str | None]) -> list[str]:
    feedback = []
    if not sections["summary"].strip(): feedback.append("Add a professional summary.")
    if not sections["skills"].strip(): feedback.append("Add a Technical Skills section.")
    if not sections["projects"].strip(): feedback.append("Include at least one technical project.")
    if not sections["education"].strip(): feedback.append("Add your education details.")
    if not sections["experience"].strip(): feedback.append("Include work experience or internships.")
    if not contact_details["email"]: feedback.append("Add your email address.")
    if not contact_details["phone"]: feedback.append("Add your phone number.")
    if not contact_details["linkedin"]: feedback.append("Include your LinkedIn profile.")
    if not contact_details["github"]: feedback.append("Add your GitHub profile.")
    if not contact_details["portfolio"]: feedback.append("Add your portfolio website.")
    if not feedback:
        feedback.append("Excellent! Your resume has all the important sections and contact details.")
    return feedback


def generate_feedback(score: float, matched_skills: set[str], missing_skills: set[str], sections: dict[str, str], contact_details: dict[str, str | None]) -> list[str]:
    feedback = generate_score_feedback(score, "job_match")
    feedback.extend(generate_skill_feedback(matched_skills, missing_skills))
    feedback.extend(generate_resume_feedback(sections, contact_details))
    if not feedback:
        feedback.append("Excellent! No improvements required.")
    return feedback
