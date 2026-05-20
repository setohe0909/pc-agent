from datetime import date

from app.domain.ports.email import EmailConfigPort, EmailProviderPort
from app.domain.ports.llm import LLMPort


class EmailWorkflow:
    def __init__(self, email_provider: EmailProviderPort, email_config: EmailConfigPort, llm: LLMPort) -> None:
        self.email_provider = email_provider
        self.email_config = email_config
        self.llm = llm

    async def run(self, prompt: str, payload: dict) -> dict:
        sub_command = payload.get("sub_command", "status")
        if sub_command in {"status", "model-status"}:
            return await self._status()
        if sub_command == "sent-today":
            return await self._sent_today()
        if sub_command == "categorize":
            return await self._categorize(prompt, payload)
        if sub_command == "bulk-reply":
            return await self._bulk_reply(payload)
        return {
            "status": "error",
            "message": "Comando de email no reconocido. Usa `!email status`, `sent-today`, `categorize` o `--template-<nombre> <categoria>`.",
        }

    async def _status(self) -> dict:
        health = await self.email_provider.check_health()
        templates = self.email_config.list_templates()
        status = "success" if health.configured else "needs_configuration"
        return {
            "status": status,
            "message": (
                "**Email Agent - Status**\n"
                f"Proveedor: `{health.provider}`\n"
                f"Cuenta: `{health.account_id or 'sin cuenta'}`\n"
                f"Lectura: `{'activa' if health.read_enabled else 'pendiente'}`\n"
                f"Envio: `{'activo' if health.send_enabled else 'bloqueado'}`\n"
                f"Templates: `{len(templates)}`\n\n"
                f"{health.detail}"
            ),
            "email_status": {
                "provider": health.provider,
                "configured": health.configured,
                "read_enabled": health.read_enabled,
                "send_enabled": health.send_enabled,
                "templates": [template.name for template in templates],
            },
        }

    async def _sent_today(self) -> dict:
        try:
            messages = await self.email_provider.list_sent_on(date.today())
        except RuntimeError as exc:
            return {"status": "needs_configuration", "message": f"No puedo listar enviados todavia: {exc}"}
        except NotImplementedError as exc:
            return {
                "status": "adapter_required",
                "message": f"El proveedor esta configurado, pero falta conectar el adapter real de lectura: {exc}",
            }
        if not messages:
            return {"status": "success", "message": "No hay emails enviados hoy desde el proveedor configurado."}
        lines = ["**Emails enviados hoy**"]
        for item in messages[:50]:
            lines.append(f"- `{item.sent_at.isoformat()}` {item.subject} -> {', '.join(item.recipients)}")
        return {"status": "success", "message": "\n".join(lines)}

    async def _categorize(self, prompt: str, payload: dict) -> dict:
        category = payload.get("category") or prompt.strip() or "general"
        health = await self.email_provider.check_health()
        if not health.configured:
            return {
                "status": "needs_configuration",
                "message": f"No puedo categorizar todavía: {health.detail}",
            }
        return {
            "status": "accepted",
            "message": (
                f"Listo para categorizar emails como `{category}`. "
                "El adapter real debe aplicar filtros guardados, clasificacion asistida y auditoria antes de persistir etiquetas."
            ),
        }

    async def _bulk_reply(self, payload: dict) -> dict:
        template_name = payload.get("template_name")
        category = payload.get("category")
        if not template_name or not category:
            return {"status": "error", "message": "Usa `!email --template-<nombre> <categoria>`."}
        template = self.email_config.get_template(template_name)
        if template is None:
            return {
                "status": "error",
                "message": f"No existe el template `{template_name}`. Crealo primero en el administrador.",
            }
        try:
            matches = await self.email_provider.search_by_category(category, limit=int(payload.get("limit", 100)))
        except RuntimeError as exc:
            return {"status": "needs_configuration", "message": f"No puedo preparar bulk reply todavia: {exc}"}
        except NotImplementedError as exc:
            return {
                "status": "adapter_required",
                "message": f"El proveedor esta configurado, pero falta conectar el adapter real de categorizacion/envio: {exc}",
            }
        email_ids = [message.id for message in matches]
        dry_run = not bool(payload.get("is_approved", False))
        try:
            result = await self.email_provider.send_bulk_replies(email_ids, template, dry_run=dry_run)
        except RuntimeError as exc:
            return {"status": "needs_configuration", "message": f"No puedo encolar respuestas todavia: {exc}"}
        except NotImplementedError as exc:
            return {
                "status": "adapter_required",
                "message": f"El proveedor esta configurado, pero falta conectar el adapter real de envio: {exc}",
            }
        return {
            "status": "requires_approval" if dry_run else "accepted",
            "requires_approval": dry_run,
            "message": (
                f"Bulk reply preparado con template `{template.name}` para categoria `{category}`.\n"
                f"Coincidencias: `{len(email_ids)}`\n"
                f"Modo: `{'revision/aprobacion' if dry_run else 'cola de envio'}`\n"
                "Los envios masivos deben respetar rate limits, opt-out, idempotencia y auditoria por proveedor."
            ),
            "email_bulk_reply": result,
        }
