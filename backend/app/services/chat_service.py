import json
import logging
from typing import Generator
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.openai_client import client
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
    # Existing synchronous endpoint
    # --------------------------------------------------
    def ask(
        self,
        db: Session,
        message: str,
        conversation_id: UUID | None = None,
        previous_response_id: str | None = None,
    ):

        logger.info("Incoming request")

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

            return {
                "response": response.output_text,
                "response_id": response.id,
            }

        except Exception:
            logger.exception("OpenAI request failed.")
            raise

    # --------------------------------------------------
    # Streaming endpoint (SSE)
    # --------------------------------------------------
    def stream(
        self,
        db: Session,
        message: str,
        conversation_id: UUID | None = None,
        previous_response_id: str | None = None,
    ) -> Generator[str, None, None]:

        logger.info("Streaming request started.")

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

            yield (
                f"data: {json.dumps({'type': 'start'})}\n\n"
            )

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
                # Capture OpenAI response ID
                # ------------------------------------------
                if hasattr(event, "response") and event.response:
                    response_id = getattr(
                        event.response,
                        "id",
                        response_id,
                    )

                # ------------------------------------------
                # Stream text deltas
                # ------------------------------------------
                if event.type == "response.output_text.delta":

                    assistant_text += event.delta

                    payload = {
                        "type": "delta",
                        "text": event.delta,
                    }

                    yield (
                        f"data: {json.dumps(payload)}\n\n"
                    )

                # ------------------------------------------
                # Optional logging
                # ------------------------------------------
                elif event.type == "response.created":

                    logger.info(
                        "OpenAI response created."
                    )

                elif event.type == "response.completed":

                    logger.info(
                        "OpenAI response completed."
                    )

                elif event.type == "response.failed":

                    logger.error(
                        "OpenAI response failed."
                    )

                elif event.type == "error":

                    logger.error(event)

            # ------------------------------------------
            # Save assistant message
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
            # ------------------------------------------
            # Notify frontend that streaming completed
            # ------------------------------------------
            payload = {
                "type": "completed",
                "response_id": response_id,
            }

            yield (
                f"data: {json.dumps(payload)}\n\n"
            )

            logger.info("Streaming completed.")

        except Exception as ex:

            logger.exception("Streaming failed.")

            payload = {
                "type": "error",
                "message": str(ex),
            }

            yield (
                f"data: {json.dumps(payload)}\n\n"
            )


chat_service = ChatService()