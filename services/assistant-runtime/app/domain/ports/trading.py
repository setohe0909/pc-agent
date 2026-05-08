from typing import Protocol


class TradingPort(Protocol):
    async def get_markets(self) -> list[dict]:
        ...

    async def get_balance(self) -> float:
        ...

    async def place_order(self, ticker: str, action: str, amount: float, client_order_id: str | None = None) -> dict:
        ...
