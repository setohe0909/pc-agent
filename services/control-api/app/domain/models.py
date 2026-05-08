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


@dataclass(frozen=True)
class SupabaseVerification:
    reachable: bool
    rest_available: bool
    knowledge_schema_ready: bool
    has_publishable_key: bool
    has_service_role_key: bool
    detail: str
