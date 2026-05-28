import httpx


class OpenAISpeechTranscriber:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini-transcribe") -> None:
        self.api_key = api_key
        self.model = model

    async def transcribe(self, audio: bytes, filename: str, content_type: str, language: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "language": language,
            "response_format": "json",
        }
        files = {
            "file": (filename or "speech.webm", audio, content_type or "audio/webm"),
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
            )
        response.raise_for_status()
        payload = response.json()
        return str(payload.get("text") or "")
