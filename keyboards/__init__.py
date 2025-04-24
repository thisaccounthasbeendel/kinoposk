
from .main import get_main_menu
from .tops import get_tops_menu
from .about import get_about_menu
from .search import get_cancel_keyboard, get_cancel_keyboard_adv  # Добавляем импорт

__all__ = [
    'get_main_menu',
    'get_cancel_keyboard',
    'get_cancel_keyboard_adv',  # Добавляем в __all__
    'get_tops_menu',
    'get_about_menu',
]

