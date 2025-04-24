from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, types
from core.admin import is_admin

class AdminAccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: types.CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, является ли callback_data одним из защищенных разделов
        if event.data in {
            "categories"
        }:
            if not is_admin(event.from_user.id):
                # Для не-админов просто показываем сообщение
                await event.answer(
                    "🚧 Раздел в разработке\nДоступно только администрации!",
                    show_alert=True
                )
                return
            
        # Для админов и всех остальных колбэков продолжаем обработку
        return await handler(event, data)
