"""
Authentication routers for the dictionary application.
"""
from datetime import timedelta

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from .. import database, auth, crud, schemas
from ..templates import templates


router = APIRouter()


@router.get("/signup/", response_class=HTMLResponse, name="signup")
async def signup_page(request: Request):
    """Render the registration page."""
    return templates.TemplateResponse(request=request, name="registration/signup.html")


@router.post("/signup/", name="signup")
async def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """Handle user registration."""
    errors = []
    if crud.get_user_by_username(db, username):
        errors.append("Username already registered")
    if crud.get_user_by_email(db, email):
        errors.append("Email already registered")

    if errors:
        return templates.TemplateResponse(
            request=request, name="registration/signup.html", context={"errors": errors}
        )

    user_in = schemas.UserCreate(username=username, email=email, password=password)
    crud.create_user(db, user_in)
    return RedirectResponse(url="/login/", status_code=status.HTTP_302_FOUND)


@router.get("/login/", response_class=HTMLResponse, name="login")
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse(request=request, name="registration/login.html")


@router.post("/login/", name="login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """Handle user login and issue JWT token."""
    user = crud.get_user_by_username(db, username)
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request, name="registration/login.html", context={"error": "Invalid username or password"}
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url="/words/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.post("/logout/", name="logout")
async def logout():
    """Handle user logout by clearing the authentication cookie."""
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
