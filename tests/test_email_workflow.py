import asyncio
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "assistant-runtime"))

from app.domain.email.models import EmailAuditEvent, EmailBulkJob, EmailCategory, EmailMessage, EmailProviderHealth, EmailTemplate
from app.adapters.email import _message_from_dict
from app.use_cases.email_workflow import EmailWorkflow


class FakeEmailConfig:
    def __init__(self) -> None:
        self.templates = [
            EmailTemplate(
                name="seguimiento",
                subject="Re: {{subject}}",
                body="Hola {{name}}, gracias por escribirnos.",
                category="lead",
            )
        ]

    def default_provider(self) -> str:
        return "google"

    def get_template(self, name: str) -> EmailTemplate | None:
        return next((template for template in self.templates if template.name == name), None)

    def list_templates(self) -> list[EmailTemplate]:
        return self.templates

    def list_categories(self) -> list[EmailCategory]:
        return [EmailCategory(name="lead", description="Leads entrantes")]


class FakeEmailProvider:
    def __init__(self) -> None:
        self.sent_calls = []

    async def check_health(self) -> EmailProviderHealth:
        return EmailProviderHealth(
            provider="google",
            configured=True,
            read_enabled=True,
            send_enabled=True,
            detail="ok",
            account_id="team@example.com",
        )

    async def list_sent_on(self, day: date) -> list[EmailMessage]:
        return [
            EmailMessage(
                id="email-1",
                provider="google",
                account_id="team@example.com",
                subject="Propuesta",
                sender="team@example.com",
                recipients=["lead@example.com"],
                sent_at=datetime(2026, 5, 20, 9, 0, 0),
            )
        ]

    async def search_by_category(self, category: str, limit: int = 100) -> list[EmailMessage]:
        return [
            EmailMessage(
                id="email-2",
                provider="google",
                account_id="team@example.com",
                subject="Quiero info",
                sender="lead@example.com",
                recipients=["team@example.com"],
                sent_at=datetime(2026, 5, 20, 8, 0, 0),
            )
        ]

    async def send_bulk_replies(self, email_ids: list[str], template: EmailTemplate, dry_run: bool) -> dict:
        self.sent_calls.append({"email_ids": email_ids, "template": template.name, "dry_run": dry_run})
        return {"status": "sent" if not dry_run else "planned", "email_ids": email_ids, "template": template.name, "dry_run": dry_run}


class FakeEmailJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, EmailBulkJob] = {}
        self.audit: list[EmailAuditEvent] = []

    async def create_bulk_job(self, job: EmailBulkJob) -> EmailBulkJob:
        self.jobs[job.id] = job
        return job

    async def get_bulk_job(self, job_id: str) -> EmailBulkJob:
        return self.jobs[job_id]

    async def approve_bulk_job(self, job_id: str, approved_by: str | None) -> EmailBulkJob:
        from dataclasses import replace
        from datetime import datetime, timezone

        from app.domain.email.models import EmailBulkJobStatus

        job = self.jobs[job_id]
        approved = replace(job, status=EmailBulkJobStatus.approved, approved_by=approved_by, approved_at=datetime.now(timezone.utc))
        self.jobs[job_id] = approved
        return approved

    async def reject_bulk_job(self, job_id: str, rejected_by: str | None, reason: str) -> EmailBulkJob:
        from dataclasses import replace

        from app.domain.email.models import EmailBulkJobStatus

        job = replace(self.jobs[job_id], status=EmailBulkJobStatus.cancelled)
        self.jobs[job_id] = job
        return job

    async def mark_bulk_job_queued(self, job_id: str, provider_result: dict) -> EmailBulkJob:
        from dataclasses import replace

        from app.domain.email.models import EmailBulkJobStatus

        job = replace(self.jobs[job_id], status=EmailBulkJobStatus.queued, provider_result=provider_result)
        self.jobs[job_id] = job
        return job

    async def mark_bulk_job_status(self, job_id: str, status: str, provider_result: dict | None = None) -> EmailBulkJob:
        from dataclasses import replace

        from app.domain.email.models import EmailBulkJobStatus

        job = replace(self.jobs[job_id], status=EmailBulkJobStatus(status), provider_result=provider_result or self.jobs[job_id].provider_result)
        self.jobs[job_id] = job
        return job

    async def update_recipient_status(
        self,
        job_id: str,
        email_id: str,
        status: str,
        provider_message_id: str | None = None,
        error_detail: str | None = None,
    ) -> None:
        from dataclasses import replace

        job = self.jobs[job_id]
        recipients = [replace(item, status=status) if item.email_id == email_id else item for item in job.recipients]
        self.jobs[job_id] = replace(job, recipients=recipients)

    async def list_bulk_jobs(self, statuses: list[str] | None = None, limit: int = 50) -> list[EmailBulkJob]:
        jobs = list(self.jobs.values())
        if statuses:
            jobs = [job for job in jobs if job.status.value in set(statuses)]
        return jobs[:limit]

    async def append_audit(self, event: EmailAuditEvent) -> None:
        self.audit.append(event)


class EmailWorkflowTests(unittest.TestCase):
    def test_status_includes_provider_and_templates(self) -> None:
        async def scenario() -> None:
            workflow = EmailWorkflow(FakeEmailProvider(), FakeEmailConfig(), FakeEmailJobRepository(), llm=None)
            result = await workflow.run("status", {"sub_command": "status"})
            self.assertEqual(result["status"], "success")
            self.assertIn("team@example.com", result["message"])
            self.assertEqual(result["email_status"]["templates"], ["seguimiento"])
            self.assertEqual(result["email_status"]["categories"], ["lead"])

        asyncio.run(scenario())

    def test_bulk_reply_requires_approval_by_default(self) -> None:
        async def scenario() -> None:
            provider = FakeEmailProvider()
            jobs = FakeEmailJobRepository()
            workflow = EmailWorkflow(provider, FakeEmailConfig(), jobs, llm=None)
            result = await workflow.run(
                "lead",
                {
                    "sub_command": "bulk-reply",
                    "template_name": "seguimiento",
                    "category": "lead",
                    "requested_by": "user-1",
                },
            )
            self.assertEqual(result["status"], "requires_approval")
            self.assertTrue(result["requires_approval"])
            self.assertTrue(result["email_bulk_reply"]["provider_result"]["dry_run"])
            self.assertEqual(len(jobs.jobs), 1)
            self.assertEqual(provider.sent_calls[-1]["dry_run"], True)

        asyncio.run(scenario())

    def test_approved_bulk_reply_queues_without_provider_send(self) -> None:
        async def scenario() -> None:
            provider = FakeEmailProvider()
            jobs = FakeEmailJobRepository()
            workflow = EmailWorkflow(provider, FakeEmailConfig(), jobs, llm=None)
            prepared = await workflow.run(
                "lead",
                {"sub_command": "bulk-reply", "template_name": "seguimiento", "category": "lead"},
            )
            job_id = prepared["email_bulk_reply"]["job_id"]
            approved = await workflow.run(
                "approve",
                {"sub_command": "bulk-reply", "job_id": job_id, "is_approved": True, "approved_by": "manager-1"},
            )
            self.assertEqual(approved["status"], "accepted")
            self.assertFalse(approved["requires_approval"])
            self.assertEqual(approved["email_bulk_reply"]["status"], "queued")
            self.assertEqual(len(provider.sent_calls), 1)
            self.assertEqual(provider.sent_calls[-1]["dry_run"], True)

        asyncio.run(scenario())

    def test_process_queued_sends_pending_recipients_once(self) -> None:
        async def scenario() -> None:
            provider = FakeEmailProvider()
            jobs = FakeEmailJobRepository()
            workflow = EmailWorkflow(provider, FakeEmailConfig(), jobs, llm=None)
            prepared = await workflow.run(
                "lead",
                {"sub_command": "bulk-reply", "template_name": "seguimiento", "category": "lead"},
            )
            job_id = prepared["email_bulk_reply"]["job_id"]
            await workflow.run(
                "approve",
                {"sub_command": "bulk-reply", "job_id": job_id, "is_approved": True, "approved_by": "manager-1"},
            )
            processed = await workflow.run("process", {"sub_command": "process-queued"})
            self.assertEqual(processed["status"], "success")
            self.assertEqual(jobs.jobs[job_id].status.value, "sent")
            self.assertEqual(provider.sent_calls[-1]["dry_run"], False)
            self.assertEqual(jobs.jobs[job_id].recipients[0].status, "sent")

        asyncio.run(scenario())

    def test_pc_client_message_mapping_keeps_recipients_as_addresses(self) -> None:
        message = _message_from_dict(
            {
                "id": "local-1",
                "subject": "Hola",
                "from": "sender@example.com",
                "to": "a@example.com,b@example.com",
                "date": "2026-05-20T10:00:00Z",
            },
            provider="pc_client",
            account_id="team@example.com",
        )

        self.assertEqual(message.recipients, ["a@example.com", "b@example.com"])
        self.assertEqual(message.sender, "sender@example.com")


if __name__ == "__main__":
    unittest.main()
