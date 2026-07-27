from flask import Blueprint, current_app, render_template

import extensions
from utils.logger import get_logger

history_bp = Blueprint("history", __name__)
logger = get_logger(__name__)


@history_bp.route("/history")
def history():
    try:
        response = extensions.get_supabase(current_app).table("resume_history").select("*").order("created_at", desc=True).execute()
        history_items = response.data or []
    except Exception:
        logger.exception("Failed to fetch resume history from Supabase.")
        history_items = []
    return render_template("history.html", history=history_items)
