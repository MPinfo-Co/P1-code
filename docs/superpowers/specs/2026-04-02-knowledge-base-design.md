# 知識庫模組設計文件

> 日期：2026-04-02（brainstorm 修訂 2026-04-07）
> 狀態：**已轉交 SA #46，本檔保留為 brainstorm / 決策記錄**

> ⚠️ **正式內容請以 P1-analysis issue-46 為準：**
> - 商業邏輯與資料模型：[`../../../../P1-analysis/issue-46/business-logic.md`](../../../../P1-analysis/issue-46/business-logic.md)
> - SD 工作拆解與 TestPlan：[`../../../../P1-analysis/issue-46/SD-WBS.md`](../../../../P1-analysis/issue-46/SD-WBS.md)
>
> 本檔的用途：保存 brainstorm 討論過程與「為什麼這樣決定」的理由脈絡，規格細節若與 SA 檔案衝突以 SA 為準。

---

## 背景與問題

MP-Box AI 分析時不認識公司環境，無法區分「正常行為」與「異常行為」。例如 AD Server 的境外連線是正常的，但 AI 會報為異常。

**解決方向：** 讓使用者在前端維護公司環境資料，存入 DB，AI 分析時自動注入 prompt 提供脈絡。

---

## 功能範圍（Option B）

1. 使用者可 CRUD 四張知識資料表（資產/帳號/白名單/網段）
2. 知識庫與 AI 夥伴為多對多綁定
3. Flash Task 執行時自動全量注入已綁定知識庫（MVP），架構預留按需查詢空間
4. 存取設定：指定哪些角色可讀取知識庫

---

## 開發流程規劃

採用單一 Epic → SA → SD → PG 直線鏈，不拆分 SD/PG：

```
Epic（知識庫模組）     P1-project
 └── SA Issue         P1-analysis
      └── SD Issue    P1-design
           └── PG Issue  P1-code
```

各階段由 AI 產出草稿，使用者審核後 merge 觸發下游。

---

## 資料模型

### 新增資料表

```
knowledge_bases
  id, name, description, analysis_rules, created_by, created_at, updated_at
  -- analysis_rules: TEXT，自由文字描述「我的環境裡這些屬於正常行為」，
  --                  注入到 Haiku prompt 的【分析規則】段落供 AI 語義判讀。
  --                  詳見「分析規則欄位設計（Pain 2 直接解法）」章節。

kb_assets（設備資產表）
  id, kb_id, ip, hostname, purpose, criticality, notes

kb_accounts（帳號清單）
  id, kb_id, username, account_type (normal/privileged/service), notes

kb_whitelist（安全 IP 白名單）
  id, kb_id, ip_or_cidr, reason, notes

kb_networks（網段規劃表）
  id, kb_id, cidr, zone_name, description, notes

kb_ai_partner_bindings（多對多）
  id, kb_id, ai_partner_type ENUM('security'), enabled, created_at

kb_access_roles（存取設定）
  id, kb_id, role, created_at
```

### 注入機制（Flash Task）

```
Flash Task 執行前：
  1. 查詢 kb_ai_partner_bindings WHERE ai_partner_type='security' AND enabled=true
  2. 取出對應 knowledge_bases 的四張資料表
  3. 壓縮成 ~500-1,000 tokens 的 context 字串
  4. 塞進 Haiku prompt system message
```

詳細的 prompt 結構、白名單標記、context 壓縮格式於下方三個章節定義。

---

## Prompt 結構與快取決策（2026-04-07 brainstorm）

### 結論：本階段不啟用 prompt caching

**查證：**
- 目前 `claude_flash.py` / `claude_pro.py` 都**沒有** `cache_control`，並未在 cache
- Haiku 的 prompt caching 最小門檻為 **2,048 tokens**（Sonnet/Opus 為 1,024）
- 現有 `SYSTEM_PROMPT` ~400-500 tokens + KB context ~950 tokens ≈ **~1,400 tokens**，仍低於 Haiku 門檻，加 `cache_control` 不生效
- Flash Task 每 20 分鐘跑一次：
  - 5m TTL → 每次 cache 已過期，只付 1.25× 寫入成本、零讀取收益 ❌
  - 1h TTL → 3 次中 2 次命中，但寫入成本 2×，需靜態區塊跨過最小門檻才划算
- Pro Task 一天一次，caching 天生無意義

**決策：本階段不引入 `cache_control`**。未來若符合下列任一條件再評估：
1. `SYSTEM_PROMPT + KB` 超過 2,048 tokens
2. Flash 間隔縮短到 < 5 分鐘
3. Anthropic 調降 Haiku 的最小快取門檻

### Prompt 結構調整

Flash Task 的 system message 從單一字串改為 block 陣列，讓靜態指令與動態 KB context 清楚分離：

```python
# Before（現況）
client.messages.create(
    model="claude-haiku-4-5-20251001",
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": prompt_with_logs}],
)

# After（注入 KB）
system_blocks = [
    {"type": "text", "text": SYSTEM_PROMPT_BASE},  # 靜態：模型行為指令
]
if kb_context_text:  # 若有綁定知識庫且非空
    system_blocks.append({"type": "text", "text": kb_context_text})

client.messages.create(
    model="claude-haiku-4-5-20251001",
    system=system_blocks,
    messages=[{"role": "user", "content": prompt_with_logs}],
)
```

**為什麼放 system 而不是 user message：**
- Claude 把 system 視為「身份與背景」，KB 是環境脈絡，語義對齊
- user message 每次都帶 `logs_json` 大量變動，若把 KB 塞進 user，Haiku 可能把 KB 當成 log 的一部分誤判
- 用 block 陣列分離靜態指令與 KB 後，未來要補 `cache_control` 只需在第二個 block 加標記，無需重構
- Sonnet（Pro Task）是否同樣注入，本次未討論，暫不變更（沿用現況）

**降級行為：** 當 KB 綁定為空、所有 KB 內容皆空、或 KB context builder 拋例外時，`system_blocks` 只保留 `SYSTEM_PROMPT_BASE`，分析流程不中斷（對齊驗收條件 3）。

---

## 白名單標記點與彙總策略（2026-04-07 brainstorm）

### 適用範圍

`kb_whitelist`（IP/CIDR 白名單）**僅作用於 FortiGate 三條彙總線**（`deny_external` / `deny_internal` / `warning`）。Windows log 不套用 IP 白名單；Windows 的等效語義透過 `kb_accounts.account_type` 注入 KB context 字串提供（見「KB context 壓縮格式」章節）。

### 標記時機：彙總前 in-place 標記

選擇「彙總前 in-place 標記 + 彙總時統計」方案。流程：

```python
# backend/app/tasks/flash_task.py :: _process_batch()
logs = ssb.fetch_logs(batch.time_from, batch.time_to, ...)

# NEW: 注入白名單前綴（取自綁定的 KB，每次 Flash 載入一次）
whitelist_cidrs = load_kb_whitelist_cidrs(binding)
_mark_whitelist(logs, whitelist_cidrs)  # in-place 對 FortiGate log 設 _whitelisted=True

# 進入既有管線
forti_summaries, windows_logs = preaggregate(logs)
```

**`_mark_whitelist` 規則：**
- 只處理 FortiGate log（dynamic_columns 含 `.sdata.forti.` 前綴的）
- 對每筆 log，檢查 `srcip` 或 `dstip` 任一個落在任何白名單 CIDR → 設 `log["_whitelisted"] = True`
- 用 Python `ipaddress` 模組處理 CIDR；whitelist_cidrs 預先 parse 成 `IPv4Network` / `IPv6Network` 物件清單，避免每筆 log 重新 parse
- Windows log 不檢查、不加欄位
- 效能：~1,800 筆 × ~10 條白名單 = ~18,000 次比對／批，遠低於 Flash Task 整體開銷

### 彙總時統計：群組級欄位

修改 `_aggregate_deny_external` / `_aggregate_deny_internal` / `_aggregate_warning`，每個 summary 新增兩個欄位：

```python
{
  "type": "deny_internal",
  "group_key": "deny_internal_broadcast_p137",
  "total_count": 50,
  "whitelisted_count": 3,         # 新增：群組內被標記的 log 數
  "whitelisted_ratio": 0.06,      # 新增：whitelisted_count / total_count
  "top_src_ips": [...],
  ...
}
```

### Haiku prompt 規則追加

於 `SYSTEM_PROMPT_BASE` 的「規則」段落新增：

> 若彙總摘要的 `whitelisted_ratio >= 0.8`，代表此群組大多來自 KB 白名單（已知良性來源），star_rank 降一階，但異常模式仍須回報；`whitelisted_ratio < 0.8` 時正常判讀。

對應原 spec 的核心精神：**白名單不過濾、不移除，只提供降權脈絡，異常仍須回報**。

### 不外洩保證

`_whitelisted` 是 raw log 的臨時欄位。`_attach_raw_logs` 在組裝事件時只複製固定欄位（`id` / `timestamp` / `host` / `program` / `message`），`_whitelisted` 不會被傳到前端或寫入 DB。

### TestPlan 要點（SD 階段細化）

| ID | 案例 | 預期 |
|----|------|------|
| W1 | 白名單 IP 出現在 `deny_internal` 群組 | summary 含 `whitelisted_count > 0` |
| W2 | 白名單 CIDR `10.1.0.0/16` 命中 `10.1.5.5` | log 被標記 `_whitelisted=True` |
| W3 | 白名單為空（KB 未綁定或 whitelist 表空） | 所有 summary 的 `whitelisted_count = 0`，管線不中斷 |
| W4 | Windows log 通過 `_mark_whitelist` | 不新增 `_whitelisted` 欄位 |
| W5 | `whitelisted_ratio >= 0.8` 的群組 | Haiku 輸出 `star_rank` 較對照組低一階 |
| W6 | `_attach_raw_logs` 後的事件 | 不含 `_whitelisted` 欄位 |

---

## KB context 壓縮格式（2026-04-07 brainstorm）

### 結論：自然語言條列 + 固定 builder 樣板

選擇「自然語言條列」格式（非 JSON、非 Markdown 表格），由程式按固定樣板填入。

**理由：**
1. **Token 效率最高** — 比 JSON 省 30-40%、比 Markdown 表格省 15-20%
2. **Haiku 對中文條列的注意力分布優於 JSON** — 既有 FortiGate 摘要驗證自然語言摘要命中率高於純 JSON
3. **跟 `SYSTEM_PROMPT_BASE` 風格一致** — 既有 prompt 就是中文條列格式
4. **欄位不固定的擔憂由「程式產出」解決** — 不是讓 LLM 產生格式，是 Python builder 按樣板填入，輸出穩定

### Builder 函式介面

```python
# backend/app/services/kb_context_builder.py
def build_kb_context(kbs: list[KnowledgeBase]) -> str:
    """
    將多個綁定的 KB 合併壓縮成自然語言條列字串。
    返回空字串代表「無知識庫」，呼叫端會跳過注入。
    """
```

**為何接受 `list[KnowledgeBase]`：** 對應 KB ↔ AI 夥伴的多對多綁定，一次 Flash Task 可能拉到多份 KB。

### 樣板

```
## 公司環境知識庫

重要資產：
- {ip} = {hostname}（{purpose}，{criticality} 重要性）
- ...

已知帳號：
- {username}（{account_type} 帳號{，備註}）
- ...

安全 IP 白名單（log 已標記 whitelisted_ratio）：
- {ip_or_cidr}（{reason}）
- ...

網段規劃：
- {cidr} = {zone_name}（{description}）
- ...
```

### 規則

| 規則 | 行為 |
|------|------|
| 任一段為空 | 整段省略，不留空標題 |
| `notes` / `description` 等選填欄位為空 | 省略對應括號內容，避免 `（）` 空括號 |
| 多 KB 合併衝突 | 同 `ip` / `username` / `ip_or_cidr` / `cidr` 去重，**後綁定的 KB 覆蓋前者**（簡單規則，避免複雜衝突解析） |
| 條目排序 | assets 依 criticality 高→低；accounts 依 type（privileged → service → normal）；whitelist / networks 依字典序 |
| 硬上限 | 每段最多 50 條，超過取前 50 + 段尾追加「... 還有 N 筆未顯示（請精簡 KB）」 |
| Builder 例外 | catch 所有 Exception → log warning → 回傳 `""`，Flash Task 不中斷 |

### Token 估算（修訂）

| 段落 | 條目數 | 每條平均 tokens | 小計 |
|------|--------|---------------|------|
| 標題 + 段標 | — | — | ~30 |
| 重要資產 | 20 | ~15 | ~300 |
| 已知帳號 | 30 | ~12 | ~360 |
| 白名單 | 10 | ~12 | ~120 |
| 網段規劃 | 10 | ~14 | ~140 |
| **合計** | | | **~950 tokens** |

略高於原 spec 的 ~700 估算，仍 < 1,000 上限，佔每次 ~32K 的約 3%。下方「Token 影響估算」表已更新。

### TestPlan 要點

| ID | 案例 | 預期 |
|----|------|------|
| C1 | 單一 KB，四段都有資料 | 輸出含四段標題與條目 |
| C2 | 單一 KB，僅 assets 段有資料 | 輸出僅含 assets 段，其他段不出現空標題 |
| C3 | 兩個 KB 綁定，重複 IP | 後綁定的覆蓋前者，不重複出現 |
| C4 | assets 條目超過 50 | 截斷並追加「還有 N 筆未顯示」 |
| C5 | KB 全空 / 未綁定 | 回傳 `""`，`system_blocks` 只剩 base |
| C6 | builder 函式拋例外 | 回傳 `""`，Flash Task 仍成功 |
| C7 | 條目有 None / 空字串欄位 | 不出現 `（）` 空括號或 `None` 字樣 |
| C8 | 條目排序 | criticality 高→低、account_type privileged→service→normal |

---

## 分析規則欄位設計（Pain 2 直接解法，2026-04-07 brainstorm）

### 痛點對齊

使用者反映「**AD Server 類事件天天出現但其實是誤報**」。檢視現有 KB 設計後發現：
- `kb_assets` 雖能標記 IP=AD-DC-01、purpose=Domain Controller，但 Haiku 是否能據此自動推論「DC 對外存取 80/443 為 Windows Update 同步」依賴 LLM prior knowledge，**不可靠**
- `kb_whitelist` 只作用於 FortiGate 三線（見上方章節），對 Windows EventID 高量噪音（例如 DC 收到大量 4625 失敗登入）無效

因此原 KB 設計無法直接解決 Pain 2。需要補一個欄位讓使用者**明確告訴 AI**「這些情境是已知正常」。

### 結論：在 `knowledge_bases` 加 `analysis_rules` TEXT 欄位

**選擇原因（vs 其他方案）：**

| 方案 | 維護成本 | 表達彈性 | Schema 變動 | MVP 友善度 |
|------|---------|---------|------------|----------|
| kb_assets 加 `behavior_notes` 欄位 | 高（每筆 asset 都要填） | 受限於單一資產 | `kb_assets` 加欄位 | 中 |
| **knowledge_bases 加 `analysis_rules`** | **低（KB 整體一次）** | **任何規則都能寫** | **單表加欄位** | **高** |
| 獨立 `kb_normal_behaviors` 表 | 低 | 高 | 多一張表 | 低（MVP 過重） |

**選 `analysis_rules`** —— 用一段自由文字承載「跨資產通用規則」，最輕量。

### Schema

```sql
ALTER TABLE knowledge_bases ADD COLUMN analysis_rules TEXT;
```

無預設值、可為 NULL。前端 KB 詳情頁加一個多行文字框「分析規則」供使用者編輯。

### 範例填寫

```
- AD Server (10.1.0.10, 10.1.0.11) 的 4625 高量為一般用戶端登入失敗，視為正常 (star_rank ≤ 2)
- AD Server 對外存取 80/443 為 Windows Update 同步，視為正常
- 備份伺服器 (10.1.0.50) 每晚 02:00-04:00 的 NetBIOS 廣播為備份任務，視為正常
- 員工辦公網段 (10.2.0.0/24) 的 mDNS / LLMNR 廣播為一般使用，star_rank ≤ 2
```

### KB context builder 樣板追加

`build_kb_context` 在輸出尾端追加【分析規則】段落（多 KB 綁定時，每個 KB 的 `analysis_rules` 用空行串接）：

```
## 公司環境知識庫

重要資產：
- ...

已知帳號：
- ...

安全 IP 白名單（log 已標記 whitelisted_ratio）：
- ...

網段規劃：
- ...

【分析規則】
- AD Server (10.1.0.10, 10.1.0.11) 的 4625 高量為一般用戶端登入失敗，視為正常 (star_rank ≤ 2)
- ...
```

**規則：**
- `analysis_rules` 為 NULL 或空字串 → 整段省略
- 多 KB 綁定且都有 `analysis_rules` → 用空行串接，依 KB 綁定順序
- 不去重（規則文字判斷重複難度高，由使用者自管）

### Haiku prompt 規則追加

於 `SYSTEM_PROMPT_BASE` 的「規則」段落新增：

> 若事件符合 KB 提供的【分析規則】所述情境，依規則調整 star_rank（規則寫「視為正常」就降至 1 或 2、寫「star_rank ≤ N」就上限為 N）。規則沒涵蓋的事件正常判讀。

### 與 `kb_whitelist` 的互補關係

兩者**不重複、不衝突**：

| 機制 | 作用層 | 適用 | 確定性 |
|------|--------|------|--------|
| `kb_whitelist` | 程式層（preaggregator 統計 `whitelisted_ratio`） | 僅 FortiGate 三線 | 高（精確 IP/CIDR 比對） |
| `analysis_rules` | LLM 層（Haiku 語義判讀 prompt） | Windows + FortiGate 都適用 | 中（依 Haiku 對自然語言規則的理解） |

例：AD Server 對外 80/443 可以**兩邊都標**：白名單做程式確定性降權；分析規則做語義延伸（例如「同樣的規則也適用於 DR Server 10.1.0.20」這種程式不會自動推論的情境）。

### Token 影響

`analysis_rules` 預期 ~200-400 tokens（10-20 條規則），加上其他段落總和約 **1,200-1,400 tokens**，仍 < 1,500，佔每次 ~32K 的約 4%。下方「Token 影響估算」表已更新。

### TestPlan 要點

| ID | 案例 | 預期 |
|----|------|------|
| R1 | KB 含 `analysis_rules`（10 條規則） | KB context 含【分析規則】段落、規則內容完整出現 |
| R2 | `analysis_rules` 為 NULL | KB context 不含【分析規則】段落 |
| R3 | 兩個 KB 綁定，都有 `analysis_rules` | 兩段以空行串接出現，依綁定順序 |
| R4 | 規則含「視為正常」+ Haiku 收到符合規則的 log | 輸出 `star_rank ≤ 2` |
| R5 | 規則含「star_rank ≤ 3」+ Haiku 收到符合規則的 log | 輸出 `star_rank ≤ 3` |
| R6 | 規則沒涵蓋的事件 | Haiku 正常判讀，不受影響 |
| **R7** | **AD Server EventID 4625 高量場景（對應 Pain 2 真實情境）** | **star_rank 降至 ≤ 2，不被誤報為高風險** |

R7 是 **Pain 2 的端對端驗收案例**，必須在 PG 階段實際跑 Haiku 驗證。

---

## 跨日延續修法（Pain 1 — 跟本 Epic 解耦的獨立 fix）

### 問題重述

使用者反映「**同件事隔天同樣發生但被拆成兩筆事件**」。經查證 `pro_task.py` 與原 spec 後發現：

1. **原 spec（`2026-03-31-security-incident-list-design.md` §5）** 定義 `security_events.continued_from BIGINT` FK 欄位
2. **`claude_pro.py` Sonnet prompt** 已要求輸出 `continued_from_match_key` 欄位
3. **`pro_task.py`（行 97-132）** 完全沒讀取 `continued_from_match_key`，也從未寫入 `continued_from` FK
4. 結果：Sonnet 已正確判斷延續關係，但程式忽略此資訊；當 Sonnet 在不同日選了不同的代表 match_key，`UPDATE` 條件不命中 → INSERT 新事件 → 拆成兩筆

### 修法（與 KB Epic 解耦）

修改 `pro_task.py` 的 existing 查詢條件，把 `continued_from_match_key` 納入候選 keys：

```python
# Before
existing = (
    db.query(SecurityEvent)
    .filter(
        SecurityEvent.match_key == ev["match_key"],
        SecurityEvent.current_status.in_(["pending", "investigating"]),
    )
    .order_by(SecurityEvent.event_date.desc())
    .first()
)

# After
candidate_keys = [ev["match_key"]]
continued_key = ev.get("continued_from_match_key")
if continued_key:
    candidate_keys.append(continued_key)

existing = (
    db.query(SecurityEvent)
    .filter(
        SecurityEvent.match_key.in_(candidate_keys),
        SecurityEvent.current_status.in_(["pending", "investigating"]),
    )
    .order_by(SecurityEvent.event_date.desc())
    .first()
)
```

並在 UPDATE 分支補上 `continued_from` FK 寫入（首次建立延續鏈）。

### 驗收

| ID | 案例 | 預期 |
|----|------|------|
| F1 | 昨天事件 `match_key=A`、今天 `match_key=A` | UPDATE existing（與現況一致） |
| F2 | 昨天 `match_key=A`、今天 `match_key=B` 但 `continued_from_match_key=A` | UPDATE existing（match by A），不 INSERT |
| F3 | 昨天事件 `match_key=A` 已 resolved、今天 `match_key=A` | INSERT 新事件（與現況一致） |
| F4 | Sonnet 沒輸出 `continued_from_match_key` | 行為與現況一致 |
| F5 | F2 case 後 | `continued_from` FK 欄位被填寫 |

### 範圍切割

**此修法不屬於本 KB Epic 範圍**，應另開獨立 fix Issue。理由：
- 跟知識庫的 SA → SD → PG 流程無依賴關係
- 改動局部（單一檔案、無 schema 變動）
- 是修正既有設計死角（`continued_from` 欄位早就存在但沒被使用），不是新功能

本 spec 在此記錄是為了：
1. 讓 KB Epic 的閱讀者知道 Pain 1 已有獨立解法、不要重複設計
2. 確認 KB 的 `analysis_rules` 不需要承擔跨日延續責任

---

## API 規格（概覽，SD 階段細化）

| Method | Path | 說明 |
|--------|------|------|
| GET | `/api/knowledge-bases` | 列表 |
| POST | `/api/knowledge-bases` | 新建 |
| GET | `/api/knowledge-bases/{id}` | 詳情（含四張資料表） |
| PUT | `/api/knowledge-bases/{id}` | 更新基本資料 |
| DELETE | `/api/knowledge-bases/{id}` | 刪除 |
| GET/POST/PUT/DELETE | `/api/knowledge-bases/{id}/assets` | 資產 CRUD |
| GET/POST/PUT/DELETE | `/api/knowledge-bases/{id}/accounts` | 帳號 CRUD |
| GET/POST/PUT/DELETE | `/api/knowledge-bases/{id}/whitelist` | 白名單 CRUD |
| GET/POST/PUT/DELETE | `/api/knowledge-bases/{id}/networks` | 網段 CRUD |
| GET/POST/DELETE | `/api/knowledge-bases/{id}/bindings` | AI 夥伴綁定 |
| GET/POST/DELETE | `/api/knowledge-bases/{id}/access` | 存取角色設定 |

---

## 前端頁面（概覽，SD 階段細化）

現有 `KnowledgeBase/` 頁面結構已符合設計方向：

| Tab | 功能 |
|-----|------|
| 資料表 | 四張資料表的 CRUD（切換 Tab 顯示不同表） |
| 綁定設定 | AI 夥伴多對多綁定管理（取代現有 mock 的「綁定夥伴」欄位） |
| 存取設定 | 角色權限管理 |

知識庫列表頁保持現有卡片設計，搜尋過濾維持。

---

## Token 影響估算

| 項目 | 數量 | Token 估計 |
|------|------|-----------|
| 標題 + 段標 | — | ~30 |
| 資產表（20 筆，含 hostname/purpose/criticality） | ~20 行 | ~300 |
| 帳號清單（30 筆，含 type/note） | ~30 行 | ~360 |
| 白名單（10 筆，含 reason） | ~10 行 | ~120 |
| 網段表（10 筆，含 zone/description） | ~10 行 | ~140 |
| 分析規則（10-20 條自由文字） | — | ~200-400 |
| **合計** | | **~1,200-1,400 tokens** |

佔每次 ~32K tokens 的約 4%，精準度提升遠大於成本增加。詳細格式見「KB context 壓縮格式」與「分析規則欄位設計」章節。

---

## SA 草稿要點

SA 階段 AI 需要產出：

**business-logic.md**
- Use Case：管理員維護知識庫（含 `analysis_rules`） / Flash Task 注入 / 角色權限控制
- ER 圖（文字版，含 `knowledge_bases.analysis_rules` 欄位）
- 注入機制完整邏輯（含失敗降級：知識庫為空時跳過，不中斷分析）
- 白名單處理邏輯：彙總前 in-place 標記 raw log + 彙總時統計群組級 `whitelisted_count` / `whitelisted_ratio`，不過濾；Haiku prompt 指示 `whitelisted_ratio >= 0.8` 時降權但異常仍回報。詳見「白名單標記點與彙總策略」章節
- 分析規則注入邏輯：`build_kb_context` 在輸出尾端追加【分析規則】段落；Haiku prompt 指示依規則調整 star_rank。詳見「分析規則欄位設計」章節

**SD-WBS.md**
- 後端：6 張新 table（含 `knowledge_bases.analysis_rules`）+ Alembic migration + 11 組 API + Flash Task 注入邏輯（KB context builder + 白名單標記）
- 前端：KnowledgeBase 頁面從 mock → 真實 API（3 個 Tab + KB 詳情頁的「分析規則」多行文字框）
- 測試：CRUD + 注入 + 角色存取 + R7 端對端驗收（AD Server 4625 高量場景）

---

## SD 草稿要點

SD 階段 AI 需要產出：

**Spec/**
- 完整 API 規格（request/response schema、錯誤碼）
- 注入 context 的壓縮格式規範

**schema/**
- 6 張新 table 的 DDL

**Prototype/**
- 確認現有 `KnowledgeBase/` mock HTML 是否需要更新

**TestPlan/**
- T1～Tn 測試案例（CRUD × 4 表 + 綁定 + 存取 + 注入驗證）

---

## 驗收條件

1. 使用者可新建知識庫並維護四張資料表（資產/帳號/白名單/網段）
2. 知識庫可綁定 AI 夥伴（多對多），綁定後下次 Flash Task 自動注入
3. 未綁定或空知識庫時，分析流程不受影響（降級跳過）
4. 存取設定可指定角色，無權限角色無法讀取
5. **`analysis_rules` 端對端驗收**：填入「AD Server 4625 高量視為正常」規則，實際跑 Haiku 後對應事件 `star_rank ≤ 2`（對應 R7 案例與 Pain 2）
6. pytest 數量 ≥ TestPlan 案例數，每個 test function 標注 TestPlan ID

---

## 設計決策記錄

| 問題 | 決策 | 理由 |
|------|------|------|
| 白名單實作位置 | 彙總前 in-place 標記 raw log + 彙總時統計群組級欄位 `whitelisted_count` / `whitelisted_ratio`，不過濾；prompt 指示 AI 降低嚴重性但異常仍回報 | 完整可見、不會因 `top_src_ips` 截斷而漏算；異常仍須知道，不能硬過濾。詳見「白名單標記點與彙總策略」章節 |
| 白名單作用範圍 | 僅 FortiGate 三條彙總線；Windows 不套用 IP 白名單 | Windows 的等效語義由 `kb_accounts.account_type` 透過 KB context 字串提供 |
| ai_partner_type | Enum，MVP 只定 `security` | 目前無其他 AI 夥伴，等真的要做再 migration |
| 知識庫刪除邏輯 | 硬刪除 + 二次確認彈窗 + FK cascade | 內部管理員使用，soft delete 增加 MVP 複雜度不值得；彈窗告知影響範圍已足夠 |
| Prompt caching 是否啟用 | **本階段不啟用** | Haiku 最小門檻 2,048 tokens，現有靜態區塊 ~1,400 tokens 低於門檻；且 Flash 20 分鐘間隔與 5m TTL 不匹配、1h TTL 寫入成本高。詳見「Prompt 結構與快取決策」章節 |
| KB 注入位置 | Flash Task system message（block 陣列形式追加） | 語義對齊（身份/背景），避免與 user message 的 logs_json 混淆；為未來加 `cache_control` 預留結構 |
| KB context 格式 | 自然語言條列 + 程式固定 builder 樣板 | Token 效率高於 JSON / Markdown 表格、Haiku 注意力分布最好、與既有 prompt 風格一致；程式產出保證格式穩定 |
| Pain 2（AD Server 誤報）解法 | `knowledge_bases` 加 `analysis_rules` TEXT 欄位 + KB context 追加【分析規則】段落 + Haiku prompt 規則 | 維護成本最低（KB 整體一次 vs 每筆 asset 一次）、表達彈性最高、跨 Windows/FortiGate 都適用；Haiku 對自然語言規則的理解優於 JSON 結構化 enum。詳見「分析規則欄位設計」章節 |
| Pain 1（跨日拆兩筆）解法 | **獨立 fix Issue，跟本 Epic 解耦**：修 `pro_task.py` 用 Sonnet 已輸出但被忽略的 `continued_from_match_key`，並補寫 `continued_from` FK | 是修正既有設計死角而非新功能（`continued_from` 欄位早就存在但 `pro_task.py` 從未使用）；改動局部、無 schema 變動；不應綁進 KB Epic 的 SA→SD→PG 流程。詳見「跨日延續修法」章節 |
