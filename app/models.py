"""
Database models for the dictionary application.
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """User model representing a registered user."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    words = relationship("Word", back_populates="owner")


class Word(Base):
    """Word model representing a Bulgarian word with its translation."""
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    bulgarian_word = Column(String, index=True)
    russian_translation = Column(String)
    example_sentence = Column(Text, nullable=True)
    is_learned = Column(Boolean, default=False)
    # pylint: disable=not-callable
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="words")
