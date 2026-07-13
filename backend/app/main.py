from fastapi import FastAPI

from app.api.chat import router as chat_router

app = FastAPI(
    title="Enterprise AI Copilot",
    version="1.0.0",
)

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