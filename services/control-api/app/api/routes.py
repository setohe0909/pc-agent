import os
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, field_validator

from app.api.auth import require_admin
from app.adapters.config.ingestion_control import JsonIngestionControl
from app.adapters.config.in_memory import InMemoryKnowledgeSourceRepository
from app.adapters.config.probes import HttpSystemProbe
from app.adapters.config.runtime_config import RuntimeConfigStore, RuntimeConfigUpdate
from app.adapters.config.settings import settings
from app.adapters.mentis.repository import SupabaseMentisMemoryRepository
from app.adapters.supabase.client import SupabaseVectorKnowledgeBase
from app.adapters.whatsapp.repository import SupabaseWhatsAppOutreachRepository
from app.application.use_cases import (
    CheckSystemStatus,
    CreateWhatsAppCampaign,
    GetIngestionSchedule,
    ListWhatsAppCampaigns,
    ListWhatsAppContacts,
    ListIngestionRuns,
    ListConsolidationHistory,
    ListMemoryFragments,
    ListKnowledgeSources,
    RegisterKnowledgeSource,
    ClearMemoryContext,
    TriggerIngestionRun,
    UpsertWhatsAppContact,
    UpdateIngestionSchedule,
    VerifyMentisHealth,
    VerifySupabaseVectorStore,
)
from app.domain.models import DiscordConfig, IngestionSchedule, KnowledgeSource, SourceType, WhatsAppCampaign, WhatsAppContact

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
    target: str = Field(pattern="^(markets|trends|mentis|consolidation|all)$")


class WhatsAppContactRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=32, pattern=r"^\+?[0-9]{8,32}$")
    display_name: str | None = Field(default=None, max_length=160)
    source: str = Field(default="manual", max_length=80)
    consent_status: str = Field(default="opted_in", pattern="^(opted_in|opted_out|unknown)$")
    tags: list[str] = Field(default_factory=list, max_length=20)
    metadata: dict = Field(default_factory=dict)


class WhatsAppCampaignRequest(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    message_template: str = Field(min_length=5, max_length=2000)
    target_tag: str | None = Field(default=None, max_length=80)
    scheduled_for: datetime | None = None
    metadata: dict = Field(default_factory=dict)


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
            "openai_admin_api_key_configured": bool(runtime.get("openai_admin_api_key") or os.getenv("OPENAI_ADMIN_API_KEY")),
            "gemini_api_key_configured": bool(runtime.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")),
            "together_api_key_configured": bool(runtime.get("together_api_key") or os.getenv("TOGETHER_API_KEY")),
            "langfuse_public_key_configured": bool(runtime.get("langfuse_public_key") or settings.langfuse_public_key),
            "langfuse_secret_key_configured": bool(runtime.get("langfuse_secret_key") or settings.langfuse_secret_key),
            "kalshi_configured": bool(
                (runtime.get("kalshi_username") or settings.kalshi_username) and 
                (runtime.get("kalshi_password") or settings.kalshi_password)
            ),
            "openwa": {
                "base_url": settings.effective("openwa_base_url"),
                "session_id": settings.effective("openwa_session_id"),
                "configured": bool(runtime.get("openwa_api_key") or settings.openwa_api_key),
            },
            "coder_web": {
                "has_github_auth": bool(runtime.get("github_token")),
                "stack": runtime.get("coder_web_stack", "react-ts")
            }
        },
    }


@router.get("/config/runtime")
async def get_runtime_config() -> dict:
    return {"runtime": runtime_config_store.public_view()}


@router.get("/models/usage")
async def model_usage() -> dict:
    runtime = runtime_config_store.read()
    start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = datetime.utcnow()
    providers = [
        await _openai_usage(runtime, start),
        _static_provider_usage(
            provider="gemini",
            configured=bool(runtime.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")),
            budget=runtime.get("gemini_monthly_budget_usd"),
            detail=(
                "Gemini expone límites por proyecto en AI Studio/Google Cloud. "
                "Para consumo live se debe conectar Cloud Monitoring o exportar billing del proyecto."
            ),
        ),
        _static_provider_usage(
            provider="together",
            configured=bool(runtime.get("together_api_key") or os.getenv("TOGETHER_API_KEY")),
            budget=runtime.get("together_monthly_budget_usd"),
            detail=(
                "Together entrega rate limits en respuestas y gasto en su dashboard. "
                "Podemos volverlo live registrando usage por request en Langfuse/Supabase."
            ),
        ),
    ]
    return {
        "period": {
            "start": start.date().isoformat(),
            "end": end.date().isoformat(),
            "label": "Mes actual",
        },
        "providers": providers,
    }


@router.put("/config/runtime", dependencies=[Depends(require_admin)])
async def update_runtime_config(request: RuntimeConfigUpdate) -> dict:
    updated = runtime_config_store.update(request)
    
    # Intentar sincronizar con Supabase si está configurado
    s_url = settings.effective("supabase_url")
    s_key = settings.effective("supabase_service_role_key")
    if s_url and s_key:
        await runtime_config_store.sync_to_supabase(s_url, s_key)
        
    return {"runtime": updated}


async def _openai_usage(runtime: dict, start: datetime) -> dict:
    budget = runtime.get("openai_monthly_budget_usd")
    admin_key = runtime.get("openai_admin_api_key") or os.getenv("OPENAI_ADMIN_API_KEY")
    configured = bool(runtime.get("openai_api_key") or os.getenv("OPENAI_API_KEY"))
    base = {
        "provider": "openai",
        "configured": configured,
        "unit": "USD",
        "used": None,
        "limit": budget,
        "source": "OpenAI Costs API",
    }
    if not configured:
        return {**base, "status": "not_configured", "detail": "Falta OPENAI_API_KEY."}
    if not admin_key:
        return {
            **base,
            "status": "needs_admin_key",
            "detail": "Configura OPENAI_ADMIN_API_KEY para consultar consumo real de la organización.",
        }

    try:
        params = {
            "start_time": int(start.timestamp()),
            "bucket_width": "1d",
            "limit": 31,
        }
        headers = {"Authorization": f"Bearer {admin_key}"}
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get("https://api.openai.com/v1/organization/costs", headers=headers, params=params)
        if resp.status_code >= 400:
            return {
                **base,
                "status": "error",
                "detail": f"OpenAI Costs API respondió HTTP {resp.status_code}.",
            }
        total = 0.0
        for bucket in resp.json().get("data", []):
            for result in bucket.get("results", []):
                amount = result.get("amount", {})
                total += float(amount.get("value") or 0)
        return {
            **base,
            "status": "live",
            "used": round(total, 4),
            "detail": "Consumo real del mes actual consultado desde OpenAI.",
        }
    except Exception as exc:
        return {
            **base,
            "status": "error",
            "detail": f"No se pudo consultar OpenAI Costs API: {exc}",
        }


def _static_provider_usage(provider: str, configured: bool, budget: float | None, detail: str) -> dict:
    return {
        "provider": provider,
        "configured": configured,
        "status": "manual_limit" if configured else "not_configured",
        "used": None,
        "limit": budget,
        "unit": "USD",
        "source": "Configuración local",
        "detail": detail if configured else f"Falta configurar la API key de {provider}.",
    }


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
    use_case = VerifyMentisHealth(_mentis_memory_repository())
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
    try:
        memory = await ListMemoryFragments(_mentis_memory_repository()).execute(context=context, limit=50)
        return {"memory": memory}
    except Exception as exc:
        return {"memory": [], "detail": str(exc)}


@router.get("/mentis/memory")
async def get_mentis_memory(context: str | None = None):
    return await get_today_intelligence(context)


@router.delete("/intelligence/memory/today")
async def clear_today_intelligence(context: str | None = None):
    try:
        deleted = await ClearMemoryContext(_mentis_memory_repository()).execute(context=context)
        return {
            "status": "success",
            "deleted": deleted,
            "message": f"Memoria ({context or 'general'}) eliminada correctamente.",
        }
    except Exception as exc:
        print(f"[MEMORY DELETE ERROR] Unexpected error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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


@router.get("/marketing/whatsapp")
async def get_whatsapp_outreach() -> dict:
    repository = _whatsapp_outreach_repository()
    try:
        contacts = await ListWhatsAppContacts(repository).execute(limit=200)
        campaigns = await ListWhatsAppCampaigns(repository).execute(limit=100)
        return {"contacts": contacts, "campaigns": campaigns}
    except Exception as exc:
        return {"contacts": [], "campaigns": [], "detail": str(exc)}


@router.post("/marketing/whatsapp/contacts", dependencies=[Depends(require_admin)])
async def upsert_whatsapp_contact(request: WhatsAppContactRequest) -> dict:
    repository = _whatsapp_outreach_repository()
    contact = WhatsAppContact(**request.model_dump())
    try:
        saved = await UpsertWhatsAppContact(repository).execute(contact)
        return {"contact": saved}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/marketing/whatsapp/campaigns", dependencies=[Depends(require_admin)])
async def create_whatsapp_campaign(request: WhatsAppCampaignRequest) -> dict:
    repository = _whatsapp_outreach_repository()
    campaign = WhatsAppCampaign(**request.model_dump())
    try:
        saved = await CreateWhatsAppCampaign(repository).execute(campaign)
        return {"campaign": saved}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/intelligence/memory/consolidation")
async def get_consolidation_history():
    try:
        history = await ListConsolidationHistory(_mentis_memory_repository()).execute()
        return {"history": history}
    except Exception as exc:
        return {"history": [], "detail": str(exc)}


def _supabase_knowledge_base() -> SupabaseVectorKnowledgeBase:
    return SupabaseVectorKnowledgeBase(
        url=settings.effective("supabase_url"),
        publishable_key=settings.effective("supabase_publishable_key"),
        service_role_key=settings.effective("supabase_service_role_key"),
    )


def _mentis_memory_repository() -> SupabaseMentisMemoryRepository:
    return SupabaseMentisMemoryRepository(
        url=settings.effective("supabase_url"),
        publishable_key=settings.effective("supabase_publishable_key"),
        service_role_key=settings.effective("supabase_service_role_key"),
    )


def _whatsapp_outreach_repository() -> SupabaseWhatsAppOutreachRepository:
    return SupabaseWhatsAppOutreachRepository(
        url=settings.effective("supabase_url"),
        service_role_key=settings.effective("supabase_service_role_key"),
    )


def _knowledge_source_repository(require_persistence: bool = False):
    if settings.effective("supabase_url") and settings.effective("supabase_publishable_key"):
        return _supabase_knowledge_base()
    if require_persistence:
        raise RuntimeError("Supabase debe estar configurado para acciones administrativas persistentes.")
    return source_repository
