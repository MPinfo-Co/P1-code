# Backend — MP-BOX 1.0

FastAPI + SQLAlchemy + PostgreSQL 後端服務。

## 技術棧

| 套件 | 用途 |
|---|---|
| FastAPI | Web 框架，自動產生 API 文件 |
| SQLAlchemy | ORM，用 Python 操作資料庫 |
| Alembic | 資料庫 schema 版本管理（migration） |
| pydantic-settings | 讀取 .env 設定 |
| psycopg2-binary | PostgreSQL 連線驅動 |
| uvicorn | ASGI 伺服器，執行 FastAPI |

## 環境建置

### 1. PostgreSQL

```bash
sudo service postgresql start

# 建立使用者與資料庫（第一次才需要）
sudo -u postgres psql -c "CREATE USER <user> WITH PASSWORD '<password>';"
sudo -u postgres psql -c "CREATE DATABASE mpbox OWNER <user>;"
```

### 2. Python 虛擬環境

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 環境變數

```bash
cp .env.example .env
```

編輯 `.env`：

```env
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/mpbox
```

> **注意：** 密碼若含 `@` 符號，需改為 `%40`
> 例：密碼 `@abc123` → 寫成 `%40abc123`

### 4. 執行 Migration

```bash
alembic upgrade head
```

確認 table 建立：

```bash
sudo -u postgres psql -d mpbox -c "\dt"
```

### 5. 啟動服務

```bash
uvicorn app.main:app --reload
```

開啟 `http://localhost:8000/health` 確認回傳 `{"status": "ok"}`

API 文件：`http://localhost:8000/docs`

## 專案結構

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口，註冊所有 router
│   ├── core/
│   │   └── config.py        # 讀取 .env（DATABASE_URL 等設定）
│   ├── db/
│   │   └── session.py       # SQLAlchemy engine / SessionLocal / Base / get_db()
│   ├── models/              # SQLAlchemy ORM model（對應資料庫 table）
│   │   └── user.py          # User、Role、UserRole
│   └── api/                 # API endpoint（router）
│       └── health.py        # GET /health
├── alembic/                 # Migration 設定與腳本
│   ├── env.py               # Alembic 設定（讀 .env、載入 models）
│   └── versions/            # 每次 schema 變更的腳本
├── alembic.ini              # Alembic 主設定檔
├── .env                     # 本地環境變數（不進 git）
├── .env.example             # 環境變數範本（進 git）
├── requirements.txt         # 套件清單
└── venv/                    # 虛擬環境（不進 git）
```

## 資料庫 Schema（目前）

### users
| 欄位 | 型別 | 說明 |
|---|---|---|
| id | INTEGER PK | 主鍵 |
| name | VARCHAR(100) | 姓名 |
| email | VARCHAR(255) UNIQUE | 信箱，登入用 |
| password_hash | VARCHAR(255) | bcrypt 加密密碼 |
| is_active | BOOLEAN | 帳號是否啟用 |
| created_at / updated_at | TIMESTAMP | 時間戳記 |

### roles
| 欄位 | 型別 | 說明 |
|---|---|---|
| id | INTEGER PK | 主鍵 |
| name | VARCHAR(100) UNIQUE | 角色名稱 |
| can_access_ai | BOOLEAN | 可使用 AI 夥伴 |
| can_use_kb | BOOLEAN | 可查閱知識庫 |
| can_manage_accounts | BOOLEAN | 可管理帳號 |
| can_manage_roles | BOOLEAN | 可管理角色 |
| can_edit_ai | BOOLEAN | 可編輯 AI 設定 |
| can_manage_kb | BOOLEAN | 可管理知識庫 |

### user_roles
| 欄位 | 型別 | 說明 |
|---|---|---|
| user_id | FK → users | 使用者 |
| role_id | FK → roles | 角色 |

完整 schema 定義請見 `P1-analysis/database/entity-analysis.md`

## API Endpoints（目前）

| Method | Path | 說明 |
|---|---|---|
| GET | /health | 確認服務正常 |

**預計新增（P4-3）：**

| Method | Path | 說明 | Input | Output |
|---|---|---|---|---|
| POST | /api/auth/login | 登入，取得 JWT | `{ email, password }` | `{ access_token, token_type }` |
| GET | /api/auth/me | 取得目前登入使用者 | Header: Bearer token | `{ id, name, email, role }` |

## 新增 API 流程

1. 在 `app/models/` 建立或確認對應 model
2. 在 `app/api/` 建立新的 router 檔案
3. 在 `app/main.py` 用 `app.include_router()` 註冊
4. 若有新 table → `alembic revision --autogenerate -m "描述"` → `alembic upgrade head`

## Migration 操作

```bash
# 產生新的 migration 腳本（model 有變更時）
alembic revision --autogenerate -m "描述變更內容"

# 套用所有未執行的 migration
alembic upgrade head

# 查看目前版本
alembic current

# 回退一版
alembic downgrade -1
```

## 常見問題

**Q: `ModuleNotFoundError: No module named 'app'`**
確認你在 `backend/` 資料夾下，且 venv 已啟動（有 `(venv)` 前綴）。

**Q: 密碼含特殊字元 `@` 無法連線**
`.env` 中的密碼需 URL encode：`@` → `%40`

**Q: `alembic upgrade head` 說 database 不存在**
先確認 PostgreSQL 已啟動（`sudo service postgresql start`），且 `mpbox` 資料庫已建立。
