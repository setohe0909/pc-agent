import httpx

from app.domain.models import KnowledgeSource, SourceType, SupabaseVerification
from app.ports.gateways import KnowledgeSourceRepository, VectorKnowledgeBase


class SupabaseVectorKnowledgeBase(VectorKnowledgeBase, KnowledgeSourceRepository):
    def __init__(
        self,
        url: str,
        publishable_key: str,
        service_role_key: str | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.publishable_key = publishable_key
        self.service_role_key = service_role_key

    async def verify(self) -> SupabaseVerification:
        has_publishable_key = bool(self.publishable_key)
        has_service_role_key = bool(self.service_role_key)
        if not self.url or not has_publishable_key:
            return SupabaseVerification(
                reachable=False,
                rest_available=False,
                knowledge_schema_ready=False,
                has_publishable_key=has_publishable_key,
                has_service_role_key=has_service_role_key,
                detail="Falta SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY",
            )

        headers = {
            "apikey": self.publishable_key,
            "Authorization": f"Bearer {self.publishable_key}",
        }
        endpoint = f"{self.url}/rest/v1/knowledge_sources"
        try:
            async with httpx.AsyncClient(timeout=6) as client:
                response = await client.get(endpoint, headers=headers, params={"select": "id", "limit": "1"})
            schema_ready = response.status_code < 400
            rest_available = response.status_code != 404
            return SupabaseVerification(
                reachable=True,
                rest_available=rest_available,
                knowledge_schema_ready=schema_ready,
                has_publishable_key=has_publishable_key,
                has_service_role_key=has_service_role_key,
                detail=f"Supabase REST respondio HTTP {response.status_code}",
            )
        except Exception as exc:
            return SupabaseVerification(
                reachable=False,
                rest_available=False,
                knowledge_schema_ready=False,
                has_publishable_key=has_publishable_key,
                has_service_role_key=has_service_role_key,
                detail=str(exc),
            )

    async def list_sources(self) -> list[KnowledgeSource]:
        headers = self._headers(use_service_role=False)
        endpoint = f"{self.url}/rest/v1/knowledge_sources"
        async with httpx.AsyncClient(timeout=6) as client:
            response = await client.get(
                endpoint,
                headers=headers,
                params={"select": "id,name,source_type,url,schedule,enabled", "order": "created_at.desc"},
            )
        response.raise_for_status()
        return [self._source_from_row(row) for row in response.json()]

    async def add_source(self, source: KnowledgeSource) -> KnowledgeSource:
        if not self.service_role_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY es requerido para crear fuentes persistentes.")
        headers = self._headers(use_service_role=True)
        headers["Prefer"] = "return=representation"
        endpoint = f"{self.url}/rest/v1/knowledge_sources"
        payload = {
            "name": source.name,
            "source_type": source.source_type.value,
            "url": source.url,
            "schedule": source.schedule,
            "enabled": source.enabled,
        }
        async with httpx.AsyncClient(timeout=6) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        rows = response.json()
        return self._source_from_row(rows[0])

    def _headers(self, use_service_role: bool) -> dict[str, str]:
        key = self.service_role_key if use_service_role else self.publishable_key
        return {
            "apikey": key or self.publishable_key,
            "Authorization": f"Bearer {key or self.publishable_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _source_from_row(row: dict) -> KnowledgeSource:
        return KnowledgeSource(
            id=row["id"],
            name=row["name"],
            source_type=SourceType(row["source_type"]),
            url=row.get("url"),
            schedule=row.get("schedule"),
            enabled=row.get("enabled", True),
        )
