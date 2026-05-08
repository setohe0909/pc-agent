import httpx

from app.ports.gateways import ConversationTracer


class LangfuseTracer(ConversationTracer):
    def __init__(self, host: str) -> None:
        self.host = host.rstrip("/")

    async def trace_event(self, name: str, payload: dict) -> None:
        # Placeholder until Langfuse auth/project keys are configured.
        async with httpx.AsyncClient(timeout=3) as client:
            await client.get(f"{self.host}/api/public/health")
