# ==========================================================
# ATS RESUME SCORE CHECKER
# Part 1 - Project Setup & Resume Parser
# Author : Harshit Pundir
# ==========================================================

# -----------------------------
# Import Required Libraries
# -----------------------------
   
from flask import Flask, request, jsonify, render_template
from reportlab.platypus import Table, TableStyle
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from supabase import create_client
from io import BytesIO
from reportlab.pdfgen import canvas
from flask import send_file
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Spacer)
from reportlab.lib.styles import getSampleStyleSheet 
from datetime import datetime
from reportlab.platypus import Paragraph, Spacer
import google.generativeai as genai
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

latest_report = {}
# -----------------------------
# Load Environment Variables
# -----------------------------
# Reads variables from .env file

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")



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

    lines = text.splitlines()

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

    normalized_headings = {
        re.sub(r"[^a-z]", "", h.lower())
        for h in headings
    }

    normalized_all_headings = {
        re.sub(r"[^a-z]", "", h.lower())
        for h in all_headings
    }

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
            feedback.append(
                "Your resume has a strong match with the job description."
            )
        else:
            feedback.append(
                "Your resume is well structured and ATS-friendly."
        )

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
    global latest_report

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
        ats_score = calculate_ats_score(skill_score, section_score, contact_score, completeness_score)
        feedback = generate_feedback( ats_score, matched_skills, missing_skills, sections, contact_details)
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

        latest_report = {
            "mode": "job_match",
            "resume_name": file.filename,
            "score": ats_score,
            "matched_skills": sorted(matched_skills),
            "missing_skills": sorted(missing_skills),
            "section_score": section_score,
            "contact_score": contact_score,
            "completeness_score": completeness_score,
            "feedback": feedback
        }    

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

    assessment = generate_score_feedback(resume_score, "resume_analysis")
    recommendations = generate_resume_feedback(sections,contact_details)

    section_status = {
        "Summary": bool(sections["summary"].strip()),
        "Skills": bool(sections["skills"].strip()),
        "Projects": bool(sections["projects"].strip()),
        "Education": bool(sections["education"].strip()),
        "Experience": bool(sections["experience"].strip())
    }

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

    latest_report = {
        "resume_name": file.filename,
        "score": resume_score,
        "overall_assessment": {
            "title": assessment[0],
            "message": assessment[1]
        },
        "section_score": section_score,
            "contact": {
            "Email": bool(contact_details["email"]),
            "Phone": bool(contact_details["phone"]),
            "LinkedIn": bool(contact_details["linkedin"]),
            "GitHub": bool(contact_details["github"]),
            "Portfolio": bool(contact_details["portfolio"])
        },
        "contact_score": contact_score,
        "completeness_score": completeness_score,
        "sections": section_status,
        "resume_skills": sorted(resume_skills),
        "missing_skills": [],
        "recommendations": recommendations
    }    

    return jsonify({
        "mode": "resume_analysis",
        "score": resume_score,
        "overall_assessment": {"title": assessment[0],"message": assessment[1]},
        "recommendations": recommendations,
        "sections": section_status,
        "section_score": section_score,
        "contact_score": contact_score,
        "completeness_score": completeness_score,
        "resume_skills": sorted(resume_skills),
        "contact_details": contact_details
    })

@app.route("/history")
def history():
    try:
        response = supabase.table("resume_history").select("*").order("created_at", desc=True).execute()
        history_items = response.data or []
    except Exception:
        logger.exception("Failed to fetch resume history from Supabase.")
        history_items = []

    return render_template("history.html", history=history_items)

def create_pdf_styles():
    styles = getSampleStyleSheet()

    styles.add( ParagraphStyle(name="MainTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=24,
            textColor=HexColor("#2563EB"),   # Blue
            spaceAfter=6
        )
    )

    styles.add(ParagraphStyle( name="SubTitle", parent=styles["Heading2"], alignment=TA_CENTER, fontSize=13,
            textColor=HexColor("#6B7280"),   # Gray
            spaceAfter=20
        )
    )

    styles.add( ParagraphStyle( name="SectionHeading", parent=styles["Heading2"], fontSize=15,textColor=HexColor("#1D4ED8"),
            spaceBefore=15,
            spaceAfter=10
        )
    )

    styles.add(ParagraphStyle( name="ScoreStyle", parent=styles["Title"], alignment=TA_CENTER, fontSize=34,
            textColor=HexColor("#059669"),   # Green
            spaceAfter=10
        )
    )

    return styles

def add_header(story, styles, report):
    # Main Title
    story.append(Paragraph("<b>ResumePilot AI</b>", styles["MainTitle"]))

    # Subtitle
    story.append(Paragraph("Professional ATS Analysis Report",styles["SubTitle"]))

    story.append(Spacer(1, 15))

    # Resume Name
    story.append(Paragraph(f"<b>Resume:</b> {report['resume_name']}",styles["BodyText"]))

    # Generated Date & Time
    generated_time = datetime.now().strftime("%d %B %Y | %I:%M %p")

    story.append(Paragraph(f"<b>Generated On:</b> {generated_time}", styles["BodyText"]))

    # Space before next section
    story.append(Spacer(1, 20))

def create_progress_bar(score, width=250, height=14):
    drawing = Drawing(width, height + 15)

    drawing.add(Rect(0,0,width,height,strokeColor=colors.grey , fillColor=colors.whitesmoke))

    if score >= 80:
        bar_color = colors.green
    elif score >= 60:
        bar_color = colors.orange
    else:
        bar_color = colors.red

    drawing.add(Rect(0,0, width * score / 100,height,fillColor=bar_color, strokeColor=bar_color))

    drawing.add(String(width + 10, 2, f"{score:.0f}%"))
    return drawing    

def add_score_card(story, styles, report):
    # Section Heading
    story.append(Paragraph("<b>ATS SCORE</b>", styles["SectionHeading"]))

    # Score
    story.append(Paragraph(f"<b>{report['score']}%</b>",styles["ScoreStyle"]))

    story.append(Spacer(1, 10))

    # Assessment Title
    story.append(Paragraph(report["overall_assessment"]["title"],styles["SectionHeading"]))

    story.append(create_progress_bar(report["score"]))
    story.append(Spacer(1,15))
    # Assessment Message
    story.append(Paragraph(report["overall_assessment"]["message"],styles["BodyText"]))

    story.append(Spacer(1, 20))

def add_score_table(story, styles, report):
    story.append(Paragraph("<b>Score Breakdown</b>", styles["SectionHeading"]))

    data = [
        ["Metric", "Score"],
        ["ATS Score", f"{report['score']}%"],
        ["Section Score", f"{report['section_score']}%"],
        ["Contact Score", f"{report['contact_score']}%"],
        ["Completeness Score", f"{report['completeness_score']}%"]
    ]

    table = Table(data,colWidths=[4*inch, 1.5*inch])

    table.setStyle(
        TableStyle([
            # Header
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 12),

            # Body
            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
            ("TEXTCOLOR", (0,1), (-1,-1), colors.black),
            ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,1), (-1,-1), 11),

            # Alignment
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

            # Grid
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

            # Padding
            ("BOTTOMPADDING", (0,0), (-1,0), 10),
            ("TOPPADDING", (0,1), (-1,-1), 8),
            ("BOTTOMPADDING", (0,1), (-1,-1), 8),
        ])
    )

    story.append(table)
    story.append(Spacer(1,20))


def add_resume_health(story, styles, report):
    # Heading
    story.append(Paragraph("<b>Resume Health</b>",styles["SectionHeading"]) )

    data = [["Section", "Status"]]

    for section, present in report["sections"].items():
        status = "✔ Present" if present else "✖ Missing"
        data.append([section, status])

    table = Table(data,colWidths=[4*inch, 2*inch])

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),

            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

            ("ALIGN", (0,0), (-1,-1), "CENTER"),

            ("BOTTOMPADDING", (0,0), (-1,0), 10),
            ("TOPPADDING", (0,1), (-1,-1), 8),
            ("BOTTOMPADDING", (0,1), (-1,-1), 8),
        ])
    )

    story.append(table)
    story.append(Spacer(1,20))


def add_contact_section(story, styles, report):
    story.append(Paragraph("<b>Contact Information</b>",styles["SectionHeading"]))

    data = [["Contact", "Status"]]

    for contact, present in report["contact"].items():
        status = "✔ Available" if present else "✖ Missing"
        data.append([contact, status])

    table = Table(
        data,
        colWidths=[4*inch, 2*inch]
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),

            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

            ("ALIGN", (0,0), (-1,-1), "CENTER"),

            ("BOTTOMPADDING", (0,0), (-1,0), 10),
            ("TOPPADDING", (0,1), (-1,-1), 8),
            ("BOTTOMPADDING", (0,1), (-1,-1), 8),
        ])
    )

    story.append(table)
    story.append(Spacer(1,20))


def add_skills_section(story, styles, report):
    story.append(
        Paragraph(
            "<b>Detected Skills</b>",
            styles["SectionHeading"]
        )
    )

    skills = report["resume_skills"]

    if not skills:
        story.append(Paragraph("No technical skills detected.",styles["BodyText"]))
        story.append(Spacer(1,20))
        return

    data = [["Skill", "Skill"]]

    for i in range(0, len(skills), 2):
        left = skills[i]

        if i + 1 < len(skills):
            right = skills[i + 1]
        else:
            right = ""

        data.append([left, right])

    table = Table( data, colWidths=[3*inch, 3*inch])

    table.setStyle(
        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2563EB")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("BACKGROUND",(0,1),(-1,-1),colors.whitesmoke),

            ("GRID",(0,0),(-1,-1),0.5,colors.grey),

            ("ALIGN",(0,0),(-1,-1),"CENTER"),

            ("BOTTOMPADDING",(0,0),(-1,0),10),
            ("TOPPADDING",(0,1),(-1,-1),8),
            ("BOTTOMPADDING",(0,1),(-1,-1),8),
        ])
    )

    story.append(table)
    story.append(Spacer(1,20))


def add_recommendations(story, styles, report):
    story.append( Paragraph( "<b>Recommendations</b>",styles["SectionHeading"] ))

    data = [["Suggestions"]]

    for recommendation in report["recommendations"]:
        data.append([f"✓ {recommendation}"])

    table = Table(
        data,
        colWidths=[6*inch]
    )

    table.setStyle(
        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F59E0B")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("BACKGROUND",(0,1),(-1,-1),colors.HexColor("#FEF3C7")),

            ("GRID",(0,0),(-1,-1),0.5,colors.grey),

            ("LEFTPADDING",(0,0),(-1,-1),12),
            ("RIGHTPADDING",(0,0),(-1,-1),12),

            ("TOPPADDING",(0,1),(-1,-1),8),
            ("BOTTOMPADDING",(0,1),(-1,-1),8),

        ])
    )

    story.append(table)
    story.append(Spacer(1,20))


def add_footer(story, styles):

    story.append(Spacer(1,15))

    story.append( Paragraph( "<b>Generated by ResumePilot AI</b>", styles["SectionHeading"] ))

    story.append( Paragraph( f"Generated on: {datetime.now().strftime('%d %B %Y | %I:%M %p')}",styles["BodyText"]))

    story.append( Paragraph( "Thank you for using ResumePilot AI. Best of luck with your career!", styles["BodyText"] ) )

def add_page_border(canvas, doc):
    canvas.saveState()

    width, height = doc.pagesize

    margin = 20

    canvas.setStrokeColor(colors.HexColor("#2563EB"))
    canvas.setLineWidth(2)

    canvas.rect( margin, margin, width - 2 * margin, height - 2 * margin)

    canvas.restoreState()
def add_matched_skills(story, styles, report):

    story.append(
        Paragraph(
            "<b>Matched Skills</b>",
            styles["SectionHeading"]
        )
    )

    data = [["Matched Skills"]]

    skills = report["matched_skills"]

    if not skills:
        data.append(["No matched skills found."])
    else:
        for skill in skills:
            data.append([f"✓ {skill}"])

    table = Table(data, colWidths=[6 * inch])

    table.setStyle(
        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#16A34A")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("BACKGROUND",(0,1),(-1,-1),colors.HexColor("#DCFCE7")),

            ("GRID",(0,0),(-1,-1),0.5,colors.grey),

            ("LEFTPADDING",(0,0),(-1,-1),12),
            ("RIGHTPADDING",(0,0),(-1,-1),12),

            ("TOPPADDING",(0,1),(-1,-1),8),
            ("BOTTOMPADDING",(0,1),(-1,-1),8),

        ])
    )

    story.append(table)
    story.append(Spacer(1,20))


def add_missing_skills(story, styles, report):

    story.append(
        Paragraph(
            "<b>Missing Skills</b>",
            styles["SectionHeading"]
        )
    )

    data = [["Missing Skills"]]

    skills = report["missing_skills"]

    if not skills:
        data.append(["Excellent! No missing skills."])
    else:
        for skill in skills:
            data.append([f"✗ {skill}"])

    table = Table(data, colWidths=[6 * inch])

    table.setStyle(
        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DC2626")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("BACKGROUND",(0,1),(-1,-1),colors.HexColor("#FEE2E2")),

            ("GRID",(0,0),(-1,-1),0.5,colors.grey),

            ("LEFTPADDING",(0,0),(-1,-1),12),
            ("RIGHTPADDING",(0,0),(-1,-1),12),

            ("TOPPADDING",(0,1),(-1,-1),8),
            ("BOTTOMPADDING",(0,1),(-1,-1),8),

        ])
    )

    story.append(table)
    story.append(Spacer(1,20))


def add_job_match_feedback(story, styles, report):

    story.append(
        Paragraph(
            "<b>Improvement Suggestions</b>",
            styles["SectionHeading"]
        )
    )

    data = [["Suggestions"]]

    for suggestion in report["feedback"]:
        data.append([f"✓ {suggestion}"])

    table = Table(data, colWidths=[6 * inch])

    table.setStyle(
        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F59E0B")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("BACKGROUND",(0,1),(-1,-1),colors.HexColor("#FEF3C7")),

            ("GRID",(0,0),(-1,-1),0.5,colors.grey),

            ("LEFTPADDING",(0,0),(-1,-1),12),
            ("RIGHTPADDING",(0,0),(-1,-1),12),

            ("TOPPADDING",(0,1),(-1,-1),8),
            ("BOTTOMPADDING",(0,1),(-1,-1),8),

        ])
    )

    story.append(table)
    story.append(Spacer(1,20))

def generate_ai_resume_feedback(resume_text):

    prompt = f"""
        You are an expert ATS Resume Writer.

        Analyze the following resume.

        Improve only these sections.

        1. Professional Summary

        2. Technical Skills

        3. Projects

        4. Experience

        5. General ATS Tips

        Rules:

        - Never invent fake experience.
        - Never add technologies not already supported by the resume.
        - Improve wording professionally.
        - Keep everything truthful.
        - Return clean Markdown.

        Resume:

        {resume_text}
        """

    response = model.generate_content(prompt)

    return response.text

@app.route("/ai-improve", methods=["POST"])
def ai_improve():

    file = request.files.get("resume")

    if not file:
        return jsonify({"error": "Resume not uploaded"}), 400

    try:
        resume_text = extract_text_from_pdf(file)
    except Exception:
        return jsonify({"error": "Unable to read resume"}), 400

    try:
        result = generate_ai_resume_feedback(resume_text)
    except Exception:
        return jsonify({"error": "AI service unavailable"}), 500

    return jsonify({
        "response": result
    })

@app.route("/download-report")
def download_report():
    global latest_report

    if not latest_report:
        return {"error": "No report available."}, 400

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = create_pdf_styles()
    story = []

    add_header(story, styles, latest_report)
    add_score_card(story, styles, latest_report)
    add_score_table(story, styles, latest_report)

    if latest_report.get("mode") == "job_match":

        add_matched_skills(story, styles, latest_report)
        add_missing_skills(story, styles, latest_report)
        add_job_match_feedback(story, styles, latest_report)

    else:

        add_resume_health(story, styles, latest_report)
        add_contact_section(story, styles, latest_report)
        add_skills_section(story, styles, latest_report)
        add_recommendations(story, styles, latest_report)

    add_footer(story, styles)

    doc.build(story,onFirstPage=add_page_border,onLaterPages=add_page_border)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="ResumePilot_Report.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
