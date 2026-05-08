from typing import Protocol


class LLMPort(Protocol):
    async def chat(self, prompt: str, context: dict | None = None) -> str:
        ...

    async def analyze_trade(self, market_data: dict, prompt: str) -> dict:
        ...
