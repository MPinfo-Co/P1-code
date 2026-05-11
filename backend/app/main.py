"""
The Entry site of MP-Box
@version: v0.0.1
@author: Yinchen
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.logger_utils import get_system_logger
from app.scheduler import start_scheduler, stop_scheduler
from app.api.auth import router as auth_router
from app.api.fn_ai_partner_chat import router as fn_ai_partner_chat_router
from app.api.company_data import router as company_data_router
from app.api.events import router as events_router
from app.api.fn_ai_partner_config import router as fn_ai_partner_config_router
from app.api.fn_expert_setting import router as fn_expert_setting_router
from app.api.fn_ai_partner_tool import router as fn_ai_partner_tool_router
from app.api.fn_feedback import router as fn_feedback_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.navigation import router as navigation_router
from app.api.roles import router as roles_router
from app.api.user import router as user_router
from app.middlewares.request_response_handler import RequestResponseHandlerMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan of FastAPI app, which executes when FastAPI starts and ends.
    """
    system_logger = get_system_logger()
    server_start_time = datetime.now()
    server_start_time_str = server_start_time.strftime("%Y%m%d-%H%M%S")
    system_logger.info(f"""
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃  ⚡ Systems initialized           ┃
        ┃  🌐 MP-Box server                 ┃
        ┃  ⏱️ Start time: {server_start_time_str}   ┃
        ┃  🚀 Ready for requests            ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """)
    start_scheduler()
    yield
    stop_scheduler()
    server_end_time = datetime.now()
    server_duration = server_end_time - server_start_time
    server_end_time_str = server_end_time.strftime("%Y%m%d-%H%M%S")
    system_logger.info(f"""
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃  ⚡ Systems Stopped               ┃
        ┃  🌐 MP-Box server                 ┃
        ┃  ⏱️ Stop time: {server_end_time_str}    ┃
        ┃  ⏱️ Duration: {server_duration}      ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """)


def create_app():
    """
    Function to create FastAPI app
    :return: FastAPI app
    """
    server = FastAPI(lifespan=lifespan)

    server.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    server.add_middleware(RequestResponseHandlerMiddleware)

    server.include_router(auth_router)
    server.include_router(fn_ai_partner_chat_router)
    server.include_router(company_data_router)
    server.include_router(events_router)
    server.include_router(fn_ai_partner_config_router)
    server.include_router(fn_expert_setting_router)
    server.include_router(fn_ai_partner_tool_router)
    server.include_router(fn_feedback_router)
    server.include_router(health_router)
    server.include_router(ingest_router)
    server.include_router(user_router)
    server.include_router(roles_router)
    server.include_router(navigation_router)

    return server


app = create_app()
