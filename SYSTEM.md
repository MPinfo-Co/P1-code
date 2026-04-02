# MP-Box 系統說明 — AI 交接文件

> 這份文件是寫給未來接手這個專案的 AI（或人類開發者）看的。
> 假設你完全不了解這個系統，從頭讀起就能理解每個部分在做什麼。

## 這個系統在做什麼？

MP-Box 是一個資安監控平台。核心功能：

1. 每 10 分鐘從公司的 log 伺服器（SSB）拉取最新的系統 log
2. 程式先從 log 的 dynamic columns 提取欄位，產生穩定的 group_key（用於事件合併）
3. 送精簡後的 log 給 Claude Haiku 快速分析，找出資安事件
4. 程式用 group_key 自動去重合併，維護「當天累計事件」
5. 每天凌晨 02:00 用 Claude Sonnet 對累計事件做最終彙整（修正嚴重度、補充建議處置）
6. 同一個攻擊跨天會自動合併（延伸 date_end、累加 detection_count），不會重複產生事件
7. 資安專家早上上班打開系統，就能看到 AI 整理好的事件，依嚴重度排列

## 資料流

```
公司設備（FortiGate 防火牆、Windows AD Server）
  → syslog → SSB（syslog-ng Store Box, 192.168.10.48）
  → REST API（每 10 分鐘，Celery Beat）
  → Flash Task：search_expression 過濾 → 約 1,800 筆/10分鐘
  → 方案 B 預彙總：FortiGate 1,760 筆 → 24 筆摘要 + Windows 72 筆原樣
  → 合計 ~96 筆送 AI（1 chunk）→ Claude Haiku
  → 程式產 group_key → 覆蓋 AI 的 match_key → attach 原始 log
  → 程式合併（同 group_key 去重）→ 存合併 JSON + 更新當天累計
  → 每日 02:00 → Pro Task 讀當天累計 JSON
  → Claude Sonnet 最終彙整（補 description、suggests、修正 star_rank）
  → 寫入 security_events（同 match_key 未結案事件 → 合併延續；已結案 → 不動）
  → GET /api/events → 前端清單頁 / 詳情頁
```

## 如何重現目前成果（給新接手的人）

### 環境準備

```bash
# 1. PostgreSQL（本機已安裝，或用 Docker）
# 確認 mpbox DB 存在，連線字串在 backend/.env

# 2. Redis
redis-server --daemonize yes

# 3. 後端
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 4. 跑 migration（建 table）
alembic upgrade head

# 5. 前端
cd frontend-mui
npm install
```

### 啟動服務

```bash
# 終端 1：後端 API
cd backend && source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 終端 2：前端
cd frontend-mui && npm run dev

# 瀏覽器打開 http://localhost:5173
# 登入：帳號 Rex（或 users.js 裡的名字），密碼 123
```

### 手動跑一次管線（不用排程）

> 腳本位置：`backend/scripts/run_pipeline.py`
> 流程：SSB 拉 log → 切 chunk 送 Haiku → 程式產 group_key + 合併 → Sonnet 彙整 → 寫入 DB
> **注意：會呼叫 Claude API（Haiku + Sonnet），執行前確認 API 額度**

```bash
cd backend && source venv/bin/activate
python scripts/run_pipeline.py
```

### 清除資料重跑

```sql
-- 連入 DB
PGPASSWORD='@R86o31b5' psql -h localhost -U Robert -d mpbox

-- 清除所有事件資料
DELETE FROM event_history;
DELETE FROM security_events;
DELETE FROM flash_results;
DELETE FROM daily_analysis;
DELETE FROM log_batches;
```

## 事件合併機制（重要）

### group_key（程式產的，穩定）

每條 raw log 進來後，程式從 dynamic_columns 提取欄位產生 group_key：

| 類型 | group_key 格式 | 範例 | 合併範圍 |
|------|---------------|------|---------|
| FortiGate deny（外部來源） | `deny_external_{dstip前三段}` | `deny_external_211.21.43` | 同一目標網段被外部打 |
| FortiGate deny（內部來源） | `deny_internal_{srcip}` | `deny_internal_192.168.10.4` | 各內部 IP 獨立 |
| FortiGate warning | `warning_{subtype}` | `warning_forward` | 同類型警告 |
| Windows 4625 | `4625_{username}` | `4625_administrator` | 同帳號登入失敗（不管哪台主機） |
| Windows 4648 | `4648_{username}` | `4648_msol_2cd93d9077be` | 同帳號明確憑證登入 |
| Windows 4740 | `4740_{username}` | `4740_mp0263` | 同帳號被鎖定 |

**為什麼不讓 AI 產 match_key？** 因為 AI 每次的措辭不穩定，同一個攻擊可能產出不同 key，導致無法合併。

### 合併時機

1. **每個 chunk 分析完** → `_override_match_keys` 用程式的 group_key 覆蓋 AI 的
2. **同一 batch 內** → `_merge_events` 依 group_key 合併（star_rank 取最高、detection_count 加總、logs/ioc/mitre 聯集）
3. **當天累計** → 新 batch merge 進 chunk_index=-1 的累計 JSON
4. **跨日延續** → Pro Task 寫入時找同 match_key 且未結案（pending/investigating）的事件 → UPDATE（date_end 延伸、detection_count 累加）
5. **已結案（resolved/dismissed）** → 不會被覆蓋，永遠保留

### flash_results 的 chunk_index 慣例

| chunk_index | 意義 |
|-------------|------|
| 0, 1, 2... | 個別 chunk 的 Haiku 原始分析結果 |
| 999 | 該 batch 所有 chunk 合併後的結果 |
| -1 | 當天累計（Pro Task 只讀這筆） |

## Log 兩階段過濾（SSB → 程式 → Haiku）

每 10 分鐘的 log 經過兩階段過濾才送 AI，從 ~12.5 萬筆公司全量 log 縮減到 ~77 筆（99.94%）：

```
公司全量 log（~125,000 筆/10分鐘，實測）
  │
  ▼ ── 第一階段：SSB search_expression 過濾 ──
  │    只拉 Windows 資安事件 + FortiGate deny/warning
  │    程式碼：config.py → SSB_SEARCH_EXPRESSION
  │    規則：
  │      Windows：EventID 4625/4648/4720/4722/4725/4740
  │      FortiGate：action=deny OR level=warning
  │
  ~1,700 筆（FortiGate ~1,675 + Windows ~52）
  │
  ▼ ── 第二階段：程式預彙總 + 精簡 ──
  │    程式碼：log_preaggregator.py + claude_flash.py（_slim_log）
  │
  │  ┌─ FortiGate（~1,675 筆 → ~25 筆摘要）
  │  │   不送 message，用 dynamic_columns 結構化欄位
  │  │   依規則分組彙總：
  │  │
  │  │   deny 外部來源（srcip 非 RFC1918）：
  │  │     Group by dstip 前三段 → 如 deny_external_211.21.43
  │  │     摘要含：target_subnet, total_count, unique_src_count,
  │  │            top_src_ips(10), top_dst_ports(5), src_countries(10),
  │  │            time_range, group_key, representative_log_ids(5)
  │  │
  │  │   deny 內部來源（srcip 為 RFC1918）：
  │  │     Group by srcip → 如 deny_internal_192.168.10.31
  │  │     摘要含：srcip, total_count, dst_ips(10), top_dst_ports(5),
  │  │            time_range, group_key, representative_log_ids(5)
  │  │
  │  │   warning：
  │  │     Group by subtype → 如 warning_forward
  │  │     摘要含：subtype, total_count, top_src_ips(5), top_dst_ips(5),
  │  │            top_dst_ports(5), time_range, group_key,
  │  │            representative_log_ids(5)
  │  │
  │  └─ Windows（~52 筆 → 原樣通過，不彙總）
  │      提取 dynamic_columns：event_id, event_username, event_host,
  │                           event_type, event_category
  │      保留精簡 message：砍掉尾巴固定說明文字
  │      （「當...的時候，就會產生這個事件」等模板文字）
  │
  ~77 筆送 AI（1 chunk，~32K tokens）
  │
  ▼ ── Haiku 分析 ──
```

### 實測數據（2026-04-01）

| 階段 | 數量 | 說明 |
|------|------|------|
| SSB 全量 | ~125,000 筆 | 公司所有設備的 syslog |
| 第一階段後 | ~1,727 筆 | search_expression 過濾 |
| 其中 FortiGate | ~1,675 筆 | deny + warning |
| 其中 Windows | ~52 筆 | 6 種 EventID |
| 第二階段後 | **~77 筆** | FortiGate 25 筆摘要 + Windows 52 筆 |
| Token 量 | ~32K | 1 chunk，不需等 rate limit |

### API 費用（2026-04-01 實測比較）

| 指標 | 舊方法（無預彙總） | 方案 B（兩階段過濾） | 節省 |
|------|--------|--------|------|
| 送 AI 筆數 | ~1,400 筆原始 log | ~77 筆（彙總+精簡） | 95% |
| Chunk 數 | 5（每 chunk 等 1 分鐘 rate limit） | 1（秒殺） | — |
| Input tokens | ~505,000 | ~32,000 | 94% |
| 每次 Haiku 費用 | ~$0.55 | ~$0.035 | **94%** |
| 每日 Haiku（144 次） | ~$79 | ~$5.1 | 94% |
| **每月 Haiku** | **~$2,376** | **~$153** | **94%** |
| 每次 Sonnet | ~$0.11 | ~$0.11 | — |
| **每月總計** | **~$2,480** | **~$257** | **90%** |

> 設計文件：`docs/superpowers/specs/2026-04-01-cost-optimization-design.md`
> 測試腳本：`backend/scripts/run_planb_comparison.py`
> 測試結果：`backend/scripts/planb_result.json`

### 方案 B 事件品質實測（2026-04-01）

**舊方法產出 5 事件 vs 方案 B 產出 3 事件：**

| 舊方法事件 | Star | 方案 B 對應 | Star | 說明 |
|---|---|---|---|---|
| 外部掃描 211.21.43 | 4 | 外部掃描 RDP/HTTP | 4 | 合併為 1 筆，更完整 |
| 外部端口掃描 | 3 | ↑ 同上 | — | 預彙總合併同網段 |
| NetBIOS 廣播異常 | 3 | NetBIOS+mDNS 異常 | 3 | 合併內部廣播類 |
| IPv6 mDNS 攔截 | 2 | ↑ 同上 | — | 預彙總合併 |
| VPN UNKNOWN 連線 | 2 | DNS 查詢異常轉發 | 2 | 不同發現 |

**結論：** 方案 B 事件更精簡、合併更合理，核心威脅都有偵測到。舊方法拆得更細但部分事件重複。

### 方案 B 溯源與 match_key 機制

每筆 FortiGate 預彙總摘要包含：
- **`group_key`**：程式產的穩定 key（如 `deny_external_211.21.43`），Prompt 要求 AI 直接用作 match_key
- **`representative_log_ids`**：最多 5 筆代表性 SSB ID，供 `_attach_raw_logs` 溯源回原始 log
- 雙重保險：即使 AI 不聽指令改了 match_key，`_override_match_keys` 也會用 representative_log_ids 對應回 group_key 覆蓋

> 已知限制：VPN 事件可能被 warning 彙總吞掉，個別 VPN 事件細節可能丟失

### 設計決策紀錄

1. **Windows message 不能完全丟掉**：dynamic_columns 沒有來源 IP、失敗原因、目標伺服器等細節，但可砍掉固定說明文字（尾巴的「當...的時候，就會產生這個事件」）
2. **FortiGate message 可以完全不送**：dynamic_columns 已涵蓋所有分析欄位（action、level、srcip、dstip 等）
3. **新 EventID 加入不影響架構設計**：只需改 `SSB_SEARCH_EXPRESSION`，但建議與資安部門確認後再加
4. **量大的 EventID（4768/4769/4776）暫不加**：等方案穩定後再評估，加入方式見「尚未完成 → 中期階段」
5. **方案 A（Windows only）是方案 B（Windows + FortiGate）的子集**：方案 B 包含所有方案 A 的改動，切換只需改 `ANALYSIS_MODE` 環境變數

## 事件摘要格式（AI Prompt 規範）

事件的 `affected_detail` 使用【】標籤格式：

| 標籤 | 必填 | 說明 |
|------|------|------|
| 【異常發現】 | 必填 | 發生什麼事 + 受影響的設備/帳號/IP |
| 【風險分析】 | 必填 | 嚴重性、可能後果、為什麼需要關注 |
| 【攻擊來源】 | 選填 | 有明確來源 IP 或主機時才填 |

## 原始 Log 溯源

每個事件最多保留 5 條原始 SSB log，存在 `security_events.logs`（JSONB）。

每條 log 包含：
- `id` — SSB 的唯一 ID，可回 SSB 查完整記錄
- `timestamp` — Unix timestamp
- `host` — 來源主機
- `program` — 來源程式
- `message` — 完整原始訊息

溯源流程：Haiku 回傳 `log_ids` → `_attach_raw_logs` 用 SSB ID 從原始 chunk 找到對應 log → 存入事件

## SSB 連線與 Log 過濾

### 基本資訊
- **SSB 位址**：192.168.10.48（公司內網，syslog-ng Store Box）
- **API 版本**：`/api/5/`
- **Logspace**：`ALL`（包含所有設備 log）
- **SSL**：自簽憑證，需 `verify=False`
- **暴力保護**：10 次登入失敗 / 60 秒 → 封鎖 5 分鐘

### search_expression 語法

SSB 的 search_expression 是 Web UI 搜尋語法，**不是** syslog-ng filter 語法：

- 純文字：`starting`（搜尋 message 欄位）
- 欄位搜尋：`program:syslog-ng`
- Dynamic column：`nvpair:.sdata.win@18372.4.event_id=4625`
- 組合：用 `OR` 串接（大寫）
- 驗證語法：`GET /api/5/search/logspace/validate?search_expression=...`

### 目前的過濾規則

```
# Windows AD（透過 .sdata.win@18372.4.event_id）
4625 — 登入失敗        4648 — 明確憑證登入/RunAs
4720 — 新建帳號        4722 — 啟用帳號
4725 — 停用帳號        4740 — 帳號鎖定

# FortiGate 防火牆（透過 .sdata.forti.*）
action=deny — 拒絕連線    level=warning — 警告等級
```

### 未納入的 EventID

| EventID | 意義 | 未納入原因 |
|---------|------|-----------|
| 4624 | 登入成功 | 6 小時 6 萬筆，雜訊太多 |
| 4719 | 稽核政策變更 | 實測 0 筆，但發生時重要，可考慮加入 |
| 4672 | 特殊權限指派 | 量大，暫不納入 |

### SSB Dynamic Columns（常用）

FortiGate：`.sdata.forti.action`、`.sdata.forti.level`、`.sdata.forti.srcip`、`.sdata.forti.dstip`、`.sdata.forti.dstport`、`.sdata.forti.srccountry`、`.sdata.forti.subtype`

Windows：`.sdata.win@18372.4.event_id`、`.sdata.win@18372.4.event_username`、`.sdata.win@18372.4.event_source`、`.sdata.win@18372.4.event_host`

### SSB API 參考

- 登入：`POST /api/5/login`
- 查 log：`GET /api/5/search/logspace/filter/<logspace>?from=&to=&search_expression=&offset=&limit=`
- 查筆數：`GET /api/5/search/logspace/number_of_messages/<logspace>?...`
- 查 dynamic columns：`GET /api/5/search/logspace/list_dynamic_columns/<logspace>`
- 驗證語法：`GET /api/5/search/logspace/validate?search_expression=`
- API 文件：`API/REST API Documentation.pdf`、`API/SSB_7.7.0_RPCAPIQuickstartGuide.pdf`

## 目錄結構

```
/（專案根目錄）
├── docker-compose.yml          # 一鍵啟動 5 個服務（Docker 環境）
├── CLAUDE.md                   # 你正在讀的這份文件
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                    # 機密設定（不進 git）
│   ├── .env.example
│   ├── alembic/                # DB migration
│   └── app/
│       ├── main.py             # FastAPI 入口（含 CORS + events router）
│       ├── worker.py           # Celery app + Beat 排程定義
│       ├── core/
│       │   ├── config.py       # Pydantic Settings（所有環境變數）
│       │   ├── deps.py         # get_current_user JWT 驗證
│       │   └── security.py     # JWT/bcrypt
│       ├── db/session.py       # SQLAlchemy engine + SessionLocal
│       ├── models/security_event.py  # LogBatch, FlashResult, SecurityEvent, DailyAnalysis, EventHistory
│       ├── schemas/security_event.py # Pydantic request/response
│       ├── services/
│       │   ├── ssb_client.py        # SSB 認證 + 分頁 + auto-relogin
│       │   ├── claude_flash.py      # Haiku：精簡 log + 分析 + JSON 解析
│       │   ├── claude_pro.py        # Sonnet：彙整 + suggests
│       │   └── log_preaggregator.py # 方案 B：FortiGate 預彙總（deny/warning 分組統計）
│       ├── tasks/
│       │   ├── flash_task.py   # group_key 產生 + chunk 處理 + 合併 + 累計
│       │   └── pro_task.py     # 讀累計 → Sonnet → 寫入/合併 security_events
│       ├── api/events.py       # GET/PATCH/POST 安全事件 API
│       ├── scripts/
│       │   ├── run_pipeline.py          # 手動跑完整管線（SSB → Haiku → Sonnet → DB）
│       │   └── run_planb_comparison.py  # 方案 B 測試 + 成本比較報告
│       └── tests/              # 11 個單元測試
├── frontend-mui/
│   ├── vite.config.js          # /api proxy → localhost:8000
│   └── src/pages/AiPartner/
│       ├── IssueList.jsx       # 清單頁（MUI Table + Popover + Pagination）
│       └── IssueDetail.jsx     # 詳情頁（MUI Tabs/Card + 3 tabs + 聊天面板 placeholder）
├── API/                        # SSB API 參考 PDF
└── docs/superpowers/           # 設計文件 + 實作計畫
```

## 前端頁面

### 清單頁（IssueList.jsx）
- MUI Table（非 DataGrid），欄位：事件說明、處理優先級、發生期間+偵測筆數、影響範圍（Popover）、處理狀態、負責人員、執行動作
- 預設只顯示「未處理 + 處理中」，篩選下拉可選全部/各狀態
- MUI Pagination，每頁 10 筆

### 詳情頁（IssueDetail.jsx）
- 左右分欄：左側 MUI Tabs + 右側聊天面板（placeholder）
- Tab 1 事件詳情：事件摘要（Card）+ 建議處置方法（最推薦/次推薦/可選 + MITRE 溯源按鈕）+ 關聯日誌摘要（SSB ID + metadata + raw message）
- Tab 2 歷史事件：空狀態（Epic 2 範圍）
- Tab 3 處置紀錄：歷史列表（List + Chip）+ 新增表單（日期/備註/變更狀態）

### 狀態顯示對應

| DB 值 | 前端顯示 |
|-------|---------|
| pending | 未處理 |
| investigating | 處理中 |
| resolved | 已處理 |
| dismissed | 擱置 |

### 登入（Login.jsx）
- Mock 登入：帳號用 `frontend-mui/src/data/users.js` 裡的名字，密碼 `123`
- 登入時同時打 `POST /api/auth/login` 拿真實 JWT token 存到 localStorage
- DB 帳號：`admin@mpinfo.com.tw` / `admin123`

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| DATABASE_URL | PostgreSQL 連線字串 | — |
| JWT_SECRET_KEY | JWT 簽名密鑰 | — |
| SSB_HOST | SSB 位址 | https://192.168.10.48 |
| SSB_USERNAME / SSB_PASSWORD | SSB 帳密 | — |
| SSB_LOGSPACE | logspace 名稱 | ALL |
| ANTHROPIC_API_KEY | Claude API key | — |
| CELERY_BROKER_URL | Redis broker | redis://localhost:6379/0 |
| ANALYSIS_MODE | `full`（方案 B）或 `windows_only`（方案 A） | full |
| FLASH_CHUNK_SIZE | chunk 大小 | 300 |
| FLASH_MAX_RETRY | chunk 重試次數 | 3 |
| FLASH_INTERVAL_MINUTES | Flash 間隔 | 10 分鐘 |
| PRO_TASK_HOUR / PRO_TASK_MINUTE | Pro 執行時間 | 2:00 |

## 尚未完成

### 當前階段（先跑穩第一間客戶）

- **新增 EventID** — 加入 4719/4726/4728/4732/4756/1102（量少但重要，零成本）+ 4768/4771（Kerberos，量少）
- **Celery 排程** — 程式碼寫好，但 Worker + Beat 尚未以背景服務啟動
- **跨天合併驗證** — 只跑過單次管線，尚未驗證隔天 Sonnet 的事件延續是否正確
- **歷史事件 tab** — 空狀態，Epic 2 範圍
- **AI 聊天面板** — placeholder，需要接 Claude API 做即時問答
- **前端登入** — 仍為 mock，需改成打真實 API
- **affected_summary 欄位** — 用 ALTER TABLE 從 VARCHAR(20) 改為 VARCHAR(100)，不在 migration 裡
- **Sonnet 會改 match_key** — 已加 fallback logs 機制，但理想上應該在 prompt 中強制 Sonnet 保留程式產的 key

### 中期階段（成本優化 + 使用體驗，在通用化之前處理）

#### API 成本進一步優化（目前 ~$155 USD / ~$4,938 TWD 每月）

| 方式 | 節省幅度 | 說明 |
|------|---------|------|
| **⭐ 拉長間隔 10→20 分鐘** | 省 50%（降至 ~$2,500/月） | 已驗證：凌晨量跟白天差不多（~1,600/10min），20 分鐘仍在 1 chunk 內（~154 筆 < 300），不影響偵測品質。改 `FLASH_INTERVAL_MINUTES=20` 即可。**明天第一件事做這個。** |
| ~~空窗跳過~~ | ~~省 10-30%~~ | 已驗證無效：凌晨 00:00-05:00 平均 1,626 筆/10min，跟白天差不多，外部掃描 24 小時不停 |
| **FortiGate 重複跳過** | 省 20-40% | 跟上一次摘要 pattern 相同就不送，只送有差異的 |
| **Windows 4648 預彙總** | 省少量 token | 4648 佔 Windows 95%，大部分是同帳號重複，可像 FortiGate 一樣彙總 |

#### JWT Token 過期處理

**現狀：** `JWT_EXPIRE_MINUTES = 60`，絕對時間過期（不管有沒有操作，登入 60 分鐘後就失效）

**需處理：**
- 方案 1：加長時間 → `JWT_EXPIRE_MINUTES = 480`（8 小時，上班時間免重登），最簡單
- 方案 2：自動續期（sliding window）→ 前端每次 API 呼叫時後端回新 token，需改前後端

### 下一階段（通用化，可複製到其他客戶）

> **背景：** 目前所有過濾規則、防火牆欄位、預彙總邏輯都 hard-coded 在程式碼中，僅適用於本公司環境（SSB + FortiGate + Windows AD）。要賣給其他客戶必須通用化。
> **時機：** 本公司跑穩、驗證完整個管線後再開始。從實戰經驗抽象出通用架構，避免過早設計出不實用的抽象。

#### 1. 過濾規則可配置化

**現狀（hard-coded）：**
- `config.py` 裡 `SSB_SEARCH_EXPRESSION` 寫死 6 個 Windows EventID + FortiGate deny/warning
- 要改規則就要改程式碼重新部署

**目標：**
- EventID 清單、防火牆過濾條件改為設定檔或 DB 設定表
- 提供管理介面讓資安人員自行新增/移除監控規則
- 每間客戶部署時只需改設定，不動程式碼

#### 2. 預彙總邏輯可插拔化

**現狀（hard-coded）：**
- `log_preaggregator.py` 只認 FortiGate 的 `.sdata.forti.*` 欄位
- 分組規則寫死（deny 外部 by 目標網段、deny 內部 by 來源 IP、warning by subtype）
- `claude_flash.py` 的 `_slim_log` 只認 FortiGate 和 Windows 兩種格式

**目標：**
- 設計 adapter 介面：每種防火牆廠牌（FortiGate、Palo Alto、Cisco ASA 等）一個 adapter
- 每個 adapter 定義：欄位映射（srcip/dstip/action 對應哪個 dynamic_column）、分組規則、精簡邏輯
- 新增廠牌只需寫一個 adapter，不動核心管線程式碼

#### 3. group_key 生成規則可配置化

**現狀（hard-coded）：**
- `flash_task.py::_generate_group_key` 寫死每種 log 類型的 key 格式
- `log_preaggregator.py` 裡各分組函數也寫死 group_key 格式

**目標：**
- group_key 的生成規則跟著 adapter 走
- 每種 adapter 定義自己的分組欄位和 key 格式

#### 4. 高量 EventID 的智慧預過濾

**現狀（不收）：**
- 4624（登入成功，~1,500/10min）、4672（特殊權限，~140/10min）等高量 EventID 完全不收
- 這些裡面藏有潛在異常（異常時段登入、特權帳號異常、Pass-the-Hash 等）

**實測數據（2026-04-01，6 小時）：**

| EventID | 說明 | 6小時量 | 每10分鐘 | 潛在偵測 |
|---------|------|---------|---------|---------|
| 4624 | 登入成功 | 54,382 | ~1,510 | 異常時段登入、異地登入 |
| 4672 | 特殊權限指派 | 5,058 | ~140 | 權限提升攻擊 |
| 4769 | Kerberos 服務票證 | 5,044 | ~140 | Kerberoasting |
| 4776 | NTLM 驗證 | 4,869 | ~135 | Pass-the-Hash |
| 4771 | Kerberos 預驗證失敗 | 1,202 | ~33 | 密碼噴灑 |

**目標：**
- 程式層預過濾：不是全送 AI，而是先用規則篩出「可疑的」再送
- 例如 4624 只送「非上班時間登入」「特權帳號登入」「同帳號短時間多主機登入」
- 預過濾規則也要可配置

#### 5. 非 SSB 環境支援

**現狀：** 只支援 SSB（syslog-ng Store Box）的 REST API 和 dynamic_columns
**目標：**
- 支援其他 log 來源：Elasticsearch、Splunk、Graylog 等
- 沒有 dynamic_columns 時 fallback 到 regex 從 message 提取欄位
- log 來源也是 adapter 模式

## 設計文件

| 文件 | 路徑 |
|------|------|
| 實作計畫（12 tasks） | `docs/superpowers/plans/2026-03-31-security-incident-list.md` |
| 設計規格 | `docs/superpowers/specs/2026-03-31-security-incident-list-design.md` |
| 技術設計（TDD） | `TDD.md` |
| 業務邏輯 | `business-logic.md` |
| 工作分解（WBS） | `SD-WBS.md` |
| UI 雛形 | `MP-Box_資安專家_v73_claude.html` |
| 實體分析 | `entity-analysis.md` |

## Git 提交歷史

```
190bbc4 perf: slim log fields before Haiku, increase chunk size 100→300
3b2fd35 feat: replace match_key with group_key for broader event merging
8669d1f feat: deterministic match_key from log fields + merge ongoing events across days
a903f80 fix: log attachment lookup by SSB id, status labels, default filter
e755867 feat: attach raw SSB logs to events for traceability
331d290 feat: align frontend with prototype, update AI prompts
5ba013d docs: update CLAUDE.md with event merging pipeline
7c18ac0 docs: update CLAUDE.md with full system documentation
aa15dfb feat: implement SSB pipeline, Celery tasks, events API, and frontend integration
61a4581 feat: add security event models and migration (5 new tables)
d6208ab feat: add celery/anthropic/httpx deps and new config settings
65f33b7 fix: harden Docker setup
952e9bf feat: add Docker Compose and Dockerfile for backend services
```
