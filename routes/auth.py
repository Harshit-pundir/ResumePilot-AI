from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import COOKIE_SECURE
from extensions import supabase
from routes.security import create_token, hash_password, verify_password
from utils.constants import EXPIRE_MINUTES

from postgrest.exceptions import APIError

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def login_and_redirect(user_id):
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=create_token(user_id),
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")


@router.post("/auth/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    email = email.strip().lower()
    error = None

    if "@" not in email:
        error = "Please enter a valid email."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."
    elif password != confirm_password:
        error = "Passwords do not match."
    else:
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            error = "An account with this email already exists."

    if error:
        return templates.TemplateResponse(
            request, "register.html", {"error": error, "email": email}, status_code=400
        )

    try:
        new_user = supabase.table("users").insert(
            {"email": email, "password_hash": hash_password(password)}
        ).execute()
    except APIError as e:
        if "23505" in str(e):  # email pehle se hai
            return templates.TemplateResponse(
                request, "register.html",
                {"error": "An account with this email already exists.", "email": email},
                status_code=400,
            )
        raise

    return login_and_redirect(new_user.data[0]["id"])
    


@router.post("/auth/login", response_class=HTMLResponse)
def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()

    result = supabase.table("users").select("id, password_hash").eq("email", email).execute()
    user = result.data[0] if result.data else None

    if user is None or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "Invalid email or password.", "email": email},
            status_code=401,
        )

    return login_and_redirect(user["id"])


@router.post("/auth/logout")
def logout_user():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token")
    return response