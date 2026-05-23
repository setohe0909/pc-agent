import json
import os
from pathlib import Path

import httpx

from app.domain.ports.task_tracker import TaskTrackerPort


class LinearTaskTrackerAdapter(TaskTrackerPort):
    def __init__(self) -> None:
        self.config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
        self.api_url = os.getenv("LINEAR_API_BASE_URL", "https://api.linear.app/graphql")

    async def get_issue(self, issue_id: str) -> dict | None:
        token = self._runtime_config().get("linear_api_key") or os.getenv("LINEAR_API_KEY")
        if not token or not issue_id:
            return None
        query = """
        query Issue($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            description
            priority
            url
            assignee { name email }
            team { name key }
            project { name }
          }
        }
        """
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.api_url,
                headers={"Authorization": token, "Content-Type": "application/json"},
                json={"query": query, "variables": {"id": issue_id}},
            )
        if response.status_code >= 400:
            raise RuntimeError(f"Linear issue lookup HTTP {response.status_code}: {response.text[:240]}")
        data = response.json()
        if data.get("errors"):
            raise RuntimeError(f"Linear issue lookup error: {data['errors'][:1]}")
        return data.get("data", {}).get("issue")

    def _runtime_config(self) -> dict:
        try:
            path = Path(self.config_path)
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return {}
