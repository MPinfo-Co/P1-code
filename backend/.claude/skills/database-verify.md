---
name: alembic-database
description: Update and fix postgresSQL version mismatch database by Alembic
---

When generation new function codes, checks database schema and updates alembic

1. Check alembic library exist, if not, run `pip install sqlalchemy alembic`
2. **Version check**: Check if current database schema aligns with @app/db/models, if not runs `alembic update head`
3. **Verify**: If still not align with code base after update, generate update .py file to match database schema
4. **Final check**: If alembic not properly executes, find and fix error through web-search, fix problem then executes again

DO NOT clear database, schema or table automatically, ask for human approval any time tries to execute `del` command outside of alembic