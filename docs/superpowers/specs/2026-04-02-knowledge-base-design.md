# 知識庫模組設計文件

> 日期：2026-04-02  
> 狀態：草稿，待審核

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
  id, name, description, created_by, created_at, updated_at

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
| 資產表（20 筆） | ~20 行 | ~200 |
| 帳號清單（30 筆） | ~30 行 | ~300 |
| 白名單（10 筆） | ~10 行 | ~100 |
| 網段表（10 筆） | ~10 行 | ~100 |
| **合計** | | **~700 tokens** |

佔每次 ~32K tokens 的 2.2%，精準度提升遠大於成本增加。

---

## SA 草稿要點

SA 階段 AI 需要產出：

**business-logic.md**
- Use Case：管理員維護知識庫 / Flash Task 注入 / 角色權限控制
- ER 圖（文字版）
- 注入機制完整邏輯（含失敗降級：知識庫為空時跳過，不中斷分析）
- 白名單處理邏輯：`log_preaggregator.py` 預彙總時對白名單 IP 加上 `is_whitelisted: true` 標記，不過濾；Haiku prompt 加入指示「白名單 IP 若行為正常請降低嚴重性，但異常模式仍須回報」

**SD-WBS.md**
- 後端：6 張新 table + Alembic migration + 11 組 API + Flash Task 注入邏輯
- 前端：KnowledgeBase 頁面從 mock → 真實 API（3 個 Tab）
- 測試：CRUD + 注入 + 角色存取

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
5. pytest 數量 ≥ TestPlan 案例數，每個 test function 標注 TestPlan ID

---

## 設計決策記錄

| 問題 | 決策 | 理由 |
|------|------|------|
| 白名單實作位置 | 程式層標記 `is_whitelisted`，不過濾；prompt 指示 AI 降低嚴重性但異常仍回報 | 白名單 IP 異常時必須知道，不能硬過濾 |
| ai_partner_type | Enum，MVP 只定 `security` | 目前無其他 AI 夥伴，等真的要做再 migration |
| 知識庫刪除邏輯 | 硬刪除 + 二次確認彈窗 + FK cascade | 內部管理員使用，soft delete 增加 MVP 複雜度不值得；彈窗告知影響範圍已足夠 |
