import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

CONFIG_PATH = Path(os.getenv("RUNTIME_CONFIG_PATH", "runtime-config.json"))

PUBLIC_KEYS = {
    "open_claw_base_url",
    "mentis_base_url",
    "langfuse_host",
    "supabase_url",
    "embedding_provider",
    "embedding_model",
    "embedding_dimensions",
    "ollama_base_url",
    "discord_requests_channel_id",
    "discord_notifications_channel_id",
    "discord_status_channel_id",
    "discord_approver_user_ids",
    "default_llm_provider",
}

SECRET_KEYS = {
    "supabase_publishable_key",
    "supabase_service_role_key",
    "mentis_api_key",
    "langfuse_public_key",
    "langfuse_secret_key",
    "openai_api_key",
    "gemini_api_key",
    "minimax_api_key",
    "discord_bot_token",
}


class RuntimeConfigUpdate(BaseModel):
    open_claw_base_url: str | None = Field(default=None, max_length=2048)
    mentis_base_url: str | None = Field(default=None, max_length=2048)
    langfuse_host: str | None = Field(default=None, max_length=2048)
    supabase_url: str | None = Field(default=None, max_length=2048)
    supabase_publishable_key: str | None = Field(default=None, max_length=4096)
    supabase_service_role_key: str | None = Field(default=None, max_length=4096)
    embedding_provider: str | None = Field(default=None, max_length=80)
    embedding_model: str | None = Field(default=None, max_length=120)
    embedding_dimensions: int | None = Field(default=None, ge=1, le=8192)
    ollama_base_url: str | None = Field(default=None, max_length=2048)
    discord_requests_channel_id: str | None = Field(default=None, max_length=80)
    discord_notifications_channel_id: str | None = Field(default=None, max_length=80)
    discord_status_channel_id: str | None = Field(default=None, max_length=80)
    discord_approver_user_ids: str | None = Field(default=None, max_length=1000)
    discord_bot_token: str | None = Field(default=None, max_length=4096)
    default_llm_provider: str | None = Field(default=None, max_length=80)
    mentis_api_key: str | None = Field(default=None, max_length=4096)
    langfuse_public_key: str | None = Field(default=None, max_length=4096)
    langfuse_secret_key: str | None = Field(default=None, max_length=4096)
    openai_api_key: str | None = Field(default=None, max_length=4096)
    gemini_api_key: str | None = Field(default=None, max_length=4096)
    minimax_api_key: str | None = Field(default=None, max_length=4096)

    @field_validator("open_claw_base_url", "mentis_base_url", "langfuse_host", "supabase_url", "ollama_base_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.startswith(("http://", "https://")):
            raise ValueError("La URL debe iniciar con http:// o https://")
        return value.rstrip("/")


class RuntimeConfigStore:
    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self.path = path

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def public_view(self) -> dict[str, Any]:
        current = self.read()
        return {
            **{key: current[key] for key in PUBLIC_KEYS if key in current},
            "secrets": {key: bool(current.get(key)) for key in SECRET_KEYS},
        }

    def update(self, update: RuntimeConfigUpdate) -> dict[str, Any]:
        current = self.read()
        incoming = update.model_dump(exclude_unset=True)
        for key, value in incoming.items():
            if value in {None, ""}:
                continue
            current[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
        return self.public_view()
