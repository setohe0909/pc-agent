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
        print(f"[STUB] Respondiendo en {platform} al comentario {comment_id}: {text}")
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
