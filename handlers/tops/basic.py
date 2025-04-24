from aiogram import Router, F, types
from keyboards.tops import get_tops_menu
from keyboards.pagination import get_pagination_keyboard
from services.kinopoisk_api import kinopoisk_api
from constants import TOPS_RESULTS_TEMPLATE
import logging

# Словарь соответствия callback_data и типов коллекций API
COLLECTION_TYPES = {
    "tpop": "TOP_POPULAR_ALL",
    "tnew": "TOP_POPULAR_MOVIES",
    "t250": "TOP_250_MOVIES",
    "tcin": "TOP_AWAIT_MOVIES"
}

# Словарь соответствия callback_data и названий коллекций
COLLECTION_NAMES = {
    "tpop": "🔥 Популярное",
    "tnew": "🆕 Новинки",
    "t250": "⭐ Топ 250",
    "tcin": "🎬 Сейчас в кино"
}

# Количество фильмов на странице
FILMS_PER_PAGE = 10

async def show_tops_menu(callback: types.CallbackQuery):
    """Показывает меню с топами фильмов"""
    try:
        await callback.message.edit_text(
            "🏆 <b>Топы фильмов</b>\n\n"
            "Выберите интересующую вас категорию:",
            reply_markup=get_tops_menu().as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Error in show_tops_menu: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")

async def show_top_collection(callback: types.CallbackQuery):
    """Показывает выбранную коллекцию фильмов"""
    try:
        collection_type = callback.data
        api_collection_type = COLLECTION_TYPES.get(collection_type)
        collection_name = COLLECTION_NAMES.get(collection_type)

        result = await kinopoisk_api.get_collection(api_collection_type, 1)
        if not result:
            await callback.answer("Ошибка получения данных")
            return

        total_films = result.get('total', 0)
        if total_films == 0:
            await callback.answer("Фильмы не найдены")
            return

        custom_total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE
        films = result.get('items', [])[:FILMS_PER_PAGE]

        keyboard = get_pagination_keyboard(collection_type, 1, custom_total_pages, films)

        message_text = TOPS_RESULTS_TEMPLATE.format(
            collection_name=collection_name,
            page=1,
            total_pages=custom_total_pages,
            total_films=total_films
        )

        await callback.message.edit_text(
            text=message_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Error in show_top_collection: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")

async def process_top_pagination(callback: types.CallbackQuery, collection_type: str, page: int):
    """Обрабатывает пагинацию в топах фильмов"""
    try:
        api_collection_type = COLLECTION_TYPES.get(collection_type)
        collection_name = COLLECTION_NAMES.get(collection_type)

        result = await kinopoisk_api.get_collection(api_collection_type, page)
        if not result or 'items' not in result:
            await callback.answer("Не удалось загрузить страницу")
            return

        total_films = result.get('total', 0)
        films = result.get('items', [])[:FILMS_PER_PAGE]
        custom_total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE

        message_text = TOPS_RESULTS_TEMPLATE.format(
            collection_name=collection_name,
            page=page,
            total_pages=custom_total_pages,
            total_films=total_films
        )

        # Проверяем, является ли это возвратом к результатам
        if callback.data.startswith('btr_'):
            await callback.message.delete()
            await callback.message.answer(
                text=message_text,
                reply_markup=get_pagination_keyboard(collection_type, page, custom_total_pages, films).as_markup(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text=message_text,
                reply_markup=get_pagination_keyboard(collection_type, page, custom_total_pages, films).as_markup(),
                parse_mode="HTML"
            )
        
    except Exception as e:
        logging.error(f"Error in process_top_pagination: {e}")
        await callback.answer("Произошла ошибка при загрузке страницы")

def register_tops_handlers(router: Router):
    """Регистрирует обработчики для топов фильмов"""
    router.callback_query.register(show_tops_menu, F.data == "tops")
    router.callback_query.register(show_top_collection, F.data.in_(COLLECTION_TYPES.keys()))
    
    # Обработчик для пагинации в топах
    async def handle_top_pagination(callback: types.CallbackQuery):
        """Обработчик пагинации в топах"""
        try:
            parts = callback.data.split('_')
            collection_type = parts[0]  # tpop, tnew, t250, tcin
            page = int(parts[2])  # номер страницы

            await process_top_pagination(callback, collection_type, page)
        except Exception as e:
            logging.error(f"Error in handle_top_pagination: {e}")
            await callback.answer("Произошла ошибка при переключении страницы")

    # Регистрируем обработчик пагинации
    router.callback_query.register(
        handle_top_pagination,
        F.data.regexp(r'^(tpop|tnew|t250|tcin)_page_\d+$')
    )
