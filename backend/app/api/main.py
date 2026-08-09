from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.api.routers import (
    workflows,
    dashboard,
    conversations,
)



app = FastAPI(
    title="Enterprise AI Copilot API",
    description=(
        "Production API layer for "
        "Enterprise AI Agent Platform"
    ),
    version="1.0.0",
)



# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)



# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(
    workflows.router
)

# Preserve the versionless route while supporting the documented legacy API path.
app.include_router(
    workflows.router,
    prefix="/api",
)


app.include_router(
    dashboard.router
)


app.include_router(
    conversations.router
)



# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "service": "enterprise-ai-copilot-api",
    }



@app.get("/")
async def root():

    return {
        "name":
            "Enterprise AI Copilot API",

        "version":
            "1.0.0",

        "status":
            "running",
    }
