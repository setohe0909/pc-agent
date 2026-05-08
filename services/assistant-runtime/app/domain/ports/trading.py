from typing import Protocol


class TradingPort(Protocol):
    async def get_markets(self) -> list[dict]:
        ...

    async def place_order(self, ticker: str, action: str, amount: float) -> dict:
        ...
