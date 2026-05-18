from app.domain.models import (
    IngestionRun,
    IngestionSchedule,
    KnowledgeSource,
    ConsolidationRecord,
    MemoryFragment,
    MentisVerification,
    ServiceStatus,
    SupabaseVerification,
)
from app.ports.gateways import (
    IngestionControl,
    KnowledgeSourceRepository,
    MentisMemory,
    MemoryRepository,
    SystemProbe,
    VectorKnowledgeBase,
)


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


class ListMemoryFragments:
    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def execute(self, context: str | None = None, limit: int = 50) -> list[MemoryFragment]:
        return await self.repository.list_recent(context=context, limit=limit)


class ClearMemoryContext:
    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def execute(self, context: str | None = None) -> int:
        return await self.repository.clear_context(context=context)


class ListConsolidationHistory:
    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def execute(self, limit: int = 100) -> list[ConsolidationRecord]:
        return await self.repository.list_consolidations(limit=limit)


class VerifySupabaseVectorStore:
    def __init__(self, knowledge_base: VectorKnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    async def execute(self) -> SupabaseVerification:
        return await self.knowledge_base.verify()


class GetIngestionSchedule:
    def __init__(self, control: IngestionControl) -> None:
        self.control = control

    async def execute(self) -> IngestionSchedule:
        return await self.control.get_schedule()


class UpdateIngestionSchedule:
    def __init__(self, control: IngestionControl) -> None:
        self.control = control

    async def execute(self, schedule: IngestionSchedule) -> IngestionSchedule:
        return await self.control.update_schedule(schedule)


class ListIngestionRuns:
    def __init__(self, control: IngestionControl) -> None:
        self.control = control

    async def execute(self) -> list[IngestionRun]:
        return await self.control.list_runs()


class TriggerIngestionRun:
    def __init__(self, control: IngestionControl) -> None:
        self.control = control

    async def execute(self, target: str) -> IngestionRun:
        return await self.control.trigger_run(target)
