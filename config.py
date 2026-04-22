# Завантаження та валідація

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    WEBHOOK_SECRET: str
    DATABASE_URL: str
    REDIS_URL: str
    RENDER_EXTERNAL_URL: str
    CRON_SECRET_TOKEN: str
    GROUP_CHAT_ID: int
    SUPER_ADMIN_IDS: List[int]
    TIMEZONE: str = "Europe/Kyiv"
    SENTRY_DSN: str = ""

    @property
    def super_admin_ids_set(self) -> set[int]:
        return set(self.SUPER_ADMIN_IDS)

settings = Settings()