import os
from enum import Enum

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

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
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    gate = _discord_gate(request)
    if not gate["allowed"]:
        return {
            "status": "requires_discord_approval",
            "provider": provider,
            "reason": gate["reason"],
            "decision": None,
        }
    return {
        "status": "accepted",
        "provider": provider,
        "message": "Solicitud aceptada por la compuerta Discord. Kalshi real sigue pendiente de adapter y politica de riesgo.",
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
