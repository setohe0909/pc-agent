from datetime import date
from typing import Protocol

from app.domain.email.models import EmailAuditEvent, EmailBulkJob, EmailCategory, EmailMessage, EmailProviderHealth, EmailTemplate


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

    def list_categories(self) -> list[EmailCategory]:
        ...


class EmailJobRepositoryPort(Protocol):
    async def create_bulk_job(self, job: EmailBulkJob) -> EmailBulkJob:
        ...

    async def get_bulk_job(self, job_id: str) -> EmailBulkJob:
        ...

    async def approve_bulk_job(self, job_id: str, approved_by: str | None) -> EmailBulkJob:
        ...

    async def reject_bulk_job(self, job_id: str, rejected_by: str | None, reason: str) -> EmailBulkJob:
        ...

    async def mark_bulk_job_queued(self, job_id: str, provider_result: dict) -> EmailBulkJob:
        ...

    async def mark_bulk_job_status(self, job_id: str, status: str, provider_result: dict | None = None) -> EmailBulkJob:
        ...

    async def update_recipient_status(
        self,
        job_id: str,
        email_id: str,
        status: str,
        provider_message_id: str | None = None,
        error_detail: str | None = None,
    ) -> None:
        ...

    async def list_bulk_jobs(self, statuses: list[str] | None = None, limit: int = 50) -> list[EmailBulkJob]:
        ...

    async def append_audit(self, event: EmailAuditEvent) -> None:
        ...
