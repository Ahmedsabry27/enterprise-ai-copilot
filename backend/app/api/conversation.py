from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
)
from app.services.conversation_service import (
    conversation_service,
)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


# --------------------------------------------------
# Create Conversation
# --------------------------------------------------
@router.post("", response_model=ConversationResponse)
def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
):
    return conversation_service.create_conversation(
        db=db,
        title=request.title,
    )


# --------------------------------------------------
# Get All Conversations
# --------------------------------------------------
@router.get("", response_model=list[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
):
    return conversation_service.get_conversations(db)


# --------------------------------------------------
# Get Conversation
# --------------------------------------------------
@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation = conversation_service.get_conversation(
        db,
        conversation_id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation


# --------------------------------------------------
# Update Conversation Title
# --------------------------------------------------
@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def update_conversation(
    conversation_id: UUID,
    request: ConversationUpdate,
    db: Session = Depends(get_db),
):
    conversation = (
        conversation_service.update_conversation_title(
            db=db,
            conversation_id=conversation_id,
            title=request.title,
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation


# --------------------------------------------------
# Get Conversation Messages
# --------------------------------------------------
@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation = conversation_service.get_conversation(
        db,
        conversation_id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation_service.get_messages(
        db,
        conversation_id,
    )


# --------------------------------------------------
# Delete Conversation
# --------------------------------------------------
@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = conversation_service.delete_conversation(
        db,
        conversation_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return {
        "message": "Conversation deleted",
    }