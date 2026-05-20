from dataclasses import dataclass, field
from datetime import datetime


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
