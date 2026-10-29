import markdown

from fastapi import APIRouter , File , UploadFile
from fastapi.responses import JSONResponse

from services.ai_service import generate_ai_resume_feedback
from services.pdf_parser import extract_text_from_pdf
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _friendly_ai_error(error):
    """Convert provider failures to safe messages for the UI."""
    status_code = getattr(error, "status_code", None)
    error_name = error.__class__.__name__.lower()
    is_network_error = (
        "connection" in error_name
        or "network" in error_name
        or "api" in error_name
    )

    if status_code == 429 or "rate" in error_name:
        return (
            "The AI service is busy right now. Please wait a moment and try again.",
            429,
        )

    if status_code in (408, 504) or "timeout" in error_name:
        return "The AI request took too long. Please try again in a moment.", 504

    if is_network_error:
        return (
            "We could not reach the AI service. "
            "Please check your connection and try again.",
            503,
        )

    return "We could not generate AI suggestions right now. Please try again.", 500


@router.post("/ai-improve")
def ai_improve(resume : UploadFile = File(None)):
    if not resume:
        error_response = {"error": "Resume not uploaded"}
        return JSONResponse(error_response, 400)

    try:
        resume_text = extract_text_from_pdf(resume.file)
    except Exception:
        error_response = {"error": "Unable to read resume"}
        return JSONResponse(error_response, 400)
    
    try:
        result = generate_ai_resume_feedback(resume_text)
    except Exception as error:
        logger.exception("AI provider error")
        message, status = _friendly_ai_error(error)
        error_response = {"error": message}
        return JSONResponse(error_response, status)

    rendered_html = markdown.markdown(
        result,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )
    response_payload = {
        "response": result,
        "html": rendered_html,
    }
    return response_payload