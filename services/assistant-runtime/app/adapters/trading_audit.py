import os
from datetime import datetime, timezone

import httpx

from app.domain.ports.trading import TradeAuditEvent, TradeAuditRepository, TradingExposureRepository


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
                response = await client.post(
                    f"{self.url.rstrip('/')}/rest/v1/trading_audit_events",
                    headers=headers,
                    json=payload,
                )
            if response.status_code >= 400:
                raise RuntimeError(f"Trading audit HTTP {response.status_code}: {response.text[:240]}")
        except Exception as exc:
            print(f"[TRADING AUDIT ERROR] {exc}")
            raise


class SupabaseTradingExposureRepository(TradingExposureRepository):
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    async def daily_notional(self, actor_id: str | None, environment: str) -> float:
        if not self.url or not self.key:
            return 0.0
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        params = {
            "select": "payload",
            "event_type": "eq.trade_submit_attempt",
            "environment": f"eq.{environment}",
            "created_at": f"gte.{start.isoformat()}",
        }
        if actor_id:
            params["actor_id"] = f"eq.{actor_id}"
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}"}
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                f"{self.url.rstrip('/')}/rest/v1/trading_audit_events",
                headers=headers,
                params=params,
            )
        if response.status_code >= 400:
            raise RuntimeError(f"Trading exposure HTTP {response.status_code}: {response.text[:240]}")
        total = 0.0
        for row in response.json():
            try:
                total += float((row.get("payload") or {}).get("amount") or 0)
            except (TypeError, ValueError):
                continue
        return total


def _redact(payload: dict) -> dict:
    redacted = {}
    for key, value in payload.items():
        if any(secret in key.lower() for secret in ("password", "secret", "token", "key")):
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted
