from aiogram import types
from aiogram.fsm.context import FSMContext
from handlers.tops.basic import process_top_pagination, COLLECTION_TYPES, COLLECTION_NAMES, FILMS_PER_PAGE
from handlers.search.basic import process_search_pagination
from handlers.search.advanced import process_advanced_search_pagination
from keyboards.main import get_main_menu
from constants import WELCOME_MESSAGE
from services.kinopoisk_api import kinopoisk_api
from keyboards.pagination import get_pagination_keyboard
import logging
from services.redis_service import RedisService

async def handle_back_to_results(callback: types.CallbackQuery):
    try:
        parts = callback.data.split('_')
        parts = parts[1:]  # Пропускаем префикс btr_
        
        if parts[0] == 's':  # Если это возврат к обычному поиску
            search_hash = parts[1]
            page = int(parts[2])
            await process_search_pagination(callback, search_hash, page)
        elif parts[0] == 'adv':  # Если это возврат к расширенному поиску
            search_hash = parts[1]
            page = int(parts[2])
            redis_service = RedisService.get_instance()
            search_data_json = await redis_service.get_query(f"adv_{search_hash}")  # Добавляем префикс adv_
            if search_data_json:
                await process_advanced_search_pagination(callback, search_hash, page)
            else:
                await callback.answer("Данные поиска не найдены")
        else:  # Если это возврат к топу
            collection_type = parts[0]
            page = int(parts[1])
            await process_top_pagination(callback, collection_type, page)

        await callback.answer()

    except Exception as e:
        logging.error(f"[BACK HANDLER] Error: {e}")
        await callback.answer("Произошла ошибка при возврате к результатам")

async def handle_main_menu(callback: types.CallbackQuery):
    """Обработчик для кнопки 'Главное меню'"""
    try:
        # Проверяем, можно ли редактировать сообщение
        # Если в сообщении есть медиа (фото/видео), его нельзя отредактировать в текст
        if callback.message.content_type == 'text':
            await callback.message.edit_text(
                WELCOME_MESSAGE,
                reply_markup=get_main_menu().as_markup(),
                parse_mode="HTML"
            )
        else:
            # Если сообщение с медиа - удаляем и отправляем новое
            try:
                await callback.message.delete()
            except Exception:
                pass  # Игнорируем ошибку, если сообщение уже удалено
            
            await callback.message.answer(
                WELCOME_MESSAGE,
                reply_markup=get_main_menu().as_markup(),
                parse_mode="HTML"
            )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Error in handle_main_menu: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")
