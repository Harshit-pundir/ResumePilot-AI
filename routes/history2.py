from fastapi import APIRouter
from utils.logger import get_logger
from extensions2 import supabase

router = APIRouter();
logger = get_logger(__name__)

@router.get("/api/history")
def get_history():
    try:
        
        response = supabase.table("resume_history").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception:
        logger.exception("History fetch failed")
        return []
