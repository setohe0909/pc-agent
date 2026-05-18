import asyncio
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "control-api"))

from app.application.use_cases import ClearMemoryContext, ListConsolidationHistory, ListMemoryFragments
from app.domain.models import ConsolidationRecord, MemoryFragment, MentisVerification


class FakeMemoryRepository:
    def __init__(self) -> None:
        self.fragments = [MemoryFragment(category="general", summary="uno")]
        self.cleared_context = None

    async def verify(self) -> MentisVerification:
        return MentisVerification(True, True, True, "ok")

    async def list_recent(self, context: str | None, limit: int = 50) -> list[MemoryFragment]:
        return self.fragments[:limit]

    async def clear_context(self, context: str | None) -> int:
        self.cleared_context = context
        return 3

    async def save_fragment(self, fragment: MemoryFragment) -> MemoryFragment:
        self.fragments.append(fragment)
        return fragment

    async def list_consolidations(self, limit: int = 100) -> list[ConsolidationRecord]:
        return [
            ConsolidationRecord(
                id="c1",
                category="consolidated_general",
                title="Resumen",
                summary="Resumen largo",
                status="succeeded",
                memory_count=2,
                metadata={"type": "long_term_consolidation"},
                created_at=datetime.now(timezone.utc),
            )
        ][:limit]


class MemoryUseCaseTests(unittest.TestCase):
    def test_list_memory_fragments(self) -> None:
        async def scenario() -> None:
            repo = FakeMemoryRepository()
            result = await ListMemoryFragments(repo).execute(context="general", limit=1)
            self.assertEqual(result[0].summary, "uno")

        asyncio.run(scenario())

    def test_clear_context_returns_deleted_count(self) -> None:
        async def scenario() -> None:
            repo = FakeMemoryRepository()
            deleted = await ClearMemoryContext(repo).execute(context="picture")
            self.assertEqual(deleted, 3)
            self.assertEqual(repo.cleared_context, "picture")

        asyncio.run(scenario())

    def test_list_consolidation_history(self) -> None:
        async def scenario() -> None:
            repo = FakeMemoryRepository()
            result = await ListConsolidationHistory(repo).execute()
            self.assertEqual(result[0].status, "succeeded")
            self.assertEqual(result[0].memory_count, 2)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
