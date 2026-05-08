import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "control-api"))

from app.application.use_cases import ListKnowledgeSources, RegisterKnowledgeSource
from app.domain.models import KnowledgeSource, SourceType


class FakeKnowledgeSourceRepository:
    def __init__(self) -> None:
        self.sources: list[KnowledgeSource] = []

    async def list_sources(self) -> list[KnowledgeSource]:
        return self.sources

    async def add_source(self, source: KnowledgeSource) -> KnowledgeSource:
        self.sources.append(source)
        return source


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


if __name__ == "__main__":
    unittest.main()
