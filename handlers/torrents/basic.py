from aiogram import Router, F, types
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.torrent_parser import TorrentParser
from services.kinopoisk_api import kinopoisk_api
from keyboards.torr_pagination import get_torrent_pagination_keyboard, get_torrent_details_keyboard
from services.redis_service import RedisService
from services.torrent_converter import torrent_converter
import logging
import re
from constants import (
    TORRENT_DETAILS_TEMPLATE,
    TORRENT_LIST_TEMPLATE,
    TORRENT_DOWNLOAD_CAPTION
)

router = Router()

TORRENTS_PER_PAGE = 5

async def process_torrent_pagination(callback: types.CallbackQuery):
    """Обрабатывает пагинацию в списке торрентов"""
    try:
        parts = callback.data.split('_')
        kinopoisk_id = parts[1]
        page = int(parts[2])
        
        # Получаем сохраненный callback для возврата к карточке фильма
        redis_service = RedisService.get_instance()
        film_callback = await redis_service.get_query(f"film_callback_{kinopoisk_id}")
        
        # Получаем информацию о типе контента
        film_info = await kinopoisk_api.get_film_details(kinopoisk_id)
        is_series = film_info.get('type', '').lower() == 'tv_series'
        
        # Получаем и фильтруем торренты
        parser = TorrentParser()
        parser.set_filter(min_seeders=1)
        results = await parser.get_torrents(kinopoisk_id, is_series=is_series)
        film_name = film_info.get('nameRu', 'Неизвестный фильм')
        
        if not results:
            await callback.answer("Торренты не найдены", show_alert=True)
            return
            
        # Фильтрация и пагинация торрентов
        total_torrents = len(results)
        total_pages = (total_torrents + TORRENTS_PER_PAGE - 1) // TORRENTS_PER_PAGE
        start_idx = (page - 1) * TORRENTS_PER_PAGE
        end_idx = start_idx + TORRENTS_PER_PAGE
        current_torrents = results[start_idx:end_idx]
        
        keyboard = get_torrent_pagination_keyboard(
            kinopoisk_id=kinopoisk_id,
            current_page=page,
            total_pages=total_pages,
            torrents=current_torrents,
            film_callback=film_callback
        )
        
        message_text = TORRENT_LIST_TEMPLATE.format(
            film_name=film_name,
            page=page,
            total_pages=total_pages,
            total_torrents=total_torrents
        )
        
        # Проверяем, есть ли текст в сообщении
        has_text = bool(callback.message.text)
        
        # Если в сообщении есть текст и это пагинация, редактируем
        if has_text and callback.data.startswith('tp_'):
            await callback.message.edit_text(
                text=message_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
        else:
            # Если нет текста или это не пагинация, удаляем и отправляем новое
            await callback.message.delete()
            await callback.message.answer(
                text=message_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
            
    except Exception as e:
        logging.error(f"[JACRED PAGINATION] Error in process_torrent_pagination: {e}")
        await callback.answer("Произошла ошибка при загрузке торрентов")

async def show_torrent_details(callback: types.CallbackQuery):
    """Показывает детальную информацию о торренте"""
    try:
        parts = callback.data.split('_')
        kinopoisk_id = parts[1]
        torrent_idx = int(parts[2])
        current_page = int(parts[3])  # Добавляем получение текущей страницы из callback_data
        
        # Получаем данные о торренте
        parser = TorrentParser()
        results = await parser.get_torrents(kinopoisk_id)
        torrent = results[torrent_idx]
        
        message_text = TORRENT_DETAILS_TEMPLATE.format(
            title=torrent['title'],
            season=torrent.get('season', 'Н/Д'),
            voice=torrent['voice'],
            quality=torrent['quality'],
            size=torrent['size_gb'],
            seeders=torrent.get('seeders', 0),
            score=torrent['score']
        )
        
        keyboard, magnet_hash = get_torrent_details_keyboard(
            kinopoisk_id=kinopoisk_id,
            magnet_link=torrent['magnet'],
            current_page=current_page
        )
        
        # Сохраняем магнет-ссылку в Redis
        redis_service = RedisService.get_instance()
        await redis_service.store_query(f"magnet_{magnet_hash}", torrent['magnet'])
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
            
    except Exception as e:
        logging.error(f"[JACRED PAGINATION] Error in show_torrent_details: {e}")
        await callback.answer("Произошла ошибка при загрузке деталей торрента")

@router.callback_query(lambda c: c.data.startswith('download_'))
async def handle_torrent_download(callback: types.CallbackQuery):
    """Обрабатывает скачивание торрент файла"""
    try:
        parts = callback.data.split('_')
        magnet_hash = parts[1]
        kinopoisk_id = parts[2]
        
        # Получаем магнет-ссылку из Redis
        redis_service = RedisService.get_instance()
        magnet_link = await redis_service.get_query(f"magnet_{magnet_hash}")
        
        if not magnet_link:
            await callback.answer("Ссылка устарела, вернитесь к поиску", show_alert=True)
            return
            
        # Конвертируем магнет в торрент файл
        result = await torrent_converter.convert_magnet(magnet_link)
        
        if result:
            torrent_name, torrent_path = result
            
            # Проверяем существование файла перед отправкой
            if not torrent_path.exists():
                logging.error(f"Torrent file not found before sending: {torrent_path}")
                await callback.answer("Ошибка при подготовке торрент-файла", show_alert=True)
                return
                
            logging.info(f"Sending torrent file: {torrent_path}")
            
            # Создаем клавиатуру с кнопкой возврата
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="↩️ Вернуться к раздаче",
                callback_data=f"back_to_torrent_{kinopoisk_id}_{magnet_hash}"
            ))

            builder.row(InlineKeyboardButton(
                text="🏠 В Главное меню",
                callback_data="main_menu"
            ))
            
            # Удаляем сообщение с информацией о раздаче
            await callback.message.delete()
            
            # Отправляем торрент-файл с кнопкой в caption
            await callback.message.answer_document(
                FSInputFile(torrent_path),
                caption=TORRENT_DOWNLOAD_CAPTION.format(torrent_name=torrent_name),
                reply_markup=builder.as_markup()
            )
            
            # Проверяем существование файла перед удалением
            if torrent_path.exists():
                logging.info(f"Cleaning up torrent file: {torrent_path}")
                torrent_converter.cleanup_file(torrent_path)
            else:
                logging.warning(f"Torrent file not found for cleanup: {torrent_path}")
                
        else:
            await callback.answer("Не удалось создать торрент файл", show_alert=True)
            
    except Exception as e:
        logging.error(f"[TORRENT DOWNLOAD] Error: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при скачивании торрента", show_alert=True)

@router.callback_query(lambda c: c.data.startswith('back_to_torrent_'))
async def handle_back_to_torrent(callback: types.CallbackQuery):
    """Возвращает к информации о раздаче"""
    try:
        parts = callback.data.split('_')
        kinopoisk_id = parts[3]
        magnet_hash = parts[4]
        
        # Получаем магнет-ссылку из Redis для идентификации торрента
        redis_service = RedisService.get_instance()
        magnet_link = await redis_service.get_query(f"magnet_{magnet_hash}")
        
        if not magnet_link:
            await callback.answer("Информация о раздаче устарела", show_alert=True)
            return
        
        # Получаем данные о торренте
        parser = TorrentParser()
        results = await parser.get_torrents(kinopoisk_id)
        
        # Ищем торрент по магнет-ссылке
        torrent = next((t for t in results if t['magnet'] == magnet_link), None)
        
        if not torrent:
            await callback.answer("Информация о раздаче не найдена", show_alert=True)
            return
        
        message_text = TORRENT_DETAILS_TEMPLATE.format(
            title=torrent['title'],
            season=torrent.get('season', 'Н/Д'),
            voice=torrent['voice'],
            quality=torrent['quality'],
            size=torrent['size_gb'],
            seeders=torrent.get('seeders', 0),
            score=torrent['score']
        )
        
        keyboard, _ = get_torrent_details_keyboard(
            kinopoisk_id=kinopoisk_id,
            magnet_link=magnet_link,
            current_page=1  # Возвращаемся на первую страницу
        )
        
        # Отправляем новое сообщение с информацией о раздаче
        await callback.message.answer(
            text=message_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
        
        # Удаляем сообщение с кнопкой возврата
        await callback.message.delete()
        
    except Exception as e:
        logging.error(f"[BACK TO TORRENT] Error: {e}")
        await callback.answer("Произошла ошибка при возврате к информации о раздаче")

def register_torrent_handlers(router: Router) -> None:
    """Регистрирует обработчики для торрентов"""
    router.callback_query.register(
        process_torrent_pagination,
        F.data.regexp(r'^tp_\d+_\d+$')  # tp_{kinopoisk_id}_{page}
    )
    router.callback_query.register(
        show_torrent_details,
        F.data.regexp(r'^td_\d+_\d+_\d+$')  # td_{kinopoisk_id}_{torrent_idx}_{page}
    )
    router.callback_query.register(
        handle_torrent_download,
        F.data.regexp(r'^download_[a-f0-9]+_\d+$')  # download_{magnet_hash}_{kinopoisk_id}
    )
    router.callback_query.register(
        handle_back_to_torrent,
        F.data.regexp(r'^back_to_torrent_\d+_[a-f0-9]+$')  # back_to_torrent_{kinopoisk_id}_{magnet_hash}
    )
