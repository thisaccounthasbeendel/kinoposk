from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_about_menu() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📝 Последние обновления", switch_inline_query_current_chat="#инфо_историяверсий ")
    builder.button(text="✍️ Написать админу", url="https://t.me/thisaccounthasbeendel")
    builder.button(text="🏠 В Главное меню", callback_data="main_menu")
    
    builder.adjust(2, 1)
    
    return builder