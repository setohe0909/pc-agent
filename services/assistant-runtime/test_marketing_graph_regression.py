import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.adapters.open_claw import OpenClawLLMAdapter
from app.main import ActionType, AssistantRequest, Source, _format_internal_error
from app.use_cases.marketing_graph import MarketingGraph


class FakeLLM:
    async def chat(self, *args, **kwargs):
        prompt = args[0] if args else ""
        if "Clasifica el sentimiento" in prompt:
            return "POSITIVE"
        return "respuesta generica"

    async def analyze_trade(self, *args, **kwargs):
        return {}

    async def get_tools_response(self, *args, **kwargs):
        raise AssertionError("No deberia consultar al LLM para dashboards explicitos")

    async def generate_image(self, *args, **kwargs):
        return ""


class FakeMemory:
    async def get_context(self, user_id: str):
        return ""

    async def save_interaction(self, user_id: str, data: dict) -> None:
        return None

    async def save_memory(self, category: str, summary: str) -> bool:
        return True


class FakeMarketing:
    def __init__(self):
        self.dashboard_calls = 0
        self.replies = []
        self.dms = []
        self.saved_leads = []
        self.campaign_drafts = []
        self.post_drafts = []
        self.automation_runs = []
        self.scheduled_posts = []
        self.published_posts = []
        self.processed = set()

    async def get_comments(self, platform: str, post_id: str):
        return [
            {"id": "c1", "user": "user1", "text": "Me encanta este diseño!"},
            {"id": "c2", "user": "user2", "text": "INFO por favor"},
        ]

    async def reply_to_comment(self, platform: str, comment_id: str, text: str):
        self.replies.append((platform, comment_id, text))
        return True

    async def send_dm(self, platform: str, user_id: str, text: str):
        self.dms.append((platform, user_id, text))
        return True

    async def get_competitor_data(self, platform: str, competitor_handle: str):
        return {"handle": competitor_handle, "recent_posts": [{"text": "post", "engagement": "high"}]}

    async def save_lead(self, lead_data: dict):
        self.saved_leads.append(lead_data)
        return True

    async def get_dashboard(self):
        self.dashboard_calls += 1
        return {
            "status": "success",
            "source": "Zernio Analytics",
            "period": "Últimos 30 días",
            "accounts": {"instagram": "@brand_oficial", "tiktok": "@brand_tok"},
            "metrics": {
                "total_reach": "184.2K",
                "total_impressions": "312.7K",
                "total_engagement_rate": "6.4%",
                "followers_growth": "+14.1%",
                "leads_detected": 28,
                "sentiment_score": "8.9/10",
            },
            "platforms": {
                "instagram": {
                    "followers_growth": "+12.5%",
                    "reach": "96.4K",
                    "impressions": "171.8K",
                    "engagement_rate": "5.8%",
                    "profile_visits": "4.1K",
                    "website_clicks": 342,
                    "top_content": {"title": "Reel_Zernio_Integration", "reach": "38.2K", "engagement_rate": "8.1%"},
                },
                "tiktok": {
                    "followers_growth": "+16.8%",
                    "views": "142.6K",
                    "engagement_rate": "7.2%",
                    "completion_rate": "41%",
                    "shares": 1180,
                    "profile_visits": "3.6K",
                    "top_content": {"title": "Behind_the_brand_process", "views": "54.9K", "engagement_rate": "9.4%"},
                },
            },
            "audience": {
                "top_locations": ["Bogotá", "Medellín"],
                "top_age_range": "25-34",
                "best_posting_windows": ["12:00-14:00", "19:00-21:00"],
            },
            "recommendations": ["Duplicar el formato ganador en TikTok."],
        }

    async def generate_report(self, report_type: str):
        return {"status": "success", "summary": "ok", "link": "#"}

    async def get_top_content(self, platform=None, limit=5):
        return [
            {"platform": "tiktok", "title": "Top TikTok", "format": "video", "views": "54.9K", "engagement_rate": "9.4%", "shares": 100, "saves": 50, "topic": "educativo"},
            {"platform": "instagram", "title": "Top Reel", "format": "reel", "reach": "38.2K", "engagement_rate": "8.1%", "shares": 80, "saves": 70, "topic": "producto"},
        ][:limit]

    async def get_audience_insights(self):
        return {
            "top_locations": ["Bogotá", "Medellín"],
            "top_age_range": "25-34",
            "segments": [{"name": "Compradores", "share": "38%", "signal": "INFO"}],
            "best_posting_windows": ["12:00-14:00"],
            "content_preferences": ["educativo"],
        }

    async def get_alerts(self):
        return [{"severity": "high", "platform": "tiktok", "title": "Oportunidad", "detail": "Views altas", "recommendation": "Mejorar CTA"}]

    async def get_leads(self, status=None):
        return [{"platform": "instagram", "user": "lead", "intent_score": 9, "status": "hot", "signal": "INFO", "suggested_next_step": "Enviar catálogo"}]

    async def get_best_posting_windows(self):
        return {
            "instagram": ["12:00-14:00"],
            "tiktok": ["18:00-22:00"],
            "by_format": {"reels": "12:30"},
            "recommendation": "Publicar al mediodía.",
        }

    async def list_posts(self, platform=None, limit=10):
        return [{"id": "post-1", "platform": "instagram", "format": "reel"}][:limit]

    async def save_campaign_draft(self, campaign: dict):
        self.campaign_drafts.append(campaign)
        self.processed.add(campaign.get("id"))
        return True

    async def save_post_draft(self, post: dict):
        self.post_drafts.append(post)
        self.processed.add(post.get("id"))
        return True

    async def save_automation_run(self, run: dict):
        self.automation_runs.append(run)
        if run.get("dedupe_key"):
            self.processed.add(run["dedupe_key"])
        return True

    async def has_processed(self, dedupe_key: str):
        return dedupe_key in self.processed

    async def schedule_post(self, post: dict):
        self.scheduled_posts.append(post)
        return True

    async def publish_post(self, post: dict):
        self.published_posts.append(post)
        return True


class MarketingGraphRegressionTests(unittest.TestCase):
    def test_dashboard_prompt_executes_zernio_without_llm_tool_detection(self):
        async def scenario():
            marketing = FakeMarketing()
            graph = MarketingGraph(llm=FakeLLM(), memory=FakeMemory(), marketing=marketing)

            result = await graph.run(
                prompt="Genera un dashboard de mis metricas actuales",
                payload={"sub_command": "chat"},
            )

            self.assertEqual(result["status"], "success")
            self.assertIn("Dashboard Zernio", result["message"])
            self.assertIn("Instagram", result["message"])
            self.assertIn("TikTok", result["message"])
            self.assertIn("Próximas acciones", result["message"])
            self.assertIn("dashboard", result)
            self.assertEqual(marketing.dashboard_calls, 1)

        asyncio.run(scenario())

    def test_gemini_tool_schema_uses_uppercase_types(self):
        adapter = OpenClawLLMAdapter()

        tools = [
            {
                "name": "generate_report",
                "description": "Genera un informe",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string"},
                    },
                    "required": ["report_type"],
                },
            }
        ]

        converted = adapter._to_gemini_tools(tools)

        self.assertEqual(converted[0]["parameters"]["type"], "OBJECT")
        self.assertEqual(
            converted[0]["parameters"]["properties"]["report_type"]["type"],
            "STRING",
        )
        self.assertEqual(tools[0]["parameters"]["type"], "object")

    def test_existing_marketer_subcommands_still_execute(self):
        async def scenario():
            commands = [
                "respond",
                "research",
                "status",
                "qualify",
                "magnet",
                "funnel",
                "trends",
                "sentiment",
                "collab",
                "memory",
                "report",
                "top-content",
                "audience",
                "alerts",
                "comments",
                "negative-comments",
                "reply-drafts",
                "leads",
                "content-plan",
                "repurpose",
                "best-hours",
                "competitors",
                "campaign",
                "posts",
            ]

            for command in commands:
                with self.subTest(command=command):
                    graph = MarketingGraph(llm=FakeLLM(), memory=FakeMemory(), marketing=FakeMarketing())
                    result = await graph.run(
                        prompt="marca minimalista",
                        payload={"sub_command": command},
                    )

                    self.assertIn(result["status"], {"success", "requires_approval"})
                    self.assertNotIn("no disponible", result["message"].lower())

        asyncio.run(scenario())

    def test_campaign_and_posts_explicit_commands_do_not_use_llm_tool_detection(self):
        async def scenario():
            for command in ("campaign", "posts"):
                with self.subTest(command=command):
                    graph = MarketingGraph(llm=FakeLLM(), memory=FakeMemory(), marketing=FakeMarketing())
                    result = await graph.run(
                        prompt="lanzar nueva colección",
                        payload={"sub_command": command, "autonomy_level": "assisted"},
                    )

                    self.assertEqual(result["status"], "requires_approval")
                    self.assertIn("Zernio", result["message"])

        asyncio.run(scenario())

    def test_natural_negative_comments_prompt_filters_without_llm_tool_detection(self):
        class NegativeMarketing(FakeMarketing):
            async def get_comments(self, platform: str, post_id: str):
                return [
                    {"id": "c1", "user": "user1", "text": "Me encanta este diseño!"},
                    {"id": "c2", "user": "user2", "text": "Tengo un problema con la demora"},
                ]

        async def scenario():
            graph = MarketingGraph(llm=FakeLLM(), memory=FakeMemory(), marketing=NegativeMarketing())

            result = await graph.run(
                prompt="Muestra comentarios negativos",
                payload={"sub_command": "chat"},
            )

            self.assertEqual(result["status"], "success")
            self.assertIn("problema", result["message"])
            self.assertNotIn("Me encanta", result["message"])

        asyncio.run(scenario())

    def test_internal_key_errors_are_reported_with_context(self):
        request = AssistantRequest(
            action_type=ActionType.marketing,
            prompt="crea una estrategia",
            source=Source(platform="discord", user_id="123"),
            payload={"sub_command": "chat"},
        )

        result = _format_internal_error(KeyError("object"), request, "ejecutando marketer:chat")

        self.assertEqual(result["status"], "error")
        self.assertIn("subcomando `chat`", result["message"])
        self.assertIn("schema de herramientas", result["hint"])
        self.assertIn("object", result["error_detail"])


if __name__ == "__main__":
    unittest.main()
