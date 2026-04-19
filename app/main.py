from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.container import get_vector_store_manager
from app.core.logging import configure_logging
from app.mcp.server import mcp

mcp_http_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    get_vector_store_manager().load()
    async with mcp.session_manager.run():
        yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    application.include_router(router)
    application.mount("/mcp", mcp_http_app)
    return application


app = create_app()
