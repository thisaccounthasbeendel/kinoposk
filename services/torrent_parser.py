import aiohttp
import logging
from typing import Optional, Union
from urllib.parse import quote, urljoin
from services.redis_service import RedisService
from services.kinopoisk_api import kinopoisk_api
import json
import re
import hashlib
import base64

class TorrentParser:
    def __init__(self):
        self.base_url = "https://jacred.xyz"
        self.api_version = "v1.0"
        
        # Настройки фильтрации
        self.filter_settings = {
            'sort_by_size': False,
            'sort_by_date': False,
            'min_seeders': 0,
            'selected_voice': None,
            'min_quality': None
        }
        
        # Словарь предпочтительных студий озвучки
        self.voice_priorities = {
            "HDRezka Studio": 10,
            "LostFilm": 9,
            "NewStudio": 8,
            "Red Head Sound": 8,
            "Кубик в Кубе": 7,
            "Пифагор": 6,
            "Дубляж": 5
        }
        
        # Приоритеты качества видео
        self.quality_priorities = {
            "1080": 3,
            "720": 2,
            "480": 1
        }

    def set_filter(self, **kwargs):
        """Устанавливает параметры фильтрации"""
        for key, value in kwargs.items():
            if key in self.filter_settings:
                self.filter_settings[key] = value

    async def _make_request(self, search_query: str) -> Optional[str]:
        """Выполняет запрос к API поиска"""
        url = f"{self.base_url}/api/{self.api_version}/torrents?search={search_query}&apikey=null&exact=true"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': f'{self.base_url}/'
        }

        try:
            logging.info(f"[JACRED PARSER] Making API request for: {search_query}")
            logging.debug(f"[JACRED PARSER] Full URL: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    logging.info(f"[JACRED PARSER] Response status: {response.status}")
                    response_text = await response.text()
                    
                    # Парсим JSON
                    response_data = json.loads(response_text)
                    if isinstance(response_data, list):
                        logging.info(f"[JACRED PARSER] Found {len(response_data)} torrents")
                    else:
                        logging.info("[JACRED PARSER] Response content: No results found")
                    
                    if response.status != 200:
                        logging.error(f"[JACRED PARSER] Request failed with status {response.status}")
                        return None
                    return response_text
        except Exception as e:
            logging.error(f"[JACRED PARSER] Request error: {str(e)}")
            return None

    async def _filter_results(self, results: list, is_series: bool = False) -> list:
        """Фильтрует и сортирует результаты поиска с учетом настроек фильтрации"""
        filtered = []
        
        for item in results:
            # Пропускаем торренты с недостаточным количеством сидов
            if item.get('sid', 0) < self.filter_settings['min_seeders']:
                continue

            score = 0
            
            # Определяем качество из поля quality
            quality = item.get('quality')
            if quality and str(quality) in self.quality_priorities:
                score += self.quality_priorities[str(quality)]
            
            # Проверяем соответствие минимальному качеству
            if (self.filter_settings['min_quality'] and 
                quality and 
                self.quality_priorities.get(str(quality), 0) < 
                self.quality_priorities.get(str(self.filter_settings['min_quality']), 0)):
                continue
            
            # Определяем озвучку из массива voices
            voices = item.get('voices', [])
            current_voice = None
            max_priority = -1
            
            for voice in voices:
                priority = self.voice_priorities.get(voice, 0)
                if priority > max_priority:
                    max_priority = priority
                    current_voice = voice
            
            if max_priority > 0:
                score += max_priority
            
            # Фильтруем по выбранной озвучке
            if (self.filter_settings['selected_voice'] and 
                self.filter_settings['selected_voice'] not in voices):
                continue
            
            # Для сериалов проверяем сезоны
            if is_series and not item.get('seasons'):
                continue

            # Обработка полного описания качества
            quality = item.get('quality')
            quality_full = item.get('quality_full', '')  # получаем полное описание если есть
            if not quality_full and 'title' in item:
                # Пытаемся извлечь информацию о качестве из названия
                quality_info = []
                title = item['title'].upper()
                
                # Проверяем наличие информации о качестве
                if quality:
                    quality_info.append(f"{quality}p")
                
                # Ищем информацию о кодеках (расширенный список)
                codecs = [
                    'HEVC', 'H265', 'H.265', 'X265', 'X.265',
                    'H264', 'H.264', 'X264', 'X.264',
                    'AVC', 'XVID', 'DIVX'
                ]
                for codec in codecs:
                    if codec in title:
                        quality_info.append(codec)
                        break  # берем только первый найденный кодек
                
                # Ищем HDR форматы
                hdr_formats = ['HDR', 'HDR10', 'HDR10+', 'DOLBY VISION', 'DV']
                for hdr in hdr_formats:
                    if hdr in title:
                        quality_info.append(hdr)
                        break  # берем только первый найденный HDR формат
                
                # Ищем информацию о битрейте
                if '10BIT' in title or '10-BIT' in title:
                    quality_info.append('10bit')
                elif '8BIT' in title or '8-BIT' in title:
                    quality_info.append('8bit')
                
                # Ищем дополнительную информацию о качестве
                if 'REMUX' in title:
                    quality_info.append('REMUX')
                elif 'BLURAY' in title or 'BLU-RAY' in title:
                    quality_info.append('BluRay')
                elif 'WEBDL' in title or 'WEB-DL' in title:
                    quality_info.append('WEB-DL')
                elif 'WEBRIP' in title:
                    quality_info.append('WEBRip')
                elif 'HDTV' in title:
                    quality_info.append('HDTV')
                
                quality_full = ' '.join(quality_info) if quality_info else f"{quality}p"
            
            # Добавляем дополнительную информацию
            item.update({
                'score': score,
                'voice': current_voice or 'Неизвестная',
                'quality': f"{quality}p" if quality else 'Неизвестное',
                'quality_full': quality_full,  # Добавляем полное описание качества
                'size_gb': item.get('size', 0) / (1024 * 1024 * 1024),
                'seeders': item.get('sid', 0)
            })
            
            filtered.append(item)
        
        # Применяем сортировку согласно настройкам
        if self.filter_settings['sort_by_size']:
            filtered.sort(key=lambda x: x['size_gb'], reverse=True)
        elif self.filter_settings['sort_by_date']:
            filtered.sort(key=lambda x: x.get('createTime', ''), reverse=True)
        else:
            filtered.sort(key=lambda x: (x['score'], x['seeders']), reverse=True)
        
        return filtered

    def decode_hash(self, hash_str: str) -> str:
        """Декодирует хеш в оригинальное название используя тот же алгоритм, что и в инлайн кнопках"""
        try:
            # Декодируем base64 и получаем оригинальное название
            decoded = base64.b64decode(hash_str + "=" * (-len(hash_str) % 4)).decode('utf-8')
            return decoded
        except Exception as e:
            logging.error(f"[JACRED PARSER] Error decoding hash: {str(e)}")
            return None

    async def get_torrents(self, kinopoisk_id: str, is_series: bool = False) -> Optional[Union[str, list]]:
        """
        Поиск торрентов с применением фильтров
        Args:
            kinopoisk_id: str - идентификатор фильма/сериала в КиноПоиске
            is_series: bool - является ли контент сериалом
        """
        try:
            # Получаем название фильма из КиноПоиска
            film_name = await kinopoisk_api.get_film_name(kinopoisk_id)
            if not film_name:
                logging.error(f"[JACRED PARSER] Failed to get film name for KinoPoisk ID: {kinopoisk_id}")
                return None
                
            logging.info(f"[JACRED PARSER] Searching torrent for film '{film_name}' (KinoPoisk ID: {kinopoisk_id})")
            
            # Делаем запрос к API jacred
            response_text = await self._make_request(film_name)
            if not response_text:
                return None
            
            results = json.loads(response_text)
            if not results or not isinstance(results, list):
                logging.warning("[JACRED PARSER] No results in API response")
                return None

            filtered_results = await self._filter_results(results, is_series)
            if not filtered_results:
                logging.warning("[JACRED PARSER] No results after filtering")
                return None

            return filtered_results

        except Exception as e:
            logging.error(f"[JACRED PARSER] Error in get_best_torrent: {str(e)}")
            return None

# Создаем глобальный экземпляр парсера
torrent_parser = TorrentParser()
