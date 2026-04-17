from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Flash Task
    FLASH_CHUNK_SIZE: int = 300
    FLASH_MAX_RETRY: int = 3

    # Pro Task（cron 格式，預設凌晨 02:00）
    PRO_TASK_HOUR: int = 2
    PRO_TASK_MINUTE: int = 0

    # Ingest endpoint shared secret（與 adapter 共用）
    INGEST_SECRET: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
