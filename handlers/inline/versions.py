from aiogram import Router, F, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
from pathlib import Path
import logging
from services.redis_service import RedisService
from constants import ABOUT_MESSAGE
from keyboards import get_about_menu

router = Router()

def load_changelog():
    try:
        with open(Path("changelog.json"), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading changelog: {e}")
        return {"versions": []}

def get_version_keyboard() -> InlineKeyboardBuilder:
    """Создает клавиатуру для просмотра версии"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="show_about")
    return builder

@router.callback_query(F.data == "show_about")
async def back_to_about(callback: types.CallbackQuery):
    """Обработчик возврата в меню О боте"""
    try:
        message = await callback.message.edit_text(
            ABOUT_MESSAGE,
            reply_markup=get_about_menu().as_markup(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        # Сохраняем ID отредактированного сообщения
        redis_service = RedisService.get_instance()
        await redis_service.save_about_message_id(callback.from_user.id, message.message_id)
        logging.info(f"[VERSIONS] Updated about message_id {message.message_id} for user {callback.from_user.id}")
        
        await callback.answer()
    except Exception as e:
        logging.error(f"[VERSIONS] Error in back_to_about: {e}")
        await callback.answer("Произошла ошибка при возврате в меню")

@router.inline_query(F.query.startswith("#инфо_историяверсий"))
async def versions_inline_query(query: types.InlineQuery):
    logging.info(f"[VERSIONS] Processing inline query from user {query.from_user.id}")
    
    changelog = load_changelog()
    
    results = [
        InlineQueryResultArticle(
            id=f"version_{idx}",
            title=f"Версия {version['version']} от {version['date']}",
            description=version['changes'][0],  # Показываем первое изменение в описании
            input_message_content=InputTextMessageContent(
                message_text=f"update_{version['version']}_{version['date']}"
            )
        )
        for idx, version in enumerate(changelog['versions'])
    ]
    
    await query.answer(results, cache_time=300)

@router.message(F.text.startswith("update_"))
async def process_version_selection(message: types.Message):
    try:
        # Сначала удаляем сообщение с командой update_
        await message.delete()
        
        _, version, date = message.text.split('_', 2)
        user_id = message.from_user.id
        
        # Получаем message_id сообщения "О боте" из Redis
        redis_service = RedisService.get_instance()
        about_message_id = await redis_service.get_about_message_id(user_id)
        
        if about_message_id:
            try:
                # Удаляем сообщение "О боте"
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=about_message_id
                )
                logging.info(f"[VERSIONS] Deleted about message {about_message_id}")
                # Очищаем ID в Redis
                await redis_service.delete_about_message_id(user_id)
            except Exception as e:
                logging.error(f"[VERSIONS] Error deleting about message {about_message_id}: {e}")
        
        changelog = load_changelog()
        version_data = next(
            (v for v in changelog['versions'] if v['version'] == version),
            None
        )
        
        if not version_data:
            return
        
        changes_text = (
            f"📝 <b>История обновлений</b>\n\n"
            f"🆕 <b>Версия {version}</b> от {date}\n\n"
            f"{chr(10).join(version_data['changes'])}"
        )

        # Отправляем информацию о версии
        await message.answer(
            changes_text,
            reply_markup=get_version_keyboard().as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logging.error(f"[VERSIONS] Error handling version selection: {e}")
