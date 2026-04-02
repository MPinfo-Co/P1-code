# 設計規格：安全事件清單 — SSB + Claude AI 完整實作

> **日期**：2026-03-31
> **Epic**：MPinfo-Co/P1-project#50
> **參考文件**：TDD.md / business-logic.md / SD-WBS.md / entity-analysis.md
> **UI 基準**：MP-Box_資安專家_v73_claude.html

---

## 1. 範圍（Scope）

本規格涵蓋從 SSB syslog 資料來源到前端安全事件清單頁的完整端對端實作，包含：

- Docker Compose 基礎設施（PostgreSQL + Redis + FastAPI + Celery Worker + Celery Beat）
- SSB REST API Client（認證、分頁拉取、search_expression 過濾）
- Celery Flash Task（每 10 分鐘，Claude Haiku 分析）
- Celery Pro Task（每日 02:00，Claude Sonnet 彙整）
- 5 張 DB table 的 Alembic migration
- 後端 REST API（GET/PATCH /api/events + POST /history）
- 前端 IssueList.jsx 從 mock data 改為串接真實 API

**不含範圍（Epic 2）**：事件詳情頁 tab 完整功能、相似案例、IssueDetail 頁的完整 PATCH/history 流程。

---

## 2. 架構概覽

```
FortiGate / Windows Server / AD Server
  ↓ syslog UDP/TCP 514
SSB (192.168.10.48) — 每日約 600 萬筆原始 log
  ↓ REST API（每 10 分鐘，Celery Beat）
Flash Task：search_expression 過濾 → 約 4.2 萬筆/10分鐘
  ↓ 切分 chunk（500 筆/chunk）→ 順序處理
Claude Haiku（claude-haiku-4-5-20251001）— 快速分析
  ↓ events JSON（star_rank / title / match_key / ioc_list / mitre_tags）
flash_results table（JSONB 暫存）
  ↓ 每日 02:00，Celery Beat
Pro Task：match_key 分群 → 去重彙整
  ↓
Claude Sonnet（claude-sonnet-4-6）— 深度分析
  ↓
security_events table（最終事件快照）
  ↓ GET /api/events
前端 IssueList.jsx（React + MUI DataGrid）
```

---

## 3. 基礎設施：Docker Compose

**5 個 services：**

| Service | Image | 說明 |
|---------|-------|------|
| db | postgres:15 | PostgreSQL，volume pgdata，health check |
| redis | redis:7 | Celery broker & result backend |
| api | backend（build） | uvicorn app.main:app，port 8000 |
| worker | backend（build） | celery -A app.worker worker |
| beat | backend（build） | celery -A app.worker beat |

`api`、`worker`、`beat` 共用同一份 backend 程式碼，依賴 `db` 和 `redis` health check 通過後才啟動。

前端繼續使用 `npm run dev`，不納入 Docker Compose。

---

## 4. 後端目錄結構（新增）

```
backend/app/
├── worker.py              # Celery app 設定 + Beat 排程定義
├── core/config.py         # 新增 SSB_* / ANTHROPIC_API_KEY env vars
├── models/
│   └── security_event.py  # SecurityEvent, LogBatch, FlashResult,
│                          # DailyAnalysis, EventHistory ORM models
├── schemas/
│   └── security_event.py  # Pydantic schema（API request/response）
├── services/
│   ├── ssb_client.py      # SSB 認證 + 分頁拉取
│   ├── claude_flash.py    # Claude Haiku 呼叫 + prompt
│   └── claude_pro.py      # Claude Sonnet 呼叫 + prompt
├── tasks/
│   ├── flash_task.py      # 每 10 分鐘 Celery task
│   └── pro_task.py        # 每日 02:00 Celery task
└── api/
    └── events.py          # REST API endpoints
```

---

## 5. DB Schema（5 張新 Table）

### log_batches
每次 Flash Task 的批次紀錄，用於補跑追蹤。

```sql
CREATE TABLE log_batches (
    id              BIGSERIAL PRIMARY KEY,
    time_from       TIMESTAMP NOT NULL,
    time_to         TIMESTAMP NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    records_fetched INT NOT NULL DEFAULT 0,
    chunks_total    INT NOT NULL DEFAULT 0,
    chunks_done     INT NOT NULL DEFAULT 0,
    retry_count     INT NOT NULL DEFAULT 0,
    error_message   TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### flash_results
每個 chunk 的 Claude Haiku 輸出。

```sql
CREATE TABLE flash_results (
    id            BIGSERIAL PRIMARY KEY,
    batch_id      BIGINT NOT NULL REFERENCES log_batches(id) ON DELETE CASCADE,
    chunk_index   INT NOT NULL,
    chunk_size    INT NOT NULL,
    events        JSONB NOT NULL DEFAULT '[]',
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    processed_at  TIMESTAMP,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**events JSONB 單筆結構：**
```json
{
  "star_rank": 4,
  "title": "帳號 MP0263 異常登入嘗試",
  "affected_summary": "MP0263（異常登入）",
  "affected_detail": "【受影響對象】MP0263\n【攻擊來源】172.18.1.84\n【攻擊行為】短時間內多次登入失敗\n【時間範圍】09:00–09:10",
  "match_key": "MP0263_login_failure_172.18.1.84",
  "log_ids": ["813298855461315879"],
  "ioc_list": ["172.18.1.84"],
  "mitre_tags": ["T1110"]
}
```

### security_events
Pro Task 彙整後的最終事件，前端清單頁資料來源。

```sql
CREATE TABLE security_events (
    id                BIGSERIAL PRIMARY KEY,
    event_date        DATE NOT NULL,
    date_end          DATE,
    star_rank         SMALLINT NOT NULL CHECK (star_rank BETWEEN 1 AND 5),
    title             VARCHAR(200) NOT NULL,
    description       TEXT,
    affected_summary  VARCHAR(20) NOT NULL,
    affected_detail   TEXT,
    current_status    VARCHAR(20) NOT NULL DEFAULT 'pending',
    match_key         VARCHAR(200) NOT NULL,
    detection_count   INT NOT NULL DEFAULT 0,
    continued_from    BIGINT REFERENCES security_events(id),
    assignee_user_id  INT REFERENCES users(id),
    suggests          JSONB,
    logs              JSONB,
    ioc_list          JSONB,
    mitre_tags        JSONB,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### daily_analysis
Pro Task 每日執行紀錄。

```sql
CREATE TABLE daily_analysis (
    id                  BIGSERIAL PRIMARY KEY,
    analysis_date       DATE NOT NULL UNIQUE,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    flash_results_count INT NOT NULL DEFAULT 0,
    events_created      INT NOT NULL DEFAULT 0,
    events_updated      INT NOT NULL DEFAULT 0,
    error_message       TEXT,
    started_at          TIMESTAMP,
    completed_at        TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### event_history
安全事件處理日誌。

```sql
CREATE TABLE event_history (
    id          BIGSERIAL PRIMARY KEY,
    event_id    BIGINT NOT NULL REFERENCES security_events(id) ON DELETE CASCADE,
    user_id     INT NOT NULL REFERENCES users(id),
    action      VARCHAR(20) NOT NULL,
    old_status  VARCHAR(20),
    new_status  VARCHAR(20),
    note        TEXT,
    resolved_at TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 6. SSB Client（services/ssb_client.py）

### 認證
```
POST /api/5/login
Body: username=<SSB_USERNAME>&password=<SSB_PASSWORD>
Response: {"result": "<token>", ...}
→ 後續請求帶入 Cookie: AUTHENTICATION_TOKEN=<token>
```

- SSL：`verify=False`（自簽憑證）
- Token 失效時自動重登（401 → re-login → retry）
- 暴力保護：10 次失敗/60 秒 → 封鎖 5 分鐘；登入失敗計數，達閾值前停止重試

### 分頁拉取
```
GET /api/5/search/logspace/filter/<SSB_LOGSPACE>
  ?from=<unix>&to=<unix>&search_expression=<rules>&offset=0&limit=1000
```

offset 累加 1000 直到 result 筆數 < 1000（分頁結束）。

### search_expression 初版規則（FortiGate + Windows）
```
(program("FortiGate") AND (severity(warning,error,critical,emergency) OR
  message("action=deny") OR message("action=block")))
OR
(program("Microsoft-Windows") AND (
  message("EventID: 4624") OR message("EventID: 4625") OR
  message("EventID: 4648") OR message("EventID: 4720") OR
  message("EventID: 4722") OR message("EventID: 4725") OR
  message("EventID: 4740")
))
```

> 實際語法待連上 SSB 後確認欄位格式，可能需微調。

---

## 7. Flash Task（tasks/flash_task.py）

排程：每 `FLASH_INTERVAL_MINUTES`（預設 10）分鐘觸發。

```
1. 補跑檢查：查最新 failed log_batch → 若存在先補跑
2. 建立新 log_batch（status: running）
3. SSB Client 分頁拉取（time_from = 上次 to, time_to = now）
4. 切分 chunks（每 FLASH_CHUNK_SIZE=500 筆）
5. 逐一送 Claude Haiku（順序處理）：
   - 成功 → 寫入 flash_results（status: success）
   - 失敗 → retry 最多 FLASH_MAX_RETRY=3 次
   - 仍失敗 → flash_result status: failed，繼續下一個 chunk
6. 更新 log_batch（status: success / failed）
```

---

## 8. Claude Haiku Prompt 規範（services/claude_flash.py）

- Model：`claude-haiku-4-5-20251001`
- SDK：`anthropic` Python SDK，`messages.create()`
- 強制 JSON 輸出（system prompt 明確要求只輸出 JSON 陣列，不加說明）

**輸出欄位規範：**

| 欄位 | 規則 |
|------|------|
| `star_rank` | 1（正常資訊）/ 2（低風險）/ 3（中風險）/ 4（高風險）/ 5（緊急）|
| `affected_summary` | 20 字以內，格式：`{對象}（{補充}）` |
| `affected_detail` | 必含【受影響對象】【攻擊行為】，選填【攻擊來源】【時間範圍】|
| `match_key` | 全英文/數字/底線，格式：`{對象}_{攻擊類型}_{來源}` |

若無資安事件輸出空陣列 `[]`。

---

## 9. Pro Task（tasks/pro_task.py）

排程：每日 `PRO_TASK_CRON`（預設 `0 2 * * *`，凌晨 02:00）觸發。

```
1. 建立 daily_analysis（status: running）
2. 讀取當日所有 flash_results WHERE status='success'
3. 展開 events JSONB → 依 match_key 分群
4. 送 Claude Sonnet（claude-sonnet-4-6）：
   - 輸入：各群組事件 + 前一天 security_events（延續判斷）
   - 輸出：去重後最終事件陣列，含 description / suggests / detection_count
5. 寫入 security_events：
   - 同 match_key + 同 event_date → UPDATE
   - 跨日延續 → continued_from = 前一天 event.id，INSERT 新紀錄
   - 全新事件 → INSERT
6. 更新 daily_analysis（status: success，記錄 events_created / events_updated）
```

---

## 10. REST API（app/api/events.py）

所有 endpoints 需要 JWT 驗證（現有 auth middleware），資安專家角色（`can_access_ai=True`）。

### GET /api/events
```
Query params：
  status      string   pending|investigating|resolved|dismissed（逗號分隔多選）
  keyword     string   搜尋 title（ILIKE）
  date_from   string   ISO8601 date
  date_to     string   ISO8601 date
  page        int      預設 1
  page_size   int      預設 20，最大 100

排序：star_rank DESC（固定）

Response 200：
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [ { id, event_date, date_end, star_rank, title, affected_summary,
               detection_count, current_status, assignee_user_id, created_at } ]
}
```

### GET /api/events/{id}
完整事件資料 + `history` 陣列。

### PATCH /api/events/{id}
```
Body: { current_status?, assignee_user_id? }
副作用：自動寫 event_history（action: status_change 或 assign）
Response 200：更新後完整事件資料
```

### POST /api/events/{id}/history
```
Body: { note, resolved_at? }
副作用：寫 event_history（action: comment 或 resolve）
Response 201：新建 event_history
```

---

## 11. 前端改動（IssueList.jsx）

1. 移除對 `IssuesContext`（mock data）的依賴
2. 新增 `useEffect` + `fetch('/api/events?' + queryParams)`
3. 篩選邏輯移至後端（帶 query params），前端只管 UI 狀態
4. 欄位對應：`star_rank`→星等、`title`→事件說明、`event_date`/`date_end`→發生期間、`affected_summary`→影響範圍（Chip）、`current_status`→處理狀態（DB 英文 → UI 中文）、`detection_count`→偵測筆數

---

## 12. 環境變數（新增至 .env.example）

```bash
# SSB
SSB_HOST=https://192.168.10.48
SSB_USERNAME=
SSB_PASSWORD=
SSB_LOGSPACE=                       # 部署後執行 list_logspaces 確認

# Anthropic Claude
ANTHROPIC_API_KEY=

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Flash Task
FLASH_CHUNK_SIZE=500
FLASH_MAX_RETRY=3
FLASH_INTERVAL_MINUTES=10

# Pro Task
PRO_TASK_CRON=0 2 * * *
```

---

## 13. 已知限制 / 待確認

| 項目 | 說明 |
|------|------|
| SSB search_expression 語法 | 待連上 192.168.10.48 後確認實際欄位格式 |
| SSB Logspace 名稱 | 部署後執行 `/search/logspace/list_logspaces` 確認 |
| Claude Haiku 輸出穩定性 | 需測試是否總是輸出合法 JSON，必要時加 retry + JSON 解析保護 |
| Pro Task Sonnet token 用量 | 若當日 flash_results 量大，需評估是否分批送 Sonnet |
| 事件詳情頁 | Epic 2 範圍，本次不實作 |
