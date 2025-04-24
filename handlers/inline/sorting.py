from aiogram import Router, F, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from services.redis_service import RedisService
from services.kinopoisk_api import kinopoisk_api
from keyboards.advanced_search import get_advanced_search_keyboard
import logging

router = Router()

@router.inline_query(F.query.startswith("#фильтр_сортировка"))
async def sorting_inline_query(query: types.InlineQuery):
    logging.info(f"[SORTING] Processing inline query from user {query.from_user.id}")
    
    results = [
        InlineQueryResultArticle(
            id=sort_key,
            title=sort_name,
            description=f"Сортировать результаты {sort_name.lower()}",
            input_message_content=InputTextMessageContent(
                message_text=f"sort_{sort_key}"
            )
        )
        for sort_key, sort_name in kinopoisk_api.sort_options.items()
    ]
    
    logging.info(f"[SORTING] Generated {len(results)} sorting options")
    await query.answer(results, cache_time=300)

@router.message(F.text.startswith("sort_"))
async def process_sort_selection(message: types.Message):
    try:
        # Парсим сообщение (формат: sort_KEY)
        _, sort_key = message.text.split('_', 1)
        user_id = message.from_user.id
        
        # Получаем текущие фильтры и message_id
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        # Обновляем фильтры
        filters['sort_by'] = sort_key

        # Удаляем сообщение с выбором сортировки
        await message.delete()
        
        # Если есть сохраненное сообщение с клавиатурой, удаляем его
        if keyboard_message_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=keyboard_message_id
                )
            except Exception as e:
                logging.error(f"Error deleting keyboard message: {e}")
        
        # Отправляем новое сообщение с обновленной клавиатурой
        new_msg = await message.answer(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        # Сохраняем обновленные фильтры и новый message_id
        await redis_service.save_search_filters(user_id, filters, new_msg.message_id)
        
    except Exception as e:
        logging.error(f"[SORTING] Error handling sort selection: {e}")
