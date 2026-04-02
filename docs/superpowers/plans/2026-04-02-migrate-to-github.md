# Code Test → P1-code 遷移計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 `code test`（本地工作目錄）的所有成果搬移到 `P1-code`（GitHub 官方 repo），並正確整合文件。

**Architecture:** 單向搬移，不合併 git history。在 P1-code 開 chore branch → 複製檔案 → 處理衝突合併 → commit → push → PR。

**Tech Stack:** Python/FastAPI、React/MUI、PostgreSQL/Alembic、Celery/Redis、Claude API

---

## 路徑說明

- `LOCAL` = `/mnt/c/Users/MP0451.MPINFO/Desktop/code test`
- `GITHUB` = `/mnt/c/Users/MP0451.MPINFO/OneDrive - M-Power Information Co. Ltd/AIDC_Github/P1-code`

---

## 遷移地圖（搬什麼、放哪裡）

### 文件類

| 來源（LOCAL） | 目的地（GITHUB） | 處理方式 |
|---|---|---|
| `CLAUDE.md` | `SYSTEM.md` | 改名複製 |
| `系統入門導覽.md` | `docs/系統入門導覽.md` | 直接複製 |
| `GITHUB/CLAUDE.md` | `GITHUB/CLAUDE.md` | 加一行指向 SYSTEM.md |

### Backend 新增檔案（直接複製）

| 來源（LOCAL） | 目的地（GITHUB） |
|---|---|
| `backend/app/services/ssb_client.py` | `backend/app/services/ssb_client.py` |
| `backend/app/services/claude_flash.py` | `backend/app/services/claude_flash.py` |
| `backend/app/services/claude_pro.py` | `backend/app/services/claude_pro.py` |
| `backend/app/services/log_preaggregator.py` | `backend/app/services/log_preaggregator.py` |
| `backend/app/services/__init__.py` | `backend/app/services/__init__.py` |
| `backend/app/tasks/flash_task.py` | `backend/app/tasks/flash_task.py` |
| `backend/app/tasks/pro_task.py` | `backend/app/tasks/pro_task.py` |
| `backend/app/tasks/__init__.py` | `backend/app/tasks/__init__.py` |
| `backend/app/worker.py` | `backend/app/worker.py` |
| `backend/app/models/security_event.py` | `backend/app/models/security_event.py` |
| `backend/app/schemas/security_event.py` | `backend/app/schemas/security_event.py` |
| `backend/app/api/events.py` | `backend/app/api/events.py` |
| `backend/alembic/versions/4ccbef57de2b_add_security_event_tables.py` | 同路徑 |
| `backend/scripts/run_pipeline.py` | `backend/scripts/run_pipeline.py` |
| `backend/scripts/run_planb_comparison.py` | `backend/scripts/run_planb_comparison.py` |

> **不複製** `backend/scripts/planb_result.json`（測試產出物，非程式碼）

### Backend 需要合併的檔案

| 檔案 | 差異說明 |
|---|---|
| `backend/app/core/config.py` | LOCAL 多了 SSB/Anthropic/Celery/Analysis 設定；GITHUB 多了 Vercel CORS |
| `backend/app/main.py` | LOCAL 有 events_router；GITHUB 有 Vercel CORS origins |
| `backend/requirements.txt` | LOCAL 有 celery/anthropic/httpx；GITHUB 有 pytest-cov/ruff |

### Frontend

| 來源 | 目的地 | 處理方式 |
|---|---|---|
| `LOCAL/frontend-mui/src/pages/AiPartner/` | `GITHUB/frontend-mui/src/pages/AiPartner/` | 覆蓋複製（local 版本更完整） |
| 其他 pages | 先 diff 確認再決定 | 見 Task 5 |

### 其他

| 來源 | 目的地 | 處理方式 |
|---|---|---|
| `docker-compose.yml` | `docker-compose.yml` | 直接複製 |
| `API/` 目錄（PDF）| `API/` | 直接複製 |
| `backend/.env.example` | `backend/.env.example` | 合併（加入 SSB/Claude/Celery 變數） |

---

## Task 1：開 Branch

**Files:**
- Modify: `GITHUB/.git/` （branch 操作）

- [ ] **Step 1：進入 P1-code，確認目前狀態**

```bash
cd "/mnt/c/Users/MP0451.MPINFO/OneDrive - M-Power Information Co. Ltd/AIDC_Github/P1-code"
git status
git log --oneline -3
```

Expected：working tree clean，在 main branch。

- [ ] **Step 2：建立 chore branch**

```bash
git checkout -b chore-migrate-code-test
```

- [ ] **Step 3：安裝 pre-commit hooks（P1-code 有 ruff + commitlint）**

```bash
cd backend && pip install pre-commit ruff && cd ..
pre-commit install
cd frontend-mui && npm install && cd ..
```

---

## Task 2：文件遷移

**Files:**
- Create: `GITHUB/SYSTEM.md`
- Create: `GITHUB/docs/系統入門導覽.md`
- Modify: `GITHUB/CLAUDE.md`

- [ ] **Step 1：複製 CLAUDE.md → SYSTEM.md**

```bash
cp "LOCAL/CLAUDE.md" "GITHUB/SYSTEM.md"
```

- [ ] **Step 2：複製 系統入門導覽.md**

```bash
mkdir -p "GITHUB/docs"
cp "LOCAL/系統入門導覽.md" "GITHUB/docs/系統入門導覽.md"
```

- [ ] **Step 3：更新 GITHUB/CLAUDE.md，加入 SYSTEM.md 參照**

在 `GITHUB/CLAUDE.md` 的「## 專案說明」區塊下方新增：

```markdown
## 系統技術文件

MP-Box 的完整系統架構、資料流、事件合併機制，見 [`SYSTEM.md`](./SYSTEM.md)。
```

- [ ] **Step 5：Commit**

```bash
cd GITHUB
git add SYSTEM.md docs/ CLAUDE.md
git commit -m "docs: migrate system docs and superpowers plans from code test"
```

---

## Task 3：Backend 新增檔案

**Files:** 全部為新增，見遷移地圖「Backend 新增檔案」清單

- [ ] **Step 1：建立目錄結構**

```bash
mkdir -p "GITHUB/backend/app/services"
mkdir -p "GITHUB/backend/app/tasks"
mkdir -p "GITHUB/backend/scripts"
```

- [ ] **Step 2：複製 services**

```bash
cp "LOCAL/backend/app/services/__init__.py"        "GITHUB/backend/app/services/"
cp "LOCAL/backend/app/services/ssb_client.py"      "GITHUB/backend/app/services/"
cp "LOCAL/backend/app/services/claude_flash.py"    "GITHUB/backend/app/services/"
cp "LOCAL/backend/app/services/claude_pro.py"      "GITHUB/backend/app/services/"
cp "LOCAL/backend/app/services/log_preaggregator.py" "GITHUB/backend/app/services/"
```

- [ ] **Step 3：複製 tasks**

```bash
cp "LOCAL/backend/app/tasks/__init__.py"    "GITHUB/backend/app/tasks/"
cp "LOCAL/backend/app/tasks/flash_task.py"  "GITHUB/backend/app/tasks/"
cp "LOCAL/backend/app/tasks/pro_task.py"    "GITHUB/backend/app/tasks/"
```

- [ ] **Step 4：複製 worker、models、schemas、api**

```bash
cp "LOCAL/backend/app/worker.py"                    "GITHUB/backend/app/"
cp "LOCAL/backend/app/models/security_event.py"     "GITHUB/backend/app/models/"
cp "LOCAL/backend/app/schemas/security_event.py"    "GITHUB/backend/app/schemas/"
cp "LOCAL/backend/app/api/events.py"                "GITHUB/backend/app/api/"
```

- [ ] **Step 5：複製 alembic migration**

```bash
cp "LOCAL/backend/alembic/versions/4ccbef57de2b_add_security_event_tables.py" \
   "GITHUB/backend/alembic/versions/"
```

- [ ] **Step 6：複製 scripts**

```bash
cp "LOCAL/backend/scripts/run_pipeline.py"         "GITHUB/backend/scripts/"
cp "LOCAL/backend/scripts/run_planb_comparison.py" "GITHUB/backend/scripts/"
```

- [ ] **Step 7：Commit**

```bash
cd GITHUB
git add backend/app/services/ backend/app/tasks/ backend/app/worker.py \
        backend/app/models/security_event.py backend/app/schemas/security_event.py \
        backend/app/api/events.py backend/alembic/versions/4ccbef57de2b_* \
        backend/scripts/
git commit -m "feat: add SSB pipeline, Celery tasks, Claude services, security events API"
```

---

## Task 4：Backend 合併檔案

**Files:**
- Modify: `GITHUB/backend/app/core/config.py`
- Modify: `GITHUB/backend/app/main.py`
- Modify: `GITHUB/backend/requirements.txt`
- Modify: `GITHUB/backend/.env.example`

- [ ] **Step 1：合併 config.py**

開啟 `GITHUB/backend/app/core/config.py`，在現有設定後（`JWT_EXPIRE_MINUTES` 之後）加入：

```python
    # SSB
    SSB_HOST: str = "https://192.168.10.48"
    SSB_USERNAME: str = ""
    SSB_PASSWORD: str = ""
    SSB_LOGSPACE: str = ""
    SSB_SEARCH_EXPRESSION: str = (
        "nvpair:.sdata.win@18372.4.event_id=4625 OR "
        "nvpair:.sdata.win@18372.4.event_id=4648 OR "
        "nvpair:.sdata.win@18372.4.event_id=4720 OR "
        "nvpair:.sdata.win@18372.4.event_id=4722 OR "
        "nvpair:.sdata.win@18372.4.event_id=4725 OR "
        "nvpair:.sdata.win@18372.4.event_id=4740 OR "
        "nvpair:.sdata.forti.action=deny OR "
        "nvpair:.sdata.forti.level=warning"
    )
    SSB_SEARCH_EXPRESSION_WINDOWS_ONLY: str = (
        "nvpair:.sdata.win@18372.4.event_id=4625 OR "
        "nvpair:.sdata.win@18372.4.event_id=4648 OR "
        "nvpair:.sdata.win@18372.4.event_id=4720 OR "
        "nvpair:.sdata.win@18372.4.event_id=4722 OR "
        "nvpair:.sdata.win@18372.4.event_id=4725 OR "
        "nvpair:.sdata.win@18372.4.event_id=4740 OR "
        "nvpair:.sdata.win@18372.4.event_id=4719 OR "
        "nvpair:.sdata.win@18372.4.event_id=4726 OR "
        "nvpair:.sdata.win@18372.4.event_id=4728 OR "
        "nvpair:.sdata.win@18372.4.event_id=4732 OR "
        "nvpair:.sdata.win@18372.4.event_id=4756 OR "
        "nvpair:.sdata.win@18372.4.event_id=1102"
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

    # Pro Task
    PRO_TASK_HOUR: int = 2
    PRO_TASK_MINUTE: int = 0

    @property
    def effective_search_expression(self) -> str:
        if self.ANALYSIS_MODE == "windows_only":
            return self.SSB_SEARCH_EXPRESSION_WINDOWS_ONLY
        return self.SSB_SEARCH_EXPRESSION
```

- [ ] **Step 2：合併 main.py**

開啟 `GITHUB/backend/app/main.py`，做兩個改動：

1. 在 import 區加入：
```python
from app.api.events import router as events_router
```

2. CORS `allow_origins` 保留 GITHUB 版本（含 Vercel），並加入 local 的 5173：
```python
allow_origins=[
    "http://localhost:5173",
    "https://p1-code.vercel.app",
    "https://*.vercel.app",
],
```

3. 找到 `x = 1` 這行（佔位符），改為：
```python
app.include_router(events_router)
```

- [ ] **Step 3：合併 requirements.txt**

在 `GITHUB/backend/requirements.txt` 末尾加入（`pytest-cov` 和 `ruff` 行之前）：

```
celery[redis]==5.4.0
anthropic>=0.50.0
httpx==0.28.1
```

- [ ] **Step 4：更新 .env.example**

在 `GITHUB/backend/.env.example` 加入：

```
# SSB
SSB_HOST=https://192.168.10.48
SSB_USERNAME=
SSB_PASSWORD=
SSB_LOGSPACE=ALL

# Anthropic
ANTHROPIC_API_KEY=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Pipeline
ANALYSIS_MODE=full
FLASH_INTERVAL_MINUTES=20
```

- [ ] **Step 5：ruff 檢查**

```bash
cd GITHUB/backend
ruff check app/ --fix
ruff format app/
```

若有錯誤，逐一修正後再繼續。

- [ ] **Step 6：Commit**

```bash
cd GITHUB
git add backend/app/core/config.py backend/app/main.py \
        backend/requirements.txt backend/.env.example
git commit -m "feat: merge SSB/Celery/Claude config and events router into backend"
```

---

## Task 5：Frontend 遷移

**Files:**
- Modify: `GITHUB/frontend-mui/src/pages/AiPartner/`

- [ ] **Step 1：比較 AiPartner 頁面差異**

```bash
diff "LOCAL/frontend-mui/src/pages/AiPartner/IssueList.jsx" \
     "GITHUB/frontend-mui/src/pages/AiPartner/IssueList.jsx" | head -30
diff "LOCAL/frontend-mui/src/pages/AiPartner/IssueDetail.jsx" \
     "GITHUB/frontend-mui/src/pages/AiPartner/IssueDetail.jsx" | head -30
```

確認 local 版本有完整的 API 整合（`/api/events`）。

- [ ] **Step 2：複製 AiPartner 頁面**

```bash
cp "LOCAL/frontend-mui/src/pages/AiPartner/IssueList.jsx" \
   "GITHUB/frontend-mui/src/pages/AiPartner/"
cp "LOCAL/frontend-mui/src/pages/AiPartner/IssueDetail.jsx" \
   "GITHUB/frontend-mui/src/pages/AiPartner/"
cp "LOCAL/frontend-mui/src/pages/AiPartner/AiPartner.jsx" \
   "GITHUB/frontend-mui/src/pages/AiPartner/"
```

- [ ] **Step 3：比較其他差異較大的頁面**

```bash
diff "LOCAL/frontend-mui/src/pages/Login/Login.jsx" \
     "GITHUB/frontend-mui/src/pages/Login/Login.jsx"
```

若 local 版本有 JWT token 整合邏輯，覆蓋；若差不多，跳過。

- [ ] **Step 4：Prettier 檢查**

```bash
cd GITHUB/frontend-mui
npx prettier --check src/pages/AiPartner/
```

若有格式問題：`npx prettier --write src/pages/AiPartner/`

- [ ] **Step 5：Commit**

```bash
cd GITHUB
git add frontend-mui/src/pages/AiPartner/
git commit -m "feat: update AiPartner pages with SSB pipeline integration and full UI"
```

---

## Task 6：其他檔案

**Files:**
- Create: `GITHUB/docker-compose.yml`
- Create: `GITHUB/API/`

- [ ] **Step 1：複製 docker-compose.yml**

```bash
cp "LOCAL/docker-compose.yml" "GITHUB/docker-compose.yml"
```

- [ ] **Step 2：複製 API 文件目錄**

```bash
cp -r "LOCAL/API/" "GITHUB/API/"
```

> **注意：** PDF 檔案較大，確認 .gitignore 沒有排除 PDF 再 commit。

- [ ] **Step 3：確認 .gitignore**

```bash
cat "GITHUB/.gitignore" | grep -E "pdf|API"
```

若有排除規則，在此步驟決定是否要把 API/ 加進 .gitignore 例外。

- [ ] **Step 4：Commit**

```bash
cd GITHUB
git add docker-compose.yml API/
git commit -m "chore: add docker-compose and SSB API reference docs"
```

---

## Task 7：驗證與收尾

- [ ] **Step 1：確認 backend 可以啟動**

```bash
cd GITHUB/backend
source venv/bin/activate  # 或建新 venv
pip install -r requirements.txt
python -c "from app.core.config import settings; print(settings.ANALYSIS_MODE)"
```

Expected：`full`

- [ ] **Step 2：確認 alembic migration chain 正確**

```bash
cd GITHUB/backend
alembic history
```

Expected：三條 migration 按順序（users/roles → token_blacklist → security_events）

- [ ] **Step 3：確認 frontend 可以啟動**

```bash
cd GITHUB/frontend-mui
npm run dev
```

Expected：無 compile error，瀏覽器可打開

- [ ] **Step 4：確認 git log 乾淨**

```bash
cd GITHUB
git log --oneline chore-migrate-code-test ^main
```

Expected：看到 Task 2-6 的 commit，無意外檔案。

- [ ] **Step 5：Push branch**

```bash
cd GITHUB
git push -u origin chore-migrate-code-test
```

- [ ] **Step 6：開 PR**

```bash
gh pr create \
  --title "chore: migrate code test pipeline to P1-code" \
  --body "將 code test 本地工作目錄的 SSB pipeline、Claude 整合、前端 AiPartner 頁面遷移至正式 repo。

## 變更摘要
- 新增 SSB client、Celery tasks、Claude Flash/Pro services
- 新增 security_events alembic migration
- 更新 AiPartner 前端頁面（IssueList、IssueDetail）
- 新增系統文件 SYSTEM.md（原 CLAUDE.md）
- 合併 config、main、requirements

## 測試方式
- \`python -c \"from app.core.config import settings; print(settings.ANALYSIS_MODE)\"\`
- \`alembic history\`（確認 migration chain）
- \`npm run dev\`（確認前端無 compile error）" \
  --base main
```

---

## 注意事項

1. **venv 不複製**：`backend/venv/` 不搬，GITHUB 端重新 `pip install`
2. **.env 不複製**：機密檔案，只更新 `.env.example`
3. **planb_result.json 不複製**：測試產出物
4. **node_modules 不複製**：GITHUB 端重新 `npm install`
5. **pre-commit hooks**：P1-code 有 ruff + commitlint，每次 commit 前先跑 `ruff check` + `ruff format`
6. **commit message 格式**：`{type}({scope}): 說明`（commitlint 會擋不符合的格式）
