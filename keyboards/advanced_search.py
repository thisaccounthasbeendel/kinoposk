from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional, Dict
from services.kinopoisk_api import kinopoisk_api

def get_advanced_search_keyboard(current_filters: Optional[Dict] = None) -> InlineKeyboardBuilder:
    """Создает клавиатуру для расширенного поиска"""
    builder = InlineKeyboardBuilder()
    
    if current_filters is None:
        current_filters = {}
    
    # Жанр
    genre_text = "🎭 Жанр"
    if current_filters.get('genre'):
        genre = current_filters['genre']
        genre_text += f": {genre['name']}"
    builder.button(
        text=genre_text,
        switch_inline_query_current_chat="#фильтр_жанр "
    )
    
    # Рейтинг
    rating_text = "⭐ Рейтинг"
    if current_filters.get('rating'):
        rating = current_filters['rating']
        rating_text += f": {rating['range']}"
    builder.button(
        text=rating_text,
        switch_inline_query_current_chat="#фильтр_рейтинг "
    )
    
    # Год
    year_text = "📅 Год выхода"
    if current_filters.get('year'):
        year = current_filters['year']
        year_text += f": {year['range']}"
    builder.button(
        text=year_text,
        switch_inline_query_current_chat="#фильтр_год "
    )
    
    # Страна
    country_text = "🌍 Страна"
    if 'country' in current_filters:
        country = current_filters['country']
        country_text = f"🌍 Страна: {country['name']}"
    builder.button(
        text=country_text,
        switch_inline_query_current_chat="#фильтр_страна "
    )
    
    # Сортировка
    sort_text = "📊 Сортировка"
    if current_filters.get('sort_by'):
        sort_text += f": {kinopoisk_api.sort_options[current_filters['sort_by']]}"
    builder.button(
        text=sort_text,
        switch_inline_query_current_chat="#фильтр_сортировка "
    )
    
    # Кнопки сброса, поиска и возврата в меню
    builder.button(text="🔄 Сбросить фильтры", callback_data="adv_reset")
    if any(current_filters.values()):
        builder.button(
            text="🔍 Искать с фильтрами",
            callback_data="adv_search_start"
        )
    builder.button(text="🏠 В Главное меню", callback_data="main_menu")
    
    # Настраиваем расположение кнопок (5 основных кнопок по 2 в ряд + кнопки действий по одной)
    builder.adjust(2, 2, 1, 1, 1, 1)
    
    return builder

def get_genres_keyboard(selected_genre: Optional[str] = None) -> InlineKeyboardBuilder:
    """Создает клавиатуру с жанрами"""
    builder = InlineKeyboardBuilder()
    
    # Используем существующий словарь жанров из API Кинопоиска
    for genre_name, genre_id in kinopoisk_api.genre_ids.items():
        text = f"✓ {genre_name}" if genre_name == selected_genre else genre_name
        builder.button(
            text=text,
            callback_data=f"genre_{genre_id}"
        )
    
    # Добавляем кнопку "Назад"
    builder.button(text="↩️ Назад", callback_data="advanced_search")
    
    # Настраиваем расположение кнопок (по 2 в ряд)
    builder.adjust(2)
    
    return builder

def get_back_to_filters_button(search_hash: str) -> InlineKeyboardBuilder:
    """Создает кнопку возврата к фильтрам"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚙️ Вернуться к фильтрам",
        callback_data=f"back_to_filters_{search_hash}"
    )
    return builder
