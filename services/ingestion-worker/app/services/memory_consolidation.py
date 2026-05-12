import httpx
import json
from datetime import datetime, timezone, timedelta
from app.settings import settings
import google.generativeai as genai
import os

class MemoryConsolidationService:
    def __init__(self):
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_service_role_key
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-2.0-flash-lite")

    async def run_consolidation(self):
        print("[MEMORY] Iniciando consolidación de memoria diaria...")
        
        # 1. Obtener memorias de las últimas 24 horas
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        
        url = f"{self.supabase_url}/rest/v1/mentis_memory?created_at=gte.{yesterday}&order=created_at.desc"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    print(f"[MEMORY ERROR] No se pudo obtener memorias: {resp.text}")
                    return
                
                memories = resp.json()
                if not memories:
                    print("[MEMORY] No hay memorias recientes para consolidar.")
                    return
                
                # 2. Agrupar por categoría
                grouped = {}
                for m in memories:
                    cat = m.get("category", "general")
                    if cat not in grouped: grouped[cat] = []
                    grouped[cat].append(m.get("summary", ""))

                # 3. Consolidar cada categoría con LLM
                consolidated_summaries = []
                for cat, texts in grouped.items():
                    print(f"[MEMORY] Consolidando categoría: {cat} ({len(texts)} items)")
                    full_text = "\n---\n".join(texts)
                    prompt = (
                        f"A continuación tienes una lista de eventos/aprendizajes registrados hoy para la categoría '{cat}'. "
                        f"Resume los puntos más importantes de manera concisa y genera 'Aprendizajes Permanentes' "
                        f"que sirvan para el futuro del agente.\n\n"
                        f"MEMORIAS:\n{full_text}"
                    )
                    
                    response = await self.model.generate_content_async(prompt)
                    summary = response.text
                    
                    consolidated_summaries.append({
                        "category": f"consolidated_{cat}",
                        "summary": summary,
                        "metadata": {"type": "daily_consolidation", "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
                    })

                # 4. Guardar los resúmenes consolidados en Supabase (usando la misma tabla por ahora con un flag de consolidado)
                # O podríamos guardarlos en una tabla de 'knowledge' dedicada
                for cs in consolidated_summaries:
                    save_resp = await client.post(
                        f"{self.supabase_url}/rest/v1/mentis_memory",
                        headers=headers,
                        json=cs
                    )
                    if save_resp.status_code not in [200, 201, 204]:
                        print(f"[MEMORY ERROR] Error guardando consolidación: {save_resp.text}")
                
                print(f"[MEMORY] Consolidación completada. Se generaron {len(consolidated_summaries)} resúmenes.")
                
            except Exception as e:
                print(f"[MEMORY CRITICAL ERROR] {e}")

    async def notify_discord(self, message: str):
        if not settings.discord_notifications_channel_id: return
        url = f"https://discord.com/api/v10/channels/{settings.discord_notifications_channel_id}/messages"
        headers = {"Authorization": f"Bot {settings.discord_bot_token}"}
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers, json={"content": message})
