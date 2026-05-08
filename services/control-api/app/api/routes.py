from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.api.auth import require_admin
from app.adapters.config.in_memory import InMemoryKnowledgeSourceRepository
from app.adapters.config.probes import HttpSystemProbe
from app.adapters.config.runtime_config import RuntimeConfigStore, RuntimeConfigUpdate
from app.adapters.config.settings import settings
from app.adapters.mentis.client import MentisHttpMemory
from app.adapters.supabase.client import SupabaseVectorKnowledgeBase
from app.application.use_cases import (
    CheckSystemStatus,
    ListKnowledgeSources,
    RegisterKnowledgeSource,
    VerifyMentisHealth,
    VerifySupabaseVectorStore,
)
from app.domain.models import DiscordConfig, KnowledgeSource, SourceType

router = APIRouter()
source_repository = InMemoryKnowledgeSourceRepository()
runtime_config_store = RuntimeConfigStore()


class KnowledgeSourceRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    source_type: SourceType
    url: str | None = Field(default=None, max_length=2048)
    schedule: str | None = Field(default=None, max_length=120)
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.startswith(("https://", "http://")):
            raise ValueError("La URL debe iniciar con http:// o https://")
        return value


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "control-api"}


@router.get("/status")
async def status() -> dict:
    use_case = CheckSystemStatus(HttpSystemProbe(settings))
    return {"services": await use_case.execute()}


@router.get("/config")
async def config() -> dict:
    runtime = runtime_config_store.read()
    return {
        "environment": settings.environment,
        "default_llm_provider": settings.effective("default_llm_provider"),
        "discord": DiscordConfig(
            requests_channel_id=settings.effective("discord_requests_channel_id"),
            notifications_channel_id=settings.effective("discord_notifications_channel_id"),
            status_channel_id=settings.effective("discord_status_channel_id"),
        ),
        "discord_control": {
            "approver_user_ids": settings.effective("discord_approver_user_ids"),
            "has_bot_token": bool(runtime.get("discord_bot_token") or settings.discord_bot_token),
        },
        "integrations": {
            "open_claw": settings.effective("open_claw_base_url"),
            "mentis": settings.effective("mentis_base_url"),
            "langfuse": settings.effective("langfuse_host"),
            "supabase": {
                "url": settings.effective("supabase_url"),
                "embedding_provider": settings.effective("embedding_provider"),
                "embedding_model": settings.effective("embedding_model"),
                "embedding_dimensions": settings.effective("embedding_dimensions"),
                "has_publishable_key": bool(runtime.get("supabase_publishable_key") or settings.supabase_publishable_key),
                "has_service_role_key": bool(runtime.get("supabase_service_role_key") or settings.supabase_service_role_key),
            },
            "ollama": settings.effective("ollama_base_url"),
        },
    }


@router.get("/config/runtime")
async def get_runtime_config() -> dict:
    return {"runtime": runtime_config_store.public_view()}


@router.put("/config/runtime", dependencies=[Depends(require_admin)])
async def update_runtime_config(request: RuntimeConfigUpdate) -> dict:
    return {"runtime": runtime_config_store.update(request)}


@router.get("/knowledge-sources")
async def list_knowledge_sources() -> dict:
    repository = _knowledge_source_repository()
    use_case = ListKnowledgeSources(repository)
    return {"sources": await use_case.execute()}


@router.post("/knowledge-sources", dependencies=[Depends(require_admin)])
async def add_knowledge_source(request: KnowledgeSourceRequest) -> dict:
    repository = _knowledge_source_repository(require_persistence=True)
    use_case = RegisterKnowledgeSource(repository)
    source = KnowledgeSource(**request.model_dump())
    try:
        return {"source": await use_case.execute(source)}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/mentis/verify")
async def verify_mentis() -> dict:
    use_case = VerifyMentisHealth(MentisHttpMemory(settings.effective("mentis_base_url")))
    return {"mentis": await use_case.execute()}


@router.get("/supabase/verify")
async def verify_supabase() -> dict:
    knowledge_base = _supabase_knowledge_base()
    use_case = VerifySupabaseVectorStore(knowledge_base)
    return {"supabase": await use_case.execute()}


def _supabase_knowledge_base() -> SupabaseVectorKnowledgeBase:
    return SupabaseVectorKnowledgeBase(
        url=settings.effective("supabase_url"),
        publishable_key=settings.effective("supabase_publishable_key"),
        service_role_key=settings.effective("supabase_service_role_key"),
    )


def _knowledge_source_repository(require_persistence: bool = False):
    if settings.effective("supabase_url") and settings.effective("supabase_publishable_key"):
        return _supabase_knowledge_base()
    if require_persistence:
        raise RuntimeError("Supabase debe estar configurado para acciones administrativas persistentes.")
    return source_repository
