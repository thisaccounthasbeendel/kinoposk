from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.advanced_search import get_advanced_search_keyboard
from keyboards.main import get_main_menu
from keyboards.pagination import get_pagination_keyboard
from keyboards.search import get_cancel_keyboard_adv
from services.redis_service import RedisService
from services.kinopoisk_api import kinopoisk_api
from constants import WELCOME_MESSAGE, ADV_SEARCH_RESULTS_TEMPLATE
from handlers.search.basic import FILMS_PER_PAGE  # Оставляем только эту константу
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.validators import TextValidator
from aiogram.filters.callback_data import CallbackData
import logging
import json
import hashlib

router = Router()

class AdvancedSearchStates(StatesGroup):
    waiting_for_query = State()

class AdvancedSearchCallbackFactory(CallbackData, prefix="adv_search"):
    action: str

async def show_advanced_search(callback: types.CallbackQuery):
    """Показывает меню расширенного поиска"""
    try:
        # Получаем Redis сервис
        redis_service = RedisService.get_instance()
        
        # Получаем или инициализируем пустые фильтры
        filters, _ = await redis_service.get_search_filters(callback.from_user.id) or {}
        
        # Редактируем текущее сообщение
        edited_msg = await callback.message.edit_text(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        # Важно: сохраняем message_id первого сообщения
        await redis_service.save_search_filters(
            callback.from_user.id,
            filters or {},  # если фильтры None, используем пустой словарь
            edited_msg.message_id
        )
        
        await callback.answer()
            
    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error showing menu: {e}")
        await callback.answer("Произошла ошибка при открытии расширенного поиска")

async def show_genres(callback: types.CallbackQuery):
    """Показывает список жанров через инлайн режим"""
    # Сразу открываем инлайн режим в текущем чате
    await callback.message.delete()  # Удаляем текущее сообщение с меню
    await callback.answer()
    
    # Создаем новое сообщение с клавиатурой, которая сразу активирует инлайн режим
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎭 Выбрать жанр",
        switch_inline_query_current_chat="#фильтр_жанр "  # Пробел в конце важен
    )
    builder.button(text="↩️ Назад", callback_data="advanced_search")
    builder.adjust(1)
    
    await callback.message.answer(
        "🎭 <b>Выберите жанр из списка:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

async def process_genre_selection(callback: types.CallbackQuery):
    """Обрабатывает выбор жанра"""
    try:
        genre_code = callback.data.split('_')[1]
        user_id = callback.from_user.id
        
        # Получаем текущие фильтры и message_id
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        # Добавляем выбранный жанр
        filters['genre'] = genre_code
        
        # Удаляем старое сообщение с клавиатурой
        if keyboard_message_id:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=keyboard_message_id
                )
            except Exception as e:
                logging.error(f"Error deleting keyboard message: {e}")
        
        # Отправляем новое сообщение с клавиатурой
        new_msg = await callback.message.answer(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        # Сохраняем обновленные фильтры и новый message_id
        await redis_service.save_search_filters(user_id, filters, new_msg.message_id)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error processing genre selection: {e}")
        await callback.answer("Произошла ошибка при выборе жанра")

async def process_rating_selection(callback: types.CallbackQuery):
    """Обрабатывает выбор рейтинга"""
    try:
        rating_id = callback.data.split('_')[1]
        user_id = callback.from_user.id
        
        # Получаем текущие фильтры и message_id
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        # Удаляем старое сообщение с клавиатурой если есть
        if keyboard_message_id:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=keyboard_message_id
                )
            except Exception as e:
                logging.error(f"Error deleting old keyboard message: {e}")
        
        # Сохраняем выбранный рейтинг
        filters['rating'] = rating_id
        
        # Отправляем новое сообщение с клавиатурой
        new_msg = await callback.message.answer(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        # Сохраняем обновленные фильтры и новый message_id
        await redis_service.save_search_filters(user_id, filters, new_msg.message_id)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"[RATING] Error processing rating selection: {e}")
        await callback.answer("Произошла ошибка при выборе рейтинга")

async def process_sort_selection(callback: types.CallbackQuery):
    """Обрабатывает выбор сортировки"""
    try:
        sort_key = callback.data.split('_')[1]
        user_id = callback.from_user.id
        
        # Получаем текущие фильтры и message_id
        redis_service = RedisService.get_instance()
        filters, keyboard_message_id = await redis_service.get_search_filters(user_id)
        
        # Удаляем старое сообщение с клавиатурой если есть
        if keyboard_message_id:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=keyboard_message_id
                )
            except Exception as e:
                logging.error(f"Error deleting old keyboard message: {e}")
        
        # Сохраняем выбранную сортировку
        filters['sort_by'] = sort_key
        
        # Отправляем новое сообщение с клавиатурой
        new_msg = await callback.message.answer(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        # Сохраняем обновленные фильтры и новый message_id
        await redis_service.save_search_filters(user_id, filters, new_msg.message_id)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"[SORT] Error processing sort selection: {e}")
        await callback.answer("Произошла ошибка при выборе сортировки")

async def reset_filters(callback: types.CallbackQuery):
    """Сбрасывает все фильтры"""
    logging.info(f"[ADVANCED SEARCH] Resetting filters for user {callback.from_user.id}")
    
    try:
        # Удаляем старое сообщение
        await callback.message.delete()
        
        # Отправляем новое с пустыми фильтрами
        new_msg = await callback.message.answer(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard({}).as_markup(),
            parse_mode="HTML"
        )
        
        # Сохраняем пустые фильтры и новый message_id
        redis_service = RedisService.get_instance()
        await redis_service.save_search_filters(
            callback.from_user.id, 
            {},  # пустые фильтры
            new_msg.message_id  # важно: сохраняем ID нового сообщения
        )
        
        await callback.answer("Фильтры сброшены")
        
    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error resetting filters: {e}")

async def get_user_filters(user_id: int) -> dict:
    """Получает сохраненные фильтры пользователя"""
    redis_service = RedisService.get_instance()
    filters_json = await redis_service.get(f"searchFilters:{user_id}")
    return json.loads(filters_json) if filters_json else {}

async def save_user_filters(user_id: int, filters: dict):
    """Сохраняет фильтры пользователя"""
    redis_service = RedisService.get_instance()
    await redis_service.set(
        f"searchFilters:{user_id}",
        json.dumps(filters),
        ex=3600  # Храним 1 час
    )

async def show_countries(callback: types.CallbackQuery, state: FSMContext):
    """Показывает список стран через инлайн режим"""
    # Удаляем текущее сообщение
    await callback.message.delete()
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🌍 Выбрать страну",
        switch_inline_query_current_chat="#фильтр_страна "
    )
    builder.button(text="↩️ Назад", callback_data="advanced_search")
    builder.adjust(1)
    
    # Отправляем новое сообщение
    await callback.message.answer(
        "🌍 <b>Выберите страну из списка:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

async def back_to_main_menu(callback: types.CallbackQuery):
    """Возвращает пользователя в главное меню"""
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu().as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

# Добавляем обработчик отмены для расширенного поиска
@router.callback_query(F.data == "cancel_search_adv")
async def cancel_advanced_search(callback: types.CallbackQuery, state: FSMContext):
    """Отменяет расширенный поиск и возвращает в главное меню"""
    current_state = await state.get_state()
    
    # Проверяем, находимся ли мы в состоянии расширенного поиска
    if current_state != AdvancedSearchStates.waiting_for_query.state:
        await callback.answer("Это действие больше недоступно", show_alert=True)
        # Удаляем сообщение с кнопкой отмены
        try:
            await callback.message.delete()
        except Exception:
            pass  # Игнорируем ошибку, если сообщение уже удалено
        return

    # Очищаем состояние
    await state.clear()
    
    # Редактируем текущее сообщение, возвращая главное меню
    await callback.message.edit_text(
        text=WELCOME_MESSAGE,
        reply_markup=get_main_menu().as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "adv_search_start")
async def start_filtered_search(callback: types.CallbackQuery, state: FSMContext):
    """Начинает поиск с выбранными фильтрами"""
    user_id = callback.from_user.id
    
    # Получаем сохраненные фильтры
    redis_service = RedisService.get_instance()
    filters, _ = await redis_service.get_search_filters(user_id)
    
    logging.info(f"[ADVANCED SEARCH] Starting filtered search with filters: {json.dumps(filters, ensure_ascii=False)}")
    
    # Удаляем клавиатуру с фильтрами
    await callback.message.delete()
    
    # Отправляем новое сообщение с кнопкой отмены
    cancel_message = await callback.message.answer(
        "🔍 Введите название фильма для поиска:",
        reply_markup=get_cancel_keyboard_adv().as_markup()
    )
    
    # Сохраняем message_id для последующего удаления
    await state.set_data({'cancel_message': cancel_message})
    
    # Устанавливаем СВОЁ состояние
    await state.set_state(AdvancedSearchStates.waiting_for_query)
    await callback.answer()

# Обновляем регистрацию обработчиков
def register_advanced_search_handlers(router: Router):
    """Регистрирует обработчики расширенного поиска"""
    # Сначала регистрируем конкретные обработчики
    router.callback_query.register(show_advanced_search, F.data == "advanced_search")
    router.callback_query.register(reset_filters, F.data == "adv_reset")
    router.callback_query.register(show_genres, F.data == "adv_genre")
    router.callback_query.register(show_countries, F.data == "adv_country")
    router.callback_query.register(start_filtered_search, F.data == "adv_search_start")
    router.callback_query.register(search_by_filters_only, F.data == "adv_search_filters_only")  # Правильный callback_data
    router.callback_query.register(cancel_advanced_search, F.data == "cancel_search_adv")
    router.callback_query.register(back_to_main_menu, F.data == "main_menu")
    
    # Затем регистрируем обработчики с префиксами
    router.callback_query.register(process_genre_selection, lambda c: c.data.startswith("genre_"))
    router.callback_query.register(process_rating_selection, lambda c: c.data.startswith("rating_"))
    router.callback_query.register(process_sort_selection, lambda c: c.data.startswith("sort_"))
    
    # В конце регистрируем самый общий обработчик пагинации
    router.callback_query.register(
        handle_advanced_search_pagination,
        lambda c: c.data and c.data.startswith("adv_")  # Обрабатываем adv_{hash}_{page}
    )
    
    # Регистрируем обработчик сообщений
    router.message.register(process_advanced_search_query, AdvancedSearchStates.waiting_for_query)  # Используем СВОЁ состояние
    router.callback_query.register(return_to_filters, lambda c: c.data.startswith("back_to_filters_"))

# Добавляем обработчик сообщений для расширенного поиска
@router.message(AdvancedSearchStates.waiting_for_query)  # Используем СВОЁ состояние
async def process_advanced_search_query(message: types.Message, state: FSMContext):
    """Обрабатывает поисковый запрос с фильтрами"""
    try:
        query = message.text.strip()
        safe_query = TextValidator.sanitize_text(query)
        user_id = message.from_user.id
        
        # Получаем сообщение с кнопкой отмены для удаления
        state_data = await state.get_data()
        cancel_message = state_data.get('cancel_message')
        
        redis_service = RedisService.get_instance()
        filters, _ = await redis_service.get_search_filters(user_id)
        
        # Преобразуем фильтры в формат API
        api_filters = {}
        
        # Обработка жанра
        if 'genre' in filters:
            api_filters['genres'] = filters['genre']['id']
            
        # Обработка страны
        if 'country' in filters:
            api_filters['countries'] = filters['country']['id']
            
        # Обработка года
        if 'year' in filters:
            year_range = filters['year']['range'].split('-')
            api_filters['yearFrom'] = int(year_range[0])
            api_filters['yearTo'] = int(year_range[1] if len(year_range) > 1 else year_range[0])
            
        # Обработка рейтинга
        if 'rating' in filters:
            rating_range = filters['rating']['range'].split('-')
            api_filters['ratingFrom'] = float(rating_range[0])
            api_filters['ratingTo'] = float(rating_range[1] if len(rating_range) > 1 else 10)
            
        # Обработка сортировки
        if 'sort_by' in filters and filters['sort_by'] != 'none':
            api_filters['order'] = filters['sort_by']

        logging.info(f"[ADVANCED SEARCH] Prepared API filters: {api_filters}")

        search_id = generate_advanced_search_id(safe_query, user_id)
        search_data = {
            'query': safe_query,
            'filters': api_filters
        }
        await redis_service.store_query(f"adv_{search_id}", json.dumps(search_data))

        result = await kinopoisk_api.search_films(safe_query, 1, api_filters)
        
        if not result:
            await message.answer(
                "😕 Ничего не найдено. Попробуйте изменить параметры поиска.",
                reply_markup=get_main_menu().as_markup()
            )
            if cancel_message:
                await cancel_message.delete()
            await state.clear()
            return

        total_films = result.get('total', 0)
        films = result.get('items', [])[:FILMS_PER_PAGE]
        total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE

        keyboard = get_pagination_keyboard(f"adv_{search_id}", 1, total_pages, films)

        # Удаляем сообщение пользователя с запросом
        await message.delete()
        
        # Удаляем сообщение с кнопкой отмены
        if cancel_message:
            await cancel_message.delete()

        await message.answer(
            format_search_results(
                query=safe_query,
                filters=format_filters_for_display(filters),
                total_films=total_films,
                page=1,
                total_pages=total_pages
            ),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

        await state.clear()

    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error: {e}")
        await message.answer(
            "😕 Произошла ошибка при поиске. Попробуйте позже.",
            reply_markup=get_main_menu().as_markup()
        )
        if cancel_message:
            await cancel_message.delete()
        await state.clear()

def format_filters_for_display(filters: dict) -> str:
    """Форматирует фильтры для отображения в сообщении"""
    parts = []
    if 'genre' in filters:
        parts.append(f"🎭 Жанр: {filters['genre']['name']}")
    if 'country' in filters:
        parts.append(f"🌍 Страна: {filters['country']['name']}")
    if 'year' in filters:
        parts.append(f"📅 Год: {filters['year']['range']}")
    if 'sort_by' in filters and filters['sort_by'] != 'none':
        sort_names = {
            'RATING': 'По рейтингу ⭐',
            'NUM_VOTE': 'По популярности 👥',
            'YEAR': 'По году 📅'
        }
        parts.append(f"📊 Сортировка: {sort_names.get(filters['sort_by'], filters['sort_by'])}")
    
    return "\n".join(parts) if parts else "без фильтров"

def format_search_results(query: str, filters: str, total_films: int, page: int, total_pages: int) -> str:
    """Форматирует результаты поиска для отображения в сообщении"""
    return ADV_SEARCH_RESULTS_TEMPLATE.format(
        query=query,
        filters=filters,
        total_films=total_films,
        page=page,
        total_pages=total_pages
    )

@router.callback_query(lambda c: c.data.startswith('adv_'))
async def handle_advanced_search_pagination(callback: types.CallbackQuery):
    try:
        parts = callback.data.split('_')
        if len(parts) != 4:
            raise ValueError(f"Invalid callback data format: {callback.data}")
            
        search_hash = parts[1]
        page = int(parts[3])
        
        redis_service = RedisService.get_instance()
        search_data_json = await redis_service.get_query(f"adv_{search_hash}")
        if not search_data_json:
            await callback.answer("Произошла ошибка при поиске")
            return
            
        search_data = json.loads(search_data_json)
        query = search_data['query']
        api_filters = search_data['filters']
        
        # Используем логику из базового поиска
        api_page = (page - 1) // 2 + 1
        result = await kinopoisk_api.search_films(query, api_page, api_filters)
        
        if not result:
            await callback.answer("Ничего не найдено")
            return
            
        total_films = result.get('total', 0)
        total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE
        
        # Получаем список фильмов и выбираем нужную половину
        films = result.get('items', [])
        start_idx = ((page - 1) % 2) * FILMS_PER_PAGE
        films = films[start_idx:start_idx + FILMS_PER_PAGE]
        
        keyboard = get_pagination_keyboard(f"adv_{search_hash}", page, total_pages, films)
        
        filters, _ = await redis_service.get_search_filters(callback.from_user.id)
        filters_display = format_filters_for_display(filters)
        
        await callback.message.edit_text(
            text=format_search_results(
                query=query,
                filters=filters_display,
                total_films=total_films,
                page=page,
                total_pages=total_pages
            ),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error in pagination: {e}")
        await callback.answer("Произошла ошибка при поиске")

async def process_advanced_search_pagination(callback: types.CallbackQuery, search_hash: str, page: int):
    """Обрабатывает пагинацию в результатах расширенного поиска"""
    redis_service = RedisService.get_instance()
    try:
        search_data_json = await redis_service.get_query(f"adv_{search_hash}")
        if not search_data_json:
            logging.error(f"[ADVANCED SEARCH] Failed to get search data from Redis for hash: {search_hash}")
            await callback.answer("Произошла ошибка при поиске")
            return
            
        search_data = json.loads(search_data_json)
        original_query = search_data['query']
        filters = search_data['filters']
            
        # Вычисляем правильную страницу для API
        api_page = (page - 1) // 2 + 1
        result = await kinopoisk_api.search_films(original_query, api_page, filters)
        
        if not result:
            await callback.answer("Произошла ошибка при поиске")
            return

        total_films = result.get('total', 0)
        films = result.get('items', [])
        
        # Вычисляем правильный срез для текущей страницы
        start_idx = ((page - 1) % 2) * FILMS_PER_PAGE
        films = films[start_idx:start_idx + FILMS_PER_PAGE]
        
        total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE

        keyboard = get_pagination_keyboard(f"adv_{search_hash}", page, total_pages, films)

        # Проверяем, является ли это возвратом из карточки фильма
        if callback.data.startswith('btr_'):
            await callback.message.delete()
            await callback.message.answer(
                text=format_search_results(
                    query=original_query,
                    filters=format_filters_for_display(filters),
                    total_films=total_films,
                    page=page,
                    total_pages=total_pages
                ),
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text=format_search_results(
                    query=original_query,
                    filters=format_filters_for_display(filters),
                    total_films=total_films,
                    page=page,
                    total_pages=total_pages
                ),
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error in pagination: {e}")
        await callback.answer("Произошла ошибка при поиске")

# Регистрируем обработчик
router.callback_query.register(start_filtered_search, F.data == "adv_search_start")

def generate_advanced_search_id(query: str, user_id: int) -> str:
    """
    Генерирует уникальный хеш для расширенного поиска, включая и запрос и ID пользователя,
    чтобы потом можно было достать его фильтры из Redis
    """
    combined = f"{query}:{user_id}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

@router.callback_query(lambda c: c.data.startswith("back_to_filters_"))
async def return_to_filters(callback: types.CallbackQuery):
    """Возвращает пользователя к настройке фильтров"""
    try:
        user_id = callback.from_user.id
        redis_service = RedisService.get_instance()
        filters, _ = await redis_service.get_search_filters(user_id)
        
        # Редактируем текущее сообщение с новой клавиатурой
        edited_msg = await callback.message.edit_text(
            "🔎 <b>Расширенный поиск</b>\n\n"
            "Выберите параметры для поиска:",
            reply_markup=get_advanced_search_keyboard(filters).as_markup(),
            parse_mode="HTML"
        )
        
        # Сохраняем message_id нового сообщения с клавиатурой
        await redis_service.save_search_filters(
            user_id,
            filters,
            edited_msg.message_id
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error returning to filters: {e}")
        await callback.answer("Произошла ошибка при возврате к фильтрам")

@router.callback_query(F.data == "adv_search_filters_only")
async def search_by_filters_only(callback: types.CallbackQuery):
    """Выполняет поиск только по фильтрам без ключевого слова"""
    try:
        user_id = callback.from_user.id
        
        # Получаем сохраненные фильтры
        redis_service = RedisService.get_instance()
        filters, _ = await redis_service.get_search_filters(user_id)
        
        logging.info(f"[ADVANCED SEARCH] Starting filters-only search with filters: {json.dumps(filters, ensure_ascii=False)}")
        
        # Удаляем клавиатуру с фильтрами
        await callback.message.delete()
        
        # Сразу делаем поиск с пустым query
        result = await kinopoisk_api.search_films("", 1, filters)
        
        if not result:
            await callback.message.answer(
                "😕 Ничего не найдено. Попробуйте изменить параметры поиска.",
                reply_markup=get_main_menu().as_markup()
            )
            return

        total_films = result.get('total', 0)
        films = result.get('items', [])[:FILMS_PER_PAGE]
        total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE

        # Генерируем search_id и сохраняем данные поиска
        search_id = generate_advanced_search_id("", user_id)
        await redis_service.store_query(
            f"adv_{search_id}",
            json.dumps({
                'query': "",
                'filters': filters
            })
        )

        keyboard = get_pagination_keyboard(f"adv_{search_id}", 1, total_pages, films)
        
        await callback.message.answer(
            format_search_results(
                query="",
                filters=format_filters_for_display(filters),
                total_films=total_films,
                page=1,
                total_pages=total_pages
            ),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

    except Exception as e:
        logging.error(f"[ADVANCED SEARCH] Error in filters-only search: {e}")
        await callback.message.answer(
            "Произошла ошибка при поиске. Попробуйте позже.",
            reply_markup=get_main_menu().as_markup()
        )
