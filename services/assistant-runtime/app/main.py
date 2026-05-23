import os
import json
import base64
import binascii
import uuid
from pathlib import Path
from enum import Enum

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.adapters.email import ConfiguredEmailProvider, RuntimeEmailConfig
from app.adapters.email_jobs import FileEmailJobRepository, SupabaseEmailJobRepository
from app.use_cases.writer_workflow import WriterWorkflow
from app.use_cases.email_workflow import EmailWorkflow

def load_runtime_config():
    config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
    try:
        if Path(config_path).exists():
            config = json.loads(Path(config_path).read_text(encoding="utf-8"))
            for key, value in config.items():
                if value:
                    # Update environment so litellm and other components see it
                    env_key = key.upper()
                    os.environ[env_key] = str(value)
                    
                    # Litellm compatibility for Ollama
                    if env_key == "OLLAMA_BASE_URL":
                        os.environ["OLLAMA_API_BASE"] = str(value)
            print(f"Configuracion runtime cargada desde {config_path}")
    except Exception as exc:
        print(f"Error cargando configuracion runtime: {exc}")

load_runtime_config()

app = FastAPI(title="PC Agent Assistant Runtime")


class ActionType(str, Enum):
    chat = "chat"
    research = "research"
    trade_decision = "trade_decision"
    open_position = "open_position"
    marketing = "marketing"
    writer = "writer"
    picture = "picture"
    coder_web = "coder-web"
    email = "email"
    model_status = "model_status"


class Source(BaseModel):
    platform: str
    channel_id: str | None = None
    user_id: str | None = None


class Approval(BaseModel):
    status: str = "none"
    channel_id: str | None = None
    approver_user_id: str | None = None
    message_id: str | None = None


class AssistantRequest(BaseModel):
    action_type: ActionType = ActionType.chat
    prompt: str = Field(min_length=1, max_length=8000)
    source: Source
    approval: Approval | None = None
    images: list[str] = Field(default_factory=list) # Base64 images
    image_metadata: list[dict] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_COUNT = 4


def _format_internal_error(exc: Exception, request: AssistantRequest, stage: str) -> dict:
    raw_detail = str(exc) or repr(exc)
    error_type = type(exc).__name__
    sub_command = request.payload.get("sub_command", "chat") if isinstance(request.payload, dict) else "chat"
    hint = "Revisa los logs del assistant-runtime para el traceback completo."

    if isinstance(exc, KeyError):
        missing = str(exc).strip("'\"")
        raw_detail = f"Clave o valor esperado no encontrado: {missing}"
        if missing in {"object", "string", "array", "boolean", "number", "integer"}:
            hint = (
                "Parece un problema de schema de herramientas del LLM. "
                "Asegúrate de reiniciar/reconstruir assistant-runtime para cargar el adapter actualizado."
            )
        else:
            hint = f"El flujo intentó leer '{missing}' en una respuesta o payload que no lo tenía."
    elif "schema JSON incompatible" in raw_detail or "detección de herramientas" in raw_detail:
        hint = "El problema está en la detección de intención/tools del LLM, antes de ejecutar la acción."
    elif "429" in raw_detail or "quota" in raw_detail.lower():
        hint = "El proveedor LLM devolvió límite de cuota/rate limit. Cambia proveedor, revisa cuota o reintenta más tarde."
    elif "nodename nor servname" in raw_detail or "Name or service not known" in raw_detail:
        hint = "El servicio no pudo resolver/conectar a una dependencia externa desde el entorno actual."
    elif "ZERNIO" in raw_detail.upper() or "zernio" in raw_detail.lower():
        hint = "El problema parece venir de la integración Zernio o su respuesta."

    expose_details = os.getenv("EXPOSE_ERROR_DETAILS", "false").lower() == "true"
    public_detail = raw_detail if expose_details else "Detalle tecnico retenido por seguridad. Usa trace_id en logs."

    message = (
        f"No pude completar `{request.action_type.value}`"
        f" con subcomando `{sub_command}` durante `{stage}`.\n"
        f"Tipo: `{error_type}`\n"
        f"Detalle: {public_detail}\n"
        f"Pista: {hint}"
    )

    response = {
        "status": "error",
        "message": message,
        "error_type": error_type,
        "error_stage": stage,
        "hint": hint,
    }
    if expose_details:
        response["error_detail"] = raw_detail
    return response
    return response


def _assistant_response(result: dict, request: AssistantRequest) -> dict:
    return {
        "status": result.get("status", "accepted"),
        "provider": os.getenv("DEFAULT_LLM_PROVIDER", "openai"),
        "message": result.get("message") or "El asistente no pudo generar una respuesta de texto.",
        "order": result.get("order"),
        "critic_note": result.get("critic_note"),
        "warnings": result.get("warnings", []),
        "dashboard": result.get("dashboard"),
        "campaign": result.get("campaign"),
        "posts": result.get("posts"),
        "actions": result.get("actions", []),
        "suggestion": result.get("suggestion"),
        "picture_plan": result.get("picture_plan"),
        "verification": result.get("verification"),
        "image_url": result.get("image_url"),
        "image_b64": result.get("image_b64"),
        "model_status": result.get("model_status"),
        "email_status": result.get("email_status"),
        "email_bulk_reply": result.get("email_bulk_reply"),
        "requires_approval": result.get("requires_approval", result.get("status") == "requires_approval"),
        "input": request.model_dump(),
    }


def _email_job_repository():
    requested = os.getenv("EMAIL_JOB_REPOSITORY", "auto").lower()
    supabase_repo = SupabaseEmailJobRepository()
    if requested == "file":
        return FileEmailJobRepository()
    if requested == "supabase" or (requested == "auto" and supabase_repo.configured):
        return supabase_repo
    return FileEmailJobRepository()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "assistant-runtime"}


@app.post("/assistant/request")
async def assistant_request(request: AssistantRequest) -> dict:
    stage = "validando permisos"
    gate = _discord_gate(request)
    if not gate["allowed"]:
        return {
            "status": "requires_discord_approval",
            "reason": gate["reason"],
            "decision": None,
        }

    # Inyectar dependencias (Hexagonal Architecture)
    from app.adapters.kalshi import KalshiHttpAdapter
    from app.adapters.open_claw import OpenClawLLMAdapter
    from app.adapters.memory import MentisMemoryAdapter
    from app.adapters.pilot_web import PilotWebAdapter
    from app.adapters.linear import LinearTaskTrackerAdapter
    from app.adapters.trading_audit import SupabaseTradeAuditRepository, SupabaseTradingExposureRepository
    from app.adapters.zernio_adapter import ZernioAdapter
    from app.domain.trading_policies import ConfigurableRiskPolicy
    from app.use_cases.marketing_graph import MarketingGraph
    from app.use_cases.model_status import ModelStatusService
    from app.use_cases.trading_workflow import TradingWorkflow

    trading_port = KalshiHttpAdapter()
    llm_port = OpenClawLLMAdapter()
    memory_port = MentisMemoryAdapter()
    workflow = TradingWorkflow(
        trading_port=trading_port,
        llm_port=llm_port,
        memory_port=memory_port,
        risk_policy=ConfigurableRiskPolicy(exposure_repository=SupabaseTradingExposureRepository()),
        audit_repository=SupabaseTradeAuditRepository(),
    )
    marketing_workflow = MarketingGraph(llm=llm_port, memory=memory_port, marketing=ZernioAdapter())
    writer_workflow = WriterWorkflow(llm_port=llm_port, memory_port=memory_port)
    email_config = RuntimeEmailConfig()
    email_workflow = EmailWorkflow(
        email_provider=ConfiguredEmailProvider(email_config),
        email_config=email_config,
        email_jobs=_email_job_repository(),
        llm=llm_port,
    )
    model_status_service = ModelStatusService(llm=llm_port)
    from app.use_cases.picture_graph import PictureGraph
    from app.use_cases.coder_web_graph import CoderWebGraph
    picture_workflow = PictureGraph(llm=llm_port, memory=memory_port)
    
    coder_web_adapter = PilotWebAdapter()
        
    coder_web_workflow = CoderWebGraph(
        llm=llm_port,
        memory=memory_port,
        coder_web=coder_web_adapter,
        task_tracker=LinearTaskTrackerAdapter(),
    )

    try:
        if request.action_type in {ActionType.trade_decision, ActionType.open_position}:
            stage = "ejecutando flujo de trading"
            result = await workflow.execute_trade_decision(prompt=request.prompt, user_id=request.source.user_id)
        elif request.action_type == ActionType.marketing:
            stage = "preparando flujo de marketing"
            _debug_payload(f"Entrando a MarketingGraph con prompt: {request.prompt}")
            decoded = _decode_request_images(request.images)
            if decoded["status"] == "error":
                return decoded
            image_data = decoded["images"]
            
            stage = f"ejecutando marketer:{request.payload.get('sub_command', 'chat')}"
            result = await marketing_workflow.run(prompt=request.prompt, payload=request.payload, images=image_data)
        elif request.action_type == ActionType.writer:
            stage = "ejecutando writer"
            _debug_payload(f"Entrando a WriterWorkflow con prompt: {request.prompt}")
            result = await writer_workflow.execute_writer_action(prompt=request.prompt, payload=request.payload)
        elif request.action_type == ActionType.email:
            stage = f"ejecutando email:{request.payload.get('sub_command', 'status')}"
            _debug_payload(f"Entrando a EmailWorkflow con prompt: {request.prompt}")
            result = await email_workflow.run(prompt=request.prompt, payload=request.payload)
        elif request.action_type == ActionType.picture:
            stage = "ejecutando picture"
            _debug_payload(f"Entrando a PictureGraph con prompt: {request.prompt}")
            decoded = _decode_request_images(request.images)
            if decoded["status"] == "error":
                return decoded
            image_data = decoded["images"]
            result = await picture_workflow.run(
                prompt=request.prompt,
                payload=request.payload,
                images=image_data,
                image_metadata=request.image_metadata,
            )
        elif request.action_type == ActionType.coder_web:
            stage = "ejecutando coder-web"
            _debug_payload(f"Entrando a CoderWebGraph con prompt: {request.prompt}")
            decoded = _decode_request_images(request.images)
            if decoded["status"] == "error":
                return decoded
            image_data = decoded["images"]
            result = await coder_web_workflow.run(prompt=request.prompt, payload=request.payload, images=image_data)
        elif request.action_type == ActionType.model_status:
            stage = "consultando modelos conectados"
            result = model_status_service.get_status(agent=request.payload.get("agent", request.prompt))
        else:
            stage = "ejecutando chat"
            result_text = await workflow.execute_chat(prompt=request.prompt, user_id=request.source.user_id)
            result = {"status": "success", "message": result_text}

        # Fallback if result is None
        if result is None:
            result = {"status": "error", "message": "El sub-agente no devolvió ningún resultado."}

        _debug_payload(f"Workflow result: {result}")

        return _assistant_response(result, request)
    except Exception as exc:
        import traceback
        trace_id = str(uuid.uuid4())
        error_trace = traceback.format_exc()
        print(f"[CRITICAL ERROR][{trace_id}] {exc}\n{error_trace}")
        response = _format_internal_error(exc, request, stage)
        response["trace_id"] = trace_id
        if os.getenv("EXPOSE_DEBUG_TRACES", "false").lower() == "true":
            response["debug_trace"] = error_trace
        return response


def _discord_gate(request: AssistantRequest) -> dict:
    if request.action_type not in {ActionType.trade_decision, ActionType.open_position}:
        return {"allowed": True, "reason": "No es accion de trading."}

    expected_channel = os.getenv("DISCORD_REQUESTS_CHANNEL_ID")
    if request.source.platform != "discord":
        return {"allowed": False, "reason": "Toda decision de trading debe originarse en Discord."}
    if expected_channel and request.source.channel_id != expected_channel:
        return {"allowed": False, "reason": "La decision no proviene del canal Discord autorizado."}
    if not request.approval or request.approval.status != "approved":
        return {"allowed": False, "reason": "Falta aprobacion explicita en Discord."}
    if expected_channel and request.approval.channel_id != expected_channel:
        return {"allowed": False, "reason": "La aprobacion no proviene del canal Discord autorizado."}
    approvers = {
        value.strip()
        for value in os.getenv("DISCORD_APPROVER_USER_IDS", "").split(",")
        if value.strip()
    }
    if approvers and request.approval.approver_user_id not in approvers:
        return {"allowed": False, "reason": "El aprobador no esta autorizado."}
    return {"allowed": True, "reason": "Aprobado por Discord."}


def _debug_payload(message: str) -> None:
    if os.getenv("DEBUG_ASSISTANT_PAYLOADS", "false").lower() == "true":
        print(f"[DEBUG] {message}")


def _decode_request_images(images_b64: list[str]) -> dict:
    if len(images_b64) > MAX_IMAGE_COUNT:
        return {"status": "error", "message": f"Máximo {MAX_IMAGE_COUNT} imágenes por solicitud."}

    image_data = []
    for img_b64 in images_b64:
        if img_b64.startswith("data:image/") and "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        if (len(img_b64) * 3 / 4) > MAX_IMAGE_SIZE:
            return {"status": "error", "message": "Una de las imágenes excede el límite de 5MB."}
        try:
            image_data.append(base64.b64decode(img_b64, validate=True))
        except (binascii.Error, ValueError):
            return {"status": "error", "message": "Una de las imágenes no es base64 válido."}
    return {"status": "success", "images": image_data}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
