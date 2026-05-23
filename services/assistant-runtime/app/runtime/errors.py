import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeErrorEnvelope:
    status: str
    code: str
    message: str
    error_type: str
    stage: str
    hint: str
    trace_id: str
    retryable: bool = False
    detail: str | None = None

    def to_dict(self) -> dict:
        payload = {
            "status": self.status,
            "code": self.code,
            "message": self.message,
            "error_type": self.error_type,
            "error_stage": self.stage,
            "hint": self.hint,
            "trace_id": self.trace_id,
            "retryable": self.retryable,
        }
        if self.detail is not None:
            payload["error_detail"] = self.detail
        return payload


def error_envelope(exc: Exception, action_type: str, sub_command: str, stage: str, trace_id: str) -> RuntimeErrorEnvelope:
    raw_detail = str(exc) or repr(exc)
    error_type = type(exc).__name__
    retryable = False
    code = "runtime_error"
    hint = "Revisa los logs del assistant-runtime usando el trace_id."

    if isinstance(exc, KeyError):
        code = "missing_expected_value"
        missing = str(exc).strip("'\"")
        raw_detail = f"Clave o valor esperado no encontrado: {missing}"
        if missing in {"object", "type", "properties"}:
            hint = "El problema parece estar en el schema de herramientas del LLM antes de ejecutar la acción."
        else:
            hint = f"El flujo intentó leer `{missing}` en una respuesta o payload que no lo tenía."
    elif "429" in raw_detail or "quota" in raw_detail.lower() or "rate limit" in raw_detail.lower():
        code = "provider_rate_limited"
        retryable = True
        hint = "El proveedor devolvió límite de cuota o rate limit. Reintenta más tarde o cambia proveedor."
    elif "timeout" in raw_detail.lower():
        code = "dependency_timeout"
        retryable = True
        hint = "Una dependencia tardó demasiado. Reintenta o revisa conectividad."
    elif "nodename nor servname" in raw_detail or "Name or service not known" in raw_detail:
        code = "dependency_unreachable"
        retryable = True
        hint = "El runtime no pudo resolver o conectar una dependencia externa."
    elif "schema JSON incompatible" in raw_detail or "detección de herramientas" in raw_detail:
        code = "tool_schema_error"
        hint = "El problema está en el schema de herramientas del LLM antes de ejecutar la acción."
    elif "ZERNIO" in raw_detail.upper() or "zernio" in raw_detail.lower():
        code = "zernio_adapter_error"
        hint = "El problema parece venir de la integración Zernio o su respuesta."

    expose_details = os.getenv("EXPOSE_ERROR_DETAILS", "false").lower() == "true"
    public_detail = raw_detail if expose_details else "Detalle tecnico retenido por seguridad."
    message = (
        f"No pude completar `{action_type}` con subcomando `{sub_command}` durante `{stage}`.\n"
        f"Código: `{code}`\n"
        f"Tipo: `{error_type}`\n"
        f"Detalle: {public_detail}\n"
        f"Trace: `{trace_id}`\n"
        f"Pista: {hint}"
    )

    return RuntimeErrorEnvelope(
        status="error",
        code=code,
        message=message,
        error_type=error_type,
        stage=stage,
        hint=hint,
        trace_id=trace_id,
        retryable=retryable,
        detail=raw_detail if expose_details else None,
    )
