import httpx

from app.domain.models import MentisVerification
from app.ports.gateways import MentisMemory


class MentisHttpMemory(MentisMemory):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def verify(self) -> MentisVerification:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 404:
                    response = await client.get(self.base_url)
            reachable = response.status_code < 500
            return MentisVerification(
                reachable=reachable,
                can_read=False,
                can_write=False,
                detail=(
                    f"MentisDB respondio HTTP {response.status_code}. "
                    "Falta configurar prueba MCP real de lectura/escritura."
                ),
            )
        except Exception as exc:
            return MentisVerification(
                reachable=False,
                can_read=False,
                can_write=False,
                detail=str(exc),
            )
