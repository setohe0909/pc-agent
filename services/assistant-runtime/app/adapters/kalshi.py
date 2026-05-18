import json
import os
from pathlib import Path
from typing import Any

import httpx

from app.domain.ports.trading import TradingPort


class KalshiHttpAdapter(TradingPort):
    def __init__(self) -> None:
        self.config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
        self.environment = os.getenv("KALSHI_ENV", "paper")
        self.api_base_url = os.getenv("KALSHI_API_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2").rstrip("/")

    def _get_credentials(self):
        try:
            if Path(self.config_path).exists():
                config = json.loads(Path(self.config_path).read_text(encoding="utf-8"))
                return {
                    "username": config.get("kalshi_username"),
                    "password": config.get("kalshi_password"),
                    "key_id": config.get("kalshi_key_id")
                }
        except Exception:
            pass
        return None

    async def get_markets(self) -> list[dict]:
        creds = self._get_credentials()
        if not creds or not creds["username"]:
            # Fallback a demo si no hay credenciales
            return [
                {
                    "ticker": "KXFED-DEMO",
                    "title": "Will the Fed target rate be 3.50%? (DEMO)",
                    "yes_price": 0.45,
                    "no_price": 0.55,
                    "volume": 120000,
                },
                {
                    "ticker": "KXINFL-DEMO",
                    "title": "Will US Inflation be > 3.1%? (DEMO)",
                    "yes_price": 0.12,
                    "no_price": 0.88,
                    "volume": 45000,
                }
            ]
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get(f"{self.api_base_url}/markets", params={"limit": "20"})
            if response.status_code < 400:
                data = response.json()
                markets = data.get("markets", data if isinstance(data, list) else [])
                return [self._normalize_market(market) for market in markets]
            print(f"[KALSHI] Markets HTTP {response.status_code}: {response.text[:160]}")
        except Exception as exc:
            print(f"[KALSHI] Error consultando markets: {exc}")
        return []

    async def get_balance(self) -> float:
        creds = self._get_credentials()
        if not creds or not creds["username"]:
            return 1000.0  # Balance ficticio para demo
        
        if self.environment != "live":
            return float(os.getenv("KALSHI_PAPER_BALANCE", "1000"))
        print("[KALSHI] Balance live requiere autenticacion firmada configurada.")
        return 0.0

    async def place_order(self, ticker: str, action: str, amount: float, client_order_id: str | None = None) -> dict:
        creds = self._get_credentials()
        order_id = client_order_id or f"ord-{os.urandom(4).hex()}"
        
        if not creds or not creds["username"]:
            print(f"[KALSHI DEMO] Orden {order_id}: {action} {amount} en {ticker}")
            return {"status": "executed", "order_id": order_id, "message": "Orden DEMO ejecutada."}

        if self.environment != "live" or os.getenv("KALSHI_TRADING_ENABLED", "false").lower() != "true":
            return {
                "status": "blocked",
                "order_id": order_id,
                "message": "Orden no enviada: Kalshi live esta deshabilitado por configuracion.",
            }

        print(f"[KALSHI REAL] Preparando orden {order_id} para {creds['username']} en {ticker}")
        return {
            "status": "blocked",
            "order_id": order_id,
            "message": "Orden no enviada: falta configurar autenticacion firmada del API Kalshi.",
        }

    @staticmethod
    def _normalize_market(market: dict[str, Any]) -> dict:
        return {
            "ticker": market.get("ticker") or market.get("id"),
            "title": market.get("title") or market.get("subtitle") or market.get("ticker"),
            "yes_price": market.get("yes_price") or market.get("yes_bid") or market.get("last_price"),
            "no_price": market.get("no_price") or market.get("no_bid"),
            "volume": market.get("volume") or market.get("volume_24h"),
        }
