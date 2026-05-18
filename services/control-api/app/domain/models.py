from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class ServiceState(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    offline = "offline"
    unknown = "unknown"


class SourceType(str, Enum):
    kalshi_market = "kalshi_market"
    trend = "trend"
    rss = "rss"
    website = "website"
    manual = "manual"


@dataclass(frozen=True)
class ServiceStatus:
    name: str
    state: ServiceState
    detail: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DiscordConfig:
    requests_channel_id: str | None
    notifications_channel_id: str | None
    status_channel_id: str | None


@dataclass(frozen=True)
class KnowledgeSource:
    name: str
    source_type: SourceType
    url: str | None = None
    schedule: str | None = None
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class MentisVerification:
    reachable: bool
    can_read: bool
    can_write: bool
    detail: str
    latency_ms: int | None = None


@dataclass(frozen=True)
class SupabaseVerification:
    reachable: bool
    rest_available: bool
    knowledge_schema_ready: bool
    has_publishable_key: bool
    has_service_role_key: bool
    detail: str


@dataclass(frozen=True)
class IngestionSchedule:
    market_ingestion_cron: str
    trends_ingestion_cron: str
    mentis_sync_cron: str


@dataclass(frozen=True)
class IngestionRun:
    id: str
    target: str
    status: str
    detail: str
    started_at: datetime
    finished_at: datetime | None = None


@dataclass(frozen=True)
class MemoryFragment:
    category: str
    summary: str
    metadata: dict = field(default_factory=dict)
    id: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class ConsolidationRecord:
    id: str
    category: str
    title: str
    summary: str
    status: str
    memory_count: int
    metadata: dict
    created_at: datetime


@dataclass(frozen=True)
class WhatsAppContact:
    phone_number: str
    display_name: str | None = None
    source: str = "manual"
    consent_status: str = "opted_in"
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class WhatsAppCampaign:
    name: str
    message_template: str
    status: str = "draft"
    target_tag: str | None = None
    scheduled_for: datetime | None = None
    recipient_count: int = 0
    metadata: dict = field(default_factory=dict)
    id: str | None = None
    created_at: datetime | None = None
