from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.database.base import Base
from app.database.session import engine
from app.logging.logger import logger
from app.logging.middleware import LoggingMiddleware
from app.metrics.db_metrics import setup_database_metrics

# Import models so SQLAlchemy registers them
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401


# Prevent duplicate SQLAlchemy event registration
_db_metrics_initialized = False


# --------------------------------------------------
# Application Lifespan
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_metrics_initialized

    logger.info("Starting Enterprise AI Copilot...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")

        # Register SQLAlchemy metrics once
        if not _db_metrics_initialized:
            setup_database_metrics(engine)
            _db_metrics_initialized = True
            logger.info("Database metrics initialized.")

    except Exception:
        logger.exception("Failed to initialize the database.")
        raise

    yield

    logger.info("Enterprise AI Copilot shutting down.")


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------
app = FastAPI(
    title="Enterprise AI Copilot",
    version="1.2.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Prometheus Metrics
# --------------------------------------------------
Instrumentator(
    excluded_handlers=[
        "/metrics",
        "/health",
        "/favicon.ico",
    ],
).instrument(app).expose(app)


# --------------------------------------------------
# Middleware
# --------------------------------------------------
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# API Routes
# --------------------------------------------------
app.include_router(chat_router)
app.include_router(conversation_router)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------
@app.get("/")
def root():
    logger.info("Root endpoint called.")

    return {
        "message": "Enterprise AI Copilot API is running.",
        "version": "1.2.0",
    }


# --------------------------------------------------
# Health Endpoint
# --------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "enterprise-ai-backend",
        "version": "1.2.0",
    }


# --------------------------------------------------
# Detailed Health Check
# --------------------------------------------------
@app.get("/health/details")
def health_details():

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        database = "healthy"

    except Exception as ex:
        logger.exception("Database health check failed.")
        database = str(ex)

    return {
        "status": "healthy",
        "service": "enterprise-ai-backend",
        "database": database,
        "version": "1.2.0",
    }


# --------------------------------------------------
# AWS Lambda Handler
# --------------------------------------------------
handler = Mangum(app)