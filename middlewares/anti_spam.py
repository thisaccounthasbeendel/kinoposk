from typing import Dict
import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from core import setup_logger
from services.redis_service import RedisService

logger = setup_logger()

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 110, timeout: int = 3):
        super().__init__()
        self.limit = limit
        self.timeout = timeout

    async def __call__(self, handler, event, data):
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            current_time = asyncio.get_event_loop().time()
            redis_service = RedisService.get_instance()  # Используем существующий инстанс
            
            # Получаем текущие временные метки
            timestamps = await redis_service.get_user_spam_timestamps(user_id)
            
            # Фильтруем устаревшие временные метки
            timestamps = [t for t in timestamps if current_time - t < self.timeout]
            timestamps.append(current_time)
            
            # Сохраняем обновленные данные
            await redis_service.update_spam_timestamps(user_id, timestamps, self.timeout)
            
            if len(timestamps) > self.limit:
                logger.info(f"🤡 Пользователь с ID {user_id} заблокирован за спам. Игнорируем клоуна {self.timeout} секунд(ы).")
                return
                
        return await handler(event, data)
