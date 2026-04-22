# Завантаження та валідація

from typing import List
from pydantic import field_validator
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

    @field_validator("SUPER_ADMIN_IDS", mode="before")
    @classmethod
    def parse_super_admin_ids(cls, v):
        if isinstance(v, str):
            # "123,456" -> [123, 456]
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        elif isinstance(v, int):
            # 1730836640 -> [1730836640]
            return [v]
        elif isinstance(v, list):
            return v
        raise ValueError("SUPER_ADMIN_IDS must be a list, comma-separated string, or single integer")

    @property
    def super_admin_ids_set(self) -> set[int]:
        return set(self.SUPER_ADMIN_IDS)

settings = Settings()