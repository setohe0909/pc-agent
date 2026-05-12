import os
from app.domain.ports.marketing import MarketingPort

class SocialMediaStubAdapter(MarketingPort):
    async def get_comments(self, platform: str, post_id: str) -> list[dict]:
        # En una implementación real, aquí se llamaría a la API de Instagram o TikTok
        print(f"[STUB] Obteniendo comentarios de {platform} para el post {post_id}")
        return [
            {"id": "c1", "user": "user1", "text": "Me encanta este diseño!"},
            {"id": "c2", "user": "user2", "text": "Cuándo sale la nueva temporada?"},
            {"id": "c3", "user": "user3", "text": "El color no me convence mucho..."},
        ]

    async def reply_to_comment(self, platform: str, comment_id: str, text: str) -> bool:
        print(f"[STUB] Replying to {platform} comment {comment_id}: {text}")
        return True

    async def send_dm(self, platform: str, user_id: str, text: str) -> bool:
        print(f"[STUB] Sending DM to {platform} user {user_id}: {text}")
        return True

    async def get_competitor_data(self, platform: str, competitor_handle: str) -> dict:
        print(f"[STUB] Obteniendo datos de competidor {competitor_handle} en {platform}")
        return {
            "handle": competitor_handle,
            "recent_posts": [
                {"text": "Nueva colección de verano disponible", "engagement": "high"},
                {"text": "Ofertas relámpago este fin de semana", "engagement": "medium"}
            ]
        }

    async def save_lead(self, lead_data: dict) -> bool:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        if not url or not key:
            print("[STUB] Error: Supabase config missing for save_lead")
            return False
        
        print(f"[STUB] Guardando lead de {lead_data['external_user']} en Supabase...")
        import httpx
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{url}/rest/v1/marketing_leads", headers=headers, json=lead_data)
                return resp.status_code in [200, 201, 204]
            except Exception as e:
                print(f"[STUB ERROR] {e}")
                return False
