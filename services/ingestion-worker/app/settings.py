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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
