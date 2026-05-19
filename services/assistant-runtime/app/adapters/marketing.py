import os
from app.domain.ports.marketing import MarketingPort

class SocialMediaStubAdapter(MarketingPort):
    def __init__(self):
        self._processed: set[str] = set()
        self.campaign_drafts: list[dict] = []
        self.post_drafts: list[dict] = []
        self.automation_runs: list[dict] = []

    async def get_comments(
        self,
        platform: str,
        post_id: str,
        data_source: str | None = None,
        account_id: str | None = None,
    ) -> list[dict]:
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

    async def get_dashboard(self) -> dict:
        print("[STUB] Obteniendo dashboard de marketing")
        return {
            "status": "success",
            "metrics": {"engagement": "4.2%", "growth": "+15%"}
        }

    async def generate_report(self, report_type: str) -> dict:
        print(f"[STUB] Generando reporte: {report_type}")
        return {
            "status": "success",
            "report_type": report_type,
            "data": "Report data stub"
        }

    async def get_top_content(self, platform: str | None = None, limit: int = 5) -> list[dict]:
        content = [
            {"platform": "instagram", "title": "Reel lanzamiento", "format": "reel", "reach": "24.1K", "engagement_rate": "7.4%", "topic": "producto"},
            {"platform": "tiktok", "title": "Proceso creativo", "format": "video", "views": "48.3K", "engagement_rate": "8.9%", "topic": "behind-the-scenes"},
        ]
        if platform:
            content = [item for item in content if item["platform"] == platform]
        return content[:limit]

    async def get_audience_insights(self) -> dict:
        return {
            "top_locations": ["Bogotá", "Medellín", "Ciudad de México"],
            "top_age_range": "25-34",
            "segments": [
                {"name": "Compradores potenciales", "share": "38%", "signal": "guardados y clicks"},
                {"name": "Comunidad creativa", "share": "31%", "signal": "comentarios y shares"},
            ],
            "best_posting_windows": ["12:00-14:00", "19:00-21:00"],
        }

    async def get_alerts(self) -> list[dict]:
        return [
            {"severity": "medium", "platform": "instagram", "title": "Caída de alcance en carruseles", "detail": "-18% vs semana anterior"},
            {"severity": "low", "platform": "tiktok", "title": "Buen momentum en videos educativos", "detail": "+22% completion rate"},
        ]

    async def get_leads(self, status: str | None = None) -> list[dict]:
        leads = [
            {"platform": "instagram", "user": "user2", "intent_score": 8, "status": "hot", "signal": "pidió INFO"},
            {"platform": "tiktok", "user": "user_tok", "intent_score": 7, "status": "warm", "signal": "preguntó precio"},
        ]
        if status:
            leads = [lead for lead in leads if lead["status"] == status]
        return leads

    async def get_whatsapp_outreach(self) -> dict:
        return {
            "contacts": [
                {"phone_number": "+573001112233", "display_name": "Lead demo", "consent_status": "opted_in", "tags": ["demo"]}
            ],
            "campaigns": [
                {"name": "Campana demo", "status": "draft", "recipient_count": 1, "target_tag": "demo"}
            ],
        }

    async def get_best_posting_windows(self) -> dict:
        return {
            "instagram": ["12:00-14:00", "19:00-21:00"],
            "tiktok": ["18:00-22:00", "07:00-09:00"],
            "recommendation": "Publica Reels al mediodía y TikToks educativos al cierre del día.",
        }

    async def list_posts(self, platform: str | None = None, limit: int = 10) -> list[dict]:
        posts = [
            {"id": "stub-post-1", "platform": "instagram", "format": "reel", "title": "Reel lanzamiento", "status": "published"},
            {"id": "stub-post-2", "platform": "tiktok", "format": "video", "title": "Proceso creativo", "status": "published"},
        ]
        if platform:
            posts = [post for post in posts if post["platform"] == platform]
        return posts[:limit]

    async def save_campaign_draft(self, campaign: dict) -> bool:
        self.campaign_drafts.append(campaign)
        self._processed.add(campaign.get("id", "campaign-draft"))
        return True

    async def save_post_draft(self, post: dict) -> bool:
        self.post_drafts.append(post)
        self._processed.add(post.get("id", "post-draft"))
        return True

    async def save_automation_run(self, run: dict) -> bool:
        self.automation_runs.append(run)
        dedupe_key = run.get("dedupe_key")
        if dedupe_key:
            self._processed.add(dedupe_key)
        return True

    async def has_processed(self, dedupe_key: str) -> bool:
        return dedupe_key in self._processed

    async def schedule_post(self, post: dict) -> bool:
        print(f"[STUB] Scheduling post draft {post.get('id')}")
        return True

    async def publish_post(self, post: dict) -> bool:
        print(f"[STUB] Publishing post draft {post.get('id')}")
        return True
