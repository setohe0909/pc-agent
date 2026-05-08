import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "assistant-runtime"))

from app.main import Approval, AssistantRequest, Source, _discord_gate


class AssistantRuntimeGateTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["DISCORD_REQUESTS_CHANNEL_ID"] = "requests"
        os.environ["DISCORD_APPROVER_USER_IDS"] = "admin"

    def test_trade_decision_requires_discord_approval(self) -> None:
        request = AssistantRequest(
            action_type="trade_decision",
            prompt="Comprar si el mercado esta barato",
            source=Source(platform="web", channel_id=None, user_id="user"),
        )

        result = _discord_gate(request)

        self.assertFalse(result["allowed"])
        self.assertIn("Discord", result["reason"])

    def test_trade_decision_accepts_authorized_discord_approval(self) -> None:
        request = AssistantRequest(
            action_type="trade_decision",
            prompt="Comprar si el mercado esta barato",
            source=Source(platform="discord", channel_id="requests", user_id="user"),
            approval=Approval(
                status="approved",
                channel_id="requests",
                approver_user_id="admin",
                message_id="message",
            ),
        )

        result = _discord_gate(request)

        self.assertTrue(result["allowed"])


if __name__ == "__main__":
    unittest.main()
