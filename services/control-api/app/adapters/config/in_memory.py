from app.domain.models import KnowledgeSource, SourceType
from app.ports.gateways import KnowledgeSourceRepository


class InMemoryKnowledgeSourceRepository(KnowledgeSourceRepository):
    def __init__(self) -> None:
        self.sources: list[KnowledgeSource] = [
            KnowledgeSource(
                name="Kalshi markets",
                source_type=SourceType.kalshi_market,
                schedule="0 */2 * * *",
                enabled=True,
            ),
            KnowledgeSource(
                name="Tendencias generales",
                source_type=SourceType.trend,
                schedule="15 */4 * * *",
                enabled=True,
            ),
        ]

    async def list_sources(self) -> list[KnowledgeSource]:
        return self.sources

    async def add_source(self, source: KnowledgeSource) -> KnowledgeSource:
        self.sources.append(source)
        return source
