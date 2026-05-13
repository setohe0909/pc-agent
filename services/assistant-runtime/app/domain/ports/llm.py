from typing import Protocol


class LLMPort(Protocol):
    async def chat(self, prompt: str, context: dict | None = None, images: list[bytes] | None = None, system_instruction: str | None = None) -> str:
        ...

    async def analyze_trade(self, market_data: dict, prompt: str, system_instruction: str | None = None) -> dict:
        ...

    async def get_tools_response(self, prompt: str, tools: list[dict], system_instruction: str | None = None) -> dict:
        ...

    async def generate_image(self, prompt: str) -> str:
        """Generates an image from a prompt and returns the URL or base64 data."""
        ...
