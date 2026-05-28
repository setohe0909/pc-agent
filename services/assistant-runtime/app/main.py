import base64
import binascii
import json
import os
import uuid
from enum import Enum
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from app.runtime.errors import error_envelope


def load_runtime_config() -> None:
    config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
    try:
        if Path(config_path).exists():
            config = json.loads(Path(config_path).read_text(encoding="utf-8"))
            for key, value in config.items():
                if value:
                    env_key = key.upper()
                    os.environ[env_key] = str(value)
                    if env_key == "OLLAMA_BASE_URL":
                        os.environ["OLLAMA_API_BASE"] = str(value)
            print(f"Configuracion runtime cargada desde {config_path}")
    except Exception as exc:
        print(f"Error cargando configuracion runtime: {exc}")


load_runtime_config()

app = FastAPI(title="PC Agent Assistant Runtime")


class ActionType(str, Enum):
    chat = "chat"
    orchestrator = "orchestrator"
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
    images: list[str] = Field(default_factory=list)
    image_metadata: list[dict] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_COUNT = 4


@app.on_event("startup")
async def startup() -> None:
    from app.runtime.container import build_runtime_container

    app.state.runtime_container = build_runtime_container()


@app.get("/health")
async def health() -> dict:
    container_ready = hasattr(app.state, "runtime_container")
    return {"status": "ok" if container_ready else "starting", "service": "assistant-runtime", "container_ready": container_ready}


@app.post("/assistant/request")
async def assistant_request(request: AssistantRequest, http_request: Request) -> dict:
    trace_id = str(uuid.uuid4())
    stage = "validando permisos"
    container = _get_runtime_container(http_request)

    gate = _discord_gate(request)
    if not gate["allowed"]:
        return {
            "status": "requires_discord_approval",
            "reason": gate["reason"],
            "decision": None,
            "trace_id": trace_id,
        }

    try:
        _check_rate_limit(container, request)
        metadata = _trace_metadata(request, trace_id)
        async with container.tracer.span("assistant.request", metadata):
            result, stage = await dispatch_assistant_request(container, request)
            if result is None:
                result = {"status": "error", "message": "El sub-agente no devolvió ningún resultado."}
            _debug_payload(f"Workflow result: {result}")
            response = _assistant_response(result, request)
            response["trace_id"] = trace_id
            return response
    except Exception as exc:
        import traceback

        error_trace = traceback.format_exc()
        print(f"[CRITICAL ERROR][{trace_id}] {exc}\n{error_trace}")
        sub_command = request.payload.get("sub_command", "chat") if isinstance(request.payload, dict) else "chat"
        response = error_envelope(exc, request.action_type.value, sub_command, stage, trace_id).to_dict()
        if os.getenv("EXPOSE_DEBUG_TRACES", "false").lower() == "true":
            response["debug_trace"] = error_trace
        return response


async def dispatch_assistant_request(container, request: AssistantRequest) -> tuple[dict | None, str]:
    if request.action_type in {ActionType.trade_decision, ActionType.open_position}:
        stage = "ejecutando flujo de trading"
        return await container.trading_workflow.execute_trade_decision(prompt=request.prompt, user_id=request.source.user_id), stage
    if request.action_type == ActionType.marketing:
        decoded = _decode_request_images(request.images)
        if decoded["status"] == "error":
            return decoded, "validando imagenes de marketing"
        stage = f"ejecutando marketer:{request.payload.get('sub_command', 'chat')}"
        return await container.marketing_workflow.run(prompt=request.prompt, payload=request.payload, images=decoded["images"]), stage
    if request.action_type == ActionType.writer:
        stage = "ejecutando writer"
        return await container.writer_workflow.execute_writer_action(prompt=request.prompt, payload=request.payload), stage
    if request.action_type == ActionType.email:
        stage = f"ejecutando email:{request.payload.get('sub_command', 'status')}"
        return await container.email_workflow.run(prompt=request.prompt, payload=request.payload), stage
    if request.action_type == ActionType.picture:
        decoded = _decode_request_images(request.images)
        if decoded["status"] == "error":
            return decoded, "validando imagenes de picture"
        stage = "ejecutando picture"
        return await container.picture_workflow.run(
            prompt=request.prompt,
            payload=request.payload,
            images=decoded["images"],
            image_metadata=request.image_metadata,
        ), stage
    if request.action_type == ActionType.coder_web:
        decoded = _decode_request_images(request.images)
        if decoded["status"] == "error":
            return decoded, "validando imagenes de coder-web"
        stage = "ejecutando coder-web"
        return await container.coder_web_workflow.run(prompt=request.prompt, payload=request.payload, images=decoded["images"]), stage
    if request.action_type == ActionType.model_status:
        stage = "consultando modelos conectados"
        return container.model_status_service.get_status(agent=request.payload.get("agent", request.prompt)), stage
    if request.action_type == ActionType.orchestrator:
        stage = "orquestando agentes"
        return await container.orchestrator_workflow.run(prompt=request.prompt, payload=request.payload), stage

    stage = "ejecutando chat"
    result_text = await container.trading_workflow.execute_chat(prompt=request.prompt, user_id=request.source.user_id)
    return {"status": "success", "message": result_text}, stage


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
        "email_jobs": result.get("email_jobs"),
        "orchestrator": result.get("orchestrator"),
        "requires_approval": result.get("requires_approval", result.get("status") == "requires_approval"),
        "input": request.model_dump(),
    }


def _format_internal_error(exc: Exception, request: AssistantRequest, stage: str) -> dict:
    sub_command = request.payload.get("sub_command", "chat") if isinstance(request.payload, dict) else "chat"
    response = error_envelope(exc, request.action_type.value, sub_command, stage, "test-trace").to_dict()
    response["error_detail"] = str(exc) or repr(exc)
    return response


def _get_runtime_container(http_request: Request):
    if not hasattr(http_request.app.state, "runtime_container"):
        from app.runtime.container import build_runtime_container

        http_request.app.state.runtime_container = build_runtime_container()
    return http_request.app.state.runtime_container


def _check_rate_limit(container, request: AssistantRequest) -> None:
    actor = request.source.user_id or request.source.channel_id or "anonymous"
    decision = container.rate_limiter.check(f"{request.source.platform}:{actor}:{request.action_type.value}")
    if not decision.allowed:
        raise RuntimeError(f"Rate limit excedido. Reintenta en {decision.retry_after_seconds}s.")


def _trace_metadata(request: AssistantRequest, trace_id: str) -> dict:
    return {
        "trace_id": trace_id,
        "action_type": request.action_type.value,
        "sub_command": request.payload.get("sub_command", "chat") if isinstance(request.payload, dict) else "chat",
        "platform": request.source.platform,
        "channel_id": request.source.channel_id,
        "user_id": request.source.user_id,
        "image_count": len(request.images),
    }


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
