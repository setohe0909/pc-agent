from typing import Protocol

from app.domain.models import (
    IngestionRun,
    IngestionSchedule,
    MemoryFragment,
    KnowledgeSource,
    ConsolidationRecord,
    MentisVerification,
    ServiceStatus,
    SupabaseVerification,
    WhatsAppCampaign,
    WhatsAppContact,
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


class MemoryRepository(Protocol):
    async def verify(self) -> MentisVerification:
        ...

    async def list_recent(self, context: str | None, limit: int = 50) -> list[MemoryFragment]:
        ...

    async def clear_context(self, context: str | None) -> int:
        ...

    async def save_fragment(self, fragment: MemoryFragment) -> MemoryFragment:
        ...

    async def list_consolidations(self, limit: int = 100) -> list[ConsolidationRecord]:
        ...


class WhatsAppOutreachRepository(Protocol):
    async def list_contacts(self, limit: int = 100) -> list[WhatsAppContact]:
        ...

    async def upsert_contact(self, contact: WhatsAppContact) -> WhatsAppContact:
        ...

    async def list_campaigns(self, limit: int = 100) -> list[WhatsAppCampaign]:
        ...

    async def create_campaign(self, campaign: WhatsAppCampaign) -> WhatsAppCampaign:
        ...

    async def decide_campaign(self, campaign_id: str, approved: bool, decided_by: str) -> WhatsAppCampaign:
        ...

    async def count_opted_in_recipients(self, target_tag: str | None = None) -> int:
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


class AssistantRuntimeGateway(Protocol):
    async def submit_request(self, payload: dict) -> dict:
        ...


class SpeechTranscriber(Protocol):
    async def transcribe(self, audio: bytes, filename: str, content_type: str, language: str) -> str:
        ...
