# ==========================================================
# ATS RESUME SCORE CHECKER
# Part 1 - Project Setup & Resume Parser
# Author : Harshit Pundir
# ==========================================================

# -----------------------------
# Import Required Libraries
# -----------------------------

from flask import Flask
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from supabase import create_client
import json
import os
import re
import spacy


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

nlp = spacy.load("en_core_web_sm")


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

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ==========================================================
# ATS SCORE WEIGHTS
# ==========================================================

SKILL_WEIGHT = 60
SECTION_WEIGHT = 20
CONTACT_WEIGHT = 10
COMPLETENESS_WEIGHT = 10

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

            continue

    return complete_text.lower()


# ==========================================================
# RESUME SECTION EXTRACTOR
# ==========================================================

def extract_section(text, headings):
    """
    Extract a particular section
    like Skills, Projects, Education etc.

    Parameters
    ----------
    text : Resume text

    headings : List of possible section names

    Returns
    -------
    Extracted section text
    """

    # Escape special characters
    pattern = "|".join(map(re.escape, headings))

    regex = (
        rf"(?:{pattern})"
        rf"\s*(.*?)"
        rf"(?=\b(?:"
        rf"education|"
        rf"projects|"
        rf"experience|"
        rf"skills|"
        rf"technical skills|"
        rf"certifications|"
        rf"summary|"
        rf"$)\b)"
    )

    match = re.search(
        regex,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return ""


# ==========================================================
# EXTRACT ALL SECTIONS
# ==========================================================

def extract_resume_sections(text) :
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


def load_skills() -> list:
    """
    Load all predefined skills from skills.json
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    skills_file = os.path.join(base_dir, "skills.json")

    try:
        with open(skills_file, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        print("skills.json file not found.")
        return []

    except json.JSONDecodeError:
        print("Invalid JSON format.")
        return []


def extract_skills(text : str, known_skills : list) -> set:
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


def match_skills(resume_skills: set,jd_skills: set):
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

def extract_contact_details(text: str) -> dict:
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

    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",text)
    if email:
        contacts["email"] = email.group()

    # -------------------------
    # Phone Number
    # -------------------------

    phone = re.search(r"(?:\+91[\-\s]?)?[6-9]\d{9}",text)

    if phone:
        contacts["phone"] = phone.group()

    # -------------------------
    # LinkedIn
    # -------------------------

    linkedin = re.search(r"https?://(?:www\.)?linkedin\.com/[^\s]+",text)

    if linkedin:
        contacts["linkedin"] = linkedin.group()

    # -------------------------
    # GitHub
    # -------------------------

    github = re.search(r"https?://(?:www\.)?github\.com/[^\s]+",text)

    if github:
        contacts["github"] = github.group()

    # -------------------------
    # Portfolio
    # -------------------------

    portfolio = re.search( r"https?://[^\s]+",text)

    if portfolio:

        url = portfolio.group()

        if ("linkedin.com" not in url and"github.com" not in url):
            contacts["portfolio"] = url

    return contacts

# ==========================================================
# CALCULATE SKILL SCORE
# ==========================================================

def calculate_skill_score(matched_skills : set,jd_skills : set) -> float:
    """
    Calculate how many required skills
    are present in the resume.

    Formula

        matched skills
    ---------------------- × 100
      total JD skills
    """

    # Prevent division by zero
    if len(jd_skills) == 0:
        return 0
    

    score = (len(matched_skills) / len(jd_skills) ) * 100
    return round(score,2)

# ==========================================================
# CALCULATE SECTION SCORE
# ==========================================================

def calculate_section_score(sections : dict) -> float:
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
    available_section = 0

    # Check every section
    for section in sections.values():

        if section.strip():
            available_sections += 1

    score = (available_sections/total_sections) * 100

    return round(score, 2)


# ==========================================================
# CALCULATE CONTACT SCORE
# ==========================================================

def calculate_contact_score(contact_details: dict) -> float:
    """
    Calculate score based on
    available contact information.
    """

    total_contact_details = len(contact_details)
    available_contact_details = 0

    for contact in contact_details.values():

        if contact:
            available_contact_details += 1

    score = (
        available_contact_details
        /
        total_contact_details
    ) * 100

    return round(score, 2)

# ==========================================================
# CALCULATE RESUME COMPLETENESS SCORE
# ==========================================================

def calculate_completeness_score(sections: dict,contact_details: dict) -> float:
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

    score = (
        available_items
        /
        total_items
    ) * 100

    return round(score, 2)

# ==========================================================
# CALCULATE FINAL ATS SCORE
# ==========================================================

def calculate_ats_score(skill_score: float,section_score: float,contact_score: float,completeness_score: float) -> float:
    """
    Calculate final ATS score
    using weighted scoring.
    """

    final_score = (

        skill_score * SKILL_WEIGHT +

        section_score * SECTION_WEIGHT +

        contact_score * CONTACT_WEIGHT +

        completeness_score * COMPLETENESS_WEIGHT

    ) / 100

    return round(final_score, 2)