from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CampaignPlan:
    id: str
    topic: str
    goal: str
    audience: str
    channels: list[str]
    pillars: list[str]
    calendar: list[dict[str, Any]]
    kpis: list[str]
    source_insights: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PostDraft:
    id: str
    campaign_id: str
    platform: str
    format: str
    hook: str
    caption: str
    cta: str
    hashtags: list[str]
    scheduled_window: str
    metric_goal: str
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AutomationAction:
    action_type: str
    resource_type: str
    payload: dict[str, Any]
    dedupe_key: str
    external_write: bool = False
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AutomationResult:
    status: str
    message: str
    actions: list[AutomationAction] = field(default_factory=list)
    campaign: CampaignPlan | None = None
    posts: list[PostDraft] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requires_approval: bool = False

    def to_response(self) -> dict[str, Any]:
        response: dict[str, Any] = {
            "status": self.status,
            "message": self.message,
            "warnings": self.warnings,
            "requires_approval": self.requires_approval,
            "actions": [action.to_dict() for action in self.actions],
        }
        if self.campaign:
            response["campaign"] = self.campaign.to_dict()
        if self.posts:
            response["posts"] = [post.to_dict() for post in self.posts]
        return response
