from typing import Optional, Dict
from redis.asyncio import Redis
import logging
from core.config import RedisConfig
import json

class RedisService:
    _instance = None
    _redis = None

    @classmethod
    def initialize(cls, config: RedisConfig):
        """Инициализация Redis соединения"""
        if cls._redis is None:
            cls._redis = Redis(
                host=config.host,
                port=config.port,
                db=config.db,
                password=config.password,
                decode_responses=True
            )

    def __init__(self, redis: Redis):
        self.redis = redis
        self._prefix = "search:"
        self._search_filters_prefix = "searchFilters:"  # Префикс для фильтров поиска фильмов
        self._torrent_filters_prefix = "torrentFilters:"  # Префикс для фильтров торрентов
        self._spam_prefix = "spam:"  # Новый префикс для антиспама
        self._ttl = 3600  # 1 час

    @classmethod
    def get_instance(cls) -> 'RedisService':
        if cls._instance is None:
            if cls._redis is None:
                raise RuntimeError("Redis not initialized. Call RedisService.initialize() first")
            cls._instance = cls(cls._redis)
        return cls._instance

    async def save_search_filters(self, user_id: int, filters: Dict, message_id: int = None) -> bool:
        """
        Сохраняет фильтры поиска и message_id клавиатуры
        
        Args:
            user_id: ID пользователя
            filters: Словарь с фильтрами
            message_id: ID сообщения с клавиатурой
        """
        try:
            data = {
                'filters': filters,
                'keyboard_message_id': message_id
            }
            key = f"{self._search_filters_prefix}{user_id}"
            await self.redis.set(
                key,
                json.dumps(data),
                ex=self._ttl
            )
            return True
        except Exception as e:
            logging.error(f"Redis save search filters error: {e}")
            return False

    async def get_search_filters(self, user_id: int) -> tuple[Dict, Optional[int]]:
        """
        Получает сохраненные фильтры поиска и message_id клавиатуры
        
        Args:
            user_id: ID пользователя
        Returns:
            tuple: (filters_dict, keyboard_message_id)
        """
        try:
            key = f"{self._search_filters_prefix}{user_id}"
            data = await self.redis.get(key)
            if data:
                parsed = json.loads(data)
                return parsed.get('filters', {}), parsed.get('keyboard_message_id')
            return {}, None
        except Exception as e:
            logging.error(f"Redis get search filters error: {e}")
            return {}, None

    async def clear_search_filters(self, user_id: int) -> bool:
        """
        Очищает фильтры поиска фильмов пользователя
        
        Args:
            user_id: ID пользователя
        """
        try:
            key = f"{self._search_filters_prefix}{user_id}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logging.error(f"Redis clear search filters error: {e}")
            return False

    async def save_torrent_filters(self, user_id: int, filters: Dict) -> bool:
        """
        Сохраняет фильтры поиска торрентов пользователя в Redis
        
        Args:
            user_id: ID пользователя
            filters: Словарь с фильтрами (качество, озвучка, размер и т.д.)
        """
        try:
            key = f"{self._torrent_filters_prefix}{user_id}"
            await self.redis.set(
                key,
                json.dumps(filters),
                ex=self._ttl
            )
            return True
        except Exception as e:
            logging.error(f"Redis save torrent filters error: {e}")
            return False

    async def get_torrent_filters(self, user_id: int) -> Optional[Dict]:
        """
        Получает фильтры поиска торрентов пользователя из Redis
        
        Args:
            user_id: ID пользователя
        Returns:
            Dict с фильтрами или пустой словарь, если фильтры не найдены
        """
        try:
            key = f"{self._torrent_filters_prefix}{user_id}"
            data = await self.redis.get(key)
            return json.loads(data) if data else {}
        except Exception as e:
            logging.error(f"Redis get torrent filters error: {e}")
            return {}

    async def clear_torrent_filters(self, user_id: int) -> bool:
        """
        Очищает фильтры поиска торрентов пользователя
        
        Args:
            user_id: ID пользователя
        """
        try:
            key = f"{self._torrent_filters_prefix}{user_id}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logging.error(f"Redis clear torrent filters error: {e}")
            return False

    async def store_query(self, query_id: str, query: str) -> bool:
        """Сохраняет поисковый запрос"""
        try:
            key = f"{self._prefix}{query_id}"
            await self.redis.set(key, query, ex=self._ttl)
            return True
        except Exception as e:
            logging.error(f"Redis store query error: {e}")
            return False

    async def get_query(self, query_id: str) -> Optional[str]:
        """Получает поисковый запрос по ID"""
        try:
            key = f"{self._prefix}{query_id}"
            return await self.redis.get(key)
        except Exception as e:
            logging.error(f"Redis get query error: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Удаляет ключ из Redis"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logging.error(f"Redis delete error: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Получает значение по ключу из Redis"""
        try:
            value = await self.redis.get(key)
            return value if value else None
        except Exception as e:
            logging.error(f"Redis get error: {e}")
            return None

    async def get_user_spam_timestamps(self, user_id: int) -> list:
        """Получает временные метки сообщений пользователя"""
        try:
            key = f"{self._spam_prefix}{user_id}"
            data = await self.redis.get(key)
            return json.loads(data) if data else []
        except Exception as e:
            logging.error(f"Redis get spam timestamps error: {e}")
            return []

    async def update_spam_timestamps(self, user_id: int, timestamps: list, timeout: int) -> bool:
        """Обновляет временные метки сообщений пользователя"""
        try:
            key = f"{self._spam_prefix}{user_id}"
            await self.redis.set(
                key,
                json.dumps(timestamps),
                ex=timeout
            )
            return True
        except Exception as e:
            logging.error(f"Redis update spam timestamps error: {e}")
            return False

    async def save_about_message_id(self, user_id: int, message_id: int) -> bool:
        """Сохраняет ID сообщения для меню О боте"""
        try:
            key = f"about_message:{user_id}"
            await self.redis.set(key, str(message_id), ex=3600)  # TTL 1 час
            return True
        except Exception as e:
            logging.error(f"Redis save about message ID error: {e}")
            return False

    async def get_about_message_id(self, user_id: int) -> int:
        """Получает ID сообщения для меню О боте"""
        try:
            key = f"about_message:{user_id}"
            message_id = await self.redis.get(key)
            return int(message_id) if message_id else None
        except Exception as e:
            logging.error(f"Redis get about message ID error: {e}")
            return None

    async def delete_about_message_id(self, user_id: int) -> bool:
        """Удаляет ID сообщения для меню О боте"""
        try:
            key = f"about_message:{user_id}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logging.error(f"Redis delete about message ID error: {e}")
            return False

# Создаем заглушку для глобального экземпляра
redis_service = None
