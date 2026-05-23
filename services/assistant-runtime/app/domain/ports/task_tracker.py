from typing import Protocol


class TaskTrackerPort(Protocol):
    async def get_issue(self, issue_id: str) -> dict | None:
        ...
