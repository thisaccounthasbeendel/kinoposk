from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.kinopoisk_api import kinopoisk_api
from services.redis_service import RedisService
from keyboards.pagination import get_pagination_keyboard, get_short_hash
from keyboards.search import get_cancel_keyboard
from keyboards.main import get_main_menu
from constants import WELCOME_MESSAGE, BASIC_SEARCH_RESULTS_TEMPLATE
import logging
import json  # Добавляем импорт json
from utils.validators import TextValidator

# Create router instance
router = Router()

# Количество фильмов на странице
FILMS_PER_PAGE = 10

class SearchStates(StatesGroup):
    waiting_for_query = State()

async def start_search(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс поиска"""
    cancel_message = await callback.message.edit_text(
        "🔍 Введите название фильма для поиска:",
        reply_markup=get_cancel_keyboard().as_markup()
    )
    await state.set_data({'cancel_message': cancel_message})
    await state.set_state(SearchStates.waiting_for_query)
    await callback.answer()

async def process_search_query(message: types.Message, state: FSMContext):
    """Обрабатывает поисковый запрос"""
    current_state = await state.get_state()
    logging.info(f"[DEBUG] Current state in basic search: {current_state}")
    
    query = message.text.strip()
    
    # Очистка текста
    safe_query = TextValidator.sanitize_text(query)
    
    # Получаем сохраненное сообщение с кнопкой отмены
    state_data = await state.get_data()
    cancel_message = state_data.get('cancel_message')
    
    # Получаем результаты поиска (первая страница API)
    result = await kinopoisk_api.search_films(safe_query, 1)
    if not result:
        await message.answer(
            "😕 Произошла ошибка при поиске. Попробуйте позже.",
            reply_markup=get_main_menu().as_markup()
        )
        # Удаляем сообщение с кнопкой отмены
        if cancel_message:
            await cancel_message.delete()
        await state.clear()
        return

    total_films = result.get('total', 0)
    if total_films == 0:
        await message.answer(
            "😕 По вашему запросу ничего не найдено.",
            reply_markup=get_main_menu().as_markup()
        )
        # Удаляем сообщение с кнопкой отмены
        if cancel_message:
            await cancel_message.delete()
        await state.clear()
        return

    films = result.get('items', [])[:FILMS_PER_PAGE]
    total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE

    # Генерируем query_id и сохраняем в Redis
    query_id = get_short_hash(safe_query)
    logging.info(f"[SEARCH] Generated query_id: {query_id} for search query: {safe_query}")
    
    redis_service = RedisService.get_instance()
    if not await redis_service.store_query(query_id, safe_query):
        logging.error(f"[SEARCH] Failed to store search query in Redis. query_id: {query_id}, query: {safe_query}")
        await message.answer(
            "😕 Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu().as_markup()
        )
        await state.clear()
        return

    # Используем query_id в callback_data
    keyboard = get_pagination_keyboard(f"s_{query_id}", 1, total_pages, films)

    message_text = BASIC_SEARCH_RESULTS_TEMPLATE.format(
        query=safe_query,
        page=1,
        total_pages=total_pages,
        total_films=total_films
    )

    try:
        # Удаляем сообщение пользователя с запросом
        await message.delete()
        
        # Удаляем сообщение с кнопкой отмены
        if cancel_message:
            await cancel_message.delete()
            
        await message.answer(
            text=message_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"[SEARCH] Error sending message: {e}")
        await message.answer(
            "😕 Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu().as_markup()
        )

    await state.clear()

@router.callback_query(lambda c: c.data.startswith('s_'))
async def handle_search_pagination(callback: types.CallbackQuery):
    """Обработчик пагинации в поиске"""
    try:
        data = callback.data
        logging.info(f"Received callback_data: {data}")
        
        parts = data.split('_')
        if len(parts) >= 4:  # формат: ['s', 'b4a5d', 'page', '2']
            search_hash = parts[1]  # берем хеш
            page = int(parts[-1])   # берем последнее число как страницу
            await process_search_pagination(callback, search_hash, page)
        else:
            raise ValueError(f"Invalid s_ format: {parts}")
            
    except Exception as e:
        logging.error(f"Error in handle_search_pagination: {e}")
        await callback.answer("Произошла ошибка при переключении страницы")

async def process_search_pagination(callback: types.CallbackQuery, search_hash: str, page: int):
    """Обрабатывает пагинацию в результатах поиска"""
    redis_service = RedisService.get_instance()
    try:
        # Получаем оригинальный поисковый запрос из Redis по query_id
        original_query = await redis_service.get_query(search_hash)
        if not original_query:
            logging.error(f"[SEARCH] Failed to get query from Redis for query_id: {search_hash}")
            await callback.answer("Произошла ошибка при поиске")
            return
            
        # Используем оригинальный запрос для API
        api_page = (page - 1) // 2 + 1
        result = await kinopoisk_api.search_films(original_query, api_page)
        
        if not result:
            await callback.answer("Произошла ошибка при поиске")
            return
            
        total_films = result.get('total', 0)
        total_pages = (total_films + FILMS_PER_PAGE - 1) // FILMS_PER_PAGE
        
        # Получаем список фильмов и выбираем нужную половину
        films = result.get('items', [])
        start_idx = ((page - 1) % 2) * FILMS_PER_PAGE
        films = films[start_idx:start_idx + FILMS_PER_PAGE]
        
        # Формируем сообщение
        message_text = BASIC_SEARCH_RESULTS_TEMPLATE.format(
            query=original_query,
            page=page,
            total_pages=total_pages,
            total_films=total_films
        )
        
        # Создаем клавиатуру с пагинацией, используя query_id
        keyboard = get_pagination_keyboard(f"s_{search_hash}", page, total_pages, films)
        
        # Удаляем текущее сообщение (карточку фильма)
        await callback.message.delete()
        
        # Отправляем новое сообщение с результатами поиска
        await callback.message.answer(
            text=message_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"[SEARCH] Error in process_search_pagination: {e}")
        await callback.answer("Произошла ошибка при возврате к результатам")

async def cancel_search(callback: types.CallbackQuery, state: FSMContext):
    """Отменяет поиск и возвращает в главное меню"""
    current_state = await state.get_state()
    
    # Проверяем, находимся ли мы в состоянии поиска
    if current_state != SearchStates.waiting_for_query.state:
        await callback.answer("Это действие больше недоступно", show_alert=True)
        # Удаляем сообщение с просьбой ввести название фильма и кнопкой отмены
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

def register_search_handlers(router: Router):
    """Регистрирует обработчики для поиска"""
    router.callback_query.register(start_search, F.data == "search")
    router.message.register(process_search_query, SearchStates.waiting_for_query)
    router.callback_query.register(cancel_search, F.data == "cancel_search")
    
    # Добавляем обработчик для пагинации поиска
    router.callback_query.register(
        handle_search_pagination,
        lambda c: c.data and c.data.startswith("s_")  # Обрабатываем s_{hash}_{page}
    )
    
    # Добавляем обработчик для пагинации через номера страниц
    router.callback_query.register(
        handle_search_pagination,
        lambda c: c.data and "search_" in c.data and "_page_" in c.data  # Обрабатываем search_{hash}_page_{page}
    )
