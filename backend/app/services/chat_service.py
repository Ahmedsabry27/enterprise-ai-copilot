import logging

from app.core.openai_client import client

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

    def ask(
        self,
        message: str,
        previous_response_id: str | None = None,
    ):
        logger.info("Incoming request")

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

            logger.info("OpenAI response generated.")

            return {
                "response": response.output_text,
                "response_id": response.id,
            }

        except Exception:
            logger.exception("OpenAI request failed.")
            raise


chat_service = ChatService()