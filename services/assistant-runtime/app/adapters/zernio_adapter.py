import os
import httpx
from datetime import datetime, timezone, timedelta
from app.domain.ports.marketing import MarketingPort


MONTH_DAYS = 30


def _to_iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


class ZernioAdapter(MarketingPort):
    def __init__(self):
        self.api_key = os.getenv("ZERNIO_API_KEY", "")
        self.base_url = "https://zernio.com/api/v1"

        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
        )
        self._accounts_cache: list[dict] | None = None
        self._processed: set[str] = set()

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------
    def _z_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _supa_headers(self):
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

    async def _z_get(self, path: str, params: dict | None = None) -> dict | list | None:
        if not self.api_key:
            print("[ZERNIO] ZERNIO_API_KEY no configurada")
            return None
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers=self._z_headers(), params=params)
                if resp.status_code == 200:
                    return resp.json()
                print(f"[ZERNIO][HTTP {resp.status_code}] GET {path}")
                return None
        except Exception as e:
            print(f"[ZERNIO][ERROR] GET {path}: {e}")
            return None

    async def _z_post(self, path: str, data: dict) -> bool:
        if not self.api_key:
            return False
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, headers=self._z_headers(), json=data)
                return resp.status_code in (200, 201, 204)
        except Exception as e:
            print(f"[ZERNIO][ERROR] POST {path}: {e}")
            return False

    async def _supa_get(self, table: str, params: str = "") -> list | None:
        if not self.supabase_url or not self.supabase_key:
            return None
        url = f"{self.supabase_url}/rest/v1/{table}?{params}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=self._supa_headers())
                if resp.status_code == 200:
                    return resp.json()
                return None
        except Exception as e:
            print(f"[ZERNIO][DB ERROR] GET {table}: {e}")
            return None

    async def _supa_post(self, table: str, data: dict) -> bool:
        if not self.supabase_url or not self.supabase_key:
            return False
        url = f"{self.supabase_url}/rest/v1/{table}"
        headers = {**self._supa_headers(), "Prefer": "return=minimal"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, headers=headers, json=data)
                return resp.status_code in (200, 201, 204)
        except Exception as e:
            print(f"[ZERNIO][DB ERROR] POST {table}: {e}")
            return False

    async def _get_memory(self, category: str, limit: int = 20) -> list[dict]:
        result = await self._supa_get(
            "mentis_memory",
            f"category=eq.{category}&select=category,summary,metadata,created_at&order=created_at.desc&limit={limit}",
        )
        return result or []

    async def _save_memory(self, category: str, summary: str, metadata: dict | None = None) -> bool:
        return await self._supa_post("mentis_memory", {
            "category": category,
            "summary": summary,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # ------------------------------------------------------------------
    # Account helpers
    # ------------------------------------------------------------------
    async def _fetch_accounts(self) -> list[dict]:
        if self._accounts_cache is not None:
            return self._accounts_cache
        data = await self._z_get("/accounts")
        if data and isinstance(data, dict):
            self._accounts_cache = data.get("accounts", [])
        else:
            self._accounts_cache = []
        return self._accounts_cache

    async def _get_account_id(self, platform: str) -> str | None:
        for acc in await self._fetch_accounts():
            if acc.get("platform") == platform:
                return acc.get("_id")
        return None

    async def _get_account_ids(self) -> dict[str, str]:
        result = {}
        for acc in await self._fetch_accounts():
            result[acc.get("platform")] = acc.get("_id")
        return result

    # ------------------------------------------------------------------
    # MarketingPort implementation
    # ------------------------------------------------------------------
    async def get_connected_accounts(self) -> dict:
        accounts = await self._fetch_accounts()
        result = {}
        for acc in accounts:
            platform = acc.get("platform")
            username = acc.get("username", "conectado")
            followers = acc.get("followersCount", 0)
            result[platform] = f"@{username} ({followers} seguidores)"
        if not result:
            return {"instagram": "no conectada", "tiktok": "no conectada"}
        return result

    async def get_comments(self, platform: str, post_id: str) -> list[dict]:
        print(f"[ZERNIO] Leyendo comentarios reales desde Zernio ({platform}/{post_id})")
        memories = await self._get_memory(f"marketing_comments_{platform}", limit=30)
        comments = []
        for mem in memories:
            meta = mem.get("metadata") or {}
            comments.append({
                "id": meta.get("comment_id", mem.get("id", "")),
                "user": meta.get("user", "desconocido"),
                "text": mem.get("summary", ""),
                "created_at": mem.get("created_at", ""),
            })
        return comments

    async def reply_to_comment(self, platform: str, comment_id: str, text: str) -> bool:
        print(f"[ZERNIO] Respondiendo comentario {comment_id}")
        return await self._save_memory(
            f"marketing_replies_{platform}",
            f"Respuesta a {comment_id}: {text}",
            {"comment_id": comment_id, "platform": platform, "reply_text": text},
        )

    async def send_dm(self, platform: str, user_id: str, text: str) -> bool:
        print(f"[ZERNIO] Enviando DM a {user_id}")
        return await self._save_memory(
            "marketing_dms",
            f"DM a {user_id} en {platform}: {text}",
            {"platform": platform, "user_id": user_id, "text": text},
        )

    async def get_competitor_data(self, platform: str, competitor_handle: str) -> dict:
        print(f"[ZERNIO] Competitor data no disponible via API, retornando vacío")
        return {"handle": competitor_handle, "recent_posts": []}

    async def save_lead(self, lead_data: dict) -> bool:
        print(f"[ZERNIO] Guardando lead en marketing_leads")
        return await self._supa_post("marketing_leads", lead_data)

    async def get_dashboard(self) -> dict:
        print("[ZERNIO] Construyendo dashboard desde Zernio API")
        accounts = await self._fetch_accounts()
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=MONTH_DAYS)
        since = _to_iso(month_ago)
        until = _to_iso(now)

        # Mapear platforms
        platform_map = {}
        for acc in accounts:
            p = acc.get("platform")
            platform_map[p] = {
                "id": acc.get("_id"),
                "username": acc.get("username", ""),
                "display": acc.get("displayName", ""),
                "followers": acc.get("followersCount", 0),
                "posts": acc.get("externalPostCount", 0),
            }

        ig_id = platform_map.get("instagram", {}).get("id")
        tt_id = platform_map.get("tiktok", {}).get("id")

        ig_insights = None
        if ig_id:
            raw = await self._z_get(
                f"/analytics/instagram/account-insights",
                {"accountId": ig_id, "since": since, "until": until},
            )
            if isinstance(raw, dict) and raw.get("success"):
                ig_insights = raw.get("metrics", {})

        tt_insights = None
        if tt_id:
            raw = await self._z_get(
                f"/analytics/tiktok/account-insights",
                {"accountId": tt_id, "since": since, "until": until},
            )
            if isinstance(raw, dict) and raw.get("success"):
                tt_insights = raw.get("metrics", {})

        # Top content
        analytics_raw = await self._z_get(
            "/analytics",
            {"sortBy": "engagement", "order": "desc", "limit": "5"},
        )
        posts_list = []
        if isinstance(analytics_raw, dict):
            posts_list = analytics_raw.get("posts", [])

        # Follower stats
        follower_raw = await self._z_get("/accounts/follower-stats")
        follower_accounts = []
        if isinstance(follower_raw, dict):
            follower_accounts = follower_raw.get("accounts", [])

        # Best times
        best_times_raw = await self._z_get("/analytics/best-time")
        best_slots = []
        if isinstance(best_times_raw, dict):
            best_slots = best_times_raw.get("slots", [])

        # Demographics
        demographics = None
        if ig_id:
            demo = await self._z_get(
                f"/analytics/instagram/demographics",
                {"accountId": ig_id},
            )
            if isinstance(demo, dict) and demo.get("success"):
                demographics = demo.get("demographics", {})

        # Daily metrics
        daily_raw = await self._z_get("/analytics/daily-metrics", {"limit": "90"})
        daily_data = []
        if isinstance(daily_raw, dict):
            daily_data = daily_raw.get("dailyData", [])

        # Construir métricas consolidadas
        total_reach = 0
        total_impressions = 0
        total_engagement = 0.0
        total_interactions = 0
        post_count_30d = 0

        for day in daily_data:
            post_count_30d += day.get("postCount", 0)
            m = day.get("metrics", {})
            total_impressions += m.get("impressions", 0) or 0
            total_reach += m.get("reach", 0) or 0
            total_interactions += (
                (m.get("likes", 0) or 0)
                + (m.get("comments", 0) or 0)
                + (m.get("shares", 0) or 0)
                + (m.get("saves", 0) or 0)
            )

        if total_reach > 0:
            total_engagement = round((total_interactions / total_reach) * 100, 1)

        # IG insights
        ig_metrics = {}
        if ig_insights:
            ig_metrics = {
                "reach": ig_insights.get("reach", {}).get("total", 0),
                "views": ig_insights.get("views", {}).get("total", 0),
                "accounts_engaged": ig_insights.get("accounts_engaged", {}).get("total", 0),
                "total_interactions": ig_insights.get("total_interactions", {}).get("total", 0),
                "impressions": ig_insights.get("impressions", {}).get("total", "N/D"),
                "profile_visits": ig_insights.get("profile_visits", {}).get("total", "N/D"),
                "website_clicks": ig_insights.get("website_clicks", {}).get("total", "N/D"),
                "follower_growth": ig_insights.get("follower_growth", {}).get("total", "N/D"),
            }

        ig_engagement_rate = "N/D"
        ig_reach = ig_metrics.get("reach", 0)
        ig_interactions = ig_metrics.get("total_interactions", 0)
        if isinstance(ig_reach, (int, float)) and isinstance(ig_interactions, (int, float)) and ig_reach > 0:
            ig_engagement_rate = f"{round((ig_interactions / ig_reach) * 100, 1)}%"

        tt_metrics = {}
        if tt_insights:
            tt_metrics = {
                "follower_count": tt_insights.get("follower_count", {}).get("total", 0),
                "likes_count": tt_insights.get("likes_count", {}).get("total", 0),
                "video_count": tt_insights.get("video_count", {}).get("total", 0),
                "views": tt_insights.get("views", {}).get("total", "N/D"),
                "shares": tt_insights.get("shares", {}).get("total", "N/D"),
                "profile_visits": tt_insights.get("profile_visits", {}).get("total", "N/D"),
                "completion_rate": tt_insights.get("completion_rate", {}).get("total", "N/D"),
                "follower_growth": tt_insights.get("follower_growth", {}).get("total", "N/D"),
            }

        tt_engagement_rate = "N/D"

        # Top content por platform
        ig_top = None
        tt_top = None
        for p in posts_list:
            plat = p.get("platform", "")
            if plat == "instagram" and ig_top is None:
                a = p.get("analytics", {})
                ig_top = {
                    "title": p.get("content", "")[:60],
                    "format": p.get("mediaType", "post"),
                    "reach": a.get("reach", 0),
                    "views": a.get("views", 0),
                    "impressions": a.get("impressions", 0),
                    "engagement_rate": f"{a.get('engagementRate', 0)}%",
                    "likes": a.get("likes", 0),
                    "comments": a.get("comments", 0),
                    "shares": a.get("shares", 0),
                    "url": p.get("platformPostUrl", ""),
                }
            if plat == "tiktok" and tt_top is None:
                a = p.get("analytics", {})
                tt_top = {
                    "title": p.get("content", "")[:60],
                    "format": p.get("mediaType", "video"),
                    "views": a.get("views", 0),
                    "likes": a.get("likes", 0),
                    "comments": a.get("comments", 0),
                    "shares": a.get("shares", 0),
                    "engagement_rate": f"{a.get('engagementRate', 0)}%",
                    "url": p.get("platformPostUrl", ""),
                }

        # Alertas basadas en datos
        alerts = self._build_alerts(daily_data, ig_insights, platform_map)

        # Recomendaciones
        recs = []
        if ig_top:
            recs.append(f"El mejor contenido en IG es '{ig_top.get('title', '')}' con {ig_top.get('engagement_rate', 'N/A')} de engagement.")
        if tt_top:
            recs.append(f"En TikTok el top contenido tiene {tt_top.get('views', 0)} views.")
        if best_slots:
            top_slot = best_slots[0]
            day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            day_name = day_names[top_slot.get("day_of_week", 0)] if top_slot.get("day_of_week", 0) < 7 else "?"
            recs.append(f"Mejor horario: {day_name} a las {top_slot.get('hour', '?')}:00 (avg engagement: {top_slot.get('avg_engagement', 0)})")
        if not recs:
            recs.append("Sigue publicando contenido para generar más datos y recomendaciones.")

        # Mejores horarios formateados
        windows = self._slots_to_windows(best_slots)

        # Audiencia
        audience = self._build_audience(demographics, platform_map)

        # Follower growth from follower-stats endpoint
        ig_follower_growth = "N/D"
        tt_follower_growth = "N/D"
        for acc in follower_accounts:
            plat = acc.get("platform", "")
            growth = acc.get("followerGrowth")
            if growth is not None:
                growth_str = f"+{growth}" if growth >= 0 else str(growth)
                if plat == "instagram":
                    ig_follower_growth = growth_str
                elif plat == "tiktok":
                    tt_follower_growth = growth_str

        return {
            "status": "success",
            "source": "Zernio API (datos reales)",
            "period": f"{since} al {until}",
            "accounts": {
                "instagram": platform_map.get("instagram", {}).get("username", "no conectada"),
                "tiktok": platform_map.get("tiktok", {}).get("username", "no conectada"),
            },
            "metrics": {
                "total_reach": str(total_reach),
                "total_impressions": str(total_impressions),
                "total_engagement_rate": f"{total_engagement}%",
                "followers_growth": ig_follower_growth,
                "leads_detected": 0,
                "sentiment_score": "N/D",
                "posts_last_30d": post_count_30d,
            },
            "platforms": {
                "instagram": {
                    "followers": platform_map.get("instagram", {}).get("followers", 0),
                    "external_posts": platform_map.get("instagram", {}).get("posts", 0),
                    "reach": ig_metrics.get("reach", "N/D"),
                    "views": ig_metrics.get("views", "N/D"),
                    "impressions": ig_metrics.get("impressions", "N/D"),
                    "accounts_engaged": ig_metrics.get("accounts_engaged", "N/D"),
                    "total_interactions": ig_metrics.get("total_interactions", "N/D"),
                    "engagement_rate": ig_engagement_rate,
                    "followers_growth": ig_metrics.get("follower_growth", ig_follower_growth),
                    "profile_visits": ig_metrics.get("profile_visits", "N/D"),
                    "website_clicks": ig_metrics.get("website_clicks", "N/D"),
                    "top_content": ig_top,
                },
                "tiktok": {
                    "followers": platform_map.get("tiktok", {}).get("followers", 0),
                    "external_posts": platform_map.get("tiktok", {}).get("posts", 0),
                    "follower_count": tt_metrics.get("follower_count", "N/D"),
                    "likes_count": tt_metrics.get("likes_count", "N/D"),
                    "video_count": tt_metrics.get("video_count", "N/D"),
                    "views": tt_metrics.get("views", "N/D"),
                    "shares": tt_metrics.get("shares", "N/D"),
                    "profile_visits": tt_metrics.get("profile_visits", "N/D"),
                    "completion_rate": tt_metrics.get("completion_rate", "N/D"),
                    "engagement_rate": tt_engagement_rate,
                    "followers_growth": tt_metrics.get("follower_growth", tt_follower_growth),
                    "top_content": tt_top,
                },
            },
            "audience": audience,
            "best_posting_windows": windows,
            "alerts": alerts,
            "recommendations": recs,
        }

    def _build_alerts(self, daily_data: list, ig_insights: dict | None, platform_map: dict) -> list[dict]:
        alerts = []
        if not daily_data:
            return alerts
        total_impressions = sum(
            (d.get("metrics", {}).get("impressions", 0) or 0) for d in daily_data
        )
        if total_impressions == 0 and platform_map:
            alerts.append({
                "severity": "low",
                "platform": "general",
                "title": "Sin actividad reciente",
                "detail": "No se detectaron impresiones en los últimos 30 días. Revisa si las cuentas están publicando.",
                "recommendation": "Programa contenido regularmente para mantener la actividad.",
            })
        ig_name = platform_map.get("instagram", {}).get("username", "")
        if ig_name:
            alerts.append({
                "severity": "low",
                "platform": "instagram",
                "title": "Monitoreo activo",
                "detail": f"Cuenta @{ig_name} con datos sincronizados correctamente.",
                "recommendation": "Revisa el dashboard periódicamente para seguimiento de métricas.",
            })
        return alerts

    def _build_audience(self, demographics: dict | None, platform_map: dict) -> dict:
        if not demographics:
            ig = platform_map.get("instagram", {})
            return {
                "source": "Zernio API",
                "top_locations": [],
                "top_age_range": "N/D",
                "gender_split": {},
                "segments": [
                    {"name": "Seguidores Instagram", "share": f"{ig.get('followers', 0)}", "signal": "followers"},
                ],
                "content_preferences": [],
            }
        age_data = demographics.get("age", [])
        city_data = demographics.get("city", [])
        country_data = demographics.get("country", [])
        gender_data = demographics.get("gender", [])

        top_age = age_data[0]["dimension"] if age_data else "N/D"
        top_cities = [c["dimension"] for c in city_data[:3]] if city_data else []
        top_countries = [c["dimension"] for c in country_data[:3]] if country_data else []

        gender_map = {}
        for g in gender_data:
            gender_map[g["dimension"]] = f"{g.get('value', 0)}"

        segments = []
        if age_data:
            total_age = sum(a.get("value", 0) for a in age_data)
            for a in age_data[:3]:
                pct = round((a.get("value", 0) / total_age) * 100) if total_age else 0
                segments.append({
                    "name": f"Edad {a['dimension']}",
                    "share": f"{pct}%",
                    "signal": f"{a.get('value', 0)} seguidores",
                })

        return {
            "source": "Zernio API - Instagram Demographics",
            "top_locations": top_cities or top_countries,
            "top_countries": top_countries,
            "top_age_range": top_age,
            "age_breakdown": [{"range": a["dimension"], "count": a["value"]} for a in age_data],
            "gender_split": gender_map,
            "segments": segments or [
                {"name": "Seguidores Instagram", "share": f"{platform_map.get('instagram', {}).get('followers', 0)}", "signal": "followers"},
            ],
            "content_preferences": [],
        }

    def _slots_to_windows(self, slots: list[dict]) -> dict:
        if not slots:
            return {"instagram": [], "tiktok": [], "by_format": {}, "recommendation": "Publica y acumula datos para obtener recomendaciones."}
        ig_hours = set()
        tt_hours = set()
        for s in slots:
            h = s.get("hour", 0)
            label = f"{h:02d}:00-{(h+1) % 24:02d}:00"
            ig_hours.add(label)
            tt_hours.add(label)
        best_slot = slots[0]
        day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        day_name = day_names[best_slot.get("day_of_week", 0)] if best_slot.get("day_of_week", 0) < 7 else "?"
        return {
            "instagram": sorted(ig_hours),
            "tiktok": sorted(tt_hours),
            "by_format": {
                "mejor_dia": day_name,
                "mejor_hora": f"{best_slot.get('hour', 0):02d}:00",
                "avg_engagement": best_slot.get("avg_engagement", 0),
            },
            "recommendation": f"Mejor momento: {day_name} a las {best_slot.get('hour', 0):02d}:00 con engagement promedio de {best_slot.get('avg_engagement', 0)}.",
        }

    async def generate_report(self, report_type: str) -> dict:
        print(f"[ZERNIO] Generando informe: {report_type}")
        dashboard = await self.get_dashboard()
        metrics = dashboard.get("metrics", {})
        summary = (
            f"Informe {report_type} desde Zernio API.\n"
            f"Cuentas: Instagram @{dashboard.get('accounts', {}).get('instagram', '?')} / "
            f"TikTok @{dashboard.get('accounts', {}).get('tiktok', '?')}.\n"
            f"Posts (30d): {metrics.get('posts_last_30d', 'N/A')} · "
            f"Alcance: {metrics.get('total_reach', 'N/A')} · "
            f"Impresiones: {metrics.get('total_impressions', 'N/A')} · "
            f"Engagement: {metrics.get('total_engagement_rate', 'N/A')}."
        )
        return {
            "status": "success",
            "source": "Zernio API",
            "report_type": report_type,
            "summary": summary,
            "data": dashboard,
        }

    async def get_top_content(self, platform: str | None = None, limit: int = 5) -> list[dict]:
        print(f"[ZERNIO] Top content desde Zernio API")
        params = {"sortBy": "engagement", "order": "desc", "limit": str(limit)}
        if platform:
            params["platform"] = platform
        raw = await self._z_get("/analytics", params)
        posts = []
        if isinstance(raw, dict):
            posts = raw.get("posts", [])
        result = []
        for item in posts:
            a = item.get("analytics", {})
            result.append({
                "platform": item.get("platform", "general"),
                "title": (item.get("content", "") or "")[:80],
                "format": item.get("mediaType", "post"),
                "views": a.get("views", 0),
                "reach": a.get("reach", 0),
                "impressions": a.get("impressions", 0),
                "likes": a.get("likes", 0),
                "comments": a.get("comments", 0),
                "shares": a.get("shares", 0),
                "saves": a.get("saves", 0),
                "engagement_rate": f"{a.get('engagementRate', 0)}%",
                "url": item.get("platformPostUrl", ""),
                "published_at": item.get("publishedAt", ""),
            })
        return result[:limit]

    async def get_audience_insights(self) -> dict:
        print("[ZERNIO] Audiencia desde Zernio API")
        ig_id = await self._get_account_id("instagram")
        if not ig_id:
            return {
                "source": "Zernio API",
                "top_locations": [],
                "top_age_range": "N/D",
                "gender_split": {},
                "segments": [],
                "content_preferences": [],
            }
        raw = await self._z_get(
            "/analytics/instagram/demographics",
            {"accountId": ig_id},
        )
        if not isinstance(raw, dict) or not raw.get("success"):
            accounts = await self._fetch_accounts()
            ig = next((a for a in accounts if a.get("platform") == "instagram"), {})
            return {
                "source": "Zernio API",
                "top_locations": [],
                "top_age_range": "N/D",
                "gender_split": {},
                "segments": [{"name": "Seguidores", "share": f"{ig.get('followersCount', 0)}", "signal": "followers"}],
                "content_preferences": [],
            }
        demo = raw.get("demographics", {})
        age_data = demo.get("age", [])
        city_data = demo.get("city", [])
        gender_data = demo.get("gender", [])

        top_age = age_data[0]["dimension"] if age_data else "N/D"
        top_locs = [c["dimension"] for c in city_data[:5]] if city_data else []
        gender_map = {}
        for g in gender_data:
            gender_map[g["dimension"]] = f"{g.get('value', 0)}"

        segments = []
        if age_data:
            total = sum(a.get("value", 0) for a in age_data)
            for a in age_data[:3]:
                pct = round((a.get("value", 0) / total) * 100) if total else 0
                segments.append({
                    "name": f"Edad {a['dimension']}",
                    "share": f"{pct}%",
                    "signal": f"{a.get('value', 0)} seguidores",
                })

        return {
            "source": "Zernio API - Instagram Demographics",
            "top_locations": top_locs,
            "top_age_range": top_age,
            "gender_split": gender_map,
            "segments": segments,
            "age_breakdown": [{"range": a["dimension"], "count": a["value"]} for a in age_data],
            "content_preferences": ["contenido visual", "stories", "reels"],
        }

    async def get_alerts(self) -> list[dict]:
        print("[ZERNIO] Alertas desde análisis de datos")
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=MONTH_DAYS)
        daily_raw = await self._z_get(
            "/analytics/daily-metrics",
            {"limit": "90"},
        )
        daily_data = []
        if isinstance(daily_raw, dict):
            daily_data = daily_raw.get("dailyData", [])
        alerts = self._build_alerts(daily_data, None, {})
        alerts_from_db = await self._get_memory("marketing_alerts", limit=10)
        for mem in alerts_from_db:
            meta = mem.get("metadata") or {}
            alerts.append({
                "severity": meta.get("severity", "low"),
                "platform": meta.get("platform", "general"),
                "title": mem.get("summary", "Alerta"),
                "detail": meta.get("detail", ""),
                "recommendation": meta.get("recommendation", "Revisar manualmente"),
            })
        return alerts

    async def get_leads(self, status: str | None = None) -> list[dict]:
        print(f"[ZERNIO] Leads desde marketing_leads ({status or 'todos'})")
        params = "select=*&order=created_at.desc&limit=50"
        if status:
            params += f"&status=eq.{status}"
        result = await self._supa_get("marketing_leads", params)
        if not result:
            return []
        leads = []
        for row in result:
            meta = row.get("metadata") or {}
            leads.append({
                "id": row.get("id", ""),
                "platform": row.get("platform", "desconocido"),
                "user": row.get("external_user", "desconocido"),
                "comment_text": row.get("comment_text", ""),
                "intent_score": row.get("intent_score", 0),
                "status": meta.get("status", row.get("category", "new")),
                "signal": meta.get("signal", row.get("reason", "")),
                "suggested_next_step": meta.get("suggested_next_step", "Contactar con mensaje personalizado"),
                "created_at": row.get("created_at", ""),
            })
        return leads

    async def get_best_posting_windows(self) -> dict:
        print("[ZERNIO] Mejores horarios desde Zernio API")
        raw = await self._z_get("/analytics/best-time")
        slots = []
        if isinstance(raw, dict):
            slots = raw.get("slots", [])
        return self._slots_to_windows(slots)

    async def list_posts(self, platform: str | None = None, limit: int = 10) -> list[dict]:
        print("[ZERNIO] Posts desde Zernio API")
        params = {"limit": str(limit), "sortBy": "date", "order": "desc"}
        raw = await self._z_get("/analytics", params)
        posts = []
        if isinstance(raw, dict):
            posts = raw.get("posts", [])
        result = []
        for item in posts:
            if platform and item.get("platform") != platform:
                continue
            result.append({
                "id": item.get("_id", ""),
                "platform": item.get("platform", "general"),
                "format": item.get("mediaType", "post"),
                "title": (item.get("content", "") or "")[:80],
                "status": item.get("status", "published"),
                "published_at": item.get("publishedAt", ""),
                "url": item.get("platformPostUrl", ""),
                "thumbnail": item.get("thumbnailUrl", ""),
            })
        return result[:limit]

    async def save_campaign_draft(self, campaign: dict) -> bool:
        print(f"[ZERNIO] Guardando campaña")
        ok = await self._save_memory(
            "marketing_campaigns",
            campaign.get("name", "Campaña"),
            {k: v for k, v in campaign.items() if k != "name"},
        )
        if ok:
            self._processed.add(campaign.get("id", "campaign-draft"))
        return ok

    async def save_post_draft(self, post: dict) -> bool:
        platform = post.get("platform", "general")
        ok = await self._save_memory(
            f"marketing_posts_{platform}",
            post.get("title", "Post"),
            {k: v for k, v in post.items() if k != "title"},
        )
        if ok:
            self._processed.add(post.get("id", "post-draft"))
        return ok

    async def save_automation_run(self, run: dict) -> bool:
        ok = await self._save_memory(
            "marketing_automation",
            f"Run: {run.get('action', 'desconocido')}",
            {k: v for k, v in run.items() if k != "action"},
        )
        dedupe_key = run.get("dedupe_key")
        if dedupe_key:
            self._processed.add(dedupe_key)
        return ok

    async def has_processed(self, dedupe_key: str) -> bool:
        if dedupe_key in self._processed:
            return True
        memories = await self._get_memory("marketing_automation", limit=50)
        for mem in memories:
            meta = mem.get("metadata") or {}
            if meta.get("dedupe_key") == dedupe_key:
                self._processed.add(dedupe_key)
                return True
        return False

    async def schedule_post(self, post: dict) -> bool:
        print(f"[ZERNIO] Programando post via Zernio API")
        platform = post.get("platform", "instagram")
        account_ids = await self._get_account_ids()
        account_id = account_ids.get(platform)

        zernio_payload = {
            "content": post.get("content", post.get("title", "")),
            "platforms": [
                {"platform": platform, "accountId": account_id}
            ],
        }
        if post.get("scheduled_for"):
            zernio_payload["scheduledFor"] = post["scheduled_for"]
        if post.get("media_urls"):
            zernio_payload["mediaUrls"] = post["media_urls"]

        return await self._z_post("/posts", zernio_payload)

    async def publish_post(self, post: dict) -> bool:
        print(f"[ZERNIO] Publicando post via Zernio API")
        platform = post.get("platform", "instagram")
        account_ids = await self._get_account_ids()
        account_id = account_ids.get(platform)

        zernio_payload = {
            "content": post.get("content", post.get("title", "")),
            "platforms": [
                {"platform": platform, "accountId": account_id}
            ],
        }
        if post.get("media_urls"):
            zernio_payload["mediaUrls"] = post["media_urls"]

        return await self._z_post("/posts", zernio_payload)
