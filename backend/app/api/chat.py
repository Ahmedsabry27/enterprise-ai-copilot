from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
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
):

    try:

        result = chat_service.ask(
            db=db,
            message=request.message,
            conversation_id=request.conversation_id,
            previous_response_id=request.previous_response_id,
        )

        return ChatResponse(
            response=result["response"],
            response_id=result["response_id"],
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# --------------------------------------------------
# Streaming Endpoint (SSE)
# --------------------------------------------------
@router.post("/chat/stream")
def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):

    try:

        generator = chat_service.stream(
            db=db,
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

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
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