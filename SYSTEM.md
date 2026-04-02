# MP-Box 系統說明

> 給 AI 和人類開發者的交接文件。

## 系統概述

MP-Box 是資安監控平台，自動從公司 log 伺服器拉取 syslog，用 AI 分析產出資安事件。

**核心流程：**
```
公司設備（FortiGate + Windows AD）
  → syslog → SSB（192.168.10.48）
  → 每 20 分鐘 Celery Beat 觸發 Flash Task
  → SSB API 拉 log → 程式預彙總（~1,800 筆 → ~96 筆）
  → Claude Haiku 分析 → 程式產 group_key + 合併 → 當天累計
  → 每日 02:00 Pro Task → Claude Sonnet 彙整 → 寫入 DB
  → 前端清單頁 / 詳情頁
```

## 快速啟動

```bash
# 後端
cd backend && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd frontend-mui && npm install && npm run dev
# http://localhost:5173，帳號 Rex，密碼 123

# 手動跑一次管線（會呼叫 Claude API，確認額度）
cd backend && python scripts/run_pipeline.py

# 清除資料重跑
PGPASSWORD='@R86o31b5' psql -h localhost -U Robert -d mpbox
DELETE FROM event_history; DELETE FROM security_events;
DELETE FROM flash_results; DELETE FROM daily_analysis; DELETE FROM log_batches;
```

## 事件合併機制

### group_key（程式產的，穩定）

| 類型 | group_key 格式 | 合併範圍 |
|------|---------------|---------|
| FortiGate deny 外部 | `deny_external_{dstip前三段}` | 同目標網段 |
| FortiGate deny 內部（廣播/多播） | `deny_internal_broadcast_p{dstport}` | 同 port 的廣播行為（不分 IP） |
| FortiGate deny 內部（單播） | `deny_internal_{srcip}` | 各內部 IP 獨立 |
| FortiGate warning | `warning_{subtype}` | 同類型警告 |
| Windows | `{event_id}_{username}` | 同帳號同事件類型 |

**廣播/多播判斷：** dstip 為 x.x.x.255（IPv4 廣播）、224.x~239.x（IPv4 多播）、ff 開頭（IPv6 多播）→ 依 port 分組，不分來源 IP。其他 dstip → 依 srcip 分組。這個邏輯通用於所有客戶環境，不需要維護 port 清單。

**為什麼不讓 AI 產 key？** AI 措辭不穩定，同攻擊可能產不同 key，無法合併。Sonnet prompt 已強制保留程式產的 key。

### Sonnet 合併規則（Pro Task）

Sonnet 在每日彙整時會依三個條件判斷是否合併不同 group_key 的事件：
1. **同一類安全現象** — 行為相同（都是廣播被擋、都是掃描等）
2. **同一個根因** — 同一個設定問題或同一波攻擊
3. **同一個處置方式** — 資安專家的處理動作相同

安全閥：單一事件最多合併 5 個不同 group_key，超過代表太寬泛。

### 合併流程

1. chunk 分析完 → `_override_match_keys` 覆蓋 AI 的 key
2. 同 batch 內 → `_merge_events` 依 group_key 合併
3. 當天累計 → merge 進 chunk_index=-1
4. 跨日 → Pro Task 找同 match_key 未結案事件 → UPDATE 延伸
5. 已結案（resolved/dismissed）→ 不覆蓋

### flash_results chunk_index

| chunk_index | 意義 |
|-------------|------|
| 0, 1, 2... | 個別 chunk 原始結果 |
| 999 | batch 合併後結果 |
| -1 | 當天累計（Pro Task 讀這筆） |

## Log 過濾

```
公司全量 ~125,000 筆/10分鐘
  → SSB search_expression 過濾 → ~1,800 筆
  → 程式預彙總 → ~96 筆送 AI（1 chunk, ~32K tokens）
```

### 收的 EventID

**Windows AD：** 4625（登入失敗）、4648（明確憑證登入）、4720（新建帳號）、4722（啟用帳號）、4725（停用帳號）、4740（帳號鎖定）、4719（稽核政策變更）、4726（刪除帳號）、4728/4732/4756（加入安全群組）、1102（安全日誌清除）

**FortiGate：** action=deny、level=warning

### 未收（量太大，需預過濾才能加）

4624（登入成功 ~1,500/10min）、4672（特殊權限 ~140/10min）、4769（Kerberos ~140/10min）、4776（NTLM ~135/10min）

## 目錄結構

```
backend/
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── worker.py                # Celery Beat 排程
│   ├── core/config.py           # 環境變數 + search_expression
│   ├── services/
│   │   ├── ssb_client.py        # SSB API 連線
│   │   ├── claude_flash.py      # Haiku 分析 + log 精簡
│   │   ├── claude_pro.py        # Sonnet 每日彙整
│   │   └── log_preaggregator.py # FortiGate 預彙總
│   ├── tasks/
│   │   ├── flash_task.py        # group_key + 合併 + 累計
│   │   └── pro_task.py          # Sonnet → 寫入 DB
│   └── api/events.py            # 事件 CRUD API
frontend-mui/src/pages/AiPartner/
├── IssueList.jsx                # 清單頁（MUI Table）
└── IssueDetail.jsx              # 詳情頁（MUI Tabs）
```

## 前端

**清單頁：** MUI Table，預設顯示未處理+處理中，每頁 10 筆
**詳情頁：** 左側 3 Tabs（事件詳情/歷史事件/處置紀錄）+ 右側聊天面板 placeholder
**狀態對應：** pending=未處理、investigating=處理中、resolved=已處理、dismissed=擱置
**登入：** Mock 登入（users.js 名字 + 密碼 123），背景拿 JWT

## AI Prompt 規範

事件 `affected_detail` 使用【】標籤：
- 【異常發現】必填 — 發生什麼事 + 受影響對象
- 【風險分析】必填 — 嚴重性與可能後果
- 【攻擊來源】選填 — 有明確來源才填

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| DATABASE_URL | PostgreSQL 連線字串 | — |
| JWT_SECRET_KEY | JWT 密鑰 | — |
| SSB_HOST / SSB_USERNAME / SSB_PASSWORD | SSB 連線 | 192.168.10.48 |
| ANTHROPIC_API_KEY | Claude API key | — |
| CELERY_BROKER_URL | Redis | redis://localhost:6379/0 |
| ANALYSIS_MODE | `full` 或 `windows_only` | full |
| FLASH_INTERVAL_MINUTES | Flash 間隔（分鐘） | 20 |
| FLASH_CHUNK_SIZE | chunk 大小 | 300 |

## 成本

預彙總 + 20 分鐘間隔後：Haiku ~$77/月 + Sonnet ~$3.3/月 ≈ **$80/月**

## 目前狀態（2026-04-02）

### 已完成
- 完整管線（SSB → Haiku → 合併 → Sonnet → DB → 前端）
- 方案 B 預彙總（94% token 節省）
- Flash 間隔 20 分鐘（再省 50%）
- Sonnet match_key 鎖定（prompt 強制保留程式 key）
- 12 個 Windows EventID + FortiGate deny/warning
- group_key 合併 + 跨日延續 + 原始 log 溯源

### 進行中
- **知識庫功能** — 讓 AI 認識公司環境，提升精準度（見下方）

### 待做

**精準度：**
- 知識庫（資產表/帳號表/白名單/網段）→ 塞進 prompt 或程式過濾
- FortiGate 重複跳過（跟上次摘要相同就不送 AI）
- Windows 4648 預彙總（同帳號重複可彙總）

**功能：**
- Celery Worker + Beat 排程啟動
- 跨天合併驗證
- 歷史事件 tab（Epic 2）
- AI 聊天面板
- 前端登入改真實 API

**通用化（跑穩後再做）：**
- 過濾規則/預彙總/group_key 可配置化
- 防火牆 adapter（FortiGate/Palo Alto/Cisco ASA）
- 非 SSB log 來源（Elasticsearch/Splunk）
- 高量 EventID 智慧預過濾

## 知識庫規劃

**問題：** AI 不認識公司環境，無法區分「正常行為」和「異常行為」。例如 AD Server 的境外連線是正常的，但 AI 會報為異常。

**做法：** 使用者在前端維護資料表 → 存 DB → Flash Task 執行時自動注入：

| 資料表 | 程式怎麼用 | 效果 |
|--------|-----------|------|
| 設備資產表（IP → 主機名/用途） | 塞進 Haiku prompt | AI 知道哪台重要 |
| 帳號清單（特權/服務帳號標記） | 塞進 Haiku prompt | 區分正常排程 vs 異常 |
| 安全 IP 白名單 | 程式層過濾，不送 AI | 省成本 + 減噪 |
| 網段規劃表 | 塞進 Haiku prompt | AI 判斷影響範圍 |

**Token 影響：** 知識庫壓縮後 ~500-1,000 tokens，佔每次 ~32K 的 3%，精準度提升遠大於成本增加。

## 參考文件

| 文件 | 位置 |
|------|------|
| UI 雛形 | P1-design repo: `Prototype/MP-Box_資安專家_v73_claude.html` |
| SSB API 文件 | `API/REST API Documentation.pdf` |
| 設計規格 | `docs/superpowers/specs/2026-03-31-security-incident-list-design.md` |
| 成本優化設計 | `docs/superpowers/specs/2026-04-01-cost-optimization-design.md` |
| 實作計畫 | `docs/superpowers/plans/2026-03-31-security-incident-list.md` |
| 成本優化實作 | `docs/superpowers/plans/2026-04-01-cost-optimization-implementation.md` |
