import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "control-api"))

from app.application.use_cases import (
    CreateWhatsAppCampaign,
    DecideWhatsAppCampaign,
    ListWhatsAppCampaigns,
    ListWhatsAppContacts,
    UpsertWhatsAppContact,
)
from app.domain.models import WhatsAppCampaign, WhatsAppContact


class FakeWhatsAppOutreachRepository:
    def __init__(self) -> None:
        self.contacts: list[WhatsAppContact] = []
        self.campaigns: list[WhatsAppCampaign] = []

    async def list_contacts(self, limit: int = 100) -> list[WhatsAppContact]:
        return self.contacts[:limit]

    async def upsert_contact(self, contact: WhatsAppContact) -> WhatsAppContact:
        self.contacts.append(contact)
        return contact

    async def list_campaigns(self, limit: int = 100) -> list[WhatsAppCampaign]:
        return self.campaigns[:limit]

    async def create_campaign(self, campaign: WhatsAppCampaign) -> WhatsAppCampaign:
        self.campaigns.append(campaign)
        return campaign

    async def decide_campaign(self, campaign_id: str, approved: bool, decided_by: str) -> WhatsAppCampaign:
        status = "queued" if approved else "cancelled"
        current = self.campaigns[0]
        decided = WhatsAppCampaign(
            id=campaign_id,
            name=current.name,
            message_template=current.message_template,
            status=status,
            target_tag=current.target_tag,
            recipient_count=current.recipient_count,
            metadata={"decided_by": decided_by, "requires_approval": False},
        )
        self.campaigns[0] = decided
        return decided

    async def count_opted_in_recipients(self, target_tag: str | None = None) -> int:
        if target_tag:
            return len([contact for contact in self.contacts if contact.consent_status == "opted_in" and target_tag in contact.tags])
        return len([contact for contact in self.contacts if contact.consent_status == "opted_in"])


class WhatsAppOutreachUseCaseTests(unittest.TestCase):
    def test_contact_requires_opt_in(self) -> None:
        async def scenario() -> None:
            repo = FakeWhatsAppOutreachRepository()
            with self.assertRaises(ValueError):
                await UpsertWhatsAppContact(repo).execute(
                    WhatsAppContact(phone_number="+573001112233", consent_status="unknown")
                )

        asyncio.run(scenario())

    def test_create_campaign_counts_opted_in_recipients(self) -> None:
        async def scenario() -> None:
            repo = FakeWhatsAppOutreachRepository()
            await UpsertWhatsAppContact(repo).execute(
                WhatsAppContact(phone_number="+573001112233", tags=["launch"])
            )
            campaign = await CreateWhatsAppCampaign(repo).execute(
                WhatsAppCampaign(name="Launch", message_template="Hola", target_tag="launch")
            )
            self.assertEqual(campaign.status, "draft")
            self.assertEqual(campaign.recipient_count, 1)
            self.assertTrue(campaign.metadata["requires_approval"])
            listed = await ListWhatsAppCampaigns(repo).execute()
            self.assertEqual(listed, [campaign])

        asyncio.run(scenario())

    def test_list_contacts(self) -> None:
        async def scenario() -> None:
            repo = FakeWhatsAppOutreachRepository()
            await UpsertWhatsAppContact(repo).execute(WhatsAppContact(phone_number="+573001112233"))
            listed = await ListWhatsAppContacts(repo).execute()
            self.assertEqual(listed[0].phone_number, "+573001112233")

        asyncio.run(scenario())

    def test_decide_campaign_queues_approved_campaign(self) -> None:
        async def scenario() -> None:
            repo = FakeWhatsAppOutreachRepository()
            repo.campaigns.append(WhatsAppCampaign(id="cmp-1", name="Launch", message_template="Hola"))
            decided = await DecideWhatsAppCampaign(repo).execute("cmp-1", approved=True, decided_by="admin")
            self.assertEqual(decided.status, "queued")
            self.assertEqual(decided.metadata["decided_by"], "admin")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
