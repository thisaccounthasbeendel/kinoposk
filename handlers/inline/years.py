from aiogram import Router, F, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from datetime import datetime
from services.redis_service import RedisService
from keyboards.advanced_search import get_advanced_search_keyboard
import logging

router = Router()

def generate_year_ranges() -> list[tuple[str, str, str]]:
    """
    Генерирует список годов с разными интервалами
    Возвращает список кортежей (id, отображаемый_текст, значение_года)
    """
    current_year = datetime.now().year
    years = []
    
    # До 1950 - интервалы по 10 лет
    for decade in range(1900, 1950, 10):
        year_id = str(decade)
        year_range = f"{decade}-{decade+9}"
        years.append((year_id, year_range, year_range))
    
    # 1950-1969 - интервалы по 10 лет
    for decade in range(1950, 1970, 10):
        year_id = str(decade)
        year_range = f"{decade}-{decade+9}"
        years.append((year_id, year_range, year_range))
    
    # С 1970 до текущего года - интервалы по 5 лет
    start_year = 1970
    while start_year <= current_year:
        end_year = min(start_year + 4, current_year)
        year_id = str(start_year)
        year_range = f"{start_year}-{end_year}"
        years.append((year_id, year_range, year_range))
        start_year += 5
    
    return years

@router.inline_query(F.query.startswith("#фильтр_год"))
async def years_inline_query(query: types.InlineQuery):
    """Обрабатывает инлайн запрос для выбора года"""
    try:

        # Генерируем варианты годов для выбора
        years = generate_year_ranges()
        results = [
            InlineQueryResultArticle(
                id=year_id,
                title=f"📅 {display_text}",
                description=f"Фильмы {display_text} года",
                input_message_content=InputTextMessageContent(
                    message_text=f"year_{year_id}_{display_text}"
                )
            )
            for year_id, display_text, _ in years
        ]
        
        await query.answer(results, cache_time=300)
        
    except Exception as e:
        logging.error(f"[YEARS] Error in inline query: {e}")
        await query.answer([], cache_time=300)

@router.message(F.text.startswith("year_"))
async def handle_year_selection(message: types.Message):
    try:
        # Парсим сообщение (формат: year_ID_RANGE)
        _, year_id, year_range = message.text.split('_', 2)
        user_id = message.from_user.id
        
        # Получаем текущие фильтры и message_id
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        # Обновляем фильтры
        filters['year'] = {
            'id': year_id,
            'range': year_range
        }

        # Удаляем сообщение с выбором года
        await message.delete()
        
        # Сначала пытаемся отредактировать существующее сообщение
        if keyboard_message_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=keyboard_message_id,
                )
            except Exception as e:
                logging.error(f"Error editing message: {e}")
        
        # Если не получилось отредактировать, отправляем новое
        new_msg = await message.answer(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        # Сохраняем обновленные фильтры и новый message_id
        await redis_service.save_search_filters(user_id, filters, new_msg.message_id)
        
    except Exception as e:
        logging.error(f"[YEARS] Error handling year selection: {e}")
