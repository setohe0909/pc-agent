import os
from app.domain.ports.trading import TradingPort

class KalshiLiveDemoAdapter(TradingPort):
    """
    Adapter demo para Kalshi Live. 
    En producción, esto usaría el SDK oficial de Kalshi con API Keys reales.
    """
    def __init__(self):
        self.limit_per_trade = 10.0 # Límite de seguridad de $10 USD

    async def get_markets(self, limit: int = 10) -> list[dict]:
        # Mock de datos reales
        return [
            {"ticker": "FED-26MAY-T25", "title": "Will Fed raise rates?", "yes_price": 0.45},
            {"ticker": "BTC-26MAY-60K", "title": "Will BTC be above 60k?", "yes_price": 0.70}
        ]

    async def place_order(self, ticker: str, side: str, amount_usd: float) -> dict:
        if amount_usd > self.limit_per_trade:
            raise ValueError(f"Orden excede el límite de seguridad de ${self.limit_per_trade}")
        
        print(f"[KALSHI-LIVE-DEMO] Colocando orden {side} en {ticker} por ${amount_usd}")
        return {
            "status": "executed",
            "order_id": "live_mock_12345",
            "ticker": ticker,
            "side": side,
            "amount": amount_usd
        }

    async def get_balance(self) -> float:
        return 1000.0 # Balance simulado
