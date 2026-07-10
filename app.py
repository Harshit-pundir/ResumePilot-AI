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
# PDF TEXT EXTRACTION
# ==========================================================

def extract_text_from_pdf(file):
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

def extract_resume_sections(text):
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
# LOAD KNOWING SKILLS
# ==========================================================


def load_skills():
    """
    Load all predefined skills from skills.json
    """

    with open("skills.json", "r", encoding="utf-8") as file:
        known_skills = json.load(file)

    return known_skills


def extract_skills(resume_text, jd_text, known_skills):
    """
    Extract skills present in
    Resume and Job Description.
    """

    # Convert to lowercase
    resume_text = resume_text.lower()
    jd_text = jd_text.lower()

    # Store unique skills
    resume_skills = set()
    jd_skills = set()

    # Check every skill
    for skill in known_skills:

        pattern = rf"\b{re.escape(skill.lower())}\b"

        if re.search(pattern, resume_text):
            resume_skills.add(skill)

        if re.search(pattern, jd_text):
            jd_skills.add(skill)

    return resume_skills, jd_skills


def match_skills(resume_skills, jd_skills):

    matched_skills = resume_skills & jd_skills

    missing_skills = jd_skills - resume_skills

    return matched_skills, missing_skills
