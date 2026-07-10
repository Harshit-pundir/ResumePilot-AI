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
# EXTRACT IMPORTANT KEYWORDS
# ==========================================================

# ==========================================================
# EXTRACT IMPORTANT KEYWORDS
# ==========================================================

def get_tokens(text):
    """
    Extract meaningful keywords from text.

    This function:
    1. Converts text into tokens
    2. Removes stop words (is, the, of...)
    3. Removes punctuation
    4. Removes numbers
    5. Converts words to their base form (lemma)

    Example
    -------
    Input:
        "Developed REST APIs using Java and Spring Boot"

    Output:
        {
            "develop",
            "rest",
            "api",
            "java",
            "spring",
            "boot"
        }
    """

    # Convert text into spaCy document
    doc = nlp(text)

    # Store unique keywords
    keywords = set()

    # Visit every word
    for token in doc:

        # Ignore numbers
        if not token.is_alpha:
            continue

        # Ignore common words
        if token.is_stop:
            continue

        # Convert to base form
        keyword = token.lemma_.lower()

        # Store keyword
        keywords.add(keyword)

    return keywords

# ==========================================================
# MATCH JD KEYWORDS WITH RESUME
# ==========================================================

def match_keywords(jd_keywords, resume_text):
    """
    Compare Job Description keywords
    with Resume.

    Returns:
        matched_keywords
        missing_keywords
    """

    matched_keywords = []
    missing_keywords = []

    # Check every JD keyword
    for keyword in jd_keywords:

        # Match whole word only
        pattern = rf"\b{re.escape(keyword)}\b"

        if re.search(pattern, resume_text):

            matched_keywords.append(keyword)

        else:

            missing_keywords.append(keyword)

    return matched_keywords, missing_keywords

