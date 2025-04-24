from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import hashlib

def get_torrent_pagination_keyboard(kinopoisk_id: str, current_page: int, total_pages: int, 
                                  torrents: list, film_callback: str) -> InlineKeyboardBuilder:
    """
    Создает клавиатуру с пагинацией для торрентов
    
    Args:
        kinopoisk_id: ID фильма на Кинопоиске
        current_page: Текущая страница
        total_pages: Всего страниц
        torrents: Список торрентов для текущей страницы
        film_callback: Коллбек для возврата к карточке фильма
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки для торрентов в колонку
    for idx, torrent in enumerate(torrents):
        voice_display = torrent.get('voice', 'Неизвестная')
        if voice_display == "Дубляж":
            voice_display = "Дубляж (оригинал)"
        
        # Используем полное описание качества из торрента
        quality_display = torrent.get('quality_full', torrent['quality'])
        
        button_text = (
            f"📥 {quality_display} | "
            f"💾 {torrent['size_gb']:.1f}GB | "
            f"👥 {torrent['seeders']} | "
            f"🎧 {voice_display}"
        )
        
        # Добавляем каждый торрент отдельной строкой
        builder.row(InlineKeyboardButton(
            text=button_text,
            callback_data=f"td_{kinopoisk_id}_{idx}_{current_page}"  # Добавляем текущую страницу
        ))
    
    # Кнопки навигации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"tp_{kinopoisk_id}_{current_page-1}"
        ))
    
    # Добавляем номера страниц
    start_page = max(1, current_page - 2)
    end_page = min(total_pages, current_page + 2)
    
    for page in range(start_page, end_page + 1):
        text = f"[{page}]" if page == current_page else str(page)
        nav_buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=f"tp_{kinopoisk_id}_{page}"
        ))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"tp_{kinopoisk_id}_{current_page+1}"
        ))
    
    builder.row(*nav_buttons)
    
    # Кнопка возврата к карточке фильма
    builder.row(InlineKeyboardButton(
        text="↩️ Назад к фильму",
        callback_data=film_callback
    ))

    builder.row(InlineKeyboardButton(
        text="🏠 В главное меню",
        callback_data="main_menu"
    ))
    
    return builder

def get_torrent_details_keyboard(kinopoisk_id: str, magnet_link: str, current_page: int) -> InlineKeyboardBuilder:
    """Создает клавиатуру для деталей торрента"""
    builder = InlineKeyboardBuilder()
    
    # Генерируем короткий хеш для магнет-ссылки
    magnet_hash = hashlib.md5(magnet_link.encode()).hexdigest()[:8]
    
    # Кнопка скачивания с коротким хешем
    builder.row(InlineKeyboardButton(
        text="📥 Скачать торрент",
        callback_data=f"download_{magnet_hash}_{kinopoisk_id}"  # Добавляем kinopoisk_id для возврата
    ))
    
    # Кнопка возврата к списку
    builder.row(InlineKeyboardButton(
        text="↩️ Назад к списку",
        callback_data=f"tp_{kinopoisk_id}_{current_page}"
    ))

    builder.row(InlineKeyboardButton(
        text="🏠 В главное меню",
        callback_data="main_menu"
    ))
    
    return builder, magnet_hash  # Возвращаем и хеш для сохранения в Redis
