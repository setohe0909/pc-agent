from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class CoderWebFile:
    path: str
    content: str
    encoding: str = "utf-8"


@dataclass(frozen=True)
class CoderWebAsset:
    path: str
    content_b64: str


@dataclass(frozen=True)
class CoderWebTask:
    name: str
    description: str
    stack: str
    plan: dict
    files: list[CoderWebFile]
    assets: list[CoderWebAsset] = field(default_factory=list)
    repository_full_name: str | None = None
    base_branch: str = "main"
    branch_name: str | None = None
    linear_issue_id: str | None = None
    preview_required: bool = False


class CoderWebPort(Protocol):
    async def execute_task(self, task: CoderWebTask) -> dict:
        """Apply a generated web task to source control and return PR/deploy/audit details."""
        ...
