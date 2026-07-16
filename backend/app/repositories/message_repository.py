from uuid import UUID

from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:

    def create(
        self,
        db: Session,
        conversation_id: UUID,
        role: str,
        content: str,
        response_id: str | None = None,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            response_id=response_id,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    def get_by_conversation(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> list[Message]:

        return (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(Message.created_at.asc())
            .all()
        )


message_repository = MessageRepository()