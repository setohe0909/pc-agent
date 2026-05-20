import json
import os
from datetime import date
from pathlib import Path

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
        raise NotImplementedError(
            "El adapter de proveedor real debe implementar list_sent_on con paginacion, scopes read-only y trazabilidad."
        )

    async def search_by_category(self, category: str, limit: int = 100) -> list[EmailMessage]:
        health = await self.check_health()
        if not health.configured:
            raise RuntimeError(health.detail)
        raise NotImplementedError(
            "El adapter de proveedor real debe implementar busqueda por categoria usando reglas guardadas y metadata."
        )

    async def send_bulk_replies(self, email_ids: list[str], template: EmailTemplate, dry_run: bool) -> dict:
        health = await self.check_health()
        if not health.configured:
            raise RuntimeError(health.detail)
        if not health.send_enabled:
            raise RuntimeError("Envio de email desactivado. Activalo en el administrador y usa aprobacion humana.")
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
