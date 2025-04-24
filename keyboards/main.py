from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔍 Поиск фильма", callback_data="search")
    builder.button(text="📂 Категории", callback_data="categories")
    builder.button(text="🏆 Топы", callback_data="tops")
    builder.button(text="🔎 Расширенный поиск", callback_data="advanced_search")
    builder.button(text="ℹ️ О боте", callback_data="about")
    
    builder.adjust(2, 2, 1)
    
    return builder