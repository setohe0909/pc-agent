from datetime import date
from uuid import uuid4

from app.domain.email.models import EmailAuditEvent, EmailBulkJob, EmailBulkJobStatus, EmailBulkRecipient
from app.domain.ports.email import EmailConfigPort, EmailJobRepositoryPort, EmailProviderPort
from app.domain.ports.llm import LLMPort


class EmailWorkflow:
    def __init__(
        self,
        email_provider: EmailProviderPort,
        email_config: EmailConfigPort,
        email_jobs: EmailJobRepositoryPort,
        llm: LLMPort,
    ) -> None:
        self.email_provider = email_provider
        self.email_config = email_config
        self.email_jobs = email_jobs
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
        if sub_command == "deny-bulk-reply":
            return await self._deny_bulk_reply(payload)
        if sub_command == "process-queued":
            return await self._process_queued(payload)
        return {
            "status": "error",
            "message": "Comando de email no reconocido. Usa `!email status`, `sent-today`, `categorize` o `--template-<nombre> <categoria>`.",
        }

    async def _status(self) -> dict:
        health = await self.email_provider.check_health()
        templates = self.email_config.list_templates()
        categories = self.email_config.list_categories()
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
                f"Categorias: `{len(categories)}`\n\n"
                f"{health.detail}"
            ),
            "email_status": {
                "provider": health.provider,
                "configured": health.configured,
                "read_enabled": health.read_enabled,
                "send_enabled": health.send_enabled,
                "templates": [template.name for template in templates],
                "categories": [category.name for category in categories],
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
        if payload.get("job_id") and payload.get("is_approved"):
            return await self._approve_bulk_reply(payload)

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
        health = await self.email_provider.check_health()
        recipients = [
            EmailBulkRecipient(
                email_id=message.id,
                recipient=message.sender,
                subject=message.subject,
                metadata={"sender": message.sender, "sent_at": message.sent_at.isoformat(), "labels": message.labels},
            )
            for message in matches
        ]
        email_ids = [recipient.email_id for recipient in recipients]
        try:
            dry_run_result = await self.email_provider.send_bulk_replies(email_ids, template, dry_run=True)
        except RuntimeError as exc:
            return {"status": "needs_configuration", "message": f"No puedo encolar respuestas todavia: {exc}"}
        except NotImplementedError as exc:
            return {
                "status": "adapter_required",
                "message": f"El proveedor esta configurado, pero falta conectar el adapter real de envio: {exc}",
            }
        job = EmailBulkJob(
            id=str(uuid4()),
            provider=health.provider,
            account_id=health.account_id,
            template=template,
            category=category,
            status=EmailBulkJobStatus.requires_approval,
            requested_by=payload.get("requested_by") or payload.get("user_id"),
            recipients=recipients,
            provider_result=dry_run_result,
            metadata={"source": payload.get("source"), "limit": payload.get("limit", 100)},
        )
        await self.email_jobs.create_bulk_job(job)
        await self.email_jobs.append_audit(
            EmailAuditEvent(
                event_type="email_bulk_job_prepared",
                actor_id=job.requested_by,
                detail=f"Bulk reply preparado para categoria `{category}` con template `{template.name}`.",
                job_id=job.id,
                metadata={"recipient_count": job.recipient_count, "provider": job.provider},
            )
        )
        return {
            "status": "requires_approval",
            "requires_approval": True,
            "message": (
                f"Bulk reply preparado con template `{template.name}` para categoria `{category}`.\n"
                f"Job: `{job.id}`\n"
                f"Coincidencias: `{len(email_ids)}`\n"
                "Modo: `revision/aprobacion`\n"
                "Los envios no saldran hasta que un aprobador confirme el job."
            ),
            "email_bulk_reply": _bulk_job_payload(job, dry_run_result),
        }

    async def _approve_bulk_reply(self, payload: dict) -> dict:
        job_id = str(payload.get("job_id") or "")
        approved_by = payload.get("approved_by") or payload.get("user_id")
        try:
            approved_job = await self.email_jobs.approve_bulk_job(job_id, approved_by)
            queued_job = await self.email_jobs.mark_bulk_job_queued(
                job_id,
                {"status": "queued", "reason": "approved_pending_email_worker"},
            )
            await self.email_jobs.append_audit(
                EmailAuditEvent(
                    event_type="email_bulk_job_approved",
                    actor_id=approved_by,
                    detail="Bulk reply aprobado y encolado para procesamiento durable.",
                    job_id=job_id,
                    metadata={"recipient_count": approved_job.recipient_count},
                )
            )
        except RuntimeError as exc:
            return {"status": "error", "message": f"No pude aprobar el bulk reply: {exc}"}
        except NotImplementedError as exc:
            return {"status": "adapter_required", "message": f"Falta adapter real de envio: {exc}"}
        return {
            "status": "accepted",
            "requires_approval": False,
            "message": (
                f"Bulk reply `{job_id}` aprobado y encolado.\n"
                f"Destinatarios: `{queued_job.recipient_count}`\n"
                "Un worker debe procesar la cola con idempotencia por destinatario."
            ),
            "email_bulk_reply": _bulk_job_payload(queued_job, queued_job.provider_result),
        }

    async def _deny_bulk_reply(self, payload: dict) -> dict:
        job_id = str(payload.get("job_id") or "")
        rejected_by = payload.get("rejected_by") or payload.get("user_id")
        reason = str(payload.get("reason") or "Denegado desde Discord")
        try:
            job = await self.email_jobs.reject_bulk_job(job_id, rejected_by, reason)
            await self.email_jobs.append_audit(
                EmailAuditEvent(
                    event_type="email_bulk_job_denied",
                    actor_id=rejected_by,
                    detail=reason,
                    job_id=job_id,
                    metadata={"provider": job.provider},
                )
            )
        except RuntimeError as exc:
            return {"status": "error", "message": f"No pude denegar el bulk reply: {exc}"}
        return {
            "status": "cancelled",
            "requires_approval": False,
            "message": f"Bulk reply `{job_id}` denegado. No se envio ningun email.",
            "email_bulk_reply": _bulk_job_payload(job, job.provider_result),
        }

    async def _process_queued(self, payload: dict) -> dict:
        limit = int(payload.get("limit", 10))
        actor_id = payload.get("requested_by") or payload.get("user_id") or "email-worker"
        try:
            jobs = await self.email_jobs.list_bulk_jobs([EmailBulkJobStatus.queued.value], limit=limit)
        except RuntimeError as exc:
            return {"status": "error", "message": f"No pude listar jobs de email en cola: {exc}"}

        processed = []
        for job in jobs:
            pending = [recipient for recipient in job.recipients if recipient.status in {"pending", "failed"}]
            if not pending:
                done = await self.email_jobs.mark_bulk_job_status(job.id, EmailBulkJobStatus.sent.value, job.provider_result)
                processed.append(_bulk_job_payload(done, done.provider_result))
                continue
            try:
                await self.email_jobs.mark_bulk_job_status(job.id, EmailBulkJobStatus.sending.value, job.provider_result)
                result = await self.email_provider.send_bulk_replies(
                    [recipient.email_id for recipient in pending],
                    job.template,
                    dry_run=False,
                )
                await self._apply_recipient_results(job.id, pending, result)
                final_status = EmailBulkJobStatus.sent.value if _provider_result_sent(result) else EmailBulkJobStatus.queued.value
                updated = await self.email_jobs.mark_bulk_job_status(job.id, final_status, result)
                await self.email_jobs.append_audit(
                    EmailAuditEvent(
                        event_type="email_bulk_job_processed",
                        actor_id=actor_id,
                        detail=f"Job `{job.id}` procesado por worker.",
                        job_id=job.id,
                        metadata={"provider_result": result, "recipient_count": len(pending)},
                    )
                )
                processed.append(_bulk_job_payload(updated, result))
            except (RuntimeError, NotImplementedError) as exc:
                failed = await self.email_jobs.mark_bulk_job_status(
                    job.id,
                    EmailBulkJobStatus.failed.value,
                    {"status": "failed", "error": str(exc)},
                )
                await self.email_jobs.append_audit(
                    EmailAuditEvent(
                        event_type="email_bulk_job_failed",
                        actor_id=actor_id,
                        detail=str(exc),
                        job_id=job.id,
                        metadata={"recipient_count": len(pending)},
                    )
                )
                processed.append(_bulk_job_payload(failed, failed.provider_result))

        return {
            "status": "success",
            "message": f"Jobs de email procesados: `{len(processed)}`.",
            "email_jobs": processed,
        }

    async def _apply_recipient_results(self, job_id: str, recipients: list[EmailBulkRecipient], result: dict) -> None:
        result_rows = result.get("recipients") or result.get("results") or []
        by_email_id = {
            str(item.get("email_id") or item.get("id")): item
            for item in result_rows
            if isinstance(item, dict)
        }
        fallback_status = "sent" if _provider_result_sent(result) else "queued"
        for recipient in recipients:
            row = by_email_id.get(recipient.email_id, {})
            status = str(row.get("status") or fallback_status)
            if status not in {"queued", "sending", "sent", "failed", "skipped"}:
                status = fallback_status
            await self.email_jobs.update_recipient_status(
                job_id=job_id,
                email_id=recipient.email_id,
                status=status,
                provider_message_id=row.get("provider_message_id") or row.get("message_id"),
                error_detail=row.get("error") or row.get("error_detail"),
            )


def _bulk_job_payload(job: EmailBulkJob, provider_result: dict) -> dict:
    return {
        "job_id": job.id,
        "provider": job.provider,
        "account_id": job.account_id,
        "template": job.template.name,
        "category": job.category,
        "status": job.status.value,
        "recipient_count": job.recipient_count,
        "recipients_preview": [
            {"email_id": item.email_id, "recipient": item.recipient, "subject": item.subject}
            for item in job.recipients[:10]
        ],
        "provider_result": provider_result,
    }


def _provider_result_sent(result: dict) -> bool:
    return str(result.get("status") or "").lower() in {"sent", "delivered", "completed", "success"}
