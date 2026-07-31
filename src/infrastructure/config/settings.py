from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="dickbot", alias="POSTGRES_DB")
    postgres_user: str = Field(default="dickbot", alias="POSTGRES_USER")
    postgres_password: str = Field(default="dickbot", alias="POSTGRES_PASSWORD")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    grow_cooldown_hours: int = Field(default=24, alias="GROW_COOLDOWN_HOURS")
    grow_min_delta_cm: int = Field(default=-5, alias="GROW_MIN_DELTA_CM")
    grow_max_delta_cm: int = Field(default=10, alias="GROW_MAX_DELTA_CM")

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
