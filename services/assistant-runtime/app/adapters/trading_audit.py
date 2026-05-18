import os
from datetime import datetime, timezone

import httpx

from app.domain.ports.trading import TradeAuditEvent, TradeAuditRepository


class SupabaseTradeAuditRepository(TradeAuditRepository):
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    async def record(self, event: TradeAuditEvent) -> None:
        if not self.url or not self.key:
            return None
        payload = {
            "event_type": event.event_type,
            "actor_id": event.actor_id,
            "order_id": event.order_id,
            "ticker": event.ticker,
            "environment": event.environment,
            "payload": _redact(event.payload),
            "created_at": (event.created_at or datetime.now(timezone.utc)).isoformat(),
        }
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(f"{self.url.rstrip('/')}/rest/v1/trading_audit_events", headers=headers, json=payload)
        except Exception as exc:
            print(f"[TRADING AUDIT ERROR] {exc}")


def _redact(payload: dict) -> dict:
    redacted = {}
    for key, value in payload.items():
        if any(secret in key.lower() for secret in ("password", "secret", "token", "key")):
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted
