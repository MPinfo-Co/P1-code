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
    anthropic_fast_model: str = Field(
        "claude-haiku-4-5-20251001", alias="ANTHROPIC_FAST_MODEL"
    )

    # Anthropic (single key shared by Haiku + Sonnet jobs)
    anthropic_api_key: str | None = Field(None, alias="ANTHROPIC_API_KEY")

    analysis_mode: str = Field(
        "full", alias="ANALYSIS_MODE"
    )  # "full" or "windows_only"

    # Haiku scheduling (interval-only; runtime guard checks is_enabled before fetch)
    haiku_interval_minutes: int = Field(10, alias="HAIKU_INTERVAL_MINUTES")
    haiku_chunk_size: int = Field(100, alias="HAIKU_CHUNK_SIZE")
    haiku_max_retry: int = Field(8, alias="HAIKU_MAX_RETRY")

    # Sonnet company data injection limit (characters; acts as token budget proxy)
    sonnet_company_data_max_tokens: int = Field(
        50000, alias="SONNET_COMPANY_DATA_MAX_TOKENS"
    )

    # Settings sync cadence (Sonnet's HH:MM comes from DB; this controls how often we re-read)
    expert_settings_reload_minutes: int = Field(
        5, alias="EXPERT_SETTINGS_RELOAD_MINUTES"
    )


settings = Settings()
