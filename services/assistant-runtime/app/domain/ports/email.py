from datetime import date
from typing import Protocol

from app.domain.email.models import EmailMessage, EmailProviderHealth, EmailTemplate


class EmailProviderPort(Protocol):
    async def check_health(self) -> EmailProviderHealth:
        ...

    async def list_sent_on(self, day: date) -> list[EmailMessage]:
        ...

    async def search_by_category(self, category: str, limit: int = 100) -> list[EmailMessage]:
        ...

    async def send_bulk_replies(self, email_ids: list[str], template: EmailTemplate, dry_run: bool) -> dict:
        ...


class EmailConfigPort(Protocol):
    def default_provider(self) -> str:
        ...

    def get_template(self, name: str) -> EmailTemplate | None:
        ...

    def list_templates(self) -> list[EmailTemplate]:
        ...
