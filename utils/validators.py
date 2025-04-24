import re
from typing import Optional, Tuple
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

class TextValidator:
    # Максимальная длина текста
    MAX_TEXT_LENGTH = 100
    
    # Минимальная длина текста для поиска
    MIN_SEARCH_LENGTH = 2
    
    # Регулярное выражение для проверки на специальные символы и инъекции
    SAFE_TEXT_PATTERN = re.compile(r'^[\w\s\-.,!?«»\'\"]+$', re.UNICODE)
    
    # Запрещенные слова или фразы
    FORBIDDEN_WORDS = [
        'drop', 'delete', 'update', 'insert',  # SQL инъекции
        '<script>', 'javascript:',  # XSS
        '/dev/null', '$(', '${',  # Command injection
    ]

    @staticmethod
    def get_main_menu_button() -> InlineKeyboardBuilder:
        """Создает клавиатуру с одной кнопкой возврата в главное меню"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Главное меню", callback_data="main_menu")
        return builder

    @classmethod
    def validate_search_query(cls, text: str) -> Tuple[bool, Optional[str], Optional[InlineKeyboardBuilder]]:
        """
        Валидация поискового запроса
        
        Args:
            text: Текст для проверки
            
        Returns:
            Tuple[bool, Optional[str], Optional[InlineKeyboardBuilder]]: 
            (успех валидации, сообщение об ошибке, клавиатура)
        """
        # Проверка на None или пустую строку
        if not text or not isinstance(text, str):
            return False, "Текст не может быть пустым", cls.get_main_menu_button()
            
        # Очистка от лишних пробелов
        text = text.strip()
        
        # Проверка минимальной длины
        if len(text) < cls.MIN_SEARCH_LENGTH:
            return False, f"Текст должен содержать минимум {cls.MIN_SEARCH_LENGTH} символа", cls.get_main_menu_button()
            
        # Проверка максимальной длины
        if len(text) > cls.MAX_TEXT_LENGTH:
            return False, f"Текст не должен превышать {cls.MAX_TEXT_LENGTH} символов", cls.get_main_menu_button()
            
        # Проверка на запрещенные слова
        for word in cls.FORBIDDEN_WORDS:
            if word.lower() in text.lower():
                return False, "Текст содержит запрещенные слова или выражения", cls.get_main_menu_button()
                
        # Проверка на специальные символы
        if not cls.SAFE_TEXT_PATTERN.match(text):
            return False, "Текст содержит недопустимые символы", cls.get_main_menu_button()
            
        return True, None, None

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Очистка текста от потенциально опасных элементов
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        # Удаление лишних пробелов
        text = ' '.join(text.split())
        
        # Экранирование специальных символов HTML
        text = (text
               .replace('&', '&amp;')
               .replace('<', '&lt;')
               .replace('>', '&gt;')
               .replace('"', '&quot;')
               .replace("'", '&#x27;'))
               
        return text

    @classmethod
    def is_valid_film_id(cls, film_id: str) -> bool:
        """
        Проверка валидности ID фильма
        
        Args:
            film_id: ID фильма
            
        Returns:
            bool: True если ID валидный
        """
        return bool(re.match(r'^\d+$', str(film_id)))
