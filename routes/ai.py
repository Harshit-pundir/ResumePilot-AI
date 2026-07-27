from flask import Blueprint, jsonify, request

from services.ai_service import generate_ai_resume_feedback
from services.pdf_parser import extract_text_from_pdf
from utils.logger import get_logger

ai_bp = Blueprint("ai", __name__)
logger = get_logger(__name__)


@ai_bp.route("/ai-improve", methods=["POST"])
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
    except Exception as e:
        logger.exception("Gemini API Error")
        return jsonify({"error": str(e)}), 500
    return jsonify({"response": result})
