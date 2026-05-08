from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class KnowledgeSource:
    id: str
    name: str
    source_type: str
    url: str | None
    schedule: str | None
    enabled: bool


@dataclass(frozen=True)
class KnowledgeDocument:
    source_id: str
    title: str
    content: str
    metadata: dict
    content_hash: str
    embedding: list[float]
    embedding_provider: str = "ollama"
    embedding_model: str = "mxbai-embed-large"


class SupabaseKnowledgeStore:
    def __init__(self, url: str, publishable_key: str, service_role_key: str | None) -> None:
        self.url = url.rstrip("/")
        self.publishable_key = publishable_key
        self.service_role_key = service_role_key

    async def list_enabled_sources(self, limit: int) -> list[KnowledgeSource]:
        headers = self._headers(service_role=False)
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.url}/rest/v1/knowledge_sources",
                headers=headers,
                params={
                    "select": "id,name,source_type,url,schedule,enabled",
                    "enabled": "eq.true",
                    "limit": str(limit),
                    "order": "created_at.desc",
                },
            )
        response.raise_for_status()
        return [
            KnowledgeSource(
                id=row["id"],
                name=row["name"],
                source_type=row["source_type"],
                url=row.get("url"),
                schedule=row.get("schedule"),
                enabled=row.get("enabled", True),
            )
            for row in response.json()
        ]

    async def upsert_documents(self, documents: list[KnowledgeDocument]) -> int:
        if not documents:
            return 0
        if not self.service_role_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY es requerido para guardar embeddings.")

        payload = [
            {
                "source_id": document.source_id,
                "title": document.title,
                "content": document.content,
                "metadata": document.metadata,
                "content_hash": document.content_hash,
                "embedding": _format_vector(document.embedding),
                "embedding_provider": document.embedding_provider,
                "embedding_model": document.embedding_model,
            }
            for document in documents
        ]
        headers = self._headers(service_role=True)
        headers["Prefer"] = "resolution=merge-duplicates"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.url}/rest/v1/knowledge_documents",
                headers=headers,
                params={"on_conflict": "content_hash"},
                json=payload,
            )
        response.raise_for_status()
        return len(documents)

    def _headers(self, service_role: bool) -> dict[str, str]:
        key = self.service_role_key if service_role else self.publishable_key
        return {
            "apikey": key or self.publishable_key,
            "Authorization": f"Bearer {key or self.publishable_key}",
            "Content-Type": "application/json",
        }


def _format_vector(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
