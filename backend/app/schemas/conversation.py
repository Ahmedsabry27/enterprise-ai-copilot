from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# --------------------------------------------------
# Create Conversation
# --------------------------------------------------

class ConversationCreate(BaseModel):
    title: str


# --------------------------------------------------
# Update Conversation
# --------------------------------------------------

class ConversationUpdate(BaseModel):
    title: str


# --------------------------------------------------
# Response
# --------------------------------------------------

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime