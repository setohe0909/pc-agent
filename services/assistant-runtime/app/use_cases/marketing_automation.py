import hashlib
import json
from typing import Any

from app.domain.marketing.models import AutomationAction, AutomationResult, CampaignPlan, PostDraft
from app.domain.marketing.policies import AutonomyPolicy
from app.domain.ports.llm import LLMPort
from app.domain.ports.marketing import MarketingPort
from app.domain.ports.memory import MemoryPort


class MarketingAutomationService:
    def __init__(self, llm: LLMPort, marketing: MarketingPort, memory: MemoryPort):
        self.llm = llm
        self.marketing = marketing
        self.memory = memory

    async def plan_campaign(self, topic: str, payload: dict | None = None, context: str = "") -> dict:
        payload = payload or {}
        policy = AutonomyPolicy.from_payload(payload)
        if not policy.automation_enabled:
            return {"status": "error", "message": "La automatización de marketing está desactivada por MARKETER_AUTOMATION_ENABLED=false."}
        campaign = await self._build_campaign_plan(topic, context)
        action = AutomationAction(
            action_type="approve_campaign",
            resource_type="campaign",
            payload=campaign.to_dict(),
            dedupe_key=f"campaign:{campaign.id}",
            external_write=True,
        )

        if payload.get("is_approved"):
            await self.marketing.save_automation_run({
                "dedupe_key": action.dedupe_key,
                "action_type": action.action_type,
                "status": "approved",
                "resource": campaign.to_dict(),
            })
            return AutomationResult(
                status="success",
                message=self._format_campaign(campaign, approved=True),
                actions=[action],
                campaign=campaign,
            ).to_response()

        if not await self.marketing.has_processed(action.dedupe_key):
            await self.marketing.save_campaign_draft(campaign.to_dict())
            await self.marketing.save_automation_run({
                "dedupe_key": action.dedupe_key,
                "action_type": action.action_type,
                "status": "draft",
                "autonomy_level": policy.autonomy_level,
                "resource": campaign.to_dict(),
            })

        return AutomationResult(
            status="requires_approval",
            message=self._format_campaign(campaign, approved=False),
            actions=[action],
            campaign=campaign,
            requires_approval=True,
        ).to_response()

    async def generate_post_queue(self, topic: str, payload: dict | None = None, context: str = "") -> dict:
        payload = payload or {}
        policy = AutonomyPolicy.from_payload(payload)
        if not policy.automation_enabled:
            return {"status": "error", "message": "La automatización de marketing está desactivada por MARKETER_AUTOMATION_ENABLED=false."}
        campaign = await self._build_campaign_plan(topic, context)
        posts = await self._build_post_drafts(campaign)
        actions = [
            AutomationAction(
                action_type="schedule_post",
                resource_type="post",
                payload=post.to_dict(),
                dedupe_key=f"post:{post.id}",
                external_write=True,
            )
            for post in posts
        ]

        if payload.get("is_approved"):
            allowed, reason = policy.can_execute_write(approved=True)
            if allowed:
                for post in posts:
                    await self.marketing.schedule_post(post.to_dict())
                status_note = "Posts aprobados y enviados a programación vía Zernio."
            else:
                status_note = f"Posts aprobados como borradores. No se programaron: {reason}"
            await self.marketing.save_automation_run({
                "dedupe_key": f"post-queue:{campaign.id}",
                "action_type": "approve_posts",
                "status": "approved",
                "write_allowed": allowed,
                "reason": reason,
                "posts": [post.to_dict() for post in posts],
            })
            return AutomationResult(
                status="success",
                message=self._format_posts(posts, status_note),
                actions=actions,
                campaign=campaign,
                posts=posts,
            ).to_response()

        for post in posts:
            dedupe_key = f"post:{post.id}"
            if not await self.marketing.has_processed(dedupe_key):
                await self.marketing.save_post_draft(post.to_dict())
                await self.marketing.save_automation_run({
                    "dedupe_key": dedupe_key,
                    "action_type": "post_draft",
                    "status": "draft",
                    "autonomy_level": policy.autonomy_level,
                    "resource": post.to_dict(),
                })

        return AutomationResult(
            status="requires_approval",
            message=self._format_posts(posts, "Requiere aprobación para programar/publicar. En MVP asistido no se publica automáticamente."),
            actions=actions,
            campaign=campaign,
            posts=posts,
            requires_approval=True,
        ).to_response()

    async def respond_to_comments(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        policy = AutonomyPolicy.from_payload(payload)
        if not policy.automation_enabled:
            return {"status": "error", "message": "La automatización de marketing está desactivada por MARKETER_AUTOMATION_ENABLED=false."}
        comments = await self.marketing.get_comments("instagram", "latest_post")
        drafts = []
        for comment in comments:
            prompt = (
                "Actúa como Community Manager. Redacta una respuesta breve, cálida y orientada a marca "
                f"para este comentario: \"{comment.get('text', '')}\"."
            )
            reply = await self.llm.chat(prompt)
            drafts.append({"platform": "instagram", "comment_id": comment.get("id"), "comment": comment.get("text"), "reply": reply})

        if payload.get("is_approved"):
            allowed, reason = policy.can_execute_write(approved=True)
            if allowed:
                for draft in drafts:
                    await self.marketing.reply_to_comment(draft["platform"], draft["comment_id"], draft["reply"])
                return {"status": "success", "message": self._format_reply_drafts(drafts, "Respuestas publicadas vía Zernio.")}
            return {"status": "success", "message": self._format_reply_drafts(drafts, f"Aprobación recibida, pero no publiqué: {reason}")}

        return {"status": "requires_approval", "message": self._format_reply_drafts(drafts, "Borradores listos. Requieren aprobación antes de publicar.")}

    async def process_lead_magnets(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        policy = AutonomyPolicy.from_payload(payload)
        if not policy.automation_enabled:
            return {"status": "error", "message": "La automatización de marketing está desactivada por MARKETER_AUTOMATION_ENABLED=false."}
        magnets = {
            "GUIA": {"link": "https://brand.com/free-guide", "name": "Guía de Estilo"},
            "INFO": {"link": "https://brand.com/catalog", "name": "Catálogo 2026"},
        }
        comments = await self.marketing.get_comments("instagram", "latest_post")
        drafts = []
        for comment in comments:
            text_upper = comment.get("text", "").upper()
            for trigger, data in magnets.items():
                if trigger in text_upper:
                    drafts.append({
                        "platform": "instagram",
                        "user": comment.get("user"),
                        "trigger": trigger,
                        "dm": f"¡Hola! Gracias por tu interés. Aquí tienes tu {data['name']}: {data['link']}",
                    })
                    break

        if payload.get("is_approved"):
            allowed, reason = policy.can_execute_write(approved=True)
            if allowed:
                for draft in drafts:
                    await self.marketing.send_dm(draft["platform"], draft["user"], draft["dm"])
                return {"status": "success", "message": self._format_dm_drafts(drafts, "DMs enviados vía Zernio.")}
            return {"status": "success", "message": self._format_dm_drafts(drafts, f"Aprobación recibida, pero no envié DMs: {reason}")}

        return {"status": "requires_approval", "message": self._format_dm_drafts(drafts, "DMs en borrador. Requieren aprobación antes de enviar.")}

    async def qualify_leads(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        policy = AutonomyPolicy.from_payload(payload)
        if not policy.automation_enabled:
            return {"status": "error", "message": "La automatización de marketing está desactivada por MARKETER_AUTOMATION_ENABLED=false."}
        comments = await self.marketing.get_comments("instagram", "latest_post")
        leads = []
        for comment in comments:
            text = comment.get("text", "")
            hot_signal = any(word in text.upper() for word in ("INFO", "PRECIO", "COMPRAR", "QUIERO", "CATALOGO"))
            if hot_signal:
                leads.append({
                    "platform": "instagram",
                    "external_user": comment.get("user"),
                    "comment_text": text,
                    "intent_score": 8,
                    "category": "hot",
                    "reason": "Intención detectada por palabra clave",
                })

        if payload.get("is_approved"):
            allowed, reason = policy.can_execute_write(approved=True)
            if allowed:
                for lead in leads:
                    await self.marketing.save_lead(lead)
                    await self.memory.save_memory(category="marketing_lead", summary=f"Lead cualificado detectado: {lead['external_user']} ({lead['category']})")
                return {"status": "success", "message": self._format_leads(leads, "Leads guardados.")}
            return {"status": "success", "message": self._format_leads(leads, f"Aprobación recibida, pero no guardé leads: {reason}")}

        return {"status": "requires_approval", "message": self._format_leads(leads, "Leads detectados como borrador. Requieren aprobación antes de guardar.")}

    async def _build_campaign_plan(self, topic: str, context: str) -> CampaignPlan:
        dashboard = await self.marketing.get_dashboard()
        top_content = await self.marketing.get_top_content(limit=5)
        audience = await self.marketing.get_audience_insights()
        best_hours = await self.marketing.get_best_posting_windows()
        topic = topic.strip() or "campaña de crecimiento"
        campaign_id = self._stable_id("campaign", topic)
        audience_label = self._audience_label(audience)
        pillars = self._pillars(top_content)
        calendar = [
            {"day": "Día 1", "channel": "Instagram", "format": "Reel", "theme": pillars[0], "window": self._first_window(best_hours, "instagram")},
            {"day": "Día 2", "channel": "TikTok", "format": "Video educativo", "theme": pillars[1], "window": self._first_window(best_hours, "tiktok")},
            {"day": "Día 4", "channel": "Instagram", "format": "Carrusel", "theme": pillars[2], "window": self._first_window(best_hours, "instagram", index=1)},
            {"day": "Día 6", "channel": "TikTok", "format": "Storytelling corto", "theme": pillars[0], "window": self._first_window(best_hours, "tiktok", index=1)},
        ]
        kpis = [
            f"Alcance objetivo: {dashboard.get('metrics', {}).get('total_reach', 'N/D')}",
            "Engagement objetivo: +10% vs promedio actual",
            "Leads objetivo: 15 conversaciones calificadas",
        ]
        return CampaignPlan(
            id=campaign_id,
            topic=topic,
            goal=f"Impulsar {topic} con crecimiento orgánico y captación de leads.",
            audience=audience_label,
            channels=["instagram", "tiktok"],
            pillars=pillars,
            calendar=calendar,
            kpis=kpis,
            source_insights={"dashboard": dashboard, "top_content": top_content, "audience": audience, "best_hours": best_hours, "context": context[:500]},
        )

    async def _build_post_drafts(self, campaign: CampaignPlan) -> list[PostDraft]:
        best_hours = campaign.source_insights.get("best_hours", {})
        return [
            PostDraft(
                id=self._stable_id("post", campaign.id, "instagram-reel"),
                campaign_id=campaign.id,
                platform="instagram",
                format="reel",
                hook=f"Lo que nadie te muestra sobre {campaign.topic}",
                caption=f"Una mirada breve y útil a {campaign.topic}. Guarda este post si quieres aplicarlo esta semana.",
                cta="Comenta INFO para recibir la guía.",
                hashtags=["#marketing", "#instagram", "#crecimiento"],
                scheduled_window=self._first_window(best_hours, "instagram"),
                metric_goal="Alcance y comentarios con intención",
            ),
            PostDraft(
                id=self._stable_id("post", campaign.id, "instagram-carousel"),
                campaign_id=campaign.id,
                platform="instagram",
                format="carousel",
                hook=f"Checklist rápido para {campaign.topic}",
                caption=f"Desliza y usa esta guía para convertir {campaign.topic} en una acción concreta.",
                cta="Guárdalo y compártelo con tu equipo.",
                hashtags=["#contenido", "#estrategia", "#marca"],
                scheduled_window=self._first_window(best_hours, "instagram", index=1),
                metric_goal="Guardados y shares",
            ),
            PostDraft(
                id=self._stable_id("post", campaign.id, "tiktok-educativo"),
                campaign_id=campaign.id,
                platform="tiktok",
                format="video educativo",
                hook=f"3 errores al trabajar {campaign.topic}",
                caption=f"Evita estos errores y convierte {campaign.topic} en una oportunidad real.",
                cta="Síguenos para la parte 2.",
                hashtags=["#tiktokmarketing", "#aprende", "#negocio"],
                scheduled_window=self._first_window(best_hours, "tiktok"),
                metric_goal="Views y completion rate",
            ),
            PostDraft(
                id=self._stable_id("post", campaign.id, "tiktok-story"),
                campaign_id=campaign.id,
                platform="tiktok",
                format="storytelling corto",
                hook=f"Así nació la idea de {campaign.topic}",
                caption=f"Historia breve con aprendizaje práctico para la comunidad.",
                cta="Comenta qué parte quieres ver en detalle.",
                hashtags=["#storytelling", "#marca", "#creadores"],
                scheduled_window=self._first_window(best_hours, "tiktok", index=1),
                metric_goal="Retención y comentarios",
            ),
        ]

    def _format_campaign(self, campaign: CampaignPlan, approved: bool) -> str:
        status = "Aprobada como campaña asistida. No se publicó ni programó nada." if approved else "Requiere aprobación para activar. No se publicó ni programó nada."
        calendar = "\n".join(
            f"- {item['day']}: {item['channel']} · {item['format']} · {item['theme']} · {item['window']}"
            for item in campaign.calendar
        )
        pillars = ", ".join(campaign.pillars)
        kpis = "\n".join(f"- {kpi}" for kpi in campaign.kpis)
        return (
            f"## 📣 Campaña Zernio: {campaign.topic}\n"
            f"**Estado:** {status}\n\n"
            f"**Objetivo:** {campaign.goal}\n"
            f"**Audiencia:** {campaign.audience}\n"
            f"**Canales:** {', '.join(campaign.channels)}\n"
            f"**Pilares:** {pillars}\n\n"
            f"### Calendario propuesto\n{calendar}\n\n"
            f"### KPIs\n{kpis}"
        )

    def _format_posts(self, posts: list[PostDraft], note: str) -> str:
        lines = [f"## 🗂️ Borradores de posts Zernio\n**Estado:** {note}\n"]
        for index, post in enumerate(posts, start=1):
            lines.append(
                f"{index}. **{post.platform} · {post.format}** ({post.scheduled_window})\n"
                f"   - Hook: {post.hook}\n"
                f"   - Caption: {post.caption}\n"
                f"   - CTA: {post.cta}\n"
                f"   - Hashtags: {' '.join(post.hashtags)}\n"
                f"   - Métrica objetivo: {post.metric_goal}"
            )
        return "\n".join(lines)

    def _format_reply_drafts(self, drafts: list[dict], note: str) -> str:
        if not drafts:
            return "No encontré comentarios recientes para responder."
        lines = [f"## 💬 Borradores de respuesta\n**Estado:** {note}\n"]
        for draft in drafts:
            lines.append(f"- **Comentario:** {draft['comment']}\n  **Respuesta:** {draft['reply']}")
        return "\n".join(lines)

    def _format_dm_drafts(self, drafts: list[dict], note: str) -> str:
        if not drafts:
            return "No encontré comentarios con palabras clave de Lead Magnet (GUIA, INFO)."
        lines = [f"## 🧲 Borradores de DM\n**Estado:** {note}\n"]
        for draft in drafts:
            lines.append(f"- **{draft['user']}** ({draft['trigger']}): {draft['dm']}")
        return "\n".join(lines)

    def _format_leads(self, leads: list[dict], note: str) -> str:
        if not leads:
            return "No se encontraron leads de alta intención en las interacciones recientes."
        lines = [f"## 🎯 Leads cualificados\n**Estado:** {note}\n"]
        for lead in leads:
            lines.append(f"- **{lead['external_user']}**: {lead['comment_text']} · Score: {lead['intent_score']}/10")
        return "\n".join(lines)

    def _audience_label(self, audience: dict[str, Any]) -> str:
        segments = audience.get("segments", [])
        if segments:
            return f"{segments[0].get('name', 'Audiencia principal')} ({segments[0].get('share', 'N/D')})"
        return f"Audiencia principal {audience.get('top_age_range', 'N/D')}"

    def _pillars(self, top_content: list[dict]) -> list[str]:
        topics = [item.get("topic") for item in top_content if item.get("topic")]
        defaults = ["educativo", "storytelling", "prueba social"]
        pillars = []
        for topic in topics + defaults:
            if topic not in pillars:
                pillars.append(topic)
        return pillars[:3]

    def _first_window(self, windows: dict, platform: str, index: int = 0) -> str:
        values = windows.get(platform, [])
        if not values:
            return "Por definir"
        return values[min(index, len(values) - 1)]

    async def publish_post(self, content: str, media: list[str] | None = None,
                           platform: str = "instagram",
                           scheduled_for: str | None = None,
                           payload: dict | None = None) -> dict:
        payload = payload or {}

        if not payload.get("is_approved"):
            enhanced_desc = await self._enhance_description(content)
            hashtags = await self._generate_hashtags(enhanced_desc)
            caption = f"{enhanced_desc}\n\n{' '.join(hashtags)}"
            return {
                "status": "requires_approval",
                "requires_approval": True,
                "message": (
                    f"📝 **Sugerencia de publicación para {platform}:**\n\n"
                    f"{enhanced_desc}\n\n"
                    f"**Hashtags:** {' '.join(hashtags)}"
                ),
                "suggestion": {
                    "enhanced_description": enhanced_desc,
                    "hashtags": hashtags,
                    "caption": caption,
                },
            }

        suggestion = payload.get("suggestion")
        if suggestion:
            caption = suggestion.get("caption", content)
        else:
            hashtags = await self._generate_hashtags(content)
            caption = f"{content}\n\n{' '.join(hashtags)}"

        media_urls = []
        if media:
            for b64_data in media:
                media_urls.append(f"data:image/png;base64,{b64_data}")
        post_data = {
            "platform": platform,
            "content": caption,
            "media_urls": media_urls,
        }
        if scheduled_for:
            post_data["scheduled_for"] = scheduled_for
            ok = await self.marketing.schedule_post(post_data)
        else:
            ok = await self.marketing.publish_post(post_data)
        if ok:
            return {
                "status": "success",
                "message": f"Post {'programado' if scheduled_for else 'publicado'} en {platform}.\n\n{caption}",
            }
        return {"status": "error", "message": f"No se pudo {'programar' if scheduled_for else 'publicar'} el post en {platform}."}

    async def _enhance_description(self, content: str) -> str:
        prompt = (
            "Eres un copywriter experto en marketing para Instagram y TikTok en español. "
            "Mejora la siguiente descripción para un post, haciéndola más atractiva, "
            "con llamada a la acción y emojis relevantes. "
            "Devuelve SOLO el texto mejorado, sin explicaciones ni hashtags.\n\n"
            f"Descripción original: {content}"
        )
        try:
            enhanced = await self.llm.chat(prompt)
            return enhanced.strip()
        except Exception:
            return content

    async def _generate_hashtags(self, content: str) -> list[str]:
        prompt = (
            "Genera exactamente 5 hashtags relevantes en español para este contenido de Instagram/TikTok. "
            "Devuelve SOLO los hashtags separados por espacios, sin números ni viñetas, sin explicación.\n\n"
            f"Contenido: {content}"
        )
        try:
            raw = await self.llm.chat(prompt)
            tags = [w.strip() for w in raw.replace("#", "").split() if w.strip()]
            return [f"#{t}" for t in tags[:5]]
        except Exception:
            return ["#marketing", "#contenido", "#crecimiento", "#trending", "#viral"]

    def _stable_id(self, *parts: str) -> str:
        raw = json.dumps(parts, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        return f"mkt-{digest}"
