from app.domain.ports.trading import TradingPort


class KalshiDemoAdapter(TradingPort):
    def __init__(self) -> None:
        pass

    async def get_markets(self) -> list[dict]:
        # Simulamos datos de Kalshi para el demo
        return [
            {
                "ticker": "KXFED-23DEC-T3.50",
                "title": "Will the Fed target rate be 3.50%?",
                "yes_price": 0.45,
                "no_price": 0.55,
                "volume": 120000,
            },
            {
                "ticker": "KXINFL-23NOV-T3.1",
                "title": "Will US Inflation be > 3.1%?",
                "yes_price": 0.12,
                "no_price": 0.88,
                "volume": 45000,
            },
            {
                "ticker": "BTC-70K-EOY",
                "title": "Will BTC cross $70k by end of year?",
                "yes_price": 0.70,
                "no_price": 0.30,
                "volume": 850000,
            }
        ]

    async def place_order(self, ticker: str, action: str, amount: float) -> dict:
        print(f"[KALSHI DEMO] Colocando orden: {action} {amount} contracts on {ticker}")
        return {
            "order_id": "demo-order-12345",
            "ticker": ticker,
            "action": action,
            "status": "executed",
            "amount": amount,
            "message": "Orden demo ejecutada exitosamente (No real money used)."
        }
