from aiogram import Router, F, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from services.redis_service import RedisService
from services.kinopoisk_api import kinopoisk_api
from keyboards.advanced_search import get_advanced_search_keyboard
import logging

router = Router()

@router.inline_query(F.query.startswith("#фильтр_жанр"))
async def genres_inline_query(query: types.InlineQuery):
    logging.info(f"[GENRES] Processing inline query from user {query.from_user.id}")
    
    search_query = query.query.replace("#фильтр_жанр", "").strip().lower()
    
    # Получаем список жанров из API
    genres = await kinopoisk_api.genres
    if not genres:
        logging.error("[GENRES] Failed to get genres from API")
        return await query.answer(
            results=[],
            cache_time=300
        )
    
    # Фильтруем пустые значения
    genres = [genre for genre in genres if genre.get('genre') and genre.get('id')]
    
    # Добавляем опцию "Любой"
    genres.insert(0, {"id": "none", "genre": "Любой"})
    
    # Фильтруем жанры по поисковому запросу если он есть
    if search_query:
        genres = [
            genre for genre in genres
            if search_query in genre['genre'].lower()
        ]
    
    results = [
        InlineQueryResultArticle(
            id=str(genre['id']),
            title=genre['genre'],
            input_message_content=InputTextMessageContent(
                message_text=f"genre_{genre['id']}_{genre['genre']}"
            ),
            description="Выбрать жанр"  # Добавим description для наглядности
        )
        for genre in genres
    ]
    
    logging.info(f"[GENRES] Generated {len(results)} genre options")
    
    # Добавим логирование для отладки
    logging.info(f"[GENRES] Results: {[{'id': r.id, 'title': r.title} for r in results]}")
    
    await query.answer(
        results=results,
        cache_time=300
    )

@router.message(F.text.startswith("genre_"))
async def handle_genre_selection(message: types.Message):
    try:
        # Парсим сообщение (формат: genre_ID_NAME)
        _, genre_id, genre_name = message.text.split('_', 2)
        user_id = message.from_user.id
        
        # Получаем текущие фильтры и message_id
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        # Обновляем фильтры
        filters['genre'] = {
            'id': genre_id,
            'name': genre_name
        }

        # Удаляем сообщение с выбором жанра
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
        logging.error(f"[GENRES] Error handling genre selection: {e}")
