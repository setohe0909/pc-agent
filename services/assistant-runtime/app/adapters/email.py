import json
import os
from datetime import date
from pathlib import Path

import httpx

from app.domain.email.models import EmailMessage, EmailProviderHealth, EmailTemplate
from app.domain.ports.email import EmailConfigPort, EmailProviderPort


class RuntimeEmailConfig(EmailConfigPort):
    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = Path(config_path or os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json"))

    def read(self) -> dict:
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def default_provider(self) -> str:
        return str(self.read().get("email_provider") or os.getenv("EMAIL_PROVIDER") or "not_configured")

    def get_template(self, name: str) -> EmailTemplate | None:
        normalized = name.strip().lower()
        for template in self.list_templates():
            if template.name.lower() == normalized:
                return template
        return None

    def list_templates(self) -> list[EmailTemplate]:
        templates = self.read().get("email_templates") or []
        if isinstance(templates, str):
            try:
                templates = json.loads(templates)
            except json.JSONDecodeError:
                templates = []
        return [_template_from_dict(item) for item in templates if isinstance(item, dict)]


class ConfiguredEmailProvider(EmailProviderPort):
    def __init__(self, config: RuntimeEmailConfig) -> None:
        self.config = config

    async def check_health(self) -> EmailProviderHealth:
        runtime = self.config.read()
        provider = self.config.default_provider()
        configured = _provider_configured(provider, runtime)
        send_enabled = bool(runtime.get("email_send_enabled", False))
        account_id = runtime.get("email_account_id")
        if provider == "not_configured":
            detail = "Selecciona y configura un proveedor de email en el administrador."
        elif configured:
            detail = (
                "Proveedor configurado. Las operaciones de lectura/envio deben ejecutarse mediante "
                "el adapter dedicado del proveedor con OAuth/token refresh, auditoria y rate limits."
            )
        else:
            detail = f"Proveedor {provider} seleccionado, pero faltan credenciales requeridas."
        return EmailProviderHealth(
            provider=provider,
            configured=configured,
            read_enabled=configured,
            send_enabled=configured and send_enabled,
            detail=detail,
            account_id=account_id,
        )

    async def list_sent_on(self, day: date) -> list[EmailMessage]:
        health = await self.check_health()
        if not health.configured:
            raise RuntimeError(health.detail)
        runtime = self.config.read()
        if health.provider == "pc_client":
            rows = await _pc_client_get(runtime, "/sent", params={"date": day.isoformat()})
            return [_message_from_dict(row, health.provider, health.account_id) for row in rows]
        raise NotImplementedError(
            "El adapter de proveedor real debe implementar list_sent_on con paginacion, scopes read-only y trazabilidad."
        )

    async def search_by_category(self, category: str, limit: int = 100) -> list[EmailMessage]:
        health = await self.check_health()
        if not health.configured:
            raise RuntimeError(health.detail)
        runtime = self.config.read()
        if health.provider == "pc_client":
            rows = await _pc_client_get(runtime, "/search", params={"category": category, "limit": str(limit)})
            return [_message_from_dict(row, health.provider, health.account_id) for row in rows]
        raise NotImplementedError(
            "El adapter de proveedor real debe implementar busqueda por categoria usando reglas guardadas y metadata."
        )

    async def send_bulk_replies(self, email_ids: list[str], template: EmailTemplate, dry_run: bool) -> dict:
        health = await self.check_health()
        if not health.configured:
            raise RuntimeError(health.detail)
        if not health.send_enabled:
            raise RuntimeError("Envio de email desactivado. Activalo en el administrador y usa aprobacion humana.")
        runtime = self.config.read()
        if health.provider == "pc_client":
            return await _pc_client_post(
                runtime,
                "/bulk-replies",
                {
                    "email_ids": email_ids,
                    "template": {
                        "name": template.name,
                        "subject": template.subject,
                        "body": template.body,
                        "category": template.category,
                        "requires_approval": template.requires_approval,
                        "rate_limit_per_minute": template.rate_limit_per_minute,
                    },
                    "dry_run": dry_run,
                },
            )
        return {
            "status": "planned" if dry_run else "queued",
            "email_ids": email_ids,
            "template": template.name,
            "dry_run": dry_run,
        }


def _provider_configured(provider: str, runtime: dict) -> bool:
    if provider == "google":
        return bool(runtime.get("email_google_client_id") and runtime.get("email_google_client_secret"))
    if provider == "outlook":
        return bool(runtime.get("email_outlook_client_id") and runtime.get("email_outlook_client_secret") and runtime.get("email_outlook_tenant_id"))
    if provider == "imap_smtp":
        return bool(runtime.get("email_imap_host") and runtime.get("email_smtp_host") and runtime.get("email_username") and runtime.get("email_password"))
    if provider == "pc_client":
        return bool(runtime.get("email_pc_client_bridge_url"))
    return False


def _template_from_dict(data: dict) -> EmailTemplate:
    return EmailTemplate(
        name=str(data.get("name", "")).strip(),
        subject=str(data.get("subject", "")).strip(),
        body=str(data.get("body", "")).strip(),
        category=data.get("category"),
        requires_approval=bool(data.get("requires_approval", True)),
        rate_limit_per_minute=int(data.get("rate_limit_per_minute") or 30),
    )


async def _pc_client_get(runtime: dict, path: str, params: dict[str, str]) -> list[dict]:
    base_url = str(runtime.get("email_pc_client_bridge_url", "")).rstrip("/")
    headers = _pc_client_headers(runtime)
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{base_url}{path}", headers=headers, params=params)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Bridge local de email no disponible o respondio error: {exc}") from exc
    data = response.json()
    if isinstance(data, dict):
        return data.get("emails") or data.get("messages") or []
    return data if isinstance(data, list) else []


async def _pc_client_post(runtime: dict, path: str, payload: dict) -> dict:
    base_url = str(runtime.get("email_pc_client_bridge_url", "")).rstrip("/")
    headers = _pc_client_headers(runtime)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{base_url}{path}", headers=headers, json=payload)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Bridge local de email no disponible o respondio error: {exc}") from exc
    data = response.json()
    return data if isinstance(data, dict) else {"status": "accepted", "result": data}


def _pc_client_headers(runtime: dict) -> dict[str, str]:
    token = runtime.get("email_pc_client_bridge_token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _message_from_dict(row: dict, provider: str, account_id: str | None) -> EmailMessage:
    sent_at = row.get("sent_at") or row.get("date") or row.get("created_at")
    return EmailMessage(
        id=str(row.get("id") or row.get("message_id")),
        provider=str(row.get("provider") or provider),
        account_id=str(row.get("account_id") or account_id or ""),
        subject=str(row.get("subject") or ""),
        sender=str(row.get("sender") or row.get("from") or ""),
        recipients=_as_list(row.get("recipients") or row.get("to")),
        sent_at=_parse_datetime(sent_at),
        snippet=str(row.get("snippet") or ""),
        labels=_as_list(row.get("labels")),
        metadata=dict(row.get("metadata") or {}),
    )


def _parse_datetime(value: str | None):
    from datetime import datetime, timezone

    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]
