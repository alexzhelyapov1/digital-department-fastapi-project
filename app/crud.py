"""
Database CRUD operations for the dictionary application.
"""
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from . import models, schemas, auth


def get_user_by_username(db: Session, username: str):
    """Retrieve a user by their username."""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """Retrieve a user by their email."""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user in the database."""
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_words(db: Session, user_id: int):
    """Retrieve all words for a specific user."""
    return db.query(models.Word).filter(models.Word.user_id == user_id).order_by(
        models.Word.created_at.desc()
    ).all()


def create_word(db: Session, word: schemas.WordCreate, user_id: int):
    """Create a new word for a user."""
    db_word = models.Word(**word.model_dump(), user_id=user_id)
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word


def get_word(db: Session, word_id: int, user_id: int):
    """Retrieve a specific word for a user."""
    return db.query(models.Word).filter(
        models.Word.id == word_id,
        models.Word.user_id == user_id
    ).first()


def update_word(db: Session, word_id: int, word_data: schemas.WordCreate, user_id: int):
    """Update an existing word for a user."""
    db_word = get_word(db, word_id, user_id)
    if db_word:
        for key, value in word_data.model_dump().items():
            setattr(db_word, key, value)
        db.commit()
        db.refresh(db_word)
    return db_word


def get_random_word(db: Session, user_id: int):
    """Retrieve a random word for a user for quiz purposes."""
    # pylint: disable=not-callable
    return db.query(models.Word).filter(
        models.Word.user_id == user_id
    ).order_by(func.random()).first()
