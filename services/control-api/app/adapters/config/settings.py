from pydantic_settings import BaseSettings, SettingsConfigDict

from app.adapters.config.runtime_config import RuntimeConfigStore


class Settings(BaseSettings):
    environment: str = "local"
    admin_api_token: str = "change-me-admin-token"
    cors_allow_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
    open_claw_base_url: str = "http://assistant-runtime:8100"
    mentis_base_url: str = "http://mentisdb:9471"
    mentis_enabled: bool = False
    langfuse_host: str = "http://langfuse-web:3000"
    langfuse_enabled: bool = False
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    next_public_supabase_url: str = "https://gerhikdxsbglfdsupmsi.supabase.co"
    next_public_supabase_publishable_key: str = "sb_publishable_sV7xhYAjW0gg-2MXGk0MHg_jQ4l9GN9"
    supabase_url: str = "https://gerhikdxsbglfdsupmsi.supabase.co"
    supabase_publishable_key: str = "sb_publishable_sV7xhYAjW0gg-2MXGk0MHg_jQ4l9GN9"
    supabase_service_role_key: str | None = None
    vector_database_url: str = "postgresql://postgres:postgres@supabase-vector-db:5432/postgres"
    embedding_provider: str = "ollama"
    embedding_model: str = "mxbai-embed-large"
    embedding_dimensions: int = 1024
    ollama_base_url: str = "http://ollama:11434"
    discord_requests_channel_id: str | None = None
    discord_notifications_channel_id: str | None = None
    discord_status_channel_id: str | None = None
    discord_approver_user_ids: str | None = None
    discord_bot_token: str | None = None
    default_llm_provider: str = "openai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    def effective(self, key: str):
        runtime = RuntimeConfigStore().read()
        return runtime.get(key, getattr(self, key))


settings = Settings()
