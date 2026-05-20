from datetime import datetime
from datetime import timezone

import httpx

from app.domain.models import WhatsAppCampaign, WhatsAppContact
from app.ports.gateways import WhatsAppOutreachRepository


class SupabaseWhatsAppOutreachRepository(WhatsAppOutreachRepository):
    def __init__(self, url: str, service_role_key: str | None) -> None:
        self.url = (url or "").rstrip("/")
        self.service_role_key = service_role_key

    async def list_contacts(self, limit: int = 100) -> list[WhatsAppContact]:
        params = {
            "select": "id,phone_number,display_name,source,consent_status,tags,metadata,created_at",
            "order": "created_at.desc",
            "limit": str(min(max(limit, 1), 500)),
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{self.url}/rest/v1/whatsapp_contacts",
                headers=self._headers(),
                params=params,
            )
        response.raise_for_status()
        return [self._contact_from_row(row) for row in response.json()]

    async def upsert_contact(self, contact: WhatsAppContact) -> WhatsAppContact:
        payload = {
            "phone_number": contact.phone_number,
            "display_name": contact.display_name,
            "source": contact.source,
            "consent_status": contact.consent_status,
            "tags": contact.tags,
            "metadata": contact.metadata,
        }
        headers = {**self._headers(), "Prefer": "resolution=merge-duplicates,return=representation"}
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(f"{self.url}/rest/v1/whatsapp_contacts", headers=headers, json=payload)
        response.raise_for_status()
        return self._contact_from_row(response.json()[0])

    async def list_campaigns(self, limit: int = 100) -> list[WhatsAppCampaign]:
        params = {
            "select": "id,name,message_template,status,target_tag,scheduled_for,recipient_count,metadata,created_at",
            "order": "created_at.desc",
            "limit": str(min(max(limit, 1), 500)),
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{self.url}/rest/v1/whatsapp_campaigns",
                headers=self._headers(),
                params=params,
            )
        response.raise_for_status()
        return [self._campaign_from_row(row) for row in response.json()]

    async def create_campaign(self, campaign: WhatsAppCampaign) -> WhatsAppCampaign:
        payload = {
            "name": campaign.name,
            "message_template": campaign.message_template,
            "status": campaign.status,
            "target_tag": campaign.target_tag,
            "scheduled_for": campaign.scheduled_for.isoformat() if campaign.scheduled_for else None,
            "recipient_count": campaign.recipient_count,
            "metadata": campaign.metadata,
        }
        headers = {**self._headers(), "Prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(f"{self.url}/rest/v1/whatsapp_campaigns", headers=headers, json=payload)
        response.raise_for_status()
        return self._campaign_from_row(response.json()[0])

    async def decide_campaign(self, campaign_id: str, approved: bool, decided_by: str) -> WhatsAppCampaign:
        status = "queued" if approved else "cancelled"
        payload = {
            "status": status,
            "metadata": {
                "decision": "approved" if approved else "denied",
                "decided_by": decided_by,
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "requires_approval": False,
            },
        }
        headers = {**self._headers(), "Prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.patch(
                f"{self.url}/rest/v1/whatsapp_campaigns",
                headers=headers,
                params={"id": f"eq.{campaign_id}"},
                json=payload,
            )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise RuntimeError("Campana WhatsApp no encontrada.")
        return self._campaign_from_row(rows[0])

    async def count_opted_in_recipients(self, target_tag: str | None = None) -> int:
        params = {"select": "id", "consent_status": "eq.opted_in"}
        if target_tag:
            params["tags"] = f"cs.{{{target_tag}}}"
        headers = {**self._headers(), "Prefer": "count=exact"}
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{self.url}/rest/v1/whatsapp_contacts",
                headers=headers,
                params=params,
            )
        response.raise_for_status()
        count_range = response.headers.get("content-range", "0-0/0")
        return int(count_range.rsplit("/", 1)[-1])

    def _headers(self) -> dict[str, str]:
        if not self.url or not self.service_role_key:
            raise RuntimeError("WhatsApp Outreach requiere SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY.")
        return {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _contact_from_row(row: dict) -> WhatsAppContact:
        return WhatsAppContact(
            id=row.get("id"),
            phone_number=row["phone_number"],
            display_name=row.get("display_name"),
            source=row.get("source", "manual"),
            consent_status=row.get("consent_status", "opted_in"),
            tags=row.get("tags") or [],
            metadata=row.get("metadata") or {},
            created_at=_parse_datetime(row.get("created_at")),
        )

    @staticmethod
    def _campaign_from_row(row: dict) -> WhatsAppCampaign:
        return WhatsAppCampaign(
            id=row.get("id"),
            name=row["name"],
            message_template=row["message_template"],
            status=row.get("status", "draft"),
            target_tag=row.get("target_tag"),
            scheduled_for=_parse_datetime(row.get("scheduled_for")),
            recipient_count=row.get("recipient_count") or 0,
            metadata=row.get("metadata") or {},
            created_at=_parse_datetime(row.get("created_at")),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
