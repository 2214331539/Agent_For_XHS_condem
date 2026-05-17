from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Byt Review System"
    app_env: str = "local"
    api_prefix: str = "/api"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "postgresql+psycopg://byt:byt_dev_password@localhost:55432/byt_review"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_image_model: str = "gpt-image-1"
    agent_provider: Literal["local", "openai"] = "local"

    storage_backend: Literal["local", "aliyun_oss"] = "local"
    local_storage_dir: str = "./media"
    public_media_base_url: str = "http://localhost:8000/media"
    oss_endpoint: str = ""
    oss_bucket: str = ""
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_region: str = ""
    oss_public_base_url: str = ""

    reminder_days_after_publish: int = Field(default=7, ge=1)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
