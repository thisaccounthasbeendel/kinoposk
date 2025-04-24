# Версия бота
BOT_VERSION = "2.0.0.0"

# Сообщение приветствия
WELCOME_MESSAGE = (
    "👋 Привет! Я КиноПоиск Бот\n\n"
    "Я помогу вам найти информацию о фильмах, сериалах и мультфильмах. "
    "Используйте меню ниже для навигации:\n\n"
    "🔍 <b>Поиск фильма</b> - быстрый поиск по названию\n"
    "📂 <b>Категории</b> - поиск по жанрам\n"
    "🏆 <b>Топы</b> - популярные подборки\n"
    "🔎 <b>Расширенный поиск</b> - поиск с фильтрами\n"
)

# Сообщение "О боте"
ABOUT_MESSAGE = (
    "🤖 <b>КиноПоиск Бот</b>\n\n"
    "Помогу найти информацию о фильмах, сериалах и мультфильмах:\n"
    "• Поиск по названию\n"
    "• Рейтинги и оценки\n"
    "• Информация о съёмочной группе\n"
    "• Описание и трейлеры\n"
    "• Топы и подборки\n\n"
    "🔍 <b>Как пользоваться:</b>\n"
    "1. Используйте кнопку «Поиск фильма» для быстрого поиска\n"
    "2. «Расширенный поиск» поможет найти фильм по жанру, году и рейтингу\n"
    "3. В разделе «Топы» найдёте популярные подборки\n\n"
    '📊 <b>Источник данных:</b> <a href="https://kinopoiskapiunofficial.tech">Kinopoisk API Unofficial</a>\n'
    f"🔄 <b>Версия:</b> {BOT_VERSION}"
)

TOPS_RESULTS_TEMPLATE = (
    "🏆 <b>{collection_name}</b>\n\n"
    "❗️ Фильмы обозначены через эмодзи попкорна: 🍿, а сериалы через кинопроектор: 🎥\n\n"
    "📑 Страница {page} из {total_pages} (всего фильмов: {total_films})\n\n"
    "Выберите фильм для просмотра подробной информации:"
)

BASIC_SEARCH_RESULTS_TEMPLATE = (
    "🔍 Результаты поиска по запросу: <b>{query}</b>\n\n"
    "❗️ Фильмы обозначены через эмодзи попкорна: 🍿, а сериалы через кинопроектор: 🎥\n\n"
    "📑 Страница {page} из {total_pages} (всего найдено: {total_films})\n\n"
    "Выберите фильм для просмотра подробной информации:"
)

ADV_SEARCH_RESULTS_TEMPLATE = (
    "🔍 Результаты расширенного поиска по запросу: <b>{query}</b>\n\n"
    "❗️ Фильмы обозначены через эмодзи попкорна: 🍿, а сериалы через кинопроектор: 🎥\n\n"
    "📑 Примененные фильтры:\n{filters}\n\n"
    "📊 Статистика поиска:\n\n"
    "📚 Всего найдено: {total_films}\n"
    "📍 Страница {page} из {total_pages}"
)

ADVANCED_SEARCH_MENU_TEMPLATE = (
    "🔎 <b>Расширенный поиск</b>\n\n"
    "Выберите параметры для поиска:"
)

TORRENT_DETAILS_TEMPLATE = (
    "📥 <b>Информация о раздаче:</b>\n\n"
    "📝 Название: {title}\n"
    "🎬 Сезон: {season}\n"
    "🎧 Озвучка: {voice}\n"
    "🎥 Качество: {quality}\n"
    "💾 Размер: {size:.2f} GB\n"
    "👥 Раздают: {seeders}\n"
    "⭐ Приоритет (качество + озвучка): {score}"
)

TORRENT_LIST_TEMPLATE = (
    "🎬 <b>{film_name}</b>\n\n"
    "📥 <b>Доступные торренты</b>\n"
    "Страница {page} из {total_pages} (всего раздач: {total_torrents})"
)

TORRENT_DOWNLOAD_CAPTION = "📥 Торрент-файл: {torrent_name}"

def format_search_results(query: str, filters: str, total_films: int, page: int, total_pages: int) -> str:
    return ADV_SEARCH_RESULTS_TEMPLATE.format(
        query=query,
        filters=filters,
        total_films=total_films,
        page=page,
        total_pages=total_pages
    )
