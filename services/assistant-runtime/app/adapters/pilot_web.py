import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.domain.ports.coder_web import CoderWebAsset, CoderWebFile, CoderWebPort, CoderWebTask


class PilotWebAdapter(CoderWebPort):
    """Production adapter for Coder Web.

    It applies generated code through GitHub branches, commits and pull requests.
    Optional Linear and preview-deploy integrations are driven by runtime config.
    """

    def __init__(self) -> None:
        self.config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
        self.github_api_base_url = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com").rstrip("/")
        self.linear_api_base_url = os.getenv("LINEAR_API_BASE_URL", "https://api.linear.app/graphql").rstrip("/")
        self.run_log_dir = Path(os.getenv("CODER_WEB_RUN_LOG_DIR", "/tmp/pc-agent-coder-web-runs"))

    async def execute_task(self, task: CoderWebTask) -> dict:
        runtime = self._runtime_config()
        token = runtime.get("github_token") or os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("Coder Web requiere GITHUB_TOKEN o github_token en runtime config.")
        repo_full_name = task.repository_full_name or runtime.get("coder_web_repository") or await self._create_repository(task, runtime, token)
        branch_name = _safe_branch_name(task.branch_name or f"coder-web/{task.name}")
        logs: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            headers = _github_headers(token)
            repo = await self._github_json(client, "GET", f"/repos/{repo_full_name}", headers=headers)
            self._assert_repo_permissions(repo)
            base_branch = task.base_branch or repo.get("default_branch") or "main"
            base_ref = await self._github_json(client, "GET", f"/repos/{repo_full_name}/git/ref/heads/{base_branch}", headers=headers)
            base_sha = base_ref["object"]["sha"]
            branch_name = await self._create_branch(client, repo_full_name, branch_name, base_sha, headers)
            logs.append({"step": "branch_created", "branch": branch_name, "base": base_branch, "base_sha": base_sha})

            latest_ref = await self._github_json(client, "GET", f"/repos/{repo_full_name}/git/ref/heads/{branch_name}", headers=headers)
            latest_commit_sha = latest_ref["object"]["sha"]
            latest_commit = await self._github_json(client, "GET", f"/repos/{repo_full_name}/git/commits/{latest_commit_sha}", headers=headers)
            tree_sha = await self._create_tree(client, repo_full_name, latest_commit["tree"]["sha"], task.files, task.assets, headers)
            commit = await self._github_json(
                client,
                "POST",
                f"/repos/{repo_full_name}/git/commits",
                headers=headers,
                json={
                    "message": self._commit_message(task),
                    "tree": tree_sha,
                    "parents": [latest_commit_sha],
                },
            )
            await self._github_json(
                client,
                "PATCH",
                f"/repos/{repo_full_name}/git/refs/heads/{branch_name}",
                headers=headers,
                json={"sha": commit["sha"]},
            )
            logs.append({"step": "commit_created", "commit_sha": commit["sha"], "file_count": len(task.files), "asset_count": len(task.assets)})

            pr = await self._create_pull_request(client, repo_full_name, base_branch, branch_name, task, headers)
            logs.append({"step": "pull_request_created", "number": pr.get("number"), "url": pr.get("html_url")})

            preview = await self._trigger_preview(client, runtime, task, repo_full_name, branch_name, pr)
            logs.append({"step": "preview", **preview})

            linear = await self._update_linear(client, runtime, task, pr, preview)
            if linear:
                logs.append({"step": "linear_updated", **linear})

        run_log_path = self._write_run_log(task, repo_full_name, branch_name, logs)
        rollback = {
            "type": "close_pr_and_delete_branch",
            "pull_request_url": pr.get("html_url"),
            "branch": branch_name,
            "delete_ref_endpoint": f"/repos/{repo_full_name}/git/refs/heads/{branch_name}",
        }
        return {
            "status": "success",
            "repo_url": repo.get("html_url"),
            "repo_full_name": repo_full_name,
            "branch": branch_name,
            "commit_sha": commit["sha"],
            "pull_request_url": pr.get("html_url"),
            "pull_request_number": pr.get("number"),
            "preview": preview,
            "linear": linear,
            "validation": {
                "status": "configured",
                "detail": "El PR incluye workflow de CI para install/build/test cuando el proyecto define scripts.",
                "workflow_path": ".github/workflows/coder-web-validate.yml",
            },
            "rollback": rollback,
            "run_log_path": str(run_log_path),
            "logs": logs,
        }

    async def _create_repository(self, task: CoderWebTask, runtime: dict, token: str) -> str:
        owner = runtime.get("github_org") or runtime.get("github_owner") or os.getenv("GITHUB_OWNER")
        private = _as_bool(runtime.get("coder_web_private_repo", os.getenv("CODER_WEB_PRIVATE_REPO", "true")))
        payload = {
            "name": _safe_repo_name(task.name),
            "description": task.description[:350],
            "private": private,
            "auto_init": True,
        }
        endpoint = f"/orgs/{owner}/repos" if owner else "/user/repos"
        async with httpx.AsyncClient(timeout=30) as client:
            data = await self._github_json(client, "POST", endpoint, headers=_github_headers(token), json=payload)
        return data["full_name"]

    async def _create_branch(self, client: httpx.AsyncClient, repo: str, branch: str, sha: str, headers: dict) -> str:
        candidate = branch
        for index in range(5):
            response = await client.post(
                f"{self.github_api_base_url}/repos/{repo}/git/refs",
                headers=headers,
                json={"ref": f"refs/heads/{candidate}", "sha": sha},
            )
            if response.status_code == 201:
                return candidate
            if response.status_code == 422 and "Reference already exists" in response.text:
                candidate = f"{branch}-{index + 1}"
                continue
            self._raise_github(response, "create branch")
        raise RuntimeError("No pude crear una rama unica para Coder Web.")

    async def _create_tree(
        self,
        client: httpx.AsyncClient,
        repo: str,
        base_tree: str,
        files: list[CoderWebFile],
        assets: list[CoderWebAsset],
        headers: dict,
    ) -> str:
        if not files:
            raise RuntimeError("Coder Web no genero archivos para commit.")
        tree_items = []
        seen_paths = set()
        for file in [*files, _validation_workflow_file(), _runbook_file()]:
            path = _safe_repo_path(file.path)
            if path in seen_paths:
                raise RuntimeError(f"Ruta duplicada en paquete Coder Web: {path}")
            seen_paths.add(path)
            tree_items.append({"path": path, "mode": "100644", "type": "blob", "content": file.content})
        for asset in assets:
            path = _safe_repo_path(asset.path)
            if path in seen_paths:
                raise RuntimeError(f"Ruta duplicada en assets Coder Web: {path}")
            seen_paths.add(path)
            tree_items.append({"path": path, "mode": "100644", "type": "blob", "content": asset.content_b64, "encoding": "base64"})
        tree = await self._github_json(
            client,
            "POST",
            f"/repos/{repo}/git/trees",
            headers=headers,
            json={"base_tree": base_tree, "tree": tree_items},
        )
        return tree["sha"]

    async def _create_pull_request(
        self,
        client: httpx.AsyncClient,
        repo: str,
        base_branch: str,
        branch: str,
        task: CoderWebTask,
        headers: dict,
    ) -> dict:
        body = _pr_body(task)
        if task.linear_issue_id:
            body += f"\n\nLinear: {task.linear_issue_id}"
        return await self._github_json(
            client,
            "POST",
            f"/repos/{repo}/pulls",
            headers=headers,
            json={"title": f"Coder Web: {task.name}", "head": branch, "base": base_branch, "body": body},
        )

    async def _trigger_preview(self, client: httpx.AsyncClient, runtime: dict, task: CoderWebTask, repo: str, branch: str, pr: dict) -> dict:
        hook_url = runtime.get("coder_web_preview_deploy_hook_url") or os.getenv("CODER_WEB_PREVIEW_DEPLOY_HOOK_URL")
        if not hook_url:
            if task.preview_required:
                raise RuntimeError("Preview deploy requerido, pero falta CODER_WEB_PREVIEW_DEPLOY_HOOK_URL.")
            return {"status": "not_configured"}
        payload = {"repository": repo, "branch": branch, "pull_request": pr.get("html_url"), "task": task.name}
        response = await client.post(str(hook_url), json=payload, timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(f"Preview deploy hook HTTP {response.status_code}: {response.text[:240]}")
        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text[:240]}
        return {"status": "triggered", "response": data}

    async def _update_linear(self, client: httpx.AsyncClient, runtime: dict, task: CoderWebTask, pr: dict, preview: dict) -> dict | None:
        issue_id = task.linear_issue_id
        token = runtime.get("linear_api_key") or os.getenv("LINEAR_API_KEY")
        if not issue_id or not token:
            return None
        comment = (
            f"Coder Web creó PR: {pr.get('html_url')}\n\n"
            f"Preview: `{preview.get('status')}`\n"
            "Validación: workflow de CI incluido en el PR."
        )
        query = """
        mutation CreateComment($issueId: String!, $body: String!) {
          commentCreate(input: {issueId: $issueId, body: $body}) {
            success
            comment { id url }
          }
        }
        """
        response = await client.post(
            self.linear_api_base_url,
            headers={"Authorization": token, "Content-Type": "application/json"},
            json={"query": query, "variables": {"issueId": issue_id, "body": comment}},
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Linear comment HTTP {response.status_code}: {response.text[:240]}")
        data = response.json()
        if data.get("errors"):
            raise RuntimeError(f"Linear GraphQL error: {data['errors'][:1]}")
        return {"issue_id": issue_id, "comment_url": data.get("data", {}).get("commentCreate", {}).get("comment", {}).get("url")}

    async def _github_json(self, client: httpx.AsyncClient, method: str, path: str, headers: dict, json: dict | None = None) -> dict:
        response = await client.request(method, f"{self.github_api_base_url}{path}", headers=headers, json=json)
        if response.status_code >= 400:
            self._raise_github(response, method.lower())
        return response.json()

    def _assert_repo_permissions(self, repo: dict) -> None:
        permissions = repo.get("permissions") or {}
        if not (permissions.get("push") or permissions.get("maintain") or permissions.get("admin")):
            raise RuntimeError("El token de GitHub no tiene permiso de escritura sobre el repositorio destino.")

    def _commit_message(self, task: CoderWebTask) -> str:
        suffix = f"\n\nLinear: {task.linear_issue_id}" if task.linear_issue_id else ""
        return f"Coder Web: {task.name}{suffix}"

    def _runtime_config(self) -> dict:
        try:
            path = Path(self.config_path)
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return {}

    def _write_run_log(self, task: CoderWebTask, repo: str, branch: str, logs: list[dict]) -> Path:
        self.run_log_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_log_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_safe_repo_name(task.name)}.json"
        path.write_text(
            json.dumps(
                {"task": task.name, "repo": repo, "branch": branch, "linear_issue_id": task.linear_issue_id, "logs": logs},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return path

    def _raise_github(self, response: httpx.Response, operation: str) -> None:
        raise RuntimeError(f"GitHub {operation} HTTP {response.status_code}: {response.text[:240]}")


def _github_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _validation_workflow_file() -> CoderWebFile:
    return CoderWebFile(
        path=".github/workflows/coder-web-validate.yml",
        content="""name: Coder Web Validate

on:
  pull_request:
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        if: hashFiles('package.json') != ''
        with:
          node-version: '22'
          cache: npm
      - run: npm ci
        if: hashFiles('package-lock.json') != ''
      - run: npm install
        if: hashFiles('package.json') != '' && hashFiles('package-lock.json') == ''
      - run: npm run lint --if-present
        if: hashFiles('package.json') != ''
      - run: npm test -- --watch=false
        if: hashFiles('package.json') != ''
        continue-on-error: false
      - run: npm run build --if-present
        if: hashFiles('package.json') != ''
""",
    )


def _runbook_file() -> CoderWebFile:
    return CoderWebFile(
        path="docs/coder-web-runbook.md",
        content=(
            "# Coder Web Runbook\n\n"
            "- Review the pull request diff and CI checks before merge.\n"
            "- Rollback by closing the PR and deleting the branch if validation fails.\n"
            "- Preview deploy status is recorded in the Coder Web response and run log.\n"
        ),
    )


def _pr_body(task: CoderWebTask) -> str:
    return (
        "## Coder Web Production Task\n\n"
        f"Stack: `{task.stack}`\n\n"
        "### Plan\n"
        f"```json\n{json.dumps(task.plan, indent=2, sort_keys=True)}\n```\n\n"
        "### Production controls\n"
        "- Code committed to an isolated branch.\n"
        "- Pull request opened for human review.\n"
        "- CI validation workflow included.\n"
        "- Rollback path: close PR and delete branch.\n"
    )


def _safe_repo_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip()).strip(".-")
    if not cleaned:
        raise RuntimeError("Coder Web no pudo derivar un nombre valido de repositorio.")
    return cleaned[:90]


def _safe_branch_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9/_-]+", "-", value.strip()).strip("/-")
    if ".." in cleaned or cleaned.endswith(".lock"):
        raise RuntimeError("Nombre de rama inseguro para GitHub.")
    return cleaned[:180] or f"coder-web/{os.urandom(3).hex()}"


def _safe_repo_path(value: str) -> str:
    path = value.strip().replace("\\", "/").lstrip("/")
    parts = [part for part in path.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise RuntimeError(f"Ruta insegura en paquete Coder Web: {value}")
    if parts[0] == ".git":
        raise RuntimeError(f"Ruta reservada en paquete Coder Web: {value}")
    return "/".join(parts)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def asset_from_image(index: int, image: bytes) -> CoderWebAsset:
    ext = "png" if image.startswith(b"\x89PNG") else "jpg" if image.startswith(b"\xff\xd8") else "bin"
    return CoderWebAsset(
        path=f"public/coder-web-assets/reference-{index}.{ext}",
        content_b64=base64.b64encode(image).decode("ascii"),
    )
