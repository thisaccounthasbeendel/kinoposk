# Kinoposkbot
# Телеграм бот для поиска фильмов

Этот бот для Telegram позволяет пользователям искать фильмы через сервис Кинопоиск используя различные фильтры.
А так-же можно смотреть уже готовые подборки фильмов, например как Топ250 и другие коллекции.

<div align="center">
  <p>
    <a href="https://github.com/thisaccounthasbeendel">
      <img src="./src/githubImage.png" alt="KinoposkBot" />
    </a>
  </p>
  
  <div>
    <p>
      <a href="./gnu-gpl-v3.0.md">
        <img src="https://img.shields.io/badge/Лицензия-GPLV_3-green"/>
      </a>
      <a href="https://t.me/kinposkbot" target="_blank">
        <img src="https://img.shields.io/badge/Telegram-Channel-blue"/>
      </a>
    </p>
  </div>
</div>

## 🚀 Функции
- 🔍 Поиск фильма - быстрый поиск по названию
- 📂 Категории - поиск по жанрам( в разработке )
- 🏆 Топы - популярные подборки
- 🔎 Расширенный поиск - поиск с фильтрами

## 📦 Установка

### 1. Клонирование репозитория
```bash 
git clone https://github.com/thisaccounthasbeendel/kinoposkbot.git
cd kinoposkbot
```

### 2. Установка зависимостей
```bash
pip install -r req.txt
```

### 3. Конфигурация
Создайте файл `.env` в корне проекта и укажите в нем ваш токен бота:
```
BOT_TOKEN= Токен вашего бота
KINOPOISK_API_KEY=  Ключ для неоцифиального API кинопоиска
REDIS_HOST= Адрес по которому доступен ваш Redis
REDIS_PORT= Порт, на который отзывается Redis
REDIS_DB= Номер базы данных Redis
REDIS_PASSWORD= Паоль для автоирации в Redis(если не установлен - оставьте пустым)
```

### 4. Запуск бота
```bash
python main.py
```

## 📂 Структура проекта
```
kinopoisk-bot/
├── core/                     # Ядро приложения - конфигурация, логирование
├── handlers/                 # Обработчики команд и сообщений
│   ├── about/                # Обработчики раздела "О боте"
│   ├── common/               # Общие обработчики
│   ├── inline/               # Обработчики инлайн-режима
│   ├── search/               # Обработчики поиска
│   ├── tops/                 # Обработчики настроек
│   └── torrents/             # Обработчики торрентов(мелкая шалость)
├── keyboards/                # Клавиатуры
├── middlewares/              # Промежуточные обработчики для доступа, логирования, и др.
├── services/                 # Внешние сервисы (Kinopoisk, Redis, Jacred, и др.)
├── utils/                    # Вспомогательные утилиты
├── .gitignore                # Список игнорируемых Git файлов
├── constants.py              # Константы проекта
├── main.py                   # Точка входа в приложение
├── README.md                 # Документация проекта
└── req.txt                   # Зависимости проекта
```

## 🛠 Технологии

### Основные
- [Python 3.9+](https://www.python.org/) - язык программирования
- [aiogram 3.19.0](https://docs.aiogram.dev/) - асинхронный фреймворк для создания Telegram ботов
- [Redis 5.0+](https://redis.io/) - для кэширования и хранения данных

### API и интеграции
- [Kinopoisk API Unofficial](https://kinopoiskapiunofficial.tech/) - API для получения данных о фильмах
- [Telegram Bot API](https://core.telegram.org/bots/api) - API Telegram для ботов

### Зависимости
- aiohttp - для асинхронных HTTP запросов
- redis[hiredis] - клиент Redis с оптимизированным парсером
- environs - для работы с переменными окружения
- watchfiles - для автоперезагрузки в режиме разработки (dev.py)

### Особенности реализации
- Асинхронная архитектура
- FSM (Finite State Machine) для управления диалогами
- Кэширование запросов к API
- Система логирования
- Модульная структура

## 🤝 Вклад в проект
Если у вас есть идеи по улучшению бота:
1. Сделайте **fork** репозитория
2. Внесите изменения в своей ветке
3. Откройте **pull request**

## 📜 Лицензия
Этот проект распространяется под лицензией gnu-gpl-v3.0.

---

Если у вас есть вопросы или предложения, открывайте Issue или создавайте Pull Request! 😊

