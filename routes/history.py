from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from deps import get_current_user
from extensions import supabase

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    response = (supabase.table("resume_history").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute())
    return templates.TemplateResponse(
        request, "history.html", {"history": response.data, "user": user}
    )


@router.get("/api/history")
def history_api(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Please log in."}, status_code=401)

    response = (supabase.table("resume_history").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute())
    return response.data


@router.get("/admin/history", response_class=HTMLResponse)
def admin_history(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user["role"] != "admin":
        return HTMLResponse("Admin only", status_code=403)

    # admin ko sabki rows milti hain (koi filter nahi)
    rows = supabase.table("resume_history").select("*").order("created_at", desc=True).execute().data
    users = supabase.table("users").select("id, email").execute().data

    email_of = {u["id"]: u["email"] for u in users}   # id se email dhundne ke liye
    for row in rows:
        row["owner_email"] = email_of.get(row.get("user_id"), "(unknown)")

    return templates.TemplateResponse(
        request, "history.html", {"history": rows, "user": user, "show_owner": True}
    )
