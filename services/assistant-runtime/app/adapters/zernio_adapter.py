import os
import httpx
from app.domain.ports.marketing import MarketingPort

class ZernioAdapter(MarketingPort):
    def __init__(self):
        self.api_key = os.getenv("ZERNIO_API_KEY", "")
        self.base_url = "https://api.zernio.com/v1"
        self._processed: set[str] = set()
        self._campaign_drafts: list[dict] = []
        self._post_drafts: list[dict] = []
        self._automation_runs: list[dict] = []
        
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

    async def get_top_content(self, platform: str | None = None, limit: int = 5) -> list[dict]:
        print(f"[ZERNIO] Obteniendo top content ({platform or 'all'})")
        content = [
            {
                "platform": "tiktok",
                "title": "Behind_the_brand_process",
                "format": "video",
                "views": "54.9K",
                "engagement_rate": "9.4%",
                "completion_rate": "41%",
                "saves": 920,
                "shares": 1180,
                "topic": "proceso creativo"
            },
            {
                "platform": "instagram",
                "title": "Reel_Zernio_Integration",
                "format": "reel",
                "reach": "38.2K",
                "engagement_rate": "8.1%",
                "saves": 640,
                "shares": 410,
                "topic": "integración y producto"
            },
            {
                "platform": "instagram",
                "title": "Carousel_Style_Guide",
                "format": "carousel",
                "reach": "24.6K",
                "engagement_rate": "6.9%",
                "saves": 980,
                "shares": 210,
                "topic": "educativo"
            },
            {
                "platform": "tiktok",
                "title": "Founder_story_short",
                "format": "video",
                "views": "31.4K",
                "engagement_rate": "7.6%",
                "completion_rate": "36%",
                "saves": 380,
                "shares": 560,
                "topic": "storytelling"
            },
        ]
        if platform:
            content = [item for item in content if item["platform"] == platform]
        return content[:limit]

    async def get_audience_insights(self) -> dict:
        print("[ZERNIO] Obteniendo audiencia")
        return {
            "top_locations": ["Bogotá", "Medellín", "Ciudad de México"],
            "top_age_range": "25-34",
            "gender_split": {"female": "58%", "male": "39%", "unknown": "3%"},
            "segments": [
                {"name": "Compradores potenciales", "share": "38%", "signal": "clicks, guardados y mensajes con INFO"},
                {"name": "Comunidad creativa", "share": "31%", "signal": "comentarios, shares y contenido guardado"},
                {"name": "Audiencia nueva TikTok", "share": "21%", "signal": "views altas con baja conversión a perfil"},
            ],
            "best_posting_windows": ["12:00-14:00", "19:00-21:00"],
            "content_preferences": ["procesos detrás de cámara", "guías prácticas", "comparativas antes/después"]
        }

    async def get_alerts(self) -> list[dict]:
        print("[ZERNIO] Obteniendo alertas")
        return [
            {
                "severity": "high",
                "platform": "tiktok",
                "title": "Views altas, conversión a perfil moderada",
                "detail": "El contenido top logra 54.9K views, pero las visitas al perfil están debajo del potencial.",
                "recommendation": "Agregar CTA visual en los primeros 5 segundos y comentario fijado con lead magnet."
            },
            {
                "severity": "medium",
                "platform": "instagram",
                "title": "Carruseles con muchos guardados",
                "detail": "Los carruseles educativos superan a Reels en saves.",
                "recommendation": "Convertir carruseles ganadores en Reels narrados y stories con encuesta."
            },
            {
                "severity": "low",
                "platform": "instagram",
                "title": "Sentimiento saludable",
                "detail": "Sentiment score 8.9/10 sin señales fuertes de crisis.",
                "recommendation": "Mantener monitoreo de comentarios negativos y responder en menos de 12h."
            },
        ]

    async def get_leads(self, status: str | None = None) -> list[dict]:
        print(f"[ZERNIO] Obteniendo leads ({status or 'all'})")
        leads = [
            {"platform": "instagram", "user": "zernio_lead", "intent_score": 9, "status": "hot", "signal": "Pidió INFO en comentario", "suggested_next_step": "Enviar catálogo y pregunta de necesidad"},
            {"platform": "tiktok", "user": "tok_style_21", "intent_score": 8, "status": "hot", "signal": "Preguntó precio en video top", "suggested_next_step": "Responder con rango y llevar a DM"},
            {"platform": "instagram", "user": "creative_buyer", "intent_score": 7, "status": "warm", "signal": "Guardó 3 contenidos educativos", "suggested_next_step": "Enviar guía de estilo"},
        ]
        if status:
            leads = [lead for lead in leads if lead["status"] == status]
        return leads

    async def get_best_posting_windows(self) -> dict:
        print("[ZERNIO] Obteniendo mejores horarios")
        return {
            "instagram": ["12:00-14:00", "19:00-21:00"],
            "tiktok": ["18:00-22:00", "07:00-09:00"],
            "by_format": {
                "reels": "12:30",
                "carousels": "19:30",
                "tiktok_educativo": "20:15",
                "stories": "08:30"
            },
            "recommendation": "Concentrar piezas educativas en la noche y contenido de conversión al mediodía."
        }

    async def list_posts(self, platform: str | None = None, limit: int = 10) -> list[dict]:
        print(f"[ZERNIO] Listando posts ({platform or 'all'})")
        posts = [
            {"id": "ig-reel-zernio", "platform": "instagram", "format": "reel", "title": "Reel_Zernio_Integration", "status": "published"},
            {"id": "ig-carousel-style", "platform": "instagram", "format": "carousel", "title": "Carousel_Style_Guide", "status": "published"},
            {"id": "tt-brand-process", "platform": "tiktok", "format": "video", "title": "Behind_the_brand_process", "status": "published"},
        ]
        if platform:
            posts = [post for post in posts if post["platform"] == platform]
        return posts[:limit]

    async def save_campaign_draft(self, campaign: dict) -> bool:
        print(f"[ZERNIO] Guardando borrador de campaña {campaign.get('id')}")
        self._campaign_drafts.append(campaign)
        self._processed.add(campaign.get("id", "campaign-draft"))
        return True

    async def save_post_draft(self, post: dict) -> bool:
        print(f"[ZERNIO] Guardando borrador de post {post.get('id')}")
        self._post_drafts.append(post)
        self._processed.add(post.get("id", "post-draft"))
        return True

    async def save_automation_run(self, run: dict) -> bool:
        print(f"[ZERNIO] Registrando automation run {run.get('dedupe_key')}")
        self._automation_runs.append(run)
        dedupe_key = run.get("dedupe_key")
        if dedupe_key:
            self._processed.add(dedupe_key)
        return True

    async def has_processed(self, dedupe_key: str) -> bool:
        return dedupe_key in self._processed

    async def schedule_post(self, post: dict) -> bool:
        print(f"[ZERNIO] Programando post {post.get('id')}")
        return True

    async def publish_post(self, post: dict) -> bool:
        print(f"[ZERNIO] Publicando post {post.get('id')}")
        return True
