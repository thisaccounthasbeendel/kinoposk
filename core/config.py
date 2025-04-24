from dataclasses import dataclass
from environs import Env

@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str | None = None

@dataclass
class Config:
    BOT_TOKEN: str
    KINOPOISK_API_KEY: str
    redis: RedisConfig

def load_config() -> Config:
    env = Env()
    env.read_env()
    
    # Добавим проверку на пустой токен
    bot_token = env("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN cannot be empty")
    
    # Конфигурация Redis
    redis_config = RedisConfig(
        host=env.str("REDIS_HOST", "localhost"),
        port=env.int("REDIS_PORT", 6379),
        db=env.int("REDIS_DB", 0),
        password=env.str("REDIS_PASSWORD", None)
    )
        
    return Config(
        BOT_TOKEN=bot_token,
        KINOPOISK_API_KEY=env("KINOPOISK_API_KEY"),
        redis=redis_config
    )
