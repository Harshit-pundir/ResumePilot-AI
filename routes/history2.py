from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from extensions2 import supabase
from utils.logger import get_logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = get_logger(__name__)


@router.get("/api/history")
def get_history():
    try:
        response = supabase.table("resume_history").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception:
        logger.exception("History fetch failed")
        return []


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    try:
        response = supabase.table("resume_history").select("*").order("created_at", desc=True).execute()
        history_items = response.data or []
    except Exception:
        logger.exception("History fetch failed")
        history_items = []
    return templates.TemplateResponse(request, "history.html", {"history": history_items})