import time

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.sse import to_sse
from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.logging.logger import logger
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

    logger.info(
        "Chat request received",
        extra={
            "user_id": user["sub"],
            "username": user.get("username"),
        },
    )

    try:

        response = chat_service.ask(
            db=db,
            user_id=user["sub"],
            message=request.message,
            conversation_id=request.conversation_id,
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
            response=response.text,
            response_id=response.response_id,
        )

    except Exception as ex:

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
    logger.info(
        "Streaming chat request received",
        extra={
            "user_id": user["sub"],
            "username": user.get("username"),
        },
    )

    try:

        def event_stream():

            for event in chat_service.stream(
                db=db,
                user_id=user["sub"],
                message=request.message,
                conversation_id=request.conversation_id,
            ):
                yield to_sse(event)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as ex:

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