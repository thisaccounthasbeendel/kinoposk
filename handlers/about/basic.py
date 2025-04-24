from aiogram import Router, F, types
from keyboards import get_about_menu
from keyboards.main import get_main_menu
from constants import ABOUT_MESSAGE, WELCOME_MESSAGE
from services.redis_service import RedisService
import logging

router = Router()

@router.callback_query(F.data == "show_about")
async def show_about(callback: types.CallbackQuery):
    """Показывает меню О боте"""
    message = await callback.message.edit_text(
        ABOUT_MESSAGE,
        reply_markup=get_about_menu().as_markup(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    # Сохраняем message_id сообщения "О боте" в Redis
    redis_service = RedisService.get_instance()
    await redis_service.save_about_message_id(callback.from_user.id, message.message_id)
    logging.info(f"[ABOUT] Saved about message_id {message.message_id} for user {callback.from_user.id}")

async def back_to_main_from_about(callback: types.CallbackQuery):
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu().as_markup(),
        parse_mode="HTML"
    )

def register_about_handlers(router: Router):
    router.callback_query.register(show_about, F.data == "about")
    router.callback_query.register(back_to_main_from_about, F.data == "main_menu")
