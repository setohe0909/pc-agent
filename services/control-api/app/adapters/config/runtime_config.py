import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

CONFIG_PATH = Path(os.getenv("RUNTIME_CONFIG_PATH", "runtime-config.json"))

PUBLIC_KEYS = {
    "open_claw_base_url",
    "mentis_base_url",
    "mentis_enabled",
    "langfuse_host",
    "langfuse_enabled",
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
    "instagram_access_token",
    "tiktok_api_key",
    "marketing_brand_type",
    "marketing_tone",
    "marketing_poll_frequency",
}


class RuntimeConfigUpdate(BaseModel):
    open_claw_base_url: str | None = Field(default=None, max_length=2048)
    mentis_base_url: str | None = Field(default=None, max_length=2048)
    mentis_enabled: bool | None = None
    langfuse_host: str | None = Field(default=None, max_length=2048)
    langfuse_enabled: bool | None = None
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
    instagram_access_token: str | None = Field(default=None, max_length=4096)
    instagram_account_id: str | None = Field(default=None, max_length=4096)
    tiktok_api_key: str | None = Field(default=None, max_length=4096)
    tiktok_user_id: str | None = Field(default=None, max_length=4096)
    marketing_brand_type: str | None = Field(default=None, max_length=80)
    marketing_tone: str | None = Field(default=None, max_length=80)
    marketing_poll_frequency: str | None = Field(default=None, max_length=80)

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

    async def sync_to_supabase(self, supabase_url: str, service_role_key: str) -> bool:
        """Sincroniza el archivo local con la tabla system_config en Supabase."""
        import httpx
        current = self.read()
        headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        endpoint = f"{supabase_url}/rest/v1/system_config"
        payload = {
            "id": "default",
            "config": current
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)
                return resp.status_code < 400
        except Exception as e:
            print(f"[ERROR] Fallo sincronización a Supabase: {e}")
            return False

    async def load_from_supabase(self, supabase_url: str, service_role_key: str) -> bool:
        """Carga la configuración desde Supabase al archivo local."""
        import httpx
        headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
        }
        endpoint = f"{supabase_url}/rest/v1/system_config?id=eq.default&select=config"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(endpoint, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data and "config" in data[0]:
                        remote_config = data[0]["config"]
                        self.path.write_text(json.dumps(remote_config, indent=2, sort_keys=True), encoding="utf-8")
                        return True
            return False
        except Exception as e:
            print(f"[ERROR] Fallo carga desde Supabase: {e}")
            return False
