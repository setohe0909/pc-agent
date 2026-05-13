import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, field_validator

from app.api.auth import require_admin
from app.adapters.config.ingestion_control import JsonIngestionControl
from app.adapters.config.in_memory import InMemoryKnowledgeSourceRepository
from app.adapters.config.probes import HttpSystemProbe
from app.adapters.config.runtime_config import RuntimeConfigStore, RuntimeConfigUpdate
from app.adapters.config.settings import settings
from app.adapters.mentis.client import MentisHttpMemory
from app.adapters.supabase.client import SupabaseVectorKnowledgeBase
from app.application.use_cases import (
    CheckSystemStatus,
    GetIngestionSchedule,
    ListIngestionRuns,
    ListKnowledgeSources,
    RegisterKnowledgeSource,
    TriggerIngestionRun,
    UpdateIngestionSchedule,
    VerifyMentisHealth,
    VerifySupabaseVectorStore,
)
from app.domain.models import DiscordConfig, IngestionSchedule, KnowledgeSource, SourceType

router = APIRouter()
source_repository = InMemoryKnowledgeSourceRepository()
runtime_config_store = RuntimeConfigStore()
ingestion_control = JsonIngestionControl()


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


class IngestionScheduleRequest(BaseModel):
    market_ingestion_cron: str = Field(max_length=120)
    trends_ingestion_cron: str = Field(max_length=120)
    mentis_sync_cron: str = Field(max_length=120)

    @field_validator("market_ingestion_cron", "trends_ingestion_cron", "mentis_sync_cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        try:
            CronTrigger.from_crontab(value)
        except ValueError as exc:
            raise ValueError("Cron invalido. Usa formato de 5 campos, por ejemplo: 0 */2 * * *") from exc
        return value


class TriggerIngestionRequest(BaseModel):
    target: str = Field(pattern="^(markets|trends|mentis|all)$")


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
            "mentis_enabled": settings.effective("mentis_enabled"),
            "langfuse": settings.effective("langfuse_host"),
            "langfuse_enabled": settings.effective("langfuse_enabled"),
            "supabase": {
                "url": settings.effective("supabase_url"),
                "embedding_provider": settings.effective("embedding_provider"),
                "embedding_model": settings.effective("embedding_model"),
                "embedding_dimensions": settings.effective("embedding_dimensions"),
                "has_publishable_key": bool(runtime.get("supabase_publishable_key") or settings.supabase_publishable_key),
                "has_service_role_key": bool(runtime.get("supabase_service_role_key") or settings.supabase_service_role_key),
            },
            "ollama": settings.effective("ollama_base_url"),
            "openai_api_key_configured": bool(runtime.get("openai_api_key") or os.getenv("OPENAI_API_KEY")),
            "gemini_api_key_configured": bool(runtime.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")),
            "langfuse_public_key_configured": bool(runtime.get("langfuse_public_key") or settings.langfuse_public_key),
            "langfuse_secret_key_configured": bool(runtime.get("langfuse_secret_key") or settings.langfuse_secret_key),
            "kalshi_configured": bool(
                (runtime.get("kalshi_username") or settings.kalshi_username) and 
                (runtime.get("kalshi_password") or settings.kalshi_password)
            ),
            "coder_web": {
                "has_wix_auth": bool(runtime.get("wix_api_key")),
                "has_github_auth": bool(runtime.get("github_token")),
                "stack": runtime.get("coder_web_stack", "react-ts")
            }
        },
    }


@router.get("/config/runtime")
async def get_runtime_config() -> dict:
    return {"runtime": runtime_config_store.public_view()}


@router.put("/config/runtime", dependencies=[Depends(require_admin)])
async def update_runtime_config(request: RuntimeConfigUpdate) -> dict:
    updated = runtime_config_store.update(request)
    
    # Intentar sincronizar con Supabase si está configurado
    s_url = settings.effective("supabase_url")
    s_key = settings.effective("supabase_service_role_key")
    if s_url and s_key:
        await runtime_config_store.sync_to_supabase(s_url, s_key)
        
    return {"runtime": updated}


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
    if not settings.effective("mentis_enabled"):
        return {
            "mentis": {
                "reachable": False,
                "can_read": False,
                "can_write": False,
                "detail": "MentisDB opcional desactivado. Activalo en Configuracion cuando el servicio este corriendo.",
                "enabled": False,
            }
        }
    use_case = VerifyMentisHealth(MentisHttpMemory(settings.effective("mentis_base_url")))
    return {"mentis": await use_case.execute(), "enabled": True}


@router.get("/supabase/verify")
async def verify_supabase() -> dict:
    knowledge_base = _supabase_knowledge_base()
    use_case = VerifySupabaseVectorStore(knowledge_base)
    return {"supabase": await use_case.execute()}


@router.get("/ingestion")
async def ingestion_status() -> dict:
    schedule = await GetIngestionSchedule(ingestion_control).execute()
    runs = await ListIngestionRuns(ingestion_control).execute()
    return {"schedule": schedule, "runs": runs}


@router.put("/ingestion/schedule", dependencies=[Depends(require_admin)])
async def update_ingestion_schedule(request: IngestionScheduleRequest) -> dict:
    schedule = IngestionSchedule(**request.model_dump())
    updated = await UpdateIngestionSchedule(ingestion_control).execute(schedule)
    return {"schedule": updated}


@router.post("/ingestion/runs", dependencies=[Depends(require_admin)])
async def trigger_ingestion_run(request: TriggerIngestionRequest) -> dict:
    worker_url = "http://ingestion-worker:8000"
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.post(f"{worker_url}/run/{request.target}")
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": f"No se pudo contactar al worker: {e}"}


@router.get("/intelligence/memory/today")
async def get_today_intelligence(context: str | None = None):
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    url = settings.effective("supabase_url")
    key = settings.effective("supabase_service_role_key") or settings.effective("supabase_publishable_key")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    
    # Determinar filtro segun el contexto
    if context == "marketer":
        category_filter = "&category=ilike.marketing_*"
    elif context == "picture":
        category_filter = "&category=ilike.picture_*"
    elif context == "coder-web":
        category_filter = "&category=ilike.coder-web_*"
    else:
        # Por defecto excluimos marketing, picture y coder-web para la memoria de inteligencia general
        category_filter = "&category=not.ilike.marketing_*,category=not.ilike.picture_*,category=not.ilike.coder-web_*"

    async with httpx.AsyncClient() as client:
        try:
            # Ya no filtramos por fecha diaria. Buscamos los registros más recientes (LTM)
            # para que el agente siempre tenga contexto evolutivo.
            query_url = f"{url}/rest/v1/mentis_memory?{category_filter[1:]}&order=created_at.desc&limit=50"
            response = await client.get(query_url, headers=headers)
            if response.status_code != 200:
                return {"memory": [], "detail": f"Error de Supabase: {response.text}"}
            return {"memory": response.json()}
        except Exception as e:
            return {"memory": [], "detail": str(e)}


@router.get("/mentis/memory")
async def get_mentis_memory(context: str | None = None):
    return await get_today_intelligence(context)


@router.delete("/intelligence/memory/today")
async def clear_today_intelligence(context: str | None = None):
    url = settings.effective("supabase_url")
    key = settings.effective("supabase_service_role_key") or settings.effective("supabase_publishable_key")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    
    # Determinar filtro segun el contexto
    if context == "marketer":
        category_filter = "category=ilike.marketing_*"
    elif context == "picture":
        category_filter = "category=ilike.picture_*"
    elif context == "coder-web":
        category_filter = "category=ilike.coder-web_*"
    else:
        category_filter = "category=not.ilike.marketing_*,category=not.ilike.picture_*,category=not.ilike.coder-web_*"

    async with httpx.AsyncClient() as client:
        try:
            query_url = f"{url}/rest/v1/mentis_memory?{category_filter}"
            response = await client.delete(query_url, headers=headers)
            if response.status_code not in [200, 204]:
                print(f"[MEMORY DELETE ERROR] Supabase returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Supabase Error: {response.text}")
            return {"status": "success", "message": f"Memoria ({context or 'general'}) eliminada correctamente."}
        except HTTPException:
            raise
        except Exception as e:
            print(f"[MEMORY DELETE ERROR] Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketing/leads")
async def get_marketing_leads():
    url = settings.effective("supabase_url")
    key = settings.effective("supabase_service_role_key") or settings.effective("supabase_publishable_key")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    
    async with httpx.AsyncClient() as client:
        try:
            query_url = f"{url}/rest/v1/marketing_leads?order=created_at.desc"
            response = await client.get(query_url, headers=headers)
            if response.status_code != 200:
                return {"leads": [], "detail": f"Error de Supabase: {response.text}"}
            return {"leads": response.json()}
        except Exception as e:
            return {"leads": [], "detail": str(e)}


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
