from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "mpbox",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.flash_task", "app.tasks.pro_task"],
)

celery_app.conf.timezone = "Asia/Taipei"
celery_app.conf.enable_utc = True

celery_app.conf.beat_schedule = {
    "flash-task": {
        "task": "app.tasks.flash_task.run_flash_task",
        "schedule": settings.FLASH_INTERVAL_MINUTES * 60,
    },
    "pro-task": {
        "task": "app.tasks.pro_task.run_pro_task",
        "schedule": crontab(
            hour=settings.PRO_TASK_HOUR, minute=settings.PRO_TASK_MINUTE
        ),
    },
}
