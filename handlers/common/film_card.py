from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.kinopoisk_api import kinopoisk_api
from services.torrent_parser import TorrentParser
from services.redis_service import RedisService  # Добавляем импорт
import logging

# Создаем роутер
router = Router()

MAX_DESCRIPTION_LENGTH = 700

async def show_film_card(callback: types.CallbackQuery):
    try:
        logging.info(f"[FILM CARD] Входящий callback_data: {callback.data}")
        parts = callback.data.split('_')
        logging.info(f"[FILM CARD] Split parts: {parts}")
        
        film_id = parts[1]
        
        # Сохраняем callback для возврата к результатам
        redis_service = RedisService.get_instance()
        
        # Определяем тип коллекции и страницу
        if len(parts) >= 4:  # Для поиска и расширенного поиска
            if parts[3] == 'adv':  # Если это расширенный поиск
                search_hash = parts[2]
                back_callback_data = f"btr_adv_{search_hash}_{parts[4]}"  # Добавляем префикс btr_
            elif parts[3] == 's':  # Если это обычный поиск
                search_hash = parts[2]
                back_callback_data = f"btr_s_{search_hash}_{parts[4]}"    # Добавляем префикс btr_
            else:  # Если это топ
                collection_type = parts[2]
                page = parts[3]
                back_callback_data = f"btr_{collection_type}_{page}"      # Добавляем префикс btr_
                
            # Сохраняем оба callback'а
            await redis_service.store_query(f"film_callback_{film_id}", callback.data)
            await redis_service.store_query(f"back_callback_{film_id}", back_callback_data)
        else:
            raise ValueError(f"Invalid callback_data format: {callback.data}")
        
        logging.info(f"[FILM CARD] Making back button with callback_data: {back_callback_data}")
        
        logging.info(f"[FILM CARD] Fetching film details for ID: {film_id}")
        film = await kinopoisk_api.get_film_details(film_id)
        
        if not film:
            logging.error(f"[FILM CARD] Failed to get film details for ID: {film_id}")
            await callback.answer("Не удалось получить информацию о фильме")
            return

        # Форматируем информацию о фильме
        name_ru = film.get('nameRu')
        name_en = film.get('nameEn')
        
        # Формируем название фильма
        film_name = ""
        if name_ru and name_en:
            film_name = f"🇷🇺 <b>{name_ru}</b>\n🇺🇸 {name_en}"
        elif name_ru:
            film_name = f"🇷🇺 <b>{name_ru}</b>"
        elif name_en:
            film_name = f"🇷🇺 <b>{name_en}</b>"
        else:
            film_name = "🇷🇺 <b>Название отсутствует</b>"

        # Обработка года выпуска
        year = film.get('year')
        year = str(year) if year else "Отсутствует"

        # Обработка рейтинга
        rating = film.get('ratingKinopoisk')
        rating = str(rating) if rating else "Отсутствует"

        # Обработка жанров - исправляем форматирование
        genres = film.get('genres', [])
        genres_str = ', '.join(g['genre'].capitalize() for g in genres) if genres else "Отсутствуют"

        # Обработка стран - исправляем форматирование
        countries = film.get('countries', [])
        countries_str = ', '.join(c['country'] for c in countries) if countries else "Отсутствуют"

        # Обработка описания
        description = film.get('description', 'Описание отсутствует')

        # Формируем базовую информацию
        base_info = (
            f"{film_name}\n\n"
            f"📅 Год: {year}\n"
            f"⭐ Рейтинг: {rating}\n"
            f"🎭 Жанры: {genres_str}\n"
            f"🌎 Страны: {countries_str}\n\n"
            f"📝 Описание:\n"
        )

        # Проверяем, что description не None перед обработкой
        if description:
            # Обрезаем описание с учетом оставшегося места
            available_length = MAX_DESCRIPTION_LENGTH - len(base_info)
            if len(description) > available_length:
                description = description[:available_length].rsplit(' ', 1)[0] + "..."
        else:
            description = "Описание отсутствует"

        caption = base_info + description

        # Обработка постера
        poster_url = film.get('posterUrl')
        if not poster_url:
            await callback.answer("Изображение фильма недоступно")
            return

        # Создаем клавиатуру для карточки фильма
        builder = InlineKeyboardBuilder()
        
        # Добавляем кнопку Назад
        builder.button(
            text="↩️ Назад к результатам",
            callback_data=back_callback_data
        )
        
        # Добавляем кнопку для просмотра торрентов
        builder.button(
            text="📥 Смотреть торренты",
            callback_data=f"tp_{film_id}_1"  # Страница 1
        )
        
        # Добавляем кнопку Кинопоиска
        kinopoisk_app_link = f"https://www.kinopoisk.ru/film/{film_id}/"
        builder.button(
            text="🎥 Открыть в Кинопоиске",
            url=kinopoisk_app_link
        )
        
        # Добавляем кнопку главного меню
        builder.button(
            text="🏠 В Главное меню",
            callback_data="main_menu"
        )
        
        builder.adjust(1, 2, 1)  # Расположение кнопок: 1-2-1

        # Отправляем сообщение
        try:
            await callback.message.answer_photo(
                photo=poster_url,
                caption=caption,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            await callback.message.delete()
        except Exception as e:
            logging.error(f"[FILM CARD] Error sending photo: {str(e)}, builder data: {builder.buttons}")
            await callback.answer("Произошла ошибка при показе фильма")

    except Exception as e:
        logging.error(f"[FILM CARD] Error in show_film_card: {str(e)}, callback_data: {callback.data}")
        await callback.answer("Произошла ошибка при показе фильма")

def register_handlers(router: Router) -> None:
    """Регистрирует обработчики для карточек фильмов"""
    # Регистрируем обработчики
    router.callback_query.register(
        show_film_card,
        F.data.startswith('f_')
    )

async def debug_callback(callback: types.CallbackQuery):
    logging.info(f"[FILM CARD] Debug: received callback with data: {callback.data}")
    await callback.answer()

def register_film_card_handlers(router: Router):
    """Регистрирует обработчики для карточек фильмов"""
    # Добавляем отладочный обработчик для всех callback
    router.callback_query.register(debug_callback)
    
    # Регистрируем основной обработчик
    router.callback_query.register(
        show_film_card,
        F.data.startswith('f_')
    )

# Экспортируем роутер и функцию регистрации
__all__ = ["router", "show_film_card", "register_handlers", "register_film_card_handlers"]
