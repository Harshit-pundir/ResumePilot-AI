# ==========================================================
# ATS RESUME SCORE CHECKER
# Part 1 - Project Setup & Resume Parser
# Author : Harshit Pundir
# ==========================================================

# -----------------------------
# Import Required Libraries
# -----------------------------

from flask import Flask, request, jsonify, render_template
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from supabase import create_client
import json
import logging
import os
import re
import spacy


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


# -----------------------------
# Load Environment Variables
# -----------------------------
# Reads variables from .env file

load_dotenv()


# -----------------------------
# Load spaCy NLP Model
# -----------------------------
# This model helps us remove stop words,
# convert words into their root form (lemma),
# and process text efficiently.

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' is not installed.")
    raise


# -----------------------------
# Flask App
# -----------------------------

app = Flask(__name__)

# Secret key is used for sessions and flash messages
app.secret_key = os.getenv("SECRET_KEY")


# -----------------------------
# Supabase Configuration
# -----------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================================
# CONSTANTS
# ==========================================================

PERCENT_MULTIPLIER = 100
ROUND_DECIMALS = 2

SKILL_WEIGHT = 60
SECTION_WEIGHT = 20
CONTACT_WEIGHT = 10
COMPLETENESS_WEIGHT = 10

RESUME_SECTION_WEIGHT = 50
RESUME_CONTACT_WEIGHT = 20
RESUME_COMPLETENESS_WEIGHT = 30

EXCELLENT_SCORE_THRESHOLD = 90
VERY_GOOD_SCORE_THRESHOLD = 75
GOOD_SCORE_THRESHOLD = 60
AVERAGE_SCORE_THRESHOLD = 40

SKILLS_FILE_NAME = "skills.json"

# ==========================================================
# PDF TEXT EXTRACTION
# ==========================================================

def extract_text_from_pdf(file) -> str:
    """
    Extract text from uploaded PDF.

    Parameters
    ----------
    file : Uploaded PDF

    Returns
    -------
    str
        Complete resume text
    """

    reader = PdfReader(file)

    complete_text = ""

    # Read every page

    for page in reader.pages:
        try:
            page_text = page.extract_text()
            # Some pages may return None
            if page_text:
                complete_text += page_text + " "
                
        except Exception:
            logger.exception("Error while extracting text from a PDF page.")
            continue

    return complete_text.lower()


# ==========================================================
# RESUME SECTION EXTRACTOR
# ==========================================================

def extract_section(text: str, headings: list[str]) -> str:
    """
    Extract a particular section
    like Skills, Projects, Education etc.
    """

    lines = text.splitlines()

    # All possible section headings
    all_headings = {
        "summary",
        "professional summary",
        "profile",
        "technical skills",
        "skills",
        "core skills",
        "professional skills",
        "projects",
        "project",
        "education",
        "academic",
        "qualification",
        "experience",
        "work experience",
        "professional experience",
        "leadership",
        "achievements",
        "certifications"
    }

    start = -1

    # Find requested heading
    for i, line in enumerate(lines):
        current = line.strip().lower()
        if current in headings:
            start = i + 1
            break

    if start == -1:
        return ""

    section = []

    # Read until next heading
    for i in range(start, len(lines)):
        current = lines[i].strip().lower()

        if current in all_headings:
            break

        section.append(lines[i])

    return "\n".join(section).strip()


# ==========================================================
# EXTRACT ALL SECTIONS
# ==========================================================

def extract_resume_sections(text: str) -> dict[str, str]:
    """
    Extract all important sections
    from the resume.
    """

    sections = {

        "skills": extract_section(
            text,
            [
                "technical skills",
                "skills",
                "core skills",
                "professional skills"
            ]
        ),

        "projects": extract_section(
            text,
            [
                "projects",
                "project"
            ]
        ),

        "education": extract_section(
            text,
            [
                "education",
                "academic",
                "qualification"
            ]
        ),

        "experience": extract_section(
            text,
            [
                "experience",
                "work experience",
                "professional experience"
            ]
        ),

        "summary": extract_section(
            text,
            [
                "summary",
                "professional summary",
                "profile"
            ]
        )
    }

    return sections

 
# ==========================================================
# LOAD PREDEFINED SKILLS
# ==========================================================


def load_skills() -> list[str]:
    """
    Load predefined skills from the local skills.json file.

    Returns
    -------
    list[str]
        Skill names loaded from skills.json. Returns an empty list if the
        file is missing or contains invalid JSON.
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    skills_file = os.path.join(base_dir, SKILLS_FILE_NAME)

    try:
        with open(skills_file, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        logger.exception("skills.json file not found.")
        return []

    except json.JSONDecodeError:
        logger.exception("Invalid JSON format.")
        return []


def extract_skills(text: str, known_skills: list[str]) -> set[str]:
    """
    Extract all predefined skills
    from given text.

    Parameters
    ----------
    text : Resume or JD text

    known_skills : list

    Returns
    -------
    set
    """

    text = text.lower()

    found_skills = set()

    for skill in known_skills:
        pattern = rf"\b{re.escape(skill.lower())}\b"
        if re.search(pattern, text):
            found_skills.add(skill)

    return found_skills


def match_skills(resume_skills: set[str],jd_skills: set[str]) -> tuple[set[str], set[str]]:
    """
    Compare resume skills with
    job description skills.

    Parameters
    ----------
    resume_skills : set

    jd_skills : set

    Returns
    -------
    matched_skills : set

    missing_skills : set
    """

    matched_skills = resume_skills & jd_skills
    missing_skills = jd_skills - resume_skills
    return matched_skills, missing_skills

# ==========================================================
# EXTRACT CONTACT DETAILS
# ==========================================================

def extract_contact_details(text: str) -> dict[str, str | None]:
    """
    Extract contact details from resume.

    Returns
    -------
    dict
        Email
        Phone
        LinkedIn
        GitHub
        Portfolio
    """

    contacts = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "portfolio": None
    }

    # -------------------------
    # Email
    # -------------------------

    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email:
        contacts["email"] = email.group()

    # -------------------------
    # Phone Number
    # -------------------------

    phone = re.search(r"(?:\+91[\-\s]?)?[6-9]\d{9}", text)

    if phone:
        contacts["phone"] = phone.group()

    # -------------------------
    # LinkedIn
    # -------------------------

    linkedin = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s]+",text)


    if linkedin:
        contacts["linkedin"] = linkedin.group()

    # -------------------------
    # GitHub
    # -------------------------

    github = re.search(r"(?:https?://)?(?:www\.)?github\.com/[^\s]+",text)

    if github:
        contacts["github"] = github.group()

    # -------------------------
    # Portfolio
    # -------------------------

    urls = re.findall(r"https?://[^\s]+", text)

    for url in urls:
        if ("linkedin.com" not in url and "github.com" not in url):
            contacts["portfolio"] = url
            break

    return contacts

# ==========================================================
# CALCULATE SKILL SCORE
# ==========================================================

def calculate_skill_score(matched_skills: set[str], jd_skills: set[str]) -> float:
    """
    Calculate how many required skills
    are present in the resume.

    Formula

        matched skills
    ---------------------- × 100
      total JD skills
    """

    # Prevent division by zero
    if not jd_skills:
        return 0
    
    score = (len(matched_skills) / len(jd_skills)) * PERCENT_MULTIPLIER
    return round(score, ROUND_DECIMALS)

# ==========================================================
# CALCULATE SECTION SCORE
# ==========================================================

def calculate_section_score(sections: dict[str, str]) -> float:
    """
    Calculate score based on
    available resume sections.

    Expected Sections
    -----------------
    - Summary
    - Skills
    - Projects
    - Education
    - Experience
    """

    total_sections = len(sections)
    available_sections = 0

    # Check every section
    for section in sections.values():
        if section.strip():
            available_sections += 1

    score = (available_sections / total_sections) * PERCENT_MULTIPLIER

    return round(score, ROUND_DECIMALS)


# ==========================================================
# CALCULATE CONTACT SCORE
# ==========================================================

def calculate_contact_score(contact_details: dict[str, str | None]) -> float:
    """
    Calculate score based on
    available contact information.
    """

    total_contact_details = len(contact_details)
    available_contact_details = 0

    for contact in contact_details.values():
        if contact:
            available_contact_details += 1

    score = (available_contact_details / total_contact_details) * PERCENT_MULTIPLIER
    return round(score, ROUND_DECIMALS)

# ==========================================================
# CALCULATE RESUME COMPLETENESS SCORE
# ==========================================================

def calculate_completeness_score(sections: dict[str, str],contact_details: dict[str, str | None]) -> float:
    """
    Calculate how complete
    the resume is.
    """

    total_items = len(sections) + len(contact_details)

    available_items = 0

    # Count available sections
    for section in sections.values():
        if section.strip():
            available_items += 1

    # Count available contacts
    for contact in contact_details.values():
        if contact:
            available_items += 1

    score = (available_items / total_items) * PERCENT_MULTIPLIER
    return round(score, ROUND_DECIMALS)

# ==========================================================
# CALCULATE RESUME SCORE (WITHOUT JOB DESCRIPTION)
# ==========================================================

def calculate_resume_score(section_score: float,contact_score: float,completeness_score: float) -> float:
    """
    Calculate resume score when
    no Job Description is provided.

    Weights
    -------
    Section Score       : 50%
    Contact Score       : 20%
    Completeness Score  : 30%
    """

    final_score = (
        section_score * RESUME_SECTION_WEIGHT
        + contact_score * RESUME_CONTACT_WEIGHT
        + completeness_score * RESUME_COMPLETENESS_WEIGHT
    ) / PERCENT_MULTIPLIER

    return round(final_score, ROUND_DECIMALS)

# ==========================================================
# CALCULATE FINAL ATS SCORE
# ==========================================================

def calculate_ats_score(skill_score: float,section_score: float, contact_score: float, completeness_score: float) -> float:
    """
    Calculate final ATS score
    using weighted scoring.
    """

    final_score = (
        skill_score * SKILL_WEIGHT
        + section_score * SECTION_WEIGHT
        + contact_score * CONTACT_WEIGHT
        + completeness_score * COMPLETENESS_WEIGHT
    ) / PERCENT_MULTIPLIER

    return round(final_score, ROUND_DECIMALS)

# ==========================================================
# GENERATE SCORE FEEDBACK
# ==========================================================

def generate_score_feedback(score: float, mode: str) -> list[str]:
    """
    Generate feedback based on
    the final score.

    Parameters
    ----------
    score : float
        Resume / ATS score

    mode : str
        "resume_analysis"
        or
        "job_match"
    """

    feedback = []

    # Different titles for different modes
    if mode == "resume_analysis":
        title = "Resume"
    else:
        title = "ATS"

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



# ==========================================================
# GENERATE SKILL FEEDBACK
# ==========================================================

def generate_skill_feedback(matched_skills: set[str],missing_skills: set[str]) -> list[str]:
    """
    Generate feedback based on
    matched and missing skills.
    """

    feedback = []

    # Tell user how many skills matched
    feedback.append(f"You matched {len(matched_skills)} required skill(s).")

    # If no skills are missing
    if not missing_skills:

        feedback.append("Excellent! You matched all the required technical skills.")
        return feedback

    # Suggestions for missing skills
    for skill in sorted(missing_skills):

        feedback.append(f"Consider adding '{skill}' if you have experience with it.")

    return feedback

# ==========================================================
# GENERATE RESUME FEEDBACK
# ==========================================================

def generate_resume_feedback(sections: dict[str, str],contact_details: dict[str, str | None]) -> list[str]:
    """
    Generate feedback based on
    resume structure and contact details.
    """

    feedback = []

    # -------------------------
    # Resume Sections
    # -------------------------
    

    if not sections["summary"].strip():
        feedback.append("Add a professional summary.")

    if not sections["skills"].strip():
        feedback.append("Add a Technical Skills section.")

    if not sections["projects"].strip():
        feedback.append("Include at least one technical project.")

    if not sections["education"].strip():
        feedback.append("Add your education details.")

    if not sections["experience"].strip():
        feedback.append("Include work experience or internships.")

    # -------------------------
    # Contact Details
    # -------------------------

    if not contact_details["email"]:
        feedback.append("Add your email address.")

    if not contact_details["phone"]:
        feedback.append("Add your phone number.")

    if not contact_details["linkedin"]:
        feedback.append("Include your LinkedIn profile.")

    if not contact_details["github"]:
        feedback.append("Add your GitHub profile.")

    if not contact_details["portfolio"]:
        feedback.append("Add your portfolio website.")

    # If everything is present
    if not feedback:
        feedback.append("Excellent! Your resume has all the important sections and contact details.")

    return feedback

# ==========================================================
# GENERATE FINAL FEEDBACK
# ==========================================================

def generate_feedback(score: float,matched_skills: set[str], missing_skills: set[str], sections: dict[str, str],
    contact_details: dict[str, str | None]) -> list[str]:
    """
    Generate complete ATS feedback.

    Combines:
    - Score feedback
    - Skill feedback
    - Resume feedback
    """

    feedback = []

    # Overall ATS Score Feedback
    feedback.extend(generate_score_feedback(score, "job_match"))

    # Skill Feedback
    feedback.extend(generate_skill_feedback(matched_skills, missing_skills))

    # Resume Feedback
    feedback.extend(generate_resume_feedback(sections, contact_details))

    if not feedback:
        feedback.append("Excellent! No improvements required.")

    return feedback

# ==========================================================
# HOME PAGE
# ==========================================================

@app.route("/")
def home() -> str:
    return render_template("index.html")

# ==========================================================
# UPLOAD RESUME
# ==========================================================

@app.route("/upload", methods=["POST"])
def upload_resume():

    # Resume PDF
    file = request.files.get("resume")

    # Job Description
    job_description = request.form.get("job_description", "").strip().lower()

    if not file:
        return jsonify({
            "error": "Please upload a resume."
        }), 400

    try:
        resume_text = extract_text_from_pdf(file)
    except Exception:
        logger.exception("Unable to read the uploaded PDF.")
        return jsonify({
            "error": "Unable to read the uploaded PDF."
        }), 400
    
    sections = extract_resume_sections(resume_text)
    known_skills = load_skills()

    if not known_skills:

        return jsonify({
            "error": "Skills database could not be loaded."
        }), 500
    
    resume_skills = extract_skills(resume_text, known_skills)
    contact_details = extract_contact_details(resume_text)
    section_score = calculate_section_score(sections)
    contact_score = calculate_contact_score(contact_details)
    completeness_score = calculate_completeness_score(sections, contact_details)


    # ======================================================
    # MODE 1 : Resume + Job Description
    # ======================================================

    if job_description:

        jd_skills = extract_skills(job_description, known_skills)

        if not jd_skills:
            return jsonify({
                "error": "No recognizable technical skills found in the job description."
            }), 400
        
        matched_skills, missing_skills = match_skills(resume_skills, jd_skills)
        skill_score = calculate_skill_score(matched_skills, jd_skills)
        ats_score = calculate_ats_score(
            skill_score,
            section_score,
            contact_score,
            completeness_score
        )
        feedback = generate_feedback(
            ats_score,
            matched_skills,
            missing_skills,
            sections,
            contact_details
        )
        try:
            supabase.table("resume_history").insert({
                "resume_name": file.filename,
                "mode": "job_match",
                "score": ats_score,
                "section_score": section_score,
                "contact_score": contact_score,
                "completeness_score": completeness_score
            }).execute()

        except Exception:
            logger.exception("Failed to save analysis to Supabase.")        

        return jsonify({
            "mode": "job_match",
            "score": ats_score,
            "skill_score": skill_score,
            "section_score": section_score,
            "contact_score": contact_score,
            "completeness_score": completeness_score,
            "matched_skills": sorted(matched_skills),
            "missing_skills": sorted(missing_skills),
            "contact_details": contact_details,
            "feedback": feedback
        })


    # ======================================================
    # MODE 2 : Resume Analysis Only
    # ======================================================

    resume_score = calculate_resume_score(
        section_score,
        contact_score,
        completeness_score
    )
    feedback = generate_score_feedback(resume_score, "resume_analysis")
    feedback.extend(generate_resume_feedback(sections, contact_details))
    feedback.insert(0, f"Resume Score: {resume_score}%")

    try:
        supabase.table("resume_history").insert({
            "resume_name": file.filename,
            "mode": "resume_analysis",
            "score": resume_score,
            "section_score": section_score,
            "contact_score": contact_score,
            "completeness_score": completeness_score
        }).execute()

    except Exception:
        logger.exception("Failed to save analysis to Supabase.")    

    return jsonify({
        "mode": "resume_analysis",
        "score": resume_score,
        "section_score": section_score,
        "contact_score": contact_score,
        "completeness_score": completeness_score,
        "resume_skills": sorted(resume_skills),
        "contact_details": contact_details,
        "feedback": feedback
    })

@app.route("/history")
def history():
    response = supabase.table("resume_history").select("*").order("created_at",desc=True).execute()
    return jsonify(response.data)

if __name__ == "__main__":
    app.run(debug=True)
