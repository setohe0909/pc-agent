import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "assistant-runtime"))

from app.domain.ports.trading import RiskPolicy
from app.domain.trading_policies import ConfigurableRiskPolicy
from app.use_cases.trading_workflow import TradingWorkflow


class FakeTrading:
    async def get_markets(self) -> list[dict]:
        return [{"ticker": "KXTEST", "title": "Test market"}]

    async def get_balance(self) -> float:
        return 100.0

    async def place_order(self, ticker: str, action: str, amount: float, client_order_id: str | None = None) -> dict:
        return {"status": "blocked", "order_id": client_order_id, "message": "blocked by adapter"}


class FakeLLM:
    async def analyze_trade(self, market_data: dict, prompt: str, system_instruction: str | None = None) -> dict:
        return {"should_trade": True, "ticker": "KXTEST", "action": "BUY YES", "amount": 1, "decision": "buy"}

    async def chat(self, prompt: str, context: dict | None = None, images=None, system_instruction=None) -> str:
        return "aprobado"


class FakeMemory:
    def __init__(self) -> None:
        self.saved = []

    async def get_context(self, user_id: str) -> str:
        return ""

    async def save_interaction(self, user_id: str, data: dict) -> None:
        self.saved.append(data)

    async def save_memory(self, category: str, summary: str) -> bool:
        return True


class TradingWorkflowTests(unittest.TestCase):
    def test_blocked_order_is_not_reported_as_executed(self) -> None:
        async def scenario() -> None:
            memory = FakeMemory()
            workflow = TradingWorkflow(
                trading_port=FakeTrading(),
                llm_port=FakeLLM(),
                memory_port=memory,
                risk_policy=ConfigurableRiskPolicy(RiskPolicy(max_order_amount=10)),
            )
            result = await workflow.execute_trade_decision("trade", user_id="user")
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(memory.saved, [])

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
