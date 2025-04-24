
from aiogram import Router, F, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from services.redis_service import RedisService
from services.kinopoisk_api import kinopoisk_api
from keyboards.advanced_search import get_advanced_search_keyboard
import logging

router = Router()

@router.inline_query(F.query.startswith("#фильтр_страна"))
async def countries_inline_query(query: types.InlineQuery):
    logging.info(f"[COUNTRIES] Processing inline query from user {query.from_user.id}")
    
    RESULTS_PER_PAGE = 50
    offset = int(query.offset) if query.offset else 0
    
    search_query = query.query.replace("#фильтр_страна", "").strip().lower()
    
    # Получаем список стран из API
    countries = await kinopoisk_api.countries
    if not countries:
        logging.error("[COUNTRIES] Failed to get countries from API")
        return await query.answer(
            results=[],
            cache_time=300
        )
    
    # Фильтруем страны по поисковому запросу
    if search_query:
        countries = [
            country for country in countries
            if search_query in country['country'].lower()
        ]
    
    # Добавляем опцию "Любая" только на первой странице
    if offset == 0:
        countries.insert(0, {"id": "none", "country": "Любая"})
    
    # Получаем срез стран для текущей страницы
    current_page = countries[offset:offset + RESULTS_PER_PAGE]
    
    results = [
        InlineQueryResultArticle(
            id=str(country['id']),
            title=country['country'],
            input_message_content=InputTextMessageContent(
                message_text=f"country_{country['id']}_{country['country']}"
            )
        )
        for country in current_page
    ]
    
    # Определяем, есть ли ещё страны для следующей страницы
    next_offset = str(offset + RESULTS_PER_PAGE) if len(countries) > offset + RESULTS_PER_PAGE else ""
    
    logging.info(f"[COUNTRIES] Generated {len(results)} country options, offset: {offset}, next_offset: {next_offset}")
    await query.answer(
        results=results,
        cache_time=300,
        next_offset=next_offset
    )

@router.message(F.text.startswith("country_"))
async def handle_country_selection(message: types.Message):
    """Обрабатывает выбор страны из инлайн режима"""
    try:
        _, country_id, country_name = message.text.split('_', 2)
        user_id = message.from_user.id
        
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        filters['country'] = {
            'id': country_id,
            'name': country_name
        }
        
        await message.delete()
        
        if keyboard_message_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=keyboard_message_id
                )
            except Exception as e:
                logging.error(f"[COUNTRIES] Error editing message: {e}")
        
        new_msg = await message.answer(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        await redis_service.save_search_filters(user_id, filters, new_msg.message_id)
        
    except Exception as e:
        logging.error(f"[COUNTRIES] Error processing country selection: {e}")

