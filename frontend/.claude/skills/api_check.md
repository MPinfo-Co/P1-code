---
name: Backend-API-design-pattern
description: Checks API url and request format of backend
---
Check API route and request body before creating frontend fetch codes
**Request body**: 
    1. Inspect through files in @../backend/app/api/schema/
    2. Find target pydantic classes
    3. Format resective request body for frontend
**API route**:
    1. Inspect through files in @../backend/app/api/
    2. Backend is build in FastAPI framework
    3. Find route of target API by docstring or function name

If API route cannot be found, ask human to resolve problem, DO NOT create API by yourself