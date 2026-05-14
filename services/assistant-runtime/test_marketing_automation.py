import asyncio
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.use_cases.marketing_automation import MarketingAutomationService


class FakeLLM:
    def __init__(self):
        self.calls = []

    async def chat(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return "respuesta generica"


class FakeMemory:
    def __init__(self):
        self.saved = []

    async def get_context(self, user_id: str):
        return ""

    async def save_memory(self, category: str, summary: str) -> bool:
        self.saved.append((category, summary))
        return True


class FakeMarketing:
    def __init__(self):
        self.replies = []
        self.dms = []
        self.saved_leads = []
        self.campaign_drafts = []
        self.post_drafts = []
        self.automation_runs = []
        self.scheduled_posts = []
        self.published_posts = []
        self.processed = set()
        self.dashboard_calls = 0

    async def get_dashboard(self):
        self.dashboard_calls += 1
        return {
            "metrics": {"total_reach": "184.2K"},
            "audience": {"top_age_range": "25-34"},
            "recommendations": ["Duplicar formato ganador"],
        }

    async def get_top_content(self, platform=None, limit=5):
        return [
            {"platform": "instagram", "topic": "producto", "format": "reel"},
            {"platform": "tiktok", "topic": "educativo", "format": "video"},
        ][:limit]

    async def get_audience_insights(self):
        return {
            "segments": [{"name": "Compradores potenciales", "share": "38%"}],
            "top_age_range": "25-34",
        }

    async def get_best_posting_windows(self):
        return {"instagram": ["12:00-14:00", "19:00-21:00"], "tiktok": ["18:00-22:00", "07:00-09:00"]}

    async def get_comments(self, platform, post_id):
        return [
            {"id": "c1", "user": "u1", "text": "INFO por favor"},
            {"id": "c2", "user": "u2", "text": "Me encanta"},
        ]

    async def reply_to_comment(self, platform, comment_id, text):
        self.replies.append((platform, comment_id, text))
        return True

    async def send_dm(self, platform, user_id, text):
        self.dms.append((platform, user_id, text))
        return True

    async def save_lead(self, lead_data):
        self.saved_leads.append(lead_data)
        return True

    async def save_campaign_draft(self, campaign):
        self.campaign_drafts.append(campaign)
        self.processed.add(campaign["id"])
        return True

    async def save_post_draft(self, post):
        self.post_drafts.append(post)
        self.processed.add(post["id"])
        return True

    async def save_automation_run(self, run):
        self.automation_runs.append(run)
        if run.get("dedupe_key"):
            self.processed.add(run["dedupe_key"])
        return True

    async def has_processed(self, dedupe_key):
        return dedupe_key in self.processed

    async def schedule_post(self, post):
        self.scheduled_posts.append(post)
        return True

    async def publish_post(self, post):
        self.published_posts.append(post)
        return True


class MarketingAutomationTests(unittest.TestCase):
    def setUp(self):
        self._old_allow = os.environ.get("MARKETER_ALLOW_WRITES")
        self._old_enabled = os.environ.get("MARKETER_AUTOMATION_ENABLED")
        os.environ["MARKETER_AUTOMATION_ENABLED"] = "true"
        os.environ["MARKETER_ALLOW_WRITES"] = "false"

    def tearDown(self):
        if self._old_allow is None:
            os.environ.pop("MARKETER_ALLOW_WRITES", None)
        else:
            os.environ["MARKETER_ALLOW_WRITES"] = self._old_allow
        if self._old_enabled is None:
            os.environ.pop("MARKETER_AUTOMATION_ENABLED", None)
        else:
            os.environ["MARKETER_AUTOMATION_ENABLED"] = self._old_enabled

    def test_assisted_campaign_creates_draft_and_requires_approval(self):
        async def scenario():
            marketing = FakeMarketing()
            service = MarketingAutomationService(FakeLLM(), marketing, FakeMemory())

            result = await service.plan_campaign("lanzar nueva colección", {"autonomy_level": "assisted"})

            self.assertEqual(result["status"], "requires_approval")
            self.assertIn("campaign", result)
            self.assertEqual(marketing.dashboard_calls, 1)
            self.assertEqual(len(marketing.campaign_drafts), 1)

        asyncio.run(scenario())

    def test_duplicate_campaign_draft_is_not_saved_twice(self):
        async def scenario():
            marketing = FakeMarketing()
            service = MarketingAutomationService(FakeLLM(), marketing, FakeMemory())

            await service.plan_campaign("lanzar nueva colección", {"autonomy_level": "assisted"})
            await service.plan_campaign("lanzar nueva colección", {"autonomy_level": "assisted"})

            self.assertEqual(len(marketing.campaign_drafts), 1)

        asyncio.run(scenario())

    def test_posts_queue_generates_instagram_and_tiktok_without_scheduling(self):
        async def scenario():
            marketing = FakeMarketing()
            service = MarketingAutomationService(FakeLLM(), marketing, FakeMemory())

            result = await service.generate_post_queue("lanzar nueva colección", {"autonomy_level": "assisted"})

            self.assertEqual(result["status"], "requires_approval")
            platforms = {post["platform"] for post in result["posts"]}
            self.assertEqual(platforms, {"instagram", "tiktok"})
            self.assertEqual(marketing.scheduled_posts, [])
            self.assertEqual(marketing.published_posts, [])

        asyncio.run(scenario())

    def test_assisted_write_actions_do_not_call_external_write_methods(self):
        async def scenario():
            marketing = FakeMarketing()
            service = MarketingAutomationService(FakeLLM(), marketing, FakeMemory())

            respond = await service.respond_to_comments({"autonomy_level": "assisted"})
            magnet = await service.process_lead_magnets({"autonomy_level": "assisted"})
            qualify = await service.qualify_leads({"autonomy_level": "assisted"})

            self.assertEqual(respond["status"], "requires_approval")
            self.assertEqual(magnet["status"], "requires_approval")
            self.assertEqual(qualify["status"], "requires_approval")
            self.assertEqual(marketing.replies, [])
            self.assertEqual(marketing.dms, [])
            self.assertEqual(marketing.saved_leads, [])

        asyncio.run(scenario())

    def test_approved_post_queue_saves_zernio_drafts_when_writes_enabled(self):
        async def scenario():
            marketing = FakeMarketing()
            service = MarketingAutomationService(FakeLLM(), marketing, FakeMemory())

            result = await service.generate_post_queue("lanzar nueva colección", {"autonomy_level": "assisted", "is_approved": True})
            self.assertEqual(result["status"], "success")
            self.assertEqual(marketing.scheduled_posts, [])
            self.assertEqual(marketing.published_posts, [])

            os.environ["MARKETER_ALLOW_WRITES"] = "true"
            result = await service.generate_post_queue("lanzar nueva colección", {"autonomy_level": "assisted", "is_approved": True})
            self.assertEqual(result["status"], "success")
            self.assertEqual(marketing.scheduled_posts, [])
            self.assertTrue(marketing.published_posts)
            self.assertTrue(all(post.get("draft") for post in marketing.published_posts))
            self.assertIn("drafts en Zernio", result["message"])

        asyncio.run(scenario())

    def test_approved_post_uses_exact_approved_suggestion_without_regenerating(self):
        async def scenario():
            marketing = FakeMarketing()
            llm = FakeLLM()
            service = MarketingAutomationService(llm, marketing, FakeMemory())
            approved_caption = "Texto aprobado por el usuario\n\n#uno #dos #tres"

            result = await service.publish_post(
                "texto original que no debe publicarse",
                media_urls=["https://cdn.example.com/post.png"],
                platform="instagram",
                payload={
                    "is_approved": True,
                    "suggestion": {
                        "enhanced_description": "Texto aprobado por el usuario",
                        "hashtags": ["#uno", "#dos", "#tres"],
                        "caption": approved_caption,
                    },
                },
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(marketing.published_posts[0]["content"], approved_caption)
            self.assertEqual(llm.calls, [])

        asyncio.run(scenario())

    def test_approved_post_rebuilds_caption_from_suggestion_parts_without_regenerating(self):
        async def scenario():
            marketing = FakeMarketing()
            llm = FakeLLM()
            service = MarketingAutomationService(llm, marketing, FakeMemory())

            result = await service.publish_post(
                "texto original que no debe publicarse",
                platform="instagram",
                payload={
                    "is_approved": True,
                    "suggestion": {
                        "enhanced_description": "Descripción aprobada",
                        "hashtags": ["#marca", "#contenido"],
                    },
                },
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(marketing.published_posts[0]["content"], "Descripción aprobada\n\n#marca #contenido")
            self.assertEqual(llm.calls, [])

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
