# /Users/vaibhavithakur/veripura-system/backend/app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import dispose_database_engine, verify_database_connection
from app.logger import logger
from app.middleware.request_id import RequestIDMiddleware
from app.routes import health, qr, shipments, upload, verify


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
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"CORS origin regex: {settings.cors_origin_regex}")

    logger.info(f"ACTIVE TESSERACT CMD: {settings.tesseract_cmd}")

    await verify_database_connection()
    logger.info("Database connection verified")

    from app.ml.model_loader import model_loader

    model_loader.preload()

    yield

    logger.info("Shutting down application")
    await dispose_database_engine()


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
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(verify.router)
    app.include_router(shipments.router)
    app.include_router(qr.router)

    return app


app = create_app()
