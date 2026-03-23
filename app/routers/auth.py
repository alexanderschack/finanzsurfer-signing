from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.services.auth_service import authenticate_user, create_access_token
from app.templates_instance import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/admin/contracts", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "E-Mail oder Passwort falsch."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    token = create_access_token({"sub": user.email})
    redirect = RedirectResponse(url="/admin/contracts", status_code=302)
    is_prod = settings.app_env == "production"
    redirect.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        max_age=60 * 60 * 8,
    )
    return redirect


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
