import time

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.logging.logger import logger
from app.metrics.metrics import (
    chat_errors_total,
    chat_requests_total,
    messages_processed_total,
)
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter()


# --------------------------------------------------
# Chat Endpoint
# --------------------------------------------------
@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    start_time = time.perf_counter()

    chat_requests_total.inc()
    messages_processed_total.inc()

    logger.info(
        "Chat request received",
        extra={
            "user_id": user["sub"],
            "username": user.get("username"),
        },
    )

    try:

        result = chat_service.ask(
            db=db,
            user_id=user["sub"],
            message=request.message,
            conversation_id=request.conversation_id,
            previous_response_id=request.previous_response_id,
        )

        logger.info(
            "Chat request completed",
            extra={
                "user_id": user["sub"],
                "duration_ms": round(
                    (time.perf_counter() - start_time) * 1000,
                    2,
                ),
            },
        )

        return ChatResponse(
            response=result["response"],
            response_id=result["response_id"],
        )

    except Exception as ex:

        chat_errors_total.inc()

        logger.exception(
            "Chat request failed",
            extra={
                "user_id": user["sub"],
            },
        )

        raise HTTPException(
            status_code=500,
            detail=str(ex),
        )


# --------------------------------------------------
# Streaming Endpoint (SSE)
# --------------------------------------------------
@router.post("/chat/stream")
def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    chat_requests_total.inc()
    messages_processed_total.inc()

    logger.info(
        "Streaming chat request received",
        extra={
            "user_id": user["sub"],
            "username": user.get("username"),
        },
    )

    try:

        generator = chat_service.stream(
            db=db,
            user_id=user["sub"],
            message=request.message,
            conversation_id=request.conversation_id,
            previous_response_id=request.previous_response_id,
        )

        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as ex:

        chat_errors_total.inc()

        logger.exception(
            "Streaming chat request failed",
            extra={
                "user_id": user["sub"],
            },
        )

        raise HTTPException(
            status_code=500,
            detail=str(ex),
        )


# --------------------------------------------------
# CORS Preflight
# --------------------------------------------------
@router.options("/chat")
def options_chat():
    return Response(status_code=200)


@router.options("/chat/stream")
def options_stream():
    return Response(status_code=200)