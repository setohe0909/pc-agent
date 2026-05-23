import httpx

from app.adapters.config.settings import Settings
from app.domain.models import ServiceState, ServiceStatus
from app.ports.gateways import SystemProbe


class HttpSystemProbe(SystemProbe):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def check(self) -> list[ServiceStatus]:
        checks = [
            ("control-api", "self"),
            ("assistant-runtime", f"{self.settings.effective('open_claw_base_url')}/health"),
            ("ingestion-worker", f"{self.settings.effective('ingestion_worker_base_url')}/health"),
            ("discord-bot", f"{self.settings.effective('discord_bot_base_url')}/health"),
        ]
        if self.settings.effective("mentis_enabled"):
            checks.append(("mentis", f"{self.settings.effective('mentis_base_url')}/health"))
        else:
            checks.append(("mentis", "disabled"))
        if self.settings.effective("langfuse_enabled"):
            checks.append(("langfuse", f"{self.settings.effective('langfuse_host')}/api/public/health"))
        else:
            checks.append(("langfuse", "disabled"))
        results: list[ServiceStatus] = []
        async with httpx.AsyncClient(timeout=3) as client:
            for name, url in checks:
                if url == "self":
                    results.append(ServiceStatus(name=name, state=ServiceState.healthy, detail="API activa"))
                    continue
                if url == "disabled":
                    results.append(ServiceStatus(name=name, state=ServiceState.unknown, detail="Integracion opcional desactivada"))
                    continue
                try:
                    response = await client.get(url)
                    state = ServiceState.healthy if response.status_code < 500 else ServiceState.degraded
                    results.append(ServiceStatus(name=name, state=state, detail=f"HTTP {response.status_code}"))
                except Exception as exc:
                    results.append(ServiceStatus(name=name, state=ServiceState.offline, detail=str(exc)))
        return results
