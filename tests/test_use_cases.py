import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "control-api"))

from app.application.use_cases import ListKnowledgeSources, RegisterKnowledgeSource, SubmitAssistantRequest, TranscribeAssistantAudio
from app.domain.models import KnowledgeSource, SourceType


class FakeKnowledgeSourceRepository:
    def __init__(self) -> None:
        self.sources: list[KnowledgeSource] = []

    async def list_sources(self) -> list[KnowledgeSource]:
        return self.sources

    async def add_source(self, source: KnowledgeSource) -> KnowledgeSource:
        self.sources.append(source)
        return source


class FakeAssistantRuntimeGateway:
    def __init__(self) -> None:
        self.payload: dict | None = None

    async def submit_request(self, payload: dict) -> dict:
        self.payload = payload
        return {"status": "success", "message": f"ok:{payload['prompt']}"}


class FakeSpeechTranscriber:
    async def transcribe(self, audio: bytes, filename: str, content_type: str, language: str) -> str:
        return f"voz:{len(audio)}:{language}:{filename}:{content_type}"


class UseCaseTests(unittest.TestCase):
    def test_register_and_list_knowledge_source(self) -> None:
        async def scenario() -> None:
            repository = FakeKnowledgeSourceRepository()
            source = KnowledgeSource(
                name="Fuente macro",
                source_type=SourceType.rss,
                url="https://example.com/feed.xml",
                schedule="0 9 * * *",
            )

            saved = await RegisterKnowledgeSource(repository).execute(source)
            listed = await ListKnowledgeSources(repository).execute()

            self.assertEqual(saved.name, "Fuente macro")
            self.assertEqual(listed, [source])

        asyncio.run(scenario())

    def test_submit_assistant_request_trims_prompt(self) -> None:
        async def scenario() -> None:
            gateway = FakeAssistantRuntimeGateway()
            response = await SubmitAssistantRequest(gateway).execute({
                "action_type": "marketing",
                "prompt": "  revisa campanas  ",
                "source": {"platform": "admin"},
                "payload": {"sub_command": "status"},
            })

            self.assertEqual(response["message"], "ok:revisa campanas")
            self.assertEqual(gateway.payload["prompt"], "revisa campanas")

        asyncio.run(scenario())

    def test_submit_assistant_request_rejects_empty_prompt(self) -> None:
        async def scenario() -> None:
            with self.assertRaises(ValueError):
                await SubmitAssistantRequest(FakeAssistantRuntimeGateway()).execute({"prompt": "   "})

        asyncio.run(scenario())

    def test_transcribe_assistant_audio_returns_text(self) -> None:
        async def scenario() -> None:
            response = await TranscribeAssistantAudio(FakeSpeechTranscriber()).execute(
                audio=b"audio",
                filename="speech.webm",
                content_type="audio/webm",
                language="es",
            )

            self.assertEqual(response["text"], "voz:5:es:speech.webm:audio/webm")

        asyncio.run(scenario())

    def test_transcribe_assistant_audio_rejects_empty_audio(self) -> None:
        async def scenario() -> None:
            with self.assertRaises(ValueError):
                await TranscribeAssistantAudio(FakeSpeechTranscriber()).execute(
                    audio=b"",
                    filename="speech.webm",
                    content_type="audio/webm",
                    language="es",
                )

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
