from app.domain.models import KnowledgeSource, MentisVerification, ServiceStatus, SupabaseVerification
from app.ports.gateways import KnowledgeSourceRepository, MentisMemory, SystemProbe, VectorKnowledgeBase


class CheckSystemStatus:
    def __init__(self, probe: SystemProbe) -> None:
        self.probe = probe

    async def execute(self) -> list[ServiceStatus]:
        return await self.probe.check()


class RegisterKnowledgeSource:
    def __init__(self, repository: KnowledgeSourceRepository) -> None:
        self.repository = repository

    async def execute(self, source: KnowledgeSource) -> KnowledgeSource:
        return await self.repository.add_source(source)


class ListKnowledgeSources:
    def __init__(self, repository: KnowledgeSourceRepository) -> None:
        self.repository = repository

    async def execute(self) -> list[KnowledgeSource]:
        return await self.repository.list_sources()


class VerifyMentisHealth:
    def __init__(self, memory: MentisMemory) -> None:
        self.memory = memory

    async def execute(self) -> MentisVerification:
        return await self.memory.verify()


class VerifySupabaseVectorStore:
    def __init__(self, knowledge_base: VectorKnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    async def execute(self) -> SupabaseVerification:
        return await self.knowledge_base.verify()
