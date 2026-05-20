import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.domain.models import ConsolidationRecord, MemoryFragment, MentisVerification
from app.ports.gateways import MemoryRepository


class SupabaseMentisMemoryRepository(MemoryRepository):
    def __init__(self, url: str, publishable_key: str | None, service_role_key: str | None = None) -> None:
        self.url = (url or "").rstrip("/")
        self.publishable_key = publishable_key
        self.service_role_key = service_role_key

    async def verify(self) -> MentisVerification:
        started = time.monotonic()
        if not self.url or not self.publishable_key:
            return MentisVerification(
                reachable=False,
                can_read=False,
                can_write=False,
                latency_ms=0,
                detail="Falta SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY para Mentis.",
            )

        can_read = False
        can_write = False
        detail = "Mentis no verificado."
        try:
            async with httpx.AsyncClient(timeout=6) as client:
                read_resp = await client.get(
                    f"{self.url}/rest/v1/mentis_memory",
                    headers=self._headers(use_service_role=True),
                    params={"select": "id", "limit": "1"},
                )
                can_read = read_resp.status_code < 400
                detail = f"Lectura HTTP {read_resp.status_code}"

                if self.service_role_key:
                    payload = {
                        "category": "_healthcheck",
                        "summary": "mentis read/write verification",
                        "metadata": {"type": "healthcheck", "ephemeral": True},
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    write_resp = await client.post(
                        f"{self.url}/rest/v1/mentis_memory",
                        headers={**self._headers(use_service_role=True), "Prefer": "return=representation"},
                        json=payload,
                    )
                    can_write = write_resp.status_code in {200, 201, 204}
                    detail = f"{detail}; escritura HTTP {write_resp.status_code}"
                    if can_write and write_resp.content:
                        rows = write_resp.json()
                        if rows and rows[0].get("id"):
                            await client.delete(
                                f"{self.url}/rest/v1/mentis_memory",
                                headers=self._headers(use_service_role=True),
                                params={"id": f"eq.{rows[0]['id']}"},
                            )
                else:
                    detail = f"{detail}; escritura no verificada: falta SUPABASE_SERVICE_ROLE_KEY"
        except Exception as exc:
            detail = str(exc)

        return MentisVerification(
            reachable=can_read or can_write,
            can_read=can_read,
            can_write=can_write,
            latency_ms=int((time.monotonic() - started) * 1000),
            detail=detail,
        )

    async def list_recent(self, context: str | None, limit: int = 50) -> list[MemoryFragment]:
        params = {
            "select": "id,category,summary,metadata,created_at",
            "order": "created_at.desc",
            "limit": str(min(max(limit, 1), 200)),
        }
        context_filter = self._context_filter(context)
        endpoint = f"{self.url}/rest/v1/mentis_memory"
        if context_filter:
            endpoint = f"{endpoint}?{context_filter}"
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(endpoint, headers=self._headers(use_service_role=True), params=params)
        response.raise_for_status()
        return [self._fragment_from_row(row) for row in response.json()]

    async def clear_context(self, context: str | None) -> int:
        endpoint = f"{self.url}/rest/v1/mentis_memory?{self._context_filter(context)}"
        headers = {**self._headers(use_service_role=True), "Prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.delete(endpoint, headers=headers)
        response.raise_for_status()
        if response.status_code == 204:
            return 0
        return len(response.json())

    async def save_fragment(self, fragment: MemoryFragment) -> MemoryFragment:
        payload = {
            "category": fragment.category,
            "summary": fragment.summary,
            "metadata": fragment.metadata,
            "created_at": (fragment.created_at or datetime.now(timezone.utc)).isoformat(),
        }
        headers = {**self._headers(use_service_role=True), "Prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(f"{self.url}/rest/v1/mentis_memory", headers=headers, json=payload)
        response.raise_for_status()
        return self._fragment_from_row(response.json()[0])

    async def list_consolidations(self, limit: int = 100) -> list[ConsolidationRecord]:
        params = {
            "select": "id,category,summary,metadata,created_at",
            "metadata->>type": "eq.long_term_consolidation",
            "order": "created_at.desc",
            "limit": str(min(max(limit, 1), 200)),
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{self.url}/rest/v1/mentis_memory",
                headers=self._headers(use_service_role=True),
                params=params,
            )
        response.raise_for_status()
        return [self._consolidation_from_row(row) for row in response.json()]

    def _headers(self, use_service_role: bool) -> dict[str, str]:
        key = self.service_role_key if use_service_role and self.service_role_key else self.publishable_key
        if not key:
            raise RuntimeError("Mentis requiere una llave Supabase configurada.")
        return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    @staticmethod
    def _context_filter(context: str | None) -> str:
        if context == "all":
            return ""
        if context == "marketer":
            return "category=ilike.marketing*"
        if context == "writer":
            return "category=ilike.writer*"
        if context == "picture":
            return "category=ilike.picture*"
        if context == "coder-web":
            return "category=ilike.coder-web*"
        return "category=not.ilike.marketing*,category=not.ilike.writer*,category=not.ilike.picture*,category=not.ilike.coder-web*"

    @staticmethod
    def _fragment_from_row(row: dict) -> MemoryFragment:
        return MemoryFragment(
            id=row.get("id") or str(uuid4()),
            category=row.get("category", "general"),
            summary=row.get("summary", ""),
            metadata=row.get("metadata") or {},
            created_at=_parse_datetime(row.get("created_at")),
        )

    @staticmethod
    def _consolidation_from_row(row: dict) -> ConsolidationRecord:
        metadata = row.get("metadata") or {}
        summary = row.get("summary", "")
        title = metadata.get("title") or _first_summary_line(summary) or "Consolidacion de memoria"
        return ConsolidationRecord(
            id=row.get("id") or str(uuid4()),
            category=row.get("category", "consolidated_general"),
            title=title,
            summary=summary,
            status=metadata.get("status", "succeeded"),
            memory_count=int(metadata.get("memory_count") or metadata.get("source_count") or 0),
            metadata=metadata,
            created_at=_parse_datetime(row.get("created_at")) or datetime.now(timezone.utc),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _first_summary_line(summary: str) -> str:
    for line in summary.splitlines():
        clean = line.replace("#", "").strip()
        if clean:
            return clean[:120]
    return ""
