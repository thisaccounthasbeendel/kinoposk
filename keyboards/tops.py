from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_tops_menu() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    builder.button(text="🔥 Популярное", callback_data="tpop")
    builder.button(text="🆕 Новинки", callback_data="tnew")
    builder.button(text="⭐ Топ 250", callback_data="t250")
    #builder.button(text="🎬 Сейчас в кино", callback_data="tcin")
    builder.button(text="🏠 В Главное меню", callback_data="main_menu")

    builder.adjust(2, 1, 1)

    return builder
