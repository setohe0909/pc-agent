import os
import json
from pathlib import Path
from enum import Enum

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.adapters.kalshi import KalshiDemoAdapter
from app.adapters.open_claw import OpenClawLLMAdapter
from app.use_cases.trading_workflow import TradingWorkflow

def load_runtime_config():
    config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
    try:
        if Path(config_path).exists():
            config = json.loads(Path(config_path).read_text(encoding="utf-8"))
            for key, value in config.items():
                if value:
                    # Update environment so litellm and other components see it
                    os.environ[key.upper()] = str(value)
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
    trading_port = KalshiDemoAdapter()
    llm_port = OpenClawLLMAdapter()
    # MemoryPort no implementado por el momento en este demo
    workflow = TradingWorkflow(trading_port=trading_port, llm_port=llm_port)

    try:
        if request.action_type in {ActionType.trade_decision, ActionType.open_position}:
            result = await workflow.execute_trade_decision(prompt=request.prompt, user_id=request.source.user_id)
        else:
            result_text = await workflow.execute_chat(prompt=request.prompt, user_id=request.source.user_id)
            result = {"status": "success", "message": result_text}

        return {
            "status": result.get("status", "accepted"),
            "provider": os.getenv("DEFAULT_LLM_PROVIDER", "openai"),
            "message": result.get("message", "Operacion exitosa."),
            "order": result.get("order"),
            "input": request.model_dump(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "reason": str(exc),
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
