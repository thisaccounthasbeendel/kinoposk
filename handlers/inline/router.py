from aiogram import Router
from .genres import router as genres_router
from .ratings import router as ratings_router
from .countries import router as countries_router
from .sorting import router as sorting_router
from .years import router as years_router
from .versions import router as versions_router  # Добавляем импорт

inline_router = Router(name="inline")

def setup_inline_router() -> Router:
    inline_router.include_router(genres_router)
    inline_router.include_router(ratings_router)
    inline_router.include_router(countries_router)
    inline_router.include_router(sorting_router)
    inline_router.include_router(years_router)
    inline_router.include_router(versions_router)  # Добавляем роутер версий
    return inline_router
