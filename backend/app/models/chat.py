from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    previous_response_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    response_id: str