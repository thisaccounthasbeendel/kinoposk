import aiohttp
import logging
import json
import time
from typing import Optional, Tuple, Dict
from core import load_config
from services.kinopoisk_key_manager import KinopoiskApiKeyManager


config = load_config()
key_manager = KinopoiskApiKeyManager(config.KINOPOISK_API_KEYS)

class KinopoiskAPI:
    def __init__(self):
        self.base_url = "https://kinopoiskapiunofficial.tech/api/v2.2"
        self.key_manager = key_manager
        self.headers = {
            "X-API-KEY": self.key_manager.current_key,
            "Content-Type": "application/json"
        }
        self._filters_cache = None
        self._cache_timestamp = None
        self._cache_duration = 3600  # 1 час

        # Словарь соответствия жанров и их ID
        self.genre_ids = {
            "Любой": "none",  # Добавляем опцию "Любой"
            "Триллер": 1, "Драма": 2, "Криминал": 3, "Мелодрама": 4, 
            "Детектив": 5, "Фантастика": 6, "Приключения": 7, 
            "Биография": 8, "Фильм-нуар": 9, "Вестерн": 10, 
            "Боевик": 11, "Фэнтези": 12, "Комедия": 13, "Военный": 14,
            "История": 15, "Музыка": 16, "Ужасы": 17, "Мультфильм": 18,
            "Семейный": 19, "Мюзикл": 20, "Спорт": 21, "Документальный": 22,
            "Короткометражка": 23, "Аниме": 24, "Новости": 26,
            "Концерт": 27, "Для взрослых": 28, "Церемония": 29,
            "Реальное ТВ": 30, "Игра": 31, "Ток-шоу": 32, "Детский": 33
        }

        # Словарь диапазонов рейтингов
        self.rating_ranges = {
            "Любой": "none",  # Добавляем опцию "Любой"
            "До 4": "1",
            "4-6": "2",
            "6-7": "3",
            "7-8": "4", 
            "8-9": "5",
            "9+": "6"
        }

        # Словарь значений рейтингов для API
        self.rating_values = {
            "none": (0, 10),  # Значения для "Любой"
            "1": (0, 4),
            "2": (4, 6),
            "3": (6, 7),
            "4": (7, 8),
            "5": (8, 9),
            "6": (9, 10)
        }

        # Словарь стран и их ID
        self.country_ids = {
            "Любая": "none",  # Default option
            "США": 1,
            "Россия": 34,
            "СССР": 33,
            "Великобритания": 5,
            "Франция": 3,
            "Италия": 10,
            "Испания": 8,
            "Германия": 9,
            "Канада": 14,
            "Япония": 16,
            "Китай": 21,
            "Корея Южная": 49,
            "Австралия": 13,
            "Индия": 7,
            "Бразилия": 30,
            "Швеция": 6,
            "Дания": 17,
            "Норвегия": 22,
            "Ирландия": 19,
            "Нидерланды": 23,
            "Бельгия": 45,
            "Швейцария": 2,
            "Австрия": 27,
            "Польша": 4,
            "Чехия": 18,
            "Венгрия": 48,
            "Греция": 63,
            "Турция": 44,
            "Мексика": 15,
            "Аргентина": 24
        }

        # Словарь параметров сортировки
        self.sort_options = {
            "none": "По умолчанию ⚡",  # Добавляем опцию "По умолчанию"
            "RATING": "По рейтингу ⭐",
            "NUM_VOTE": "По популярности 🔥",
            "YEAR": "По году выхода 📅"
        }
        
    async def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Выполняет запрос к API с перебором ключей"""
        url = f"{self.base_url}/{endpoint}"
        logging.info(f"[KINOPOISK API] Sending request to API")
        logging.info(f"[KINOPOISK API] Request params: {json.dumps(params, ensure_ascii=False)}")
        for _ in range(len(self.key_manager.api_keys)):
            headers = {
                "X-API-KEY": self.key_manager.current_key,
                "Content-Type": "application/json"
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        status = response.status
                        response_text = await response.text()
                        logging.info(f"[KINOPOISK API] Response status: {status}")
                        if status == 200:
                            return await response.json()
                        elif status == 402:
                            logging.warning(f"[KINOPOISK API] API key limit reached: {self.key_manager.current_key}. Switching key...")
                            try:
                                self.key_manager.next_key()
                            except RuntimeError:
                                logging.error(f"[KINOPOISK API] All API keys exhausted.")
                                return None
                            continue
                        else:
                            logging.error(f"[KINOPOISK API] Error response: {response_text}")
                            return None
            except Exception as e:
                logging.error(f"[KINOPOISK API] Request error: {str(e)}")
                return None
        logging.error(f"[KINOPOISK API] No valid API keys left.")
        return None

    @staticmethod
    async def parse_search_query(query: str) -> Tuple[str, Optional[int], Optional[str]]:
        """Парсит строку запроса на название, год и жанр"""
        parts = [part.strip() for part in query.split(',')]
        
        title = parts[0] if parts else ""
        year = None
        genre = None
        
        if len(parts) > 1 and parts[1]:
            try:
                year = int(parts[1])
            except ValueError:
                pass
                
        if len(parts) > 2:
            genre = parts[2].lower()
        
        return title, year, genre

    async def search_films(self, query: str, page: int = 1, filters: dict = None) -> dict:
        """Поиск фильмов"""
        params = {
            'keyword': query,
            'page': page
        }
        
        if filters:
            logging.info(f"[KINOPOISK API] Raw filters received: {json.dumps(filters, ensure_ascii=False)}")
            
            if 'countries' in filters:
                country_id = filters['countries']
                # Добавляем в параметры только если это конкретная страна
                if country_id and country_id != 'none':
                    params['countries'] = country_id

            if 'genres' in filters:
                genre_id = filters['genres']
                # Добавляем в параметры только если это конкретный жанр
                if genre_id and genre_id != 'none':
                    params['genres'] = genre_id
            
            if 'yearFrom' in filters:
                params['yearFrom'] = filters['yearFrom']
            
            if 'yearTo' in filters:
                params['yearTo'] = filters['yearTo']
                
            # Добавляем параметры рейтинга
            if 'ratingFrom' in filters:
                params['ratingFrom'] = filters['ratingFrom']
                
            if 'ratingTo' in filters:
                params['ratingTo'] = filters['ratingTo']

            # Добавляем параметр сортировки
            if 'order' in filters:
                params['order'] = filters['order']
        
            logging.info(f"[KINOPOISK API] Prepared search params: {json.dumps(params, ensure_ascii=False)}")

        return await self._make_request("films", params)

    async def get_film_details(self, film_id: str) -> dict:
        """Получение детальной информации о фильме"""
        return await self._make_request(f"films/{film_id}")

    async def get_collection(self, collection_type: str = "TOP_250_MOVIES", page: int = 1) -> dict:
        """
        Получение коллекции фильмов
        
        :param collection_type: Тип коллекции (TOP_250_MOVIES, TOP_POPULAR_ALL и т.д.)
        :param page: Номер страницы
        :return: Словарь с результатами
        """
        params = {
            "type": collection_type,
            "page": page
        }
        return await self._make_request("films/collections", params)

    async def get_film_name(self, film_id: str) -> Optional[str]:
        """Получает название фильма (русское или английское) по ID"""
        film_details = await self.get_film_details(film_id)
        if not film_details:
            return None
            
        # Пробуем получить русское название, если нет - английское
        return film_details.get('nameRu') or film_details.get('nameEn')

    async def get_filters(self) -> dict:
        """Получает и кэширует фильтры (страны, жанры) из API"""
        current_time = time.time()
        
        # Возвращаем кэшированные данные, если они актуальны
        if (self._filters_cache and self._cache_timestamp and 
            current_time - self._cache_timestamp < self._cache_duration):
            return self._filters_cache

        response = await self._make_request("films/filters")
        if response:
            self._filters_cache = response
            self._cache_timestamp = current_time
            
        return self._filters_cache

    @property
    async def countries(self) -> list:
        """Возвращает список стран из API"""
        filters = await self.get_filters()
        return filters.get('countries', []) if filters else []

    @property
    async def genres(self) -> list:
        """Возвращает список жанров из API"""
        filters = await self.get_filters()
        return filters.get('genres', []) if filters else []

# Создаем единственный экземпляр класса для использования во всем приложении
kinopoisk_api = KinopoiskAPI()
