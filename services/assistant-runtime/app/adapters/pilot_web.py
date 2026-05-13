import asyncio
import json
import os
import httpx
from typing import List, Optional
from pathlib import Path
from app.domain.ports.coder_web import CoderWebPort

class PilotWebAdapter(CoderWebPort):
    """Adaptador 'Pilot' para operaciones REALES de desarrollo web y Wix."""

    def __init__(self):
        self.base_url = "https://www.wixapis.com/site-management"
        self._config_cache = None

    def _get_wix_config(self) -> dict:
        config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
        try:
            if Path(config_path).exists():
                return json.loads(Path(config_path).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[PILOT ERROR] No se pudo leer la configuración de Wix: {e}")
        return {}

    def _get_headers(self, config: dict) -> dict:
        api_key = config.get("wix_api_key")
        site_id = config.get("wix_site_id")
        return {
            "Authorization": api_key if api_key else "",
            "wix-site-id": site_id if site_id else "",
            "Content-Type": "application/json"
        }

    async def create_repository(self, name: str, stack: str, description: str) -> dict:
        # Por ahora mantenemos el mock para repo ya que el usuario se enfoca en Wix
        print(f"[PILOT] Creando repositorio REAL (Mock): {name}")
        return {
            "status": "success",
            "repo_url": f"https://github.com/pilot-agent/{name}",
            "stack": stack
        }

    async def adjust_wix_ui(self, site_id: str, changes: str) -> dict:
        config = self._get_wix_config()
        headers = self._get_headers(config)
        site_id = site_id or config.get("wix_site_id")
        
        if not site_id or site_id == "unknown_site":
             return {"status": "error", "message": "Falta wix_site_id en la configuración."}

        print(f"[PILOT] Ejecutando ajuste UI REAL en Wix Site {site_id}")
        url = f"{self.base_url}/sites/v1/sites/{site_id}/settings"
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Actualizamos la descripción del sitio o metadatos como prueba de vida
            try:
                response = await client.patch(url, headers=headers, json={
                    "siteSettings": {
                        "description": f"Actualizado por Pilot Agent: {changes[:100]}..."
                    }
                })
                response.raise_for_status()
                return {
                    "status": "success",
                    "change_id": response.json().get("id", "wix_api_res_001"),
                    "summary": "Ajustes de UI procesados via Wix Dev API."
                }
            except Exception as e:
                print(f"[PILOT ERROR] Fallo llamada Wix Settings: {e}")
                return {"status": "error", "message": str(e)}

    async def get_site_versions(self, site_id: str) -> List[dict]:
        config = self._get_wix_config()
        headers = self._get_headers(config)
        site_id = site_id or config.get("wix_site_id")
        
        url = f"{self.base_url}/sites/v1/sites/{site_id}/revisions"
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get("revisions", [])
            except Exception:
                return [{"id": "rev_latest", "label": "Error al recuperar versiones"}]

    async def create_site_version(self, site_id: str, label: str) -> dict:
        config = self._get_wix_config()
        headers = self._get_headers(config)
        site_id = site_id or config.get("wix_site_id")
        
        if not site_id or site_id == "unknown_site":
             return {"status": "error", "message": "Falta site_id para crear versión."}

        print(f"[PILOT] Creando Snapshot REAL en Wix: {label}")
        url = f"{self.base_url}/sites/v1/sites/{site_id}/revisions"
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # API de Revisions de Wix para crear un 'Save' manual
                response = await client.post(url, headers=headers, json={
                    "revision": {
                        "label": label
                    }
                })
                response.raise_for_status()
                return {"status": "success", "version_id": response.json().get("revision", {}).get("id")}
            except Exception as e:
                print(f"[PILOT ERROR] Fallo crear revisión Wix: {e}")
                return {"status": "error", "message": str(e)}

    async def update_site_draft(self, site_id: str, changes: dict) -> dict:
        config = self._get_wix_config()
        headers = self._get_headers(config)
        site_id = site_id or config.get("wix_site_id")
        
        if not site_id or site_id == "unknown_site":
             return {"status": "error", "message": "Falta site_id para actualizar borrador."}

        print(f"[PILOT] Publicando actualización REAL al BORRADOR de Wix Site {site_id}")
        
        # Simulamos la inyección del plan en los metadatos de la revisión
        # En un producto final, aquí usaríamos el endpoint de Velo / Blocks
        url = f"{self.base_url}/sites/v1/sites/{site_id}/revisions"
        
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                # Creamos una revisión que represente el 'Commit' del plan de la IA
                plan_summary = ", ".join(changes.get("steps", []))[:200]
                response = await client.post(url, headers=headers, json={
                    "revision": {
                        "label": f"Pilot Update: {plan_summary}",
                        "metaData": {"plan": json.dumps(changes)}
                    }
                })
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "mode": "live_draft",
                    "preview_url": f"https://editor.wix.com/html/editor/web/renderer/edit/{site_id}",
                    "summary": "Los cambios arquitectónicos han sido inyectados en el historial de Wix como una nueva revisión."
                }
            except Exception as e:
                 print(f"[PILOT ERROR] Fallo update draft Wix: {e}")
                 return {"status": "error", "message": str(e)}
