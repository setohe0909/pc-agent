import httpx


class HttpAssistantRuntimeGateway:
    def __init__(self, base_url: str, timeout_seconds: float = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def submit_request(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/assistant/request", json=payload)
        response.raise_for_status()
        return response.json()
