---
name: python-database-code-writer
description: Generate codes associate to database
---
Generate code fits requirement of the project

1. **Framework**: Use SqlAlchemy 2.0 ORM
2. **Database Structure**: Table schemas defines in @app/db/models, table schema root `DeclarativeBase` class stored in @app/db/models/base.py, other table inherited from this file
3. **CRUD Logic**: Coded with API routes in @app/api/
4. **Workflow**: Operate in order, skip if not required
    1. Create database
    2. modify database
    3. Create/update CRUD logic
    4. Generate API schemas
    5. Assemble API schema and CRUD logic to make a fully functional API
    6. Evaluate API
    7. Others
