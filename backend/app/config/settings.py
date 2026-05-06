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


settings = Settings()
