"""
Page rendering routers for the dictionary application.
"""
import urllib.parse

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import database, auth, crud, models
from ..templates import templates


router = APIRouter()


def get_messages(request: Request):
    """Retrieve and decode flash messages from cookies."""
    msg = request.cookies.get("flash_msg")
    tag = request.cookies.get("flash_tag")
    if msg:
        # Decode URL-encoded Cyrillic message
        decoded_msg = urllib.parse.unquote(msg)
        return [{"text": decoded_msg, "tags": tag or "info"}]
    return []


@router.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request, user: models.User = Depends(auth.get_current_user)):
    """Render the landing page."""
    return templates.TemplateResponse(
        request=request, name="dictionary/index.html", context={"user": user}
    )


@router.get("/words/", response_class=HTMLResponse, name="word_list")
async def word_list(
    request: Request,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user_required)
):
    """Render the list of words for the current user."""
    words = crud.get_words(db, user.id)
    messages = get_messages(request)
    response = templates.TemplateResponse(
        request=request, name="dictionary/word_list.html",
        context={"user": user, "words": words, "messages": messages}
    )
    if messages:
        response.delete_cookie("flash_msg")
        response.delete_cookie("flash_tag")
    return response


@router.get("/words/add/", response_class=HTMLResponse, name="word_add")
async def word_add_page(
    request: Request,
    user: models.User = Depends(auth.get_current_user_required)
):
    """Render the page for adding a new word."""
    messages = get_messages(request)
    response = templates.TemplateResponse(
        request=request, name="dictionary/word_form.html", context={"user": user, "messages": messages}
    )
    if messages:
        response.delete_cookie("flash_msg")
        response.delete_cookie("flash_tag")
    return response


@router.get("/words/{pk}/edit/", response_class=HTMLResponse, name="word_edit")
async def word_edit_page(
    pk: int,
    request: Request,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user_required)
):
    """Render the page for editing an existing word."""
    word = crud.get_word(db, pk, user.id)
    messages = get_messages(request)
    response = templates.TemplateResponse(
        request=request, name="dictionary/word_form.html",
        context={"user": user, "word": word, "messages": messages}
    )
    if messages:
        response.delete_cookie("flash_msg")
        response.delete_cookie("flash_tag")
    return response


@router.get("/quiz/", response_class=HTMLResponse, name="quiz")
async def quiz_page(
    request: Request,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user_required)
):
    """Render the quiz trainer page."""
    word = crud.get_random_word(db, user.id)
    messages = get_messages(request)
    response = templates.TemplateResponse(
        request=request, name="dictionary/quiz.html",
        context={"user": user, "word": word, "messages": messages}
    )
    if messages:
        response.delete_cookie("flash_msg")
        response.delete_cookie("flash_tag")
    return response


@router.get("/words/import/", response_class=HTMLResponse, name="word_import")
async def word_import_page(
    request: Request,
    user: models.User = Depends(auth.get_current_user_required)
):
    """Render the CSV import page."""
    return templates.TemplateResponse(
        request=request, name="dictionary/word_import.html", context={"user": user}
    )
