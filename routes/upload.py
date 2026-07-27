from flask import Blueprint, current_app, jsonify, request

import extensions
from services.contact_service import extract_contact_details
from services.feedback_service import generate_feedback, generate_resume_feedback, generate_score_feedback
from services.pdf_parser import extract_text_from_pdf
from services.scoring_service import (
    calculate_ats_score, calculate_completeness_score, calculate_contact_score,
    calculate_resume_score, calculate_section_score, calculate_skill_score,
)
from services.section_extractor import extract_resume_sections
from services.skills_service import extract_skills, load_skills, match_skills
from utils.logger import get_logger

upload_bp = Blueprint("upload", __name__)
logger = get_logger(__name__)


@upload_bp.route("/upload", methods=["POST"])
def upload_resume():
    file = request.files.get("resume")
    job_description = request.form.get("job_description", "").strip().lower()
    if not file:
        return jsonify({"error": "Please upload a resume."}), 400
    try:
        resume_text = extract_text_from_pdf(file)
    except Exception:
        logger.exception("Unable to read the uploaded PDF.")
        return jsonify({"error": "Unable to read the uploaded PDF."}), 400
    sections = extract_resume_sections(resume_text)
    known_skills = load_skills()
    if not known_skills:
        return jsonify({"error": "Skills database could not be loaded."}), 500
    resume_skills = extract_skills(resume_text, known_skills)
    contact_details = extract_contact_details(resume_text)
    section_score = calculate_section_score(sections)
    contact_score = calculate_contact_score(contact_details)
    completeness_score = calculate_completeness_score(sections, contact_details)
    supabase = extensions.get_supabase(current_app)
    if job_description:
        jd_skills = extract_skills(job_description, known_skills)
        if not jd_skills:
            return jsonify({"error": "No recognizable technical skills found in the job description."}), 400
        matched_skills, missing_skills = match_skills(resume_skills, jd_skills)
        skill_score = calculate_skill_score(matched_skills, jd_skills)
        ats_score = calculate_ats_score(skill_score, section_score, contact_score, completeness_score)
        feedback = generate_feedback(ats_score, matched_skills, missing_skills, sections, contact_details)
        try:
            supabase.table("resume_history").insert({"resume_name": file.filename, "mode": "job_match", "score": ats_score, "section_score": section_score, "contact_score": contact_score, "completeness_score": completeness_score}).execute()
        except Exception:
            logger.exception("Failed to save analysis to Supabase.")
        extensions.latest_report.clear()
        extensions.latest_report.update({"mode": "job_match", "resume_name": file.filename, "score": ats_score, "matched_skills": sorted(matched_skills), "missing_skills": sorted(missing_skills), "section_score": section_score, "contact_score": contact_score, "completeness_score": completeness_score, "feedback": feedback})
        return jsonify({"mode": "job_match", "score": ats_score, "skill_score": skill_score, "section_score": section_score, "contact_score": contact_score, "completeness_score": completeness_score, "matched_skills": sorted(matched_skills), "missing_skills": sorted(missing_skills), "contact_details": contact_details, "feedback": feedback})
    resume_score = calculate_resume_score(section_score, contact_score, completeness_score)
    assessment = generate_score_feedback(resume_score, "resume_analysis")
    recommendations = generate_resume_feedback(sections, contact_details)
    section_status = {"Summary": bool(sections["summary"].strip()), "Skills": bool(sections["skills"].strip()), "Projects": bool(sections["projects"].strip()), "Education": bool(sections["education"].strip()), "Experience": bool(sections["experience"].strip())}
    try:
        supabase.table("resume_history").insert({"resume_name": file.filename, "mode": "resume_analysis", "score": resume_score, "section_score": section_score, "contact_score": contact_score, "completeness_score": completeness_score}).execute()
    except Exception:
        logger.exception("Failed to save analysis to Supabase.")
    extensions.latest_report.clear()
    extensions.latest_report.update({"resume_name": file.filename, "score": resume_score, "overall_assessment": {"title": assessment[0], "message": assessment[1]}, "section_score": section_score, "contact": {"Email": bool(contact_details["email"]), "Phone": bool(contact_details["phone"]), "LinkedIn": bool(contact_details["linkedin"]), "GitHub": bool(contact_details["github"]), "Portfolio": bool(contact_details["portfolio"])}, "contact_score": contact_score, "completeness_score": completeness_score, "sections": section_status, "resume_skills": sorted(resume_skills), "missing_skills": [], "recommendations": recommendations})
    return jsonify({"mode": "resume_analysis", "score": resume_score, "overall_assessment": {"title": assessment[0], "message": assessment[1]}, "recommendations": recommendations, "sections": section_status, "section_score": section_score, "contact_score": contact_score, "completeness_score": completeness_score, "resume_skills": sorted(resume_skills), "contact_details": contact_details})
