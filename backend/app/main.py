from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.events import router as events_router
from api.health import router as health_router
from api.ingest import router as ingest_router

def start_server():
    app = FastAPI(title="MP-Box API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "https://p1-code.vercel.app",
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(events_router)
    app.include_router(ingest_router)
    return app

app = start_server()