from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = Field(default="development", alias="API_ENV")
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(
        default="postgresql+asyncpg://sello:sello@localhost:5432/sello",
        alias="API_DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="API_REDIS_URL")
    jwt_secret: str = Field(
        default="dev-only-change-me-please-use-a-long-random-secret",
        alias="API_JWT_SECRET",
    )
    jwt_algorithm: str = Field(default="HS256", alias="API_JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60 * 24 * 7,
        alias="API_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="API_CORS_ORIGINS")
    frontend_url: str | None = Field(default=None, alias="FRONTEND_URL")
    oauth_token_encryption_key: str | None = Field(default=None, alias="OAUTH_TOKEN_ENCRYPTION_KEY")
    oauth_token_encryption_key_version: str = Field(default="v1", alias="OAUTH_TOKEN_ENCRYPTION_KEY_VERSION")
    oauth_token_refresh_window_days: int = Field(default=7, alias="OAUTH_TOKEN_REFRESH_WINDOW_DAYS")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")
    meta_verify_token: str = Field(default="change-me", alias="META_VERIFY_TOKEN")
    meta_graph_api_version: str = Field(default="v20.0", alias="META_GRAPH_API_VERSION")
    meta_app_id: str | None = Field(default=None, alias="META_APP_ID")
    meta_app_secret: str | None = Field(default=None, alias="META_APP_SECRET")
    meta_oauth_callback_url: str | None = Field(default=None, alias="META_OAUTH_CALLBACK_URL")
    instagram_webhook_url: str | None = Field(default=None, alias="INSTAGRAM_WEBHOOK_URL")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def browser_frontend_url(self) -> str:
        if self.frontend_url:
            return self.frontend_url.rstrip("/")
        if self.cors_origins:
            return self.cors_origins[0].rstrip("/")
        return "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
