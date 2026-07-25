import logging
from collections.abc import Generator
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.builders.conversation_builder import ConversationBuilder
from app.ai.factory import AIProviderFactory
from app.ai.models import (
    AIResponse,
    AIStreamEvent,
)
from app.metrics.metrics import (
    chat_errors_total,
    chat_requests_total,
    messages_processed_total,
)
from app.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)


class ChatService:
    """
    Provider-agnostic chat orchestration service.

    Responsibilities:

    - Validate conversation ownership
    - Persist user messages
    - Build conversation history
    - Delegate inference to the configured AI provider
    - Persist assistant responses
    """

    def __init__(self) -> None:
        self.provider = AIProviderFactory.get_provider()
        self.builder = ConversationBuilder()

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def _validate_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: str,
    ) -> None:

        conversation = conversation_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found or access denied."
            )

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _load_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: str,
    ):

        history = conversation_service.get_messages(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        return self.builder.build(history)

    def _save_user_message(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: str,
        message: str,
    ) -> None:

        conversation_service.save_user_message(
            db=db,
            conversation_id=conversation_id,
            content=message,
        )

        conversation_service.touch_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

    def _save_assistant_message(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: str,
        response: AIResponse,
    ) -> None:

        conversation_service.save_assistant_message(
            db=db,
            conversation_id=conversation_id,
            content=response.text,
            response_id=response.response_id,
        )

        conversation_service.touch_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )
    # --------------------------------------------------
    # Synchronous Chat
    # --------------------------------------------------

    def ask(
        self,
        db: Session,
        user_id: str,
        message: str,
        conversation_id: UUID | None = None,
    ) -> AIResponse:
        """
        Process a synchronous chat request.

        Flow:

            Validate Conversation
                    ↓
             Save User Message
                    ↓
            Load Conversation History
                    ↓
          Build AI Conversation Messages
                    ↓
              Invoke AI Provider
                    ↓
          Save Assistant Response
                    ↓
              Return AIResponse
        """

        logger.info(
            "chat_request_started",
            extra={
                "user_id": user_id,
                "conversation_id": (
                    str(conversation_id)
                    if conversation_id
                    else None
                ),
            },
        )

        chat_requests_total.inc()
        messages_processed_total.inc()

        try:

            # ------------------------------------------
            # Validate conversation
            # ------------------------------------------
            if conversation_id is None:
                raise ValueError(
                    "conversation_id is required."
                )

            self._validate_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # ------------------------------------------
            # Save user message
            # ------------------------------------------
            self._save_user_message(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
                message=message,
            )

            # ------------------------------------------
            # Build conversation
            # ------------------------------------------
            conversation = self._load_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # ------------------------------------------
            # Generate AI response
            # ------------------------------------------
            response = self.provider.ask(
                messages=conversation,
            )

            # ------------------------------------------
            # Save assistant response
            # ------------------------------------------
            self._save_assistant_message(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
                response=response,
            )

            logger.info(
                "chat_request_completed",
                extra={
                    "user_id": user_id,
                    "conversation_id": str(conversation_id),
                    "model": response.model,
                    "latency_seconds": round(
                        response.latency_seconds,
                        3,
                    ),
                },
            )

            return response

        except Exception:

            chat_errors_total.inc()

            logger.exception(
                "chat_request_failed",
                extra={
                    "user_id": user_id,
                    "conversation_id": (
                        str(conversation_id)
                        if conversation_id
                        else None
                    ),
                },
            )

            raise
    # --------------------------------------------------
    # Streaming Chat
    # --------------------------------------------------

    def stream(
        self,
        db: Session,
        user_id: str,
        message: str,
        conversation_id: UUID | None = None,
    ) -> Generator[AIStreamEvent, None, None]:
        """
        Stream a response from the configured AI provider.
        """

        logger.info(
            "stream_request_started",
            extra={
                "user_id": user_id,
                "conversation_id": (
                    str(conversation_id)
                    if conversation_id
                    else None
                ),
            },
        )

        chat_requests_total.inc()
        messages_processed_total.inc()

        assistant_text = ""
        final_response_id = None
        final_model = ""
        final_usage = None

        try:

            # ------------------------------------------
            # Validate conversation
            # ------------------------------------------
            if conversation_id is None:
                raise ValueError(
                    "conversation_id is required."
                )

            self._validate_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # ------------------------------------------
            # Save user message
            # ------------------------------------------
            self._save_user_message(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
                message=message,
            )

            # ------------------------------------------
            # Build conversation
            # ------------------------------------------
            conversation = self._load_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # ------------------------------------------
            # Stream AI response
            # ------------------------------------------
            for event in self.provider.stream(
                messages=conversation,
            ):

                if event.text:
                    assistant_text += event.text

                if event.response_id:
                    final_response_id = event.response_id

                if event.model:
                    final_model = event.model

                if event.usage:
                    final_usage = event.usage

                yield event

            # ------------------------------------------
            # Save assistant message
            # ------------------------------------------
            response = AIResponse(
                text=assistant_text,
                response_id=final_response_id,
                model=final_model,
                usage=final_usage,
            )

            self._save_assistant_message(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
                response=response,
            )

            logger.info(
                "stream_request_completed",
                extra={
                    "user_id": user_id,
                    "conversation_id": str(conversation_id),
                    "model": final_model,
                },
            )

        except Exception:

            chat_errors_total.inc()

            logger.exception(
                "stream_request_failed",
                extra={
                    "user_id": user_id,
                    "conversation_id": (
                        str(conversation_id)
                        if conversation_id
                        else None
                    ),
                },
            )

            raise
# --------------------------------------------------
# Singleton
# --------------------------------------------------

chat_service = ChatService()