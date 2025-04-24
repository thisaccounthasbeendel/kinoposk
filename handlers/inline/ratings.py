from aiogram import Router, F, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from services.redis_service import RedisService
from services.kinopoisk_api import kinopoisk_api
from keyboards.advanced_search import get_advanced_search_keyboard
import logging

router = Router()

@router.inline_query(F.query.startswith("#фильтр_рейтинг"))
async def ratings_inline_query(query: types.InlineQuery):
    logging.info(f"[RATINGS] Processing inline query from user {query.from_user.id}")
    
    # Используем значения из kinopoisk_api.rating_values
    results = [
        InlineQueryResultArticle(
            id=rating_id,
            title=f"От {rating_from} до {rating_to}",
            description=f"Фильмы с рейтингом {rating_from}-{rating_to}",
            input_message_content=InputTextMessageContent(
                message_text=f"rating_{rating_id}_{rating_from}-{rating_to}"
            )
        )
        for rating_id, (rating_from, rating_to) in kinopoisk_api.rating_values.items()
    ]
    
    logging.info(f"[RATINGS] Generated {len(results)} rating options")
    await query.answer(results, cache_time=300)

@router.message(F.text.startswith("rating_"))
async def process_rating_selection(message: types.Message):
    try:
        # Парсим сообщение (формат: rating_ID_RANGE)
        _, rating_id, rating_range = message.text.split('_', 2)
        user_id = message.from_user.id
        
        # Получаем текущие фильтры и message_id
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        # Обновляем фильтры
        filters['rating'] = {
            'id': rating_id,
            'range': rating_range
        }

        # Удаляем сообщение с выбором рейтинга
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
        logging.error(f"[RATINGS] Error handling rating selection: {e}")
