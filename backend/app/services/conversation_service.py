from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.conversation_repository import (
    conversation_repository,
)
from app.repositories.message_repository import (
    message_repository,
)


class ConversationService:

    # --------------------------------------------------
    # Conversation CRUD
    # --------------------------------------------------

    def create_conversation(
        self,
        db: Session,
        title: str = "New Conversation",
    ):
        return conversation_repository.create(
            db=db,
            title=title,
        )

    def get_conversations(
        self,
        db: Session,
    ):
        return conversation_repository.get_all(db)

    def get_conversation(
        self,
        db: Session,
        conversation_id: UUID,
    ):
        return conversation_repository.get_by_id(
            db,
            conversation_id,
        )

    # --------------------------------------------------
    # NEW - Update Conversation Title
    # --------------------------------------------------

    def update_conversation_title(
        self,
        db: Session,
        conversation_id: UUID,
        title: str,
    ):
        conversation = conversation_repository.get_by_id(
            db,
            conversation_id,
        )

        if not conversation:
            return None

        return conversation_repository.update_title(
            db=db,
            conversation=conversation,
            title=title,
        )

    def delete_conversation(
        self,
        db: Session,
        conversation_id: UUID,
    ):
        return conversation_repository.delete(
            db,
            conversation_id,
        )

    # --------------------------------------------------
    # Conversation Activity
    # --------------------------------------------------

    def touch_conversation(
        self,
        db: Session,
        conversation_id: UUID,
    ):
        """
        Updates the conversation's updated_at timestamp.
        Called whenever a new message is added.
        """

        conversation = conversation_repository.get_by_id(
            db,
            conversation_id,
        )

        if conversation:
            return conversation_repository.touch(
                db,
                conversation,
            )

        return None

    # --------------------------------------------------
    # Messages
    # --------------------------------------------------

    def save_user_message(
        self,
        db: Session,
        conversation_id: UUID,
        content: str,
    ):
        return message_repository.create(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    def save_assistant_message(
        self,
        db: Session,
        conversation_id: UUID,
        content: str,
        response_id: str | None,
    ):
        return message_repository.create(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            response_id=response_id,
        )

    def get_messages(
        self,
        db: Session,
        conversation_id: UUID,
    ):
        return message_repository.get_by_conversation(
            db,
            conversation_id,
        )


conversation_service = ConversationService()