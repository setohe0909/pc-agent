import httpx
import json
from datetime import datetime
from app.settings import settings

class MentisClient:
    def __init__(self, base_url: str):
        self.url = settings.supabase_url
        self.key = settings.supabase_service_role_key or settings.supabase_publishable_key

    async def save_daily_knowledge(self, category: str, content: str):
        """Guarda conocimiento diario en Supabase (Mentis Storage)"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        payload = {
            "category": category,
            "summary": content,
            "created_at": now.isoformat(),
            "date_key": today
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                print(f"[MENTIS] Guardando en Supabase: {category}...")
                # Nota: Usamos rpc o tabla directa. Por ahora, tabla 'mentis_memory'
                response = await client.post(
                    f"{self.url}/rest/v1/mentis_memory", 
                    headers=headers, 
                    json=payload
                )
                if response.status_code != 201:
                    print(f"[MENTIS WARNING] Error al guardar (posiblemente la tabla no existe): {response.text}")
                return True
        except Exception as e:
            print(f"[MENTIS ERROR] Fallo critico al conectar con Supabase: {e}")
            return False
