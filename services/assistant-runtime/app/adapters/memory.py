import httpx
import os

class MentisMemoryAdapter:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")

    async def get_context(self, user_id: str) -> str:
        """Busca los fragmentos de inteligencia mas recientes para dar contexto al LLM"""
        if not self.supabase_url or not self.supabase_key:
            return ""
            
        url = f"{self.supabase_url}/rest/v1/mentis_memory?select=category,summary&order=created_at.desc&limit=5"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if not data: return ""
                    context = "\n\n--- MEMORIA RECIENTE (INTELIGENCIA DEL DIA) ---\n"
                    for item in data:
                        context += f"Categoría: {item['category']}\nResumen: {item['summary']}\n\n"
                    return context
                return ""
        except Exception as e:
            print(f"[MEMORY ERROR] {e}")
            return ""

    async def save_interaction(self, user_id: str, data: dict) -> None:
        """Pendiente: Guardar interacciones de chat en una tabla de historial si se desea"""
        pass

    async def save_memory(self, category: str, summary: str) -> bool:
        """Guarda un fragmento de conocimiento/aprendizaje en la tabla mentis_memory"""
        if not self.supabase_url or not self.supabase_key:
            return False

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        url = f"{self.supabase_url}/rest/v1/mentis_memory"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        payload = {
            "category": category,
            "summary": summary,
            "created_at": now.isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, headers=headers, json=payload)
                return resp.status_code == 201
        except Exception as e:
            print(f"[MEMORY SAVE ERROR] {e}")
            return False
