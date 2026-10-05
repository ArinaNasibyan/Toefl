from functools import lru_cache
from hashlib import sha256

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    bot_token: SecretStr = Field(..., alias="BOT_TOKEN")
    webhook_secret: SecretStr | None = Field(default=None, alias="WEBHOOK_SECRET")
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./database.db",
        alias="DATABASE_URL",
    )
    debug: bool = Field(default=False, alias="DEBUG")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admin_ids_raw")
    @classmethod
    def validate_admin_ids(cls, value: str) -> str:
        for item in value.split(","):
            item = item.strip()
            if item:
                int(item)
        return value

    @property
    def admin_ids(self) -> tuple[int, ...]:
        return tuple(
            int(item.strip())
            for item in self.admin_ids_raw.split(",")
            if item.strip()
        )

    @property
    def token(self) -> str:
        return self.bot_token.get_secret_value()

    @property
    def webhook_secret_token(self) -> str:
        configured_secret = (
            self.webhook_secret.get_secret_value()
            if self.webhook_secret is not None
            else ""
        )
        seed = configured_secret or self.token
        return sha256(seed.encode()).hexdigest()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
