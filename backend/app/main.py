from fastapi import FastAPI

app = FastAPI(
    title="Enterprise AI Copilot",
    description="AI-powered enterprise assistant",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Welcome to Enterprise AI Copilot!"}

@app.get("/health")
def health():
    return {"status": "healthy"}