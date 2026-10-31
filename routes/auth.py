from fastapi import APIRouter , Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get('/login' , response_class=HTMLResponse)
def login(request : Request):
    return templates.TemplateResponse(request , "login.html" )

@router.get('/register' , response_class=HTMLResponse)
def register(request : Request):
    return templates.TemplateResponse(request , "register.html" )