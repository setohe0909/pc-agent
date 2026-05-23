import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "assistant-runtime"))

from app.main import AssistantRequest, Source, dispatch_assistant_request
from app.runtime.rate_limit import InMemoryRateLimiter


class FakeTradingWorkflow:
    async def execute_trade_decision(self, prompt, user_id=None):
        return {"status": "executed", "message": f"trade:{prompt}:{user_id}"}

    async def execute_chat(self, prompt, user_id=None):
        return f"chat:{prompt}:{user_id}"


class FakeMarketingWorkflow:
    async def run(self, prompt, payload, images=None):
        return {"status": "success", "message": f"marketing:{payload.get('sub_command')}:{len(images or [])}"}


class FakeWriterWorkflow:
    async def execute_writer_action(self, prompt, payload):
        return {"status": "success", "message": f"writer:{prompt}"}


class FakeEmailWorkflow:
    async def run(self, prompt, payload):
        return {"status": "success", "message": f"email:{payload.get('sub_command')}"}


class FakePictureWorkflow:
    async def run(self, prompt, payload, images=None, image_metadata=None):
        return {"status": "success", "message": f"picture:{len(images or [])}:{len(image_metadata or [])}"}


class FakeCoderWebWorkflow:
    async def run(self, prompt, payload, images=None):
        return {"status": "success", "message": f"coder:{payload.get('linear_issue_id')}:{len(images or [])}"}


class FakeModelStatusService:
    def get_status(self, agent):
        return {"status": "success", "message": f"models:{agent}"}


def fake_container():
    return SimpleNamespace(
        trading_workflow=FakeTradingWorkflow(),
        marketing_workflow=FakeMarketingWorkflow(),
        writer_workflow=FakeWriterWorkflow(),
        email_workflow=FakeEmailWorkflow(),
        picture_workflow=FakePictureWorkflow(),
        coder_web_workflow=FakeCoderWebWorkflow(),
        model_status_service=FakeModelStatusService(),
    )


def request(action_type, payload=None, images=None, image_metadata=None):
    return AssistantRequest(
        action_type=action_type,
        prompt="haz algo",
        source=Source(platform="test", user_id="u1"),
        payload=payload or {},
        images=images or [],
        image_metadata=image_metadata or [],
    )


class AssistantRuntimeDispatchTests(unittest.TestCase):
    def test_dispatches_all_action_types(self):
        container = fake_container()
        cases = [
            ("chat", {}, "chat:haz algo:u1"),
            ("trade_decision", {}, "trade:haz algo:u1"),
            ("marketing", {"sub_command": "status"}, "marketing:status:0"),
            ("writer", {}, "writer:haz algo"),
            ("email", {"sub_command": "status"}, "email:status"),
            ("picture", {}, "picture:0:0"),
            ("coder-web", {"linear_issue_id": "LIN-1"}, "coder:LIN-1:0"),
            ("model_status", {"agent": "coder-web"}, "models:coder-web"),
        ]
        for action_type, payload, expected_message in cases:
            with self.subTest(action_type=action_type):
                result, stage = asyncio.run(dispatch_assistant_request(container, request(action_type, payload)))
                self.assertEqual(result["message"], expected_message)
                self.assertTrue(stage)

    def test_invalid_base64_is_stable_error(self):
        result, stage = asyncio.run(dispatch_assistant_request(fake_container(), request("picture", images=["not-base64"])))

        self.assertEqual(result["status"], "error")
        self.assertIn("base64", result["message"])
        self.assertEqual(stage, "validando imagenes de picture")


class RateLimiterTests(unittest.TestCase):
    def test_rate_limiter_blocks_after_limit(self):
        limiter = InMemoryRateLimiter(limit=1, window_seconds=60)

        self.assertTrue(limiter.check("user").allowed)
        second = limiter.check("user")

        self.assertFalse(second.allowed)
        self.assertGreaterEqual(second.retry_after_seconds, 1)


if __name__ == "__main__":
    unittest.main()
