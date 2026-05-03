---
name: SQL-table-creator
description: Create table into SQL database by given schema, column name, column type etc
---
When required to create new table in SQL databases, runs create step-by-step, if error occurs, report to human

1. Make sure a schema table is given styled like:

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | INTEGER, PK | |
| name | VARCHAR(100), NOT NULL, UK | 角色名稱 |
| can_access_ai | BOOLEAN, NOT NULL, DEFAULT FALSE | 可使用 AI 夥伴功能 |
| can_use_kb | BOOLEAN, NOT NULL, DEFAULT FALSE | 可查閱知識庫 |
| can_manage_accounts | BOOLEAN, NOT NULL, DEFAULT FALSE | 可管理使用者帳號 |
| can_manage_roles | BOOLEAN, NOT NULL, DEFAULT FALSE | 可管理角色與權限 |
| can_edit_ai | BOOLEAN, NOT NULL, DEFAULT FALSE | 可編輯 AI 夥伴設定 |
| can_manage_kb | BOOLEAN, NOT NULL, DEFAULT FALSE | 可管理知識庫 |
| created_at | TIMESTAMP, NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMP, NOT NULL, DEFAULT NOW() | |

2. Checks given schema information is valid (no foreign-key violation, falsely set primary-key)
3. Creates table by sqlalchemy.orm, generate table schema by sqlalchemy orm in /app/db/models
4. Add a new version in alembic, generate update codes

Within schema tables, phrase list below:
- UK: unique key
- PK: primary key
- FK: foreign key, → {table_name} refers the key foreign to  