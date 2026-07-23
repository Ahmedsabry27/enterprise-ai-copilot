import json
import logging
import time
from typing import Generator
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.openai_client import client
from app.metrics.metrics import (
    completion_tokens_total,
    openai_errors_total,
    openai_latency_seconds,
    openai_requests_total,
    prompt_tokens_total,
    total_tokens_total,
)
from app.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are Enterprise AI Copilot.

You assist:

- Product Owners
- Scrum Masters
- Project Managers
- Business Analysts
- Solution Architects
- Developers

Always:

- Be professional
- Be concise
- Explain step by step
- Generate Jira user stories
- Generate acceptance criteria
- Generate meeting summaries
- Help with AI, SAP, AEM, APIs and Agile.
"""


class ChatService:

    # --------------------------------------------------
    # Validate conversation ownership
    # --------------------------------------------------
    def _validate_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: str,
    ) -> None:
        """
        Ensures the conversation belongs to the authenticated user.
        Raises if the conversation doesn't exist or is not owned by the user.
        """

        conversation = conversation_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found or access denied")

    # --------------------------------------------------
    # Synchronous Chat Endpoint
    # --------------------------------------------------
    def ask(
        self,
        db: Session,
        user_id: str,
        message: str,
        conversation_id: UUID | None = None,
        previous_response_id: str | None = None,
    ):

        logger.info(
            "incoming_chat_request",
            extra={"user_id": user_id},
        )

        # ------------------------------------------
        # Validate ownership + Save user message
        # ------------------------------------------
        if conversation_id:

            self._validate_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

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

        try:

            start = time.perf_counter()

            if previous_response_id:

                response = client.responses.create(
                    model="gpt-4.1-mini",
                    previous_response_id=previous_response_id,
                    input=message,
                )

            else:

                response = client.responses.create(
                    model="gpt-4.1-mini",
                    instructions=SYSTEM_PROMPT,
                    input=message,
                )

            latency = time.perf_counter() - start

            openai_requests_total.inc()
            openai_latency_seconds.observe(latency)

            usage = getattr(response, "usage", None)

            if usage:

                prompt_tokens = usage.input_tokens
                completion_tokens = usage.output_tokens
                total_tokens = usage.total_tokens

                prompt_tokens_total.inc(prompt_tokens)
                completion_tokens_total.inc(completion_tokens)
                total_tokens_total.inc(total_tokens)

                logger.info(
                    "openai_usage",
                    extra={
                        "user_id": user_id,
                        "model": "gpt-4.1-mini",
                        "latency_seconds": round(latency, 3),
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    },
                )

            # ------------------------------------------
            # Save assistant message
            # ------------------------------------------
            if conversation_id:

                conversation_service.save_assistant_message(
                    db=db,
                    conversation_id=conversation_id,
                    content=response.output_text,
                    response_id=response.id,
                )

                conversation_service.touch_conversation(
                    db=db,
                    conversation_id=conversation_id,
                    user_id=user_id,
                )

            logger.info(
                "openai_request_completed",
                extra={
                    "user_id": user_id,
                    "model": "gpt-4.1-mini",
                    "latency_seconds": round(latency, 3),
                },
            )

            return {
                "response": response.output_text,
                "response_id": response.id,
            }

        except Exception:

            openai_errors_total.inc()

            logger.exception(
                "openai_request_failed",
                extra={"user_id": user_id},
            )

            raise

    # --------------------------------------------------
    # Streaming Endpoint
    # --------------------------------------------------
    def stream(
        self,
        db: Session,
        user_id: str,
        message: str,
        conversation_id: UUID | None = None,
        previous_response_id: str | None = None,
    ) -> Generator[str, None, None]:

        logger.info(
            "streaming_request_started",
            extra={"user_id": user_id},
        )

        # ------------------------------------------
        # Validate ownership + Save user message
        # ------------------------------------------
        if conversation_id:

            self._validate_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

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

        try:

            openai_requests_total.inc()

            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            start = time.perf_counter()

            if previous_response_id:

                stream = client.responses.create(
                    model="gpt-4.1-mini",
                    previous_response_id=previous_response_id,
                    input=message,
                    stream=True,
                )

            else:

                stream = client.responses.create(
                    model="gpt-4.1-mini",
                    instructions=SYSTEM_PROMPT,
                    input=message,
                    stream=True,
                )

            response_id = None
            assistant_text = ""

            for event in stream:

                if hasattr(event, "response") and event.response:
                    response_id = getattr(
                        event.response,
                        "id",
                        response_id,
                    )

                if event.type == "response.output_text.delta":

                    assistant_text += event.delta

                    yield (
                        f"data: {json.dumps({'type': 'delta', 'text': event.delta})}\n\n"
                    )

                elif event.type == "response.completed":

                    latency = time.perf_counter() - start

                    openai_latency_seconds.observe(latency)

                    logger.info(
                        "stream_completed",
                        extra={
                            "user_id": user_id,
                            "model": "gpt-4.1-mini",
                            "latency_seconds": round(latency, 3),
                        },
                    )

                elif event.type == "response.created":
                    logger.info("stream_created")

                elif event.type == "response.failed":
                    openai_errors_total.inc()
                    logger.error("stream_failed")

                elif event.type == "error":
                    openai_errors_total.inc()
                    logger.error(
                        "stream_error",
                        extra={"error": str(event)},
                    )

            if conversation_id:

                conversation_service.save_assistant_message(
                    db=db,
                    conversation_id=conversation_id,
                    content=assistant_text,
                    response_id=response_id,
                )

                conversation_service.touch_conversation(
                    db=db,
                    conversation_id=conversation_id,
                    user_id=user_id,
                )

            yield (
                f"data: {json.dumps({'type': 'completed', 'response_id': response_id})}\n\n"
            )

            logger.info(
                "streaming_request_completed",
                extra={"user_id": user_id},
            )

        except Exception as ex:

            openai_errors_total.inc()

            logger.exception(
                "streaming_request_failed",
                extra={"user_id": user_id},
            )

            yield (
                f"data: {json.dumps({'type': 'error', 'message': str(ex)})}\n\n"
            )


chat_service = ChatService()