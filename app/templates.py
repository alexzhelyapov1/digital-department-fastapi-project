"""
Jinja2 templates configuration for the dictionary application.
"""
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
