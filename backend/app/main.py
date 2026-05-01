"""
The Entry site of MP-Box
@version: v0.0.1
@author: Yinchen
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime

from .logger_utils import get_system_logger
from .api.auth import router as auth_router
from .api.dept import router as dept_router
from .api.events import router as events_router
from .api.health import router as health_router
from .api.ingest import router as ingest_router
from .api.notice import router as notice_router
from .api.user import router as user_router
from .middlewares.request_response_handler import RequestResponseHandlerMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan of FastAPI app, which executes when FastAPI starts and ends.
    """
    system_logger = get_system_logger()
    server_start_time = datetime.now()
    server_start_time_str = server_start_time.strftime("%Y%m%d-%H%M%S")
    system_logger.info(f'''
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃  ⚡ Systems initialized           ┃
        ┃  🌐 MP-Box server                 ┃
        ┃  ⏱️ Start time: {server_start_time_str}   ┃
        ┃  🚀 Ready for requests            ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    '''
    )
    yield
    server_end_time = datetime.now()
    server_duration = server_end_time - server_start_time
    server_end_time_str = server_end_time.strftime("%Y%m%d-%H%M%S")
    system_logger.info(f'''
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃  ⚡ Systems Stopped               ┃
        ┃  🌐 MP-Box server                 ┃
        ┃  ⏱️ Stop time: {server_end_time_str}    ┃
        ┃  ⏱️ Duration: {server_duration}      ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    '''
                       )

def create_app():
    """
    Function to create FastAPI app
    :return: FastAPI app
    """
    server = FastAPI(lifespan=lifespan)

    server.add_middleware(RequestResponseHandlerMiddleware)

    server.include_router(auth_router)
    server.include_router(dept_router)
    server.include_router(events_router)
    server.include_router(health_router)
    server.include_router(ingest_router)
    server.include_router(notice_router)
    server.include_router(user_router)

    return server

app = create_app()
