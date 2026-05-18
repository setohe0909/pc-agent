import httpx


class OpenWAHttpGateway:
    def __init__(self, base_url: str, api_key: str | None, session_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session_id = session_id

    async def send_text(self, phone_number: str, text: str) -> dict:
        if not self.api_key:
            raise RuntimeError("OPENWA_API_KEY no configurada.")
        payload = {"chatId": f"{phone_number}@c.us", "text": text}
        headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.base_url}/api/sessions/{self.session_id}/messages/send-text",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            raise RuntimeError(f"OpenWA HTTP {response.status_code}: {response.text[:240]}")
        return response.json()
