from aiogram import Router
from .basic import register_tops_handlers

tops_router = Router(name="tops")

def setup_tops_router() -> Router:
    register_tops_handlers(tops_router)
    return tops_router
