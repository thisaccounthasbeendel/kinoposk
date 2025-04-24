import hashlib
import logging
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_short_hash(text: str, length: int = 5) -> str:
    """Генерирует короткий хеш из текста"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:length]

def get_pagination_keyboard(collection_type: str, current_page: int, total_pages: int, films: list) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
        
    # Получаем search_hash из collection_type (например, из 's_b4a5d' получаем 'b4a5d')
    search_hash = collection_type.split('_')[1] if '_' in collection_type else collection_type
    
    # Добавляем кнопки фильмов
    for film in films:
        film_id = film.get('kinopoiskId', '')
        name_ru = film.get('nameRu', 'Нет названия')
        year = film.get('year', '')
        rating = film.get('ratingKinopoisk', '')
        type_ru = "🎥" if film.get('type', '') == 'TV_SERIES' else "🍿"

        button_text = f"{type_ru}"
        if rating:
            button_text += f" - ⭐ {rating}"
        button_text += f" | {name_ru}"
        if year:
            button_text += f" ({year})"
        

        # Используем search_hash из collection_type вместо генерации нового хеша
        if collection_type.startswith('s_'):
            callback_data = f"f_{film_id}_{search_hash}_s_{current_page}"
        elif collection_type.startswith('adv_'):
            callback_data = f"f_{film_id}_{search_hash}_adv_{current_page}"
        else:
            callback_data = f"f_{film_id}_{collection_type}_{current_page}"
            
        builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    # Кнопки навигации
    if total_pages > 1:
        nav_buttons = []
        if current_page > 1:
            prev_callback = f"{collection_type}_page_{current_page-1}"
            nav_buttons.append(InlineKeyboardButton(
                text="◀️",
                callback_data=prev_callback
            ))
        
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)
        
        for page in range(start_page, end_page + 1):
            text = f"[{page}]" if page == current_page else str(page)
            page_callback = f"{collection_type}_page_{page}"
            nav_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=page_callback
            ))
        
        if current_page < total_pages:
            next_callback = f"{collection_type}_page_{current_page+1}"
            nav_buttons.append(InlineKeyboardButton(
                text="▶️",
                callback_data=next_callback
            ))
        
        builder.row(*nav_buttons)

    # Добавляем кнопку возврата к фильтрам для расширенного поиска
    if collection_type.startswith('adv_'):
        builder.row(InlineKeyboardButton(
            text="⚙️ Вернуться к фильтрам",
            callback_data=f"back_to_filters_{search_hash}"
        ))

    builder.row(InlineKeyboardButton(
        text="🏠 В Главное меню",
        callback_data="main_menu"
    ))

    return builder
