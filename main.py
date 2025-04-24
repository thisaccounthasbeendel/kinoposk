import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from core import load_config
from keyboards import get_main_menu
from core import setup_logger
from constants import WELCOME_MESSAGE
from handlers.about.router import setup_about_router
from handlers.common.router import setup_common_handlers, common_router
from handlers.tops.router import setup_tops_router
from handlers.search.router import setup_search_router
from handlers.inline.router import setup_inline_router  # Добавляем импорт inline роутера
from handlers.torrents.router import setup_torrent_router  # Добавляем импорт inline роутера
from services.redis_service import RedisService
import sys
from middlewares.admin_access import AdminAccessMiddleware
from middlewares.chat_type import ChatTypeMiddleware

logging = setup_logger()

async def start_bot():
    # Загрузка конфига
    config = load_config()
    
    # Инициализация Redis
    RedisService.initialize(config.redis)
    
    async with Bot(token=config.BOT_TOKEN) as bot:
        try:
            # Проверяем токен
            await bot.get_me()
        except Exception as e:
            logging.error(f"Token validation failed: {e}")
            return

        dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрируем мидлвари
        dp.callback_query.middleware(AdminAccessMiddleware())  # Админский доступ только для колбэков
        dp.inline_query.middleware(ChatTypeMiddleware())  # Добавляем новый middleware
        
        # Регистрируем хендлеры
        @dp.message(Command("start"))
        async def cmd_start(message: types.Message, state: FSMContext):
            # Очищаем любое текущее состояние при старте бота
            await state.clear()
            
            await message.answer(
                WELCOME_MESSAGE,
                reply_markup=get_main_menu().as_markup(),
                parse_mode="HTML"
            )

        # Регистрируем роутеры
        dp.include_router(setup_common_handlers(common_router))
        dp.include_router(setup_about_router())
        dp.include_router(setup_tops_router())
        dp.include_router(setup_search_router())
        dp.include_router(setup_inline_router())  # Добавляем inline роутер
        dp.include_router(setup_torrent_router())  # Добавляем inline роутер

        try:
            logging.info("Starting bot...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Polling error: {e}")

if __name__ == "__main__":
    asyncio.run(start_bot())
