import os
import json
from pathlib import Path
from enum import Enum

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.adapters.kalshi import KalshiHttpAdapter
from app.adapters.open_claw import OpenClawLLMAdapter
from app.adapters.memory import MentisMemoryAdapter
from app.adapters.marketing import SocialMediaStubAdapter
from app.use_cases.trading_workflow import TradingWorkflow
from app.use_cases.marketing_graph import MarketingGraph
from app.use_cases.writer_workflow import WriterWorkflow
from app.adapters.pilot_web import PilotWebAdapter

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
    payload: dict = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "assistant-runtime"}


@app.post("/assistant/request")
async def assistant_request(request: AssistantRequest) -> dict:
    gate = _discord_gate(request)
    if not gate["allowed"]:
        return {
            "status": "requires_discord_approval",
            "reason": gate["reason"],
            "decision": None,
        }

    # Inyectar dependencias (Hexagonal Architecture)
    trading_port = KalshiHttpAdapter()
    llm_port = OpenClawLLMAdapter()
    memory_port = MentisMemoryAdapter()
    workflow = TradingWorkflow(trading_port=trading_port, llm_port=llm_port, memory_port=memory_port)
    marketing_workflow = MarketingGraph(llm=llm_port, memory=memory_port, marketing=SocialMediaStubAdapter())
    writer_workflow = WriterWorkflow(llm_port=llm_port, memory=memory_port)
    from app.use_cases.picture_graph import PictureGraph
    from app.use_cases.coder_web_graph import CoderWebGraph
    picture_workflow = PictureGraph(llm=llm_port, memory=memory_port)
    coder_web_workflow = CoderWebGraph(llm=llm_port, memory=memory_port, coder_web=PilotWebAdapter())

    try:
        if request.action_type in {ActionType.trade_decision, ActionType.open_position}:
            result = await workflow.execute_trade_decision(prompt=request.prompt, user_id=request.source.user_id)
        elif request.action_type == ActionType.marketing:
            print(f"[DEBUG] Entrando a MarketingGraph con prompt: {request.prompt}")
            import base64
            
            # Validación de tamaño (Límite 5MB por imagen)
            MAX_IMG_SIZE = 5 * 1024 * 1024
            image_data = []
            for img_b64 in request.images:
                # Estimación rápida de tamaño de base64 (3/4 del string)
                if (len(img_b64) * 3 / 4) > MAX_IMG_SIZE:
                    return {"status": "error", "message": "Una de las imágenes excede el límite de 5MB."}
                image_data.append(base64.b64decode(img_b64))
            
            result = await marketing_workflow.run(prompt=request.prompt, payload=request.payload, images=image_data)
        elif request.action_type == ActionType.writer:
            print(f"[DEBUG] Entrando a WriterWorkflow con prompt: {request.prompt}")
            result = await writer_workflow.execute_writer_action(prompt=request.prompt, payload=request.payload)
        elif request.action_type == ActionType.picture:
            print(f"[DEBUG] Entrando a PictureGraph con prompt: {request.prompt}")
            import base64
            image_data = [base64.b64decode(img) for img in request.images]
            result = await picture_workflow.run(prompt=request.prompt, payload=request.payload, images=image_data)
        elif request.action_type == ActionType.coder_web:
            print(f"[DEBUG] Entrando a CoderWebGraph con prompt: {request.prompt}")
            import base64
            image_data = [base64.b64decode(img) for img in request.images]
            result = await coder_web_workflow.run(prompt=request.prompt, payload=request.payload, images=image_data)
        else:
            result_text = await workflow.execute_chat(prompt=request.prompt, user_id=request.source.user_id)
            result = {"status": "success", "message": result_text}

        # Fallback if result is None
        if result is None:
            result = {"status": "error", "message": "El sub-agente no devolvió ningún resultado."}

        # DEBUG: Ver que esta devolviendo el workflow
        print(f"[DEBUG] Workflow result: {result}")

        return {
            "status": result.get("status", "accepted"),
            "provider": os.getenv("DEFAULT_LLM_PROVIDER", "openai"),
            "message": result.get("message") or "El asistente no pudo generar una respuesta de texto.",
            "order": result.get("order"),
            "critic_note": result.get("critic_note"),
            "warnings": result.get("warnings", []),
            "input": request.model_dump(),
        }
    except Exception as exc:
        print(f"[ERROR] Exception in assistant_request: {exc}")
        return {
            "status": "error",
            "reason": str(exc),
            "message": f"Error interno: {str(exc)}",
            "input": request.model_dump(),
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
