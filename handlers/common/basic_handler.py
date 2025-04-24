from aiogram import types
from core.admin import is_admin

async def handle_in_development(callback: types.CallbackQuery):
    """Обработчик для разделов в разработке"""
    if not is_admin(callback.from_user.id):
        await callback.answer("🚧 Раздел в разработке", show_alert=True)
        return  # Останавливаем обработку для не-админов
    
    # Для админов отвечаем на колбэк без сообщения и продолжаем обработку
    await callback.answer()
