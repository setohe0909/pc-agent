from app.domain.models import (
    IngestionRun,
    IngestionSchedule,
    KnowledgeSource,
    ConsolidationRecord,
    MemoryFragment,
    MentisVerification,
    ServiceStatus,
    SupabaseVerification,
    WhatsAppCampaign,
    WhatsAppContact,
)
from app.ports.gateways import (
    AssistantRuntimeGateway,
    IngestionControl,
    KnowledgeSourceRepository,
    MentisMemory,
    MemoryRepository,
    SystemProbe,
    VectorKnowledgeBase,
    WhatsAppOutreachRepository,
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


class ListWhatsAppContacts:
    def __init__(self, repository: WhatsAppOutreachRepository) -> None:
        self.repository = repository

    async def execute(self, limit: int = 100) -> list[WhatsAppContact]:
        return await self.repository.list_contacts(limit=limit)


class UpsertWhatsAppContact:
    def __init__(self, repository: WhatsAppOutreachRepository) -> None:
        self.repository = repository

    async def execute(self, contact: WhatsAppContact) -> WhatsAppContact:
        if contact.consent_status != "opted_in":
            raise ValueError("Solo se pueden activar contactos con consentimiento opt-in.")
        return await self.repository.upsert_contact(contact)


class ListWhatsAppCampaigns:
    def __init__(self, repository: WhatsAppOutreachRepository) -> None:
        self.repository = repository

    async def execute(self, limit: int = 100) -> list[WhatsAppCampaign]:
        return await self.repository.list_campaigns(limit=limit)


class CreateWhatsAppCampaign:
    def __init__(self, repository: WhatsAppOutreachRepository) -> None:
        self.repository = repository

    async def execute(self, campaign: WhatsAppCampaign) -> WhatsAppCampaign:
        recipients = await self.repository.count_opted_in_recipients(campaign.target_tag)
        if recipients <= 0:
            raise ValueError("No hay destinatarios opt-in para esta campana.")
        draft = WhatsAppCampaign(
            id=campaign.id,
            name=campaign.name,
            message_template=campaign.message_template,
            status="draft",
            target_tag=campaign.target_tag,
            scheduled_for=campaign.scheduled_for,
            recipient_count=recipients,
            metadata={**campaign.metadata, "requires_approval": True, "channel": "whatsapp"},
            created_at=campaign.created_at,
        )
        return await self.repository.create_campaign(draft)


class DecideWhatsAppCampaign:
    def __init__(self, repository: WhatsAppOutreachRepository) -> None:
        self.repository = repository

    async def execute(self, campaign_id: str, approved: bool, decided_by: str) -> WhatsAppCampaign:
        if not campaign_id:
            raise ValueError("campaign_id requerido.")
        if not decided_by:
            raise ValueError("decided_by requerido.")
        return await self.repository.decide_campaign(campaign_id, approved, decided_by)


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


class SubmitAssistantRequest:
    def __init__(self, gateway: AssistantRuntimeGateway) -> None:
        self.gateway = gateway

    async def execute(self, payload: dict) -> dict:
        prompt = str(payload.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("prompt requerido.")
        return await self.gateway.submit_request({**payload, "prompt": prompt})
