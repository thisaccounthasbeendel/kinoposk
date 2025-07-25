from typing import List
import logging
from core.config import Config

class KinopoiskApiKeyManager:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0

    @property
    def current_key(self) -> str:
        return self.api_keys[self.current_index]

    def next_key(self) -> str:
        self.current_index += 1
        if self.current_index >= len(self.api_keys):
            logging.warning(f"[KINOPOISK KEY MANAGER] Все API-ключи исчерпаны!")
            raise RuntimeError("All Kinopoisk API keys have reached their limit.")
        logging.info(f"[KINOPOISK KEY MANAGER] Переключение на следующий API-ключ: #{self.current_index+1} {self.api_keys[self.current_index]}")
        return self.api_keys[self.current_index]

    def reset(self):
        self.current_index = 0

    # Менеджер только перебирает ключи, запросы выполняются в KinopoiskAPI через aiohttp
