import json
import os
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, field_validator

from app.api.auth import require_admin
from app.adapters.assistant_runtime import HttpAssistantRuntimeGateway
from app.adapters.config.ingestion_control import JsonIngestionControl
from app.adapters.config.in_memory import InMemoryKnowledgeSourceRepository
from app.adapters.config.probes import HttpSystemProbe
from app.adapters.config.runtime_config import RuntimeConfigStore, RuntimeConfigUpdate
from app.adapters.config.settings import settings
from app.adapters.speech_transcription import OpenAISpeechTranscriber
from app.adapters.mentis.repository import SupabaseMentisMemoryRepository
from app.adapters.supabase.client import SupabaseVectorKnowledgeBase
from app.adapters.whatsapp.repository import SupabaseWhatsAppOutreachRepository
from app.application.use_cases import (
    CheckSystemStatus,
    CreateWhatsAppCampaign,
    DecideWhatsAppCampaign,
    GetIngestionSchedule,
    ListWhatsAppCampaigns,
    ListWhatsAppContacts,
    ListIngestionRuns,
    ListConsolidationHistory,
    ListMemoryFragments,
    ListKnowledgeSources,
    RegisterKnowledgeSource,
    ClearMemoryContext,
    SubmitAssistantRequest,
    TranscribeAssistantAudio,
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


class WhatsAppCampaignDecisionRequest(BaseModel):
    approved: bool
    decided_by: str = Field(min_length=1, max_length=120)


class AssistantSourceRequest(BaseModel):
    platform: str = Field(default="admin", min_length=2, max_length=40)
    channel_id: str | None = Field(default="assistance-ui", max_length=120)
    user_id: str | None = Field(default="admin", max_length=120)


class AssistantProxyRequest(BaseModel):
    action_type: str = Field(default="orchestrator", pattern="^(chat|orchestrator|research|trade_decision|open_position|marketing|writer|picture|coder-web|email|model_status)$")
    prompt: str = Field(min_length=1, max_length=8000)
    source: AssistantSourceRequest = Field(default_factory=AssistantSourceRequest)
    payload: dict = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list, max_length=4)
    image_metadata: list[dict] = Field(default_factory=list)


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
                "stack": runtime.get("coder_web_stack", "react-ts"),
                "repository": runtime.get("coder_web_repository"),
                "private_repo": runtime.get("coder_web_private_repo", True),
                "has_preview_hook": bool(runtime.get("coder_web_preview_deploy_hook_url")),
                "has_linear_api_key": bool(runtime.get("linear_api_key")),
            },
            "email": {
                "provider": settings.effective("email_provider") or "not_configured",
                "account_id": settings.effective("email_account_id"),
                "send_enabled": bool(settings.effective("email_send_enabled")),
                "bulk_rate_limit": settings.effective("email_bulk_rate_limit") or 30,
                "outlook_tenant_id": settings.effective("email_outlook_tenant_id"),
                "imap_host": settings.effective("email_imap_host"),
                "smtp_host": settings.effective("email_smtp_host"),
                "username": settings.effective("email_username"),
                "pc_client_bridge_url": settings.effective("email_pc_client_bridge_url"),
                "has_google_oauth": bool(runtime.get("email_google_client_id") and runtime.get("email_google_client_secret")),
                "has_outlook_oauth": bool(
                    runtime.get("email_outlook_client_id")
                    and runtime.get("email_outlook_client_secret")
                    and runtime.get("email_outlook_tenant_id")
                ),
                "has_imap_smtp": bool(runtime.get("email_imap_host") and runtime.get("email_smtp_host") and runtime.get("email_username") and runtime.get("email_password")),
                "has_pc_client_bridge": bool(runtime.get("email_pc_client_bridge_url")),
                "template_count": _json_list_count(runtime.get("email_templates")),
                "category_count": _json_list_count(runtime.get("email_categories")),
            }
        },
    }


def _json_list_count(value) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return 0
        return len(parsed) if isinstance(parsed, list) else 0
    return 0


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
            detail=(
                "Gemini API Key no expone consumo/límite por endpoint REST. "
                "Para datos oficiales hay que conectar Google Cloud Service Usage/Monitoring del proyecto."
            ),
        ),
        _static_provider_usage(
            provider="together",
            configured=bool(runtime.get("together_api_key") or os.getenv("TOGETHER_API_KEY")),
            detail=(
                "No se muestra límite manual. El consumo/límite debe venir de endpoint oficial del proveedor "
                "o de headers oficiales capturados en requests reales."
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


@router.post("/assistant/request", dependencies=[Depends(require_admin)])
async def submit_assistant_request(request: AssistantProxyRequest) -> dict:
    runtime_url = str(settings.effective("open_claw_base_url") or settings.open_claw_base_url)
    gateway = HttpAssistantRuntimeGateway(runtime_url)
    use_case = SubmitAssistantRequest(gateway)
    try:
        return await use_case.execute(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] if exc.response is not None else str(exc)
        upstream_status = exc.response.status_code if exc.response is not None else "unknown"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Assistant runtime HTTP {upstream_status}: {detail}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"No se pudo contactar assistant-runtime: {exc}") from exc


@router.post("/assistant/transcribe", dependencies=[Depends(require_admin)])
async def transcribe_assistant_audio(
    audio: UploadFile = File(...),
    language: str = Form(default="es"),
) -> dict:
    api_key = settings.effective("openai_api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Falta configurar OPENAI_API_KEY para transcribir audio desde el navegador.",
        )
    content = await audio.read()
    use_case = TranscribeAssistantAudio(
        OpenAISpeechTranscriber(
            api_key=api_key,
            model=str(settings.effective("speech_to_text_model") or "gpt-4o-mini-transcribe"),
        )
    )
    try:
        return await use_case.execute(
            audio=content,
            filename=audio.filename or "speech.webm",
            content_type=audio.content_type or "application/octet-stream",
            language=language or "es",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] if exc.response is not None else str(exc)
        upstream_status = exc.response.status_code if exc.response is not None else "unknown"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"STT HTTP {upstream_status}: {detail}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"No se pudo contactar el servicio STT: {exc}") from exc


async def _openai_usage(runtime: dict, start: datetime) -> dict:
    admin_key = runtime.get("openai_admin_api_key") or os.getenv("OPENAI_ADMIN_API_KEY")
    configured = bool(runtime.get("openai_api_key") or os.getenv("OPENAI_API_KEY"))
    base = {
        "provider": "openai",
        "configured": configured,
        "unit": "USD",
        "used": None,
        "limit": None,
        "source": "OpenAI Costs API",
        "limit_source": "No hay endpoint público de límite mensual en la Costs API.",
    }
    if not configured:
        return {**base, "status": "not_configured", "detail": "Falta OPENAI_API_KEY."}
    if not admin_key:
        return {
            **base,
            "status": "needs_admin_key",
            "detail": "Configura OPENAI_ADMIN_API_KEY para consultar consumo real desde el endpoint oficial de OpenAI.",
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
            "detail": "Consumo real del mes actual consultado desde OpenAI. Límite mensual no disponible en este endpoint.",
        }
    except Exception as exc:
        return {
            **base,
            "status": "error",
            "detail": f"No se pudo consultar OpenAI Costs API: {exc}",
        }


def _static_provider_usage(provider: str, configured: bool, detail: str) -> dict:
    return {
        "provider": provider,
        "configured": configured,
        "status": "official_endpoint_required" if configured else "not_configured",
        "used": None,
        "limit": None,
        "unit": "USD",
        "source": "Endpoint oficial no conectado",
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
    worker_url = str(settings.effective("ingestion_worker_base_url") or "http://ingestion-worker:8000").rstrip("/")
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.post(f"{worker_url}/run/{request.target}")
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": f"No se pudo contactar al worker: {e}"}


@router.get("/intelligence/memory/today")
async def get_today_intelligence(context: str | None = None, limit: int = 50):
    try:
        memory = await ListMemoryFragments(_mentis_memory_repository()).execute(context=context, limit=limit)
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


@router.get("/email/jobs")
async def get_email_jobs(limit: int = 50) -> dict:
    try:
        return {"jobs": await _list_email_jobs(limit=limit)}
    except Exception as exc:
        return {"jobs": [], "detail": str(exc)}


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


@router.post("/marketing/whatsapp/campaigns/{campaign_id}/decision", dependencies=[Depends(require_admin)])
async def decide_whatsapp_campaign(campaign_id: str, request: WhatsAppCampaignDecisionRequest) -> dict:
    repository = _whatsapp_outreach_repository()
    try:
        campaign = await DecideWhatsAppCampaign(repository).execute(
            campaign_id=campaign_id,
            approved=request.approved,
            decided_by=request.decided_by,
        )
        return {"campaign": campaign}
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


async def _list_email_jobs(limit: int = 50) -> list[dict]:
    supabase_url = settings.effective("supabase_url")
    service_role_key = settings.effective("supabase_service_role_key")
    if not supabase_url or not service_role_key:
        raise RuntimeError("Supabase service role no configurado para listar jobs de email.")
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
    }
    async with httpx.AsyncClient(timeout=8) as client:
        jobs_response = await client.get(
            f"{str(supabase_url).rstrip('/')}/rest/v1/email_bulk_jobs",
            headers=headers,
            params={
                "select": "id,provider,account_id,template_name,category,status,requested_by,approved_by,recipient_count,created_at,updated_at,provider_result",
                "order": "created_at.desc",
                "limit": str(min(max(limit, 1), 200)),
            },
        )
        jobs_response.raise_for_status()
        jobs = jobs_response.json()
        for job in jobs:
            recipients_response = await client.get(
                f"{str(supabase_url).rstrip('/')}/rest/v1/email_bulk_job_recipients",
                headers=headers,
                params={
                    "job_id": f"eq.{job.get('id')}",
                    "select": "email_id,recipient,subject,status,provider_message_id,error_detail,created_at,updated_at",
                    "order": "created_at.asc",
                },
            )
            recipients_response.raise_for_status()
            job["recipients"] = recipients_response.json()
    return jobs


def _knowledge_source_repository(require_persistence: bool = False):
    if settings.effective("supabase_url") and settings.effective("supabase_publishable_key"):
        return _supabase_knowledge_base()
    if require_persistence:
        raise RuntimeError("Supabase debe estar configurado para acciones administrativas persistentes.")
    return source_repository
