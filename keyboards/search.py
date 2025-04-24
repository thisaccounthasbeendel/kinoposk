
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_cancel_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_search")
    return builder

def get_cancel_keyboard_adv() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_search_adv")
    return builder

