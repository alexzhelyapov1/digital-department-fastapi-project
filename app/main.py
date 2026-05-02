"""
Main application entry point for the dictionary application.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import models, database
from .routers import words, auth as auth_router, pages

# Initialize database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="BG-RU Dictionary")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(auth_router.router)
app.include_router(words.router)
