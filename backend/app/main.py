from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router

from app.database.base import Base
from app.database.session import engine

# Import models so SQLAlchemy registers them
from app.models.conversation import Conversation
from app.models.message import Message

app = FastAPI(
    title="Enterprise AI Copilot",
    version="1.1.1",
)

# --------------------------------------------------
# Create Database Tables
# --------------------------------------------------
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# CORS
# --------------------------------------------------
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
# Health Endpoints
# --------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Enterprise AI Copilot API is running.",
        "version": "1.1.1",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }

# --------------------------------------------------
# AWS Lambda Handler
# (Safe to keep while running on ECS)
# --------------------------------------------------
handler = Mangum(app)