import asyncio
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "assistant-runtime"))

from app.domain.email.models import EmailMessage, EmailProviderHealth, EmailTemplate
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


class FakeEmailProvider:
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
        return {"email_ids": email_ids, "template": template.name, "dry_run": dry_run}


class EmailWorkflowTests(unittest.TestCase):
    def test_status_includes_provider_and_templates(self) -> None:
        async def scenario() -> None:
            workflow = EmailWorkflow(FakeEmailProvider(), FakeEmailConfig(), llm=None)
            result = await workflow.run("status", {"sub_command": "status"})
            self.assertEqual(result["status"], "success")
            self.assertIn("team@example.com", result["message"])
            self.assertEqual(result["email_status"]["templates"], ["seguimiento"])

        asyncio.run(scenario())

    def test_bulk_reply_requires_approval_by_default(self) -> None:
        async def scenario() -> None:
            workflow = EmailWorkflow(FakeEmailProvider(), FakeEmailConfig(), llm=None)
            result = await workflow.run(
                "lead",
                {"sub_command": "bulk-reply", "template_name": "seguimiento", "category": "lead"},
            )
            self.assertEqual(result["status"], "requires_approval")
            self.assertTrue(result["requires_approval"])
            self.assertTrue(result["email_bulk_reply"]["dry_run"])

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
