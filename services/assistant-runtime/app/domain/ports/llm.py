from typing import Protocol


class LLMPort(Protocol):
    async def chat(self, prompt: str, context: dict | None = None) -> str:
        ...

    async def analyze_trade(self, market_data: dict, prompt: str) -> dict:
        ...

    async def get_tools_response(self, prompt: str, tools: list[dict], system_instruction: str | None = None) -> dict:
        ...
