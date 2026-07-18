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
from app.services.conversation_service import (
    conversation_service,
)

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
    # Synchronous Chat Endpoint
    # --------------------------------------------------
    def ask(
        self,
        db: Session,
        message: str,
        conversation_id: UUID | None = None,
        previous_response_id: str | None = None,
    ):

        logger.info("incoming_chat_request")

        # ------------------------------------------
        # Save user message
        # ------------------------------------------
        if conversation_id:

            conversation_service.save_user_message(
                db=db,
                conversation_id=conversation_id,
                content=message,
            )

            conversation_service.touch_conversation(
                db=db,
                conversation_id=conversation_id,
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

            # ------------------------------------------
            # Metrics
            # ------------------------------------------
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
                )

            logger.info(
                "openai_request_completed",
                extra={
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
            )

            raise

    # --------------------------------------------------
    # Streaming Endpoint (SSE)
    # --------------------------------------------------
    def stream(
        self,
        db: Session,
        message: str,
        conversation_id: UUID | None = None,
        previous_response_id: str | None = None,
    ) -> Generator[str, None, None]:

        logger.info("streaming_request_started")

        # ------------------------------------------
        # Save user message
        # ------------------------------------------
        if conversation_id:

            conversation_service.save_user_message(
                db=db,
                conversation_id=conversation_id,
                content=message,
            )

            conversation_service.touch_conversation(
                db=db,
                conversation_id=conversation_id,
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

                # ------------------------------------------
                # Capture Response ID
                # ------------------------------------------
                if hasattr(event, "response") and event.response:

                    response_id = getattr(
                        event.response,
                        "id",
                        response_id,
                    )

                # ------------------------------------------
                # Stream Text
                # ------------------------------------------
                if event.type == "response.output_text.delta":

                    assistant_text += event.delta

                    payload = {
                        "type": "delta",
                        "text": event.delta,
                    }

                    yield f"data: {json.dumps(payload)}\n\n"

                # ------------------------------------------
                # Response Completed
                # ------------------------------------------
                elif event.type == "response.completed":

                    latency = time.perf_counter() - start

                    openai_latency_seconds.observe(latency)

                    logger.info(
                        "stream_completed",
                        extra={
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
                        extra={
                            "error": str(event),
                        },
                    )

            # ------------------------------------------
            # Save Assistant Message
            # ------------------------------------------
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
                )

            payload = {
                "type": "completed",
                "response_id": response_id,
            }

            yield f"data: {json.dumps(payload)}\n\n"

            logger.info("streaming_request_completed")

        except Exception as ex:

            openai_errors_total.inc()

            logger.exception("streaming_request_failed")

            payload = {
                "type": "error",
                "message": str(ex),
            }

            yield f"data: {json.dumps(payload)}\n\n"


chat_service = ChatService()