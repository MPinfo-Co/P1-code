---
name: API-logic-writer
description: Generate codes for API endpoints of FastAPI
---
Coding logic for coding API endpoint

**Authenticate**: All API should require authenticate, the function stored in @app/util/util_store.py `authenticate` function, read function docstring for API authentication coding
**Code structure**: 
    1. API request and response body stored in @app/api/schema, one api file contracts to one schema file
    2. CRUD logic coded with API endpoints
    