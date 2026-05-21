from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


@dataclass(frozen=True)
class EmailMessage:
    id: str
    provider: str
    account_id: str
    subject: str
    sender: str
    recipients: list[str]
    sent_at: datetime
    snippet: str = ""
    labels: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EmailCategory:
    name: str
    description: str
    filters: dict = field(default_factory=dict)
    confidence_threshold: float = 0.7


@dataclass(frozen=True)
class EmailTemplate:
    name: str
    subject: str
    body: str
    category: str | None = None
    requires_approval: bool = True
    rate_limit_per_minute: int = 30


@dataclass(frozen=True)
class BulkEmailReplyPlan:
    template: EmailTemplate
    category: str
    matched_email_ids: list[str]
    dry_run: bool = True
    requires_approval: bool = True


@dataclass(frozen=True)
class EmailProviderHealth:
    provider: str
    configured: bool
    read_enabled: bool
    send_enabled: bool
    detail: str
    account_id: str | None = None


class EmailBulkJobStatus(str, Enum):
    requires_approval = "requires_approval"
    approved = "approved"
    queued = "queued"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


@dataclass(frozen=True)
class EmailBulkRecipient:
    email_id: str
    recipient: str
    subject: str
    status: str = "pending"
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EmailBulkJob:
    id: str
    provider: str
    account_id: str | None
    template: EmailTemplate
    category: str
    status: EmailBulkJobStatus
    requested_by: str | None
    recipients: list[EmailBulkRecipient]
    approved_by: str | None = None
    approved_at: datetime | None = None
    provider_result: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def recipient_count(self) -> int:
        return len(self.recipients)


@dataclass(frozen=True)
class EmailAuditEvent:
    event_type: str
    actor_id: str | None
    detail: str
    job_id: str | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
