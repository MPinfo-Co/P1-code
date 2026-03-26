from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.auth import router as auth_router

app = FastAPI(title="MP-Box API")

app.include_router(health_router)
app.include_router(auth_router)
