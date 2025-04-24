from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import InlineQuery
import logging

class ChatTypeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[InlineQuery, Dict[str, Any]], Awaitable[Any]],
        event: InlineQuery,
        data: Dict[str, Any]
    ) -> Any:
        if event.chat_type and event.chat_type != "sender":
            logging.info(f"[SECURITY] Blocked inline query from {event.from_user.id} in {event.chat_type} chat")
            await event.answer(
                results=[],
                cache_time=60,
                is_personal=True,
                title="⚠️ Вы не в личных сообщениях с ботом"
            )
            return
        
        return await handler(event, data)
