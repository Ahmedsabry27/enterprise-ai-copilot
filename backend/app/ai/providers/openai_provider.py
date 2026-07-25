import logging
import time
from collections.abc import Generator, Sequence

from openai import AuthenticationError, RateLimitError

from app.ai.adapters.openai_adapter import OpenAIAdapter
from app.ai.base import AIProvider
from app.ai.exceptions import (
    AIAuthenticationError,
    AIProviderError,
    AIRateLimitError,
    AIUnknownError,
)
from app.ai.models import (
    AIMessage,
    AIResponse,
    AIStreamEvent,
    AIUsage,
)
from app.core.openai_client import client
from app.metrics.metrics import (
    completion_tokens_total,
    openai_errors_total,
    openai_latency_seconds,
    openai_requests_total,
    prompt_tokens_total,
    total_tokens_total,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):

    MODEL = "gpt-4.1-mini"

    def ask(
        self,
        messages: Sequence[AIMessage],
    ) -> AIResponse:

        try:

            start = time.perf_counter()

            response = client.responses.create(
                model=self.MODEL,
                input=OpenAIAdapter.to_input(messages),
            )

            latency = time.perf_counter() - start

            openai_requests_total.inc()
            openai_latency_seconds.observe(latency)

            usage = self._build_usage(response)

            return AIResponse(
                text=response.output_text,
                response_id=response.id,
                model=self.MODEL,
                latency_seconds=latency,
                usage=usage,
            )

        except RateLimitError as ex:
            openai_errors_total.inc()
            raise AIRateLimitError(str(ex)) from ex

        except AuthenticationError as ex:
            openai_errors_total.inc()
            raise AIAuthenticationError(str(ex)) from ex

        except Exception as ex:
            openai_errors_total.inc()
            raise AIUnknownError(str(ex)) from ex

    def stream(
        self,
        messages: Sequence[AIMessage],
    ) -> Generator[AIStreamEvent, None, None]:

        try:

            openai_requests_total.inc()

            start = time.perf_counter()

            stream = client.responses.create(
                model=self.MODEL,
                input=OpenAIAdapter.to_input(messages),
                stream=True,
            )

            response_id = None

            yield AIStreamEvent(
                event_type="start",
                model=self.MODEL,
            )

            for event in stream:

                if hasattr(event, "response") and event.response:
                    response_id = getattr(
                        event.response,
                        "id",
                        response_id,
                    )

                if event.type == "response.output_text.delta":

                    yield AIStreamEvent(
                        event_type="delta",
                        text=event.delta,
                        model=self.MODEL,
                    )

                elif event.type == "response.completed":

                    latency = time.perf_counter() - start

                    openai_latency_seconds.observe(latency)

                    usage = None

                    if getattr(event, "response", None):
                        usage = self._build_usage(event.response)

                    yield AIStreamEvent(
                        event_type="completed",
                        response_id=response_id,
                        model=self.MODEL,
                        usage=usage,
                    )

                elif event.type == "response.failed":
                    raise AIProviderError("OpenAI stream failed")

        except AIProviderError:
            raise

        except RateLimitError as ex:
            openai_errors_total.inc()
            raise AIRateLimitError(str(ex)) from ex

        except AuthenticationError as ex:
            openai_errors_total.inc()
            raise AIAuthenticationError(str(ex)) from ex

        except Exception as ex:
            openai_errors_total.inc()
            raise AIUnknownError(str(ex)) from ex

    def _build_usage(self, response) -> AIUsage | None:

        usage = getattr(response, "usage", None)

        if usage is None:
            return None

        prompt_tokens_total.inc(usage.input_tokens)
        completion_tokens_total.inc(usage.output_tokens)
        total_tokens_total.inc(usage.total_tokens)

        logger.info(
            "openai_usage",
            extra={
                "model": self.MODEL,
                "prompt_tokens": usage.input_tokens,
                "completion_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            },
        )

        return AIUsage(
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
        )