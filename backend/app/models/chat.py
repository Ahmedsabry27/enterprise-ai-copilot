from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None
    previous_response_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    response_id: str