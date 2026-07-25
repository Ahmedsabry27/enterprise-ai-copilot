from functools import lru_cache

from app.ai.base import AIProvider
from app.ai.providers.bedrock_provider import BedrockProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import settings


class AIProviderFactory:

    @staticmethod
    @lru_cache(maxsize=1)
    def get_provider() -> AIProvider:

        provider = settings.AI_PROVIDER.lower()

        if provider == "openai":
            return OpenAIProvider()

        if provider == "bedrock":
            return BedrockProvider()

        raise ValueError(
            f"Unsupported AI provider: {provider}"
        )