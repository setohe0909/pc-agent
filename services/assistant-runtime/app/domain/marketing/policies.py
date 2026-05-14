import os


SUPPORTED_AUTONOMY_LEVELS = {"assisted", "semi_auto", "auto"}


class AutonomyPolicy:
    def __init__(
        self,
        autonomy_level: str | None = None,
        automation_enabled: bool | None = None,
        allow_writes: bool | None = None,
    ):
        default_level = os.getenv("MARKETER_AUTONOMY_DEFAULT", "assisted")
        self.autonomy_level = self.normalize_level(autonomy_level or default_level)
        self.automation_enabled = self._env_bool("MARKETER_AUTOMATION_ENABLED", True) if automation_enabled is None else automation_enabled
        self.allow_writes = self._env_bool("MARKETER_ALLOW_WRITES", False) if allow_writes is None else allow_writes

    @classmethod
    def from_payload(cls, payload: dict | None) -> "AutonomyPolicy":
        payload = payload or {}
        return cls(autonomy_level=payload.get("autonomy_level"))

    @staticmethod
    def normalize_level(value: str | None) -> str:
        normalized = (value or "assisted").strip().lower().replace("-", "_")
        if normalized not in SUPPORTED_AUTONOMY_LEVELS:
            return "assisted"
        return normalized

    @staticmethod
    def _env_bool(key: str, default: bool) -> bool:
        raw = os.getenv(key)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    def can_execute_write(self, approved: bool = False) -> tuple[bool, str]:
        if not self.automation_enabled:
            return False, "La automatización de marketing está desactivada."
        if self.autonomy_level == "assisted" and not approved:
            return False, "Modo asistido: requiere aprobación humana antes de ejecutar."
        if not self.allow_writes:
            return False, "MARKETER_ALLOW_WRITES=false: el MVP solo genera borradores aprobables."
        if self.autonomy_level in {"semi_auto", "auto"} and not approved:
            return False, "Los modos semi_auto/auto están reservados y requieren aprobación explícita en este MVP."
        return True, "Ejecución permitida."

    def requires_approval_for_write(self) -> bool:
        return True
