from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 現有設定
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # SSB
    SSB_HOST: str = "https://192.168.10.48"
    SSB_USERNAME: str = ""
    SSB_PASSWORD: str = ""
    SSB_LOGSPACE: str = ""
    SSB_SEARCH_EXPRESSION: str = (
        # Windows AD 資安事件（原有）
        "nvpair:.sdata.win@18372.4.event_id=4625 OR "  # 登入失敗
        "nvpair:.sdata.win@18372.4.event_id=4648 OR "  # 明確憑證登入（RunAs）
        "nvpair:.sdata.win@18372.4.event_id=4720 OR "  # 新建帳號
        "nvpair:.sdata.win@18372.4.event_id=4722 OR "  # 啟用帳號
        "nvpair:.sdata.win@18372.4.event_id=4725 OR "  # 停用帳號
        "nvpair:.sdata.win@18372.4.event_id=4740 OR "  # 帳號鎖定
        # Windows AD 資安事件（新增，量少但重要）
        "nvpair:.sdata.win@18372.4.event_id=4719 OR "  # 稽核政策變更
        "nvpair:.sdata.win@18372.4.event_id=4726 OR "  # 刪除帳號
        "nvpair:.sdata.win@18372.4.event_id=4728 OR "  # 加入全域安全群組
        "nvpair:.sdata.win@18372.4.event_id=4732 OR "  # 加入本機安全群組
        "nvpair:.sdata.win@18372.4.event_id=4756 OR "  # 加入萬用安全群組
        "nvpair:.sdata.win@18372.4.event_id=1102 OR "  # 安全日誌被清除
        # FortiGate 防火牆
        "nvpair:.sdata.forti.action=deny OR "  # 拒絕連線
        "nvpair:.sdata.forti.level=warning"  # 警告等級
    )

    SSB_SEARCH_EXPRESSION_WINDOWS_ONLY: str = (
        # 現有 Windows AD 資安事件
        "nvpair:.sdata.win@18372.4.event_id=4625 OR "  # 登入失敗
        "nvpair:.sdata.win@18372.4.event_id=4648 OR "  # 明確憑證登入（RunAs）
        "nvpair:.sdata.win@18372.4.event_id=4720 OR "  # 新建帳號
        "nvpair:.sdata.win@18372.4.event_id=4722 OR "  # 啟用帳號
        "nvpair:.sdata.win@18372.4.event_id=4725 OR "  # 停用帳號
        "nvpair:.sdata.win@18372.4.event_id=4740 OR "  # 帳號鎖定
        # 新增建議 EventID（量少但重要）
        "nvpair:.sdata.win@18372.4.event_id=4719 OR "  # 稽核政策變更
        "nvpair:.sdata.win@18372.4.event_id=4726 OR "  # 刪除帳號
        "nvpair:.sdata.win@18372.4.event_id=4728 OR "  # 加入全域安全群組
        "nvpair:.sdata.win@18372.4.event_id=4732 OR "  # 加入本機安全群組
        "nvpair:.sdata.win@18372.4.event_id=4756 OR "  # 加入萬用安全群組
        "nvpair:.sdata.win@18372.4.event_id=1102"  # 安全日誌被清除
    )

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Analysis mode: "full" (Windows + FortiGate) or "windows_only"
    ANALYSIS_MODE: str = "full"

    # Flash Task
    FLASH_CHUNK_SIZE: int = 300
    FLASH_MAX_RETRY: int = 3
    FLASH_INTERVAL_MINUTES: int = 20

    # Pro Task（cron 格式，預設凌晨 02:00）
    PRO_TASK_HOUR: int = 2
    PRO_TASK_MINUTE: int = 0

    @property
    def effective_search_expression(self) -> str:
        """根據 ANALYSIS_MODE 回傳對應的 search expression。"""
        if self.ANALYSIS_MODE == "windows_only":
            return self.SSB_SEARCH_EXPRESSION_WINDOWS_ONLY
        return self.SSB_SEARCH_EXPRESSION

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
