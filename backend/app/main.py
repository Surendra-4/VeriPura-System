from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logger import logger
from app.middleware.request_id import RequestIDMiddleware
from app.routes import health, qr, upload, verify


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: startup and shutdown logic.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Model directory: {settings.model_dir}")

    from app.ml.model_loader import model_loader

    model_loader.preload()

    yield

    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """
    Application factory pattern.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(verify.router)
    app.include_router(qr.router)

    return app


app = create_app()
