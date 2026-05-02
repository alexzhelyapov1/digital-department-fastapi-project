"""
Word management routers for the dictionary application.
"""
import csv
import io
import re
import urllib.parse

from fastapi import APIRouter, Depends, Form, UploadFile, File, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import database, auth, crud, schemas, models


router = APIRouter()


def validate_cyrillic(value: str, field_name: str):
    """Validate that a string contains only Cyrillic characters and allowed punctuation."""
    # Allowed: Cyrillic letters, spaces, hyphens, commas, dots, and common punctuation
    if not re.match(r'^[а-яА-ЯёЁ\s\-,\.!\?]+$', value):
        return f"Поле '{field_name}' должно содержать только кириллицу и допустимые символы."
    return None


@router.post("/words/add/", name="word_add")
async def word_add(
    bulgarian_word: str = Form(...),
    russian_translation: str = Form(...),
    example_sentence: str = Form(None),
    is_learned: bool = Form(False),
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user_required)
):
    """Handle adding a new word to the dictionary."""
    error = validate_cyrillic(bulgarian_word, "Болгарское слово")
    if not error:
        error = validate_cyrillic(russian_translation, "Русский перевод")

    if error:
        response = RedirectResponse(url="/words/add/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="flash_msg", value=urllib.parse.quote(error), max_age=5)
        response.set_cookie(key="flash_tag", value="danger", max_age=5)
        return response

    word_in = schemas.WordCreate(
        bulgarian_word=bulgarian_word,
        russian_translation=russian_translation,
        example_sentence=example_sentence,
        is_learned=is_learned
    )
    crud.create_word(db, word_in, user.id)

    response = RedirectResponse(url="/words/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="flash_msg", value=urllib.parse.quote("Слово успешно добавлено!"), max_age=5)
    response.set_cookie(key="flash_tag", value="success", max_age=5)
    return response


@router.post("/words/{pk}/edit/", name="word_edit")
async def word_edit(
    pk: int,
    bulgarian_word: str = Form(...),
    russian_translation: str = Form(...),
    example_sentence: str = Form(None),
    is_learned: bool = Form(False),
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user_required)
):
    """Handle updating an existing word."""
    error = validate_cyrillic(bulgarian_word, "Болгарское слово")
    if not error:
        error = validate_cyrillic(russian_translation, "Русский перевод")

    if error:
        response = RedirectResponse(url=f"/words/{pk}/edit/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="flash_msg", value=urllib.parse.quote(error), max_age=5)
        response.set_cookie(key="flash_tag", value="danger", max_age=5)
        return response

    word_in = schemas.WordCreate(
        bulgarian_word=bulgarian_word,
        russian_translation=russian_translation,
        example_sentence=example_sentence,
        is_learned=is_learned
    )
    crud.update_word(db, pk, word_in, user.id)

    response = RedirectResponse(url="/words/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="flash_msg", value=urllib.parse.quote("Слово успешно обновлено!"), max_age=5)
    response.set_cookie(key="flash_tag", value="success", max_age=5)
    return response


@router.post("/quiz/", name="quiz")
async def quiz_check(
    word_id: int = Form(...),
    translation: str = Form(...),
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user_required)
):
    """Check the user's answer in the quiz trainer."""
    word = crud.get_word(db, word_id, user.id)
    if not word:
        return RedirectResponse(url="/quiz/", status_code=status.HTTP_302_FOUND)

    correct = word.russian_translation.strip().lower()
    user_trans = translation.strip().lower()

    response = RedirectResponse(url="/quiz/", status_code=status.HTTP_302_FOUND)
    if user_trans == correct:
        msg = f"Верно! {word.bulgarian_word} = {word.russian_translation}"
        response.set_cookie(key="flash_msg", value=urllib.parse.quote(msg), max_age=5)
        response.set_cookie(key="flash_tag", value="success", max_age=5)
    else:
        msg = f"Ошибка. Правильный перевод для '{word.bulgarian_word}' - '{word.russian_translation}'"
        response.set_cookie(key="flash_msg", value=urllib.parse.quote(msg), max_age=5)
        response.set_cookie(key="flash_tag", value="danger", max_age=5)

    return response


@router.post("/words/import/", name="word_import")
async def word_import(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user_required)
):
    """Handle importing words from a CSV file."""
    content = await file.read()
    data_set = content.decode('UTF-8')
    io_string = io.StringIO(data_set)
    reader = csv.DictReader(io_string)

    imported_count = 0
    skipped_count = 0

    for row in reader:
        bulgarian = row.get('bulgarian_word', '').strip()
        russian = row.get('russian_translation', '').strip()
        example = row.get('example_sentence', '').strip()

        if not bulgarian or not russian:
            continue

        # Check for duplicates
        exists = db.query(models.Word).filter(
            models.Word.user_id == user.id,
            models.Word.bulgarian_word == bulgarian,
            models.Word.russian_translation == russian
        ).first()

        if not exists:
            word_in = models.Word(
                user_id=user.id,
                bulgarian_word=bulgarian,
                russian_translation=russian,
                example_sentence=example
            )
            db.add(word_in)
            imported_count += 1
        else:
            skipped_count += 1

    db.commit()

    msg = f"Успешно импортировано: {imported_count}. Пропущено (дубликаты): {skipped_count}."
    response = RedirectResponse(url="/words/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="flash_msg", value=urllib.parse.quote(msg), max_age=5)
    response.set_cookie(key="flash_tag", value="success", max_age=5)
    return response
