from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.auth import router as auth_router
from .api.echo import router as echo_router
from .api.events import router as events_router
from .api.health import router as health_router
from .api.ingest import router as ingest_router
from contextlib import asynccontextmanager
from datetime import datetime

from .logger_utils import get_system_logger


def start_server():
    """
    Start the FastAPI server
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        system_log = get_system_logger()
        start_time = datetime.now()
        start_time_s = start_time.strftime("%Y-%m-%d %H:%M:%S")
        system_log.info(
            f"""
        ╔══════════════════════════════════════╗
        ║ 🚀  MP-box                           ║
        ╠══════════════════════════════════════╣
        ║ Status : ONLINE                      ║
        ║ Started: {start_time_s}         ║
        ╚══════════════════════════════════════╝
        """
        )
        yield

        stop_time = datetime.now()
        duration = stop_time - start_time

        system_log.info(
            f"""
        ╔══════════════════════════════════════╗
        ║ "Goodbye 👋"                         ║
        ╠══════════════════════════════════════╣
        ║ Stop: {start_time_s}            ║
        ║ Duration: {duration}             ║
        ╚══════════════════════════════════════╝
        """
        )

    app = FastAPI(title="MP-Box API", lifespan=lifespan)
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
    app.include_router(echo_router)
    app.include_router(events_router)
    app.include_router(ingest_router)
    return app


app = start_server()
