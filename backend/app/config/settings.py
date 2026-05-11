"""Application settings loaded from .env via pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_expire_minutes: int = Field(60, alias="JWT_EXPIRE_MINUTES")
    jwt_algorithm: str = "HS256"
    aes_key: str = Field("default-aes-256-key-32bytes12345678", alias="AES_KEY")
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-sonnet-4-6", alias="ANTHROPIC_MODEL")

    # Anthropic (single key shared by Haiku + Sonnet jobs)
    anthropic_api_key: str | None = Field(None, alias="ANTHROPIC_API_KEY")

    # SSB defaults — only used when tb_expert_settings is unconfigured (dev fallback;
    # production must populate the DB row via /api/expert/settings)
    ssb_host: str | None = Field(None, alias="SSB_HOST")
    ssb_username: str | None = Field(None, alias="SSB_USERNAME")
    ssb_password: str | None = Field(None, alias="SSB_PASSWORD")
    ssb_logspace: str = Field("ALL", alias="SSB_LOGSPACE")
    analysis_mode: str = Field("full", alias="ANALYSIS_MODE")  # "full" or "windows_only"

    # Haiku scheduling (interval-only; runtime guard checks is_enabled before fetch)
    haiku_interval_minutes: int = Field(10, alias="HAIKU_INTERVAL_MINUTES")
    haiku_chunk_size: int = Field(100, alias="HAIKU_CHUNK_SIZE")
    haiku_max_retry: int = Field(8, alias="HAIKU_MAX_RETRY")

    # Settings sync cadence (Sonnet's HH:MM comes from DB; this controls how often we re-read)
    expert_settings_reload_minutes: int = Field(60, alias="EXPERT_SETTINGS_RELOAD_MINUTES")


settings = Settings()
