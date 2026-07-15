from fastapi import APIRouter, HTTPException, Response

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:

        result = chat_service.ask(
            message=request.message,
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


@router.options("/chat")
def options_chat():
    return Response(status_code=200)