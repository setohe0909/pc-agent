from typing import Protocol

from app.domain.models import (
    IngestionRun,
    IngestionSchedule,
    KnowledgeSource,
    MentisVerification,
    ServiceStatus,
    SupabaseVerification,
)


class SystemProbe(Protocol):
    async def check(self) -> list[ServiceStatus]:
        ...


class KnowledgeSourceRepository(Protocol):
    async def list_sources(self) -> list[KnowledgeSource]:
        ...

    async def add_source(self, source: KnowledgeSource) -> KnowledgeSource:
        ...


class MentisMemory(Protocol):
    async def verify(self) -> MentisVerification:
        ...


class ConversationTracer(Protocol):
    async def trace_event(self, name: str, payload: dict) -> None:
        ...


class VectorKnowledgeBase(Protocol):
    async def verify(self) -> SupabaseVerification:
        ...


class IngestionControl(Protocol):
    async def get_schedule(self) -> IngestionSchedule:
        ...

    async def update_schedule(self, schedule: IngestionSchedule) -> IngestionSchedule:
        ...

    async def list_runs(self) -> list[IngestionRun]:
        ...

    async def trigger_run(self, target: str) -> IngestionRun:
        ...
