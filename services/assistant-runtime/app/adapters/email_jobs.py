import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.domain.email.models import (
    EmailAuditEvent,
    EmailBulkJob,
    EmailBulkJobStatus,
    EmailBulkRecipient,
    EmailTemplate,
)
from app.domain.ports.email import EmailJobRepositoryPort


class SupabaseEmailJobRepository(EmailJobRepositoryPort):
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    @property
    def configured(self) -> bool:
        return bool(self.url and self.key)

    async def create_bulk_job(self, job: EmailBulkJob) -> EmailBulkJob:
        self._ensure_configured()
        headers = self._headers("return=minimal")
        job_payload = {
            "id": job.id,
            "provider": job.provider,
            "account_id": job.account_id,
            "template_name": job.template.name,
            "template_subject": job.template.subject,
            "template_body": job.template.body,
            "category": job.category,
            "status": job.status.value,
            "requested_by": job.requested_by,
            "recipient_count": job.recipient_count,
            "provider_result": job.provider_result,
            "metadata": {
                **job.metadata,
                "template": {
                    "category": job.template.category,
                    "requires_approval": job.template.requires_approval,
                    "rate_limit_per_minute": job.template.rate_limit_per_minute,
                },
            },
            "created_at": job.created_at.isoformat(),
        }
        recipient_payload = [
            {
                "job_id": job.id,
                "email_id": recipient.email_id,
                "recipient": recipient.recipient,
                "subject": recipient.subject,
                "status": recipient.status,
                "metadata": recipient.metadata,
            }
            for recipient in job.recipients
        ]
        async with httpx.AsyncClient(timeout=10) as client:
            job_response = await client.post(self._table_url("email_bulk_jobs"), headers=headers, json=job_payload)
            self._raise_for_supabase(job_response, "create email_bulk_jobs")
            if recipient_payload:
                recipient_response = await client.post(
                    self._table_url("email_bulk_job_recipients"),
                    headers=headers,
                    json=recipient_payload,
                )
                self._raise_for_supabase(recipient_response, "create email_bulk_job_recipients")
        return job

    async def get_bulk_job(self, job_id: str) -> EmailBulkJob:
        self._ensure_configured()
        headers = self._headers()
        async with httpx.AsyncClient(timeout=10) as client:
            job_response = await client.get(
                self._table_url("email_bulk_jobs"),
                headers=headers,
                params={"id": f"eq.{job_id}", "select": "*", "limit": "1"},
            )
            self._raise_for_supabase(job_response, "get email_bulk_jobs")
            rows = job_response.json()
            if not rows:
                raise RuntimeError(f"No existe el job de email `{job_id}`.")
            recipient_response = await client.get(
                self._table_url("email_bulk_job_recipients"),
                headers=headers,
                params={"job_id": f"eq.{job_id}", "select": "*", "order": "created_at.asc"},
            )
            self._raise_for_supabase(recipient_response, "get email_bulk_job_recipients")
        return _supabase_job_from_rows(rows[0], recipient_response.json())

    async def approve_bulk_job(self, job_id: str, approved_by: str | None) -> EmailBulkJob:
        job = await self.get_bulk_job(job_id)
        if job.status not in {EmailBulkJobStatus.requires_approval, EmailBulkJobStatus.approved}:
            raise RuntimeError(f"El job `{job_id}` no se puede aprobar desde estado `{job.status.value}`.")
        approved_at = datetime.now(timezone.utc)
        await self._patch_job(
            job_id,
            {"status": EmailBulkJobStatus.approved.value, "approved_by": approved_by, "approved_at": approved_at.isoformat()},
        )
        return replace(job, status=EmailBulkJobStatus.approved, approved_by=approved_by, approved_at=approved_at)

    async def reject_bulk_job(self, job_id: str, rejected_by: str | None, reason: str) -> EmailBulkJob:
        job = await self.get_bulk_job(job_id)
        if job.status not in {EmailBulkJobStatus.requires_approval, EmailBulkJobStatus.approved}:
            raise RuntimeError(f"El job `{job_id}` no se puede denegar desde estado `{job.status.value}`.")
        metadata = {**job.metadata, "rejected_by": rejected_by, "rejection_reason": reason}
        await self._patch_job(job_id, {"status": EmailBulkJobStatus.cancelled.value, "metadata": metadata})
        return replace(job, status=EmailBulkJobStatus.cancelled, metadata=metadata)

    async def mark_bulk_job_queued(self, job_id: str, provider_result: dict) -> EmailBulkJob:
        job = await self.get_bulk_job(job_id)
        await self._patch_job(
            job_id,
            {"status": EmailBulkJobStatus.queued.value, "provider_result": provider_result},
        )
        return replace(job, status=EmailBulkJobStatus.queued, provider_result=provider_result)

    async def append_audit(self, event: EmailAuditEvent) -> None:
        self._ensure_configured()
        payload = _audit_to_dict(event)
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self._table_url("email_audit_events"), headers=self._headers("return=minimal"), json=payload)
        self._raise_for_supabase(response, "create email_audit_events")

    async def _patch_job(self, job_id: str, payload: dict) -> None:
        self._ensure_configured()
        payload = {**payload, "updated_at": datetime.now(timezone.utc).isoformat()}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.patch(
                self._table_url("email_bulk_jobs"),
                headers=self._headers("return=minimal"),
                params={"id": f"eq.{job_id}"},
                json=payload,
            )
        self._raise_for_supabase(response, "patch email_bulk_jobs")

    def _table_url(self, table: str) -> str:
        return f"{self.url.rstrip('/')}/rest/v1/{table}"

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": str(self.key),
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise RuntimeError("Supabase no esta configurado para persistir jobs de email.")

    @staticmethod
    def _raise_for_supabase(response: httpx.Response, operation: str) -> None:
        if response.status_code >= 400:
            raise RuntimeError(f"Supabase {operation} HTTP {response.status_code}: {response.text[:240]}")


class FileEmailJobRepository(EmailJobRepositoryPort):
    def __init__(self, path: str | None = None) -> None:
        default_path = os.getenv("EMAIL_JOBS_PATH", "/tmp/pc-agent-email-jobs.json")
        self.path = Path(path or default_path)

    async def create_bulk_job(self, job: EmailBulkJob) -> EmailBulkJob:
        data = self._read()
        data.setdefault("jobs", {})[job.id] = _job_to_dict(job)
        self._write(data)
        return job

    async def get_bulk_job(self, job_id: str) -> EmailBulkJob:
        data = self._read()
        raw = data.get("jobs", {}).get(job_id)
        if not raw:
            raise RuntimeError(f"No existe el job de email `{job_id}`.")
        return _job_from_dict(raw)

    async def approve_bulk_job(self, job_id: str, approved_by: str | None) -> EmailBulkJob:
        job = await self.get_bulk_job(job_id)
        if job.status not in {EmailBulkJobStatus.requires_approval, EmailBulkJobStatus.approved}:
            raise RuntimeError(f"El job `{job_id}` no se puede aprobar desde estado `{job.status.value}`.")
        updated = replace(
            job,
            status=EmailBulkJobStatus.approved,
            approved_by=approved_by,
            approved_at=datetime.now(timezone.utc),
        )
        await self._replace_job(updated)
        return updated

    async def reject_bulk_job(self, job_id: str, rejected_by: str | None, reason: str) -> EmailBulkJob:
        job = await self.get_bulk_job(job_id)
        if job.status not in {EmailBulkJobStatus.requires_approval, EmailBulkJobStatus.approved}:
            raise RuntimeError(f"El job `{job_id}` no se puede denegar desde estado `{job.status.value}`.")
        metadata = {**job.metadata, "rejected_by": rejected_by, "rejection_reason": reason}
        updated = replace(job, status=EmailBulkJobStatus.cancelled, metadata=metadata)
        await self._replace_job(updated)
        return updated

    async def mark_bulk_job_queued(self, job_id: str, provider_result: dict) -> EmailBulkJob:
        job = await self.get_bulk_job(job_id)
        updated = replace(job, status=EmailBulkJobStatus.queued, provider_result=provider_result)
        await self._replace_job(updated)
        return updated

    async def append_audit(self, event: EmailAuditEvent) -> None:
        data = self._read()
        data.setdefault("audit", []).append(_audit_to_dict(event))
        self._write(data)

    async def _replace_job(self, job: EmailBulkJob) -> None:
        data = self._read()
        data.setdefault("jobs", {})[job.id] = _job_to_dict(job)
        self._write(data)

    def _read(self) -> dict:
        if not self.path.exists():
            return {"jobs": {}, "audit": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"jobs": {}, "audit": []}
        if not isinstance(data, dict):
            return {"jobs": {}, "audit": []}
        data.setdefault("jobs", {})
        data.setdefault("audit", [])
        return data

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)


def _job_to_dict(job: EmailBulkJob) -> dict:
    return {
        "id": job.id,
        "provider": job.provider,
        "account_id": job.account_id,
        "template": {
            "name": job.template.name,
            "subject": job.template.subject,
            "body": job.template.body,
            "category": job.template.category,
            "requires_approval": job.template.requires_approval,
            "rate_limit_per_minute": job.template.rate_limit_per_minute,
        },
        "category": job.category,
        "status": job.status.value,
        "requested_by": job.requested_by,
        "approved_by": job.approved_by,
        "approved_at": job.approved_at.isoformat() if job.approved_at else None,
        "provider_result": job.provider_result,
        "metadata": job.metadata,
        "created_at": job.created_at.isoformat(),
        "recipients": [
            {
                "email_id": recipient.email_id,
                "recipient": recipient.recipient,
                "subject": recipient.subject,
                "status": recipient.status,
                "metadata": recipient.metadata,
            }
            for recipient in job.recipients
        ],
    }


def _job_from_dict(data: dict) -> EmailBulkJob:
    template_data = data.get("template") or {}
    return EmailBulkJob(
        id=str(data.get("id") or ""),
        provider=str(data.get("provider") or ""),
        account_id=data.get("account_id"),
        template=EmailTemplate(
            name=str(template_data.get("name") or ""),
            subject=str(template_data.get("subject") or ""),
            body=str(template_data.get("body") or ""),
            category=template_data.get("category"),
            requires_approval=bool(template_data.get("requires_approval", True)),
            rate_limit_per_minute=int(template_data.get("rate_limit_per_minute") or 30),
        ),
        category=str(data.get("category") or ""),
        status=EmailBulkJobStatus(str(data.get("status") or EmailBulkJobStatus.requires_approval.value)),
        requested_by=data.get("requested_by"),
        recipients=[
            EmailBulkRecipient(
                email_id=str(item.get("email_id") or ""),
                recipient=str(item.get("recipient") or ""),
                subject=str(item.get("subject") or ""),
                status=str(item.get("status") or "pending"),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in data.get("recipients", [])
            if isinstance(item, dict)
        ],
        approved_by=data.get("approved_by"),
        approved_at=_parse_datetime(data.get("approved_at")),
        provider_result=dict(data.get("provider_result") or {}),
        metadata=dict(data.get("metadata") or {}),
        created_at=_parse_datetime(data.get("created_at")) or datetime.now(timezone.utc),
    )


def _supabase_job_from_rows(job: dict, recipients: list[dict]) -> EmailBulkJob:
    metadata = dict(job.get("metadata") or {})
    template_metadata = dict(metadata.get("template") or {})
    return EmailBulkJob(
        id=str(job.get("id") or ""),
        provider=str(job.get("provider") or ""),
        account_id=job.get("account_id"),
        template=EmailTemplate(
            name=str(job.get("template_name") or ""),
            subject=str(job.get("template_subject") or ""),
            body=str(job.get("template_body") or ""),
            category=template_metadata.get("category"),
            requires_approval=bool(template_metadata.get("requires_approval", True)),
            rate_limit_per_minute=int(template_metadata.get("rate_limit_per_minute") or 30),
        ),
        category=str(job.get("category") or ""),
        status=EmailBulkJobStatus(str(job.get("status") or EmailBulkJobStatus.requires_approval.value)),
        requested_by=job.get("requested_by"),
        recipients=[
            EmailBulkRecipient(
                email_id=str(item.get("email_id") or ""),
                recipient=str(item.get("recipient") or ""),
                subject=str(item.get("subject") or ""),
                status=str(item.get("status") or "pending"),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in recipients
            if isinstance(item, dict)
        ],
        approved_by=job.get("approved_by"),
        approved_at=_parse_datetime(job.get("approved_at")),
        provider_result=dict(job.get("provider_result") or {}),
        metadata=metadata,
        created_at=_parse_datetime(job.get("created_at")) or datetime.now(timezone.utc),
    )


def _audit_to_dict(event: EmailAuditEvent) -> dict:
    return {
        "event_type": event.event_type,
        "actor_id": event.actor_id,
        "detail": event.detail,
        "job_id": event.job_id,
        "metadata": event.metadata,
        "created_at": event.created_at.isoformat(),
    }


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
