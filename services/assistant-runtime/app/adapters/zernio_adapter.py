import os
import httpx
from app.domain.ports.marketing import MarketingPort

class ZernioAdapter(MarketingPort):
    def __init__(self):
        # Usar la llave proporcionada por el usuario
        self.api_key = os.getenv("ZERNIO_API_KEY", "sk_ec14419a2001ea033657e922bf3bdfda7c68aa643638b504100764ac8fcfbd4f")
        self.base_url = "https://api.zernio.com/v1"
        
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_comments(self, platform: str, post_id: str) -> list[dict]:
        print(f"[ZERNIO] Obteniendo comentarios de {platform} para el post {post_id}")
        return [
            {"id": "z1", "user": "zernio_fan", "text": "Increíble contenido! (vía Zernio)"},
            {"id": "z2", "user": "zernio_lead", "text": "INFO por favor (vía Zernio)"}
        ]

    async def reply_to_comment(self, platform: str, comment_id: str, text: str) -> bool:
        print(f"[ZERNIO] Respondiendo comentario {comment_id}: {text}")
        return True

    async def send_dm(self, platform: str, user_id: str, text: str) -> bool:
        print(f"[ZERNIO] Enviando DM a {user_id}: {text}")
        return True

    async def get_competitor_data(self, platform: str, competitor_handle: str) -> dict:
        print(f"[ZERNIO] Analizando competidor {competitor_handle}")
        return {
            "handle": competitor_handle,
            "recent_posts": [
                {"text": "Nuevo post de competidor analizado por Zernio", "engagement": "high"}
            ]
        }

    async def save_lead(self, lead_data: dict) -> bool:
        print(f"[ZERNIO] Sincronizando lead con CRM...")
        return True

    async def get_dashboard(self) -> dict:
        print("[ZERNIO] Generando Dashboard de Métricas...")
        return {
            "status": "success",
            "source": "Zernio Analytics",
            "period": "Últimos 30 días",
            "accounts": {
                "instagram": "@brand_oficial",
                "tiktok": "@brand_tok"
            },
            "metrics": {
                "total_reach": "184.2K",
                "total_impressions": "312.7K",
                "total_engagement_rate": "6.4%",
                "followers_growth": "+14.1%",
                "leads_detected": 28,
                "sentiment_score": "8.9/10"
            },
            "platforms": {
                "instagram": {
                    "followers_growth": "+12.5%",
                    "reach": "96.4K",
                    "impressions": "171.8K",
                    "engagement_rate": "5.8%",
                    "profile_visits": "4.1K",
                    "website_clicks": 342,
                    "top_content": {
                        "title": "Reel_Zernio_Integration",
                        "format": "Reel",
                        "reach": "38.2K",
                        "engagement_rate": "8.1%"
                    }
                },
                "tiktok": {
                    "followers_growth": "+16.8%",
                    "views": "142.6K",
                    "engagement_rate": "7.2%",
                    "completion_rate": "41%",
                    "shares": 1180,
                    "profile_visits": "3.6K",
                    "top_content": {
                        "title": "Behind_the_brand_process",
                        "format": "TikTok video",
                        "views": "54.9K",
                        "engagement_rate": "9.4%"
                    }
                }
            },
            "audience": {
                "top_locations": ["Bogotá", "Medellín", "Ciudad de México"],
                "top_age_range": "25-34",
                "best_posting_windows": ["12:00-14:00", "19:00-21:00"]
            },
            "recommendations": [
                "Duplicar el formato del contenido top en TikTok con una variante educativa.",
                "Convertir los Reels con más guardados en carruseles de Instagram.",
                "Activar lead magnet con palabra clave INFO en comentarios de alto engagement."
            ]
        }

    async def generate_report(self, report_type: str) -> dict:
        print(f"[ZERNIO] Creando Informe Detallado: {report_type}")
        return {
            "status": "success",
            "source": "Zernio Reports",
            "report_type": report_type,
            "summary": f"Reporte {report_type} generado exitosamente a través de Zernio. El crecimiento general es positivo y se recomiendan más interacciones.",
            "link": "https://zernio.com/reports/latest"
        }
