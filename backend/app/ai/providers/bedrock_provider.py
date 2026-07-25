import logging
import time
from collections.abc import Generator, Sequence

from botocore.exceptions import BotoCoreError, ClientError

from app.ai.adapters.bedrock_adapter import BedrockAdapter
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
from app.core.bedrock_client import client
from app.metrics.metrics import (
    completion_tokens_total,
    openai_errors_total,
    openai_latency_seconds,
    openai_requests_total,
    prompt_tokens_total,
    total_tokens_total,
)

logger = logging.getLogger(__name__)


class BedrockProvider(AIProvider):

    MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def ask(
        self,
        messages: Sequence[AIMessage],
    ) -> AIResponse:

        try:

            start = time.perf_counter()

            system_prompt, conversation = BedrockAdapter.to_messages(messages)

            request = {
                "modelId": self.MODEL,
                "messages": conversation,
            }

            if system_prompt:
                request["system"] = [
                    {
                        "text": system_prompt,
                    }
                ]

            response = client.converse(**request)

            latency = time.perf_counter() - start

            openai_requests_total.inc()
            openai_latency_seconds.observe(latency)

            usage = self._build_usage(response)

            text = ""

            output = response.get("output", {})

            if output.get("message"):

                for item in output["message"]["content"]:

                    if "text" in item:
                        text += item["text"]

            return AIResponse(
                text=text,
                model=self.MODEL,
                latency_seconds=latency,
                usage=usage,
            )

        except ClientError as ex:

            openai_errors_total.inc()

            error_code = ex.response["Error"]["Code"]

            if error_code == "ThrottlingException":
                raise AIRateLimitError(str(ex)) from ex

            if error_code == "AccessDeniedException":
                raise AIAuthenticationError(str(ex)) from ex

            raise AIProviderError(str(ex)) from ex

        except BotoCoreError as ex:

            openai_errors_total.inc()
            raise AIUnknownError(str(ex)) from ex

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

            system_prompt, conversation = BedrockAdapter.to_messages(messages)

            request = {
                "modelId": self.MODEL,
                "messages": conversation,
            }

            if system_prompt:
                request["system"] = [
                    {
                        "text": system_prompt,
                    }
                ]

            stream = client.converse_stream(**request)

            yield AIStreamEvent(
                event_type="start",
                model=self.MODEL,
            )

            usage = None

            for event in stream["stream"]:

                if "contentBlockDelta" in event:

                    delta = event["contentBlockDelta"]["delta"]

                    if "text" in delta:

                        yield AIStreamEvent(
                            event_type="delta",
                            text=delta["text"],
                            model=self.MODEL,
                        )

                elif "metadata" in event:

                    usage = self._build_usage(event["metadata"])

            latency = time.perf_counter() - start

            openai_latency_seconds.observe(latency)

            yield AIStreamEvent(
                event_type="completed",
                model=self.MODEL,
                usage=usage,
            )

        except ClientError as ex:

            openai_errors_total.inc()

            error_code = ex.response["Error"]["Code"]

            if error_code == "ThrottlingException":
                raise AIRateLimitError(str(ex)) from ex

            if error_code == "AccessDeniedException":
                raise AIAuthenticationError(str(ex)) from ex

            raise AIProviderError(str(ex)) from ex

        except BotoCoreError as ex:

            openai_errors_total.inc()
            raise AIUnknownError(str(ex)) from ex

        except Exception as ex:

            openai_errors_total.inc()
            raise AIUnknownError(str(ex)) from ex

    def _build_usage(
        self,
        response: dict,
    ) -> AIUsage | None:

        usage = response.get("usage")

        if usage is None:
            return None

        prompt_tokens_total.inc(usage["inputTokens"])
        completion_tokens_total.inc(usage["outputTokens"])
        total_tokens_total.inc(usage["totalTokens"])

        logger.info(
            "bedrock_usage",
            extra={
                "model": self.MODEL,
                "prompt_tokens": usage["inputTokens"],
                "completion_tokens": usage["outputTokens"],
                "total_tokens": usage["totalTokens"],
            },
        )

        return AIUsage(
            prompt_tokens=usage["inputTokens"],
            completion_tokens=usage["outputTokens"],
            total_tokens=usage["totalTokens"],
        )