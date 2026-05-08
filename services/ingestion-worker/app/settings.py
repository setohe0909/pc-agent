import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str = "https://gerhikdxsbglfdsupmsi.supabase.co"
    supabase_publishable_key: str = "sb_publishable_sV7xhYAjW0gg-2MXGk0MHg_jQ4l9GN9"
    supabase_service_role_key: str | None = None
    ollama_base_url: str = "http://ollama:11434"
    embedding_model: str = "mxbai-embed-large"
    embedding_dimensions: int = 1024
    ingestion_max_sources_per_run: int = 20
    ingestion_max_documents_per_source: int = 5
    ingestion_chunk_chars: int = 3200
    market_ingestion_cron: str = "0 */2 * * *"
    trends_ingestion_cron: str = "15 */4 * * *"
    mentis_sync_cron: str = "30 */2 * * *"
    discord_bot_token: str | None = None
    discord_notifications_channel_id: str | None = None
    langfuse_host: str = "http://langfuse-web:3000"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

def apply_runtime_config(target_settings: Settings):
    config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
    try:
        if Path(config_path).exists():
            config = json.loads(Path(config_path).read_text(encoding="utf-8"))
            for key, value in config.items():
                if hasattr(target_settings, key) and value:
                    setattr(target_settings, key, value)
            print(f"Configuracion runtime aplicada a settings desde {config_path}")
    except Exception as exc:
        print(f"Error aplicando configuracion runtime: {exc}")

apply_runtime_config(settings)
