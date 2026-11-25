from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore", hide_input_in_errors=True)
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = ""
    llm_mode: Literal["mock", "live"] = "mock"
    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr = SecretStr("")
    langsmith_project: str = "careerpilot-ai-dev"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_workspace_id: str = ""
    langsmith_agent_id: str = ""
    langsmith_agent_environment: Literal["production", "staging", "development", "local"] = "development"
    langsmith_hide_inputs: bool = True
    langsmith_hide_outputs: bool = True
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://careerpilot:careerpilot_local@localhost:5432/careerpilot"
    )
    app_env: str = "development"
    max_revision_attempts: int = Field(default=2, ge=0, le=2)
    max_upload_mb: int = Field(default=10, ge=1, le=20)
    max_text_chars: int = Field(default=40000, ge=1000, le=100000)
    llm_timeout_seconds: int = Field(default=60, ge=5, le=180)
    llm_max_retries: int = Field(default=2, ge=0, le=3)
    llm_max_tokens: int = Field(default=6000, ge=1000, le=16000)
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @model_validator(mode="after")
    def validate_configuration(self):
        if self.llm_mode == "live" and (
            not self.openai_api_key.get_secret_value() or not self.openai_model.strip()
        ):
            raise ValueError("Live mode requires OPENAI_API_KEY and OPENAI_MODEL in backend/.env.")
        if self.langsmith_tracing and not self.langsmith_api_key.get_secret_value():
            raise ValueError("Tracing requires LANGSMITH_API_KEY in backend/.env.")
        if not self.database_url.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use PostgreSQL with the psycopg driver.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
