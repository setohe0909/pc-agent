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
            
        # Determinar filtro segun el contexto
        if user_id == "marketer":
            # Para el marketer, solo traemos lo que sea de marketing
            category_filter = "category=ilike.marketing_*"
        elif user_id == "picture":
            # Para el picture agent, traemos lo relacionado con imagenes
            category_filter = "category=ilike.picture_*"
        else:
            # Para el resto (general, writer), traemos lo que NO sea de marketing ni picture
            category_filter = "category=not.ilike.marketing_*,category=not.ilike.picture_*"
            
        url = f"{self.supabase_url}/rest/v1/mentis_memory?{category_filter}&select=category,summary&order=created_at.desc&limit=5"
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
                    context = f"\n\n--- MEMORIA RECIENTE ({user_id.upper()}) ---\n"
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

    async def clear_memory(self, user_id: str) -> bool:
        """Borra los fragmentos de memoria segun el contexto"""
        if not self.supabase_url or not self.supabase_key:
            return False
            
        # Determinar filtro segun el contexto (misma logica que get_context)
        if user_id == "marketer":
            category_filter = "category=ilike.marketing_*"
        elif user_id == "picture":
            category_filter = "category=ilike.picture_*"
        else:
            category_filter = "category=not.ilike.marketing_*,category=not.ilike.picture_*"
            
        url = f"{self.supabase_url}/rest/v1/mentis_memory?{category_filter}"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.delete(url, headers=headers)
                # PostgREST devuelve 204 No Content en DELETE exitosos
                return resp.status_code in [200, 204]
        except Exception as e:
            print(f"[MEMORY CLEAR ERROR] {e}")
            return False
