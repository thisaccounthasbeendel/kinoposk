from typing import Set

# ID администраторов (как строки, так как из Telegram они приходят в виде строк)
ADMIN_IDS: Set[str] = {
    #"Тут ваш id",  # Главный админ
}

def is_admin(user_id: int | str) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return str(user_id) in ADMIN_IDS