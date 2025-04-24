from aiogram import Router
from .basic import register_search_handlers
from .advanced import register_advanced_search_handlers

search_router = Router(name="search")

def setup_search_router() -> Router:
    register_search_handlers(search_router)
    register_advanced_search_handlers(search_router)
    return search_router
