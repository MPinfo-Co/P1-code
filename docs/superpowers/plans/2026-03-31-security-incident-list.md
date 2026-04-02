# Security Incident List — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 從零建立完整管線：SSB syslog → Celery + Claude Haiku（每 10 分鐘）→ flash_results DB → Celery + Claude Sonnet（每日 02:00）→ security_events DB → REST API → 前端安全事件清單頁。

**Architecture:** Docker Compose 管理 5 個服務（PostgreSQL、Redis、FastAPI、Celery Worker、Celery Beat）。Flash Task 每 10 分鐘從 SSB 拉 log，切成 500 筆 chunk 逐一送 Claude Haiku 分析，結果存入 flash_results。Pro Task 每日凌晨 02:00 讀取當天所有 flash_results，送 Claude Sonnet 去重彙整，產出 security_events。前端 IssueList.jsx 改呼叫真實 GET /api/events。

**Tech Stack:** FastAPI、SQLAlchemy 2.0、Alembic、PostgreSQL 15、Redis 7、Celery 5、anthropic Python SDK、httpx、React + MUI DataGrid

---

## 檔案對應總覽

### 新建檔案

| 路徑 | 職責 |
|------|------|
| `docker-compose.yml`（根目錄） | 5 個 container 的編排設定 |
| `backend/Dockerfile` | backend image（api / worker / beat 共用）|
| `backend/app/worker.py` | Celery app 實例 + Beat 排程定義 |
| `backend/app/models/security_event.py` | LogBatch、FlashResult、SecurityEvent、DailyAnalysis、EventHistory ORM |
| `backend/app/schemas/security_event.py` | Pydantic schema（API request/response）|
| `backend/app/api/deps.py` | `get_current_user` 依賴函式 |
| `backend/app/services/ssb_client.py` | SSB 認證、分頁拉取、search_expression |
| `backend/app/services/claude_flash.py` | Claude Haiku 呼叫 + prompt |
| `backend/app/services/claude_pro.py` | Claude Sonnet 呼叫 + prompt |
| `backend/app/tasks/__init__.py` | 空檔（讓 Python 認識這個 package）|
| `backend/app/tasks/flash_task.py` | Flash Celery task |
| `backend/app/tasks/pro_task.py` | Pro Celery task |
| `backend/app/api/events.py` | REST API endpoints |
| `backend/tests/__init__.py` | 空檔 |
| `backend/tests/conftest.py` | pytest fixtures |
| `backend/tests/services/test_ssb_client.py` | SSB client 單元測試 |
| `backend/tests/services/test_claude_flash.py` | Claude flash 單元測試 |
| `backend/tests/tasks/test_flash_task.py` | Flash task 單元測試 |
| `backend/tests/api/test_events.py` | Events API 整合測試 |

### 修改檔案

| 路徑 | 修改內容 |
|------|----------|
| `backend/requirements.txt` | 新增 celery、anthropic、httpx、pytest、pytest-mock |
| `backend/.env.example` | 新增 SSB_*、ANTHROPIC_API_KEY、CELERY_* 等設定 |
| `backend/app/core/config.py` | 新增 Settings 欄位 |
| `backend/alembic/env.py` | 匯入新 models 讓 Alembic 能偵測 |
| `backend/app/main.py` | 註冊 events router |
| `frontend-mui/src/pages/AiPartner/IssueList.jsx` | 改呼叫真實 API，移除 mock data 依賴 |
| `frontend-mui/vite.config.js` | 新增 proxy `/api` → `http://localhost:8000` |

---

## Task 1：Docker Compose + Dockerfile

**目的：** 讓整個後端服務可以用 `docker-compose up` 一鍵啟動。

**Files:**
- Create: `docker-compose.yml`（專案根目錄，與 `backend/` 同層）
- Create: `backend/Dockerfile`

---

- [ ] **Step 1：建立 backend/Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
```

- [ ] **Step 2：建立根目錄 docker-compose.yml**

```yaml
# docker-compose.yml（放在專案根目錄，與 backend/ 同層）
version: '3.9'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: mpbox
      POSTGRES_PASSWORD: mpbox
      POSTGRES_DB: mpbox
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mpbox"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    env_file: ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app

  beat:
    build: ./backend
    command: celery -A app.worker beat --loglevel=info --scheduler celery.beat.PersistentScheduler
    env_file: ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app

volumes:
  pgdata:
```

- [ ] **Step 3：驗證 docker-compose.yml 語法正確**

在 WSL2 終端執行：
```bash
cd "/mnt/c/Users/MP0451.MPINFO/Desktop/code test"
docker compose config --quiet && echo "OK"
```
預期：印出 `OK`，無 error

- [ ] **Step 4：commit**

```bash
git add docker-compose.yml backend/Dockerfile
git commit -m "feat: add Docker Compose and Dockerfile for backend services"
```

---

## Task 2：更新 requirements.txt + config + .env.example

**目的：** 把新套件加進去，讓設定可以讀取 SSB / Claude / Celery 環境變數。

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`（如果不存在就新建）

---

- [ ] **Step 1：更新 backend/requirements.txt**（在檔案最後加入）

開啟 `backend/requirements.txt`，在末尾加入以下幾行：

```
celery[redis]==5.4.0
anthropic==0.49.0
httpx==0.28.1
pytest==8.3.4
pytest-mock==3.14.0
```

- [ ] **Step 2：更新 backend/app/core/config.py**

把整個檔案改成：

```python
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
        '(program("FortiGate") AND (severity(warning,error,critical,emergency) '
        'OR message("action=deny") OR message("action=block"))) '
        'OR (program("Microsoft-Windows") AND ('
        'message("EventID: 4624") OR message("EventID: 4625") OR '
        'message("EventID: 4648") OR message("EventID: 4720") OR '
        'message("EventID: 4722") OR message("EventID: 4725") OR '
        'message("EventID: 4740")))'
    )

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Flash Task
    FLASH_CHUNK_SIZE: int = 500
    FLASH_MAX_RETRY: int = 3
    FLASH_INTERVAL_MINUTES: int = 10

    # Pro Task（cron 格式，預設凌晨 02:00）
    PRO_TASK_HOUR: int = 2
    PRO_TASK_MINUTE: int = 0

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 3：建立或更新 backend/.env.example**

```bash
# backend/.env.example
DATABASE_URL=postgresql://mpbox:mpbox@db:5432/mpbox
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# SSB（syslog-ng Store Box）
SSB_HOST=https://192.168.10.48
SSB_USERNAME=
SSB_PASSWORD=
SSB_LOGSPACE=
# SSB_SEARCH_EXPRESSION=  # 留空使用程式預設值

# Anthropic Claude
ANTHROPIC_API_KEY=

# Celery（Docker 環境使用 redis://redis:6379/0；本機用 redis://localhost:6379/0）
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Flash Task 設定
FLASH_CHUNK_SIZE=500
FLASH_MAX_RETRY=3
FLASH_INTERVAL_MINUTES=10

# Pro Task 執行時間（24 小時制）
PRO_TASK_HOUR=2
PRO_TASK_MINUTE=0
```

- [ ] **Step 4：確認 backend/.env 存在且有填寫基本值**

```bash
# .env 至少要有以下才能啟動：
DATABASE_URL=postgresql://mpbox:mpbox@db:5432/mpbox
JWT_SECRET_KEY=dev-secret-key
ANTHROPIC_API_KEY=sk-ant-...
SSB_HOST=https://192.168.10.48
SSB_USERNAME=your_ssb_user
SSB_PASSWORD=your_ssb_password
SSB_LOGSPACE=your_logspace_name
```

> **注意：** `.env` 不進 git。確認 `.gitignore` 有 `*.env`。

- [ ] **Step 5：commit**

```bash
git add backend/requirements.txt backend/app/core/config.py backend/.env.example
git commit -m "feat: add celery/anthropic/httpx deps and new config settings"
```

---

## Task 3：DB Models + Alembic Migration

**目的：** 建立 5 張新 table 的 SQLAlchemy ORM model，跑 Alembic migration。

**Files:**
- Create: `backend/app/models/security_event.py`
- Modify: `backend/alembic/env.py`

---

- [ ] **Step 1：建立 backend/app/models/security_event.py**

```python
# backend/app/models/security_event.py
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, ForeignKey,
    Integer, SmallInteger, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class LogBatch(Base):
    __tablename__ = "log_batches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    time_from = Column(DateTime, nullable=False)
    time_to = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    records_fetched = Column(Integer, nullable=False, default=0)
    chunks_total = Column(Integer, nullable=False, default=0)
    chunks_done = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    flash_results = relationship("FlashResult", back_populates="batch", cascade="all, delete-orphan")


class FlashResult(Base):
    __tablename__ = "flash_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_id = Column(BigInteger, ForeignKey("log_batches.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    events = Column(JSONB, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    batch = relationship("LogBatch", back_populates="flash_results")


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_date = Column(Date, nullable=False)
    date_end = Column(Date)
    star_rank = Column(SmallInteger, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    affected_summary = Column(String(20), nullable=False)
    affected_detail = Column(Text)
    current_status = Column(String(20), nullable=False, default="pending")
    match_key = Column(String(200), nullable=False)
    detection_count = Column(Integer, nullable=False, default=0)
    continued_from = Column(BigInteger, ForeignKey("security_events.id"))
    assignee_user_id = Column(Integer, ForeignKey("users.id"))
    suggests = Column(JSONB)
    logs = Column(JSONB)
    ioc_list = Column(JSONB)
    mitre_tags = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    history = relationship("EventHistory", back_populates="event", cascade="all, delete-orphan")


class DailyAnalysis(Base):
    __tablename__ = "daily_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_date = Column(Date, nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="pending")
    flash_results_count = Column(Integer, nullable=False, default=0)
    events_created = Column(Integer, nullable=False, default=0)
    events_updated = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class EventHistory(Base):
    __tablename__ = "event_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(BigInteger, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)
    old_status = Column(String(20))
    new_status = Column(String(20))
    note = Column(Text)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    event = relationship("SecurityEvent", back_populates="history")
```

- [ ] **Step 2：更新 backend/alembic/env.py，讓 Alembic 能看到新 models**

開啟 `backend/alembic/env.py`，找到匯入 models 的區域（通常在 `target_metadata` 附近），加入：

```python
from app.models import user         # 已有
from app.models import security_event  # 新增這行
```

確認 `target_metadata = Base.metadata` 這行仍在。

- [ ] **Step 3：啟動 Docker Compose 的 db，跑 migration**

```bash
cd "/mnt/c/Users/MP0451.MPINFO/Desktop/code test"
docker compose up db -d
# 等待約 5 秒讓 PostgreSQL 完全啟動

docker compose run --rm api alembic upgrade head
```

預期輸出（最後一行）：
```
INFO  [alembic.runtime.migration] Running upgrade <prev_rev> -> <new_rev>, add security event tables
```

- [ ] **Step 4：確認 5 張 table 已建立**

```bash
docker compose exec db psql -U mpbox -d mpbox -c "\dt"
```

預期包含：`log_batches`, `flash_results`, `security_events`, `daily_analysis`, `event_history`

- [ ] **Step 5：commit**

```bash
git add backend/app/models/security_event.py backend/alembic/env.py backend/alembic/versions/
git commit -m "feat: add security event models and migration (5 new tables)"
```

---

## Task 4：SSB Client

**目的：** 封裝所有 SSB REST API 互動（登入、token 管理、分頁拉取）。

**Files:**
- Create: `backend/app/services/ssb_client.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/services/__init__.py`
- Create: `backend/tests/services/test_ssb_client.py`

---

- [ ] **Step 1：寫失敗測試**

建立 `backend/tests/__init__.py`（空檔）
建立 `backend/tests/services/__init__.py`（空檔）

建立 `backend/tests/services/test_ssb_client.py`：

```python
# backend/tests/services/test_ssb_client.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


def make_response(json_data, status_code=200):
    """Helper: 建立假的 httpx Response。"""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


@patch("app.services.ssb_client.httpx.Client")
def test_fetch_logs_single_page(mock_client_class):
    """從 SSB 拉取一頁 log（少於 1000 筆），應回傳所有 log 並停止分頁。"""
    from app.services.ssb_client import SSBClient

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # 模擬 login 成功
    mock_client.post.return_value = make_response({"result": "test-token", "error": {"code": None}})
    # 模擬 fetch 回傳 3 筆（< 1000，結束分頁）
    mock_client.get.return_value = make_response({
        "result": [{"stamp": 1, "message": "test log"}] * 3,
        "error": {"code": None}
    })

    client = SSBClient()
    logs = client.fetch_logs(
        datetime(2026, 3, 31, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 31, 0, 10, tzinfo=timezone.utc),
    )

    assert len(logs) == 3
    assert mock_client.get.call_count == 1  # 只呼叫一次（單頁）


@patch("app.services.ssb_client.httpx.Client")
def test_fetch_logs_two_pages(mock_client_class):
    """第一頁 1000 筆，第二頁 500 筆，共 1500 筆。"""
    from app.services.ssb_client import SSBClient

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_client.post.return_value = make_response({"result": "tok", "error": {"code": None}})
    mock_client.get.side_effect = [
        make_response({"result": [{"stamp": i} for i in range(1000)], "error": {"code": None}}),
        make_response({"result": [{"stamp": i} for i in range(500)], "error": {"code": None}}),
    ]

    client = SSBClient()
    logs = client.fetch_logs(
        datetime(2026, 3, 31, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 31, 0, 10, tzinfo=timezone.utc),
    )

    assert len(logs) == 1500
    assert mock_client.get.call_count == 2


@patch("app.services.ssb_client.httpx.Client")
def test_auto_relogin_on_401(mock_client_class):
    """Token 過期（401）後自動重登，再重試請求。"""
    from app.services.ssb_client import SSBClient

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_client.post.return_value = make_response({"result": "new-token", "error": {"code": None}})

    resp_401 = MagicMock()
    resp_401.status_code = 401
    resp_ok = make_response({"result": [], "error": {"code": None}})
    mock_client.get.side_effect = [resp_401, resp_ok]

    client = SSBClient()
    client._token = "old-token"  # 模擬已有舊 token
    logs = client.fetch_logs(
        datetime(2026, 3, 31, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 31, 0, 10, tzinfo=timezone.utc),
    )

    assert logs == []
    assert mock_client.post.call_count == 1  # 重登了一次
```

- [ ] **Step 2：確認測試失敗（模組不存在）**

```bash
cd /mnt/c/Users/MP0451.MPINFO/Desktop/code\ test/backend
source venv/bin/activate
pip install -r requirements.txt  # 安裝新套件
pytest tests/services/test_ssb_client.py -v
```

預期：`ImportError: No module named 'app.services.ssb_client'`

- [ ] **Step 3：建立 backend/app/services/ssb_client.py**

```python
# backend/app/services/ssb_client.py
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BRUTE_FORCE_LIMIT = 8  # 在觸發 SSB 封鎖（10次）前停止


class SSBClient:
    """SSB REST API 客戶端。管理認證 token，並提供分頁拉取功能。"""

    def __init__(self):
        self._token: Optional[str] = None
        self._login_failures: int = 0
        self._client = httpx.Client(verify=False, timeout=30.0)

    def _login(self) -> None:
        """登入 SSB，取得 AUTHENTICATION_TOKEN。"""
        if self._login_failures >= BRUTE_FORCE_LIMIT:
            raise RuntimeError(
                f"SSB 登入失敗 {self._login_failures} 次，停止重試以避免帳號封鎖（SSB 閾值 10 次）"
            )

        resp = self._client.post(
            f"{settings.SSB_HOST}/api/5/login",
            data={"username": settings.SSB_USERNAME, "password": settings.SSB_PASSWORD},
        )
        data = resp.json()
        if data.get("error", {}).get("code"):
            self._login_failures += 1
            raise RuntimeError(f"SSB 登入失敗：{data['error'].get('message', 'unknown error')}")

        self._token = data["result"]
        self._login_failures = 0
        logger.info("SSB 登入成功")

    def _auth_headers(self) -> dict:
        if not self._token:
            self._login()
        return {"Cookie": f"AUTHENTICATION_TOKEN={self._token}"}

    def fetch_logs(
        self,
        time_from: datetime,
        time_to: datetime,
        search_expression: str = "",
    ) -> list[dict]:
        """拉取指定時間範圍內所有符合 search_expression 的 log。自動分頁直到取完。"""
        all_logs: list[dict] = []
        offset = 0
        limit = 1000

        while True:
            resp = self._client.get(
                f"{settings.SSB_HOST}/api/5/search/logspace/filter/{settings.SSB_LOGSPACE}",
                params={
                    "from": int(time_from.timestamp()),
                    "to": int(time_to.timestamp()),
                    "search_expression": search_expression,
                    "offset": offset,
                    "limit": limit,
                },
                headers=self._auth_headers(),
            )

            if resp.status_code == 401:
                # Token 過期，重新登入後繼續
                self._token = None
                self._login()
                continue

            resp.raise_for_status()
            batch = resp.json().get("result", [])
            all_logs.extend(batch)

            if len(batch) < limit:
                break  # 最後一頁

            offset += limit

        return all_logs

    def close(self) -> None:
        self._client.close()
```

- [ ] **Step 4：執行測試，確認通過**

```bash
pytest tests/services/test_ssb_client.py -v
```

預期：
```
PASSED tests/services/test_ssb_client.py::test_fetch_logs_single_page
PASSED tests/services/test_ssb_client.py::test_fetch_logs_two_pages
PASSED tests/services/test_ssb_client.py::test_auto_relogin_on_401
```

- [ ] **Step 5：commit**

```bash
git add backend/app/services/ssb_client.py backend/tests/
git commit -m "feat: add SSB client with pagination and auto-relogin"
```

---

## Task 5：Claude Haiku Service（claude_flash.py）

**目的：** 封裝 Claude Haiku API 呼叫，接收一批 log，回傳結構化事件 JSON。

**Files:**
- Create: `backend/app/services/claude_flash.py`
- Create: `backend/tests/services/test_claude_flash.py`

---

- [ ] **Step 1：寫失敗測試**

建立 `backend/tests/services/test_claude_flash.py`：

```python
# backend/tests/services/test_claude_flash.py
import json
import pytest
from unittest.mock import MagicMock, patch


SAMPLE_LOGS = [
    {"stamp": 1711123200, "host": "192.168.1.50", "program": "Microsoft-Windows",
     "message": "EventID: 4625 Account Name: MP0263 Failure Reason: Unknown user name"},
    {"stamp": 1711123210, "host": "192.168.1.50", "program": "Microsoft-Windows",
     "message": "EventID: 4625 Account Name: MP0263 Failure Reason: Unknown user name"},
]

EXPECTED_EVENTS = [
    {
        "star_rank": 4,
        "title": "帳號 MP0263 多次登入失敗",
        "affected_summary": "MP0263（登入失敗）",
        "affected_detail": "【受影響對象】MP0263\n【攻擊行為】2 次登入失敗（EventID 4625）",
        "match_key": "MP0263_login_failure_192.168.1.50",
        "log_ids": ["1711123200", "1711123210"],
        "ioc_list": [],
        "mitre_tags": ["T1110"],
    }
]


@patch("app.services.claude_flash.Anthropic")
def test_analyze_chunk_returns_events(mock_anthropic_class):
    """正常情況：Claude 回傳合法 JSON 陣列，函式應直接回傳 list。"""
    from app.services.claude_flash import analyze_chunk

    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(EXPECTED_EVENTS))]
    mock_client.messages.create.return_value = mock_message

    result = analyze_chunk(SAMPLE_LOGS)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["star_rank"] == 4
    assert result[0]["match_key"] == "MP0263_login_failure_192.168.1.50"


@patch("app.services.claude_flash.Anthropic")
def test_analyze_chunk_returns_empty_for_benign_logs(mock_anthropic_class):
    """無資安事件時，Claude 回傳 []，函式也應回傳空 list。"""
    from app.services.claude_flash import analyze_chunk

    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="[]")]
    mock_client.messages.create.return_value = mock_message

    result = analyze_chunk([{"stamp": 1, "message": "normal info log"}])
    assert result == []


@patch("app.services.claude_flash.Anthropic")
def test_analyze_chunk_strips_markdown_code_block(mock_anthropic_class):
    """Claude 有時會用 ```json ... ``` 包住輸出，函式應能剝除並正確解析。"""
    from app.services.claude_flash import analyze_chunk

    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client

    json_with_markdown = f"```json\n{json.dumps(EXPECTED_EVENTS)}\n```"
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json_with_markdown)]
    mock_client.messages.create.return_value = mock_message

    result = analyze_chunk(SAMPLE_LOGS)
    assert len(result) == 1
```

- [ ] **Step 2：確認測試失敗**

```bash
pytest tests/services/test_claude_flash.py -v
```

預期：`ImportError: No module named 'app.services.claude_flash'`

- [ ] **Step 3：建立 backend/app/services/claude_flash.py**

```python
# backend/app/services/claude_flash.py
import json
import logging

from anthropic import Anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

# Anthropic client 在模組層級建立，共用同一個 HTTP 連線
_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """你是資安事件分析師。分析輸入的 syslog 資料，找出所有值得關注的資安事件。
規則：
1. 只輸出 JSON 陣列，不加任何說明文字、markdown 或程式碼區塊
2. 若無資安事件，輸出空陣列 []
3. star_rank 定義：1=正常資訊 2=低風險 3=中風險 4=高風險 5=緊急
4. affected_summary：20 字以內，格式「{主要對象}（{最關鍵補充}）」
5. affected_detail：必填【受影響對象】【攻擊行為】；選填【攻擊來源】【時間範圍】
6. match_key：全英文/數字/底線，格式「{識別對象}_{攻擊類型}_{來源識別}」"""

USER_PROMPT_TEMPLATE = """以下是 {chunk_size} 筆 syslog，請分析並輸出資安事件 JSON 陣列。

每筆事件格式：
{{
  "star_rank": 1-5,
  "title": "事件標題（50字以內）",
  "affected_summary": "20字以內，格式：對象（補充）",
  "affected_detail": "【受影響對象】...\\n【攻擊行為】...",
  "match_key": "英文_底線_格式",
  "log_ids": ["log 的 stamp 值（字串）"],
  "ioc_list": ["IP 或域名"],
  "mitre_tags": ["TXXXX"]
}}

syslog 資料：
{logs_json}"""


def analyze_chunk(logs: list[dict]) -> list[dict]:
    """
    送一批 log 給 Claude Haiku 分析。
    回傳：資安事件 list（無事件時回傳空 list）。
    """
    prompt = USER_PROMPT_TEMPLATE.format(
        chunk_size=len(logs),
        logs_json=json.dumps(logs, ensure_ascii=False),
    )

    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()

    # Claude 偶爾會用 ```json ... ``` 包住輸出，剝除它
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]).strip()

    events = json.loads(text)
    if not isinstance(events, list):
        raise ValueError(f"Claude 回傳的不是陣列：{type(events)}")

    return events
```

- [ ] **Step 4：執行測試，確認通過**

```bash
pytest tests/services/test_claude_flash.py -v
```

預期：3 個 PASSED

- [ ] **Step 5：commit**

```bash
git add backend/app/services/claude_flash.py backend/tests/services/test_claude_flash.py
git commit -m "feat: add Claude Haiku analysis service with JSON parsing"
```

---

## Task 6：Celery Worker + Flash Task

**目的：** 設定 Celery app，實作每 10 分鐘拉 SSB 並分析的 Flash Task。

**Files:**
- Create: `backend/app/worker.py`
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/flash_task.py`
- Create: `backend/tests/tasks/__init__.py`
- Create: `backend/tests/tasks/test_flash_task.py`

---

- [ ] **Step 1：建立 backend/app/worker.py**

```python
# backend/app/worker.py
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
        "schedule": settings.FLASH_INTERVAL_MINUTES * 60,  # 秒數
    },
    "pro-task": {
        "task": "app.tasks.pro_task.run_pro_task",
        "schedule": crontab(hour=settings.PRO_TASK_HOUR, minute=settings.PRO_TASK_MINUTE),
    },
}
```

- [ ] **Step 2：建立 backend/app/tasks/__init__.py**（空檔）

```bash
touch backend/app/tasks/__init__.py
```

- [ ] **Step 3：寫 Flash Task 測試**

建立 `backend/tests/tasks/__init__.py`（空檔），
建立 `backend/tests/tasks/test_flash_task.py`：

```python
# backend/tests/tasks/test_flash_task.py
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone


def make_batch(id=1, status="running", time_from=None, time_to=None):
    batch = MagicMock()
    batch.id = id
    batch.status = status
    batch.time_from = time_from or datetime(2026, 3, 31, 0, 0, tzinfo=timezone.utc)
    batch.time_to = time_to or datetime(2026, 3, 31, 0, 10, tzinfo=timezone.utc)
    batch.retry_count = 0
    batch.chunks_total = 0
    batch.chunks_done = 0
    batch.records_fetched = 0
    return batch


@patch("app.tasks.flash_task.analyze_chunk")
@patch("app.tasks.flash_task.SSBClient")
@patch("app.tasks.flash_task.SessionLocal")
def test_process_batch_success(mock_session, mock_ssb_class, mock_analyze):
    """正常批次：拉到 600 筆 log，切 2 個 chunk，兩個都成功。"""
    from app.tasks.flash_task import _process_batch

    db = MagicMock()
    mock_session.return_value = db

    ssb = MagicMock()
    mock_ssb_class.return_value = ssb
    ssb.fetch_logs.return_value = [{"stamp": i, "message": "log"} for i in range(600)]

    mock_analyze.return_value = [{"star_rank": 3, "title": "test", "match_key": "a_b_c",
                                   "affected_summary": "test", "log_ids": [], "ioc_list": [], "mitre_tags": []}]

    batch = make_batch()
    _process_batch(db, ssb, batch)

    assert batch.status == "success"
    assert batch.records_fetched == 600
    assert batch.chunks_total == 2   # 600 / 500 = 2 chunks
    assert mock_analyze.call_count == 2


@patch("app.tasks.flash_task.analyze_chunk")
@patch("app.tasks.flash_task.SSBClient")
@patch("app.tasks.flash_task.SessionLocal")
def test_process_chunk_retries_on_failure(mock_session, mock_ssb_class, mock_analyze):
    """Claude 呼叫失敗時，應重試最多 FLASH_MAX_RETRY 次，最終將 chunk 標為 failed。"""
    from app.tasks.flash_task import _process_chunk
    from app.core.config import settings

    db = MagicMock()
    batch = make_batch()
    mock_analyze.side_effect = Exception("Claude API error")

    flash_result = MagicMock()
    flash_result.status = "pending"

    with patch("app.tasks.flash_task.FlashResult", return_value=flash_result):
        _process_chunk(db, batch, chunk_index=0, chunk=[{"stamp": 1}])

    assert mock_analyze.call_count == settings.FLASH_MAX_RETRY
    assert flash_result.status == "failed"
```

- [ ] **Step 4：確認測試失敗**

```bash
pytest tests/tasks/test_flash_task.py -v
```

預期：`ImportError: No module named 'app.tasks.flash_task'`

- [ ] **Step 5：建立 backend/app/tasks/flash_task.py**

```python
# backend/app/tasks/flash_task.py
import logging
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.security_event import FlashResult, LogBatch
from app.services.claude_flash import analyze_chunk
from app.services.ssb_client import SSBClient
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.flash_task.run_flash_task")
def run_flash_task() -> None:
    """每 FLASH_INTERVAL_MINUTES 分鐘觸發。先補跑失敗批次，再處理當前時間窗口。"""
    db = SessionLocal()
    ssb = SSBClient()

    try:
        # 1. 補跑：找最新失敗批次
        failed = (
            db.query(LogBatch)
            .filter(LogBatch.status == "failed")
            .order_by(LogBatch.created_at.desc())
            .first()
        )
        if failed:
            logger.info(f"補跑失敗批次 id={failed.id}，時間範圍 {failed.time_from} ~ {failed.time_to}")
            failed.status = "running"
            failed.retry_count += 1
            db.commit()
            _process_batch(db, ssb, failed)

        # 2. 建立當前時間窗口批次
        last_success = (
            db.query(LogBatch)
            .filter(LogBatch.status == "success")
            .order_by(LogBatch.time_to.desc())
            .first()
        )
        now = datetime.now(timezone.utc)
        time_from = last_success.time_to if last_success else now - timedelta(
            minutes=settings.FLASH_INTERVAL_MINUTES
        )

        new_batch = LogBatch(time_from=time_from, time_to=now, status="running")
        db.add(new_batch)
        db.commit()

        _process_batch(db, ssb, new_batch)

    finally:
        db.close()
        ssb.close()


def _process_batch(db, ssb: SSBClient, batch: LogBatch) -> None:
    """拉取 log → 切 chunk → 逐一分析 → 更新 batch 狀態。"""
    try:
        logs = ssb.fetch_logs(
            batch.time_from,
            batch.time_to,
            settings.SSB_SEARCH_EXPRESSION,
        )
        batch.records_fetched = len(logs)

        chunks = [
            logs[i : i + settings.FLASH_CHUNK_SIZE]
            for i in range(0, max(len(logs), 1), settings.FLASH_CHUNK_SIZE)
        ]
        batch.chunks_total = len(chunks)
        db.commit()

        for idx, chunk in enumerate(chunks):
            _process_chunk(db, batch, chunk_index=idx, chunk=chunk)
            batch.chunks_done = idx + 1
            db.commit()

        batch.status = "success"

    except Exception as exc:
        batch.status = "failed"
        batch.error_message = str(exc)
        logger.exception(f"批次 id={batch.id} 失敗：{exc}")

    finally:
        db.commit()


def _process_chunk(db, batch: LogBatch, chunk_index: int, chunk: list[dict]) -> None:
    """送單一 chunk 給 Claude Haiku，最多重試 FLASH_MAX_RETRY 次。"""
    flash_result = FlashResult(
        batch_id=batch.id,
        chunk_index=chunk_index,
        chunk_size=len(chunk),
        status="pending",
    )
    db.add(flash_result)
    db.commit()

    for attempt in range(settings.FLASH_MAX_RETRY):
        try:
            events = analyze_chunk(chunk)
            flash_result.events = events
            flash_result.status = "success"
            flash_result.processed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"chunk {chunk_index} 成功，找到 {len(events)} 個事件")
            return
        except Exception as exc:
            logger.warning(f"chunk {chunk_index} 第 {attempt + 1} 次失敗：{exc}")

    flash_result.status = "failed"
    flash_result.error_message = f"超過最大重試次數 {settings.FLASH_MAX_RETRY}"
    db.commit()
    logger.error(f"chunk {chunk_index} 最終失敗")
```

- [ ] **Step 6：執行測試，確認通過**

```bash
pytest tests/tasks/test_flash_task.py -v
```

預期：2 個 PASSED

- [ ] **Step 7：commit**

```bash
git add backend/app/worker.py backend/app/tasks/ backend/tests/tasks/
git commit -m "feat: add Celery worker config and Flash Task with retry logic"
```

---

## Task 7：Claude Sonnet Service + Pro Task

**目的：** 用 Claude Sonnet 彙整當天所有 flash_results，產出最終 security_events。

**Files:**
- Create: `backend/app/services/claude_pro.py`
- Create: `backend/app/tasks/pro_task.py`

---

- [ ] **Step 1：建立 backend/app/services/claude_pro.py**

```python
# backend/app/services/claude_pro.py
import json
import logging

from anthropic import Anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """你是資深資安分析師。根據一整天的 AI 分析結果，產出整合去重後的最終事件清單。
規則：
1. 只輸出 JSON 陣列，不加任何說明文字
2. 合併相同攻擊的重複偵測（相同 match_key 或明顯相同的攻擊）
3. 若事件與昨天的事件相同（延續），填入 continued_from_match_key
4. detection_count 為所有相關 log 的總數
5. suggests 提供 3-5 條具體處置建議"""

USER_PROMPT_TEMPLATE = """今天日期：{today}

今天偵測到的事件候選（依 match_key 分群，每群代表同類事件的所有偵測）：
{grouped_events_json}

昨天的已確認事件（用於判斷是否為延續事件）：
{previous_events_json}

請輸出整合後的最終事件清單，每筆格式：
{{
  "match_key": "與輸入相同或合併後的 key",
  "star_rank": 1-5,
  "title": "最終事件標題（50字以內）",
  "description": "事件說明（200字以內）",
  "affected_summary": "20字以內，格式：對象（補充）",
  "affected_detail": "【受影響對象】...\\n【攻擊行為】...",
  "detection_count": 123,
  "ioc_list": ["IP 或域名"],
  "mitre_tags": ["TXXXX"],
  "suggests": ["處置步驟 1", "處置步驟 2"],
  "continued_from_match_key": "昨天的 match_key（若為延續事件），否則 null"
}}"""


def aggregate_daily(
    grouped_events: dict[str, list[dict]],
    previous_events: list[dict],
    today: str,
) -> list[dict]:
    """
    送整天的分群事件給 Claude Sonnet 彙整。
    grouped_events: { match_key: [event, event, ...], ... }
    previous_events: 昨天的 security_events 摘要
    today: "YYYY-MM-DD"
    回傳：最終事件 list
    """
    prompt = USER_PROMPT_TEMPLATE.format(
        today=today,
        grouped_events_json=json.dumps(grouped_events, ensure_ascii=False, indent=2),
        previous_events_json=json.dumps(previous_events, ensure_ascii=False),
    )

    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]).strip()

    events = json.loads(text)
    if not isinstance(events, list):
        raise ValueError(f"Claude Sonnet 回傳的不是陣列：{type(events)}")

    return events
```

- [ ] **Step 2：建立 backend/app/tasks/pro_task.py**

```python
# backend/app/tasks/pro_task.py
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.security_event import DailyAnalysis, FlashResult, LogBatch, SecurityEvent
from app.services.claude_pro import aggregate_daily
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.pro_task.run_pro_task")
def run_pro_task() -> None:
    """每日凌晨執行。讀取當天所有成功 flash_results，送 Claude Sonnet 彙整，寫入 security_events。"""
    db = SessionLocal()
    today = date.today()
    yesterday = today - timedelta(days=1)

    # 1. 建立執行紀錄
    analysis = DailyAnalysis(
        analysis_date=today,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.commit()

    try:
        # 2. 讀取今天成功的 flash_results（透過 log_batches 的時間範圍判斷當日）
        today_batches = (
            db.query(LogBatch.id)
            .filter(LogBatch.time_from >= datetime(today.year, today.month, today.day, tzinfo=timezone.utc))
            .subquery()
        )
        flash_results = (
            db.query(FlashResult)
            .filter(FlashResult.status == "success", FlashResult.batch_id.in_(today_batches))
            .all()
        )
        analysis.flash_results_count = len(flash_results)
        db.commit()

        if not flash_results:
            logger.info(f"{today}：無 flash_results，跳過 Pro Task")
            analysis.status = "success"
            analysis.completed_at = datetime.now(timezone.utc)
            db.commit()
            return

        # 3. 依 match_key 分群
        grouped: dict[str, list[dict]] = defaultdict(list)
        for fr in flash_results:
            for event in (fr.events or []):
                grouped[event["match_key"]].append(event)

        # 4. 取昨天事件（延續判斷用）
        prev_events = db.query(SecurityEvent).filter(SecurityEvent.event_date == yesterday).all()
        prev_summary = [{"match_key": e.match_key, "title": e.title, "id": e.id} for e in prev_events]
        prev_id_map = {e.match_key: e.id for e in prev_events}

        # 5. 送 Claude Sonnet
        final_events = aggregate_daily(dict(grouped), prev_summary, str(today))

        # 6. 寫入 security_events
        created = updated = 0
        for ev in final_events:
            existing = (
                db.query(SecurityEvent)
                .filter(SecurityEvent.match_key == ev["match_key"], SecurityEvent.event_date == today)
                .first()
            )
            continued_from_id = prev_id_map.get(ev.get("continued_from_match_key") or "")

            if existing:
                for field in ["star_rank", "title", "description", "affected_summary",
                               "affected_detail", "detection_count", "ioc_list",
                               "mitre_tags", "suggests"]:
                    setattr(existing, field, ev.get(field))
                existing.updated_at = datetime.now(timezone.utc)
                updated += 1
            else:
                db.add(SecurityEvent(
                    event_date=today,
                    star_rank=ev["star_rank"],
                    title=ev["title"],
                    description=ev.get("description"),
                    affected_summary=ev["affected_summary"],
                    affected_detail=ev.get("affected_detail"),
                    match_key=ev["match_key"],
                    detection_count=ev.get("detection_count", 0),
                    continued_from=continued_from_id,
                    ioc_list=ev.get("ioc_list"),
                    mitre_tags=ev.get("mitre_tags"),
                    suggests=ev.get("suggests"),
                ))
                created += 1

        db.commit()

        analysis.status = "success"
        analysis.events_created = created
        analysis.events_updated = updated
        analysis.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Pro Task 完成：新建 {created} 筆，更新 {updated} 筆")

    except Exception as exc:
        analysis.status = "failed"
        analysis.error_message = str(exc)
        db.commit()
        logger.exception(f"Pro Task 失敗：{exc}")
    finally:
        db.close()
```

- [ ] **Step 3：手動驗證 import 正常**

```bash
cd /mnt/c/Users/MP0451.MPINFO/Desktop/code\ test/backend
source venv/bin/activate
python -c "from app.services.claude_pro import aggregate_daily; print('OK')"
python -c "from app.tasks.pro_task import run_pro_task; print('OK')"
```

預期：兩行都印 `OK`，無 ImportError

- [ ] **Step 4：commit**

```bash
git add backend/app/services/claude_pro.py backend/app/tasks/pro_task.py
git commit -m "feat: add Claude Sonnet service and daily Pro Task"
```

---

## Task 8：get_current_user 依賴 + Pydantic Schemas + Events API

**目的：** 建立 REST API，讓前端可以查詢、更新安全事件。

**Files:**
- Create: `backend/app/api/deps.py`
- Create: `backend/app/schemas/security_event.py`
- Create: `backend/app/api/events.py`
- Create: `backend/tests/api/__init__.py`
- Create: `backend/tests/api/test_events.py`

---

- [ ] **Step 1：建立 backend/app/api/deps.py**

這個檔案提供 `get_current_user` 依賴，讓 events API 可以驗證 JWT。

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    驗證 JWT Bearer token，回傳對應的 User。
    Token 無效或已登出 → 401。
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 無效或已過期")

    # 確認 token 未被登出（加入黑名單）
    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    if blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已登出")

    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="使用者不存在或已停用")

    return user
```

- [ ] **Step 2：建立 backend/app/schemas/security_event.py**

```python
# backend/app/schemas/security_event.py
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class HistoryOut(BaseModel):
    id: int
    user_id: int
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventItem(BaseModel):
    """清單頁用的輕量結構（不含 description、history 等大欄位）。"""
    id: int
    event_date: date
    date_end: Optional[date] = None
    star_rank: int
    title: str
    affected_summary: str
    detection_count: int
    current_status: str
    assignee_user_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventDetail(EventItem):
    """詳情頁用的完整結構。"""
    description: Optional[str] = None
    affected_detail: Optional[str] = None
    match_key: str
    continued_from: Optional[int] = None
    suggests: Optional[list[Any]] = None
    logs: Optional[list[Any]] = None
    ioc_list: Optional[list[Any]] = None
    mitre_tags: Optional[list[Any]] = None
    updated_at: datetime
    history: list[HistoryOut] = []


class EventListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EventItem]


class EventUpdate(BaseModel):
    current_status: Optional[str] = None
    assignee_user_id: Optional[int] = None


class HistoryCreate(BaseModel):
    note: str
    resolved_at: Optional[datetime] = None


class HistoryOut201(HistoryOut):
    event_id: int
```

- [ ] **Step 3：寫 Events API 測試**

建立 `backend/tests/api/__init__.py`（空檔），
建立 `backend/tests/conftest.py`：

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    user.email = "test@test.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_user, mock_db):
    """TestClient with get_current_user and get_db both mocked（不需要真實 DB 或 JWT）。"""
    from app.main import app
    from app.api.deps import get_current_user
    from app.db.session import get_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

建立 `backend/tests/api/test_events.py`：

```python
# backend/tests/api/test_events.py
from datetime import date, datetime, timezone
from unittest.mock import MagicMock


def make_event(id=1, star_rank=5, current_status="pending"):
    ev = MagicMock()
    ev.id = id
    ev.event_date = date(2026, 3, 31)
    ev.date_end = None
    ev.star_rank = star_rank
    ev.title = f"測試事件 {id}"
    ev.affected_summary = "MP0263（登入失敗）"
    ev.detection_count = 100
    ev.current_status = current_status
    ev.assignee_user_id = None
    ev.created_at = datetime(2026, 3, 31, 2, 0, tzinfo=timezone.utc)
    ev.description = None
    ev.affected_detail = None
    ev.match_key = f"test_key_{id}"
    ev.continued_from = None
    ev.suggests = None
    ev.logs = None
    ev.ioc_list = None
    ev.mitre_tags = None
    ev.updated_at = datetime(2026, 3, 31, 2, 0, tzinfo=timezone.utc)
    ev.history = []
    return ev


def test_list_events_returns_200(client, mock_db):
    """GET /api/events 應回傳 200 及正確的分頁結構。"""
    events = [make_event(1, 5), make_event(2, 3)]
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 2
    mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = events

    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_event_returns_404_when_not_found(client, mock_db):
    """GET /api/events/999 當事件不存在時應回傳 404。"""
    mock_db.query.return_value.filter.return_value.first.return_value = None

    resp = client.get("/api/events/999")
    assert resp.status_code == 404


def test_patch_event_updates_status(client, mock_db):
    """PATCH /api/events/1 更新 current_status，應寫入 event_history 並回傳更新後事件。"""
    event = make_event(1, current_status="pending")
    mock_db.query.return_value.filter.return_value.first.return_value = event
    mock_db.refresh = MagicMock(return_value=None)

    resp = client.patch("/api/events/1", json={"current_status": "investigating"})
    assert resp.status_code == 200
    # 確認有寫入 event_history（db.add 被呼叫）
    mock_db.add.assert_called()
```

- [ ] **Step 4：確認測試失敗**

```bash
pytest tests/api/test_events.py -v
```

預期：`ImportError: No module named 'app.api.events'`（或 404 test client error）

- [ ] **Step 5：建立 backend/app/api/events.py**

```python
# backend/app/api/events.py
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.security_event import EventHistory, SecurityEvent
from app.models.user import User
from app.schemas.security_event import (
    EventDetail,
    EventListResponse,
    EventUpdate,
    HistoryCreate,
    HistoryOut201,
)

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    status: Optional[str] = Query(None, description="逗號分隔，例如 pending,investigating"),
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO8601 date, e.g. 2026-03-01"),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(SecurityEvent)

    if status:
        statuses = [s.strip() for s in status.split(",")]
        q = q.filter(SecurityEvent.current_status.in_(statuses))

    if keyword:
        q = q.filter(
            or_(
                SecurityEvent.title.ilike(f"%{keyword}%"),
                SecurityEvent.affected_summary.ilike(f"%{keyword}%"),
            )
        )

    if date_from:
        q = q.filter(SecurityEvent.event_date >= date_from)
    if date_to:
        q = q.filter(SecurityEvent.event_date <= date_to)

    total = q.count()
    items = (
        q.order_by(SecurityEvent.star_rank.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{event_id}", response_model=EventDetail)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return event


@router.patch("/{event_id}", response_model=EventDetail)
def update_event(
    event_id: int,
    body: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    if body.current_status is not None:
        db.add(EventHistory(
            event_id=event.id,
            user_id=current_user.id,
            action="status_change",
            old_status=event.current_status,
            new_status=body.current_status,
        ))
        event.current_status = body.current_status

    if body.assignee_user_id is not None:
        db.add(EventHistory(
            event_id=event.id,
            user_id=current_user.id,
            action="assign",
        ))
        event.assignee_user_id = body.assignee_user_id

    event.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/history", response_model=HistoryOut201, status_code=201)
def add_history(
    event_id: int,
    body: HistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    action = "resolve" if body.resolved_at else "comment"
    history = EventHistory(
        event_id=event_id,
        user_id=current_user.id,
        action=action,
        note=body.note,
        resolved_at=body.resolved_at,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
```

- [ ] **Step 6：執行測試，確認通過**

```bash
pytest tests/api/test_events.py -v
```

預期：3 個 PASSED

- [ ] **Step 7：commit**

```bash
git add backend/app/api/deps.py backend/app/api/events.py \
        backend/app/schemas/security_event.py \
        backend/tests/conftest.py backend/tests/api/
git commit -m "feat: add events REST API with JWT auth (GET/PATCH/POST)"
```

---

## Task 9：註冊 Events Router + 全部測試通過

**Files:**
- Modify: `backend/app/main.py`

---

- [ ] **Step 1：在 main.py 註冊 events router**

開啟 `backend/app/main.py`，改成：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.health import router as health_router

app = FastAPI(title="MP-Box API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
```

- [ ] **Step 2：執行所有測試**

```bash
cd /mnt/c/Users/MP0451.MPINFO/Desktop/code\ test/backend
source venv/bin/activate
pytest tests/ -v
```

預期：全部 PASSED，無 FAILED

- [ ] **Step 3：commit**

```bash
git add backend/app/main.py
git commit -m "feat: register events router and add CORS for frontend dev"
```

---

## Task 10：前端 IssueList.jsx 串接真實 API

**目的：** 移除 mock data，改呼叫後端 GET /api/events，篩選由後端處理。

**Files:**
- Modify: `frontend-mui/vite.config.js`
- Modify: `frontend-mui/src/pages/AiPartner/IssueList.jsx`

---

- [ ] **Step 1：在 vite.config.js 新增 API proxy**

開啟 `frontend-mui/vite.config.js`，加入 proxy 設定讓 `/api` 轉發到後端（這樣開發時不需要設定 CORS）：

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 2：改寫 frontend-mui/src/pages/AiPartner/IssueList.jsx**

用以下內容完整替換檔案：

```jsx
import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { DataGrid } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined'

const STAR_COLOR = { 5: '#b91c1c', 4: '#c2410c', 3: '#b45309', 2: '#1e40af', 1: '#475569' }

const STATUS_LABEL = {
  pending: '未處理',
  investigating: '調查中',
  resolved: '已解決',
  dismissed: '已忽略',
}

const STATUS_COLOR = {
  pending:      { bgcolor: '#fef2f2', color: '#dc2626' },
  investigating:{ bgcolor: '#fffbeb', color: '#d97706' },
  resolved:     { bgcolor: '#f0fdf4', color: '#16a34a' },
  dismissed:    { bgcolor: '#f8fafc', color: '#94a3b8' },
}

export default function IssueList() {
  const { partnerId } = useParams()
  const navigate = useNavigate()

  // 篩選草稿（尚未套用）
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [filterStart, setFilterStart] = useState('')
  const [filterEnd, setFilterEnd] = useState('')

  // 已套用篩選（觸發 fetch）
  const [applied, setApplied] = useState({ status: 'all', keyword: '', start: '', end: '' })

  // DataGrid 分頁（0-indexed）
  const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 20 })

  // 資料狀態
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        page: paginationModel.page + 1,        // 後端 page 從 1 開始
        page_size: paginationModel.pageSize,
      })
      if (applied.status !== 'all') params.set('status', applied.status)
      if (applied.keyword) params.set('keyword', applied.keyword)
      if (applied.start) params.set('date_from', applied.start)
      if (applied.end) params.set('date_to', applied.end)

      const token = localStorage.getItem('access_token')
      const res = await fetch(`/api/events?${params}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setRows(data.items)
      setTotal(data.total)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [applied, paginationModel])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  function applyFilters() {
    setPaginationModel(prev => ({ ...prev, page: 0 }))  // 套用篩選時回到第一頁
    setApplied({ status: filterStatus, keyword: filterKeyword, start: filterStart, end: filterEnd })
  }

  function resetFilters() {
    setFilterStatus('all')
    setFilterKeyword('')
    setFilterStart('')
    setFilterEnd('')
    setApplied({ status: 'all', keyword: '', start: '', end: '' })
  }

  const columns = [
    {
      field: 'title', headerName: '事件說明', flex: 2, minWidth: 180,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', lineHeight: 1.4 }}>
          {value}
        </Typography>
      ),
    },
    {
      field: 'star_rank', headerName: '優先級', width: 120,
      renderCell: ({ value }) => {
        const color = STAR_COLOR[value] || '#475569'
        return (
          <Box>
            <span style={{ color, fontSize: 14, letterSpacing: 1 }}>{'★'.repeat(value)}</span>
            <span style={{ color: '#e2e8f0', fontSize: 14, letterSpacing: 1 }}>
              {'★'.repeat(5 - value)}
            </span>
          </Box>
        )
      },
    },
    {
      field: 'event_date', headerName: '發生日期', width: 160,
      renderCell: ({ row }) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>
          {row.date_end && row.date_end !== row.event_date
            ? `${row.event_date} ~ ${row.date_end}`
            : row.event_date}
        </Typography>
      ),
    },
    {
      field: 'affected_summary', headerName: '影響範圍', width: 160,
      renderCell: ({ value }) => (
        <Chip
          label={value}
          size="small"
          sx={{ fontSize: 11, bgcolor: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' }}
        />
      ),
    },
    {
      field: 'detection_count', headerName: '偵測筆數', width: 100,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>{value?.toLocaleString()}</Typography>
      ),
    },
    {
      field: 'current_status', headerName: '處理狀態', width: 120,
      renderCell: ({ value }) => {
        const style = STATUS_COLOR[value] || STATUS_COLOR.dismissed
        return (
          <Chip
            label={STATUS_LABEL[value] || value}
            size="small"
            sx={{ fontSize: 11, fontWeight: 700, ...style }}
          />
        )
      },
    },
    {
      field: 'actions', headerName: '執行動作', width: 110, sortable: false,
      renderCell: ({ row }) => (
        <Button
          size="small"
          variant="contained"
          onClick={() => navigate(`/ai-partner/${partnerId}/issues/${row.id}`)}
          sx={{ fontSize: 12, py: 0.5 }}
        >
          事件處理
        </Button>
      ),
    },
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 110px)' }}>
      {/* 標題列 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexShrink: 0 }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b' }}>安全事件清單</Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackOutlinedIcon />}
          size="small"
          onClick={() => navigate('/ai-partner')}
          sx={{ color: '#64748b', borderColor: '#cbd5e1' }}
        >
          回上一頁
        </Button>
      </Box>

      {/* 篩選列 */}
      <Box sx={{
        bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0',
        p: 2, mb: 2, flexShrink: 0, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center',
      }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>處理狀態</InputLabel>
          <Select value={filterStatus} label="處理狀態" onChange={e => setFilterStatus(e.target.value)}>
            <MenuItem value="all">全部</MenuItem>
            {Object.entries(STATUS_LABEL).map(([val, label]) => (
              <MenuItem key={val} value={val}>{label}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          size="small" label="開始日期" type="date" value={filterStart}
          onChange={e => setFilterStart(e.target.value)}
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          size="small" label="結束日期" type="date" value={filterEnd}
          onChange={e => setFilterEnd(e.target.value)}
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          size="small" label="關鍵字" placeholder="搜尋事件說明..."
          value={filterKeyword} onChange={e => setFilterKeyword(e.target.value)}
          sx={{ width: 200 }}
        />
        <Button variant="outlined" onClick={applyFilters} sx={{ borderColor: '#2e3f6e', color: '#2e3f6e' }}>
          套用
        </Button>
        <Button variant="text" onClick={resetFilters} sx={{ color: '#64748b' }}>
          重設
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2, flexShrink: 0 }}>載入失敗：{error}</Alert>}

      {/* DataGrid */}
      <Box sx={{
        flex: 1, minHeight: 0, bgcolor: 'white', borderRadius: 2,
        border: '1px solid #e2e8f0', overflow: 'hidden', position: 'relative',
      }}>
        {loading && (
          <Box sx={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center', zIndex: 1, bgcolor: 'rgba(255,255,255,0.7)',
          }}>
            <CircularProgress size={32} />
          </Box>
        )}
        <DataGrid
          rows={rows}
          columns={columns}
          rowCount={total}
          paginationMode="server"
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          pageSizeOptions={[20, 50, 100]}
          onRowClick={({ row }) => navigate(`/ai-partner/${partnerId}/issues/${row.id}`)}
          disableRowSelectionOnClick
          sx={{ border: 'none' }}
        />
      </Box>
    </Box>
  )
}
```

- [ ] **Step 3：在瀏覽器驗證前端能顯示資料**

確認後端服務已在執行，然後：

```bash
cd /mnt/c/Users/MP0451.MPINFO/Desktop/code\ test/frontend-mui
npm run dev
```

開啟 `http://localhost:5173`，登入後進入安全事件清單頁。

預期：
- 若 DB 有 security_events 資料 → 顯示事件列表
- 若 DB 空白 → 顯示空表格（無 console error）
- 調整篩選後點「套用」→ 重新 fetch 並顯示結果

- [ ] **Step 4：commit**

```bash
git add frontend-mui/vite.config.js \
        frontend-mui/src/pages/AiPartner/IssueList.jsx
git commit -m "feat: connect IssueList to real API with server-side pagination and filters"
```

---

## Task 11：Docker Compose 完整啟動驗證

**目的：** 確認 5 個 container 全部正常，Flash Task 可手動觸發。

---

- [ ] **Step 1：啟動全部服務**

```bash
cd "/mnt/c/Users/MP0451.MPINFO/Desktop/code test"
docker compose up -d --build
```

- [ ] **Step 2：確認所有 container 健康**

```bash
docker compose ps
```

預期：5 個 container 狀態都是 `running`（db、redis 顯示 `healthy`）

- [ ] **Step 3：跑 Alembic migration（若尚未跑過）**

```bash
docker compose run --rm api alembic upgrade head
```

- [ ] **Step 4：確認 API 服務正常**

```bash
curl http://localhost:8000/health
```

預期：`{"status": "ok"}`

- [ ] **Step 5：手動觸發 Flash Task 驗證管線**

```bash
docker compose exec worker celery -A app.worker call app.tasks.flash_task.run_flash_task
```

- [ ] **Step 6：查看 Worker log 確認執行**

```bash
docker compose logs worker --tail 50
```

預期看到：`SSB 登入成功`、`chunk 0 成功`（或 SSB 連線錯誤訊息，代表 task 有觸發到）

- [ ] **Step 7：查詢 DB 確認資料寫入**

```bash
docker compose exec db psql -U mpbox -d mpbox \
  -c "SELECT id, status, records_fetched, chunks_total FROM log_batches ORDER BY id DESC LIMIT 5;"
```

- [ ] **Step 8：commit**

```bash
git add .
git commit -m "chore: verify full Docker Compose pipeline end-to-end"
```

---

## Task 12：AI 交接文件（CLAUDE.md）

**目的：** 寫一份完整說明文件，讓未來任何人（或 AI）從零開始都能理解這個系統並接手工作。

**Files:**
- Create: `CLAUDE.md`（專案根目錄）

---

- [ ] **Step 1：建立 CLAUDE.md**

以下是文件框架，請依實際實作結果填寫確切的 logspace 名稱、實際路徑等細節：

```markdown
# MP-Box 系統說明 — AI 交接文件

> 這份文件是寫給未來接手這個專案的 AI（或人類開發者）看的。
> 假設你完全不了解這個系統，從頭讀起就能理解每個部分在做什麼。

## 這個系統在做什麼？

MP-Box 是一個資安監控平台。它的核心功能是：

1. 每 10 分鐘從公司的 log 伺服器（SSB）拉取最新的系統 log
2. 用 Claude AI（快速分析版 Haiku）判斷哪些 log 代表資安威脅
3. 每天凌晨再用更強大的 Claude AI（Sonnet）把一整天的分析結果彙整成「安全事件清單」
4. 資安專家早上上班打開系統，就能看到昨晚 AI 整理好的事件，依嚴重度排列，決定要先處理哪一個

---

## 資料流（從來源到畫面）

```
公司設備（防火牆、伺服器）
  → syslog 協定 → SSB（syslog-ng Store Box, 192.168.10.48）
  → REST API（每 10 分鐘）→ Celery Flash Task
  → Claude Haiku 分析 → flash_results DB
  → 每日凌晨 2:00 → Celery Pro Task
  → Claude Sonnet 彙整 → security_events DB
  → GET /api/events → 前端安全事件清單頁
```

---

## 目錄結構說明

```
/（專案根目錄）
├── docker-compose.yml     # 一鍵啟動所有服務
├── CLAUDE.md              # 你正在讀的這份文件
├── backend/               # Python FastAPI 後端
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env               # 機密設定（不進 git！）
│   ├── .env.example       # .env 的範本
│   └── app/
│       ├── main.py        # FastAPI 入口，註冊所有 API router
│       ├── worker.py      # Celery 設定，定義排程
│       ├── core/config.py # 讀取 .env 設定（Settings class）
│       ├── db/session.py  # PostgreSQL 連線（SessionLocal, Base）
│       ├── models/        # SQLAlchemy ORM（資料庫 table 定義）
│       │   ├── user.py    # 使用者、角色
│       │   └── security_event.py  # 5 張新 table（見下方說明）
│       ├── schemas/       # Pydantic schema（API 輸出入格式）
│       ├── api/           # REST API endpoint
│       │   ├── auth.py    # 登入/登出
│       │   ├── deps.py    # get_current_user（JWT 驗證）
│       │   └── events.py  # 安全事件 CRUD
│       ├── services/      # 外部服務封裝
│       │   ├── ssb_client.py   # SSB 拉 log
│       │   ├── claude_flash.py # Claude Haiku 呼叫
│       │   └── claude_pro.py   # Claude Sonnet 呼叫
│       └── tasks/         # Celery 排程 task
│           ├── flash_task.py  # 每 10 分鐘
│           └── pro_task.py    # 每日 02:00
└── frontend-mui/          # React 前端
    └── src/pages/AiPartner/
        └── IssueList.jsx  # 安全事件清單頁（串接真實 API）
```

---

## 資料庫 Table 說明

### log_batches
記錄每次從 SSB 拉 log 的批次。每 10 分鐘一筆。
- `status`：pending → running → success / failed
- 如果 failed，下次 Flash Task 會自動補跑

### flash_results
每個 chunk（500 筆 log）送給 Claude Haiku 的結果。
- `events`：JSONB 陣列，每筆是一個資安事件的結構化描述
- 一個 batch 對應多個 flash_results

### security_events
每日凌晨由 Pro Task 彙整的最終事件。前端看到的就是這張 table。
- `star_rank`：1-5 星，越高越嚴重
- `current_status`：pending/investigating/resolved/dismissed
- `match_key`：事件的唯一識別 key，用來去重和追蹤延續事件

### daily_analysis
Pro Task 每天執行一次，這張 table 記錄每次執行狀態。

### event_history
記錄資安專家對事件的操作（改狀態、指派、留言）。

---

## 環境建置（從零開始）

### 前置需求
- Docker Desktop（需在 WSL2 中能執行 `docker` 指令）
- Node.js 18+（前端開發用）

### 步驟

```bash
# 1. 複製 .env 範本並填入實際值
cp backend/.env.example backend/.env
# 編輯 .env，填入 ANTHROPIC_API_KEY、SSB_USERNAME、SSB_PASSWORD 等

# 2. 啟動所有後端服務
docker compose up -d --build

# 3. 跑資料庫 migration（第一次才需要）
docker compose run --rm api alembic upgrade head

# 4. 啟動前端
cd frontend-mui
npm install
npm run dev
```

開啟 http://localhost:5173 就能看到前端。

---

## 重要設定說明

| 設定 | 說明 | 在哪裡改 |
|------|------|----------|
| SSB_LOGSPACE | SSB 的 logspace 名稱 | backend/.env |
| SSB_SEARCH_EXPRESSION | log 過濾條件 | backend/.env 或 config.py 的預設值 |
| FLASH_CHUNK_SIZE | 每個 chunk 幾筆 log | backend/.env |
| FLASH_INTERVAL_MINUTES | Flash Task 間隔（分鐘） | backend/.env |
| PRO_TASK_HOUR / MINUTE | Pro Task 執行時間 | backend/.env |

---

## 常見問題

**Q: Flash Task 跑了但 flash_results 都是 failed？**
查看 worker log：`docker compose logs worker --tail 100`
常見原因：ANTHROPIC_API_KEY 未設定、Claude API 回傳非 JSON。

**Q: SSB 登入失敗？**
確認 SSB_USERNAME、SSB_PASSWORD、SSB_HOST 正確。
注意：SSB 有暴力保護，10 次錯誤/60 秒 → 封鎖 5 分鐘。

**Q: security_events 沒有資料？**
Pro Task 每日凌晨才跑。手動觸發：
`docker compose exec worker celery -A app.worker call app.tasks.pro_task.run_pro_task`

**Q: 前端看不到資料？**
確認 backend/.env 的 DATABASE_URL 指向 `db`（Docker 服務名稱），不是 `localhost`。

---

## 下一步工作（Epic 2）

- 事件詳情頁（IssueDetail.jsx）完整功能：指派人、處置紀錄 tab
- 相似案例 tab
- 通知功能（高嚴重度事件自動通知）
```

- [ ] **Step 2：commit**

```bash
git add CLAUDE.md
git commit -m "docs: add AI handoff document with full system overview"
```

---

## 完成

所有 task 完成後，整個系統應該可以：
1. `docker compose up -d` 啟動後端
2. `npm run dev` 啟動前端
3. Celery Beat 每 10 分鐘自動從 SSB 拉 log 送 Claude Haiku 分析
4. 每天凌晨 02:00 自動彙整成安全事件清單
5. 前端 IssueList 頁面顯示真實的 AI 分析結果
