
from __future__ import annotations

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"

    # Default provider used when a request or agent does not specify one.
    AI_PROVIDER: Literal["openai", "bedrock"] = "openai"

    # OpenAI configuration
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4.1-mini"

    # Amazon Bedrock configuration
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "amazon.nova-lite-v1:0"
    # Optional inference-profile ID/ARN used for invocation while preserving
    # BEDROCK_MODEL_ID as the model shown in product and audit surfaces.
    BEDROCK_INFERENCE_PROFILE_ID: str | None = None
    BEDROCK_MAX_TOKENS: int = 2048
    BEDROCK_TEMPERATURE: float = 0.2
    BEDROCK_TOP_P: float = 0.9
    AUTO_AGENT_MIN_CONFIDENCE: float = 0.55

    # Database configuration
    DATABASE_URL: str | None = None
    DATABASE_SECRET_ARN: str | None = None
    DATABASE_HOST: str | None = None
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "enterprise_ai_copilot"

    # Cognito configuration
    COGNITO_REGION: str | None = None
    COGNITO_USER_POOL_ID: str | None = None
    COGNITO_CLIENT_ID: str | None = None

    # API and runtime configuration
    CORS_ALLOWED_ORIGINS: str = ""
    TRUSTED_HOSTS: str = ""
    RUN_SCHEMA_CREATE: bool = False
    SYNC_TOOL_CATALOG_ON_STARTUP: bool = False
    ENABLE_API_DOCS: bool = False

    @property
    def production(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod"}

    @property
    def default_ai_provider(self) -> str:
        return self.AI_PROVIDER.lower().strip()

    @property
    def default_ai_model(self) -> str:
        if self.default_ai_provider == "bedrock":
            return self.BEDROCK_MODEL_ID
        return self.OPENAI_MODEL

    @property
    def cors_origins(self) -> list[str]:
        configured = [
            value.strip().rstrip("/")
            for value in self.CORS_ALLOWED_ORIGINS.split(",")
            if value.strip()
        ]

        if configured:
            return configured

        if self.production:
            return []

        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

    @property
    def trusted_hosts(self) -> list[str]:
        return [
            value.strip()
            for value in self.TRUSTED_HOSTS.split(",")
            if value.strip()
        ]

    @model_validator(mode="after")
    def validate_settings(self) -> Settings:
        if not 0 <= self.BEDROCK_TEMPERATURE <= 1:
            raise ValueError(
                "BEDROCK_TEMPERATURE must be between 0 and 1"
            )

        if not 0 <= self.BEDROCK_TOP_P <= 1:
            raise ValueError(
                "BEDROCK_TOP_P must be between 0 and 1"
            )

        if self.BEDROCK_MAX_TOKENS <= 0:
            raise ValueError(
                "BEDROCK_MAX_TOKENS must be greater than 0"
            )

        if self.production:
            missing: list[str] = []

            if not (self.DATABASE_SECRET_ARN or self.DATABASE_URL):
                missing.append(
                    "DATABASE_SECRET_ARN or DATABASE_URL"
                )

            if not self.CORS_ALLOWED_ORIGINS:
                missing.append("CORS_ALLOWED_ORIGINS")

            for name in (
                "COGNITO_REGION",
                "COGNITO_USER_POOL_ID",
                "COGNITO_CLIENT_ID",
            ):
                if not getattr(self, name):
                    missing.append(name)

            if (
                self.default_ai_provider == "openai"
                and not self.OPENAI_API_KEY
            ):
                missing.append("OPENAI_API_KEY")

            if (
                self.default_ai_provider == "bedrock"
                and not self.AWS_REGION
            ):
                missing.append("AWS_REGION")

            if (
                self.default_ai_provider == "bedrock"
                and not self.BEDROCK_MODEL_ID
            ):
                missing.append("BEDROCK_MODEL_ID")

            if self.RUN_SCHEMA_CREATE:
                raise ValueError(
                    "RUN_SCHEMA_CREATE is forbidden in production"
                )

            if missing:
                raise ValueError(
                    "Missing production settings: "
                    + ", ".join(missing)
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
