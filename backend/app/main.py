from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.chat import router as chat_router

app = FastAPI(
    title="Enterprise AI Copilot",
    version="1.0.0",
)

# TEMPORARY: Allow all origins for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "Enterprise AI Copilot is running."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Lambda handler (safe to keep even if you're currently running on ECS)
handler = Mangum(app)