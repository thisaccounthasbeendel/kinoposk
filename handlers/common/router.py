from aiogram import Router, F, types
from .film_card import show_film_card, register_handlers
from .back_handler import handle_back_to_results, handle_main_menu

common_router = Router(name="common")

async def handle_categories(callback: types.CallbackQuery):
    """Пустой обработчик для categories"""
    await callback.answer()

def setup_common_handlers(router: Router) -> Router:
    # Регистрируем обработчики для магнет-ссылок
    register_handlers(router)
    
    # Обработчик для показа карточки фильма
    router.callback_query.register(
        show_film_card,
        F.data.startswith("f_")
    )

    # Обработчик для кнопки "Назад к результатам"
    router.callback_query.register(
        handle_back_to_results,
        F.data.startswith("btr_")
    )

    # Обработчик для кнопки "Главное меню"
    router.callback_query.register(
        handle_main_menu,
        F.data == "main_menu"
    )

    # Добавляем пустой обработчик для categories
    router.callback_query.register(
        handle_categories,
        F.data == "categories"
    )
    
    return router
