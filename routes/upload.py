from fastapi import APIRouter , File , UploadFile , Form, Request
from fastapi.responses import JSONResponse 
import extensions
from deps import get_current_user
from services.contact_service import extract_contact_details
from services.feedback_service import generate_feedback, generate_resume_feedback, generate_score_feedback
from services.pdf_parser import PDFTextExtractionError, extract_text_from_pdf
from services.scoring_service import build_score_breakdown, calculate_ats_score, calculate_completeness_score, calculate_contact_score
from services.scoring_service import calculate_resume_score, calculate_section_score, calculate_skill_score
from services.section_extractor import extract_resume_sections
from services.skills_service import classify_skills, extract_jd_requirements, extract_skills, load_skills
from utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter()

def save_resume_history(supabase, file, mode, score, section_score, contact_score, completeness_score, user_id):
    history_record = {
        "user_id": user_id,
        "resume_name": file.filename,
        "mode": mode,
        "score": score,
        "section_score": section_score,
        "contact_score": contact_score,
        "completeness_score": completeness_score,
    }

    try:
        supabase.table("resume_history").insert(history_record).execute()
    except Exception:
        logger.exception("Failed to save analysis to Supabase.")


def build_latest_report(user_id, report_data):
    extensions.latest_reports[user_id] = report_data


def process_job_match(job_description, skill_aliases, resume_skills, resume_text, sections, contact_details, file, section_score, contact_score, completeness_score, supabase, user_id):
    jd_extraction = extract_jd_requirements(job_description, skill_aliases)
    jd_skills = jd_extraction.normalized_skills
    if not jd_skills:
        error_response = {
            "error": "No recognizable technical skills found in the job description."
        }
        return JSONResponse(error_response, 400)

    classification = classify_skills(resume_text, jd_skills, skill_aliases)
    matched_skills = classification.exact | set(classification.evidence_based)
    related_skills = classification.related
    missing_skills = classification.missing
    semantic_skills = classification.semantic
    skill_score = calculate_skill_score(
        classification.exact,
        jd_skills,
        semantic_skills,
        unresolved_requirements=len(jd_extraction.unresolved_requirements),
        evidence_matches=classification.evidence_based,
    )
    ats_score = calculate_ats_score(skill_score, section_score, contact_score, completeness_score)
    score_breakdown = build_score_breakdown("job_match", sections, contact_details, skill_score)
    feedback = generate_feedback(ats_score, matched_skills, missing_skills, sections, contact_details)
    sorted_matched_skills = sorted(matched_skills)
    sorted_missing_skills = sorted(missing_skills)
    sorted_related_skills = sorted(related_skills)
    sorted_match_details = sorted(classification.match_details.values(), key=lambda item: item["canonical_skill"])

    save_resume_history(supabase, file, "job_match", ats_score, section_score, contact_score, completeness_score, user_id)


    latest_report = {
        "user_id": user_id,
        "mode": "job_match",
        "resume_name": file.filename,
        "score": ats_score,
        "matched_skills": sorted_matched_skills,
        "missing_skills": sorted_missing_skills,
        "related_skills": sorted_related_skills,
        "semantic_skills": dict(sorted(semantic_skills.items())),
        "evidence_skills": dict(sorted(classification.evidence_based.items())),
        "skill_evidence": classification.evidence,
        "skill_matches": sorted_match_details,
        "section_score": section_score,
        "contact_score": contact_score,
        "completeness_score": completeness_score,
        "score_breakdown": score_breakdown,
        "feedback": feedback,
    }
    build_latest_report(user_id, latest_report)

    response_payload = {
        "mode": "job_match",
        "score": ats_score,
        "skill_score": skill_score,
        "section_score": section_score,
        "contact_score": contact_score,
        "completeness_score": completeness_score,
        "score_breakdown": score_breakdown,
        "matched_skills": sorted_matched_skills,
        "missing_skills": sorted_missing_skills,
        "related_skills": sorted_related_skills,
        "semantic_skills": dict(sorted(semantic_skills.items())),
        "evidence_skills": dict(sorted(classification.evidence_based.items())),
        "skill_evidence": classification.evidence,
        "skill_matches": sorted_match_details,
        "debug": {
            "original_jd": job_description,
            "original_jd_requirements": [group.original_text for group in jd_extraction.groups],
            "requirement_groups": [
                {
                    "original_text": group.original_text,
                    "raw_skills": group.raw_skills,
                    "normalized_skills": group.normalized_skills,
                }
                for group in jd_extraction.groups
            ],
            "raw_extracted_jd_skills": jd_extraction.raw_skills,
            "normalized_jd_skills": sorted(jd_skills),
            "unparsed_requirements": jd_extraction.unresolved_requirements,
            "raw_extracted_resume_text": resume_text,
            "normalized_resume_skills": sorted(resume_skills),
            "exact_matches": [detail for detail in sorted_match_details if detail["category"] == "exact"],
            "semantic_matches": [detail for detail in sorted_match_details if detail["category"] == "semantic"],
            "evidence_matches": [detail for detail in sorted_match_details if detail["category"] == "evidence"],
            "related_skills": [detail for detail in sorted_match_details if detail["category"] == "related"],
            "missing_skills": sorted(missing_skills),
            "extraction_coverage_percent": jd_extraction.extraction_coverage,
        },
        "contact_details": contact_details,
        "feedback": feedback,
    }
    return JSONResponse(response_payload, 200)


def process_resume_analysis(resume_skills, sections, contact_details, file, section_score, contact_score, completeness_score, supabase, user_id):
    resume_score = calculate_resume_score(section_score, contact_score, completeness_score)
    score_breakdown = build_score_breakdown("resume_analysis", sections, contact_details)
    assessment = generate_score_feedback(resume_score, "resume_analysis")
    recommendations = generate_resume_feedback(sections, contact_details)
    section_status = {
        "Summary": bool(sections["summary"].strip()),
        "Skills": bool(sections["skills"].strip()),
        "Projects": bool(sections["projects"].strip()),
        "Education": bool(sections["education"].strip()),
        "Experience / Leadership (optional)": bool(sections["experience"].strip()),
        "Achievements (optional)": bool(sections["achievements"].strip()),
        "Certifications (optional)": bool(sections["certifications"].strip()),
    }
    contact_status = {
        "Email": bool(contact_details["email"]),
        "Phone": bool(contact_details["phone"]),
        "LinkedIn": bool(contact_details["linkedin"]),
        "GitHub": bool(contact_details["github"]),
        "Portfolio (optional)": bool(contact_details["portfolio"]),
    }
    overall_assessment = {
        "title": assessment[0],
        "message": assessment[1],
    }
    sorted_resume_skills = sorted(resume_skills)

    save_resume_history(supabase, file, "resume_analysis", resume_score, section_score, contact_score, completeness_score, user_id)

    latest_report = {
        "resume_name": file.filename,
        "score": resume_score,
        "overall_assessment": overall_assessment,
        "section_score": section_score,
        "contact": contact_status,
        "contact_score": contact_score,
        "completeness_score": completeness_score,
        "score_breakdown": score_breakdown,
        "sections": section_status,
        "resume_skills": sorted_resume_skills,
        "missing_skills": [],
        "recommendations": recommendations,
    }
    build_latest_report(user_id, latest_report)

    response_payload = {
        "mode": "resume_analysis",
        "score": resume_score,
        "overall_assessment": overall_assessment,
        "recommendations": recommendations,
        "sections": section_status,
        "section_score": section_score,
        "contact_score": contact_score,
        "completeness_score": completeness_score,
        "score_breakdown": score_breakdown,
        "resume_skills": sorted_resume_skills,
        "contact_details": contact_details,
    }
    return JSONResponse(response_payload)


@router.post("/upload")
def upload_resume(request: Request, resume : UploadFile = File(None) , job_description: str = Form("")):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Please log in."}, status_code=401)
    if not resume:
        error_response = {"error": "Please upload a resume."}
        return JSONResponse(error_response, 400)
    if not (resume.filename or "").lower().endswith(".pdf"):
        return JSONResponse({"error": "Unsupported file type. Please upload a PDF resume."}, 415)
    job_description = job_description.strip() if isinstance(job_description, str) else ""

    try:
        resume_text = extract_text_from_pdf(resume.file)
    except PDFTextExtractionError as exc:
        logger.warning("Resume text extraction failed: %s", exc)
        return JSONResponse({"error": str(exc)}, 422)
    except Exception:
        logger.exception("Unable to read the uploaded PDF.")
        error_response = {"error": "Unable to read the uploaded PDF."}
        return JSONResponse(error_response, 400)

    sections = extract_resume_sections(resume_text)
    skill_aliases = load_skills()
    if not skill_aliases:
        error_response = {"error": "Skills database could not be loaded."}
        return JSONResponse(error_response, 500)

    resume_skills = extract_skills(resume_text, skill_aliases)
    contact_details = extract_contact_details(resume_text)
    section_score = calculate_section_score(sections)
    contact_score = calculate_contact_score(contact_details)
    completeness_score = calculate_completeness_score(sections, contact_details)
    supabase = extensions.supabase

    if job_description:
        return process_job_match(job_description, skill_aliases, resume_skills, resume_text, sections, contact_details, resume, section_score, contact_score, completeness_score, supabase, user["id"])


    return process_resume_analysis(resume_skills, sections, contact_details, resume, section_score, contact_score, completeness_score, supabase, user["id"])
