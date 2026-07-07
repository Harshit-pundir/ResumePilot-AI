from flask import Flask, render_template, request, jsonify, redirect, url_for
from PyPDF2 import PdfReader
from supabase import create_client
from dotenv import load_dotenv
import os
import spacy

# ── Config ──────────────────────────────────────────────
load_dotenv()
nlp = spacy.load("en_core_web_sm")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)


# ── Helper Functions ─────────────────────────────────────
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text.lower().replace("\n", " ")


def extract_sections(text):
    sections = {"skills": "", "projects": "", "education": ""}
    if "technical skills" in text:
        sections["skills"] = text.split("technical skills")[-1].split("leadership")[0]
    if "projects" in text:
        sections["projects"] = text.split("projects")[-1].split("technical skills")[0]
    if "education" in text:
        sections["education"] = text.split("education")[-1].split("projects")[0]
    return sections


def get_tokens(text):
    doc = nlp(text)
    return set([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])


def match_keywords(tokens, text):
    matched = [t for t in tokens if t in text]
    unmatched = [t for t in tokens if t not in text]
    return matched, unmatched


def score_sections(sections, jd_tokens):
    result = {}
    for section_name, section_text in sections.items():
        matched = [t for t in jd_tokens if t in section_text]
        total = len(jd_tokens)
        result[section_name + "_score"] = round((len(matched) / total * 100), 2) if total > 0 else 0
    return result

def generate_tips(unmatched_keywords):
    tech_skills = ["python", "java", "flask", "sql", "django", "react", "node", "javascript", "typescript", "docker", "kubernetes", "aws", "git", "mongodb", "postgresql", "redis", "linux", "rest", "api", "machine learning", "deep learning", "pytorch", "tensorflow", "pandas", "numpy", "scikit", "html", "css", "c++", "c", "golang", "rust", "spring", "mysql"]

    soft_skills = ["expert", "solving", "problem", "analytical", "communication", "leadership", "teamwork", "management", "critical", "creative"]

    result= []
    for keyword in unmatched_keywords:
        if keyword in tech_skills:
            tip = f"Add '{keyword}' to your Technical Skills section"
        elif keyword in soft_skills:
            tip = f"Highlight '{keyword}' skills in your Professional Summary section"
        else:
            tip = f"Consider adding '{keyword}' experience to strengthen your resume"    

        result.append(tip)    

    return result    

# ── Routes ───────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return redirect(url_for("home"))

    jd_text = request.form.get("job_description", "").lower()
    file = request.files.get("file")

    if not jd_text:
        return jsonify({"error": "Job description is empty"}), 400
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    text = extract_text_from_pdf(file)
    sections = extract_sections(text)
    jd_tokens = get_tokens(jd_text)

    matched, unmatched = match_keywords(jd_tokens, text)
    total = len(matched) + len(unmatched)
    score = round((len(matched) / total * 100), 2) if total > 0 else 0

    section_scores = score_sections(sections, jd_tokens)
    unmatched_word_tips = generate_tips(unmatched)

    supabase.table("ats_results").insert({
        "job_description": jd_text,
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": unmatched
    }).execute()

    return jsonify({
        "Score": score,
        "KeyWord_exists": matched,
        "KeyWord_not_exist": unmatched,
        "section_scores": section_scores,
        "Unmatched_keyword_tips" : unmatched_word_tips
    })


@app.route("/history", methods=["GET"])
def history():
    result = supabase.table("ats_results").select("*").execute()
    return render_template("history.html", results=result.data)


# ── Run ──────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)