import json
import os
import asyncio
import email
import imaplib
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage as SmtpEmailMessage
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

import httpx

from app.domain.email.models import EmailCategory, EmailMessage, EmailProviderHealth, EmailTemplate
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

    def list_categories(self) -> list[EmailCategory]:
        categories = self.read().get("email_categories") or []
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError:
                categories = []
        return [_category_from_dict(item) for item in categories if isinstance(item, dict)]


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
        if health.provider == "imap_smtp":
            return await asyncio.to_thread(_imap_list_sent_on, runtime, day, health.account_id)
        raise NotImplementedError("Este proveedor requiere adapter OAuth dedicado. Usa pc_client o imap_smtp en produccion.")

    async def search_by_category(self, category: str, limit: int = 100) -> list[EmailMessage]:
        health = await self.check_health()
        if not health.configured:
            raise RuntimeError(health.detail)
        runtime = self.config.read()
        if health.provider == "pc_client":
            rows = await _pc_client_get(runtime, "/search", params={"category": category, "limit": str(limit)})
            return [_message_from_dict(row, health.provider, health.account_id) for row in rows]
        if health.provider == "imap_smtp":
            categories = {item.name.lower(): item for item in self.config.list_categories()}
            email_category = categories.get(category.strip().lower())
            return await asyncio.to_thread(_imap_search_by_category, runtime, category, email_category, limit, health.account_id)
        raise NotImplementedError("Este proveedor requiere adapter OAuth dedicado. Usa pc_client o imap_smtp en produccion.")

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
        if health.provider == "imap_smtp":
            return await asyncio.to_thread(_smtp_send_bulk_replies, runtime, email_ids, template, dry_run)
        raise NotImplementedError(f"El proveedor {health.provider} requiere adapter OAuth dedicado. Usa pc_client o imap_smtp en produccion.")


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


def _category_from_dict(data: dict) -> EmailCategory:
    threshold = data.get("confidence_threshold", 0.7)
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        threshold = 0.7
    return EmailCategory(
        name=str(data.get("name", "")).strip(),
        description=str(data.get("description", "")).strip(),
        filters=dict(data.get("filters") or {}),
        confidence_threshold=threshold,
    )


def _imap_list_sent_on(runtime: dict, day: date, account_id: str | None) -> list[EmailMessage]:
    mailbox = str(runtime.get("email_imap_sent_mailbox") or "Sent")
    next_day = day.toordinal() + 1
    criteria = f'(SINCE "{_imap_date(day)}" BEFORE "{_imap_date(date.fromordinal(next_day))}")'
    return _imap_search(runtime, mailbox, criteria, int(runtime.get("email_imap_max_results") or 50), account_id)


def _imap_search_by_category(
    runtime: dict,
    category: str,
    email_category: EmailCategory | None,
    limit: int,
    account_id: str | None,
) -> list[EmailMessage]:
    mailbox = str(runtime.get("email_imap_inbox_mailbox") or "INBOX")
    filters = email_category.filters if email_category else {}
    query = str(filters.get("query") or filters.get("text") or category).strip()
    subject = str(filters.get("subject") or "").strip()
    sender = str(filters.get("from") or filters.get("sender") or "").strip()
    if subject:
        criteria = f'(SUBJECT "{_imap_escape(subject)}")'
    elif sender:
        criteria = f'(FROM "{_imap_escape(sender)}")'
    elif query:
        criteria = f'(TEXT "{_imap_escape(query)}")'
    else:
        criteria = "ALL"
    return _imap_search(runtime, mailbox, criteria, limit, account_id)


def _imap_search(runtime: dict, mailbox: str, criteria: str, limit: int, account_id: str | None) -> list[EmailMessage]:
    messages: list[EmailMessage] = []
    with _imap_connection(runtime) as conn:
        status, _ = conn.select(mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"No pude abrir mailbox IMAP `{mailbox}`.")
        status, data = conn.uid("SEARCH", None, criteria)
        if status != "OK":
            raise RuntimeError(f"Busqueda IMAP fallo para criterio `{criteria}`.")
        uids = (data[0] or b"").split()
        for uid in list(reversed(uids))[: max(1, min(limit, 200))]:
            message = _imap_fetch_message(conn, uid, account_id)
            if message:
                messages.append(message)
    return messages


def _smtp_send_bulk_replies(runtime: dict, email_ids: list[str], template: EmailTemplate, dry_run: bool) -> dict:
    if not email_ids:
        return {"status": "success", "dry_run": dry_run, "recipients": []}
    account_id = str(runtime.get("email_account_id") or runtime.get("email_username") or "")
    originals: list[EmailMessage] = []
    with _imap_connection(runtime) as conn:
        mailbox = str(runtime.get("email_imap_inbox_mailbox") or "INBOX")
        status, _ = conn.select(mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"No pude abrir mailbox IMAP `{mailbox}` para responder.")
        for raw_uid in email_ids:
            message = _imap_fetch_message(conn, str(raw_uid).encode("utf-8"), account_id)
            if message:
                originals.append(message)
    planned = [
        {
            "email_id": message.id,
            "recipient": message.sender,
            "subject": _reply_subject(template.subject, message.subject),
            "status": "planned" if dry_run else "pending",
        }
        for message in originals
        if message.sender
    ]
    if dry_run:
        return {"status": "success", "dry_run": True, "recipient_count": len(planned), "recipients": planned}

    sent = []
    failures = []
    with _smtp_connection(runtime) as smtp:
        for message in originals:
            if not message.sender:
                failures.append({"email_id": message.id, "status": "failed", "error": "Original sin sender."})
                continue
            outgoing = SmtpEmailMessage()
            outgoing["From"] = account_id
            outgoing["To"] = message.sender
            outgoing["Subject"] = _reply_subject(template.subject, message.subject)
            if message.metadata.get("message_id"):
                outgoing["In-Reply-To"] = str(message.metadata["message_id"])
                outgoing["References"] = str(message.metadata["message_id"])
            outgoing.set_content(_render_template(template.body, message, account_id))
            try:
                smtp.send_message(outgoing)
                sent.append({"email_id": message.id, "recipient": message.sender, "status": "sent"})
            except Exception as exc:
                failures.append({"email_id": message.id, "recipient": message.sender, "status": "failed", "error": str(exc)})
    status = "sent" if sent and not failures else "failed" if failures and not sent else "partial"
    return {"status": status, "dry_run": False, "sent": len(sent), "failed": len(failures), "recipients": sent + failures}


def _imap_connection(runtime: dict):
    host, port = _split_host_port(str(runtime.get("email_imap_host") or ""), 993)
    username = str(runtime.get("email_username") or "")
    password = str(runtime.get("email_password") or "")
    if not host or not username or not password:
        raise RuntimeError("IMAP requiere host, usuario y password.")
    conn = imaplib.IMAP4_SSL(host, port, ssl_context=ssl.create_default_context())
    conn.login(username, password)
    return conn


def _smtp_connection(runtime: dict):
    host, port = _split_host_port(str(runtime.get("email_smtp_host") or ""), 587)
    username = str(runtime.get("email_username") or "")
    password = str(runtime.get("email_password") or "")
    if not host or not username or not password:
        raise RuntimeError("SMTP requiere host, usuario y password.")
    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=20)
    else:
        smtp = smtplib.SMTP(host, port, timeout=20)
        if str(runtime.get("email_smtp_starttls", "true")).lower() in {"1", "true", "yes", "on"}:
            smtp.starttls(context=ssl.create_default_context())
    smtp.login(username, password)
    return smtp


def _imap_fetch_message(conn, uid: bytes, account_id: str | None) -> EmailMessage | None:
    status, data = conn.uid("FETCH", uid, "(RFC822)")
    if status != "OK" or not data:
        return None
    raw = next((item[1] for item in data if isinstance(item, tuple) and len(item) > 1), None)
    if not raw:
        return None
    parsed = email.message_from_bytes(raw)
    sender = _first_address(parsed.get("From"))
    recipients = [addr for _, addr in getaddresses(parsed.get_all("To", []))]
    sent_at = _email_date(parsed.get("Date"))
    snippet = _message_snippet(parsed)
    labels = []
    return EmailMessage(
        id=uid.decode("utf-8"),
        provider="imap_smtp",
        account_id=str(account_id or ""),
        subject=str(parsed.get("Subject") or ""),
        sender=sender,
        recipients=recipients,
        sent_at=sent_at,
        snippet=snippet,
        labels=labels,
        metadata={"message_id": parsed.get("Message-ID")},
    )


def _message_snippet(parsed) -> str:
    body = ""
    if parsed.is_multipart():
        for part in parsed.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                try:
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
                except Exception:
                    continue
    else:
        try:
            body = parsed.get_payload(decode=True).decode(parsed.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            body = str(parsed.get_payload() or "")
    return " ".join(body.split())[:300]


def _render_template(template_body: str, message: EmailMessage, account_id: str) -> str:
    values = {
        "subject": message.subject,
        "sender": message.sender,
        "snippet": message.snippet,
        "account_id": account_id,
    }
    rendered = template_body
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def _reply_subject(template_subject: str, original_subject: str) -> str:
    subject = template_subject.replace("{{subject}}", original_subject)
    return subject if subject.lower().startswith("re:") else f"Re: {subject}"


def _split_host_port(value: str, default_port: int) -> tuple[str, int]:
    if ":" in value and not value.startswith("["):
        host, port = value.rsplit(":", 1)
        try:
            return host, int(port)
        except ValueError:
            return value, default_port
    return value, default_port


def _imap_date(value: date) -> str:
    return value.strftime("%d-%b-%Y")


def _imap_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _first_address(value: str | None) -> str:
    addresses = getaddresses([value or ""])
    return addresses[0][1] if addresses else ""


def _email_date(value: str | None):
    from datetime import datetime, timezone

    if not value:
        return datetime.now(timezone.utc)
    try:
        return parsedate_to_datetime(value)
    except Exception:
        return datetime.now(timezone.utc)


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
