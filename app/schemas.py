"""
Pydantic schemas for the dictionary application.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class WordBase(BaseModel):
    """Base schema for Word."""
    bulgarian_word: str
    russian_translation: str
    example_sentence: Optional[str] = None
    is_learned: bool = False


class WordCreate(WordBase):
    """Schema for creating a Word."""


class Word(WordBase):
    """Schema for Word in response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int


class UserBase(BaseModel):
    """Base schema for User."""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a User."""
    password: str


class User(UserBase):
    """Schema for User in response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    words: List[Word] = []


class Token(BaseModel):
    """Schema for Auth Token."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for Token Data."""
    username: Optional[str] = None
