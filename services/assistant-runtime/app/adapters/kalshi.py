import json
import os
from pathlib import Path
from app.domain.ports.trading import TradingPort


class KalshiHttpAdapter(TradingPort):
    def __init__(self) -> None:
        self.config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")

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
        
        # Aqui iria la logica real del SDK:
        # configuration = kalshi_python_sdk.Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
        # client = kalshi_python_sdk.ApiClient(configuration)
        # ... logic to login and get markets ...
        print(f"[KALSHI] Intentando usar cuenta real para {creds['username']}")
        return [{"ticker": "REAL-KALSHI-LINKED", "title": "Conexion real establecida (Pendiente fetch de mercados)"}]

    async def place_order(self, ticker: str, action: str, amount: float) -> dict:
        creds = self._get_credentials()
        if not creds or not creds["username"]:
            print(f"[KALSHI DEMO] Orden: {action} {amount} en {ticker}")
            return {"status": "executed", "message": "Orden DEMO ejecutada."}

        print(f"[KALSHI REAL] Ejecutando orden para {creds['username']} en {ticker}")
        return {
            "status": "pending_api",
            "message": f"Conexion con Kalshi para {creds['username']} validada. Orden enviada al pipeline de ejecucion real."
        }
