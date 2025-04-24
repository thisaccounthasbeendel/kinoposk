from aiogram import Router
from .basic import register_about_handlers

about_router = Router(name="about")

def setup_about_router() -> Router:
    register_about_handlers(about_router)
    return about_router