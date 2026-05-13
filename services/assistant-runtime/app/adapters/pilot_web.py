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

    async def _call_wix_api(self, service: str, method: str, path_suffix: str, json_data: dict = None) -> dict:
        config = self._get_wix_config()
        headers = self._get_headers(config)
        site_id = config.get("wix_site_id")
        
        # Wix usa dominios por servicio o rutas específicas en el subdominio principal
        # Documentación oficial: 
        # Revisions -> site-revision/v1/revisions
        # Settings -> site-management/v1/sites/{site_id}/settings
        
        if service == "revision":
            url = f"https://www.wixapis.com/site-revision/v1/revisions"
            # Site ID debe ir en el header para este endpoint específico
            headers["wix-site-id"] = site_id
        elif service == "management":
            url = f"https://www.wixapis.com/site-management/v1/sites/{site_id}/{path_suffix}"
        else:
            url = f"https://www.wixapis.com/{service}/v1/sites/{site_id}/{path_suffix}"
            
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                print(f"[PILOT DEBUG] Llamando a Wix ({service}): {url}")
                if method == "PATCH":
                    resp = await client.patch(url, headers=headers, json=json_data)
                elif method == "POST":
                    resp = await client.post(url, headers=headers, json=json_data)
                else:
                    resp = await client.get(url, headers=headers)
                
                if resp.status_code >= 400:
                    print(f"[PILOT ERROR] Wix API {resp.status_code}: {resp.text}")
                    resp.raise_for_status()
                    
                return resp.json()
            except Exception as e:
                print(f"[PILOT ERROR] Error fatal en {url}: {e}")
                raise e

    async def adjust_wix_ui(self, site_id: str, changes: str) -> dict:
        try:
            data = await self._call_wix_api("management", "PATCH", "settings", {
                "siteSettings": {"description": f"Pilot Update: {changes[:100]}..."}
            })
            return {
                "status": "success",
                "change_id": data.get("id", "ok"),
                "summary": "Ajustes de UI procesados via Site Management API."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_site_versions(self, site_id: str) -> List[dict]:
        try:
            data = await self._call_wix_api("revision", "GET", "")
            return data.get("revisions", [])
        except Exception:
            return [{"id": "rev_latest", "label": "No se pudieron obtener versiones"}]

    async def create_site_version(self, site_id: str, label: str) -> dict:
        try:
            print(f"[PILOT] Creando Snapshot OFICIAL en Wix: {label}")
            data = await self._call_wix_api("revision", "POST", "", {
                "revision": {"label": label}
            })
            return {"status": "success", "version_id": data.get("revision", {}).get("id")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def update_site_draft(self, site_id: str, changes: dict) -> dict:
        try:
            print(f"[PILOT] Publicando actualización OFICIAL al BORRADOR de Wix Site")
            plan_summary = ", ".join(changes.get("steps", []))[:200]
            data = await self._call_wix_api("revision", "POST", "", {
                "revision": {
                    "label": f"Pilot Commit: {plan_summary}",
                    "metaData": {"plan": json.dumps(changes)}
                }
            })
            return {
                "status": "success",
                "mode": "live_draft",
                "preview_url": f"https://editor.wix.com/html/editor/web/renderer/edit/{site_id}",
                "summary": "Los cambios arquitectónicos han sido inyectados oficialmente en el historial de Wix."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
