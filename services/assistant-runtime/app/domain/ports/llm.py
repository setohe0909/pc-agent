from typing import Protocol


class LLMPort(Protocol):
    def model_inventory(self) -> dict:
        """Returns configured model/provider metadata without calling external providers."""
        ...

    async def chat(self, prompt: str, context: dict | None = None, images: list[bytes] | None = None, system_instruction: str | None = None) -> str:
        ...

    async def analyze_trade(self, market_data: dict, prompt: str, system_instruction: str | None = None) -> dict:
        ...

    async def get_tools_response(self, prompt: str, tools: list[dict], system_instruction: str | None = None) -> dict:
        ...

    async def generate_image(self, prompt: str, context: dict | None = None) -> str:
        """Generates an image from a prompt and returns the URL or base64 data."""
        ...

    async def edit_image(
        self,
        prompt: str,
        image: bytes,
        mask: bytes | None = None,
        context: dict | None = None,
        image_mime: str | None = None,
        image_filename: str | None = None,
    ) -> str:
        """Edits an existing image and returns the URL or base64 data."""
        ...
