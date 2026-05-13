import asyncio
from typing import List, Optional
from app.domain.ports.coder_web import CoderWebPort

class PilotWebAdapter(CoderWebPort):
    """Adaptador 'Pilot' para operaciones de desarrollo web y Wix."""

    async def create_repository(self, name: str, stack: str, description: str) -> dict:
        print(f"[PILOT] Creando repositorio: {name} con stack {stack}")
        await asyncio.sleep(1) # Simular latencia
        return {
            "status": "success",
            "repo_url": f"https://github.com/pilot-agent/{name}",
            "stack": stack,
            "files": ["package.json", "tsconfig.json", "src/App.tsx", "supabase/config.toml"]
        }

    async def adjust_wix_ui(self, site_id: str, changes: str) -> dict:
        print(f"[PILOT] Ajustando Wix Site {site_id}: {changes}")
        await asyncio.sleep(1)
        return {
            "status": "success",
            "change_id": "wix_ch_9982",
            "summary": "UI actualizada siguiendo principios de diseño minimalista."
        }

    async def get_site_versions(self, site_id: str) -> List[dict]:
        return [
            {"id": "v1", "date": "2026-05-12", "label": "Initial Design"},
            {"id": "v2", "date": "2026-05-13", "label": "Minimalist Update"}
        ]

    async def create_site_version(self, site_id: str, label: str) -> dict:
        print(f"[PILOT] Creando versión en Wix: {label}")
        return {"status": "success", "version_id": f"v_{label.replace(' ', '_').lower()}"}
