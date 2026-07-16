from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:

    # --------------------------------------------------
    # Create
    # --------------------------------------------------

    def create(
        self,
        db: Session,
        title: str,
    ) -> Conversation:

        conversation = Conversation(
            title=title,
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    # --------------------------------------------------
    # Read
    # --------------------------------------------------

    def get_all(
        self,
        db: Session,
    ) -> list[Conversation]:

        return (
            db.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def get_by_id(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> Conversation | None:

        return (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

    # --------------------------------------------------
    # Update Title
    # --------------------------------------------------

    def update_title(
        self,
        db: Session,
        conversation: Conversation,
        title: str,
    ) -> Conversation:

        conversation.title = title

        # Optional: Move the conversation to the top
        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(conversation)

        return conversation

    # --------------------------------------------------
    # Touch Conversation
    # --------------------------------------------------

    def touch(
        self,
        db: Session,
        conversation: Conversation,
    ) -> Conversation:
        """
        Update the conversation's updated_at timestamp.
        Called whenever a new message is added.
        """

        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(conversation)

        return conversation

    # --------------------------------------------------
    # Delete
    # --------------------------------------------------

    def delete(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> bool:

        conversation = self.get_by_id(
            db,
            conversation_id,
        )

        if not conversation:
            return False

        db.delete(conversation)
        db.commit()

        return True


conversation_repository = ConversationRepository()